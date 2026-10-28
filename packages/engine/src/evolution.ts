import type { WhatsAppSendOtpInput } from "@astrobranding/contracts";

export class EvolutionWhatsAppClient {
  private baseUrl: string;
  private apiKey: string;
  private instance: string;

  constructor(
    baseUrl = process.env.EVOLUTION_URL || process.env.EVOLUTION_GATEWAY_URL || "http://evolution:8085",
    apiKey = process.env.EVOLUTION_API_KEY || "",
    instance = process.env.EVOLUTION_INSTANCE || process.env.PROJECT_NAME || "default"
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
      const brand = input.brandName || process.env.BRAND_NAME || process.env.PROJECT_NAME || "tu cuenta";
      const otpCode = Math.floor(100000 + Math.random() * 900000);
      const otpText = `Hola ${input.clientName || "Hola"}, tu código de verificación para ${brand} es: ${otpCode}`;

      // Evolution Go canonical endpoint: /send/text
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
        signal: AbortSignal.timeout(10000),
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
          signal: AbortSignal.timeout(10000),
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
