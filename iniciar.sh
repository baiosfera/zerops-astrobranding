#!/usr/bin/env bash
# ==============================================================================
# Iniciar ZCP: Bootstrapper Soberano Autónomo (iniciar.sh)
# Repositorio: https://github.com/catalinaglamur/zerops-astrobranding
# Ejecución Mínima: curl -fsSL https://raw.githubusercontent.com/catalinaglamur/zerops-astrobranding/main/iniciar.sh | bash
# ==============================================================================
set -euo pipefail

echo "============================================================"
echo "  🚀 INICIANDO BOOTSTRAP SOBERANO ZCP (iniciar.sh v1.0)"
echo "============================================================"

PROJECT_ROOT="${PROJECT_ROOT:-/var/www}"
REPO_URL="https://github.com/catalinaglamur/zerops-astrobranding.git"
REPO_NAME="$(basename "$REPO_URL" .git)"
REPO_DIR="${PROJECT_ROOT}/zerops-astrobranding"
DRIVE_MOUNT="${GDRIVE_MOUNT_DIR:-/var/www/baiosfera}"
SSOT_SCRIPTS="$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123/scripts"

# Manejo de argumentos opcionales (--keys, --repo)
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --keys|-k)
            if [ -f "$2" ]; then
                echo "• Cargando archivo de credenciales externas: $2"
                set -a; source "$2"; set +a
            fi
            shift 2 ;;
        --repo|-r)
            REPO_URL="$2"
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

# Exportar identidad de proyecto agnóstica para Engram y el entorno
export PROJECT_NAME="$REPO_NAME"
export ENGRAM_PROJECT="$REPO_NAME"
[ -f "$PROJECT_ROOT/.env" ] && sed -i '/^ENGRAM_PROJECT=/d' "$PROJECT_ROOT/.env" 2>/dev/null || true
echo "ENGRAM_PROJECT=$REPO_NAME" >> "$PROJECT_ROOT/.env" 2>/dev/null || true

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
    echo "• [3/4] Ejecutando unisetup.sh desde Google Drive SSoT..."
    bash "$SSOT_SCRIPTS/unisetup.sh" --all
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
