#!/usr/bin/env bash
# ==============================================================================
# iniciar.sh — Sovereign Day-0 ZCP Orchestrator & Updater (v4.0)
# Single entrypoint for clean ZCP cloning/hydration and fast `zcp-update`.
# Never auto-injects `api_keys_global` template into project vaults.
# ==============================================================================
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1

BASE_DIR="/var/www"
CATALOG_REPO="https://github.com/baiosfera/zerops-astrobranding.git"
SKILLS_REPO="https://github.com/baiosfera/zerops-astro-skills.git"
REPO_DIR="$BASE_DIR/zerops-astrobranding"
CATALOG_DIR="$REPO_DIR"
SKILLS_DIR="$BASE_DIR/zerops-astro-skills"
AGENTS_SKILLS_DIR="$BASE_DIR/.agents/skills"
LOCAL_BIN="$BASE_DIR/.bin"
DRIVE_MOUNT="${GDRIVE_MOUNT_DIR:-/var/www/baiosfera}"
USERS_APIS_DIR="$DRIVE_MOUNT/0ZEROPS-AGY/users-apis"

UPDATE_ONLY=false
SKIP_VAULT=false
SKIP_TOOLS=false
NON_INTERACTIVE=false
COPYABLE_CREDS=false
EXPLICIT_KEYS_FILE=""
PROJECT_OVERRIDE=""
EXTRA_POOLS=()

PRUNED_SKILLS=(
  jira-epic jira-task gentle-ai-bench gentle-ai-collab-perfect
  rdd-advisory-transport rdd-defect-workflow migrate-to-shoehorn
  scaffold-exercises django-drf angular using-superpowers brainstorming
  writing-plans executing-plans subagent-driven-development
  dispatching-parallel-agents finishing-a-development-branch
  using-git-worktrees requesting-code-review receiving-code-review
  test-driven-development systematic-debugging grill-me grilling
  grill-with-docs pr github-pr ask-matt claude-handoff handoff
  wayfinder teach retro loop-me software-factory chief-of-staff
  implement implement-spec improve-codebase-architecture
  setup-ts-deep-modules to-questionnaire to-spec to-tickets triage
  writing-beats writing-fragments writing-shape
  git-guardrails-claude-code issue-creation issue-root-resolution skill-registry
)

parse_args() {
  if [ "$(basename "$0")" = "zcp-update" ]; then
    UPDATE_ONLY=true
  fi
  local args=("$@")
  local i=0
  while [ "$i" -lt "${#args[@]}" ]; do
    case "${args[$i]}" in
      --update)
        UPDATE_ONLY=true
        ;;
      --full)
        UPDATE_ONLY=false
        ;;
      --skip-vault)
        SKIP_VAULT=true
        ;;
      --skip-tools)
        SKIP_TOOLS=true
        ;;
      --non-interactive)
        NON_INTERACTIVE=true
        ;;
      --copyable-creds)
        COPYABLE_CREDS=true
        ;;
      --pool)
        i=$((i + 1))
        [ -n "${args[$i]:-}" ] && EXTRA_POOLS+=("${args[$i]}")
        ;;
      --keys|-k)
        i=$((i + 1))
        EXPLICIT_KEYS_FILE="${args[$i]:-}"
        ;;
      --project|-p)
        i=$((i + 1))
        PROJECT_OVERRIDE="${args[$i]:-}"
        ;;
      -h|--help)
        echo "Uso: iniciar.sh [--update|--full] [--keys /path/to/<project>-keys.md] [--pool /path/to/pool_freellm.md] [--project <slug>] [--copyable-creds] [--skip-vault] [--skip-tools] [--non-interactive]"
        exit 0
        ;;
    esac
    i=$((i + 1))
  done
}

log() { echo "[iniciar] $*"; }

is_template_keys_file() {
  local p="${1:-}"
  [ -n "$p" ] && [ "$(basename "$p")" = "api_keys_global" ]
}

