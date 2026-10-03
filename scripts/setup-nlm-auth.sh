#!/usr/bin/env bash
# ==============================================================================
# Sovereign Google NotebookLM Persistent Authentication & noVNC Engine
# setup-nlm-auth.sh (v1.3)
# Governance: Supreme Directive v7.5 & Planner v3.0 (Track A Closed Topology)
# Features:
#   - Automated official Google Chrome (.deb) & VNC/noVNC provisioning.
#   - Ephemeral interactive noVNC login bridge (nlm-vnc-login) on port 6080.
#   - Zero overhead in idle (0 MB RAM): ephemeral Xvfb/VNC/Chrome auto-kill.
#   - Idempotent cron auto-refresh every 15 min (nlm auth refresh).
#   - Full SSoT two-way sync with Google Drive (0zcp-123/mcp/.nlm-auth/).
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZCP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NLM_DRIVE_DIR="$ZCP_ROOT/mcp/.nlm-auth"
NLM_LOCAL_DIR="/home/zerops/.notebooklm-mcp-cli"
NLM_BIN="/home/zerops/.local/bin/nlm"

if [ ! -x "$NLM_BIN" ]; then
    NLM_BIN="$(which nlm 2>/dev/null || echo "nlm")"
fi

# ------------------------------------------------------------------------------
# 1. Función: Asegurar Dependencias de Sistema (Chrome + noVNC + Xvfb)
# ------------------------------------------------------------------------------
ensure_dependencies() {
    echo "• Verificando dependencias de Google Chrome y stack gráfico efímero..."
    local pkgs_needed=()

    for cmd_pkg in "Xvfb:xvfb" "x11vnc:x11vnc" "websockify:websockify"; do
        cmd="${cmd_pkg%%:*}"
        pkg="${cmd_pkg##*:*}"
        if ! command -v "$cmd" >/dev/null 2>&1; then
            pkgs_needed+=("$pkg")
        fi
    done

    if [ ! -d "/usr/share/novnc" ]; then
        pkgs_needed+=("novnc")
    fi

    if [ ${#pkgs_needed[@]} -gt 0 ]; then
        echo "  📦 Instalando paquetes requeridos: ${pkgs_needed[*]}..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq "${pkgs_needed[@]}"
    fi

    if ! command -v google-chrome >/dev/null 2>&1; then
        echo "  🌐 Instalando Google Chrome Stable oficial (.deb)..."
        local chrome_deb="/tmp/google-chrome-stable_current_amd64.deb"
        curl -fsSL "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" -o "$chrome_deb"
        sudo dpkg -i "$chrome_deb" 2>/dev/null || sudo apt-get install -f -y -qq
        rm -f "$chrome_deb"
    fi

    echo "  ✅ Dependencias de sistema y Google Chrome operativas ($(google-chrome --version 2>/dev/null || echo 'OK'))."
}

# ------------------------------------------------------------------------------
# 2. Función: Configurar Cron Job de Auto-Refresco Desatendido
# ------------------------------------------------------------------------------
setup_cron() {
    echo "• Verificando cron job de auto-refresco (nlm auth refresh)..."
    local cron_cmd="*/15 * * * * /home/zerops/.local/bin/nlm auth refresh >/dev/null 2>&1"
    local current_cron
    current_cron="$(crontab -u zerops -l 2>/dev/null || true)"

    if ! echo "$current_cron" | grep -Fq "nlm auth refresh"; then
        echo "  ⏰ Configurando tarea de refresco cada 15 min en crontab (zerops)..."
        (echo "$current_cron"; echo "$cron_cmd") | crontab -u zerops -
    else
        echo "  ℹ️ Cron job de refresco ya configurado en crontab."
    fi

    if command -v service >/dev/null 2>&1; then
        sudo service cron status >/dev/null 2>&1 || sudo service cron start >/dev/null 2>&1 || true
    fi
}

# ------------------------------------------------------------------------------
# 3. Función: Restaurar Sesión desde Google Drive SSoT
# ------------------------------------------------------------------------------
restore_from_drive() {
    if [ -d "$NLM_DRIVE_DIR" ]; then
        echo "• Sincronizando credenciales y perfiles de NotebookLM desde Drive SSoT..."
        mkdir -p "$NLM_LOCAL_DIR" "$HOME/.notebooklm-mcp-cli"
        if [ -f "$NLM_DRIVE_DIR/nlm-auth.tar.gz" ]; then
            echo "  📦 Desempaquetando sesión comprimida (extracción instantánea)..."
            tar -xzf "$NLM_DRIVE_DIR/nlm-auth.tar.gz" -C /home/zerops/ 2>/dev/null || true
            if [ "$HOME" != "/home/zerops" ]; then
                tar -xzf "$NLM_DRIVE_DIR/nlm-auth.tar.gz" -C "$HOME/" 2>/dev/null || true
            fi
        else
            cp -rn "$NLM_DRIVE_DIR"/* "$NLM_LOCAL_DIR/" 2>/dev/null || cp -r "$NLM_DRIVE_DIR"/* "$NLM_LOCAL_DIR/" 2>/dev/null || true
            if [ "$HOME" != "/home/zerops" ]; then
                cp -rn "$NLM_DRIVE_DIR"/* "$HOME/.notebooklm-mcp-cli/" 2>/dev/null || cp -r "$NLM_DRIVE_DIR"/* "$HOME/.notebooklm-mcp-cli/" 2>/dev/null || true
            fi
        fi
        sudo chown -R zerops:zerops "$NLM_LOCAL_DIR" "$HOME/.notebooklm-mcp-cli" 2>/dev/null || true
        echo "  ✅ Sesión restaurada desde SSoT."
    fi
}

# ------------------------------------------------------------------------------
# 4. Función: Sincronizar Sesión Local hacia Google Drive SSoT
# ------------------------------------------------------------------------------
sync_to_drive() {
    echo "• Sincronizando perfil autenticado hacia Google Drive SSoT..."
    mkdir -p "$NLM_DRIVE_DIR"
    if [ -d "$NLM_LOCAL_DIR" ]; then
        local tar_tmp="/tmp/nlm-auth.tar.gz"
        tar --exclude="optimization_guide_model_store" \
            --exclude="component_crx_cache" \
            --exclude="WasmTtsEngine" \
            --exclude="OnDeviceHeadSuggestModel" \
            -czf "$tar_tmp" -C /home/zerops .notebooklm-mcp-cli 2>/dev/null || true
        if [ -f "$tar_tmp" ]; then
            cp "$tar_tmp" "$NLM_DRIVE_DIR/nlm-auth.tar.gz" 2>/dev/null || true
            rm -f "$tar_tmp"
        fi
        cp -f "$NLM_LOCAL_DIR/auth.json" "$NLM_DRIVE_DIR/auth.json" 2>/dev/null || true
        echo "  ✅ Perfil y credenciales respaldados en $NLM_DRIVE_DIR."
    fi
}

# ------------------------------------------------------------------------------
# 5. Función: Login Interactivo noVNC Efímero (nlm-vnc-login)
# ------------------------------------------------------------------------------
run_interactive_vnc_login() {
    ensure_dependencies

    local DISPLAY_NUM=":99"
    local VNC_PORT=5900
    local NOVNC_PORT=6080

    echo "=================================================================="
    echo "🚀 Iniciando Entorno Gráfico Efímero noVNC para Google NotebookLM"
    echo "=================================================================="

    # Limpiar procesos residuales previos si existieran
    pkill -f "Xvfb $DISPLAY_NUM" 2>/dev/null || true
    pkill -f "x11vnc.*$VNC_PORT" 2>/dev/null || true
    pkill -f "websockify.*$NOVNC_PORT" 2>/dev/null || true
    sleep 1

    # Iniciar Framebuffer virtual Xvfb
    echo "• Iniciando Xvfb en $DISPLAY_NUM (1280x800x24)..."
    Xvfb "$DISPLAY_NUM" -screen 0 1280x800x24 -nolisten tcp &
    local XVFB_PID=$!

    # Iniciar servidor x11vnc
    echo "• Iniciando x11vnc en puerto $VNC_PORT..."
    x11vnc -display "$DISPLAY_NUM" -rfbport "$VNC_PORT" -forever -nopw -listen 127.0.0.1 -quiet &
    local X11VNC_PID=$!

    # Iniciar websockify para exponer cliente web HTML5 noVNC
    echo "• Iniciando websockify en puerto $NOVNC_PORT..."
    websockify --web=/usr/share/novnc "$NOVNC_PORT" "127.0.0.1:$VNC_PORT" >/dev/null 2>&1 &
    local WEBSOCK_PID=$!

    # Limpieza garantizada al salir (0 MB en reposo)
    cleanup_vnc() {
        echo ""
        echo "🧹 Limpiando procesos gráficos efímeros (Zero Overhead Invariant)..."
        kill -15 "${WEBSOCK_PID:-}" "${X11VNC_PID:-}" "${XVFB_PID:-}" 2>/dev/null || true
        pkill -f "Xvfb $DISPLAY_NUM" 2>/dev/null || true
        pkill -f "x11vnc.*$VNC_PORT" 2>/dev/null || true
        pkill -f "websockify.*$NOVNC_PORT" 2>/dev/null || true
        echo "✅ Recursos gráficos liberados (0 MB RAM)."
    }
    trap cleanup_vnc EXIT INT TERM

    sleep 2

    echo ""
    echo "👉 INSTRUCCIONES DE ACCESO INTERACTIVO:"
    echo "   1. En tu code-server, ve a la pestaña 'Ports' (Puertos)."
    echo "   2. Abre o reenvía el puerto $NOVNC_PORT (URL: http://127.0.0.1:$NOVNC_PORT/vnc.html)."
    echo "   3. En la pantalla web de noVNC haz clic en 'Connect'."
    echo "   4. Verás la ventana de Google Chrome abriendo la autenticación de Google."
    echo "   5. Inicia sesión normalmente con tu cuenta de Google."
    echo "=================================================================="
    echo ""

    # Ejecutar login forzado de nlm usando el display virtual
    DISPLAY="$DISPLAY_NUM" "$NLM_BIN" login --force

    echo ""
    echo "🎉 Autenticación completada en Chrome."
    
    # Sincronizar el perfil persistente a Drive
    sync_to_drive

    # Configurar cron
    setup_cron

    # Verificar salud
    echo "• Verificando estado de sesión con nlm login --check..."
    "$NLM_BIN" login --check || true
}

# ------------------------------------------------------------------------------
# 6. Modo Instalación e Idempotencia SSoT (--install)
# ------------------------------------------------------------------------------
run_install() {
    ensure_dependencies
    restore_from_drive
    setup_cron

    # Crear wrappers ejecutables locales para acceso global (evita noexec en fuse.rclone)
    mkdir -p "/var/www/.bin"
    rm -f "/var/www/.bin/setup-nlm-auth.sh" "/var/www/.bin/setup-nlm-auth" "/var/www/.bin/nlm-vnc-login"
    sudo rm -f "/usr/local/bin/setup-nlm-auth.sh" "/usr/local/bin/setup-nlm-auth" "/usr/local/bin/nlm-vnc-login"

    cat << 'EOF' > /var/www/.bin/setup-nlm-auth.sh
#!/usr/bin/env bash
exec bash /var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/setup-nlm-auth.sh "$@"
EOF
    chmod +x /var/www/.bin/setup-nlm-auth.sh

    cat << 'EOF' > /var/www/.bin/nlm-vnc-login
#!/usr/bin/env bash
if [[ "${1:-}" =~ ^(-h|--help|help)$ ]]; then
    exec bash /var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/setup-nlm-auth.sh --help
fi
exec bash /var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/setup-nlm-auth.sh --login "$@"
EOF
    chmod +x /var/www/.bin/nlm-vnc-login

    sudo cp /var/www/.bin/nlm-vnc-login /usr/local/bin/nlm-vnc-login
    sudo cp /var/www/.bin/setup-nlm-auth.sh /usr/local/bin/setup-nlm-auth
    sudo cp /var/www/.bin/setup-nlm-auth.sh /usr/local/bin/setup-nlm-auth.sh
    sudo chmod +x /usr/local/bin/nlm-vnc-login /usr/local/bin/setup-nlm-auth /usr/local/bin/setup-nlm-auth.sh

    echo "✅ setup-nlm-auth configurado con éxito. Ejecuta 'nlm-vnc-login' para renovar sesión interactiva."
}

# ------------------------------------------------------------------------------
# Entrypoint Dispatcher
# ------------------------------------------------------------------------------
ACTION="${1:-help}"

case "$ACTION" in
    --install|install)
        run_install
        ;;
    --login|login|vnc)
        run_interactive_vnc_login
        ;;
    --sync-to-drive)
        sync_to_drive
        ;;
    --restore)
        restore_from_drive
        ;;
    --refresh|refresh)
        "$NLM_BIN" auth refresh
        ;;
    --help|help|-h)
        echo "Uso: $0 [--install | --login | --refresh | --sync-to-drive | --restore]"
        echo "Comandos disponibles:"
        echo "  --install        Instala dependencias, restaura perfil y activa cron"
        echo "  --login          Levanta noVNC efímero (6080) para login interactivo en Chrome"
        echo "  --refresh        Ejecuta refresco headless desatendido (nlm auth refresh)"
        echo "  --sync-to-drive  Respalda el perfil local hacia Google Drive SSoT"
        echo "  --restore        Restaura perfil desde Google Drive SSoT"
        exit 0
        ;;
    *)
        echo "Acción desconocida: $ACTION"
        exit 1
        ;;
esac
