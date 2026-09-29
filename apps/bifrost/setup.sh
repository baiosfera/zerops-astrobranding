#!/usr/bin/env bash
set -euo pipefail

BIFROST_VERSION="v2.2.3"
TARGET_DIR="${1:-/usr/local/bin}"

echo "==> [Bifrost Setup] Installing Maxim AI Bifrost Gateway (${BIFROST_VERSION})..."

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "$ARCH" in
  x86_64) ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

DOWNLOAD_URL="https://downloads.getmaxim.ai/bifrost/${BIFROST_VERSION}/${OS}/${ARCH}/bifrost-http"

echo "==> Downloading from: ${DOWNLOAD_URL}"
curl -fsSL -o /tmp/bifrost "${DOWNLOAD_URL}"
chmod +x /tmp/bifrost

if [ -w "$TARGET_DIR" ]; then
  mv /tmp/bifrost "${TARGET_DIR}/bifrost"
else
  sudo mv /tmp/bifrost "${TARGET_DIR}/bifrost"
fi

echo "==> [Bifrost Setup] Successfully installed bifrost to ${TARGET_DIR}/bifrost"
"${TARGET_DIR}/bifrost" -version || true
