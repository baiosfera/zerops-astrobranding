#!/usr/bin/env bash
# ==============================================================================
# Paperclip Autonomous Runtime Entrypoint
# ==============================================================================
set -e

CONFIG_DIR="/mnt/localstorage/paperclip/instances/default"
CONFIG_FILE="${CONFIG_DIR}/config.json"

echo "• [Paperclip] Iniciando verificación de configuración declarativa..."

# 1. Normalizar DATABASE_URL hacia la base de datos 'paperclip'
if [[ "${DATABASE_URL}" == *"/db" ]]; then
    export DATABASE_URL="${DATABASE_URL%/db}/paperclip"
fi

# 2. Auto-seed config.json con esquema estricto Zod si no existe en disco NVMe
if [ ! -f "$CONFIG_FILE" ]; then
    echo "• [Paperclip] Generando config.json declarativo en ${CONFIG_FILE}..."
    mkdir -p "$CONFIG_DIR" "$CONFIG_DIR/logs" "/mnt/localstorage/paperclip/storage" 2>/dev/null || true
    cat << EOF > "$CONFIG_FILE"
{
  "\$meta": {
    "version": 1,
    "updatedAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "source": "configure"
  },
  "database": {
    "mode": "postgres",
    "connectionString": "${DATABASE_URL}"
  },
  "logging": {
    "mode": "file",
    "logDir": "${CONFIG_DIR}/logs"
  },
  "server": {
    "deploymentMode": "${PAPERCLIP_DEPLOYMENT_MODE:-authenticated}",
    "exposure": "${PAPERCLIP_DEPLOYMENT_EXPOSURE:-public}",
    "bind": "${PAPERCLIP_BIND:-lan}",
    "host": "${HOST:-0.0.0.0}",
    "port": ${PORT:-3100}
  },
  "auth": {
    "baseUrlMode": "explicit",
    "publicBaseUrl": "${BETTER_AUTH_URL:-https://${zerops_subdomain}}",
    "disableSignUp": false
  },
  "telemetry": {
    "enabled": false
  }
}
EOF
fi

# 3. Garantizar symlink canónico ~/.paperclip -> /mnt/localstorage/paperclip en runtime
mkdir -p "$HOME"
ln -sfn /mnt/localstorage/paperclip "$HOME/.paperclip"

# 4. Iniciar servidor Node.js
echo "• [Paperclip] Ejecutando runtime index.mjs en puerto ${PORT:-3100}..."
exec node server/dist-runtime/index.mjs
