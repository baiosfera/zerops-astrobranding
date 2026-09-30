import { pgTable, uuid, text, timestamp, jsonb, vector, index, integer, uniqueIndex } from "drizzle-orm/pg-core";
import { sql } from "drizzle-orm";

export const clients = pgTable("clients", {
  id: uuid("id").default(sql`uuidv7()`).primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  phone: text("phone").notNull(),
  birthDate: text("birth_date").notNull(),
  birthTime: text("birth_time").notNull(),
  birthCity: text("birth_city").notNull(),
  birthCountry: text("birth_country").notNull(),
  latitude: text("latitude"),
  longitude: text("longitude"),
  status: text("status").default("active").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

/**
 * 15-Shard Omni Master Manifest Lakehouse Table (Tier 1 Bronze Dumps)
 * SSoT defined in /var/www/artifacts/omni_shards_master_manifest.md
 */
export const clientDumps = pgTable(
  "client_dumps",
  {
    id: uuid("id").default(sql`uuidv7()`).primaryKey(),
    clientId: uuid("client_id")
      .references(() => clients.id, { onDelete: "cascade" })
      .notNull(),
    birthMetadata: jsonb("birth_metadata").notNull(),
    shardWesternTropical: jsonb("shard_western_tropical").notNull(),
    shardWesternSidereal: jsonb("shard_western_sidereal").notNull(),
    shardVedicJyotish: jsonb("shard_vedic_jyotish").notNull(),
    shardVedicDashas: jsonb("shard_vedic_dashas").notNull(),
    shardBaziMetaphysics: jsonb("shard_bazi_metaphysics").notNull(),
    shardZiweiFengshui: jsonb("shard_ziwei_fengshui").notNull(),
    shardKabbalahGematria: jsonb("shard_kabbalah_gematria").notNull(),
    shardHebrewZmanim: jsonb("shard_hebrew_zmanim").notNull(),
    shardHumanDesign: jsonb("shard_human_design").notNull(),
    shardCosmobiologyMidpoints: jsonb("shard_cosmobiology_midpoints").notNull(),
    shardNasaEphemerides: jsonb("shard_nasa_ephemerides").notNull(),
    shardAstrocartographyAcg: jsonb("shard_astrocartography_acg").notNull(),
    shardBusinessPentaOrg: jsonb("shard_business_penta_org").notNull(),
    shardPartnerSynastry: jsonb("shard_partner_synastry").notNull(),
    shardPredictiveElectional: jsonb("shard_predictive_electional").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    index("client_dumps_client_id_idx").on(table.clientId),
  ]
);

/**
 * Gold Feeds Table (Tier 2 Gold Projections <1.5 KB XML)
 * Feeding specialized sub-oracles without context degradation
 */
export const clientFeeds = pgTable(
  "client_feeds",
  {
    id: uuid("id").default(sql`uuidv7()`).primaryKey(),
    clientId: uuid("client_id")
      .references(() => clients.id, { onDelete: "cascade" })
      .notNull(),
    feedType: text("feed_type").notNull(), // diag_a_psy, diag_b_voc, diag_c_mkt, diag_d_leg, diag_e_geo
    xmlPayload: text("xml_payload").notNull(),
    tokenEstimate: integer("token_estimate").default(0).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    index("client_feeds_client_id_feed_type_idx").on(table.clientId, table.feedType),
  ]
);

/**
 * Leads & Funnel Opt-In Table (WhatsApp OTP + Email Progressive)
 */
export const leads = pgTable(
  "leads",
  {
    id: uuid("id").default(sql`uuidv7()`).primaryKey(),
    phone: text("phone").notNull(),
    email: text("email"),
    name: text("name"),
    otpCode: text("otp_code"),
    otpExpiresAt: timestamp("otp_expires_at", { withTimezone: true }),
    status: text("status").default("unverified").notNull(), // unverified | verified_phone | verified_email | converted
    crmLeadId: text("crm_lead_id"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    uniqueIndex("leads_phone_idx").on(table.phone),
  ]
);

export const analyses = pgTable(
  "analyses",
  {
    id: uuid("id").default(sql`uuidv7()`).primaryKey(),
    clientId: uuid("client_id")
      .references(() => clients.id, { onDelete: "cascade" })
      .notNull(),
    chartData: jsonb("chart_data").notNull(),
    archetype: text("archetype"),
    strategicSummary: text("strategic_summary"),
    brandingRecommendations: jsonb("branding_recommendations"),
    embedding: vector("embedding", { dimensions: 1536 }),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    index("analyses_embedding_hnsw_idx").using("hnsw", table.embedding.op("vector_cosine_ops")),
    index("analyses_client_id_idx").on(table.clientId),
  ]
);

export const orders = pgTable("orders", {
  id: uuid("id").default(sql`uuidv7()`).primaryKey(),
  clientId: uuid("client_id")
    .references(() => clients.id)
    .notNull(),
  amount: text("amount").notNull(),
  currency: text("currency").default("USD").notNull(),
  status: text("status").default("pending").notNull(),
  paymentRef: text("payment_ref"),
  dianCufe: text("dian_cufe"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

/**
 * TaskOutbox: Transactional Outbox Pattern in PostgreSQL 18
 * Adapted from di-sukharev/vibe with native UUIDv7 and skipDuplicates
 */
export const taskOutbox = pgTable(
  "task_outbox",
  {
    id: uuid("id").default(sql`uuidv7()`).primaryKey(),
    type: text("type").notNull(),
    dedupeKey: text("dedupe_key"),
    payload: jsonb("payload").default({}).notNull(),
    status: text("status").default("pending").notNull(), // pending | processing | done | skipped | failed
    attempts: integer("attempts").default(0).notNull(),
    scheduledFor: timestamp("scheduled_for", { withTimezone: true }).defaultNow().notNull(),
    processingToken: text("processing_token"),
    processedAt: timestamp("processed_at", { withTimezone: true }),
    redactedAt: timestamp("redacted_at", { withTimezone: true }),
    lastError: text("last_error"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    uniqueIndex("task_outbox_type_dedupe_key_idx").on(table.type, table.dedupeKey),
    index("task_outbox_status_scheduled_for_idx").on(table.status, table.scheduledFor),
  ]
);

export type Client = typeof clients.$inferSelect;
export type NewClient = typeof clients.$inferInsert;
export type ClientDumps = typeof clientDumps.$inferSelect;
export type NewClientDumps = typeof clientDumps.$inferInsert;
export type ClientFeeds = typeof clientFeeds.$inferSelect;
export type NewClientFeeds = typeof clientFeeds.$inferInsert;
export type Lead = typeof leads.$inferSelect;
export type NewLead = typeof leads.$inferInsert;
export type Analysis = typeof analyses.$inferSelect;
export type NewAnalysis = typeof analyses.$inferInsert;
export type Order = typeof orders.$inferSelect;
export type NewOrder = typeof orders.$inferInsert;
export type TaskOutboxRecord = typeof taskOutbox.$inferSelect;
export type NewTaskOutboxRecord = typeof taskOutbox.$inferInsert;

/**
 * Normalized Client Shards Table (Decoupled Agnostic Multi-Domain Store)
 * Supports dynamic sharding across any vertical (astrology, commerce, CRM, branding)
 */
export const clientShards = pgTable(
  "client_shards",
  {
    id: uuid("id").default(sql`uuidv7()`).primaryKey(),
    clientId: uuid("client_id")
      .references(() => clients.id, { onDelete: "cascade" })
      .notNull(),
    shardType: text("shard_type").notNull(),
    payload: jsonb("payload").default({}).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    uniqueIndex("client_shards_client_id_shard_type_idx").on(table.clientId, table.shardType),
    index("client_shards_shard_type_idx").on(table.shardType),
  ]
);

export type ClientShard = typeof clientShards.$inferSelect;
export type NewClientShard = typeof clientShards.$inferInsert;

