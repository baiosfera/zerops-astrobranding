const EVOLUTION_URL = process.env.EVOLUTION_URL || "http://evolution:8085";

export async function checkEvolutionConnection(): Promise<boolean> {
  try {
    const res = await fetch(`${EVOLUTION_URL}/health`);
    return res.status === 200;
  } catch (err) {
    console.error("[Evolution] Ping failed:", err);
    return false;
  }
}

export async function sendWhatsAppMessage(number: string, text: string): Promise<boolean> {
  const cleanPhone = number.replace(/\D/g, "");
  const payload = {
    number: cleanPhone,
    text,
  };

  // EvolutionGo supports /message/sendText/ and /send/text
  const endpoints = [
    `${EVOLUTION_URL}/message/sendText/`,
    `${EVOLUTION_URL}/send/text`,
  ];

  for (const endpoint of endpoints) {
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        return true;
      }
    } catch (err) {
      console.warn(`[Evolution] Failed sending to ${endpoint}:`, err);
    }
  }

  return false;
}

export async function transcribeAudioGroq(audioBase64: string): Promise<string | null> {
  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    console.warn("[Groq Whisper] GROQ_API_KEY not configured");
    return null;
  }

  try {
    const audioBuffer = Buffer.from(audioBase64, "base64");
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
      return data.text || null;
    }
  } catch (err) {
    console.error("[Groq Whisper] Transcription error:", err);
  }
  return null;
}
