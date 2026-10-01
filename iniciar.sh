#!/usr/bin/env bash
# ==============================================================================
# Iniciar ZCP: Bootstrapper Soberano Autónomo (iniciar.sh)
# Repositorio: https://github.com/elplacerdc/zerops-astrobranding
# Ejecución Mínima: curl -fsSL https://raw.githubusercontent.com/elplacerdc/zerops-astrobranding/main/iniciar.sh | bash
# ==============================================================================
set -euo pipefail

echo "============================================================"
echo "  🚀 INICIANDO BOOTSTRAP SOBERANO ZCP (iniciar.sh v1.0)"
echo "============================================================"

PROJECT_ROOT="${PROJECT_ROOT:-/var/www}"
REPO_URL="https://github.com/elplacerdc/zerops-astrobranding.git"
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

# Cargar gdrive.env si existe en la raíz
if [ -f "$PROJECT_ROOT/gdrive.env" ]; then
    set -a; source "$PROJECT_ROOT/gdrive.env"; set +a
fi

# Determinar identidad agnóstica de proyecto (prioridad: CLI > gdrive.env / env > repo name)
TARGET_PROJECT="${PROJECT_NAME_ARG:-${PROJECT_NAME:-${CLIENT_NAME:-}}}"
APP_IDENTITY="${TARGET_PROJECT:-$REPO_NAME}"

export PROJECT_NAME="$APP_IDENTITY"
export ENGRAM_PROJECT="$APP_IDENTITY"
[ -f "$PROJECT_ROOT/.env" ] && sed -i '/^ENGRAM_PROJECT=/d' "$PROJECT_ROOT/.env" 2>/dev/null || true
echo "ENGRAM_PROJECT=$APP_IDENTITY" >> "$PROJECT_ROOT/.env" 2>/dev/null || true

# Auto-adopción de ZCP_API_KEY desde el runtime Zerops
if [ -n "${ZCP_API_KEY:-}" ]; then
    export Z_TOKEN="$ZCP_API_KEY"
    export ZEROPS_TOKEN="$ZCP_API_KEY"
    [ -f "$PROJECT_ROOT/.env" ] && sed -i '/^Z_TOKEN=/d;/^ZEROPS_TOKEN=/d' "$PROJECT_ROOT/.env" 2>/dev/null || true
    echo "Z_TOKEN=$ZCP_API_KEY" >> "$PROJECT_ROOT/.env" 2>/dev/null || true
    echo "ZEROPS_TOKEN=$ZCP_API_KEY" >> "$PROJECT_ROOT/.env" 2>/dev/null || true
fi

# 1. Asegurar clonación del repositorio de la aplicación
if [ ! -d "$REPO_DIR" ]; then
    echo "• [1/4] Clonando repositorio de aplicación ($REPO_URL)..."
    git clone "$REPO_URL" "$REPO_DIR"
else
    echo "• [1/4] Repositorio detectado en $REPO_DIR."
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

# 2b. Aprovisionar catálogo soberano de skills desde GitHub (zerops-astro-skills)
SKILLS_REPO_URL="https://github.com/elplacerdc/zerops-astro-skills.git"
SKILLS_LOCAL_DIR="/var/www/zerops-astro-skills"
if [ ! -d "$SKILLS_LOCAL_DIR/.git" ]; then
    echo "• [2b/4] Clonando 65 skills soberanas desde GitHub ($SKILLS_REPO_URL)..."
    git clone --depth 1 "$SKILLS_REPO_URL" "$SKILLS_LOCAL_DIR" 2>/dev/null || true
else
    echo "• [2b/4] Actualizando skills soberanas desde GitHub..."
    git -C "$SKILLS_LOCAL_DIR" pull --ff-only 2>/dev/null || true
fi

# 3. Ejecutar orquestador maestro unisetup.sh desde Drive SSoT
if [ -f "$SSOT_SCRIPTS/unisetup.sh" ]; then
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
            "$DRIVE_MOUNT/0ZEROPS-AGY/users-apis/${TARGET_PROJECT}/elplacerdc.md"; do
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
        echo "     curl -fsSL https://raw.githubusercontent.com/elplacerdc/zerops-astrobranding/main/iniciar.sh | bash -s -- --keys /ruta/a/keys.md"
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

    bash "$SSOT_SCRIPTS/unisetup.sh" --all "${KEYS_FLAG[@]}" < /dev/null

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
    echo "❌ Error: $SSOT_SCRIPTS/unisetup.sh no disponible tras el montaje."
    exit 1
fi

# 4. Certificación final determinista
echo "• [4/4] Verificando paridad SSoT..."
if command -v ssot-parity-check >/dev/null 2>&1; then
    ssot-parity-check
elif [ -f "$SSOT_SCRIPTS/ssot-parity-check.sh" ]; then
    bash "$SSOT_SCRIPTS/ssot-parity-check.sh"
fi

echo "============================================================"
echo "  🎉 BOOTSTRAP COMPLETADO CON ÉXITO — ENTORNO LISTO"
echo "============================================================"
