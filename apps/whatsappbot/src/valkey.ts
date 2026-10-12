import Redis from "ioredis";

const valkeyUrl = process.env.VALKEY_URL || process.env.valkey_connectionString || "redis://valkey:6379";
export const redis = new Redis(valkeyUrl, {
  maxRetriesPerRequest: 3,
  retryStrategy(times) {
    return Math.min(times * 100, 3000);
  },
});

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: number;
}

export async function checkValkeyConnection(): Promise<boolean> {
  try {
    const pong = await redis.ping();
    return pong === "PONG";
  } catch (err) {
    console.error("[Valkey] Ping failed:", err);
    return false;
  }
}

export async function acquireLock(messageId: string): Promise<boolean> {
  if (!messageId) return true;
  const key = `lock:wa:${messageId}`;
  const res = await redis.set(key, "1", "EX", 45, "NX");
  return res === "OK";
}

export async function checkRateLimit(phone: string, limit = 10, windowSecs = 60): Promise<boolean> {
  const key = `ratelimit:wa:${phone}`;
  const count = await redis.incr(key);
  if (count === 1) {
    await redis.expire(key, windowSecs);
  }
  return count <= limit;
}

export async function linkPhoneAndLid(phone: string, lid: string): Promise<void> {
  const cleanPhone = phone.replace(/\D/g, "");
  const cleanLid = lid.replace(/\D/g, "");
  if (!cleanPhone || !cleanLid || cleanPhone === cleanLid) return;

  await Promise.all([
    redis.set(`wa:map:lid:${cleanLid}`, cleanPhone, "EX", 2592000),
    redis.set(`wa:map:phone:${cleanPhone}`, cleanLid, "EX", 2592000),
  ]);
}

export async function resolveCanonicalPhone(phoneOrLid: string): Promise<string> {
  const clean = phoneOrLid.replace(/\D/g, "");
  if (!clean) return "";

  if (clean.length > 13) {
    const mappedPhone = await redis.get(`wa:map:lid:${clean}`);
    if (mappedPhone) return mappedPhone;
  }

  return clean;
}

export async function getRelatedIdentifiers(phoneOrLid: string): Promise<string[]> {
  const clean = phoneOrLid.replace(/\D/g, "");
  if (!clean) return [];

  const ids = new Set<string>([clean]);
  
  const phone = await redis.get(`wa:map:lid:${clean}`);
  if (phone) ids.add(phone);

  const lid = await redis.get(`wa:map:phone:${clean}`);
  if (lid) ids.add(lid);

  return Array.from(ids);
}

export async function isHumanTakeover(phoneOrLid: string): Promise<boolean> {
  const relatedIds = await getRelatedIdentifiers(phoneOrLid);
  if (relatedIds.length === 0) return false;

  const keys = relatedIds.map((id) => `wa:human_takeover:${id}`);
  const results = await redis.mget(...keys);
  return results.some((val) => val === "1");
}

export async function setHumanTakeover(phoneOrLid: string, durationSecs = 7200): Promise<void> {
  const relatedIds = await getRelatedIdentifiers(phoneOrLid);
  const pipeline = redis.pipeline();
  for (const id of relatedIds) {
    pipeline.set(`wa:human_takeover:${id}`, "1", "EX", durationSecs);
  }
  await pipeline.exec();
}

export async function clearHumanTakeover(phoneOrLid: string): Promise<void> {
  const relatedIds = await getRelatedIdentifiers(phoneOrLid);
  const pipeline = redis.pipeline();
  for (const id of relatedIds) {
    pipeline.del(`wa:human_takeover:${id}`);
  }
  await pipeline.exec();
}

export async function isAffiliatePitched(phone: string): Promise<boolean> {
  const key = `wa:affiliate_pitched:${phone}`;
  const val = await redis.get(key);
  return val === "1";
}

export async function setAffiliatePitched(phone: string, durationSecs = 604800): Promise<void> {
  const key = `wa:affiliate_pitched:${phone}`;
  await redis.set(key, "1", "EX", durationSecs);
}

export async function getSessionHistory(phone: string, limit = 20): Promise<ChatMessage[]> {
  const key = `chat:sessions:${phone}`;
  const rawList = await redis.lrange(key, 0, limit - 1);
  return rawList
    .map((item) => {
      try {
        return JSON.parse(item) as ChatMessage;
      } catch {
        return null;
      }
    })
    .filter((m): m is ChatMessage => m !== null)
    .reverse();
}

export async function appendSessionMessage(phone: string, role: "user" | "assistant", content: string): Promise<void> {
  const key = `chat:sessions:${phone}`;
  const payload = JSON.stringify({
    role,
    content,
    timestamp: Date.now(),
  });
  await redis.lpush(key, payload);
  await redis.ltrim(key, 0, 19); // Keep last 20 messages
  await redis.expire(key, 86400 * 7); // 7 days retention
}
