#!/usr/bin/env bash
# ==============================================================================
# Iniciar ZCP: Bootstrapper Soberano Autónomo (iniciar.sh v1.7)
# Repositorio: https://github.com/baiosfera/zerops-astrobranding
# Ejecución Mínima: curl -fsSL https://raw.githubusercontent.com/baiosfera/zerops-astrobranding/main/iniciar.sh | bash
# ==============================================================================

# 0. Auto-re-ejecución en bash si se invoca desde sh, dash o terminal sin bash interactivo
if [ -z "${BASH_VERSION:-}" ]; then
    if command -v bash >/dev/null 2>&1; then
        exec bash "$0" "$@"
    else
        echo "❌ Error: bash es requerido para ejecutar este bootstrapper."
        exit 1
    fi
fi

set -euo pipefail

# 0a. Carga automática de variables del contenedor Zerops y resolución de prefijos
if [ -f /etc/environment ]; then
    set -a
    source /etc/environment 2>/dev/null || true
    set +a
fi

# Unificar variables inyectadas por Zerops con prefijo core_ si no están en entorno plano
for var in $(env | grep -E '^core_' | sed 's/=.*//' || true); do
    target_var="${var#core_}"
    if [ -z "${!target_var:-}" ]; then
        export "$target_var"="${!var}"
    fi
done

echo "============================================================"
echo "  🚀 INICIANDO BOOTSTRAP SOBERANO ZCP (iniciar.sh v1.7 - Storage & Permission Resilient)"
echo "============================================================"

PROJECT_ROOT="${PROJECT_ROOT:-/var/www}"
REPO_URL="https://github.com/baiosfera/zerops-astrobranding.git"
REPO_NAME="$(basename "$REPO_URL" .git)"
REPO_DIR="${PROJECT_ROOT}/zerops-astrobranding"
DRIVE_MOUNT="${GDRIVE_MOUNT_DIR:-/var/www/baiosfera}"
SSOT_SCRIPTS="$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/scripts"

# Manejo de argumentos opcionales (--keys, --project, --repo)
KEYS_FILE_ARG=""
PROJECT_NAME_ARG=""
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --keys|-k)
            if [ -n "${2:-}" ] && [ -f "$2" ]; then
                echo "• Cargando archivo de credenciales externas: $2"
                set -a; source "$2"; set +a
                KEYS_FILE_ARG="$2"
            fi
            shift 2 ;;
        --project|-p|--client|-c)
            PROJECT_NAME_ARG="${2:-}"
            shift 2 ;;
        --repo|-r)
            REPO_URL="${2:-}"
            REPO_NAME="$(basename "$REPO_URL" .git)"
            REPO_DIR="${PROJECT_ROOT}/$REPO_NAME"
            shift 2 ;;
        *) shift ;;
    esac
done

# Cargar gdrive.env si existe en .rclone o en la raíz (compatibilidad y auto-sanación de permisos)
if [ -f "$PROJECT_ROOT/.rclone/gdrive.env" ]; then
    if [ ! -r "$PROJECT_ROOT/.rclone/gdrive.env" ] && command -v sudo >/dev/null 2>&1; then
        sudo chown -R "$(id -un):$(id -gn)" "$PROJECT_ROOT/.rclone" 2>/dev/null || sudo chmod 644 "$PROJECT_ROOT/.rclone/gdrive.env" 2>/dev/null || true
    fi
    if [ -r "$PROJECT_ROOT/.rclone/gdrive.env" ]; then
        set -a; source "$PROJECT_ROOT/.rclone/gdrive.env" 2>/dev/null || true; set +a
    fi
elif [ -f "$PROJECT_ROOT/gdrive.env" ]; then
    if [ ! -r "$PROJECT_ROOT/gdrive.env" ] && command -v sudo >/dev/null 2>&1; then
        sudo chown "$(id -un):$(id -gn)" "$PROJECT_ROOT/gdrive.env" 2>/dev/null || sudo chmod 644 "$PROJECT_ROOT/gdrive.env" 2>/dev/null || true
    fi
    if [ -r "$PROJECT_ROOT/gdrive.env" ]; then
        set -a; source "$PROJECT_ROOT/gdrive.env" 2>/dev/null || true; set +a
    fi
