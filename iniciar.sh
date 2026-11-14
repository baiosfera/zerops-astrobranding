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
EXPLICIT_KEYS_FILE=""
PROJECT_OVERRIDE=""

parse_args() {
  local args=("$@")
  local i=0
  while [ "$i" -lt "${#args[@]}" ]; do
    case "${args[$i]}" in
      --update)
        UPDATE_ONLY=true
        ;;
      --skip-vault)
        SKIP_VAULT=true
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
        echo "Uso: iniciar.sh [--update] [--keys /path/to/keys.md] [--project <slug>] [--skip-vault]"
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
  done
  log "Skills symlinked cleanly: $SKILLS_DIR -> $AGENTS_SKILLS_DIR"
}

link_bin() {
  mkdir -p "$LOCAL_BIN" "$LOCAL_BIN/hooks" "$HOME/.local/bin"
  for s in ssot-parity-check.sh skills-suite-validate.sh skills-sync.sh zcp-sync linear-cli apotelos brand-play engram-sync engram-mcp zeropsenv seed-freellmapi-keys.sh; do
    if [ -f "$CATALOG_DIR/scripts/$s" ]; then
      chmod +x "$CATALOG_DIR/scripts/$s"
      local bin_name="${s%.sh}"
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
  mkdir -p "$BASE_DIR/.agents/rules" "$HOME/.gemini/antigravity-cli/rules"
  [ -f "$CATALOG_DIR/AGENTS.md" ] && cp -f "$CATALOG_DIR/AGENTS.md" "$BASE_DIR/AGENTS.md"
  if [ -f "$CATALOG_DIR/.agents/rules/00-SUPREME-DIRECTIVE.md" ]; then
    cp -f "$CATALOG_DIR/.agents/rules/00-SUPREME-DIRECTIVE.md" "$BASE_DIR/.agents/rules/00-SUPREME-DIRECTIVE.md"
    cp -f "$CATALOG_DIR/.agents/rules/00-SUPREME-DIRECTIVE.md" "$HOME/.gemini/antigravity-cli/rules/00-SUPREME-DIRECTIVE.md"
  fi
  [ -f "$CATALOG_DIR/.agents/hooks.json" ] && cp -f "$CATALOG_DIR/.agents/hooks.json" "$BASE_DIR/.agents/hooks.json"
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
  else
    log "INFO: $mnt not mounted yet; skipping symlink to avoid split-brain."
  fi
}

hydrate_project_vault() {
  [ "$SKIP_VAULT" = true ] && return 0

  local keys_file="${EXPLICIT_KEYS_FILE:-${ZCP_KEYS_FILE:-}}"
  # Only auto-hydrate without explicit --keys during fresh install (`--update` alone stays read/sync-safe)
  if [ -z "$keys_file" ] && [ "$UPDATE_ONLY" = false ] && [ -f "$DEFAULT_KEYS_FILE" ]; then
    keys_file="$DEFAULT_KEYS_FILE"
  fi

  if [ -z "$keys_file" ]; then
    if [ "$UPDATE_ONLY" = false ]; then
      log "WARN: No master keys file detected (expected --keys <path> or $DEFAULT_KEYS_FILE). Run 'zcp-update --update --keys /path/to/keys.md' before deploying runtimes."
    fi
    return 0
  fi

  if [ ! -f "$keys_file" ]; then
    log "ERROR: Master keys file not found: $keys_file" >&2
    return 1
  fi

  local proj_args=()
  if [ -n "$PROJECT_OVERRIDE" ]; then
    proj_args=(--project "$PROJECT_OVERRIDE")
  fi

  if [ -x "$CATALOG_DIR/scripts/setup-keys.sh" ]; then
    bash "$CATALOG_DIR/scripts/setup-keys.sh" --file "$keys_file" --non-interactive >/dev/null
  fi

  if [ -x "/usr/local/bin/zcp" ]; then
    "$LOCAL_BIN/zeropsenv" sync "${proj_args[@]}" "$keys_file"
    if [ -x "$LOCAL_BIN/seed-freellmapi-keys" ]; then
      "$LOCAL_BIN/seed-freellmapi-keys" --keys "$keys_file" "${proj_args[@]}"
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
    exec bash "$REPO_DIR/iniciar.sh" "$@"
  fi
  sync_repo "$SKILLS_REPO" "$SKILLS_DIR"
  link_skills
  link_bin
  sync_governance
  ensure_path
  setup_localstorage
  hydrate_project_vault
  setup_pre_bifrost_deepseek
  log "Bootstrap complete."
}

main "$@"
