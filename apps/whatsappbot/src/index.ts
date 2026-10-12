import { connect, JSONCodec, StringCodec } from "nats";
import { checkDbConnection, getCustomerHistory, recordIncomingLead } from "./db.js";
import {
  checkValkeyConnection,
  acquireLock,
  checkRateLimit,
  isHumanTakeover,
  setHumanTakeover,
  clearHumanTakeover,
  getSessionHistory,
  appendSessionMessage,
  type ChatMessage,
} from "./valkey.js";
import {
  checkBifrostConnection,
  requestLlmCompletion,
  detectPurchaseIntent,
  type CompletionMessage,
} from "./bifrost.js";
import {
  checkEvolutionConnection,
  sendWhatsAppMessage,
  transcribeAudioGroq,
} from "./evolution.js";
import {
  resolveBrandSSoT,
  buildSystemPrompt,
  sanitizeAndValidateUrls,
  sanitizeTone,
} from "./brandbook.js";

const PORT = parseInt(process.env.PORT || "3005", 10);
const NATS_URL = process.env.NATS_URL;
const BOT_PHONE = process.env.BOT_PHONE || "573021004070";

const jsonCodec = JSONCodec();

/**
 * Normalizes phone numbers to standard format (digits only)
 */
function cleanPhoneNumber(jidOrPhone: string): string {
  const digits = jidOrPhone.replace(/@.*$/, "").replace(/\D/g, "");
  return digits;
}

/**
 * Checks if message is a brief acknowledgement (silence rule)
 */
function isBriefAcknowledgement(text: string): boolean {
  const clean = text.trim().toLowerCase();
  const acks = ["ok", "gracias", "muchas gracias", "listo", "vale", "dale", "de una", "perfecto", "bueno", "chao"];
  return acks.includes(clean);
}

/**
 * Unified Inbound Message Processing Pipeline
 */
