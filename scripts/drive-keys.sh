#!/usr/bin/env bash
# ==============================================================================
# Sovereign Google Drive Keys & Rclone Automator (drive-keys.sh v1.0)
# Agnóstico, Holístico y con Zero Plaintext Secrets
# Permite exportar credenciales de un ZCP activo e importarlas en un ZCP limpio.
# ==============================================================================
set -euo pipefail

RCLONE_CONF_DEFAULT="/var/www/.rclone/config/rclone/rclone.conf"
ENV_FILE_DEFAULT="${GDRIVE_ENV_FILE:-/var/www/.rclone/gdrive.env}"
MOUNT_DIR_DEFAULT="/var/www/baiosfera"
REMOTE_NAME_DEFAULT="baiosfera"

usage() {
    echo "Uso: drive-keys.sh [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  --export, -e              Exporta las credenciales actuales como comando one-line para ZCP limpio"
    echo "  --import, -i <PAYLOAD>    Importa credenciales desde token base64 y monta Google Drive"
    echo "  --interactive             Configuración interactiva segura (solicita keys de forma oculta)"
    echo "  --status, -s              Verifica el estado del montaje de Google Drive"
    echo "  --help, -h                Muestra este mensaje de ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  En ZCP actual:  drive-keys.sh --export"
    echo "  En ZCP limpio:  drive-keys.sh --import \"<PAYLOAD_BASE64>\""
    echo "  O interactivo:  drive-keys.sh --interactive"
    exit 0
}

