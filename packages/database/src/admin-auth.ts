import { createHash, randomBytes, randomInt, pbkdf2Sync, timingSafeEqual } from "crypto";
import { eq, or, and, gt, desc, isNull } from "drizzle-orm";
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
    telegramUserId?: number;
    username?: string | null;
    email?: string | null;
  };
}

const DEFAULT_BOT_USERNAME = "hermes_glamur_bot";

/**
 * Hashes a plaintext password using PBKDF2 with SHA-512 and a random 16-byte salt
 */
export function hashPassword(password: string): string {
  const salt = randomBytes(16);
  const hash = pbkdf2Sync(password, salt, 100000, 64, "sha512").toString("hex");
  return `pbkdf2:100000:${salt.toString("hex")}:${hash}`;
}

/**
 * Timing-safe password verification against stored PBKDF2 hash
 */
export function verifyPassword(password: string, storedHash: string): boolean {
  if (!storedHash || !storedHash.startsWith("pbkdf2:")) return false;
  const parts = storedHash.split(":");
  if (parts.length !== 4) return false;
  const iterations = parseInt(parts[1], 10);
  const salt = Buffer.from(parts[2], "hex");
  const originalHash = parts[3];
  try {
    const computed = pbkdf2Sync(password, salt, iterations, 64, "sha512").toString("hex");
    return timingSafeEqual(Buffer.from(computed, "hex"), Buffer.from(originalHash, "hex"));
  } catch {
    return false;
  }
}

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
 * 1. PATH: Username/Email and Password Authentication
 */
export async function loginWithAdminPassword(
  identifier: string,
  password: string,
  metadata?: { ip?: string; userAgent?: string }
): Promise<AdminAuthResult> {
  const db = getDb();
  const trimmed = identifier.trim().toLowerCase();

  const [user] = await db
    .select()
    .from(adminUsers)
    .where(
      and(
        or(eq(adminUsers.username, trimmed), eq(adminUsers.email, trimmed)),
        eq(adminUsers.isActive, 1)
      )
    )
    .limit(1);

  if (!user || !user.passwordHash) {
    return {
      success: false,
      error: "invalid_credentials",
      message: "Usuario o contraseña incorrectos.",
    };
  }

  const isValid = verifyPassword(password, user.passwordHash);
  if (!isValid) {
    return {
      success: false,
      error: "invalid_credentials",
      message: "Usuario o contraseña incorrectos.",
    };
  }

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

  notifySuperadminAudit(
    `🔐 <b>Inicio de sesión en /adminn (Contraseña)</b>\nUsuario: <b>${user.name}</b> (${user.role})\nIdentificador: <code>${identifier}</code>\nIP: <code>${metadata?.ip || "Desconocida"}</code>`
  ).catch(() => {});

  return {
    success: true,
    sessionToken: rawSessionToken,
    user: {
      id: user.id,
      name: user.name,
      role: user.role,
      telegramUserId: user.telegramUserId ? Number(user.telegramUserId) : undefined,
      username: user.username,
      email: user.email,
    },
  };
}

/**
 * 2. PATH: Requests a single-use 6-digit OTP dispatched to Telegram
 */
export async function requestAdminOtp(telegramUserId: number): Promise<AdminAuthResult> {
  const db = getDb();

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

  const rawOtp = randomInt(100000, 1000000).toString();
  const codeHash = createHash("sha256").update(rawOtp).digest("hex");
  const expiresAt = new Date(Date.now() + 5 * 60 * 1000); // 5 minutes

  await db
    .delete(adminOtps)
    .where(and(eq(adminOtps.userId, user.id), isNull(adminOtps.consumedAt)));

  await db.insert(adminOtps).values({
    userId: user.id,
    codeHash,
    attempts: 0,
    expiresAt,
  });

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
 * 2. PATH: Verifies the 6-digit Telegram OTP and creates an active 7-day session
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
        isNull(adminOtps.consumedAt)
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
    await db.update(adminOtps).set({ consumedAt: now }).where(eq(adminOtps.id, otp.id));
    return {
      success: false,
      error: "too_many_attempts",
      message: "Demasiados intentos fallidos. Solicita un nuevo código.",
    };
  }

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

  await db.update(adminOtps).set({ consumedAt: now }).where(eq(adminOtps.id, otp.id));

  const rawSessionToken = randomBytes(32).toString("hex");
  const sessionTokenHash = createHash("sha256").update(rawSessionToken).digest("hex");
  const sessionId = randomBytes(16).toString("hex");
  const sessionExpiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

  await db.insert(adminSessions).values({
    id: sessionId,
    userId: user.id,
    sessionTokenHash,
    expiresAt: sessionExpiresAt,
    ipAddress: metadata?.ip || null,
    userAgent: metadata?.userAgent || null,
  });

  notifySuperadminAudit(
    `🔐 <b>Inicio de sesión en /adminn (Telegram OTP)</b>\nUsuario: <b>${user.name}</b> (${user.role})\nTelegram ID: <code>${user.telegramUserId}</code>\nIP: <code>${metadata?.ip || "Desconocida"}</code>`
  ).catch(() => {});

  return {
    success: true,
    sessionToken: rawSessionToken,
    user: {
      id: user.id,
      name: user.name,
      role: user.role,
      telegramUserId: user.telegramUserId ? Number(user.telegramUserId) : undefined,
    },
  };
}