fi

# Determinar identidad agnóstica de proyecto (prioridad: CLI > gdrive.env / env > repo name)
TARGET_PROJECT="${PROJECT_NAME_ARG:-${PROJECT_NAME:-${CLIENT_NAME:-}}}"
APP_IDENTITY="${TARGET_PROJECT:-$REPO_NAME}"
APP_IDENTITY_LOWER="$(echo "$APP_IDENTITY" | tr '[:upper:]' '[:lower:]')"

export PROJECT_NAME="$APP_IDENTITY"
export ENGRAM_PROJECT="$APP_IDENTITY_LOWER"
if [ -w /etc/environment ] || command -v sudo >/dev/null 2>&1; then
    sudo sed -i '/^ENGRAM_PROJECT=/d;/^PROJECT_NAME=/d' /etc/environment 2>/dev/null || true
    echo "ENGRAM_PROJECT=$APP_IDENTITY_LOWER" | sudo tee -a /etc/environment >/dev/null 2>&1 || true
    echo "PROJECT_NAME=$APP_IDENTITY" | sudo tee -a /etc/environment >/dev/null 2>&1 || true
fi

# Garantizar aislamiento soberano de espacio de nombres en Engram (.engram/config.json)
mkdir -p "$PROJECT_ROOT/.engram"
echo "{\"project_name\": \"$APP_IDENTITY_LOWER\"}" > "$PROJECT_ROOT/.engram/config.json"

# Auto-adopción de ZCP_API_KEY desde el runtime Zerops
if [ -n "${ZCP_API_KEY:-}" ]; then
    export Z_TOKEN="$ZCP_API_KEY"
    export ZEROPS_TOKEN="$ZCP_API_KEY"
    if [ -w /etc/environment ] || command -v sudo >/dev/null 2>&1; then
        sudo sed -i '/^Z_TOKEN=/d;/^ZEROPS_TOKEN=/d' /etc/environment 2>/dev/null || true
        echo "Z_TOKEN=$ZCP_API_KEY" | sudo tee -a /etc/environment >/dev/null 2>&1 || true
        echo "ZEROPS_TOKEN=$ZCP_API_KEY" | sudo tee -a /etc/environment >/dev/null 2>&1 || true
    fi
fi

# 0b. Guardia Resiliente: Detección, Auto-Montaje y Fallback Local (Zero Bloqueos)
echo "• Verificando servicio de almacenamiento persistente localstorage..."
LOCALSTORAGE_FOUND=false
LOCALSTORAGE_HOST="localstorage"
FALLBACK_DIR="${PROJECT_ROOT}/.storage_fallback"

# 1. Comprobación de puntos de montaje ya existentes en /mnt/
for cand in "${LOCAL_STORAGE:-}" "localstorage" "storage" "data"; do
    [ -z "$cand" ] && continue
    if [ -d "/mnt/$cand" ] && mountpoint -q "/mnt/$cand" 2>/dev/null; then
        LOCALSTORAGE_FOUND=true
        LOCALSTORAGE_HOST="$cand"
        break
    fi
done

# 2. Comprobación de conectividad de red SSH al servicio Zerops
if [ "$LOCALSTORAGE_FOUND" = false ]; then
    for cand in "${LOCAL_STORAGE:-}" "localstorage" "storage" "data"; do
        [ -z "$cand" ] && continue
        if timeout 3s ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o BatchMode=yes -o ConnectTimeout=2 "$cand" "test -d /data" 2>/dev/null; then
            LOCALSTORAGE_FOUND=true
            LOCALSTORAGE_HOST="$cand"
            break
        fi
    done
fi

