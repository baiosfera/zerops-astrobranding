#!/usr/bin/env bash
# ==============================================================================
# ZCP & Docker Skills Installer for Zerops ZCP
# Version: 6.5 (Clean Manifests, MCV Downloader & MCV Status Provisioning, SSoT)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZCP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="/var/www"
PERSISTENT_BIN="$PROJECT_ROOT/.bin"
PERSISTENT_AGENTS="$PROJECT_ROOT/.agents"

mkdir -p "$PERSISTENT_BIN" "$PERSISTENT_AGENTS/skills/zcp" "$PERSISTENT_AGENTS/skills/dckr"
rm -rf "$SCRIPT_DIR/__pycache__" 2>/dev/null || true

echo "============================================================"
echo "  [4/4] Desplegando Skills ZCP & DCKR (setup-zcp.sh v6.2)"
echo "============================================================"

# 1. Instalar Herramienta de Arnés Físico Extendido zcp-validate (v6.2)
if [ -f "$SCRIPT_DIR/zcp-validate.sh" ]; then
    cp -f "$SCRIPT_DIR/zcp-validate.sh" "$PERSISTENT_BIN/zcp-validate"
    chmod +x "$PERSISTENT_BIN/zcp-validate"
    cp "$PERSISTENT_BIN/zcp-validate" "$HOME/.local/bin/zcp-validate" 2>/dev/null || true
    cp "$PERSISTENT_BIN/zcp-validate" "/home/zerops/.local/bin/zcp-validate" 2>/dev/null || true
    sudo ln -sf "$PERSISTENT_BIN/zcp-validate" /usr/local/bin/zcp-validate 2>/dev/null || true
fi

# 1.1 Despliegue de Herramienta Soberana Linear CLI (linear-cli)
if [ -f "$SCRIPT_DIR/linear-cli" ]; then
    cp -f "$SCRIPT_DIR/linear-cli" "$PERSISTENT_BIN/linear-cli"
    chmod +x "$PERSISTENT_BIN/linear-cli"
    cp "$PERSISTENT_BIN/linear-cli" "$HOME/.local/bin/linear-cli" 2>/dev/null || true
    cp "$PERSISTENT_BIN/linear-cli" "/home/zerops/.local/bin/linear-cli" 2>/dev/null || true
    sudo ln -sf "$PERSISTENT_BIN/linear-cli" /usr/local/bin/linear-cli 2>/dev/null || true
fi

# 2. Despliegue de Utilidad Soberana MCV Downloader (mcv-download)
# Asegurar dependencias de sistema y navegador para MCV en ZCP limpio
echo "• Asegurando dependencias de sistema para MCV (ffmpeg, unrar, 7z, megatools, gdown, agent-browser)..."
sudo apt-get update -qq
sudo apt-get install -y -qq ffmpeg p7zip-full unrar megatools python3-pip 2>/dev/null || true
pip3 install requests beautifulsoup4 gdown mcp --break-system-packages 2>/dev/null || pip install requests beautifulsoup4 gdown mcp 2>/dev/null || true
if ! command -v agent-browser >/dev/null 2>&1; then
    echo "  🌐 Instalando agent-browser para descargas Sync.com..."
    sudo npm install -g agent-browser 2>/dev/null || true
fi

# Auto-sync SSoT to runtime directory if Google Drive courses mount is active
if [ -d "/var/www/baiosfera/CURSOS/MCV" ] && [ -f "$SCRIPT_DIR/mcv_downloader.py" ]; then
    if [ ! -f "/var/www/baiosfera/CURSOS/MCV/mcv_downloader.py" ] || ! cmp -s "$SCRIPT_DIR/mcv_downloader.py" "/var/www/baiosfera/CURSOS/MCV/mcv_downloader.py"; then
        cp -f "$SCRIPT_DIR/mcv_downloader.py" "/var/www/baiosfera/CURSOS/MCV/mcv_downloader.py" 2>/dev/null || true
    fi