export async function processInboundWhatsAppMessage(event: any): Promise<{ status: string; detail?: string }> {
  // 1. Extract metadata from Evolution payload (supports both Go and Baileys formats)
  const isFromMe = !!(
    event.fromMe ??
    event.key?.fromMe ??
    event.info?.IsFromMe ??
    event.info?.isFromMe
  );

  const rawChatJid = event.chatJid || event.key?.remoteJid || event.info?.Chat || "";
  const rawSenderJid = event.senderJid || event.key?.participant || event.info?.Sender || rawChatJid;
  const messageId = event.key?.id || event.messageId || event.info?.ID || `msg-${Date.now()}`;

  // Filter out status broadcasts and groups
  if (rawChatJid.includes("@g.us") || rawChatJid.includes("status@broadcast")) {
    return { status: "ignored_group_or_status" };
  }

  // Resolve customer phone
  const primaryCustomerPhone = cleanPhoneNumber(isFromMe ? rawChatJid : rawSenderJid);
  if (!primaryCustomerPhone || primaryCustomerPhone === cleanPhoneNumber(BOT_PHONE)) {
    return { status: "ignored_bot_self_message" };
  }

  // 2. Extract message text or audio
  let messageText = (
    event.message?.conversation ||
    event.message?.extendedTextMessage?.text ||
    event.message?.imageMessage?.caption ||
    event.text ||
    ""
  ).trim();

  const isAudio = !!(event.message?.audioMessage || event.audio || event.mediaType === "audio");
  if (isAudio && !messageText) {
    const audioData = event.message?.audioMessage?.base64 || event.audioBase64 || event.base64;
    if (audioData) {
      const transcription = await transcribeAudioGroq(audioData);
      if (transcription) {
        messageText = transcription.trim();
      }
    }
    if (!messageText) {
      await sendWhatsAppMessage(
        primaryCustomerPhone,
        "Recibí tu nota de voz, pero no logré escucharla con total claridad. ¿Podrías escribirme tu consulta brevemente?"
      );
      return { status: "audio_transcription_fallback" };
    }
  }

  if (!messageText) {
    return { status: "ignored_empty_payload" };
  }

  // 3. Operator takeover controls
  if (isFromMe) {
    const lower = messageText.toLowerCase();
    if (lower === "#bot") {
      await clearHumanTakeover(primaryCustomerPhone);
      await sendWhatsAppMessage(primaryCustomerPhone, "[Bot reactivado para este chat]");
      return { status: "human_takeover_cleared" };
    }
    if (["#stop", "#off", "#silencio", "#desactivar"].includes(lower)) {
      await setHumanTakeover(primaryCustomerPhone, 315360000); // 10 years
      return { status: "human_takeover_stopped_permanent" };
    }
    if (lower === "#mute") {
      await setHumanTakeover(primaryCustomerPhone, 86400); // 24 hours
      return { status: "human_takeover_muted_24h" };
    }

    // Any manual message by human operator pauses bot for 2 hours
    await setHumanTakeover(primaryCustomerPhone, 7200);
    await appendSessionMessage(primaryCustomerPhone, "assistant", `[Operador humano]: ${messageText}`);
    return { status: "human_takeover_active_2h" };
  }

  // If customer is sending while human takeover is active, store in session and stay silent
  if (await isHumanTakeover(primaryCustomerPhone)) {
    await appendSessionMessage(primaryCustomerPhone, "user", messageText);
    return { status: "ignored_human_takeover_active" };
  }

  // 4. Distributed atomic lock (prevent concurrent duplicate processing)
  const lockAcquired = await acquireLock(messageId);
  if (!lockAcquired) {
    return { status: "ignored_duplicate_message" };
  }

  // 5. Anti-flood rate limit
  const withinRate = await checkRateLimit(primaryCustomerPhone, 10, 60);
  if (!withinRate) {
    console.warn(`[RateLimit] Phone ${primaryCustomerPhone} exceeded 10 msg/min`);
    return { status: "ignored_rate_limited" };
  }

  // 6. Silence rule on brief acknowledgements
  if (isBriefAcknowledgement(messageText)) {
    await appendSessionMessage(primaryCustomerPhone, "user", messageText);
    return { status: "silence_brief_ack" };
  }

  // 7. Load customer history and past events from PostgreSQL (SSoT)
  const customerProfile = await getCustomerHistory(primaryCustomerPhone);

  // Record / update lead in background
  recordIncomingLead(primaryCustomerPhone).catch(() => {});

  // 8. Load recent session turns from Valkey
  const sessionHistory = await getSessionHistory(primaryCustomerPhone, 20);

  // 9. Build Dynamic System Prompt with Brandbook SSoT and Customer Ficha
  const systemPrompt = buildSystemPrompt(customerProfile);

  // Construct message array for LLM
  const messages: CompletionMessage[] = [
    { role: "system", content: systemPrompt },
    ...sessionHistory.map((m) => ({ role: m.role, content: m.content })),
    { role: "user", content: messageText },
  ];

  // 10. Dual-Tier routing: if commercial intent or VIP -> production tier (DeepSeek), else auto (FreeLLMAPI)
  const isPurchase = detectPurchaseIntent(messageText);
  const tier = isPurchase || customerProfile.isVip ? "production" : "auto";

  console.log(`[Inference] Dispatching turn for ${primaryCustomerPhone} (Tier: ${tier}, PurchaseIntent: ${isPurchase})`);

  let replyText = "";
  try {
    replyText = await requestLlmCompletion(messages, { tier });
  } catch (err: any) {
    console.error(`[Inference:Error] Primary tier ${tier} failed:`, err);
    // Automatic fallback to production tier if auto tier failed
    if (tier === "auto") {
      replyText = await requestLlmCompletion(messages, { tier: "production" });
    } else {
      throw err;
    }
  }

  // 11. Sanitization post-LLM
  let finalReply = sanitizeAndValidateUrls(replyText);
  finalReply = sanitizeTone(finalReply);

  // 12. Simulate natural human typing delay
  const typingDelayMs = Math.min(5000, Math.max(1500, finalReply.length * 20));
  await new Promise((resolve) => setTimeout(resolve, typingDelayMs));

  // 13. Dispatch reply to Evolution API
  const dispatched = await sendWhatsAppMessage(primaryCustomerPhone, finalReply);
  if (!dispatched) {
    console.error(`[Evolution] Failed to deliver WhatsApp reply to ${primaryCustomerPhone}`);
  }

  // 14. Persist turns in Valkey
  await appendSessionMessage(primaryCustomerPhone, "user", messageText);
  await appendSessionMessage(primaryCustomerPhone, "assistant", finalReply);

  return { status: "processed", detail: `Dispatched ${finalReply.length} chars to ${primaryCustomerPhone}` };
}

