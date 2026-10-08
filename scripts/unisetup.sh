#!/usr/bin/env bash
# ==============================================================================
# Master Universal Bootstrapper for Zerops ZCP & Gentle AI (unisetup.sh)
# Version: 3.6 (Zerops Platform Env Soberano & Auto-Purge de .env)
# ==============================================================================
set -euo pipefail

# Invariante Anti-Bytecode & Limpieza Determinista
export PYTHONDONTWRITEBYTECODE=1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZCP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-/var/www}"
INTERACTIVE=false
RUN_ALL=true
MODULE=""
CUSTOM_KEYS_FILE=""

# Asegurar persistencia de PYTHONDONTWRITEBYTECODE en el entorno global y subshells
if [ -f "/etc/environment" ] && ! grep -q "PYTHONDONTWRITEBYTECODE" /etc/environment 2>/dev/null; then
    echo "PYTHONDONTWRITEBYTECODE=1" | sudo tee -a /etc/environment >/dev/null 2>&1 || true
fi
if [ -d "/etc/profile.d" ]; then
    echo 'export PYTHONDONTWRITEBYTECODE=1' | sudo tee /etc/profile.d/python_no_pycache.sh >/dev/null 2>&1 || true
    sudo chmod +x /etc/profile.d/python_no_pycache.sh 2>/dev/null || true
fi
if [ -f "/etc/bash.bashrc" ] && ! grep -q "PYTHONDONTWRITEBYTECODE" /etc/bash.bashrc 2>/dev/null; then
    echo 'export PYTHONDONTWRITEBYTECODE=1' | sudo tee -a /etc/bash.bashrc >/dev/null 2>&1 || true
fi
if [ -f "$HOME/.bashrc" ] && ! grep -q "PYTHONDONTWRITEBYTECODE" "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PYTHONDONTWRITEBYTECODE=1' >> "$HOME/.bashrc" 2>/dev/null || true
fi

# Auto-detección y persistencia soberana de ZCP_API_KEY en plataforma Zerops
if [ -n "${ZCP_API_KEY:-}" ]; then
    export Z_TOKEN="$ZCP_API_KEY"
    export ZEROPS_TOKEN="$ZCP_API_KEY"
    if [ -f "/etc/environment" ] && ! grep -q "^ZCP_API_KEY=" /etc/environment 2>/dev/null; then
        echo "ZCP_API_KEY=\"$ZCP_API_KEY\"" | sudo tee -a /etc/environment >/dev/null 2>&1 || true
    fi
fi

# Proactive Bytecode Hygiene: purge any residual __pycache__ across hooks and scripts
rm -rf "$SCRIPT_DIR/__pycache__" "$PROJECT_ROOT/.bin/hooks/__pycache__" "$SCRIPT_DIR/hooks/__pycache__" 2>/dev/null || true

# Garantizar estructura canónica de respaldos centralizada en bak/
mkdir -p "$ZCP_ROOT/bak/scripts" "$ZCP_ROOT/bak/rules" "$ZCP_ROOT/bak/skills" "$ZCP_ROOT/bak/apis" "$ZCP_ROOT/bak/mcp" 2>/dev/null || true

