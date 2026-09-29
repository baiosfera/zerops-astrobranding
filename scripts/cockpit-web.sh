#!/usr/bin/env bash
# ==============================================================================
# Cockpit Web GUI Process Manager (cockpit-web)
# Usage: cockpit-web [start|stop|status|restart]
# ==============================================================================
set -euo pipefail

PID_FILE="/tmp/cockpit-web.pid"
PORT="${COCKPIT_PORT:-3050}"
SCRIPT="/var/www/zerops-astrobranding/scripts/cockpit-server.ts"

cmd="${1:-status}"

is_running() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

case "$cmd" in
    start)
        if is_running; then
            echo "✅ Cockpit Web GUI ya está corriendo en http://localhost:$PORT (PID: $(cat "$PID_FILE"))"
            exit 0
        fi
        echo "🚀 Iniciando Cockpit Web GUI en puerto $PORT..."
        if command -v bun >/dev/null 2>&1; then
            setsid nohup bun "$SCRIPT" </dev/null > /tmp/cockpit-web.log 2>&1 &
        else
            setsid nohup node --no-warnings --experimental-strip-types "$SCRIPT" </dev/null > /tmp/cockpit-web.log 2>&1 &
        fi
        sleep 1
        if is_running; then
            echo "✅ Cockpit Web GUI iniciado exitosamente:"
            echo "   URL Local: http://localhost:$PORT"
            echo "   PID: $(cat "$PID_FILE") (Consumo ~15MB RAM)"
            echo "   Auto-apagado: tras 30 min de inactividad"
        else
            echo "❌ Error al iniciar Cockpit Web GUI. Revisa /tmp/cockpit-web.log"
            exit 1
        fi
        ;;
    stop)
        if is_running; then
            pid=$(cat "$PID_FILE")
            echo "🛑 Deteniendo Cockpit Web GUI (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            rm -f "$PID_FILE"
            echo "✅ Cockpit Web GUI detenido. Memoria RAM liberada (0 MB idle)."
        else
            echo "ℹ️ Cockpit Web GUI no está en ejecución (0 MB RAM en reposo)."
            rm -f "$PID_FILE"
        fi
        ;;
    status)
        if is_running; then
            pid=$(cat "$PID_FILE")
            echo "● Cockpit Web GUI: EN EJECUCIÓN"
            echo "  URL: http://localhost:$PORT"
            echo "  PID: $pid"
            echo "  Uso de RAM: $(ps -o rss= -p "$pid" 2>/dev/null | awk '{print int($1/1024) " MB"}')"
        else
            echo "○ Cockpit Web GUI: DETENIDO (0 MB idle RAM)"
            echo "  Para encender: cockpit-web start"
        fi
        ;;
    restart)
        "$0" stop
        sleep 1
        "$0" start
        ;;
    *)
        echo "Uso: cockpit-web [start|stop|status|restart]"
        exit 1
        ;;
esac
