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

  // Ensure routing settings use smartest strategy and MAB exploration
  db.prepare(\"INSERT INTO settings (key, value) VALUES (\x27routing_strategy\x27, \x27smartest\x27) ON CONFLICT(key) DO UPDATE SET value = \x27smartest\x27\").run();
  db.prepare(\"INSERT INTO settings (key, value) VALUES (\x27routing_explore_enabled\x27, \x271\x27) ON CONFLICT(key) DO UPDATE SET value = \x271\x27\").run();
  db.prepare(\"INSERT INTO settings (key, value) VALUES (\x27key_selection_strategy\x27, \x27least-remaining\x27) ON CONFLICT(key) DO UPDATE SET value = \x27least-remaining\x27\").run();

  // Rebalance top Profile 1 priorities to include OpenRouter models
  const topModels = [
    { platform: \"cerebras\", model_id: \"qwen-3.8-27b\", priority: 1 },
    { platform: \"groq\", model_id: \"qwen/qwen3.8-27b\", priority: 2 },
    { platform: \"openrouter\", model_id: \"nvidia/nemotron-3.5-lightning:free\", priority: 3 },
    { platform: \"openrouter\", model_id: \"dots-studio/dots-3-note-preview:free\", priority: 4 },
    { platform: \"openrouter\", model_id: \"openrouter/free\", priority: 5 }
  ];
  for (const m of topModels) {
    const row = db.prepare(\"SELECT id FROM models WHERE platform = ? AND model_id = ?\").get(m.platform, m.model_id);
    if (row) {
      db.prepare(\"UPDATE models SET enabled = 1 WHERE id = ?\").run(row.id);
      db.prepare(\`
        INSERT INTO profile_models (profile_id, model_db_id, priority, enabled)
        VALUES (1, ?, ?, 1)
        ON CONFLICT(profile_id, model_db_id) DO UPDATE SET priority = excluded.priority, enabled = 1
      \`).run(row.id, m.priority);
    }
  }
} catch (e) {
  console.log(\"Model settings and priorities patch note: \" + e.message);
}
'"

echo "✅ [sync-freellm-auth] Credentials successfully synchronized."
