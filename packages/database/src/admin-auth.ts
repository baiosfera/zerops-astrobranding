import { createHash, randomBytes, randomInt } from "crypto";
import { eq, and, gt, desc } from "drizzle-orm";
import { getDb } from "./index";
import { adminUsers, adminOtps, adminSessions, type AdminUser } from "./schema";

export interface AdminAuthResult {
  success: boolean;
  error?: string;
  message?: string;
  expiresIn?: number;
  remainingSeconds?: number;
  remainingAttempts?: number;
  botUsername?: string;
  sessionToken?: string;
  user?: {
    id: string;
    name: string;
    role: string;
    telegramUserId: number;
  };
}

const DEFAULT_BOT_USERNAME = "hermes_glamur_bot";

/**
 * Dispatches a message via Telegram Bot API
 */
export async function sendTelegramBotMessage(
  chatId: number | string,
  text: string,
  options?: { parseMode?: "HTML" | "Markdown" | "MarkdownV2"; disableNotification?: boolean }
): Promise<{ ok: boolean; description?: string; errorCode?: number }> {
  const token = process.env.TELEGRAM_BOT_TOKEN;
  if (!token) {
    console.warn("[AdminAuth] TELEGRAM_BOT_TOKEN not configured");
    return { ok: false, description: "TELEGRAM_BOT_TOKEN not configured" };
  }

  try {
    const res = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: chatId,
        text,
        parse_mode: options?.parseMode || "HTML",
        disable_notification: options?.disableNotification || false,
      }),
    });

    const data = (await res.json()) as { ok: boolean; description?: string; error_code?: number };
    return {
      ok: data.ok,
      description: data.description,
      errorCode: data.error_code,
    };
  } catch (err: any) {
    console.error("[AdminAuth] Error dispatching Telegram message:", err);
    return { ok: false, description: err?.message || "Network error" };
  }
}

/**
 * Requests a single-use 6-digit OTP dispatched to the user's Telegram
 */
export async function requestAdminOtp(telegramUserId: number): Promise<AdminAuthResult> {
  const db = getDb();

  // 1. Verify user exists and is active
  const [user] = await db
    .select()
    .from(adminUsers)
    .where(and(eq(adminUsers.telegramUserId, telegramUserId), eq(adminUsers.isActive, 1)))
    .limit(1);

  if (!user) {
    return {
      success: false,
      error: "unauthorized_user",
      message: "Tu ID de Telegram no está autorizado como administrador.",
    };
  }

  // 2. Cooldown check: 60 seconds between OTP requests
  const oneMinuteAgo = new Date(Date.now() - 60 * 1000);
  const [recentOtp] = await db
    .select()
    .from(adminOtps)
    .where(and(eq(adminOtps.userId, user.id), gt(adminOtps.createdAt, oneMinuteAgo)))
    .orderBy(desc(adminOtps.createdAt))
    .limit(1);

  if (recentOtp) {
    const elapsedSeconds = Math.floor((Date.now() - recentOtp.createdAt.getTime()) / 1000);
    const remaining = Math.max(1, 60 - elapsedSeconds);
    return {
      success: false,
      error: "cooldown_active",
      remainingSeconds: remaining,
      message: `Espera ${remaining} segundos antes de solicitar un nuevo código.`,
    };
  }

  // 3. Generate 6-digit cryptographic OTP
  const rawOtp = randomInt(100000, 1000000).toString();
  const codeHash = createHash("sha256").update(rawOtp).digest("hex");
  const expiresAt = new Date(Date.now() + 5 * 60 * 1000); // 5 minutes

  // Invalidate previous unconsumed OTPs
  await db
    .delete(adminOtps)
    .where(and(eq(adminOtps.userId, user.id), eq(adminOtps.consumedAt, null as any)));

  // 4. Save to DB
  await db.insert(adminOtps).values({
    userId: user.id,
    codeHash,
    attempts: 0,
    expiresAt,
  });

  // 5. Send via Telegram Bot API
  const message = `🔐 <b>Código de acceso al Panel /adminn</b>\n\nTu código de verificación es:\n<code>${rawOtp}</code>\n\n⏱️ Vence en 5 minutos. No lo compartas con nadie.`;
  const tgResult = await sendTelegramBotMessage(telegramUserId, message);

  if (!tgResult.ok) {
    if (tgResult.errorCode === 403) {
      return {
        success: false,
        error: "telegram_bot_not_started",
        botUsername: DEFAULT_BOT_USERNAME,
        message: `Primero debes iniciar una conversación con el bot de Telegram @${DEFAULT_BOT_USERNAME} enviando /start.`,
      };
    }
    return {
      success: false,
      error: "telegram_dispatch_failed",
      message: tgResult.description || "No se pudo enviar el mensaje por Telegram.",
    };
  }

  return {
    success: true,
    expiresIn: 300,
    message: "Código enviado correctamente a tu Telegram.",
  };
}

/**
 * Verifies the 6-digit OTP and creates an active 7-day session
 */