install_os_deps() {
  if command -v apt-get >/dev/null 2>&1; then
    if ! command -v jq >/dev/null 2>&1 || ! command -v fusermount3 >/dev/null 2>&1 || ! command -v sshfs >/dev/null 2>&1 || ! command -v rsync >/dev/null 2>&1 || ! command -v envsubst >/dev/null 2>&1; then
      sudo apt-get update -qq
      sudo apt-get install -y -qq curl git jq fuse3 sshfs gettext-base python3-yaml rsync unzip >/dev/null
    fi
  elif command -v apk >/dev/null 2>&1; then
    sudo apk add --no-cache curl git jq fuse3 sshfs gettext py3-yaml rsync unzip >/dev/null
  fi
}

sync_repo() {
  local url="$1" dir="$2"
  if [ -d "$dir/.git" ]; then
    git -C "$dir" pull --ff-only origin main || log "WARN: ff-only pull skipped for $dir"
  else
    git clone --depth 1 "$url" "$dir"
  fi
}

ensure_gdrive_mount() {
  if [ -d "$DRIVE_MOUNT/0ZEROPS-AGY" ]; then
    return 0
  fi
  [ -f /etc/environment ] && set -a && . /etc/environment 2>/dev/null && set +a || true
  [ -f "/var/www/.rclone/gdrive.env" ] && set -a && . "/var/www/.rclone/gdrive.env" 2>/dev/null && set +a || true
  [ -f "/var/www/gdrive.env" ] && set -a && . "/var/www/gdrive.env" 2>/dev/null && set +a || true

  local cid="${GDRIVE_CLIENT_ID:-${GOOGLE_CLIENT_ID:-}}"
  local csec="${GDRIVE_CLIENT_SECRET:-${GOOGLE_CLIENT_SECRET:-}}"
  local rtok="${GDRIVE_REFRESH_TOKEN:-}"
  if [ -n "$cid" ] && [ -n "$csec" ] && [ -n "$rtok" ] && [ -f "$CATALOG_DIR/scripts/gdrive.sh" ]; then
    log "Google Drive no montado aún; ejecutando gdrive.sh..."
    bash "$CATALOG_DIR/scripts/gdrive.sh" || log "WARN: gdrive.sh no pudo completar el montaje; podés usar drive-keys --import."
  else
    log "INFO: Google Drive aún no montado en $DRIVE_MOUNT (omitiendo; podés usar 'drive-keys --import <PAYLOAD>' o pasar --keys local)."
  fi
}