/**
 * 3. PATH: Requests a single-use 6-digit OTP dispatched to WhatsApp via Evolution API
 */
export async function requestAdminWhatsAppOtp(phone: string): Promise<AdminAuthResult> {
  const db = getDb();
  const cleanPhone = phone.replace(/\D/g, "");

  const users = await db
    .select()
    .from(adminUsers)
    .where(eq(adminUsers.isActive, 1));

  const user = users.find((u) => {
    if (!u.phone) return false;
    const uClean = u.phone.replace(/\D/g, "");
    return uClean.endsWith(cleanPhone) || cleanPhone.endsWith(uClean);
  });

  if (!user) {
    return {
      success: false,
      error: "unauthorized_user",
      message: "El número de teléfono no está autorizado como administrador.",
    };
  }

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

  const rawOtp = randomInt(100000, 1000000).toString();
  const codeHash = createHash("sha256").update(rawOtp).digest("hex");
  const expiresAt = new Date(Date.now() + 5 * 60 * 1000);

  await db.insert(adminOtps).values({
    userId: user.id,
    codeHash,
    attempts: 0,
    expiresAt,
  });

  const evolutionUrl = process.env.EVOLUTION_URL || "http://evolution:8085";
  const apiKey = process.env.EVOLUTION_API_KEY || "";
  const targetNumber = cleanPhone.length === 10 ? `57${cleanPhone}` : cleanPhone;
  const message = `🔐 *Código de acceso al Panel /adminn*\n\nTu código de verificación es:\n*${rawOtp}*\n\n⏱️ Vence en 5 minutos. No lo compartas con nadie.`;

  try {
    const res = await fetch(`${evolutionUrl}/send/text`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(apiKey ? { apikey: apiKey } : {}),
      },
      body: JSON.stringify({
        number: targetNumber,
        text: message,
      }),
      signal: AbortSignal.timeout(8000),
    });

    if (!res.ok) {
      console.warn(`[AdminAuth] Evolution HTTP ${res.status}`);
    }
  } catch (err: any) {
    console.error("[AdminAuth] Evolution dispatch error:", err);
  }

  return {
    success: true,
    expiresIn: 300,
    message: "Código enviado a tu WhatsApp.",
  };
}

/**
 * 3. PATH: Verifies the 6-digit WhatsApp OTP and creates an active 7-day session
 */
export async function verifyAdminWhatsAppOtp(
  phone: string,
  code: string,
  metadata?: { ip?: string; userAgent?: string }
): Promise<AdminAuthResult> {
  const db = getDb();
  const cleanPhone = phone.replace(/\D/g, "");

  const users = await db
    .select()
    .from(adminUsers)
    .where(eq(adminUsers.isActive, 1));

  const user = users.find((u) => {
    if (!u.phone) return false;
    const uClean = u.phone.replace(/\D/g, "");
    return uClean.endsWith(cleanPhone) || cleanPhone.endsWith(uClean);
  });

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
        isNull(adminOtps.consumedAt)
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
    await db.update(adminOtps).set({ consumedAt: now }).where(eq(adminOtps.id, otp.id));
    return {
      success: false,
      error: "too_many_attempts",
      message: "Demasiados intentos fallidos. Solicita un nuevo código.",
    };
  }

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

  await db.update(adminOtps).set({ consumedAt: now }).where(eq(adminOtps.id, otp.id));

  const rawSessionToken = randomBytes(32).toString("hex");
  const sessionTokenHash = createHash("sha256").update(rawSessionToken).digest("hex");
  const sessionId = randomBytes(16).toString("hex");
  const sessionExpiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

  await db.insert(adminSessions).values({
    id: sessionId,
    userId: user.id,
    sessionTokenHash,
    expiresAt: sessionExpiresAt,
    ipAddress: metadata?.ip || null,
    userAgent: metadata?.userAgent || null,
  });

  notifySuperadminAudit(
    `🔐 <b>Inicio de sesión en /adminn (WhatsApp OTP)</b>\nUsuario: <b>${user.name}</b> (${user.role})\nTeléfono: <code>${user.phone}</code>\nIP: <code>${metadata?.ip || "Desconocida"}</code>`
  ).catch(() => {});

  return {
    success: true,
    sessionToken: rawSessionToken,
    user: {
      id: user.id,
      name: user.name,
      role: user.role,
      telegramUserId: user.telegramUserId ? Number(user.telegramUserId) : undefined,
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
      if (sa.telegramUserId) {
        await sendTelegramBotMessage(sa.telegramUserId, message, {
          disableNotification: true,
        });
      }
    }
  } catch (err) {
    console.error("[AdminAuth] Failed to send superadmin audit notification:", err);
  }
}

