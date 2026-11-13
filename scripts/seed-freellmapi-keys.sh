#!/usr/bin/env bash
# ==============================================================================
# Seed FreeLLMAPI & AI Mesh Shared Vault Secrets (v3.0 Declarative SSoT)
# Compiles BOTH primary free-tier pools (baiosfera_freellm.md + damaren_freellm.md)
# and upserts all runtime Vault secrets directly into Zerops Project Shared Vault.
# Usage: ./scripts/seed-freellmapi-keys.sh [--keys <file>] [--pool <md>] [--rotate] [--dry-run] [--restart]
# ==============================================================================
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

log_info() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
log_ok()   { echo -e "\033[1;32m[OK]\033[0m $*"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
log_err()  { echo -e "\033[1;31m[ERROR]\033[0m $*" >&2; }

KEYS_FILE=""
ROTATE=false
DRY_RUN=false
SKIP_RESTART=true
PROJECT_OVERRIDE=""
EXTRA_POOLS=()

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --keys|-k)
            KEYS_FILE="${2:-}"
            shift 2
            ;;
        --pool)
            EXTRA_POOLS+=("${2:-}")
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
            echo "Usage: seed-freellmapi-keys.sh [--keys <keys.md>] [--pool <freellm.md>] [--project <name>] [--rotate] [--dry-run] [--restart]"
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

log_info "Compiling FreeLLMAPI multi-account declarative configuration and Shared Vault secrets..."

PYTHONPATH="$LIB_DIR" python3 - "$KEYS_FILE" "$ROTATE" "$DRY_RUN" "$SKIP_RESTART" "$PROJECT_OVERRIDE" "${EXTRA_POOLS[@]}" << 'EOF_PY'
import json
import os
import sys
from vault_env import (
    DEFAULT_FREELLM_POOLS,
    ZcpVaultClient,
    build_freellm_declarative_config,
    collect_freellm_pools,
    generate_secret,
    parse_kv_file,
)

keys_file = sys.argv[1].strip()
rotate = sys.argv[2] == "true"
dry_run = sys.argv[3] == "true"
skip_restart = sys.argv[4] == "true"
project_override = sys.argv[5].strip()
extra_pools = [p for p in sys.argv[6:] if p]

kv = parse_kv_file(keys_file) if keys_file else {}
pools = list(DEFAULT_FREELLM_POOLS)
for p in extra_pools:
    if p not in pools:
        pools.append(p)

keys_list, custom_providers, loaded_sources = collect_freellm_pools(pools, extra_kv=kv)
if not keys_list and not custom_providers:
    print("[ERROR] No FreeLLM provider keys found in primary pools or keys file.", file=sys.stderr)
    sys.exit(1)

cfg = build_freellm_declarative_config(keys_list, custom_providers)
cfg_json = json.dumps(cfg, separators=(",", ":"))

print(f"[INFO] Compiled {len(keys_list)} FreeLLM keys from {len(loaded_sources)} pool file(s), {len(cfg['models'])} curated models, {len(cfg['fallback'])} fallback priorities.")

if dry_run:
    print(json.dumps({
        "dry_run": True,
        "sources": loaded_sources,
        "key_labels": [k["label"] for k in keys_list],
        "model_count": len(cfg["models"]),
        "fallback_count": len(cfg["fallback"]),
        "routing": cfg["routing"],
        "config_json_bytes": len(cfg_json),
    }, indent=2))
    sys.exit(0)

with ZcpVaultClient() as zcp:
    live_project, existing = zcp.get_project_envs()
    proj_slug = (project_override or kv.get("PROJECT_NAME") or os.getenv("PROJECT_NAME") or live_project or "zerops").strip()
    domain_slug = proj_slug.lower().replace(" ", "-")

    payload: dict[str, str] = {
        "FREEAPI_CONFIG_JSON_SECRET": cfg_json,
        "PROJECT_NAME": proj_slug,
    }
    if "ENGRAM_PROJECT" not in existing:
        payload["ENGRAM_PROJECT"] = os.getenv("ENGRAM_PROJECT") or proj_slug

    admin_email = (kv.get("FREELLMAPI_ADMIN_EMAIL") or kv.get("FREELLMAPI_EMAIL") or f"admin@{domain_slug}.internal").strip()
    admin_pass = (kv.get("FREELLMAPI_ADMIN_PASSWORD") or kv.get("FREELLMAPI_PASSWORD") or "").strip()

    if rotate or "FREEAPI_ADMIN_EMAIL_SECRET" not in existing:
        payload["FREEAPI_ADMIN_EMAIL_SECRET"] = admin_email
    if admin_pass and len(admin_pass) >= 8:
        payload["FREEAPI_ADMIN_PASSWORD_SECRET"] = admin_pass
    elif rotate or "FREEAPI_ADMIN_PASSWORD_SECRET" not in existing:
        payload["FREEAPI_ADMIN_PASSWORD_SECRET"] = generate_secret(24)

    if rotate or "FREEAPI_ENCRYPTION_KEY" not in existing:
        payload["FREEAPI_ENCRYPTION_KEY"] = generate_secret(32, hex_only=True)

    if rotate or "FREELLMAPI_CLIENT_KEY" not in existing:
        payload["FREELLMAPI_CLIENT_KEY"] = f"sk-freellmapi-{generate_secret(32)}"

    if rotate or "BIFROST_MASTER_VK" not in existing:
        payload["BIFROST_MASTER_VK"] = f"vk-bifrost-{generate_secret(28)}"

    if rotate or "PAPERCLIP_BETTER_AUTH_SECRET" not in existing:
        payload["PAPERCLIP_BETTER_AUTH_SECRET"] = generate_secret(32)
    if rotate or "PAPERCLIP_SIGNING_SECRET" not in existing:
        payload["PAPERCLIP_SIGNING_SECRET"] = generate_secret(32)

    pc_email = (kv.get("PAPERCLIP_ADMIN_EMAIL") or admin_email).strip()
    pc_pass = (kv.get("PAPERCLIP_ADMIN_PASSWORD") or admin_pass or "").strip()
    if rotate or "PAPERCLIP_ADMIN_EMAIL_SECRET" not in existing:
        payload["PAPERCLIP_ADMIN_EMAIL_SECRET"] = pc_email
    if pc_pass and len(pc_pass) >= 8:
        payload["PAPERCLIP_ADMIN_PASSWORD_SECRET"] = pc_pass
    elif rotate or "PAPERCLIP_ADMIN_PASSWORD_SECRET" not in existing:
        payload["PAPERCLIP_ADMIN_PASSWORD_SECRET"] = generate_secret(24)

    summary = zcp.upsert_project_envs(payload, skip_restart=skip_restart)
    print(f"[INFO] Project '{live_project}' Shared Vault hydrated: upserted {len(payload)} vars (existing_sensitive={summary['existing_sensitive']}, existing_plain={summary['existing_plain']}, new={summary['new_auto']}).")
EOF_PY

log_ok "FreeLLMAPI & AI Mesh Shared Vault seeding complete."
