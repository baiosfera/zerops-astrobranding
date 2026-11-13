#!/usr/bin/env bash
# ==============================================================================
# iniciar.sh — Sovereign Lightweight ZCP Bootstrapper (v3.0)
# Clean, brand-free, binary-free bootstrap for Zerops Control Plane (zcp).
# ==============================================================================
set -euo pipefail

BASE_DIR="/var/www"
CATALOG_REPO="https://github.com/baiosfera/zerops-astrobranding.git"
SKILLS_REPO="https://github.com/baiosfera/zerops-astro-skills.git"
CATALOG_DIR="$BASE_DIR/zerops-astrobranding"
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
    ln -sfn "$SKILLS_DIR/$name" "$AGENTS_SKILLS_DIR/$name"
  done
  log "Skills symlinked cleanly: $SKILLS_DIR -> $AGENTS_SKILLS_DIR"
}

link_bin() {
  mkdir -p "$LOCAL_BIN" "$LOCAL_BIN/hooks"
  for s in ssot-parity-check.sh skills-suite-validate.sh zcp-sync linear-cli; do
    if [ -f "$CATALOG_DIR/scripts/$s" ]; then
      chmod +x "$CATALOG_DIR/scripts/$s"
      ln -sfn "$CATALOG_DIR/scripts/$s" "$LOCAL_BIN/${s%.sh}"
    fi
  done
  if [ -f "$CATALOG_DIR/scripts/hooks/tool-guard.py" ]; then
    ln -sfn "$CATALOG_DIR/scripts/hooks/tool-guard.py" "$LOCAL_BIN/hooks/tool-guard.py"
  fi
  sudo ln -sfn "$CATALOG_DIR/iniciar.sh" /usr/local/bin/zcp-update || true
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
  sync_repo "$SKILLS_REPO" "$SKILLS_DIR"
  link_skills
  link_bin
  setup_localstorage
  setup_pre_bifrost_deepseek
  log "Bootstrap complete."
}

main "$@"