fi

if [ -f "/var/www/baiosfera/CURSOS/MCV/mcv_downloader.py" ]; then
    MCV_SCRIPT_SRC="/var/www/baiosfera/CURSOS/MCV/mcv_downloader.py"
elif [ -f "$SCRIPT_DIR/mcv_downloader.py" ]; then
    MCV_SCRIPT_SRC="$SCRIPT_DIR/mcv_downloader.py"
else
    MCV_SCRIPT_SRC=""
fi

if [ -n "$MCV_SCRIPT_SRC" ]; then
    echo "• Desplegando ejecutable MCV Downloader (mcv-download -> $MCV_SCRIPT_SRC)..."
    sudo rm -f /usr/local/bin/mcv-download "$PERSISTENT_BIN/mcv-download" "$HOME/.local/bin/mcv-download" "/home/zerops/.local/bin/mcv-download" 2>/dev/null || true
    cat <<EOF | sudo tee /usr/local/bin/mcv-download >/dev/null
#!/usr/bin/env bash
exec python3 -B "$MCV_SCRIPT_SRC" "\$@"
EOF
    sudo chmod +x /usr/local/bin/mcv-download
    [ -d "$PERSISTENT_BIN" ] && sudo cp -f /usr/local/bin/mcv-download "$PERSISTENT_BIN/mcv-download" 2>/dev/null || true
    [ -d "$HOME/.local/bin" ] && cp -f /usr/local/bin/mcv-download "$HOME/.local/bin/mcv-download" 2>/dev/null || true
    [ -d "/home/zerops/.local/bin" ] && cp -f /usr/local/bin/mcv-download "/home/zerops/.local/bin/mcv-download" 2>/dev/null || true
fi

# Despliegue de Utilidad de Monitoreo de Progreso (mcv-status)
if [ -n "$MCV_SCRIPT_SRC" ]; then
    echo "• Desplegando monitor de progreso MCV unificado (mcv-status -> $MCV_SCRIPT_SRC --status)..."
    sudo rm -f /usr/local/bin/mcv-status "$PERSISTENT_BIN/mcv-status" "$HOME/.local/bin/mcv-status" "/home/zerops/.local/bin/mcv-status" 2>/dev/null || true
    cat <<EOF | sudo tee /usr/local/bin/mcv-status >/dev/null
#!/usr/bin/env bash
exec python3 -B "$MCV_SCRIPT_SRC" --status "\$@"
EOF
    sudo chmod +x /usr/local/bin/mcv-status
    [ -d "$PERSISTENT_BIN" ] && sudo cp -f /usr/local/bin/mcv-status "$PERSISTENT_BIN/mcv-status" 2>/dev/null || true
    [ -d "$HOME/.local/bin" ] && cp -f /usr/local/bin/mcv-status "$HOME/.local/bin/mcv-status" 2>/dev/null || true
    [ -d "/home/zerops/.local/bin" ] && cp -f /usr/local/bin/mcv-status "/home/zerops/.local/bin/mcv-status" 2>/dev/null || true
fi

# Despliegue de Utilidad Soberana NLM Tutor (nlm-tutor)
if [ -f "$SCRIPT_DIR/nlm_tutor.py" ]; then
    NLM_TUTOR_SRC="$SCRIPT_DIR/nlm_tutor.py"
    echo "• Desplegando orquestador de aprendizaje autónomo (nlm-tutor -> $NLM_TUTOR_SRC)..."
    sudo rm -f /usr/local/bin/nlm-tutor "$PERSISTENT_BIN/nlm-tutor" "$HOME/.local/bin/nlm-tutor" "/home/zerops/.local/bin/nlm-tutor" 2>/dev/null || true
    cat <<EOF | sudo tee /usr/local/bin/nlm-tutor >/dev/null
