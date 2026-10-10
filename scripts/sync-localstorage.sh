#!/usr/bin/env bash
# Sync GDrive FUSE to SSHFS Localstorage for Brandview App
SRC_BASE="/var/www/baiosfera"
DEST_BASE="/mnt/localstorage/baiosfera"

# Asegurar directorios destino
mkdir -p "$DEST_BASE/ASTROLOGÍA/DIAG" "$DEST_BASE/FUENTES/ENVATO" 2>/dev/null || true

# Sincronizar DIAG
echo "[SYNC] Sincronizando ASTROLOGÍA/DIAG..."
rsync -a --delete --exclude='*.mp4' --exclude='*.mov' "$SRC_BASE/ASTROLOGÍA/DIAG/" "$DEST_BASE/ASTROLOGÍA/DIAG/"

# Sincronizar ENVATO
echo "[SYNC] Sincronizando FUENTES/ENVATO..."
rsync -a --delete --exclude='*.mp4' --exclude='*.mov' "$SRC_BASE/FUENTES/ENVATO/" "$DEST_BASE/FUENTES/ENVATO/"

echo "[SYNC] Completado."