resolve_mandatory_keys() {
  [ "$SKIP_VAULT" = true ] && return 0

  if [ -n "$EXPLICIT_KEYS_FILE" ]; then
    if is_template_keys_file "$EXPLICIT_KEYS_FILE"; then
      log "ERROR: 'api_keys_global' es solo una plantilla genérica. Creá y pasá un archivo propio del proyecto (ej: $USERS_APIS_DIR/Damaren/damaren.md)." >&2
      return 1
    fi
    if [ ! -f "$EXPLICIT_KEYS_FILE" ]; then
      log "ERROR: Archivo de claves no encontrado: $EXPLICIT_KEYS_FILE" >&2
      return 1
    fi
    return 0
  fi

  # In update mode (`zcp-update`), never auto-prompt or read $ZCP_KEYS_FILE unless --keys was explicitly passed.
  [ "$UPDATE_ONLY" = true ] && return 0

  if [ -n "${ZCP_KEYS_FILE:-}" ]; then
    if is_template_keys_file "$ZCP_KEYS_FILE"; then
      log "ERROR: ZCP_KEYS_FILE apunta a la plantilla 'api_keys_global'. Especificá un archivo propio de proyecto." >&2
      return 1
    fi
    if [ -f "$ZCP_KEYS_FILE" ]; then
      EXPLICIT_KEYS_FILE="$ZCP_KEYS_FILE"
      return 0
    fi
  fi

  if [ "$NON_INTERACTIVE" = true ] || [ ! -r /dev/tty ]; then
    log "ERROR: En instalación inicial (--full) debés pasar --keys /ruta/al/<proyecto>-keys.md (o --skip-vault). Nunca se auto-usa 'api_keys_global'." >&2
    return 1
  fi

  echo "" > /dev/tty
  echo "============================================================" > /dev/tty
  echo "  🔑 Selección obligatoria de archivo de credenciales" > /dev/tty
  echo "============================================================" > /dev/tty
  if [ -d "$USERS_APIS_DIR" ]; then
    echo "Archivos detectados en $USERS_APIS_DIR (excluyendo plantilla api_keys_global):" > /dev/tty
    for d in "$USERS_APIS_DIR"/*/; do
      [ -d "$d" ] || continue
      for f in "$d"*.md "$d"*.env; do
        [ -f "$f" ] || continue
        case "$(basename "$f")" in
          *_freellm.md|prompt-*|*_plan*.md|directus.md|api_keys_global) continue ;;
          *) echo "  - $f" > /dev/tty ;;
        esac
      done
    done
  fi

  while true; do
    local user_input=""
    printf '[iniciar] Ruta del archivo de claves del proyecto (.md / .env) [o "skip" para omitir]: ' > /dev/tty
    IFS= read -r user_input < /dev/tty || user_input=""
    user_input="$(printf '%s' "$user_input" | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    if [ "$user_input" = "skip" ]; then
      SKIP_VAULT=true
      return 0
    fi
    if is_template_keys_file "$user_input"; then
      echo "❌ 'api_keys_global' es plantilla genérica. Indicá el archivo real del proyecto." > /dev/tty
      continue
    fi
    if [ -n "$user_input" ] && [ -f "$user_input" ]; then
      EXPLICIT_KEYS_FILE="$user_input"
      return 0
    fi
    echo "❌ Archivo no encontrado: ${user_input:-<vacío>}. Intentá de nuevo o escribí 'skip'." > /dev/tty
  done
}

link_skills() {
  mkdir -p "$AGENTS_SKILLS_DIR"
  for skill_path in "$SKILLS_DIR"/*/; do
    [ -f "${skill_path}SKILL.md" ] || continue
    local name
    name=$(basename "$skill_path")
    if [ -d "$AGENTS_SKILLS_DIR/$name" ] && [ ! -L "$AGENTS_SKILLS_DIR/$name" ]; then
      rm -rf "$AGENTS_SKILLS_DIR/$name"
    fi
    ln -sfn "$SKILLS_DIR/$name" "$AGENTS_SKILLS_DIR/$name"
    rm -rf "$HOME/.gemini/antigravity-cli/skills/$name" "$HOME/.gemini/config/skills/$name" "$BASE_DIR/.claude/skills/$name" 2>/dev/null || true
  done

  for noise_sk in "${PRUNED_SKILLS[@]}"; do
    rm -rf "$AGENTS_SKILLS_DIR/$noise_sk" "$HOME/.gemini/antigravity-cli/skills/$noise_sk" "$HOME/.gemini/config/skills/$noise_sk" "$BASE_DIR/.claude/skills/$noise_sk" "$BASE_DIR/localstorage/skills/$noise_sk" 2>/dev/null || true
  done
  for sec_dir in "$HOME/.gemini/antigravity-cli/skills" "$HOME/.gemini/config/skills"; do
    if [ -d "$sec_dir" ]; then
      find "$sec_dir" -mindepth 1 -maxdepth 1 ! -name "_shared" -exec rm -rf {} + 2>/dev/null || true
    fi
  done

  if [ -d "$BASE_DIR/localstorage" ] && command -v rsync >/dev/null 2>&1; then
    mkdir -p "$BASE_DIR/localstorage/skills"
    rsync -aL --delete --exclude="__pycache__" --exclude="*.pyc" --exclude="*.bak" --exclude=".git" --exclude="AGENTS.md" "$AGENTS_SKILLS_DIR/" "$BASE_DIR/localstorage/skills/" 2>/dev/null || true
  fi

  rm -rf "$BASE_DIR/.atl" 2>/dev/null || true
  log "Skills symlinked & deduplicated cleanly: $SKILLS_DIR -> $AGENTS_SKILLS_DIR"
}

