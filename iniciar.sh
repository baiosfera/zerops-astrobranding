#!/usr/bin/env bash
# ==============================================================================
# iniciar.sh — Sovereign Lightweight ZCP Bootstrapper (v3.0)
# Clean, brand-free, binary-free bootstrap for Zerops Control Plane (zcp).
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
UPDATE_ONLY=false

if [ "${1:-}" = "--update" ]; then
  UPDATE_ONLY=true
fi

log() { echo "[iniciar] $*"; }

install_os_deps() {
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq curl git jq fuse3 sshfs gettext-base >/dev/null
  elif command -v apk >/dev/null 2>&1; then
    sudo apk add --no-cache curl git jq fuse3 sshfs gettext >/dev/null
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
  for s in ssot-parity-check.sh skills-suite-validate.sh skills-sync.sh zcp-sync linear-cli apotelos brand-play engram-sync engram-mcp; do
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
  if [ -f "$CATALOG_DIR/scripts/anti_slop_linter.py" ]; then
    chmod +x "$CATALOG_DIR/scripts/anti_slop_linter.py"
    ln -sfn "$CATALOG_DIR/scripts/anti_slop_linter.py" "$LOCAL_BIN/anti-slop-linter"
    ln -sfn "$CATALOG_DIR/scripts/anti_slop_linter.py" "$HOME/.local/bin/anti-slop-linter"
  fi
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

setup_pre_bifrost_deepseek() {
  if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
    log "DeepSeek V4 API key detected (https://api.deepseek.com) for pre-Bifrost inference."
  fi
}

main() {
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
  setup_pre_bifrost_deepseek
  log "Bootstrap complete."
}

main "$@"
