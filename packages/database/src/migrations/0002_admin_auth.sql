-- ==============================================================================
-- Migration 0002: Admin Auth, Telegram OTP, Session Management & Partial Slug Indexes
-- ==============================================================================

-- 1. Partial Unique Indexes for Soft-Delete Lifecycle on products & services
ALTER TABLE products DROP CONSTRAINT IF EXISTS products_slug_key;
DROP INDEX IF EXISTS products_slug_key;
CREATE UNIQUE INDEX IF NOT EXISTS products_slug_active_unique ON products (slug) WHERE is_active = 1;

ALTER TABLE services DROP CONSTRAINT IF EXISTS services_slug_key;
DROP INDEX IF EXISTS services_slug_key;
CREATE UNIQUE INDEX IF NOT EXISTS services_slug_active_unique ON services (slug) WHERE is_active = 1;

-- 2. Admin Users Table (RBAC: superadmin | merchant)
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

-- 3. Admin OTPs Table (Single-use 6-digit cryptographic OTPs)
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

-- 4. Admin Sessions Table (7-day HTTP-Only Cookie Sessions)
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

-- 5. Seed initial admin users
INSERT INTO admin_users (name, telegram_user_id, role, is_active)
VALUES 
    ('Superadmin Developer', 8971481206, 'superadmin', 1),
    ('Catalina Glamur Merchant', 888888, 'merchant', 1)
ON CONFLICT (telegram_user_id) DO UPDATE 
SET role = EXCLUDED.role, is_active = 1, updated_at = NOW();