link_bin() {
  mkdir -p "$LOCAL_BIN" "$LOCAL_BIN/hooks" "$HOME/.local/bin"
  # Remove broken gentle-ai symlink left by legacy installers
  [ -L "$LOCAL_BIN/gentle-ai" ] && [ ! -e "$LOCAL_BIN/gentle-ai" ] && rm -f "$LOCAL_BIN/gentle-ai"
  for s in ssot-parity-check.sh skills-suite-validate.sh skills-sync.sh zcp-sync linear-cli inject-agent-rule apotelos brand-play engram-sync engram-mcp zeropsenv seed-project-vault.sh seed-freellmapi-keys.sh setup-gh.sh harden-postgres-quotas.sh zcp-mount zcp-mail.sh zcp-preflight-gate.sh zcp-wa.sh astrobranding-check.sh drive-keys.sh; do
    if [ -f "$CATALOG_DIR/scripts/$s" ]; then
      chmod +x "$CATALOG_DIR/scripts/$s"
      local bin_name="${s%.sh}"
      [ -e "$LOCAL_BIN/$bin_name" ] && [ ! -L "$LOCAL_BIN/$bin_name" ] && rm -f "$LOCAL_BIN/$bin_name"
      [ -e "$HOME/.local/bin/$bin_name" ] && [ ! -L "$HOME/.local/bin/$bin_name" ] && rm -f "$HOME/.local/bin/$bin_name"
      ln -sfn "$CATALOG_DIR/scripts/$s" "$LOCAL_BIN/$bin_name"
      ln -sfn "$CATALOG_DIR/scripts/$s" "$HOME/.local/bin/$bin_name"
      sudo ln -sfn "$LOCAL_BIN/$bin_name" "/usr/local/bin/$bin_name" 2>/dev/null || true
    fi
  done
  if [ -f "$CATALOG_DIR/bin/orchesbrand" ]; then
    chmod +x "$CATALOG_DIR/bin/orchesbrand"
    ln -sfn "$CATALOG_DIR/bin/orchesbrand" "$LOCAL_BIN/orchesbrand"
    ln -sfn "$CATALOG_DIR/bin/orchesbrand" "$HOME/.local/bin/orchesbrand"
    sudo ln -sfn "$LOCAL_BIN/orchesbrand" "/usr/local/bin/orchesbrand" 2>/dev/null || true
  fi
  for pair in \
    "anti-slop-linter:anti_slop_linter.py" \
    "mega-downloader:mega_downloader.py" \
    "chroma-engine:chroma_engine.py" \
    "fontgen-engine:fontgen_engine.py" \
    "envato-font-preview:envato_font_preview.py"; do
    local bin_name="${pair%%:*}"
    local script_name="${pair#*:}"
    if [ -f "$CATALOG_DIR/scripts/$script_name" ]; then
      chmod +x "$CATALOG_DIR/scripts/$script_name"
      ln -sfn "$CATALOG_DIR/scripts/$script_name" "$LOCAL_BIN/$bin_name"
      ln -sfn "$CATALOG_DIR/scripts/$script_name" "$HOME/.local/bin/$bin_name"
      sudo ln -sfn "$LOCAL_BIN/$bin_name" "/usr/local/bin/$bin_name" 2>/dev/null || true
    fi
  done
  for h in tool-guard.py test_tool_guard.py; do
    if [ -f "$CATALOG_DIR/scripts/hooks/$h" ]; then
      chmod +x "$CATALOG_DIR/scripts/hooks/$h"
      ln -sfn "$CATALOG_DIR/scripts/hooks/$h" "$LOCAL_BIN/hooks/$h"
    fi
  done
  sudo ln -sfn "$CATALOG_DIR/iniciar.sh" /usr/local/bin/zcp-update || true
}

