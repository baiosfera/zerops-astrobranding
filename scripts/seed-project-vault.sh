#!/usr/bin/env bash
# ==============================================================================
# Seed Agnostic Project Shared Vault Secrets (v1.0)
# Reads client keys file (--keys <file>) and upserts project-level shared
# vault secrets (Paperclip, Bifrost, Evolution, TTYD, copyable API keys)
# directly into Zerops Project Shared Vault via ZcpVaultClient.
# Usage: ./scripts/seed-project-vault.sh [--keys <file>] [--project <name>] [--rotate] [--dry-run] [--restart]
# ==============================================================================
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

log_info() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
log_ok()   { echo -e "\033[1;32m[OK]\033[0m $*"; }
log_err()  { echo -e "\033[1;31m[ERROR]\033[0m $*" >&2; }

KEYS_FILE=""
ROTATE=false
DRY_RUN=false
SKIP_RESTART=true
PROJECT_OVERRIDE=""

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --keys|-k)
            KEYS_FILE="${2:-}"
            shift 2
            ;;
        --project|-p)
            PROJECT_OVERRIDE="${2:-}"
            shift 2
            ;;
        --rotate)
            ROTATE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --restart)
            SKIP_RESTART=false
            shift
            ;;
        -h|--help)
            echo "Usage: seed-project-vault.sh [--keys <keys.md>] [--project <name>] [--rotate] [--dry-run] [--restart]"
            exit 0
            ;;
        *)
            if [ -z "$KEYS_FILE" ] && [ -f "$1" ]; then
                KEYS_FILE="$1"
            fi
            shift
            ;;
    esac
done

if [ -n "$KEYS_FILE" ] && [ ! -f "$KEYS_FILE" ]; then
    log_err "Keys file not found: $KEYS_FILE"
    exit 1
fi

log_info "Hydrating agnostic Project Shared Vault secrets..."

PYTHONPATH="$LIB_DIR" python3 - "$KEYS_FILE" "$ROTATE" "$DRY_RUN" "$SKIP_RESTART" "$PROJECT_OVERRIDE" << 'EOF_PY'
import json
import os
import sys
from vault_env import (
    ZcpVaultClient,
    is_sensitive_vault_key,
    parse_kv_file,
    resolve_project_vault_payload,
)

keys_file = sys.argv[1].strip()
rotate = sys.argv[2] == "true"
dry_run = sys.argv[3] == "true"
skip_restart = sys.argv[4] == "true"
project_override = sys.argv[5].strip()

kv = parse_kv_file(keys_file) if keys_file else {}

if dry_run:
    proj_slug = (project_override or kv.get("PROJECT_NAME") or os.getenv("PROJECT_NAME") or "zerops").strip()
    payload = resolve_project_vault_payload(kv, proj_slug, existing={}, rotate=rotate)
    sensitive_keys = sorted(k for k in payload if is_sensitive_vault_key(k))
    plain_keys = sorted(k for k in payload if not is_sensitive_vault_key(k))
    print(json.dumps({
        "dry_run": True,
        "project_slug": proj_slug,
        "keys_file": keys_file or None,
        "total_vars": len(payload),
        "sensitive_count": len(sensitive_keys),
        "plain_count": len(plain_keys),
        "sensitive_keys": sensitive_keys,
        "plain_keys": plain_keys,
        "paperclip_admin_email": payload.get("PAPERCLIP_ADMIN_EMAIL", ""),
        "engram_project": payload.get("ENGRAM_PROJECT", ""),
    }, indent=2))
    sys.exit(0)

with ZcpVaultClient() as zcp:
    live_project, existing = zcp.get_project_envs()
    proj_slug = (project_override or kv.get("PROJECT_NAME") or os.getenv("PROJECT_NAME") or live_project or "zerops").strip()
    payload = resolve_project_vault_payload(kv, proj_slug, existing=existing, rotate=rotate)
    summary = zcp.upsert_project_envs(payload, skip_restart=skip_restart)
    print(
        f"[INFO] Project '{live_project}' agnostic Shared Vault hydrated: "
        f"upserted {len(payload)} vars (existing_sensitive={summary['existing_sensitive']}, "
        f"existing_plain={summary['existing_plain']}, new={summary['new_auto']})."
    )
EOF_PY

log_ok "Project Shared Vault seeding complete."
