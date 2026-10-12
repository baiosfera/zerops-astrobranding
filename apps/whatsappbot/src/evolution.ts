const EVOLUTION_URL = process.env.EVOLUTION_URL || "http://evolution:8085";
const EVOLUTION_API_KEY = process.env.EVOLUTION_API_KEY || "481c8c43-0023-4028-bad5-9d1355a3674c";

export async function checkEvolutionConnection(): Promise<boolean> {
  try {
    const res = await fetch(`${EVOLUTION_URL}/server/ok`);
    return res.status === 200;
  } catch (err) {
    console.error("[Evolution] Ping failed:", err);
    return false;
  }
}

export async function sendWhatsAppMessage(number: string, text: string): Promise<boolean> {
  const cleanPhone = number.replace(/\D/g, "");
  if (!cleanPhone) {
    console.warn("[Evolution] Cannot send message: empty phone number");
    return false;
  }

  const payload = {
    number: cleanPhone,
    text,
  };

  const endpoint = `${EVOLUTION_URL}/send/text`;
  try {
    const res = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: EVOLUTION_API_KEY,
      },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      console.log(`[Evolution] WhatsApp message sent successfully to ${cleanPhone}`);
      return true;
    }

    const errBody = await res.text();
    console.warn(`[Evolution] Send failed HTTP ${res.status}: ${errBody}`);
  } catch (err) {
    console.error(`[Evolution] Network error sending to ${endpoint}:`, err);
  }

  return false;
}

export async function downloadMediaFromEvolution(messageObj: any): Promise<string | null> {
  try {
    const res = await fetch(`${EVOLUTION_URL}/message/downloadmedia`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: EVOLUTION_API_KEY,
      },
      body: JSON.stringify({ message: messageObj }),
    });

    if (res.ok) {
      const data = (await res.json()) as any;
      const base64Str = data?.data?.base64 || data?.base64;
      if (base64Str) {
        return String(base64Str).replace(/^data:audio\/[^;]+;base64,/, "").trim();
      }
    } else {
      const err = await res.text();
      console.warn(`[Evolution] downloadmedia failed HTTP ${res.status}: ${err}`);
    }
  } catch (err) {
    console.error("[Evolution] downloadmedia network error:", err);
  }
  return null;
}

export async function transcribeAudioGroq(audioBase64: string): Promise<string | null> {
  const keys = [
    process.env.GROQ_API_KEY,
    process.env.WHISPER_GROQ_API_KEY,
  ].filter(Boolean) as string[];

  if (keys.length === 0) {
    console.warn("[Groq Whisper] GROQ_API_KEY / WHISPER_GROQ_API_KEY not configured");
    return null;
  }

  const cleanBase64 = audioBase64.replace(/^data:audio\/[^;]+;base64,/, "").trim();
  const audioBuffer = Buffer.from(cleanBase64, "base64");
  if (audioBuffer.length === 0) {
    console.warn("[Groq Whisper] Empty audio buffer after base64 decode");
    return null;
  }

  for (const apiKey of keys) {
    try {
      const blob = new Blob([audioBuffer], { type: "audio/ogg" });
      const formData = new FormData();
      formData.append("file", blob, "audio.ogg");
      formData.append("model", "whisper-large-v3-turbo");
      formData.append("language", "es");

      const res = await fetch("https://api.groq.com/openai/v1/audio/transcriptions", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
        body: formData,
      });

      if (res.ok) {
        const data = (await res.json()) as any;
        if (data.text) {
          console.log(`[Groq Whisper] Transcription successful (${data.text.length} chars)`);
          return data.text.trim();
        }
      } else {
        const errBody = await res.text();
        console.warn(`[Groq Whisper] Transcription failed HTTP ${res.status} with key ...${apiKey.slice(-6)}: ${errBody}`);
      }
    } catch (err) {
      console.error("[Groq Whisper] Network error during transcription:", err);
    }
  }

  return null;
}

