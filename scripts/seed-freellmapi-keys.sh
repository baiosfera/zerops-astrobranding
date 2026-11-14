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
import re
import sys
from vault_env import (
    ZcpVaultClient,
    build_freellm_declarative_config,
    collect_freellm_pools,
    discover_freellm_pools,
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
pools = discover_freellm_pools(keys_file or None, extra_pools)

keys_list, custom_providers, loaded_sources = collect_freellm_pools(pools, extra_kv=kv)
if not keys_list and not custom_providers:
    print("[ERROR] No FreeLLM provider keys found in discovered pools or keys file.", file=sys.stderr)
    sys.exit(1)

def _clean_domain(slug: str) -> str:
    cleaned = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-")
    return cleaned or "zerops"

def _build_runtime_cfg(proj_slug: str, client_key: str) -> tuple[dict, str]:
    domain_slug = _clean_domain(proj_slug)
    admin_email = (
        kv.get("FREEAPI_ADMIN_EMAIL")
        or kv.get("FREELLMAPI_ADMIN_EMAIL")
        or kv.get("FREELLMAPI_EMAIL")
        or f"freellmapi@{domain_slug}.internal"
    ).strip()
    raw_pass = (
        kv.get("FREEAPI_ADMIN_PASSWORD")
        or kv.get("FREELLMAPI_ADMIN_PASSWORD")
        or kv.get("FREELLMAPI_PASSWORD")
        or ""
    ).strip()
    admin_pass = raw_pass if len(raw_pass) >= 8 else generate_secret(24)
    cfg_obj = build_freellm_declarative_config(
        keys_list,
        custom_providers,
        admin_email=admin_email,
        admin_password=admin_pass,
        unified_api_key=client_key,
    )
    return cfg_obj, json.dumps(cfg_obj, separators=(",", ":"))

if dry_run:
    preview_slug = (project_override or kv.get("PROJECT_NAME") or os.getenv("PROJECT_NAME") or "zerops").strip()
    preview_cfg, preview_json = _build_runtime_cfg(preview_slug, f"sk-freellmapi-{generate_secret(32)}")
    print(f"[INFO] Compiled {len(keys_list)} FreeLLM keys from {len(loaded_sources)} pool file(s), {len(preview_cfg['models'])} curated models, {len(preview_cfg['fallback'])} fallback priorities.")
    print(json.dumps({
        "dry_run": True,
        "sources": loaded_sources,
        "key_labels": [k["label"] for k in keys_list],
        "model_count": len(preview_cfg["models"]),
        "fallback_count": len(preview_cfg["fallback"]),
        "routing": preview_cfg["routing"],
        "has_admin_block": "admin" in preview_cfg,
        "admin_email": preview_cfg.get("admin", {}).get("email", ""),
        "has_unified_api_key": bool(preview_cfg.get("unifiedApiKey")),
        "config_json_bytes": len(preview_json),
        "vault_keys": ["FREEAPI_CONFIG_JSON_SECRET", "FREEAPI_ENCRYPTION_KEY", "FREELLMAPI_CLIENT_KEY"],
    }, indent=2))
    sys.exit(0)

with ZcpVaultClient() as zcp:
    live_project, existing = zcp.get_project_envs()
    proj_slug = (project_override or kv.get("PROJECT_NAME") or os.getenv("PROJECT_NAME") or live_project or "zerops").strip()
    client_key = (kv.get("FREELLMAPI_CLIENT_KEY") or "").strip()
    if not client_key:
        client_key = f"sk-freellmapi-{generate_secret(32)}"

    cfg, cfg_json = _build_runtime_cfg(proj_slug, client_key)
    print(f"[INFO] Compiled {len(keys_list)} FreeLLM keys from {len(loaded_sources)} pool file(s), {len(cfg['models'])} curated models, {len(cfg['fallback'])} fallback priorities.")

    payload: dict[str, str] = {
        "FREEAPI_CONFIG_JSON_SECRET": cfg_json,
    }
    if rotate or "FREEAPI_ENCRYPTION_KEY" not in existing:
        payload["FREEAPI_ENCRYPTION_KEY"] = generate_secret(32, hex_only=True)
    if rotate or "FREELLMAPI_CLIENT_KEY" not in existing:
        payload["FREELLMAPI_CLIENT_KEY"] = client_key

    summary = zcp.upsert_project_envs(payload, skip_restart=skip_restart)
    print(f"[INFO] Project '{live_project}' FreeLLMAPI vault hydrated: upserted {len(payload)} vars (existing_sensitive={summary['existing_sensitive']}, existing_plain={summary['existing_plain']}, new={summary['new_auto']}).")
EOF_PY

log_ok "FreeLLMAPI declarative config & vault seeding complete."
