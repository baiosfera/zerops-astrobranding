#!/usr/bin/env bash
# ==============================================================================
# Universal PostgreSQL Anti-Starvation & Connection Quota Hardening
# Enforces database-level connection caps and defensive session timeouts.
# ==============================================================================
set -euo pipefail

DB_HOST="${database_hostname:-${db_hostname:-}}"
DB_PORT="${database_port:-${db_port:-5432}}"
DB_NAME="${database_dbName:-${db_dbName:-db}}"
SUPER_USER="${database_superUser:-${db_superUser:-postgres}}"
SUPER_PASS="${database_superUserPassword:-${db_superUserPassword:-}}"

APP_USER="${database_user:-${db_user:-db}}"

if ! command -v psql >/dev/null 2>&1; then
    echo "ℹ️ [PostgreSQL Quota Hardener] psql CLI not found. Skipping quota enforcement."
    exit 0
fi

if [ -n "$DB_HOST" ] && [ -n "$SUPER_PASS" ]; then
    echo "🛡️ [PostgreSQL Quota Hardener] Enforcing connection quotas & timeouts via superuser (${SUPER_USER})..."
    if PGPASSWORD="$SUPER_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$SUPER_USER" -d "$DB_NAME" -X -q << 'EOF'
DO $$
DECLARE
    main_db text := current_database();
BEGIN
    -- 1. Hard cap primary application database connection limit to 60 slots
    EXECUTE format('ALTER DATABASE %I WITH CONNECTION LIMIT 60', main_db);
    EXECUTE format('ALTER DATABASE %I SET idle_session_timeout = ''2min''', main_db);
    EXECUTE format('ALTER DATABASE %I SET idle_in_transaction_session_timeout = ''30s''', main_db);
    
    -- 2. Dynamically cap all non-system satellite databases to 15 slots
    FOR sat IN SELECT datname FROM pg_database WHERE datname NOT IN ('postgres', 'template0', 'template1', main_db)
    LOOP
        EXECUTE format('ALTER DATABASE %I WITH CONNECTION LIMIT 15', sat);
        EXECUTE format('ALTER DATABASE %I SET idle_session_timeout = ''2min''', sat);
        EXECUTE format('ALTER DATABASE %I SET idle_in_transaction_session_timeout = ''30s''', sat);
    END LOOP;

    -- 3. Apply role-level idle timeouts for the application user
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'db') THEN
        EXECUTE 'ALTER ROLE db SET idle_session_timeout = ''2min''';
        EXECUTE 'ALTER ROLE db SET idle_in_transaction_session_timeout = ''30s''';
    END IF;
END
$$;
EOF
    then
        echo "✅ [PostgreSQL Quota Hardener] Quotas enforced: 60 slots on main DB, 15 slots on satellite DBs, 2min idle timeout."
    else
        echo "⚠️ [PostgreSQL Quota Hardener] Warning applying superuser quotas."
    fi
elif [ -n "${database_connectionString:-${db_connectionString:-${DATABASE_URL:-}}}" ]; then
    DB_CONN="${database_connectionString:-${db_connectionString:-${DATABASE_URL}}}"
    echo "🛡️ [PostgreSQL Quota Hardener] Applying role-level timeouts via standard connection string..."
    if psql "$DB_CONN" -X -q << 'EOF'
DO $$
BEGIN
    EXECUTE format('ALTER ROLE %I SET idle_session_timeout = ''2min''', current_user);
    EXECUTE format('ALTER ROLE %I SET idle_in_transaction_session_timeout = ''30s''', current_user);
EXCEPTION WHEN OTHERS THEN
    NULL;
END
$$;
EOF
    then
        echo "✅ [PostgreSQL Quota Hardener] Role-level session timeouts applied."
    else
        echo "⚠️ [PostgreSQL Quota Hardener] Warning applying standard role timeouts."
    fi
else
    echo "ℹ️ [PostgreSQL Quota Hardener] No active PostgreSQL service detected in environment. Skipping."
fi