mask_secret() {
    local val="$1"
    local len=${#val}
    if [ "$len" -le 8 ]; then
        echo "********"
    else
        echo "${val:0:4}...${val: -4}"
    fi
}

cmd_status() {
    echo "============================================================"
    echo "  🔍 ESTADO DE GOOGLE DRIVE Y CREDENCIALES (drive-keys)"
    echo "============================================================"
    
    local rclone_conf="${RCLONE_CONF:-$RCLONE_CONF_DEFAULT}"
    if [ -f "$rclone_conf" ]; then
        echo "✓ Archivo rclone.conf detectado: $rclone_conf (Permisos: $(stat -c '%a' "$rclone_conf" 2>/dev/null || stat -f '%A' "$rclone_conf" 2>/dev/null || echo 'OK'))"
        local remote=$(awk -F'[][]' '/^\[.*\]/{print $2}' "$rclone_conf" | head -n1)
        echo "  - Remote configurado: [${remote:-desconocido}]"
    else
        echo "⚠️ Archivo rclone.conf no encontrado en $rclone_conf"
    fi

    if [ -f "$ENV_FILE_DEFAULT" ]; then
        echo "✓ Archivo gdrive.env detectado: $ENV_FILE_DEFAULT"
    fi

    local mount_dir="${GDRIVE_MOUNT_DIR:-$MOUNT_DIR_DEFAULT}"
    if mountpoint -q "$mount_dir" 2>/dev/null || grep -qs "$mount_dir" /proc/mounts 2>/dev/null; then
        echo "✓ Montaje FUSE activo en $mount_dir"
        if timeout 5s ls "$mount_dir/0ZEROPS-AGY" >/dev/null 2>&1; then
            echo "✓ Comunicación y lectura SSoT verificada (0ZEROPS-AGY accesible)."
        else
            echo "⚠️ Montaje detectado pero el directorio SSoT no respondió en 5s."
        fi
    else
        echo "❌ Google Drive NO está montado actualmente en $mount_dir"
    fi
    echo "============================================================"
}

cmd_export() {
    local client_id=""
    local client_secret=""
    local refresh_token=""
    local remote_name="$REMOTE_NAME_DEFAULT"
    local rclone_conf="${RCLONE_CONF:-$RCLONE_CONF_DEFAULT}"

    # 1. Intentar leer desde rclone.conf
    if [ -f "$rclone_conf" ]; then
        client_id=$(awk -F' = ' '/client_id/{print $2}' "$rclone_conf" | tr -d ' "' | head -n1 || true)
        client_secret=$(awk -F' = ' '/client_secret/{print $2}' "$rclone_conf" | tr -d ' "' | head -n1 || true)
        refresh_token=$(python3 -c "
import json, re
with open('$rclone_conf', 'r') as f:
    c = f.read()
m = re.search(r'token\s*=\s*(\{.*\})', c)
if m:
    try:
        t = json.loads(m.group(1))
        print(t.get('refresh_token', ''))
    except:
        pass
" 2>/dev/null || true)
        remote_name=$(awk -F'[][]' '/^\[.*\]/{print $2}' "$rclone_conf" | head -n1 || echo "$REMOTE_NAME_DEFAULT")
    fi

    # 2. Fallback a variables de entorno si faltan en conf
    [ -z "$client_id" ] && client_id="${GDRIVE_CLIENT_ID:-${GOOGLE_CLIENT_ID:-}}"
    [ -z "$client_secret" ] && client_secret="${GDRIVE_CLIENT_SECRET:-${GOOGLE_CLIENT_SECRET:-}}"
    [ -z "$refresh_token" ] && refresh_token="${GDRIVE_REFRESH_TOKEN:-}"

    if [ -z "$client_id" ] || [ -z "$client_secret" ] || [ -z "$refresh_token" ]; then
        echo "❌ Error: No se encontraron credenciales completas de Google Drive en este entorno." >&2
        echo "   Verificá que $rclone_conf exista o que GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET y GDRIVE_REFRESH_TOKEN estén exportadas." >&2
        exit 1
    fi

    # Construir JSON seguro en memoria y codificar en base64
    local b64_payload
    b64_payload=$(python3 -c "
import json, base64
data = {
    'client_id': '''$client_id''',
    'client_secret': '''$client_secret''',
    'refresh_token': '''$refresh_token''',
    'remote_name': '''$remote_name''',
    'mount_dir': '''$MOUNT_DIR_DEFAULT'''
}
print(base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8'))
")

    echo "============================================================"
    echo "  📦 CREDENCIALES GOOGLE DRIVE EXPORTADAS (One-Line One-Click)"
    echo "============================================================"
    echo "• Remote: $remote_name"
    echo "• Client ID: $(mask_secret "$client_id")"
    echo "• Client Secret: $(mask_secret "$client_secret")"
    echo "• Refresh Token: $(mask_secret "$refresh_token")"
    echo ""
    echo "👉 En tu ZCP limpio, ejecutá este comando único para importar y montar:"
    echo ""
    echo "curl -fsSL https://raw.githubusercontent.com/catalinaglamur/zerops-astrobranding/main/scripts/drive-keys.sh | bash -s -- --import \"$b64_payload\""
    echo ""
    echo "O si ya clonaste el repo:"
    echo "bash /var/www/zerops-astrobranding/scripts/drive-keys.sh --import \"$b64_payload\""
    echo "============================================================"
}

cmd_import() {
    local payload="$1"
    if [ -z "$payload" ]; then
        echo "❌ Error: Debe proporcionar el payload base64 generado por --export." >&2
        exit 1
    fi

    echo "• Decodificando y validando credenciales de Google Drive..."
    local creds_json
    creds_json=$(python3 -c "
import json, base64, sys
try:
    raw = base64.b64decode('$payload').decode('utf-8')
    data = json.loads(raw)
    assert 'client_id' in data and 'client_secret' in data and 'refresh_token' in data
    print(json.dumps(data))
except Exception as e:
    sys.exit(1)
" || { echo "❌ Error: Payload base64 inválido o corrupto." >&2; exit 1; })

    local client_id client_secret refresh_token remote_name mount_dir
    client_id=$(python3 -c "import json; print(json.loads('''$creds_json''')['client_id'])")
    client_secret=$(python3 -c "import json; print(json.loads('''$creds_json''')['client_secret'])")
    refresh_token=$(python3 -c "import json; print(json.loads('''$creds_json''')['refresh_token'])")
    remote_name=$(python3 -c "import json; print(json.loads('''$creds_json''').get('remote_name', '$REMOTE_NAME_DEFAULT'))")
    mount_dir=$(python3 -c "import json; print(json.loads('''$creds_json''').get('mount_dir', '$MOUNT_DIR_DEFAULT'))")

    # 1. Configurar directorio local de rclone
    local local_root="/var/www/.rclone"
    local rclone_conf="$local_root/config/rclone/rclone.conf"
    sudo mkdir -p "$local_root/bin" "$local_root/config/rclone" "$local_root/vault/rclone" "$mount_dir" 2>/dev/null || true

    # Escribir rclone.conf determinista
    sudo tee "$rclone_conf" > /dev/null << EOF
[$remote_name]
type = drive
scope = drive
client_id = $client_id
client_secret = $client_secret
token = {"token_type":"Bearer","refresh_token":"$refresh_token"}
EOF
    sudo chmod 600 "$rclone_conf"
    sudo chown -R zerops:zerops "$local_root" 2>/dev/null || true
    echo "  ✓ Configuración rclone escrita con permisos 600: $rclone_conf"

    # 2. Generar gdrive.env seguro
    tee "$ENV_FILE_DEFAULT" > /dev/null << EOF
# Google Drive Environment Credentials (Generated by drive-keys.sh)
GDRIVE_CLIENT_ID="$client_id"
GDRIVE_CLIENT_SECRET="$client_secret"
GDRIVE_REFRESH_TOKEN="$refresh_token"
GDRIVE_REMOTE_NAME="$remote_name"
GDRIVE_MOUNT_DIR="$mount_dir"
EOF
    chmod 600 "$ENV_FILE_DEFAULT"
    echo "  ✓ Credenciales persistidas en $ENV_FILE_DEFAULT (Permisos 600)"

    # 3. Disparar montaje inmediato
    echo "• Iniciando montaje de Google Drive vía gdrive.sh..."
    if [ -f "/var/www/zerops-astrobranding/scripts/gdrive.sh" ]; then
        bash "/var/www/zerops-astrobranding/scripts/gdrive.sh"
    elif [ -f "$(dirname "$0")/gdrive.sh" ]; then
        bash "$(dirname "$0")/gdrive.sh"
    elif [ -f "/var/www/scripts/gdrive.sh" ]; then
        bash "/var/www/scripts/gdrive.sh"
    else
        echo "ℹ️ gdrive.sh no encontrado localmente; descargando versión canónica..."
        curl -fsSL https://raw.githubusercontent.com/catalinaglamur/zerops-astrobranding/main/scripts/gdrive.sh | bash
    fi

    cmd_status
}

cmd_interactive() {
    echo "============================================================"
    echo "  🔐 CONFIGURACIÓN INTERACTIVA DE GOOGLE DRIVE (drive-keys)"
    echo "============================================================"
    echo "Ingresá tus credenciales de Google Cloud Console (Drive API):"
    echo ""
    read -rp "OAuth Client ID: " in_client_id
    read -rsp "OAuth Client Secret: " in_client_secret; echo ""
    read -rsp "OAuth Refresh Token: " in_refresh_token; echo ""
    read -rp "Remote Name [baiosfera]: " in_remote
    in_remote="${in_remote:-$REMOTE_NAME_DEFAULT}"

    if [ -z "$in_client_id" ] || [ -z "$in_client_secret" ] || [ -z "$in_refresh_token" ]; then
        echo "❌ Error: Todos los campos son obligatorios." >&2
        exit 1
    fi

    local b64_payload
    b64_payload=$(python3 -c "
import json, base64
data = {
    'client_id': '''$in_client_id''',
    'client_secret': '''$in_client_secret''',
    'refresh_token': '''$in_refresh_token''',
    'remote_name': '''$in_remote''',
    'mount_dir': '''$MOUNT_DIR_DEFAULT'''
}
print(base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8'))
")
    cmd_import "$b64_payload"
}

# Router principal
case "${1:-}" in
    --export|-e)
        cmd_export
        ;;
    --import|-i)
        shift
        cmd_import "${1:-}"
        ;;
    --interactive)
        cmd_interactive
        ;;
    --status|-s)
        cmd_status
        ;;
    --help|-h|"")
        usage
        ;;
    *)
        echo "❌ Opción desconocida: $1" >&2
        usage
        ;;
esac