if [ "$LOCALSTORAGE_FOUND" = true ]; then
    echo "  ✓ Servicio persistente '$LOCALSTORAGE_HOST' detectado y accesible vía red."
    sudo mkdir -p "/mnt/$LOCALSTORAGE_HOST"
    if ! mountpoint -q "/mnt/$LOCALSTORAGE_HOST"; then
        echo "  • Montando $LOCALSTORAGE_HOST:/data en /mnt/$LOCALSTORAGE_HOST vía SSHFS..."
        sudo sshfs -o StrictHostKeyChecking=no,UserKnownHostsFile=/dev/null,allow_other,default_permissions,reconnect,ServerAliveInterval=15,ServerAliveCountMax=3 "$LOCALSTORAGE_HOST:/data" "/mnt/$LOCALSTORAGE_HOST" || true
    fi

    # Migrar datos previos si existía un fallback local activo
    if [ -d "$FALLBACK_DIR" ] && mountpoint -q "/mnt/$LOCALSTORAGE_HOST"; then
        echo "  • Migrando datos temporales de fallback local hacia almacenamiento persistente remoto..."
        sudo cp -rn "$FALLBACK_DIR"/* "/mnt/$LOCALSTORAGE_HOST/" 2>/dev/null || true
        sudo rm -rf "$FALLBACK_DIR"
    fi

    sudo ln -sfn "/mnt/$LOCALSTORAGE_HOST" "$PROJECT_ROOT/$LOCALSTORAGE_HOST"
    echo "  ✓ Volumen persistente montado y enlazado: $PROJECT_ROOT/$LOCALSTORAGE_HOST -> /mnt/$LOCALSTORAGE_HOST"
else
    echo "  ⚠️ Servicio remoto 'localstorage' no detectado aún en el proyecto Zerops."
    echo "  📦 Activando almacenamiento persistente LOCAL en $FALLBACK_DIR (MODO RESILIENTE - CERO BLOQUEOS)..."

    # Garantizar estructura de directorios requerida inmediatamente para que Engram, SQLite y FreeLLMAPI no fallen
    sudo mkdir -p "$FALLBACK_DIR/freellmapi" "$FALLBACK_DIR/engram"
    sudo chown -R zerops:zerops "$FALLBACK_DIR"
    sudo ln -sfn "$FALLBACK_DIR" "$PROJECT_ROOT/$LOCALSTORAGE_HOST"
    echo "fallback" > "$FALLBACK_DIR/.storage_mode"
    echo "  ✓ Fallback local activo: $PROJECT_ROOT/$LOCALSTORAGE_HOST -> $FALLBACK_DIR"
    echo "  → La instalación continúa sin bloqueos. No se requiere intervención manual."

    # Intentar auto-aprovisionamiento soberano vía zcp JSON-RPC stdio si ZCP_API_KEY y zcp están presentes
    if [ -x "/usr/local/bin/zcp" ] && [ -n "${ZCP_API_KEY:-}" ] && command -v python3 >/dev/null 2>&1; then
        echo "  🤖 Intentando auto-aprovisionar 'localstorage' en Zerops vía puente autónomo ZCP..."
        python3 -c '
import subprocess, json, sys

try:
    proc = subprocess.Popen(["/usr/local/bin/zcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    def rpc(m):
        proc.stdin.write(json.dumps(m) + "\n")
        proc.stdin.flush()
        while True:
            l = proc.stdout.readline()
            if not l: return None
            try:
                d = json.loads(l)
                if "id" in d and d.get("id") == m.get("id"): return d
            except: pass

    rpc({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"bootstrap-bridge","version":"1.0"}}})
    proc.stdin.write(json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"}) + "\n")
    proc.stdin.flush()

    # Iniciar workflow bootstrap
    rpc({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"zerops_workflow","arguments":{"action":"start","workflow":"bootstrap","intent":"provision localstorage","route":"classic"}}})

    # Importar servicio localstorage
    storage_yaml = """services:
  - hostname: localstorage
    type: local-storage:single@1
    verticalAutoscaling:
      cpuMode: SHARED
    priority: 10
"""
    rpc({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"zerops_import","arguments":{"content": storage_yaml}}})
    proc.terminate()
    print("  ✓ Solicitud de aprovisionamiento de localstorage enviada a Zerops con éxito.")
except Exception as e:
    print(f"  ℹ️ Auto-aprovisionamiento diferido ({e}); operando en fallback local seguro.")
' 2>/dev/null || true
    fi
fi

# 1. Asegurar clonación del repositorio de la aplicación
if [ ! -d "$REPO_DIR" ]; then
    echo "• [1/4] Clonando repositorio de aplicación ($REPO_URL)..."
    git clone "$REPO_URL" "$REPO_DIR"
else
    echo "• [1/4] Repositorio detectado en $REPO_DIR. Sincronizando con origen..."
    git -C "$REPO_DIR" pull --ff-only 2>/dev/null || true
fi

# 2. Asegurar montaje de Google Drive SSoT vía gdrive.sh
if [ ! -d "$DRIVE_MOUNT/0ZEROPS-AGY" ]; then
    echo "• [2/4] Google Drive no montado. Ejecutando gdrive.sh..."
    if [ -f "$REPO_DIR/scripts/gdrive.sh" ]; then
        bash "$REPO_DIR/scripts/gdrive.sh"
    elif [ -f "$PROJECT_ROOT/scripts/gdrive.sh" ]; then
        bash "$PROJECT_ROOT/scripts/gdrive.sh"
    else
        echo "❌ Error crítico: No se encontró gdrive.sh para montar Google Drive."
        exit 1
    fi
else
    echo "• [2/4] Google Drive montado y verificado en $DRIVE_MOUNT."
fi

# 2a. Garantizar adopción de /artifacts como symlink persistente a Google Drive SSoT
SSOT_ARTIFACTS="$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/artifacts"
LOCAL_ARTIFACTS="$PROJECT_ROOT/artifacts"
mkdir -p "$SSOT_ARTIFACTS" 2>/dev/null || true
if [ -d "$LOCAL_ARTIFACTS" ] && [ ! -L "$LOCAL_ARTIFACTS" ]; then
    echo "• Migrando artefactos locales preexistentes hacia Google Drive SSoT..."
    cp -rn "$LOCAL_ARTIFACTS"/* "$SSOT_ARTIFACTS/" 2>/dev/null || true
    rm -rf "$LOCAL_ARTIFACTS"
fi
if [ ! -L "$LOCAL_ARTIFACTS" ]; then
    echo "• Enlazando /artifacts permanentemente a Google Drive SSoT..."
    ln -sfn "$SSOT_ARTIFACTS" "$LOCAL_ARTIFACTS"
fi
echo "  ✓ Symlink de /artifacts verificado -> $SSOT_ARTIFACTS"

# 2a-bis. Aprovisionar Persistencia Híbrida Hot/Cold de Engram
echo "• [2a-bis] Verificando persistencia híbrida Hot/Cold para Engram ($APP_IDENTITY_LOWER)..."
if command -v engram-sync >/dev/null 2>&1; then
    engram-sync --pull --project "$APP_IDENTITY_LOWER" || true
    engram-sync --status --project "$APP_IDENTITY_LOWER" || true
elif [ -f "$REPO_DIR/scripts/engram-sync" ]; then
    bash "$REPO_DIR/scripts/engram-sync" --pull --project "$APP_IDENTITY_LOWER" || true
    bash "$REPO_DIR/scripts/engram-sync" --status --project "$APP_IDENTITY_LOWER" || true
fi

# 2b. Aprovisionar catálogo soberano de skills desde GitHub (zerops-astro-skills)
SKILLS_REPO_URL="https://github.com/baiosfera/zerops-astro-skills.git"
SKILLS_LOCAL_DIR="/var/www/zerops-astro-skills"
if [ ! -d "$SKILLS_LOCAL_DIR/.git" ]; then
    echo "• [2b/4] Sincronizando catálogo de skills soberanas desde GitHub ($SKILLS_REPO_URL)..."
    git clone --depth 1 "$SKILLS_REPO_URL" "$SKILLS_LOCAL_DIR" 2>/dev/null || true
else
    echo "• [2b/4] Actualizando skills soberanas desde GitHub..."
    git -C "$SKILLS_LOCAL_DIR" pull --ff-only 2>/dev/null || true
fi

# 2c. Verificar disponibilidad de scripts SSoT en Google Drive (tolerancia de indexación FUSE)
echo "• [2c/4] Verificando disponibilidad de scripts SSoT en Google Drive..."
for i in $(seq 1 10); do
    [ -f "$SSOT_SCRIPTS/unisetup.sh" ] && break
    sleep 1
done

# 2d. Garantizar paridad activa de scripts de bootstrap entre SSoT y repositorio
if [ -f "$SSOT_SCRIPTS/iniciar.sh" ] && [ -f "$REPO_DIR/iniciar.sh" ]; then
    if ! cmp -s "$SSOT_SCRIPTS/iniciar.sh" "$REPO_DIR/iniciar.sh"; then
        cp -f "$SSOT_SCRIPTS/iniciar.sh" "$REPO_DIR/iniciar.sh" 2>/dev/null || true
    fi
fi
if [ -f "$SSOT_SCRIPTS/gdrive.sh" ] && [ -f "$REPO_DIR/scripts/gdrive.sh" ]; then
    if ! cmp -s "$SSOT_SCRIPTS/gdrive.sh" "$REPO_DIR/scripts/gdrive.sh"; then
        cp -f "$SSOT_SCRIPTS/gdrive.sh" "$REPO_DIR/scripts/gdrive.sh" 2>/dev/null || true
    fi
fi

# 3. Ejecutar orquestador maestro unisetup.sh (Cascada resiliente: Repositorio local -> Drive SSoT)
if [ -f "$REPO_DIR/scripts/unisetup.sh" ] || [ -f "$SSOT_SCRIPTS/unisetup.sh" ]; then
    echo "• [3/4] Resolviendo credenciales y ejecutando unisetup.sh..."
    RESOLVED_KEYS=""
    
    # Cascada de resolución agnóstica de credenciales:
    if [ -n "${KEYS_FILE_ARG:-}" ] && [ -f "$KEYS_FILE_ARG" ]; then
        RESOLVED_KEYS="$KEYS_FILE_ARG"
    elif [ -n "${KEYS_FILE:-}" ] && [ -f "$KEYS_FILE" ]; then
        RESOLVED_KEYS="$KEYS_FILE"
    elif [ -f "$PROJECT_ROOT/key.md" ]; then
        RESOLVED_KEYS="$PROJECT_ROOT/key.md"
    elif [ -f "$PROJECT_ROOT/keys.md" ]; then
        RESOLVED_KEYS="$PROJECT_ROOT/keys.md"
    elif [ -f "$PROJECT_ROOT/key.env" ]; then
        RESOLVED_KEYS="$PROJECT_ROOT/key.env"
    elif [ -f "$PROJECT_ROOT/keys.env" ]; then
        RESOLVED_KEYS="$PROJECT_ROOT/keys.env"
    elif [ -n "$TARGET_PROJECT" ]; then
        # Búsqueda específica en SSoT según el proyecto/cliente configurado
        for candidate in \
            "$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/apis/${TARGET_PROJECT}-keys.md" \
            "$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/apis/${TARGET_PROJECT}-key.md" \
            "$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/apis/${TARGET_PROJECT}.md" \
            "$DRIVE_MOUNT/0ZEROPS-AGY/users-apis/${TARGET_PROJECT}/${TARGET_PROJECT}-keys.md" \
            "$DRIVE_MOUNT/0ZEROPS-AGY/users-apis/${TARGET_PROJECT}/${TARGET_PROJECT}-key.md" \
            "$DRIVE_MOUNT/0ZEROPS-AGY/users-apis/${TARGET_PROJECT}/${TARGET_PROJECT}.md" \
            "$DRIVE_MOUNT/0ZEROPS-AGY/users-apis/${TARGET_PROJECT}/keys.md"; do
            if [ -f "$candidate" ]; then
                RESOLVED_KEYS="$candidate"
                break
            fi
        done
    else
        # Descubrimiento dinámico cuando no se especifica --project ni --keys
        DETECTED_PROFILES=()
        DETECTED_PATHS=()
        
        # 1. En apis de SSoT
        for f in "$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/apis/"*-keys.md; do
            if [ -f "$f" ]; then
                b=$(basename "$f")
                p="${b%-keys.md}"
                [[ "$p" =~ ^(astro_api|browser_api|keys) ]] && continue
                DETECTED_PROFILES+=("$p")
                DETECTED_PATHS+=("$f")
            fi
        done
        
        # 2. En users-apis
        for d in "$DRIVE_MOUNT/0ZEROPS-AGY/users-apis/"*; do
            if [ -d "$d" ]; then
                d_name=$(basename "$d")
                for f in "$d"/*keys*.md "$d"/*.md; do
                    if [ -f "$f" ]; then
                        f_base=$(basename "$f")
                        [[ "$f_base" =~ ^(directus|prompt-maestro) ]] && continue
                        DETECTED_PROFILES+=("$d_name")
                        DETECTED_PATHS+=("$f")
                        break
                    fi
                done
            fi
        done
        
        if [ ${#DETECTED_PROFILES[@]} -eq 1 ]; then
            RESOLVED_KEYS="${DETECTED_PATHS[0]}"
            TARGET_PROJECT="${DETECTED_PROFILES[0]}"
            echo "  ✓ Perfil único detectado en Google Drive SSoT: $TARGET_PROJECT ($RESOLVED_KEYS)"
        elif [ ${#DETECTED_PROFILES[@]} -gt 1 ]; then
            if [ -c /dev/tty ]; then
                echo "" > /dev/tty
                echo "============================================================" > /dev/tty
                echo "  🔑 MULTIPLES PERFILES DETECTADOS EN GOOGLE DRIVE SSOT" > /dev/tty
                echo "============================================================" > /dev/tty
                echo "No se especificó --project ni --keys. Selecciona el perfil para este ZCP:" > /dev/tty
                for idx in "${!DETECTED_PROFILES[@]}"; do
                    echo "  $((idx+1))) ${DETECTED_PROFILES[$idx]} (${DETECTED_PATHS[$idx]})" > /dev/tty
                done
                echo "  $(( ${#DETECTED_PROFILES[@]} + 1 ))) Ingresar ruta manual de archivo de claves" > /dev/tty
                echo "------------------------------------------------------------" > /dev/tty
                read -r -p "Selecciona una opción [1-$(( ${#DETECTED_PROFILES[@]} + 1 ))]: " SEL < /dev/tty
                if [[ "$SEL" =~ ^[0-9]+$ ]] && [ "$SEL" -ge 1 ] && [ "$SEL" -le "${#DETECTED_PROFILES[@]}" ]; then
                    chosen_idx=$((SEL - 1))
                    RESOLVED_KEYS="${DETECTED_PATHS[$chosen_idx]}"
                    TARGET_PROJECT="${DETECTED_PROFILES[$chosen_idx]}"
                elif [ "$SEL" -eq "$(( ${#DETECTED_PROFILES[@]} + 1 ))" ]; then
                    read -r -p "Ingresa la ruta absoluta de tu archivo de claves: " MANUAL_PATH < /dev/tty
                    if [ -n "$MANUAL_PATH" ] && [ -f "$MANUAL_PATH" ]; then
                        RESOLVED_KEYS="$MANUAL_PATH"
                    fi
                fi
            else
                echo "❌ Error: Múltiples perfiles de claves detectados en Drive (${DETECTED_PROFILES[*]})."
                echo "  Por favor especifica el proyecto con: iniciar.sh --project <nombre> o --keys <ruta>"
                exit 1
            fi
        fi
    fi

    # Fallback genérico agnóstico en SSoT (si existiese)
    if [ -z "$RESOLVED_KEYS" ] && [ -f "$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/apis/keys.md" ]; then
        RESOLVED_KEYS="$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/apis/keys.md"
    fi

    # Verificación estricta: Sin credenciales no hay entorno
    HAS_ENV_KEYS=false
    for test_key in GITHUB_TOKEN LINEAR_API_KEY EXA_API_KEY TAVILY_API_KEY GEMINI_API_KEY OPENAI_API_KEY; do
        if [ -n "${!test_key:-}" ]; then
            HAS_ENV_KEYS=true
            break
        fi
    done

    if [ -z "$RESOLVED_KEYS" ] && [ "$HAS_ENV_KEYS" = false ]; then
        if [ -c /dev/tty ]; then
            echo "" > /dev/tty
            echo "============================================================" > /dev/tty
            echo "  ⚠️ ATENCIÓN: SIN CREDENCIALES NO HAY ENTORNO" > /dev/tty
            echo "============================================================" > /dev/tty
            echo "No se detectaron claves en el entorno ni en Google Drive." > /dev/tty
            read -r -p "Ingresa la ruta de tu archivo de claves (.md / .env) [o 'q' para cancelar]: " USER_PROMPT_KEY < /dev/tty
            if [ -n "$USER_PROMPT_KEY" ] && [ -f "$USER_PROMPT_KEY" ]; then
                RESOLVED_KEYS="$USER_PROMPT_KEY"
            fi
        fi
    fi

    if [ -z "$RESOLVED_KEYS" ] && [ "$HAS_ENV_KEYS" = false ]; then
        echo ""
        echo "============================================================"
        echo "  ❌ ERROR CRÍTICO: SIN CREDENCIALES NO HAY ENTORNO"
        echo "============================================================"
        echo "No se encontraron claves válidas en el entorno ni en Google Drive."
        echo "El stack agéntico requiere credenciales para aprovisionarse."
        echo ""
        echo "Solución para inicializar este ZCP:"
        echo "  1. Ejecuta indicando tu archivo de claves:"
        echo "     curl -fsSL https://raw.githubusercontent.com/baiosfera/zerops-astrobranding/main/iniciar.sh | bash -s -- --keys /ruta/a/keys.md"
        echo "  2. O crea el archivo en la raíz del contenedor antes de ejecutar:"
        echo "     nano /var/www/keys.md && curl -fsSL ... | bash"
        echo "  3. O define las credenciales en /var/www/gdrive.env"
        echo "============================================================"
        exit 1
    fi

    KEYS_FLAG=()
    if [ -n "$RESOLVED_KEYS" ]; then
        echo "  🔑 Archivo de claves asignado: $RESOLVED_KEYS"
        KEYS_FLAG=("--file" "$RESOLVED_KEYS")
    else
        echo "  ℹ️ Continuando con credenciales existentes en las variables del contenedor."
    fi

    # Re-sincronizar identidad y Engram si TARGET_PROJECT fue resuelto dinámicamente
    if [ -n "$TARGET_PROJECT" ] && [ "$TARGET_PROJECT" != "$APP_IDENTITY" ]; then
        APP_IDENTITY="$TARGET_PROJECT"
        APP_IDENTITY_LOWER="$(echo "$APP_IDENTITY" | tr '[:upper:]' '[:lower:]')"
        export PROJECT_NAME="$APP_IDENTITY"
        export ENGRAM_PROJECT="$APP_IDENTITY_LOWER"
        if [ -w /etc/environment ] || command -v sudo >/dev/null 2>&1; then
            sudo sed -i '/^ENGRAM_PROJECT=/d;/^PROJECT_NAME=/d' /etc/environment 2>/dev/null || true
            echo "ENGRAM_PROJECT=$APP_IDENTITY_LOWER" | sudo tee -a /etc/environment >/dev/null 2>&1 || true
            echo "PROJECT_NAME=$APP_IDENTITY" | sudo tee -a /etc/environment >/dev/null 2>&1 || true
        fi
        mkdir -p "$PROJECT_ROOT/.engram"
        echo "{\"project_name\": \"$APP_IDENTITY_LOWER\"}" > "$PROJECT_ROOT/.engram/config.json"
        if command -v engram-sync >/dev/null 2>&1; then
            engram-sync --pull --project "$APP_IDENTITY_LOWER" || true
        fi
    fi

    if [ -f "$REPO_DIR/scripts/unisetup.sh" ]; then
        echo "• [3/4] Ejecutando unisetup.sh primario desde repositorio local ($REPO_DIR/scripts/unisetup.sh)..."
        bash "$REPO_DIR/scripts/unisetup.sh" --all "${KEYS_FLAG[@]}" < /dev/null
    elif [ -f "$SSOT_SCRIPTS/unisetup.sh" ]; then
        echo "• [3/4] Ejecutando unisetup.sh fallback desde Google Drive SSoT ($SSOT_SCRIPTS/unisetup.sh)..."
        bash "$SSOT_SCRIPTS/unisetup.sh" --all "${KEYS_FLAG[@]}" < /dev/null
    fi

    # 3b. Sembrado de claves declarativas en FreeLLMAPI y Zerops Environment
    if [ -f "$REPO_DIR/scripts/seed-freellmapi-keys.sh" ]; then
        echo "• [3b/4] Sembrando claves declarativas y aprovisionando secrets de IA..."
        bash "$REPO_DIR/scripts/seed-freellmapi-keys.sh" ${RESOLVED_KEYS:+--keys "$RESOLVED_KEYS"} || echo "  ⚠️ Seeding diferido hasta disponibilidad del servicio."
    fi

    # 3c. Garantizar instalación global de bifrost-cli para el puente agéntico
    if ! command -v bifrost-cli >/dev/null 2>&1; then
        echo "• [3c/4] Instalando @maximhq/bifrost-cli como puente agéntico de desarrollo..."
        sudo npm install -g @maximhq/bifrost-cli >/dev/null 2>&1 || true
        [ -f /usr/bin/bifrost ] && sudo ln -sf /usr/bin/bifrost /usr/local/bin/bifrost-cli || true
    fi
else
    echo "❌ Error: unisetup.sh no disponible ni en repositorio ($REPO_DIR/scripts) ni en Drive ($SSOT_SCRIPTS)."
    if command -v systemctl >/dev/null 2>&1 && ! systemctl is-active --quiet rclone-baiosfera.service; then
        echo "   El servicio rclone-baiosfera.service no está activo. Verificando diagnóstico:"
        sudo journalctl -u rclone-baiosfera.service -n 25 --no-pager || true
    fi
    exit 1
fi

# 4. Certificación final determinista
echo "• [4/4] Verificando paridad SSoT..."
if command -v ssot-parity-check >/dev/null 2>&1; then
    ssot-parity-check
elif [ -f "$SSOT_SCRIPTS/ssot-parity-check.sh" ]; then
    bash "$SSOT_SCRIPTS/ssot-parity-check.sh"
fi

# 4b. Purga obligatoria de archivos de entorno efímeros y residuales en raíz
echo "• [4b/4] Purgando archivos residuales de credenciales en /var/www/ para blindar el arranque de Zerops..."
# Resguardar gdrive.env en .rclone/ antes de purgar la raíz para no perder credenciales en reinicios
if [ -f "$PROJECT_ROOT/gdrive.env" ]; then
    mkdir -p "$PROJECT_ROOT/.rclone" 2>/dev/null || sudo mkdir -p "$PROJECT_ROOT/.rclone"
    cp -f "$PROJECT_ROOT/gdrive.env" "$PROJECT_ROOT/.rclone/gdrive.env" 2>/dev/null || sudo cp -f "$PROJECT_ROOT/gdrive.env" "$PROJECT_ROOT/.rclone/gdrive.env"
    if command -v sudo >/dev/null 2>&1; then
        sudo chown -R "$(id -un):$(id -gn)" "$PROJECT_ROOT/.rclone" 2>/dev/null || true
    fi
    chmod 600 "$PROJECT_ROOT/.rclone/gdrive.env" 2>/dev/null || sudo chmod 600 "$PROJECT_ROOT/.rclone/gdrive.env"
fi
rm -f "$PROJECT_ROOT/.env" "$PROJECT_ROOT/gdrive.env" "$PROJECT_ROOT"/key*.md "$PROJECT_ROOT"/key*.env 2>/dev/null || true

echo "============================================================"
echo "  🎉 BOOTSTRAP COMPLETADO CON ÉXITO — ENTORNO LISTO"
echo "============================================================"