sync_governance() {
  mkdir -p "$BASE_DIR/.agents/rules" "$HOME/.gemini/config/rules"
  if [ -f "$CATALOG_DIR/AGENTS.md" ]; then
    if [ ! -f "$BASE_DIR/AGENTS.md" ]; then
      cp -f "$CATALOG_DIR/AGENTS.md" "$BASE_DIR/AGENTS.md"
    else
      python3 - "$CATALOG_DIR/AGENTS.md" "$BASE_DIR/AGENTS.md" << 'EOF_SYNC_CUSTOM'
import re, sys
src_p, dst_p = sys.argv[1], sys.argv[2]
src = open(src_p, "r", encoding="utf-8").read()
dst = open(dst_p, "r", encoding="utf-8").read()
m_src = re.search(r'<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->', src, flags=re.S)
if m_src:
    block = m_src.group(0)
    if re.search(r'<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->', dst, flags=re.S):
        out = re.sub(r'<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->', lambda _: block, dst, count=1, flags=re.S)
    else:
        out = dst.rstrip() + "\n\n" + block + "\n"
    if out != dst:
        with open(dst_p, "w", encoding="utf-8") as wf:
            wf.write(out)
EOF_SYNC_CUSTOM
    fi
  fi

  if [ -f "$CATALOG_DIR/.agents/rules/00-SUPREME-DIRECTIVE.md" ]; then
    cp -f "$CATALOG_DIR/.agents/rules/00-SUPREME-DIRECTIVE.md" "$BASE_DIR/.agents/rules/00-SUPREME-DIRECTIVE.md"
    ln -sfn "$BASE_DIR/.agents/rules/00-SUPREME-DIRECTIVE.md" "$HOME/.gemini/config/rules/00-SUPREME-DIRECTIVE.md"
    rm -f "$HOME/.gemini/antigravity-cli/rules/00-SUPREME-DIRECTIVE.md" 2>/dev/null || true
  fi

  for obsolete_rule in \
    gentle-ai-03-orchestrator-part1.md \
    gentle-ai-03-orchestrator-part2.md \
    gentle-ai-04-agent-routing-part1.md \
    gentle-ai-04-agent-routing-part2.md; do
    rm -f "$HOME/.gemini/config/rules/$obsolete_rule" 2>/dev/null || true
  done
  if [ -f "$CATALOG_DIR/scripts/templates/gentle-ai-02-engram-protocol.md" ]; then
    cp -f "$CATALOG_DIR/scripts/templates/gentle-ai-02-engram-protocol.md" "$HOME/.gemini/config/rules/gentle-ai-02-engram-protocol.md"
  fi
  rm -rf "$BASE_DIR/.atl" "$HOME/.gemini/GEMINI.md" "$HOME/.gemini/system.md" "$HOME/.gemini/antigravity-cli/references" 2>/dev/null || true

  if command -v agy >/dev/null 2>&1; then
    agy plugin disable gentle-ai-engram >/dev/null 2>&1 || true
  fi
  python3 - << 'EOF_ENGRAM_SINGLETON'
import json, os
cfg_path = os.path.expanduser("~/.gemini/config/config.json")
os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
try:
    cfg = json.load(open(cfg_path, "r", encoding="utf-8")) if os.path.isfile(cfg_path) else {}
except Exception:
    cfg = {}
cfg.setdefault("plugins", {}).setdefault("gentle-ai-engram", {})["enabled"] = False
with open(cfg_path, "w", encoding="utf-8") as wf:
    json.dump(cfg, wf, indent=2)
    wf.write("\n")

agy_settings = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
os.makedirs(os.path.dirname(agy_settings), exist_ok=True)
try:
    st = json.load(open(agy_settings, "r", encoding="utf-8")) if os.path.isfile(agy_settings) else {}
except Exception:
    st = {}
st.setdefault("model", "Orchestrator (Neon)")
tw = st.setdefault("trustedWorkspaces", [])
if "/var/www" not in tw:
    tw.append("/var/www")
with open(agy_settings, "w", encoding="utf-8") as wf:
    json.dump(st, wf, indent=2)
    wf.write("\n")
os.chmod(agy_settings, 0o600)

mcp_path = os.path.expanduser("~/.gemini/config/mcp_config.json")
if os.path.isfile(mcp_path):
    try:
        mcp = json.load(open(mcp_path, "r", encoding="utf-8"))
        srv = mcp.setdefault("mcpServers", {}).setdefault("engram", {})
        if os.path.isfile("/var/www/.bin/engram-mcp") or os.path.isfile("/var/www/zerops-astrobranding/scripts/engram-mcp"):
            srv["command"] = "/var/www/.bin/engram-mcp"
            srv["args"] = []
        srv["cwd"] = "/var/www"
        with open(mcp_path, "w", encoding="utf-8") as wf:
            json.dump(mcp, wf, indent=2)
            wf.write("\n")
        os.chmod(mcp_path, 0o600)
    except Exception:
        pass
EOF_ENGRAM_SINGLETON

  [ -f "$CATALOG_DIR/.agents/hooks.json" ] && cp -f "$CATALOG_DIR/.agents/hooks.json" "$BASE_DIR/.agents/hooks.json"
  mkdir -p "$BASE_DIR/artifacts"
  for dir_name in templates blueprints; do
    if [ -d "$CATALOG_DIR/$dir_name" ]; then
      if command -v rsync >/dev/null 2>&1; then
        mkdir -p "$BASE_DIR/artifacts/$dir_name"
        rsync -a --delete "$CATALOG_DIR/$dir_name/" "$BASE_DIR/artifacts/$dir_name/"
        if [ -d "$BASE_DIR/localstorage" ]; then
          mkdir -p "$BASE_DIR/localstorage/$dir_name"
          rsync -a --delete "$CATALOG_DIR/$dir_name/" "$BASE_DIR/localstorage/$dir_name/"
        fi
      else
        rm -rf "$BASE_DIR/artifacts/$dir_name"
        cp -a "$CATALOG_DIR/$dir_name" "$BASE_DIR/artifacts/$dir_name"
        if [ -d "$BASE_DIR/localstorage" ]; then
          rm -rf "$BASE_DIR/localstorage/$dir_name"
          cp -a "$CATALOG_DIR/$dir_name" "$BASE_DIR/localstorage/$dir_name"
        fi
      fi
    fi
  done
}

