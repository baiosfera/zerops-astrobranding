import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import * as schema from "./schema";

export const DATABASE_VERSION = "1.0.0";
export * from "./schema";
export * from "./outbox-drain";
export { eq, sql } from "drizzle-orm";

let _queryClient: ReturnType<typeof postgres> | null = null;
let _db: ReturnType<typeof drizzle> | null = null;

export function getQueryClient() {
  if (!_queryClient) {
    const connectionString = process.env.DATABASE_URL || "postgres://postgres:postgres@localhost:5432/astrobranding";
    _queryClient = postgres(connectionString, {
      max: 10,
      idle_timeout: 20,
      connect_timeout: 10,
      onnotice: () => {},
    });
  }
  return _queryClient;
}

export function getDb() {
  if (!_db) {
    _db = drizzle(getQueryClient(), { schema });
  }
  return _db;
}

// Transparent Proxy for backwards compatibility and zero-crash evaluation
export const db = new Proxy({} as ReturnType<typeof drizzle<typeof schema>>, {
  get(_target, prop) {
    const instance = getDb();
    const value = Reflect.get(instance, prop);
    return typeof value === "function" ? value.bind(instance) : value;
  },
});

export async function checkDatabaseConnection(): Promise<boolean> {
  try {
    const client = getQueryClient();
    await client`SELECT 1`;
    return true;
  } catch (error) {
    console.error("[Database] Connection check failed:", error);
    return false;
  }
}

export async function initPgVector(): Promise<void> {
  try {
    const client = getQueryClient();
    await client`CREATE EXTENSION IF NOT EXISTS vector;`;
    console.log("[Database] pgvector extension initialized successfully");
  } catch (error) {
    console.error("[Database] Failed to initialize pgvector extension:", error);
  }
}
