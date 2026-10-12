export interface CompletionMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface BifrostOptions {
  tier?: "auto" | "production";
  temperature?: number;
  maxTokens?: number;
}

const BIFROST_URL = process.env.BIFROST_URL || "http://bifrost:8080/v1";
const BIFROST_VIRTUAL_KEY = process.env.BIFROST_VIRTUAL_KEY || "vk-production-main";

export async function checkBifrostConnection(): Promise<boolean> {
  try {
    const res = await fetch(`${BIFROST_URL}/models`, {
      headers: {
        Authorization: `Bearer ${BIFROST_VIRTUAL_KEY}`,
      },
    });
    return res.status === 200 || res.status === 401; // Responding service
  } catch (err) {
    console.error("[Bifrost] Health check failed:", err);
    return false;
  }
}

export async function requestLlmCompletion(
  messages: CompletionMessage[],
  options: BifrostOptions = {}
): Promise<string> {
  const isProduction = options.tier === "production";
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${BIFROST_VIRTUAL_KEY}`,
  };

  if (isProduction) {
    headers["x-tier"] = "production";
  }

  const payload = {
    model: isProduction ? "deepseek-chat" : "auto",
    messages,
    temperature: options.temperature ?? 0.2,
    max_tokens: options.maxTokens ?? 800,
  };

  const res = await fetch(`${BIFROST_URL}/chat/completions`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(15000), // 15s timeout to prevent hanging
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Bifrost returned HTTP ${res.status}: ${errText}`);
  }

  const data = (await res.json()) as any;
  const reply = data.choices?.[0]?.message?.content || data.choices?.[0]?.message?.reasoning_content;
  if (!reply) {
    throw new Error("Bifrost returned an empty response body");
  }
  return reply.trim();
}

/**
 * Detects if user message indicates commercial or booking intent
 */
export function detectPurchaseIntent(text: string, customKeywords: string[] = []): boolean {
  const normalized = text.toLowerCase();
  const baseBuyingKeywords = [
    "comprar", "compra", "orden", "pedido", "reserv", "pago", "pagar",
    "transferencia", "nequi", "daviplata", "pse", "tarjeta", "precio",
    "cuanto vale", "cuánto vale", "costo", "cotiz", "catalogo", "adquirir",
    "contrat", "ticket", "pase", "suscripci", "link de pago"
  ];
  const allKeywords = [...baseBuyingKeywords, ...customKeywords.map((k) => k.toLowerCase())];
  return allKeywords.some((kw) => normalized.includes(kw));
}