ensure_path() {
  local path_line='export PATH="/var/www/.bin:$HOME/.local/bin:$PATH"'
  if [ -f "$HOME/.bashrc" ] && ! grep -q '/var/www/.bin' "$HOME/.bashrc" 2>/dev/null; then
    printf '\n# ZCP sovereign CLIs\n%s\n' "$path_line" >> "$HOME/.bashrc"
  fi
  if [ -d /etc/profile.d ]; then
    echo "$path_line" | sudo tee /etc/profile.d/zcp_path.sh >/dev/null 2>&1 || true
    sudo chmod +x /etc/profile.d/zcp_path.sh 2>/dev/null || true
  fi
}

setup_localstorage() {
  local mnt="/mnt/localstorage"
  if [ -d "$mnt" ] && { mountpoint -q "$mnt" 2>/dev/null || [ -L "$BASE_DIR/localstorage" ] || [ -d "$mnt/engram" ] || [ -d "$mnt/apps" ]; }; then
    ln -sfn "$mnt" "$BASE_DIR/localstorage"
    log "LocalStorage active at $mnt"
    sync_playbooks "$mnt"
  else
    log "INFO: $mnt not mounted yet; skipping symlink to avoid split-brain."
  fi
}

sync_playbooks() {
  local storage_root="${1:-/mnt/localstorage}"
  local drive_hub="$DRIVE_MOUNT/KNOWLEDGE_HUB"
  local dst_pb="$storage_root/knowledge_hub/02_PLAYBOOKS_MAESTROS"
  if [ -d "$drive_hub/02_PLAYBOOKS_MAESTROS" ]; then
    mkdir -p "$dst_pb"
    rsync -au --delete "$drive_hub/02_PLAYBOOKS_MAESTROS/" "$dst_pb/" 2>/dev/null || cp -u "$drive_hub/02_PLAYBOOKS_MAESTROS"/* "$dst_pb/" 2>/dev/null || true
    log "Universal Playbooks synced to $dst_pb"
  fi
  if [ -d "$dst_pb" ]; then
    [ -d "$storage_root/playbooks" ] && [ ! -L "$storage_root/playbooks" ] && rm -rf "$storage_root/playbooks"
    ln -sfn "$dst_pb" "$storage_root/playbooks"
  fi
}

hydrate_project_vault() {
  [ "$SKIP_VAULT" = true ] && return 0

  local keys_file="$EXPLICIT_KEYS_FILE"
  if [ -z "$keys_file" ]; then
    reconcile_freellmapi_vault_scope
    return 0
  fi

  local vault_args=()
  [ -n "$PROJECT_OVERRIDE" ] && vault_args+=(--project "$PROJECT_OVERRIDE")
  [ "$COPYABLE_CREDS" = true ] && vault_args+=(--copyable-creds)

  local pool_args=()
  local pool_path
  for pool_path in "${EXTRA_POOLS[@]}"; do
    pool_args+=(--pool "$pool_path")
  done

  if [ -x "$CATALOG_DIR/scripts/setup-keys.sh" ]; then
    bash "$CATALOG_DIR/scripts/setup-keys.sh" --file "$keys_file" --non-interactive >/dev/null
    [ -f "$HOME/.env" ] && set -a && . "$HOME/.env" 2>/dev/null && set +a || true
  fi

  if [ -x "/usr/local/bin/zcp" ]; then
    if [ -x "$LOCAL_BIN/seed-project-vault" ]; then
      "$LOCAL_BIN/seed-project-vault" --keys "$keys_file" "${vault_args[@]}"
    else
      "$LOCAL_BIN/zeropsenv" sync "${vault_args[@]}" "$keys_file"
    fi
    if [ -x "$LOCAL_BIN/seed-freellmapi-keys" ]; then
      if PYTHONPATH="$CATALOG_DIR/scripts/lib" python3 - "$keys_file" "${EXTRA_POOLS[@]}" << 'EOF_HAS_POOLS'
import sys
from vault_env import collect_freellm_pools, discover_freellm_pools, parse_kv_file

kf = sys.argv[1]
extra = [p for p in sys.argv[2:] if p]
kv = parse_kv_file(kf)
pools = discover_freellm_pools(kf, extra)
keys_list, custom_providers, _ = collect_freellm_pools(pools, extra_kv=kv)
sys.exit(0 if (keys_list or custom_providers) else 1)
EOF_HAS_POOLS
      then
        "$LOCAL_BIN/seed-freellmapi-keys" --keys "$keys_file" "${vault_args[@]}" "${pool_args[@]}"
      else
        log "INFO: No FreeLLM pool specified for '$keys_file'; pass --pool <path> or set FREELLM_POOL_FILES to seed FreeLLMAPI."
      fi
    fi
    reconcile_freellmapi_vault_scope
  else
    log "WARN: /usr/local/bin/zcp not found; skipped Zerops Vault remote sync."
  fi
}

reconcile_freellmapi_vault_scope() {
  [ -x "/usr/local/bin/zcp" ] || return 0
  PYTHONPATH="$CATALOG_DIR/scripts/lib" python3 - "$CATALOG_DIR/scripts/seed-freellmapi-keys.sh" << 'EOF_RECONCILE'
import os, subprocess, sys
from vault_env import (
    FREELLMAPI_SERVICE_ONLY_KEYS,
    ZcpVaultClient,
    load_pending_freellmapi_seed,
)

seed_script = sys.argv[1]
pending = load_pending_freellmapi_seed()

with ZcpVaultClient() as zcp:
    services = zcp.list_services()
    if "freellmapi" not in services:
        sys.exit(0)
    _, proj_existing = zcp.get_project_envs()
    leaked = [k for k in sorted(FREELLMAPI_SERVICE_ONLY_KEYS) if k in proj_existing]
    if pending and os.path.isfile(seed_script):
        rc = subprocess.run(["bash", seed_script], check=False).returncode
        if rc == 0:
            sys.exit(0)
    if leaked:
        svc_existing = zcp.get_service_envs("freellmapi")
        to_copy = {}
        to_delete = []
        for k in leaked:
            val = os.environ.get(k) or os.environ.get(f"freellmapi_{k}") or ""
            if k in svc_existing:
                to_delete.append(k)
            elif val:
                to_copy[k] = val
                to_delete.append(k)
        if to_copy:
            zcp.upsert_service_envs("freellmapi", to_copy, skip_restart=True)
        if to_delete:
            zcp.delete_project_envs(to_delete, skip_restart=True)
            print(f"[iniciar] Migrated service-only FreeLLMAPI env(s) {to_delete} off Project Shared Vault onto 'freellmapi'.")
EOF_RECONCILE
}

resolve_project_slug_for_engram() {
  local cand="${PROJECT_OVERRIDE:-${ENGRAM_PROJECT:-${PROJECT_NAME:-}}}"
  if [ -z "$cand" ] && [ -n "$EXPLICIT_KEYS_FILE" ] && [ -f "$EXPLICIT_KEYS_FILE" ]; then
    cand="$(PYTHONPATH="$CATALOG_DIR/scripts/lib" python3 - "$EXPLICIT_KEYS_FILE" << 'EOF_KPROJ' 2>/dev/null || true
import sys
from vault_env import parse_kv_file
kv = parse_kv_file(sys.argv[1], filter_vault_ignored=False, include_operator_keys=True)
print((kv.get("ENGRAM_PROJECT") or kv.get("PROJECT_NAME") or "").strip())
EOF_KPROJ
)"
  fi
  if [ -z "$cand" ] && [ -x "$LOCAL_BIN/engram-sync" ]; then
    echo ""
    return 0
  fi
  printf '%s' "$cand" | tr '[:upper:]' '[:lower:]'
}

run_fresh_toolchain() {
  [ "$UPDATE_ONLY" = true ] && return 0

  if [ -f "$CATALOG_DIR/scripts/setup-gentle.sh" ]; then
    bash "$CATALOG_DIR/scripts/setup-gentle.sh" antigravity
  fi

  if [ "$SKIP_TOOLS" = false ]; then
    [ -f "$CATALOG_DIR/scripts/setup-browser.sh" ] && bash "$CATALOG_DIR/scripts/setup-browser.sh"
    [ -f "$CATALOG_DIR/scripts/setup-zcp.sh" ] && bash "$CATALOG_DIR/scripts/setup-zcp.sh"
    if [ -f "$CATALOG_DIR/scripts/setup-astrokey.sh" ]; then
      if [ -n "$EXPLICIT_KEYS_FILE" ]; then
        bash "$CATALOG_DIR/scripts/setup-astrokey.sh" --file "$EXPLICIT_KEYS_FILE" --non-interactive
      else
        bash "$CATALOG_DIR/scripts/setup-astrokey.sh" --non-interactive
      fi
    fi
    [ -f "$CATALOG_DIR/scripts/setup-gh.sh" ] && bash "$CATALOG_DIR/scripts/setup-gh.sh" || true
    [ -f "$CATALOG_DIR/scripts/harden-postgres-quotas.sh" ] && bash "$CATALOG_DIR/scripts/harden-postgres-quotas.sh" || true
  fi

  # Hydrate 3-tier Engram memory cleanly for this project
  if [ -x "$LOCAL_BIN/engram-sync" ]; then
    local eng_proj
    eng_proj="$(resolve_project_slug_for_engram)"
    if [ -n "$eng_proj" ]; then
      mkdir -p "$BASE_DIR/.engram"
      echo "{\"project_name\": \"$eng_proj\"}" > "$BASE_DIR/.engram/config.json"
      "$LOCAL_BIN/engram-sync" --pull --project "$eng_proj" || true
    else
      "$LOCAL_BIN/engram-sync" --pull || true
    fi
  fi
}

setup_pre_bifrost_deepseek() {
  if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
    log "DeepSeek API key detected (https://api.deepseek.com) for pre-Bifrost inference."
  fi
}

cleanup_residuals() {
  rm -rf "$CATALOG_DIR/scripts/__pycache__" "$CATALOG_DIR/scripts/hooks/__pycache__" "$LOCAL_BIN/hooks/__pycache__" "$BASE_DIR/.atl" 2>/dev/null || true
}

main() {
  parse_args "$@"
  if [ "$UPDATE_ONLY" = false ]; then
    install_os_deps
  fi
  sync_repo "$CATALOG_REPO" "$CATALOG_DIR"
  if [ "${INICIAR_REEXEC:-0}" != "1" ] && [ -f "$REPO_DIR/iniciar.sh" ]; then
    export INICIAR_REEXEC=1
    if [ "$UPDATE_ONLY" = true ]; then
      exec bash "$REPO_DIR/iniciar.sh" --update "$@"
    fi
    exec bash "$REPO_DIR/iniciar.sh" "$@"
  fi
  sync_repo "$SKILLS_REPO" "$SKILLS_DIR"
  [ "$UPDATE_ONLY" = false ] && ensure_gdrive_mount
  resolve_mandatory_keys
  setup_localstorage
  hydrate_project_vault
  link_bin
  run_fresh_toolchain
  link_skills
  sync_governance
  ensure_path
  setup_pre_bifrost_deepseek
  cleanup_residuals
  log "Bootstrap complete."
}

main "$@"