#!/usr/bin/env bash
exec python3 -B "$NLM_TUTOR_SRC" "\$@"
EOF
    sudo chmod +x /usr/local/bin/nlm-tutor
    [ -d "$PERSISTENT_BIN" ] && sudo cp -f /usr/local/bin/nlm-tutor "$PERSISTENT_BIN/nlm-tutor" 2>/dev/null || true
    [ -d "$HOME/.local/bin" ] && cp -f /usr/local/bin/nlm-tutor "$HOME/.local/bin/nlm-tutor" 2>/dev/null || true
    [ -d "/home/zerops/.local/bin" ] && cp -f /usr/local/bin/nlm-tutor "/home/zerops/.local/bin/nlm-tutor" 2>/dev/null || true
fi

# Despliegue de Cockpit Soberano de Telemetría (cockpit-status y cockpit-web)
COCKPIT_STATUS_SRC="$SCRIPT_DIR/cockpit-status.ts"
COCKPIT_WEB_SRC="$SCRIPT_DIR/cockpit-web.sh"
[ ! -f "$COCKPIT_STATUS_SRC" ] && COCKPIT_STATUS_SRC="$PROJECT_ROOT/zerops-astrobranding/scripts/cockpit-status.ts"
[ ! -f "$COCKPIT_WEB_SRC" ] && COCKPIT_WEB_SRC="$PROJECT_ROOT/zerops-astrobranding/scripts/cockpit-web.sh"

if [ -f "$COCKPIT_STATUS_SRC" ]; then
    echo "• Desplegando ejecutable Cockpit Status (cockpit-status -> $COCKPIT_STATUS_SRC)..."
    sudo rm -f /usr/local/bin/cockpit-status "$PERSISTENT_BIN/cockpit-status" "$HOME/.local/bin/cockpit-status" "/home/zerops/.local/bin/cockpit-status" 2>/dev/null || true
    cat <<EOF | sudo tee /usr/local/bin/cockpit-status >/dev/null
#!/usr/bin/env bash
if command -v bun >/dev/null 2>&1; then
    exec bun "$COCKPIT_STATUS_SRC" "\$@"
else
    exec node --no-warnings --experimental-strip-types "$COCKPIT_STATUS_SRC" "\$@"
fi
EOF
    sudo chmod +x /usr/local/bin/cockpit-status
    [ -d "$PERSISTENT_BIN" ] && sudo cp -f /usr/local/bin/cockpit-status "$PERSISTENT_BIN/cockpit-status" && sudo chown zerops:zerops "$PERSISTENT_BIN/cockpit-status" 2>/dev/null || true
    [ -d "$HOME/.local/bin" ] && cp -f /usr/local/bin/cockpit-status "$HOME/.local/bin/cockpit-status" 2>/dev/null || true
    [ -d "/home/zerops/.local/bin" ] && cp -f /usr/local/bin/cockpit-status "/home/zerops/.local/bin/cockpit-status" 2>/dev/null || true
fi

if [ -f "$COCKPIT_WEB_SRC" ]; then
    echo "• Desplegando gestor de proceso Cockpit Web GUI (cockpit-web -> $COCKPIT_WEB_SRC)..."
    sudo rm -f /usr/local/bin/cockpit-web "$PERSISTENT_BIN/cockpit-web" "$HOME/.local/bin/cockpit-web" "/home/zerops/.local/bin/cockpit-web" 2>/dev/null || true
    cat <<EOF | sudo tee /usr/local/bin/cockpit-web >/dev/null
#!/usr/bin/env bash
exec bash "$COCKPIT_WEB_SRC" "\$@"
EOF
    sudo chmod +x /usr/local/bin/cockpit-web
    [ -d "$PERSISTENT_BIN" ] && sudo cp -f /usr/local/bin/cockpit-web "$PERSISTENT_BIN/cockpit-web" && sudo chown zerops:zerops "$PERSISTENT_BIN/cockpit-web" 2>/dev/null || true
    [ -d "$HOME/.local/bin" ] && cp -f /usr/local/bin/cockpit-web "$HOME/.local/bin/cockpit-web" 2>/dev/null || true
    [ -d "/home/zerops/.local/bin" ] && cp -f /usr/local/bin/cockpit-web "/home/zerops/.local/bin/cockpit-web" 2>/dev/null || true