# Snapshot preventivo de scripts en bak/scripts/
SNAPSHOT_TS=$(date +%Y%m%d_%H%M%S)
for s in "$SCRIPT_DIR"/*.sh; do
    if [ -f "$s" ]; then
        s_base=$(basename "$s")
        cp -n "$s" "$ZCP_ROOT/bak/scripts/${s_base}_${SNAPSHOT_TS}.bak" 2>/dev/null || true
    fi
done

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -i|--interactive) INTERACTIVE=true; shift ;;
        --file|-f) CUSTOM_KEYS_FILE="$2"; shift 2 ;;
        --all) RUN_ALL=true; shift ;;
        --keys) RUN_ALL=false; MODULE="keys"; shift ;;
        --gentle) RUN_ALL=false; MODULE="gentle"; shift ;;
        --browser) RUN_ALL=false; MODULE="browser"; shift ;;
        --zcp) RUN_ALL=false; MODULE="zcp"; shift ;;
        --astro) RUN_ALL=false; MODULE="astro"; shift ;;
        --gh|--github) RUN_ALL=false; MODULE="gh"; shift ;;
        --drive|-d) RUN_ALL=false; MODULE="drive"; shift ;;
        *)
            if [ -f "$1" ]; then
                CUSTOM_KEYS_FILE="$1"
            fi
            shift
            ;;
    esac
done

if [ -z "$CUSTOM_KEYS_FILE" ] && [ -t 0 ] && [ "$INTERACTIVE" = false ]; then
    echo "============================================================"
    echo "  🔑 Configuración de Claves para este ZCP / Cliente"
    echo "============================================================"
    read -r -p "• Ingrese la ruta del archivo de claves (.md / .env) [o Enter para omitir]: " USER_FILE
    USER_FILE=$(echo "$USER_FILE" | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    if [ -n "$USER_FILE" ] && [ -f "$USER_FILE" ]; then
        CUSTOM_KEYS_FILE="$USER_FILE"
        echo "  ✓ Archivo seleccionado: $CUSTOM_KEYS_FILE"
    else
        echo "  ℹ️ Continuando sin archivo previo (se usarán variables del entorno)."
    fi
    echo ""
fi

PASSTHRU_ARGS=()
[ "$INTERACTIVE" = true ] && PASSTHRU_ARGS+=("--interactive")
[ -n "$CUSTOM_KEYS_FILE" ] && PASSTHRU_ARGS+=("--file" "$CUSTOM_KEYS_FILE")

echo "============================================================"
echo "  🚀 INICIANDO UNIFIED BOOTSTRAPPER (unisetup.sh v3.5)"
echo "============================================================"
echo "• SSoT Directory: $SCRIPT_DIR"
[ -n "$CUSTOM_KEYS_FILE" ] && echo "• Archivo de claves configurado: $CUSTOM_KEYS_FILE"
echo ""

run_step() {
    local step_num="$1"
    local step_name="$2"
    local script_path="$3"
    shift 3
    local extra_args=("$@")

    if [ -f "$script_path" ]; then
        echo "------------------------------------------------------------"
        echo "  [Paso $step_num] Ejecutando: $step_name"
        echo "------------------------------------------------------------"
        chmod +x "$script_path"
        bash "$script_path" "${extra_args[@]}"
        echo ""
    else
        echo "⚠️ Script no encontrado: $script_path (Omitiendo)"
    fi
}

ZEROPS_SYNC_PID=""

# Auto-recuperación y sincronización de repositorio zerops-astrobranding
if [ -d "$PROJECT_ROOT/zerops-astrobranding/.git" ]; then
    echo "• Sincronizando repositorio zerops-astrobranding con GitHub (git pull)..."
    git -C "$PROJECT_ROOT/zerops-astrobranding" pull --ff-only 2>/dev/null || true
fi
if [ -f "$SCRIPT_DIR/iniciar.sh" ] && [ -f "$PROJECT_ROOT/zerops-astrobranding/iniciar.sh" ]; then
    if ! cmp -s "$SCRIPT_DIR/iniciar.sh" "$PROJECT_ROOT/zerops-astrobranding/iniciar.sh"; then
        cp -f "$SCRIPT_DIR/iniciar.sh" "$PROJECT_ROOT/zerops-astrobranding/iniciar.sh" 2>/dev/null || true
    fi
fi
if [ -f "$SCRIPT_DIR/gdrive.sh" ] && [ -f "$PROJECT_ROOT/zerops-astrobranding/scripts/gdrive.sh" ]; then
    if ! cmp -s "$SCRIPT_DIR/gdrive.sh" "$PROJECT_ROOT/zerops-astrobranding/scripts/gdrive.sh"; then
        cp -f "$SCRIPT_DIR/gdrive.sh" "$PROJECT_ROOT/zerops-astrobranding/scripts/gdrive.sh" 2>/dev/null || true
    fi
fi

if [ "$RUN_ALL" = true ] || [ "$MODULE" = "keys" ]; then
    run_step "1/6" "Ingestión Universal de Claves & Secretos (setup-keys.sh v3.4)" "$SCRIPT_DIR/setup-keys.sh" "${PASSTHRU_ARGS[@]}"

    # Paso 1b: Sincronización autónoma hacia Zerops Cloud vía zeropsenv en segundo plano
    if [ -f "$PROJECT_ROOT/.bin/zeropsenv" ]; then
        echo "• Sincronizando variables a Zerops Cloud en segundo plano (zeropsenv sync)..."
        SYNC_LOG="/tmp/zeropsenv_sync.log"
        "$PROJECT_ROOT/.bin/zeropsenv" sync > "$SYNC_LOG" 2>&1 &
        ZEROPS_SYNC_PID=$!
        echo "  ✓ Proceso de sincronización iniciado (PID $ZEROPS_SYNC_PID). Avanzando con el despliegue..."
        echo ""
    fi
fi

if [ "$RUN_ALL" = true ] || [ "$MODULE" = "gentle" ]; then
    run_step "2/6" "Despliegue Gentle AI en Vivo desde Upstream (setup-gentle.sh)" "$SCRIPT_DIR/setup-gentle.sh" "antigravity"
fi

if [ "$RUN_ALL" = true ] || [ "$MODULE" = "drive" ]; then
    run_step "3/6" "Sincronización Custom Skills desde Google Drive (setup-drive.sh)" "$SCRIPT_DIR/setup-drive.sh"
fi

if [ "$RUN_ALL" = true ] || [ "$MODULE" = "browser" ]; then
    run_step "4/6" "Despliegue MCP Search Hub & Scraping (setup-browser.sh)" "$SCRIPT_DIR/setup-browser.sh"
fi

if [ "$RUN_ALL" = true ] || [ "$MODULE" = "zcp" ]; then
    run_step "5/6" "Despliegue Arnés Físico ZCP & DCKR (setup-zcp.sh)" "$SCRIPT_DIR/setup-zcp.sh"
fi

if [ "$RUN_ALL" = true ] || [ "$MODULE" = "astro" ]; then
    run_step "6/6" "Ingestión Claves Astrológicas, NLM & MCPs (setup-astrokey.sh)" "$SCRIPT_DIR/setup-astrokey.sh" "${PASSTHRU_ARGS[@]}"
fi

if [ "$RUN_ALL" = true ] || [ "$MODULE" = "gh" ]; then
    run_step "6b/7" "Autenticación Dinámica de GitHub CLI & CI/CD (setup-gh.sh)" "$SCRIPT_DIR/setup-gh.sh"
fi

if [ "$RUN_ALL" = true ]; then
    echo "------------------------------------------------------------"
    echo "  [Paso 7/7] Verificación Integral de Capacidades & Registry"
    echo "------------------------------------------------------------"
    # Sincronización e Ingestión de Memoria LTM Engram (Aislamiento Soberano Multi-Proyecto)
    ACTIVE_PROJECT="${ENGRAM_PROJECT:-${PROJECT_NAME:-zerops-astrobranding}}"
    mkdir -p "$PROJECT_ROOT/.engram"
    echo "{\"project_name\": \"$ACTIVE_PROJECT\"}" > "$PROJECT_ROOT/.engram/config.json"

    if [ "$ACTIVE_PROJECT" = "zerops-astrobranding" ]; then
        # Upstream Template: Restaurar memoria basal de desarrollo soberano
        ENGRAM_DUMP="$ZCP_ROOT/engram_baseline.json"
        [ ! -f "$ENGRAM_DUMP" ] && ENGRAM_DUMP="$ZCP_ROOT/engram_ssot.json"
        if [ -f "$ENGRAM_DUMP" ]; then
            echo "• Sincronizando memoria basal upstream de $ACTIVE_PROJECT desde SSoT..."
            "$PROJECT_ROOT/.bin/engram" import "$ENGRAM_DUMP" 2>/dev/null || engram import "$ENGRAM_DUMP" 2>/dev/null || true
        fi
    else
        # Proyecto Downstream / Cliente (ej: client_app): Aislamiento absoluto anti-contaminación
        CLIENT_DUMP="$ZCP_ROOT/../users-apis/${ACTIVE_PROJECT}/engram_${ACTIVE_PROJECT}.json"
        if [ -f "$CLIENT_DUMP" ]; then
            echo "• Sincronizando memoria LTM dedicada para cliente $ACTIVE_PROJECT..."
            "$PROJECT_ROOT/.bin/engram" import "$CLIENT_DUMP" 2>/dev/null || engram import "$CLIENT_DUMP" 2>/dev/null || true
        else
            echo "• Inicializando espacio de nombres LTM limpio y aislado para $ACTIVE_PROJECT..."
            engram save "Init: Bootstrap Soberano de $ACTIVE_PROJECT" "What: Inicializado espacio de nombres aislado para $ACTIVE_PROJECT.\nWhy: Adopcion limpia sin contaminacion de memoria upstream.\nWhere: /var/www\nLearned: Espacio de nombres LTM aislado y blindado contra cross-contamination." --project "$ACTIVE_PROJECT" --scope project 2>/dev/null || true
        fi
    fi

    if command -v gentle-ai >/dev/null 2>&1; then
        echo "• Refrescando registro de skills..."
        gentle-ai skill-registry refresh --force 2>/dev/null || true
    fi
    mkdir -p "$PROJECT_ROOT/.bin" 2>/dev/null || true
    if [ -f "$SCRIPT_DIR/skills-suite-validate.sh" ]; then
        echo "• Desplegando y ejecutando suite física de validación (Standard v3.0)..."
        cp -f "$SCRIPT_DIR/skills-suite-validate.sh" "$PROJECT_ROOT/.bin/skills-suite-validate"
        chmod +x "$PROJECT_ROOT/.bin/skills-suite-validate"
        sudo ln -sf "$PROJECT_ROOT/.bin/skills-suite-validate" /usr/local/bin/skills-suite-validate 2>/dev/null || true
        bash "$SCRIPT_DIR/skills-suite-validate.sh"
    fi

    if [ -n "${ZEROPS_SYNC_PID:-}" ]; then
        echo "• Verificando sincronización de variables con Zerops Cloud (PID $ZEROPS_SYNC_PID)..."
        for _wait_idx in {1..90}; do
            if ! kill -0 "$ZEROPS_SYNC_PID" 2>/dev/null; then
                break
            fi
            sleep 1
        done
        wait "$ZEROPS_SYNC_PID" 2>/dev/null || true
        if grep -q "✅" /tmp/zeropsenv_sync.log 2>/dev/null; then
            echo "  ✓ Variables de entorno sincronizadas en Zerops Cloud exitosamente."
        else
            echo "  ℹ️ Registro de sincronización hacia Zerops Cloud:"
            tail -n 5 /tmp/zeropsenv_sync.log 2>/dev/null || true
        fi
    fi

    # Invariante Anti-Basura y Barrido Determinista (FUSE Mount Prune)
    echo "• Ejecutando barrido determinista de higiene y bytecode..."
    find "$PROJECT_ROOT" \( -path "$PROJECT_ROOT/baiosfera" -o -path "$PROJECT_ROOT/mnt" -o -path "$PROJECT_ROOT/.rclone" \) -prune -o -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$SCRIPT_DIR" -maxdepth 2 -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$SCRIPT_DIR" -maxdepth 2 -name "*.pyc" -delete 2>/dev/null || true
    rm -rf "$PROJECT_ROOT/baiosfera/CURSOS/MCV/__pycache__" 2>/dev/null || true
    find /tmp -maxdepth 1 \( -name "gentle_*" -o -name "gai_*" -o -name "engram_*" -o -name "gga_*" \) -type d -exec rm -rf {} + 2>/dev/null || true
    rm -f "$PROJECT_ROOT/.env" "$PROJECT_ROOT/gdrive.env" "$PROJECT_ROOT"/key*.md "$PROJECT_ROOT"/key*.env 2>/dev/null || true
    echo "  ✓ Bytecode (__pycache__, *.pyc) y archivos temporales (.env, gdrive.env, keys) purgados."

    # Invariante Anti-Forwarding y Persistencia de Terminales Web en Code-Server
    echo "• Asegurando persistencia de terminales web y remote.autoForwardPorts en Code-Server..."
    for cfg in "/home/zerops/.local/share/code-server/User/settings.json" "$PROJECT_ROOT/.vscode/settings.json"; do
        if [ -f "$cfg" ]; then
            python3 -c "import json; p='$cfg'; d=json.load(open(p)); d['remote.autoForwardPorts']=False; d['terminal.integrated.persistentSessionReviveProcess']='onExitAndWindowClose'; d['terminal.integrated.persistentSessionScrollback']=10000; json.dump(d,open(p,'w'),indent=2)" 2>/dev/null || true
        fi
    done
    echo "  ✓ Invariantes de persistencia de terminal (onExitAndWindowClose, scrollback 10000) y auto-forwarding blindadas."

    echo "  ✅ Verificación completada con éxito."
    echo ""
fi

echo "============================================================"
echo "  🎉 UNIFIED BOOTSTRAPPER FINALIZADO CON ÉXITO (v3.4)"
echo "============================================================"