/**
 * 4. PATH: 1-Click Telegram Magic Login Link (Zero-typing, instant auth)
 */
export async function createTelegramMagicLinkToken(
  telegramUserId: number
): Promise<{ success: boolean; token?: string; error?: string }> {
  const db = getDb();
  const [user] = await db
    .select()
    .from(adminUsers)
    .where(and(eq(adminUsers.telegramUserId, telegramUserId), eq(adminUsers.isActive, 1)))
    .limit(1);

  if (!user) {
    return { success: false, error: "unauthorized_user" };
  }

  const rawToken = randomBytes(24).toString("hex");
  const tokenHash = createHash("sha256").update(rawToken).digest("hex");
  const expiresAt = new Date(Date.now() + 10 * 60 * 1000); // 10 minutes

  await db.insert(adminOtps).values({
    userId: user.id,
    codeHash: tokenHash,
    attempts: 0,
    expiresAt,
  });

  return { success: true, token: rawToken };
}

/**
 * Validates and consumes the 1-click magic login token, returning an active 7-day session token
 */
export async function consumeMagicLoginToken(
  rawToken: string,
  metadata?: { ip?: string; userAgent?: string }
): Promise<AdminAuthResult> {
  if (!rawToken || rawToken.trim().length < 16) {
    return { success: false, error: "invalid_token" };
  }

  const db = getDb();
  const tokenHash = createHash("sha256").update(rawToken.trim()).digest("hex");
  const now = new Date();

  const [otp] = await db
    .select({
      otp: adminOtps,
      user: adminUsers,
    })
    .from(adminOtps)
    .innerJoin(adminUsers, eq(adminOtps.userId, adminUsers.id))
    .where(
      and(
        eq(adminOtps.codeHash, tokenHash),
        gt(adminOtps.expiresAt, now),
        isNull(adminOtps.consumedAt),
        eq(adminUsers.isActive, 1)
      )
    )
    .limit(1);

  if (!otp || !otp.user) {
    return {
      success: false,
      error: "invalid_or_expired_token",
      message: "El enlace mágico ha expirado o ya fue utilizado.",
    };
  }

  // Invalidate OTP (single-use)
  await db.update(adminOtps).set({ consumedAt: now }).where(eq(adminOtps.id, otp.otp.id));

  // Generate 7-day cryptographic session
  const rawSessionToken = randomBytes(32).toString("hex");
  const sessionTokenHash = createHash("sha256").update(rawSessionToken).digest("hex");
  const sessionId = randomBytes(16).toString("hex");
  const sessionExpiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

  await db.insert(adminSessions).values({
    id: sessionId,
    userId: otp.user.id,
    sessionTokenHash,
    expiresAt: sessionExpiresAt,
    ipAddress: metadata?.ip || null,
    userAgent: metadata?.userAgent || null,
  });

  notifySuperadminAudit(
    `🔐 <b>Inicio de sesión en /adminn (1-Clic Telegram)</b>\nUsuario: <b>${otp.user.name}</b> (${otp.user.role})\nIP: <code>${metadata?.ip || "Desconocida"}</code>`
  ).catch(() => {});

  return {
    success: true,
    sessionToken: rawSessionToken,
    user: {
      id: otp.user.id,
      name: otp.user.name,
      role: otp.user.role,
      telegramUserId: otp.user.telegramUserId ? Number(otp.user.telegramUserId) : undefined,
      username: otp.user.username,
      email: otp.user.email,
    },
  };
}
