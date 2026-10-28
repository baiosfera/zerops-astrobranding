import type { WhatsAppSendOtpInput } from "@astrobranding/contracts";

export function calculateHumanTypingDelay(textLength: number): number {
  const charsPerSecond = 26 + Math.floor(Math.random() * 8); // 26 to 34 chars/sec
  const typingTimeMs = Math.round((textLength / charsPerSecond) * 1000);
  const cognitivePauseMs = 1500 + Math.floor(Math.random() * 1000); // 1.5s to 2.5s
  const totalDelay = typingTimeMs + cognitivePauseMs;
  return Math.max(4500, Math.min(7500, totalDelay));
}

export class EvolutionWhatsAppClient {
  private baseUrl: string;
  private apiKey: string;
  private instance: string;

  constructor(
    baseUrl = process.env.EVOLUTION_URL || process.env.EVOLUTION_GATEWAY_URL || "http://evolution:8085",
    apiKey = process.env.EVOLUTION_API_KEY || "",
    instance = process.env.EVOLUTION_INSTANCE || process.env.PROJECT_NAME || "catalinaglamur"
  ) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.instance = instance;
  }

  async healthCheck(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/server/ok`, { signal: AbortSignal.timeout(3000) });
      return res.ok;
    } catch {
      return false;
    }
  }

  async sendOtp(input: WhatsAppSendOtpInput): Promise<{ success: boolean; messageId?: string; error?: string }> {
    try {
      const cleanNumber = input.phoneNumber.replace("+", "");
      const brand = input.brandName || process.env.BRAND_NAME || process.env.PROJECT_NAME || "Catalina Glamur";
      const otpCode = Math.floor(100000 + Math.random() * 900000);
      const otpText = `Hola ${input.clientName || "Hola"}, tu código de verificación para ${brand} es: ${otpCode}`;

      // 1. Human Emulation: native WhatsApp composing state with 4.5s - 7.5s realistic delay
      const delayMs = calculateHumanTypingDelay(otpText.length);
      try {
        await fetch(`${this.baseUrl}/message/presence`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(this.apiKey ? { apikey: this.apiKey } : {}),
          },
          body: JSON.stringify({
            number: cleanNumber,
            state: "composing",
            delay: delayMs,
          }),
          signal: AbortSignal.timeout(delayMs + 4000),
        });
        await new Promise((r) => setTimeout(r, 400 + Math.floor(Math.random() * 400)));
      } catch {
        // Non-blocking fallback
      }

      // 2. Evolution Go canonical endpoint: /send/text
      const res = await fetch(`${this.baseUrl}/send/text`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          apikey: this.apiKey,
        },
        body: JSON.stringify({
          number: cleanNumber,
          text: otpText,
        }),
        signal: AbortSignal.timeout(15000),
      });

      if (!res.ok) {
        // Fallback to /message/sendText/:instance
        const fallbackRes = await fetch(`${this.baseUrl}/message/sendText/${this.instance}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            apikey: this.apiKey,
          },
          body: JSON.stringify({
            number: cleanNumber,
            text: otpText,
          }),
          signal: AbortSignal.timeout(15000),
        });
        if (!fallbackRes.ok) {
          return { success: false, error: `Status ${res.status} (fallback: ${fallbackRes.status})` };
        }
        const fallbackData = (await fallbackRes.json()) as { key?: { id?: string } };
        return { success: true, messageId: fallbackData?.key?.id };
      }

      const data = (await res.json()) as { key?: { id?: string } };
      return { success: true, messageId: data?.key?.id };
    } catch (err: unknown) {
      return { success: false, error: err instanceof Error ? err.message : "Unknown error" };
    }
  }
}

export const evolution = new EvolutionWhatsAppClient();