export async function verifyAdminOtp(
  telegramUserId: number,
  code: string,
  metadata?: { ip?: string; userAgent?: string }
): Promise<AdminAuthResult> {
  const db = getDb();

  const [user] = await db
    .select()
    .from(adminUsers)
    .where(and(eq(adminUsers.telegramUserId, telegramUserId), eq(adminUsers.isActive, 1)))
    .limit(1);

  if (!user) {
    return { success: false, error: "unauthorized_user" };
  }

  const now = new Date();
  const [otp] = await db
    .select()
    .from(adminOtps)
    .where(
      and(
        eq(adminOtps.userId, user.id),
        gt(adminOtps.expiresAt, now),
        eq(adminOtps.consumedAt, null as any)
      )
    )
    .orderBy(desc(adminOtps.createdAt))
    .limit(1);

  if (!otp) {
    return {
      success: false,
      error: "otp_expired_or_invalid",
      message: "El código ha expirado o no es válido. Solicita uno nuevo.",
    };
  }

  if (otp.attempts >= 5) {
    // Burn OTP after 5 failed attempts
    await db.update(adminOtps).set({ consumedAt: now }).where(eq(adminOtps.id, otp.id));
    return {
      success: false,
      error: "too_many_attempts",
      message: "Demasiados intentos fallidos. Solicita un nuevo código.",
    };
  }

  // Increment attempts
  await db
    .update(adminOtps)
    .set({ attempts: otp.attempts + 1 })
    .where(eq(adminOtps.id, otp.id));

  const providedHash = createHash("sha256").update(code.trim()).digest("hex");
  if (providedHash !== otp.codeHash) {
    const remaining = 5 - (otp.attempts + 1);
    return {
      success: false,
      error: "invalid_code",
      remainingAttempts: remaining,
      message: `Código incorrecto. Te quedan ${remaining} intentos.`,
    };
  }

  // Mark OTP as consumed
  await db.update(adminOtps).set({ consumedAt: now }).where(eq(adminOtps.id, otp.id));

  // Generate 7-day cryptographic session token
  const rawSessionToken = randomBytes(32).toString("hex");
  const sessionTokenHash = createHash("sha256").update(rawSessionToken).digest("hex");
  const sessionId = randomBytes(16).toString("hex");
  const sessionExpiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

  await db.insert(adminSessions).values({
    id: sessionId,
    userId: user.id,
    sessionTokenHash,
    expiresAt: sessionExpiresAt,
    ipAddress: metadata?.ip || null,
    userAgent: metadata?.userAgent || null,
  });

  // Silent audit alert to superadmins
  notifySuperadminAudit(
    `🔐 <b>Inicio de sesión en /adminn</b>\nUsuario: <b>${user.name}</b> (${user.role})\nTelegram ID: <code>${user.telegramUserId}</code>\nIP: <code>${metadata?.ip || "Desconocida"}</code>`
  ).catch(() => {});

  return {
    success: true,
    sessionToken: rawSessionToken,
    user: {
      id: user.id,
      name: user.name,
      role: user.role,
      telegramUserId: Number(user.telegramUserId),
    },
  };
}

/**
 * Validates a session cookie token against admin_sessions
 */
export async function validateAdminSession(sessionToken: string): Promise<AdminUser | null> {
  if (!sessionToken || sessionToken.trim() === "") return null;

  try {
    const db = getDb();
    const tokenHash = createHash("sha256").update(sessionToken.trim()).digest("hex");
    const now = new Date();

    const [session] = await db
      .select({
        session: adminSessions,
        user: adminUsers,
      })
      .from(adminSessions)
      .innerJoin(adminUsers, eq(adminSessions.userId, adminUsers.id))
      .where(
        and(
          eq(adminSessions.sessionTokenHash, tokenHash),
          gt(adminSessions.expiresAt, now),
          eq(adminUsers.isActive, 1)
        )
      )
      .limit(1);

    if (!session || !session.user) return null;
    return session.user;
  } catch (err) {
    console.error("[AdminAuth] Session validation error:", err);
    return null;
  }
}

/**
 * Revokes a session token
 */
export async function revokeAdminSession(sessionToken: string): Promise<boolean> {
  if (!sessionToken) return false;

  try {
    const db = getDb();
    const tokenHash = createHash("sha256").update(sessionToken.trim()).digest("hex");
    await db.delete(adminSessions).where(eq(adminSessions.sessionTokenHash, tokenHash));
    return true;
  } catch (err) {
    console.error("[AdminAuth] Session revocation error:", err);
    return false;
  }
}

/**
 * Sends a silent audit notification to all superadmins
 */
export async function notifySuperadminAudit(message: string): Promise<void> {
  try {
    const db = getDb();
    const superadmins = await db
      .select()
      .from(adminUsers)
      .where(and(eq(adminUsers.role, "superadmin"), eq(adminUsers.isActive, 1)));

    for (const sa of superadmins) {
      await sendTelegramBotMessage(sa.telegramUserId, message, {
        disableNotification: true,
      });
    }
  } catch (err) {
    console.error("[AdminAuth] Failed to send superadmin audit notification:", err);
  }
}
