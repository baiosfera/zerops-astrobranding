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

# 3. Ejecutar orquestador maestro unisetup.sh desde Drive SSoT
if [ -f "$SSOT_SCRIPTS/unisetup.sh" ]; then
    echo "• [3/4] Resolviendo credenciales y ejecutando unisetup.sh..."
    RESOLVED_KEYS=""
    
    # Cascada de resolución agnóstica de credenciales:
    if [ -n "${KEYS_FILE_ARG:-}" ] && [ -f "$KEYS_FILE_ARG" ]; then
        RESOLVED_KEYS="$KEYS_FILE_ARG"
    elif [ -n "${KEYS_FILE:-}" ] && [ -f "$KEYS_FILE" ]; then
        RESOLVED_KEYS="$KEYS_FILE"
    elif [ -f "$PROJECT_ROOT/keys.md" ]; then
        RESOLVED_KEYS="$PROJECT_ROOT/keys.md"
    elif [ -f "$PROJECT_ROOT/keys.env" ]; then
        RESOLVED_KEYS="$PROJECT_ROOT/keys.env"
    elif [ -n "$TARGET_PROJECT" ]; then
        # Búsqueda específica en SSoT según el proyecto/cliente configurado
        for candidate in \
            "$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/apis/${TARGET_PROJECT}-keys.md" \
            "$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/apis/${TARGET_PROJECT}.md" \
            "$DRIVE_MOUNT/0ZEROPS-AGY/users-apis/${TARGET_PROJECT}/${TARGET_PROJECT}-keys.md" \
            "$DRIVE_MOUNT/0ZEROPS-AGY/users-apis/${TARGET_PROJECT}/${TARGET_PROJECT}.md" \
            "$DRIVE_MOUNT/0ZEROPS-AGY/users-apis/${TARGET_PROJECT}/glamur-keys.md" \
            "$DRIVE_MOUNT/0ZEROPS-AGY/users-apis/${TARGET_PROJECT}/elplacerdc.md"; do
            if [ -f "$candidate" ]; then
                RESOLVED_KEYS="$candidate"
                break
            fi
        done
    fi

    # Fallback genérico agnóstico en SSoT (si existiese)
    if [ -z "$RESOLVED_KEYS" ] && [ -f "$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/apis/keys.md" ]; then
        RESOLVED_KEYS="$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/apis/keys.md"
    fi

    KEYS_FLAG=()
    if [ -n "$RESOLVED_KEYS" ]; then
        echo "  🔑 Archivo de claves asignado: $RESOLVED_KEYS"
        KEYS_FLAG=("--file" "$RESOLVED_KEYS")
    else
        echo "  ℹ️ Modo agnóstico: Sin archivo de claves previo asignado. Se usarán variables del entorno del contenedor."
    fi

    bash "$SSOT_SCRIPTS/unisetup.sh" --all "${KEYS_FLAG[@]}" < /dev/null
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
