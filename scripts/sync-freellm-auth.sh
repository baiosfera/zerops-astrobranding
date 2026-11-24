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

if ! zcp run freellmapi sh -c "test -f /mnt/localstorage/freellmapi/data/freeapi.db || test -f /mnt/localstorage/freellmapi/freellmapi.db" 2>/dev/null; then
    echo "ℹ️ [sync-freellm-auth] FreeLLMAPI database not yet created in /mnt/localstorage/freellmapi. Skipping."
    exit 0
fi

echo "🔐 [sync-freellm-auth] Reconciling admin credentials for ${EMAIL} in SQLite..."
zcp run freellmapi node -e '
const fs = require("fs");
const crypto = require("crypto");
const Database = require("better-sqlite3");
const email = (process.argv[1] || "").trim().toLowerCase();
const password = process.argv[2] || "";
const dbPath = fs.existsSync("/mnt/localstorage/freellmapi/data/freeapi.db")
  ? "/mnt/localstorage/freellmapi/data/freeapi.db"
  : "/mnt/localstorage/freellmapi/freellmapi.db";
const db = new Database(dbPath);
const salt = crypto.randomBytes(16);
const hash = crypto.scryptSync(password, salt, 64);
const passHash = `scrypt${salt.toString("hex")}$${hash.toString("hex")}`;

try {
  const existing = db.prepare("SELECT id FROM users WHERE email = ?").get(email);
  if (existing) {
    db.prepare("UPDATE users SET password_hash = ? WHERE id = ?").run(passHash, existing.id);
    console.log("Updated password for existing user: " + email);
  } else {
    db.prepare("INSERT INTO users (email, password_hash) VALUES (?, ?)").run(email, passHash);
    console.log("Created user: " + email);
  }
} catch (e) {
  console.log("User sync note: " + e.message);
}

try {
  db.prepare("INSERT INTO settings (key, value) VALUES (\x27routing_strategy\x27, \x27smartest\x27) ON CONFLICT(key) DO UPDATE SET value = \x27smartest\x27").run();
  db.prepare("INSERT INTO settings (key, value) VALUES (\x27routing_explore_enabled\x27, \x271\x27) ON CONFLICT(key) DO UPDATE SET value = \x271\x27").run();
  db.prepare("INSERT INTO settings (key, value) VALUES (\x27key_selection_strategy\x27, \x27least-remaining\x27) ON CONFLICT(key) DO UPDATE SET value = \x27least-remaining\x27").run();
} catch (e) {
  console.log("Model settings note: " + e.message);
}
' "$EMAIL" "$PASSWORD"

echo "✅ [sync-freellm-auth] Credentials successfully synchronized."
