#!/usr/bin/env bash
# ==============================================================================
# Reconcile FreeLLMAPI Admin Credentials between Vault (zerops_env) and SQLite
# ==============================================================================
set -euo pipefail

EMAIL="${FREELLM_ADMIN_EMAIL:-${FREELLMAPI_ADMIN_EMAIL:-}}"
PASSWORD="${FREELLM_ADMIN_PASSWORD:-${FREELLMAPI_ADMIN_PASSWORD:-}}"

if [ -z "$EMAIL" ] || [ -z "$PASSWORD" ]; then
    echo "ℹ️ [sync-freellm-auth] FREELLM_ADMIN_EMAIL or FREELLM_ADMIN_PASSWORD not set in environment. Skipping."
    exit 0
fi

if ! ssh -o BatchMode=yes -o ConnectTimeout=5 freellmapi "test -f /mnt/localstorage/freellmapi/freellmapi.db" 2>/dev/null; then
    echo "ℹ️ [sync-freellm-auth] FreeLLMAPI database not yet created at /mnt/localstorage/freellmapi/freellmapi.db. Skipping."
    exit 0
fi

echo "🔐 [sync-freellm-auth] Reconciling admin credentials for ${EMAIL} in SQLite..."
ssh freellmapi "node -e '
const crypto = require(\"crypto\");
const Database = require(\"better-sqlite3\");
const email = \"$EMAIL\".trim().toLowerCase();
const password = \"$PASSWORD\";
const db = new Database(\"/mnt/localstorage/freellmapi/freellmapi.db\");
const salt = crypto.randomBytes(16);
const hash = crypto.scryptSync(password, salt, 64);
const passHash = \`scrypt\${salt.toString(\"hex\")}\$\${hash.toString(\"hex\")}\`;

const existing = db.prepare(\"SELECT id FROM users WHERE email = ?\").get(email);
if (existing) {
  db.prepare(\"UPDATE users SET password_hash = ? WHERE id = ?\").run(passHash, existing.id);
  console.log(\"Updated password for existing user: \" + email);
} else {
  db.prepare(\"INSERT INTO users (email, password_hash) VALUES (?, ?)\").run(email, passHash);
  console.log(\"Created user: \" + email);
}
'"

echo "✅ [sync-freellm-auth] Credentials successfully synchronized."
