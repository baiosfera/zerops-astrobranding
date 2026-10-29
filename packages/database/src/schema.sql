-- ==============================================================================
-- Zerops AstroBranding Canonical PostgreSQL 18 DDL Migration
-- Implements complete schema from packages/database/src/schema.ts
-- SSoT: /var/www/zerops-astrobranding/packages/database/src/schema.ts
-- ==============================================================================

-- 1. Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Table: clients
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    birth_date TEXT NOT NULL,
    birth_time TEXT NOT NULL,
    birth_city TEXT NOT NULL,
    birth_country TEXT NOT NULL,
    latitude TEXT,
    longitude TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Table: client_dumps (15 Canonical Bronze JSONB Shards)
CREATE TABLE IF NOT EXISTS client_dumps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    birth_metadata JSONB NOT NULL,
    shard_western_tropical JSONB NOT NULL,
    shard_western_sidereal JSONB NOT NULL,
    shard_vedic_jyotish JSONB NOT NULL,
    shard_vedic_dashas JSONB NOT NULL,
    shard_bazi_metaphysics JSONB NOT NULL,
    shard_ziwei_fengshui JSONB NOT NULL,
    shard_kabbalah_gematria JSONB NOT NULL,
    shard_hebrew_zmanim JSONB NOT NULL,
    shard_human_design JSONB NOT NULL,
    shard_cosmobiology_midpoints JSONB NOT NULL,
    shard_nasa_ephemerides JSONB NOT NULL,
    shard_astrocartography_acg JSONB NOT NULL,
    shard_business_penta_org JSONB NOT NULL,
    shard_partner_synastry JSONB NOT NULL,
    shard_predictive_electional JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS client_dumps_client_id_idx ON client_dumps (client_id);

-- 4. Table: client_feeds (Tier 2 Gold Feeds)
CREATE TABLE IF NOT EXISTS client_feeds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    feed_type TEXT NOT NULL,
    xml_payload TEXT NOT NULL,
    token_estimate INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS client_feeds_client_id_feed_type_idx ON client_feeds (client_id, feed_type);

-- 5. Table: leads (Opt-In & WhatsApp OTP Funnel)
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone TEXT NOT NULL,
    email TEXT,
    name TEXT,
    otp_code TEXT,
    otp_expires_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'unverified',
    crm_lead_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS leads_phone_idx ON leads (phone);

-- 6. Table: analyses (AstroBranding Analyses & Vector Embeddings)
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    chart_data JSONB NOT NULL,
    archetype TEXT,
    strategic_summary TEXT,
    branding_recommendations JSONB,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS analyses_client_id_idx ON analyses (client_id);
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE tablename = 'analyses' AND indexname = 'analyses_embedding_hnsw_idx'
    ) THEN
        CREATE INDEX analyses_embedding_hnsw_idx ON analyses USING hnsw (embedding vector_cosine_ops);
    END IF;
END $$;

-- 7. Table: orders (Fulfillment & Payments)
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    amount TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'pending',
    payment_ref TEXT,
    dian_cufe TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. Table: task_outbox (Transactional Outbox Pattern)
CREATE TABLE IF NOT EXISTS task_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,
    dedupe_key TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    scheduled_for TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processing_token TEXT,
    processed_at TIMESTAMPTZ,
    redacted_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS task_outbox_type_dedupe_key_idx ON task_outbox (type, dedupe_key);
CREATE INDEX IF NOT EXISTS task_outbox_status_scheduled_for_idx ON task_outbox (status, scheduled_for);

-- 9. Table: client_shards (Normalized Multi-Domain Decoupled Store)
CREATE TABLE IF NOT EXISTS client_shards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    shard_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS client_shards_client_id_shard_type_idx ON client_shards (client_id, shard_type);
CREATE INDEX IF NOT EXISTS client_shards_shard_type_idx ON client_shards (shard_type);

-- 10. Table: offerings (Universal Commercial Offerings Across 6 Archetypes)
CREATE TABLE IF NOT EXISTS offerings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    archetype TEXT NOT NULL,
    channel_strategy TEXT NOT NULL,
    price NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    currency TEXT NOT NULL DEFAULT 'COP',
    compare_at_price NUMERIC(12, 2),
    availability TEXT NOT NULL DEFAULT 'in_stock',
    brand TEXT NOT NULL,
    category TEXT,
    image_url TEXT,
    additional_image_urls JSONB NOT NULL DEFAULT '[]'::jsonb,
    meta_event_mapping JSONB NOT NULL DEFAULT '{"web": "Purchase", "capi": "Purchase"}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS offerings_slug_idx ON offerings (slug);
CREATE UNIQUE INDEX IF NOT EXISTS offerings_slug_active_unique ON offerings (slug) WHERE active = true;
CREATE INDEX IF NOT EXISTS offerings_archetype_idx ON offerings (archetype);
CREATE INDEX IF NOT EXISTS offerings_channel_strategy_idx ON offerings (channel_strategy);
CREATE INDEX IF NOT EXISTS offerings_active_idx ON offerings (active);

-- 11. Table: admin_users (RBAC: Superadmin & Merchant)
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    telegram_user_id BIGINT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'merchant', -- 'superadmin' | 'merchant'
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS admin_users_telegram_idx ON admin_users (telegram_user_id);

-- 12. Table: admin_otps (Single-use Cryptographic OTPs)
CREATE TABLE IF NOT EXISTS admin_otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
    code_hash TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS admin_otps_user_expires_idx ON admin_otps (user_id, expires_at);

-- 13. Table: admin_sessions (7-day HTTP-Only Cookie Sessions)
CREATE TABLE IF NOT EXISTS admin_sessions (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES admin_users(id) ON DELETE CASCADE,
    session_token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS admin_sessions_token_hash_idx ON admin_sessions (session_token_hash);
CREATE INDEX IF NOT EXISTS admin_sessions_user_id_idx ON admin_sessions (user_id);


