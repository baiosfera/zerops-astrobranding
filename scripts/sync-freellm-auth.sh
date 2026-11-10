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

if ! ssh -o BatchMode=yes -o ConnectTimeout=5 freellmapi "test -f /mnt/localstorage/freellmapi/data/freeapi.db || test -f /mnt/localstorage/freellmapi/freellmapi.db" 2>/dev/null; then
    echo "ℹ️ [sync-freellm-auth] FreeLLMAPI database not yet created in /mnt/localstorage/freellmapi. Skipping."
    exit 0
fi

echo "🔐 [sync-freellm-auth] Reconciling admin credentials for ${EMAIL} and patching model limits in SQLite..."
ssh freellmapi "node -e '
const fs = require(\"fs\");
const crypto = require(\"crypto\");
const Database = require(\"better-sqlite3\");
const email = \"$EMAIL\".trim().toLowerCase();
const password = \"$PASSWORD\";
const dbPath = fs.existsSync(\"/mnt/localstorage/freellmapi/data/freeapi.db\")
  ? \"/mnt/localstorage/freellmapi/data/freeapi.db\"
  : \"/mnt/localstorage/freellmapi/freellmapi.db\";
const db = new Database(dbPath);
const salt = crypto.randomBytes(16);
const hash = crypto.scryptSync(password, salt, 64);
const passHash = \`scrypt\${salt.toString(\"hex\")}\$\${hash.toString(\"hex\")}\`;

try {
  const existing = db.prepare(\"SELECT id FROM users WHERE email = ?\").get(email);
  if (existing) {
    db.prepare(\"UPDATE users SET password_hash = ? WHERE id = ?\").run(passHash, existing.id);
    console.log(\"Updated password for existing user: \" + email);
  } else {
    db.prepare(\"INSERT INTO users (email, password_hash) VALUES (?, ?)\").run(email, passHash);
    console.log(\"Created user: \" + email);
  }
} catch (e) {
  console.log(\"User sync note: \" + e.message);
}

try {
  // Enforce Groq free tier 7000 ITPM limit to prevent HTTP 413 cascade failures
  const updated = db.prepare(\"UPDATE models SET tpm_limit = 7000 WHERE platform = ? AND model_id = ? AND (tpm_limit > 7000 OR tpm_limit IS NULL)\").run(\"groq\", \"qwen/qwen3.8-27b\");
  if (updated.changes > 0) {
    console.log(\"Patched Groq qwen3.8-27b tpm_limit to 7000 ITPM.\");
  }
} catch (e) {
  console.log(\"Model limit patch note: \" + e.message);
}
'"

echo "✅ [sync-freellm-auth] Credentials successfully synchronized."