/**
 * Initialize NATS JetStream Consumer
 */
async function startNatsConsumer() {
  if (!NATS_URL) {
    console.warn("[NATS] NATS_URL not provided, skipping JetStream subscriber");
    return;
  }

  try {
    console.log(`[NATS] Connecting to broker at ${NATS_URL}...`);
    const nc = await connect({ servers: NATS_URL });
    const js = nc.jetstream();

    // Subscribe to subject whatsapp.messages
    const sub = await js.subscribe("whatsapp.messages", {
      queue: "whatsapp-worker-group",
    });

    console.log("[NATS] Subscribed to JetStream stream subject 'whatsapp.messages' (queue: whatsapp-worker-group)");

    (async () => {
      for await (const msg of sub) {
        try {
          const payload = jsonCodec.decode(msg.data);
          await processInboundWhatsAppMessage(payload);
          msg.ack();
        } catch (err) {
          console.error("[NATS] Error processing message from stream:", err);
          msg.term();
        }
      }
    })();
  } catch (err) {
    console.warn("[NATS] JetStream connection failed (will rely on HTTP webhook):", err);
  }
}

/**
 * Start Bun HTTP Server (Health & Webhook Ingress)
 */
Bun.serve({
  port: PORT,
  async fetch(req: Request) {
    const url = new URL(req.url);

    // Healthcheck endpoint
    if (url.pathname === "/health" || url.pathname === "/healthz") {
      const [dbOk, valkeyOk, bifrostOk, evoOk] = await Promise.all([
        checkDbConnection(),
        checkValkeyConnection(),
        checkBifrostConnection(),
        checkEvolutionConnection(),
      ]);

      const brand = resolveBrandSSoT();
      const healthy = dbOk && valkeyOk && bifrostOk;

      const body = {
        status: healthy ? "ok" : "degraded",
        service: "whatsappbot",
        uptime: process.uptime(),
        checks: {
          database: dbOk ? "healthy" : "failing",
          valkey: valkeyOk ? "healthy" : "failing",
          bifrost: bifrostOk ? "healthy" : "failing",
          evolution: evoOk ? "healthy" : "failing",
          brandbook: brand.brandName ? "loaded" : "fallback",
        },
        brand: {
          name: brand.brandName,
          archetype: brand.archetype,
        },
      };

      return new Response(JSON.stringify(body), {
        status: healthy ? 200 : 503,
        headers: { "Content-Type": "application/json" },
      });
    }

    // Direct Webhook Ingress (dual-path from Evolution)
    if (url.pathname === "/webhook" && req.method === "POST") {
      try {
        const body = await req.json();
        // Early acknowledgment < 20ms
        const promise = processInboundWhatsAppMessage(body);
        // Do not block HTTP response
        promise.catch((err) => console.error("[Webhook] Background error:", err));

        return new Response(JSON.stringify({ status: "acknowledged" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      } catch (err: any) {
        return new Response(JSON.stringify({ error: err.message }), {
          status: 400,
          headers: { "Content-Type": "application/json" },
        });
      }
    }

    return new Response(JSON.stringify({ service: "whatsappbot", status: "running" }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  },
});

console.log(`[whatsappbot] HTTP Server running on port :${PORT}`);
startNatsConsumer();
