#!/usr/bin/env bash
# ==============================================================================
# iniciar.sh — Sovereign Lightweight ZCP Bootstrapper & Project Vault Hydrator (v3.1)
# Clean, brand-free bootstrap for Zerops Control Plane (zcp).
# Supports optional `--keys <path>` (default: users-apis/api_keys_global) to hydrate
# brand/project secrets & multi-pool FreeLLMAPI config directly into zerops_env.
# ==============================================================================
set -euo pipefail

BASE_DIR="/var/www"
CATALOG_REPO="https://github.com/baiosfera/zerops-astrobranding.git"
SKILLS_REPO="https://github.com/baiosfera/zerops-astro-skills.git"
REPO_DIR="$BASE_DIR/zerops-astrobranding"
CATALOG_DIR="$REPO_DIR"
SKILLS_DIR="$BASE_DIR/zerops-astro-skills"
AGENTS_SKILLS_DIR="$BASE_DIR/.agents/skills"
LOCAL_BIN="$BASE_DIR/.bin"
DEFAULT_KEYS_FILE="/var/www/baiosfera/0ZEROPS-AGY/users-apis/api_keys_global"

UPDATE_ONLY=false
SKIP_VAULT=false
COPYABLE_CREDS=false
EXPLICIT_KEYS_FILE=""
PROJECT_OVERRIDE=""
EXTRA_POOLS=()

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
        echo "Uso: iniciar.sh [--update|--full] [--keys /path/to/keys.md] [--pool /path/to/pool_freellm.md] [--project <slug>] [--copyable-creds] [--skip-vault]"
        exit 0
        ;;
    esac
    i=$((i + 1))
  done
}

log() { echo "[iniciar] $*"; }

install_os_deps() {
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq curl git jq fuse3 sshfs gettext-base python3-yaml >/dev/null
  elif command -v apk >/dev/null 2>&1; then
    sudo apk add --no-cache curl git jq fuse3 sshfs gettext py3-yaml >/dev/null
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
    # Purge stale frozen copies in secondary agent dirs that shadow .agents/skills symlinks
    rm -rf "$HOME/.gemini/antigravity-cli/skills/$name" "$HOME/.gemini/config/skills/$name" "$BASE_DIR/.claude/skills/$name" 2>/dev/null || true
  done

  # Purge Group E third-party noise & empty broken dirs across all discovery paths
  for noise_sk in jira-epic jira-task gentle-ai-bench gentle-ai-collab-perfect rdd-advisory-transport rdd-defect-workflow migrate-to-shoehorn scaffold-exercises django-drf angular; do
    rm -rf "$AGENTS_SKILLS_DIR/$noise_sk" "$HOME/.gemini/antigravity-cli/skills/$noise_sk" "$HOME/.gemini/config/skills/$noise_sk" "$BASE_DIR/.claude/skills/$noise_sk" "$BASE_DIR/localstorage/skills/$noise_sk" 2>/dev/null || true
  done

  # Dereference-sync consolidated skills into localstorage for Hermes runtime (when mounted)
  if [ -d "$BASE_DIR/localstorage" ] && command -v rsync >/dev/null 2>&1; then
    mkdir -p "$BASE_DIR/localstorage/skills"
    rsync -aL --delete --exclude="__pycache__" --exclude="*.pyc" --exclude="*.bak" --exclude=".git" --exclude="AGENTS.md" "$AGENTS_SKILLS_DIR/" "$BASE_DIR/localstorage/skills/" 2>/dev/null || true
  fi

  # Refresh skill registry index cleanly
  if command -v gentle-ai >/dev/null 2>&1; then
    gentle-ai skill-registry refresh --cwd "$BASE_DIR" --force --no-gitignore >/dev/null 2>&1 || true
  fi

  log "Skills symlinked & deduplicated cleanly: $SKILLS_DIR -> $AGENTS_SKILLS_DIR"
}

