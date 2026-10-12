import { connect, JSONCodec, StringCodec } from "nats";
import {
  checkDbConnection,
  getCustomerHistory,
  getEventsContextFromDb,
  recordIncomingLead,
  lookupPhoneByLidFromDb,
  syncLidMappingsToValkey,
} from "./db.js";
import {
  checkValkeyConnection,
  acquireLock,
  checkRateLimit,
  isHumanTakeover,
  setHumanTakeover,
  clearHumanTakeover,
  getSessionHistory,
  appendSessionMessage,
  linkPhoneAndLid,
  resolveCanonicalPhone,
  redis,
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
  downloadMediaFromEvolution,
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
export async function processInboundWhatsAppMessage(rawPayload: any): Promise<{ status: string; detail?: string }> {
  // 1. Extract metadata from Evolution payload (supports both Go and Baileys formats)
  const eventData = rawPayload?.data || rawPayload || {};
  const info = eventData.Info || eventData.info || rawPayload?.Info || rawPayload?.info || {};
  const key = eventData.key || rawPayload?.key || {};

  const isFromMe = Boolean(
    info.IsFromMe ??
    info.isFromMe ??
    key.fromMe ??
    eventData.fromMe ??
    rawPayload?.fromMe ??
    false
  );

  const chatJid = String(
    info.Chat ||
    key.remoteJid ||
    eventData.Chat ||
    eventData.chatJid ||
    rawPayload?.chatJid ||
    rawPayload?.remoteJid ||
    ""
  );

  const senderJid = String(
    info.Sender ||
    eventData.Sender ||
    eventData.senderJid ||
    key.participant ||
    rawPayload?.sender ||
    ""
  );

  const senderAlt = String(
    info.SenderAlt ||
    eventData.SenderAlt ||
    eventData.senderAlt ||
    ""
  );

  const isGroup = Boolean(
    (info.IsGroup ?? false) ||
    chatJid.includes("@g.us") ||
    senderJid.includes("@g.us")
  );

  // Filter out status broadcasts and groups
  if (isGroup || chatJid.includes("status@broadcast")) {
    return { status: "ignored_group_or_status" };
  }

  // Link any Phone and LID present in this webhook event
  const allCandidateIds = [
    chatJid,
    senderJid,
    senderAlt,
    key.remoteJid,
    key.participant,
    eventData.Chat,
    eventData.Sender,
    eventData.SenderAlt,
    eventData.remoteJid,
  ].filter(Boolean).map(String);

  const lidCandidate = allCandidateIds.find((id) => id.includes("@lid"));
  const phoneCandidate = allCandidateIds.find(
    (id) => id.includes("@s.whatsapp.net") && cleanPhoneNumber(id) !== cleanPhoneNumber(BOT_PHONE)
  );

  if (lidCandidate && phoneCandidate) {
    await linkPhoneAndLid(cleanPhoneNumber(phoneCandidate), cleanPhoneNumber(lidCandidate));
  }

  // Resolve customer phone (prioritizing real WhatsApp phone numbers over @lid)
  const rawTargetIds = isFromMe
    ? [chatJid, key.remoteJid, eventData.remoteJid]
    : [senderAlt, senderJid, chatJid, key.remoteJid];

  // Pick first ID that has @s.whatsapp.net, or doesn't have @lid
  const realPhoneId =
    rawTargetIds.find((id) => id && String(id).includes("@s.whatsapp.net")) ||
    rawTargetIds.find((id) => id && !String(id).includes("@lid") && !String(id).includes("@g.us")) ||
    rawTargetIds[0];

  const rawCleanPhone = cleanPhoneNumber(String(realPhoneId || (isFromMe ? chatJid : senderJid || chatJid)));
  if (!rawCleanPhone || rawCleanPhone === cleanPhoneNumber(BOT_PHONE)) {
    return { status: "ignored_bot_self_message" };
  }

  // Resolve canonical phone number (resolving LID -> real phone via Valkey or DB fallback)
  let canonicalPhone = await resolveCanonicalPhone(rawCleanPhone);
  if (canonicalPhone === rawCleanPhone && rawCleanPhone.length > 13) {
    const dbPhone = await lookupPhoneByLidFromDb(rawCleanPhone);
    if (dbPhone) {
      await linkPhoneAndLid(dbPhone, rawCleanPhone);
      canonicalPhone = dbPhone;
    }
  }

  const primaryCustomerPhone = canonicalPhone;

  const messageId = String(
    info.ID ||
    key.id ||
    eventData.messageId ||
    rawPayload?.messageId ||
    `msg-${Date.now()}`
  );

  // 2. Extract message text or audio
  const msgObj = eventData.Message || eventData.message || rawPayload?.Message || rawPayload?.message || {};
  let messageText = String(
    msgObj.conversation ||
    msgObj.extendedTextMessage?.text ||
    msgObj.imageMessage?.caption ||
    msgObj.videoMessage?.caption ||
    eventData.text ||
    rawPayload?.text ||
    ""
  ).trim();

  // Quoted message context
  const contextInfo =
    msgObj.extendedTextMessage?.contextInfo ||
    msgObj.contextInfo ||
    eventData.contextInfo;
  const quotedMessage = contextInfo?.quotedMessage;
  if (quotedMessage) {
    const quotedText = String(
      quotedMessage.conversation ||
      quotedMessage.extendedTextMessage?.text ||
      quotedMessage.imageMessage?.caption ||
      quotedMessage.videoMessage?.caption ||
      ""
    ).trim();
    if (quotedText && messageText) {
      messageText = `[En respuesta a: "${quotedText}"] ${messageText}`;
    }
  }

  const isAudio = Boolean(
    msgObj.audioMessage ||
    msgObj.AudioMessage ||
    msgObj.mimetype?.includes("audio") ||
    eventData.audioMessage ||
    eventData.AudioMessage ||
    eventData.mimetype?.includes("audio") ||
    eventData.mediaType === "audio" ||
    rawPayload?.mediaType === "audio" ||
    eventData.audio ||
    rawPayload?.audio ||
    rawPayload?.messageType === "audio" ||
    rawPayload?.messageType === "audioMessage" ||
    eventData.messageType === "audio" ||
    eventData.messageType === "audioMessage"
  );

  if (isAudio && !messageText) {
    console.log(`[WhatsAppBot] Audio message detected for ${primaryCustomerPhone}`);
    let audioData: string | null =
      msgObj.base64 ||
      msgObj.audioMessage?.base64 ||
      msgObj.AudioMessage?.base64 ||
      eventData.base64 ||
      eventData.audioBase64 ||
      rawPayload?.base64 ||
      rawPayload?.data?.base64 ||
      null;

    if (!audioData && (msgObj.audioMessage || msgObj.AudioMessage || eventData.Message)) {
      console.log(`[WhatsAppBot] Audio missing inline base64, fetching from Evolution /message/downloadmedia...`);
      audioData = await downloadMediaFromEvolution(msgObj);
    }

    if (audioData) {
      console.log(`[WhatsAppBot] Audio payload found (${audioData.length} chars), transcribing with Groq Whisper...`);
      const transcription = await transcribeAudioGroq(audioData);
      if (transcription) {
        messageText = transcription.trim();
        console.log(`[WhatsAppBot] Audio successfully transcribed for ${primaryCustomerPhone}: "${messageText}"`);
      }
    }

    if (!messageText) {
      console.warn(`[WhatsAppBot] Audio transcription returned empty for ${primaryCustomerPhone}, sending polite fallback`);
      await sendWhatsAppMessage(
        primaryCustomerPhone,
        "Recibí tu nota de voz, pero no logré escucharla con total claridad. ¿Podrías escribirme tu consulta brevemente?"
      );
      return { status: "audio_transcription_fallback" };
    }
  }

  if (!messageText) {
    console.log(`[WhatsAppBot] Webhook ignored: empty message text for ${primaryCustomerPhone} (Event: ${rawPayload?.event || "unknown"})`);
    return { status: "ignored_empty_payload" };
  }

  console.log(`[WhatsAppBot] Inbound message from ${primaryCustomerPhone}: "${messageText.substring(0, 60)}" (fromMe: ${isFromMe})`);

  // 3. Operator takeover controls
  if (isFromMe) {
    const trimmed = messageText.trim().toLowerCase();
    if (trimmed === "#bot") {
      await clearHumanTakeover(primaryCustomerPhone);
      await sendWhatsAppMessage(primaryCustomerPhone, "[Bot reactivado para este chat]");
      return { status: "human_takeover_cleared" };
    }
    if (["#stop", "#off", "#silencio", "#desactivar"].includes(trimmed)) {
      await setHumanTakeover(primaryCustomerPhone, 315360000); // 10 years permanent stop
      await sendWhatsAppMessage(primaryCustomerPhone, "[Atención automática pausada por operador]");
      return { status: "human_takeover_stopped_permanent" };
    }
    if (trimmed === "#mute") {
      await setHumanTakeover(primaryCustomerPhone, 86400); // 24 hours
      await sendWhatsAppMessage(primaryCustomerPhone, "[Bot en silencio por 24 horas]");
      return { status: "human_takeover_muted_24h" };
    }

    // Any manual message by human operator pauses bot for 2 hours
    await setHumanTakeover(primaryCustomerPhone, 7200);
    await appendSessionMessage(primaryCustomerPhone, "assistant", `[Operador humano]: ${messageText}`);
    return { status: "human_takeover_active_2h" };
  }

  // Customer requested human assistance or stop
  const cleanLower = messageText.trim().toLowerCase();
  const isStopCommand = ["#stop", "#off", "#silencio", "#desactivar"].includes(cleanLower);
  const isHumanRequest =
    isStopCommand ||
    /^(asesor|humano|persona|hablar con un humano|hablar con una persona|asesor humano)$/i.test(cleanLower) ||
    cleanLower.includes("asesor humano") ||
    cleanLower.includes("comunicarme con un humano") ||
    cleanLower.includes("hablar con una persona");

  if (isHumanRequest) {
    console.log(`[WhatsAppBot] Customer ${primaryCustomerPhone} requested human assistance or stop`);
    await setHumanTakeover(primaryCustomerPhone, 172800); // 48 hours
    await appendSessionMessage(primaryCustomerPhone, "user", messageText);
    const ackMessage = "Entendido. He pausado la atención automática para que un asesor de nuestro equipo te responda personalmente en este chat.";
    await sendWhatsAppMessage(primaryCustomerPhone, ackMessage);
    await appendSessionMessage(primaryCustomerPhone, "assistant", ackMessage);
    return { status: "customer_requested_human_takeover" };
  }

  // If customer is sending while human takeover is active, store in session and stay silent
  if (await isHumanTakeover(primaryCustomerPhone)) {
    console.log(`[WhatsAppBot] Human takeover active for ${primaryCustomerPhone}. Staying silent.`);
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

  // 7. Load customer history and live active events from PostgreSQL (SSoT)
  const [customerProfile, eventsContext] = await Promise.all([
    getCustomerHistory(primaryCustomerPhone),
    getEventsContextFromDb(),
  ]);

  // Record / update lead in background
  recordIncomingLead(primaryCustomerPhone).catch(() => {});

  // 8. Load recent session turns from Valkey
  const sessionHistory = await getSessionHistory(primaryCustomerPhone, 20);

  // 9. Build Dynamic System Prompt with Brandbook SSoT, Customer Ficha, and Live Active Events
  const systemPrompt = buildSystemPrompt(customerProfile, eventsContext);

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
    console.log(`[NATS] Connecting to broker...`);
    const parsed = new URL(NATS_URL);
    const nc = await connect({
      servers: `${parsed.hostname}:${parsed.port || "4222"}`,
      user: parsed.username ? decodeURIComponent(parsed.username) : undefined,
      pass: parsed.password ? decodeURIComponent(parsed.password) : undefined,
    });
    // Core NATS subscription with queue group (works with zero pre-created stream dependencies)
    const sub = nc.subscribe("whatsapp.messages", {
      queue: "whatsapp-worker-group",
    });

    console.log("[NATS] Subscribed to subject 'whatsapp.messages' (queue: whatsapp-worker-group)");

    (async () => {
      for await (const msg of sub) {
        try {
          const payload = jsonCodec.decode(msg.data);
          await processInboundWhatsAppMessage(payload);
        } catch (err) {
          console.error("[NATS] Error processing message from subject:", err);
        }
      }
    })();
  } catch (err) {
    console.warn("[NATS] NATS broker connection skipped (relying on HTTP webhook):", err);
  }
}

/**
 * Start Bun HTTP Server (Health & Webhook Ingress)
 */
if (import.meta.main) {
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
  syncLidMappingsToValkey(redis).catch((err) => console.warn("[Startup] LID sync error:", err));
}