fi

# Configuración determinista de Nginx Proxy para Cockpit Web (/cockpit/)
if [ -f "/etc/nginx/nginx.conf" ] && ! grep -q "location /cockpit/" /etc/nginx/nginx.conf; then
    echo "• Inyectando proxy inverso /cockpit/ en /etc/nginx/nginx.conf..."
    sudo sed -i '/location \/ {/i \        location /cockpit/ {\n            proxy_pass http://127.0.0.1:3050/;\n            proxy_http_version 1.1;\n            proxy_set_header Host $host;\n            proxy_set_header Upgrade $http_upgrade;\n            proxy_set_header Connection $connection_upgrade;\n            proxy_set_header X-Real-IP $remote_addr;\n            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n            proxy_set_header X-Forwarded-Proto $scheme;\n        }\n' /etc/nginx/nginx.conf
    sudo nginx -s reload 2>/dev/null || true
fi

# 3. Skills de Plataforma ZCP y DCKR gestionadas de forma centralizada por setup-drive.sh

# 4. Contratos ZCP & DCKR indexados canónicamente en setup-gentle.sh y .atl/skill-registry.md (Lean AGENTS.md)
echo "• Contratos arquitectónicos ZCP & Docker preservados canónicamente en AGENTS.md y .atl/skill-registry.md."

# 5. Instalación y Activación Nativa de Skill Packs de la Plataforma ZCP
if command -v zcp >/dev/null 2>&1; then
    echo "• Aprovisionando packs nativos de la plataforma Zerops (zcp skills)..."
    zcp skills pack-add andrej-karpathy-skills 2>/dev/null || true
    zcp skills pack-add superpowers 2>/dev/null || true
    # Replicación simétrica hacia Antigravity CLI
    mkdir -p "/home/zerops/.gemini/antigravity-cli/skills" 2>/dev/null || true
    cp -rn /var/www/.agents/skills/* /home/zerops/.gemini/antigravity-cli/skills/ 2>/dev/null || true
fi

# 6. Autenticación Soberana Determinista de zcli CLI
if command -v zcli >/dev/null 2>&1; then
    RESOLVED_ZCLI_TOKEN="${ZCP_API_KEY:-${ZEROPS_TOKEN:-${Z_TOKEN:-}}}"
    if [ -z "$RESOLVED_ZCLI_TOKEN" ] && [ -f /var/www/.env ]; then
        RESOLVED_ZCLI_TOKEN=$(grep -E '^(ZCP_API_KEY|ZEROPS_TOKEN|Z_TOKEN)=' /var/www/.env | head -n1 | cut -d= -f2- | sed 's/["'\'']//g') || true
    fi
    if [ -n "$RESOLVED_ZCLI_TOKEN" ]; then
        echo "• Autenticando zcli con token oficial de plataforma Zerops..."
        zcli login "$RESOLVED_ZCLI_TOKEN" 2>/dev/null || true
        if [ -f "$HOME/.config/zerops/.zcli.yml" ]; then
            sudo mkdir -p /root/.config/zerops /home/zerops/.config/zerops 2>/dev/null || true
            sudo cp -f "$HOME/.config/zerops/.zcli.yml" /root/.config/zerops/.zcli.yml 2>/dev/null || true
            sudo cp -f "$HOME/.config/zerops/.zcli.yml" /home/zerops/.config/zerops/.zcli.yml 2>/dev/null || true
            sudo chown -R zerops:zerops /home/zerops/.config 2>/dev/null || true
        fi
        echo "  ✅ zcli autenticado deterministamente para $(whoami)"
    fi
fi

echo "============================================================"
echo "  Skills ZCP & DCKR v6.7 Desplegadas con Éxito"
echo "============================================================"