link_bin() {
  mkdir -p "$LOCAL_BIN" "$LOCAL_BIN/hooks" "$HOME/.local/bin"
  for s in ssot-parity-check.sh skills-suite-validate.sh skills-sync.sh zcp-sync linear-cli apotelos brand-play engram-sync engram-mcp zeropsenv seed-project-vault.sh seed-freellmapi-keys.sh setup-gh.sh harden-postgres-quotas.sh zcp-mount zcp-mail.sh zcp-preflight-gate.sh zcp-wa.sh; do
    if [ -f "$CATALOG_DIR/scripts/$s" ]; then
      chmod +x "$CATALOG_DIR/scripts/$s"
      local bin_name="${s%.sh}"
      [ -e "$LOCAL_BIN/$bin_name" ] && [ ! -L "$LOCAL_BIN/$bin_name" ] && rm -f "$LOCAL_BIN/$bin_name"
      [ -e "$HOME/.local/bin/$bin_name" ] && [ ! -L "$HOME/.local/bin/$bin_name" ] && rm -f "$HOME/.local/bin/$bin_name"
      ln -sfn "$CATALOG_DIR/scripts/$s" "$LOCAL_BIN/$bin_name"
      ln -sfn "$CATALOG_DIR/scripts/$s" "$HOME/.local/bin/$bin_name"
    fi
  done
  if [ -f "$CATALOG_DIR/bin/orchesbrand" ]; then
    chmod +x "$CATALOG_DIR/bin/orchesbrand"
    ln -sfn "$CATALOG_DIR/bin/orchesbrand" "$LOCAL_BIN/orchesbrand"
    ln -sfn "$CATALOG_DIR/bin/orchesbrand" "$HOME/.local/bin/orchesbrand"
  fi
  for pair in "anti-slop-linter:anti_slop_linter.py" "mega-downloader:mega_downloader.py"; do
    local bin_name="${pair%%:*}"
    local script_name="${pair#*:}"
    if [ -f "$CATALOG_DIR/scripts/$script_name" ]; then
      chmod +x "$CATALOG_DIR/scripts/$script_name"
      ln -sfn "$CATALOG_DIR/scripts/$script_name" "$LOCAL_BIN/$bin_name"
      ln -sfn "$CATALOG_DIR/scripts/$script_name" "$HOME/.local/bin/$bin_name"
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
      # Preserve platform ZCP:BEGIN..ZCP:END and ZEROPS:REFLOG; sync only CUSTOM:BEGIN..CUSTOM:END
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

  # Purge conflicting ODD/budget-overflow rules so always_on stays under 20K agy token cap
  for obsolete_rule in \
    gentle-ai-03-orchestrator-part1.md \
    gentle-ai-03-orchestrator-part2.md \
    gentle-ai-04-agent-routing-part1.md \
    gentle-ai-04-agent-routing-part2.md; do
    rm -f "$HOME/.gemini/config/rules/$obsolete_rule" 2>/dev/null || true
  done

  # Ensure single Engram MCP server (--tools=agent, cwd=/var/www) and disable duplicate plugin
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
      else
        rm -rf "$BASE_DIR/artifacts/$dir_name"
        cp -a "$CATALOG_DIR/$dir_name" "$BASE_DIR/artifacts/$dir_name"
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
  if [ -d "$mnt" ] && mountpoint -q "$mnt" 2>/dev/null; then
    ln -sfn "$mnt" "$BASE_DIR/localstorage"
    log "LocalStorage mounted at $mnt"
    sync_playbooks "$mnt"
  else
    log "INFO: $mnt not mounted yet; skipping symlink to avoid split-brain."
  fi
}

sync_playbooks() {
  local storage_root="${1:-/mnt/localstorage}"
  local drive_hub="/var/www/baiosfera/KNOWLEDGE_HUB"
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

  # In update mode (`zcp-update`), ignore $ZCP_KEYS_FILE and $DEFAULT_KEYS_FILE unless --keys is passed explicitly.
  local keys_file="$EXPLICIT_KEYS_FILE"
  if [ -z "$keys_file" ] && [ "$UPDATE_ONLY" = false ]; then
    keys_file="${ZCP_KEYS_FILE:-}"
    if [ -z "$keys_file" ] && [ -f "$DEFAULT_KEYS_FILE" ]; then
      keys_file="$DEFAULT_KEYS_FILE"
    fi
  fi

  if [ -z "$keys_file" ]; then
    if [ "$UPDATE_ONLY" = false ]; then
      log "WARN: No master keys file detected (expected --keys <path> or $DEFAULT_KEYS_FILE). Run 'zcp-update --keys /path/to/keys.md' before deploying runtimes."
    fi
    return 0
  fi

  if [ ! -f "$keys_file" ]; then
    log "ERROR: Master keys file not found: $keys_file" >&2
    return 1
  fi

  local vault_args=()
  if [ -n "$PROJECT_OVERRIDE" ]; then
    vault_args+=(--project "$PROJECT_OVERRIDE")
  fi
  if [ "$COPYABLE_CREDS" = true ]; then
    vault_args+=(--copyable-creds)
  fi

  local pool_args=()
  local pool_path
  for pool_path in "${EXTRA_POOLS[@]}"; do
    pool_args+=(--pool "$pool_path")
  done

  if [ -x "$CATALOG_DIR/scripts/setup-keys.sh" ]; then
    bash "$CATALOG_DIR/scripts/setup-keys.sh" --file "$keys_file" --non-interactive >/dev/null
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
  else
    log "WARN: /usr/local/bin/zcp not found; skipped Zerops Vault remote sync."
  fi
}

setup_pre_bifrost_deepseek() {
  if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
    log "DeepSeek API key detected (https://api.deepseek.com) for pre-Bifrost inference."
  fi
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
  setup_localstorage
  link_skills
  link_bin
  sync_governance
  ensure_path
  hydrate_project_vault
  setup_pre_bifrost_deepseek
  log "Bootstrap complete."
}

main "$@"
