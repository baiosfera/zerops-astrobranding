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

export async function isHumanTakeover(phone: string): Promise<boolean> {
  const key = `wa:human_takeover:${phone}`;
  const val = await redis.get(key);
  return val === "1";
}

export async function setHumanTakeover(phone: string, durationSecs = 7200): Promise<void> {
  const key = `wa:human_takeover:${phone}`;
  await redis.set(key, "1", "EX", durationSecs);
}

export async function clearHumanTakeover(phone: string): Promise<void> {
  const key = `wa:human_takeover:${phone}`;
  await redis.del(key);
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
