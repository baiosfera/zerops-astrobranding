import { pgTable, uuid, text, timestamp, jsonb, index, integer, uniqueIndex, bigint } from "drizzle-orm/pg-core";
import { sql } from "drizzle-orm";

/**
 * 1. Users (Better Auth Compatible)
 */
export const users = pgTable("users", {
  id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  phone: text("phone"),
  emailVerified: integer("email_verified").default(0).notNull(),
  image: text("image"),
  role: text("role").default("customer").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

export const sessions = pgTable("sessions", {
  id: text("id").primaryKey(),
  userId: uuid("user_id").references(() => users.id, { onDelete: "cascade" }).notNull(),
  token: text("token").notNull().unique(),
  expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
  ipAddress: text("ip_address"),
  userAgent: text("user_agent"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

export const accounts = pgTable("accounts", {
  id: text("id").primaryKey(),
  userId: uuid("user_id").references(() => users.id, { onDelete: "cascade" }).notNull(),
  accountId: text("account_id").notNull(),
  providerId: text("provider_id").notNull(),
  accessToken: text("access_token"),
  refreshToken: text("refresh_token"),
  expiresAt: timestamp("expires_at", { withTimezone: true }),
  password: text("password"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

export const verifications = pgTable("verifications", {
  id: text("id").primaryKey(),
  identifier: text("identifier").notNull(),
  value: text("value").notNull(),
  expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

/**
 * 2. Clients
 */
export const clients = pgTable("clients", {
  id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  phone: text("phone").notNull(),
  birthDate: text("birth_date").default(""),
  birthTime: text("birth_time").default(""),
  birthCity: text("birth_city").default(""),
  birthCountry: text("birth_country").default(""),
  latitude: text("latitude"),
  longitude: text("longitude"),
  status: text("status").default("active").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

/**
 * 3. Client Dumps (15-Shard Data Lakehouse)
 */
export const clientDumps = pgTable(
  "client_dumps",
  {
    id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
    clientId: uuid("client_id")
      .references(() => clients.id, { onDelete: "cascade" })
      .notNull(),
    birthMetadata: jsonb("birth_metadata").default({}).notNull(),
    shardWesternTropical: jsonb("shard_western_tropical").default({}).notNull(),
    shardWesternSidereal: jsonb("shard_western_sidereal").default({}).notNull(),
    shardVedicJyotish: jsonb("shard_vedic_jyotish").default({}).notNull(),
    shardVedicDashas: jsonb("shard_vedic_dashas").default({}).notNull(),
    shardBaziMetaphysics: jsonb("shard_bazi_metaphysics").default({}).notNull(),
    shardZiweiFengshui: jsonb("shard_ziwei_fengshui").default({}).notNull(),
    shardKabbalahGematria: jsonb("shard_kabbalah_gematria").default({}).notNull(),
    shardHebrewZmanim: jsonb("shard_hebrew_zmanim").default({}).notNull(),
    shardHumanDesign: jsonb("shard_human_design").default({}).notNull(),
    shardCosmobiologyMidpoints: jsonb("shard_cosmobiology_midpoints").default({}).notNull(),
    shardNasaEphemerides: jsonb("shard_nasa_ephemerides").default({}).notNull(),
    shardAstrocartographyAcg: jsonb("shard_astrocartography_acg").default({}).notNull(),
    shardBusinessPentaOrg: jsonb("shard_business_penta_org").default({}).notNull(),
    shardPartnerSynastry: jsonb("shard_partner_synastry").default({}).notNull(),
    shardPredictiveElectional: jsonb("shard_predictive_electional").default({}).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    index("client_dumps_client_id_idx").on(table.clientId),
  ]
);

/**
 * 4. Client Feeds (Gold Feeds)
 */
export const clientFeeds = pgTable(
  "client_feeds",
  {
    id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
    clientId: uuid("client_id")
      .references(() => clients.id, { onDelete: "cascade" })
      .notNull(),
    feedType: text("feed_type").notNull(),
    xmlPayload: text("xml_payload").notNull(),
    tokenEstimate: integer("token_estimate").default(0).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    index("client_feeds_client_id_feed_type_idx").on(table.clientId, table.feedType),
  ]
);

/**
 * 5. Analyses
 */
export const analyses = pgTable(
  "analyses",
  {
    id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
    clientId: uuid("client_id")
      .references(() => clients.id, { onDelete: "cascade" })
      .notNull(),
    chartData: jsonb("chart_data").default({}).notNull(),
    archetype: text("archetype"),
    strategicSummary: text("strategic_summary"),
    brandingRecommendations: jsonb("branding_recommendations"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    index("analyses_client_id_idx").on(table.clientId),
  ]
);

/**
 * 6. Leads (WhatsApp OTP Funnel)
 */
export const leads = pgTable(
  "leads",
  {
    id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
    phone: text("phone").notNull(),
    email: text("email"),
    name: text("name"),
    otpCode: text("otp_code"),
    otpExpiresAt: timestamp("otp_expires_at", { withTimezone: true }),
    status: text("status").default("unverified").notNull(),
    crmLeadId: text("crm_lead_id"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    uniqueIndex("leads_phone_idx").on(table.phone),
  ]
);

/**
 * 7. Products & Variants (Catalina Glamur Activewear)
 */
export const products = pgTable(
  "products",
  {
    id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
    slug: text("slug").notNull(),
    name: text("name").notNull(),
    description: text("description"),
    category: text("category").notNull(),
    basePrice: integer("base_price").notNull(),
    images: jsonb("images").default([]).notNull(),
    isActive: integer("is_active").default(1).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    index("products_slug_idx").on(table.slug),
    uniqueIndex("products_slug_active_unique").on(table.slug).where(sql`is_active = 1`),
    index("products_category_idx").on(table.category),
  ]
);

export const productVariants = pgTable("product_variants", {
  id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
  productId: uuid("product_id").references(() => products.id, { onDelete: "cascade" }).notNull(),
  sku: text("sku").notNull().unique(),
  size: text("size").notNull(),
  color: text("color").notNull(),
  price: integer("price").notNull(),
  stock: integer("stock").default(0).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

/**
 * 8. Services (Catalina Glamur Aesthetics)
 */
export const services = pgTable(
  "services",
  {
    id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
    slug: text("slug").notNull(),
    name: text("name").notNull(),
    description: text("description"),
    durationMinutes: integer("duration_minutes").default(60).notNull(),
    price: integer("price").notNull(),
    depositRequired: integer("deposit_required").default(0).notNull(),
    depositAmount: integer("deposit_amount").default(0).notNull(),
    imageUrl: text("image_url"),
    priceRange: text("price_range"),
    badge: text("badge"),
    isActive: integer("is_active").default(1).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    index("services_slug_idx").on(table.slug),
    uniqueIndex("services_slug_active_unique").on(table.slug).where(sql`is_active = 1`),
  ]
);

/**
 * 9. Bookings (Google Calendar Adapter Ready)
 */
export const bookings = pgTable("bookings", {
  id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
  customerName: text("customer_name").notNull(),
  customerEmail: text("customer_email").notNull(),
  customerPhone: text("customer_phone").notNull(),
  serviceName: text("service_name").notNull(),
  appointmentDate: timestamp("appointment_date", { withTimezone: true }).notNull(),
  status: text("status").default("pending").notNull(),
  paymentType: text("payment_type").default("full").notNull(),
  depositAmount: integer("deposit_amount").default(0).notNull(),
  totalAmount: integer("total_amount").notNull(),
  paymentStatus: text("payment_status").default("pending").notNull(),
  googleCalendarEventId: text("google_calendar_event_id"),
  notes: text("notes"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

/**
 * 10. Orders & Order Items
 */
export const orders = pgTable("orders", {
  id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
  clientId: uuid("client_id").references(() => clients.id, { onDelete: "set null" }),
  customerName: text("customer_name").default("Guest").notNull(),
  customerEmail: text("customer_email"),
  customerPhone: text("customer_phone").default("").notNull(),
  shippingAddress: text("shipping_address"),
  shippingCity: text("shipping_city"),
  shippingDepartment: text("shipping_department"),
  daneCode: text("dane_code"),
  amount: text("amount"),
  totalAmount: integer("total_amount").default(0).notNull(),
  currency: text("currency").default("COP").notNull(),
  paymentMethod: text("payment_method").default("wompi").notNull(),
  paymentRef: text("payment_ref"),
  status: text("status").default("pending").notNull(),
  dianCufe: text("dian_cufe"),
  notes: text("notes"),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

export const orderItems = pgTable("order_items", {
  id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
  orderId: uuid("order_id").references(() => orders.id, { onDelete: "cascade" }).notNull(),
  productId: uuid("product_id").references(() => products.id).notNull(),
  variantId: uuid("variant_id").references(() => productVariants.id),
  quantity: integer("quantity").default(1).notNull(),
  unitPrice: integer("unit_price").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

/**
 * 11. Inventory Locks
 */
export const inventoryLocks = pgTable("inventory_locks", {
  id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
  variantId: uuid("variant_id").references(() => productVariants.id, { onDelete: "cascade" }).notNull(),
  orderId: uuid("order_id").references(() => orders.id, { onDelete: "cascade" }),
  quantity: integer("quantity").notNull(),
  expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
});

/**
 * 12. Task Outbox
 */
export const taskOutbox = pgTable(
  "task_outbox",
  {
    id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
    type: text("type").notNull(),
    dedupeKey: text("dedupe_key"),
    payload: jsonb("payload").default({}).notNull(),
    status: text("status").default("pending").notNull(),
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

/**
 * 13. Admin Users (Stealth Admin & Telegram Gateway RBAC)
 */
export const adminUsers = pgTable(
  "admin_users",
  {
    id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
    name: text("name").notNull(),
    username: text("username").unique(),
    email: text("email").unique(),
    passwordHash: text("password_hash"),
    phone: text("phone"),
    telegramUserId: bigint("telegram_user_id", { mode: "number" }).unique(),
    role: text("role").default("merchant").notNull(), // 'superadmin' | 'merchant'
    isActive: integer("is_active").default(1).notNull(),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    index("admin_users_telegram_idx").on(table.telegramUserId),
    index("admin_users_username_idx").on(table.username),
    index("admin_users_email_idx").on(table.email),
    index("admin_users_phone_idx").on(table.phone),
  ]
);

/**
 * 14. Admin OTPs (Single-use Cryptographic OTPs)
 */
export const adminOtps = pgTable(
  "admin_otps",
  {
    id: uuid("id").default(sql`gen_random_uuid()`).primaryKey(),
    userId: uuid("user_id").references(() => adminUsers.id, { onDelete: "cascade" }).notNull(),
    codeHash: text("code_hash").notNull(),
    attempts: integer("attempts").default(0).notNull(),
    expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
    consumedAt: timestamp("consumed_at", { withTimezone: true }),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    index("admin_otps_user_expires_idx").on(table.userId, table.expiresAt),
  ]
);

/**
 * 15. Admin Sessions (7-day HTTP-Only Cookie Sessions)
 */
export const adminSessions = pgTable(
  "admin_sessions",
  {
    id: text("id").primaryKey(),
    userId: uuid("user_id").references(() => adminUsers.id, { onDelete: "cascade" }).notNull(),
    sessionTokenHash: text("session_token_hash").notNull().unique(),
    expiresAt: timestamp("expires_at", { withTimezone: true }).notNull(),
    ipAddress: text("ip_address"),
    userAgent: text("user_agent"),
    createdAt: timestamp("created_at", { withTimezone: true }).defaultNow().notNull(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
  },
  (table) => [
    index("admin_sessions_token_hash_idx").on(table.sessionTokenHash),
    index("admin_sessions_user_id_idx").on(table.userId),
  ]
);

/**
 * 16. Site Settings (Key-Value Dynamic Configuration & Heros)
 */
export const siteSettings = pgTable("site_settings", {
  key: text("key").primaryKey(),
  value: jsonb("value").notNull(),
  description: text("description"),
  updatedAt: timestamp("updated_at", { withTimezone: true }).defaultNow().notNull(),
});

// Inferred Types
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type Session = typeof sessions.$inferSelect;
export type NewSession = typeof sessions.$inferInsert;
export type Client = typeof clients.$inferSelect;
export type NewClient = typeof clients.$inferInsert;
export type ClientDumps = typeof clientDumps.$inferSelect;
export type NewClientDumps = typeof clientDumps.$inferInsert;
export type ClientFeeds = typeof clientFeeds.$inferSelect;
export type NewClientFeeds = typeof clientFeeds.$inferInsert;
export type Analysis = typeof analyses.$inferSelect;
export type NewAnalysis = typeof analyses.$inferInsert;
export type Lead = typeof leads.$inferSelect;
export type NewLead = typeof leads.$inferInsert;
export type Product = typeof products.$inferSelect;
export type NewProduct = typeof products.$inferInsert;
export type ProductVariant = typeof productVariants.$inferSelect;
export type NewProductVariant = typeof productVariants.$inferInsert;
export type Service = typeof services.$inferSelect;
export type NewService = typeof services.$inferInsert;
export type Booking = typeof bookings.$inferSelect;
export type NewBooking = typeof bookings.$inferInsert;
export type Order = typeof orders.$inferSelect;
export type NewOrder = typeof orders.$inferInsert;
export type OrderItem = typeof orderItems.$inferSelect;
export type NewOrderItem = typeof orderItems.$inferInsert;
export type InventoryLock = typeof inventoryLocks.$inferSelect;
export type NewInventoryLock = typeof inventoryLocks.$inferInsert;
export type TaskOutboxRecord = typeof taskOutbox.$inferSelect;
export type NewTaskOutboxRecord = typeof taskOutbox.$inferInsert;
export type AdminUser = typeof adminUsers.$inferSelect;
export type NewAdminUser = typeof adminUsers.$inferInsert;
export type AdminOtp = typeof adminOtps.$inferSelect;
export type NewAdminOtp = typeof adminOtps.$inferInsert;
export type AdminSession = typeof adminSessions.$inferSelect;
export type NewAdminSession = typeof adminSessions.$inferInsert;
export type SiteSetting = typeof siteSettings.$inferSelect;
export type NewSiteSetting = typeof siteSettings.$inferInsert;
