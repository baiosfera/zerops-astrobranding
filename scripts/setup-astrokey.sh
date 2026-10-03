#!/usr/bin/env bash
# ==============================================================================
# Universal Astrological Secret Ingestion, NLM Installer & MCP Deployer
# Version: 4.5 (Antigravity MCP Schemas Deployment, Interactive Key Prompt & nlm setup)
# ==============================================================================
set -euo pipefail

INTERACTIVE=false
CUSTOM_FILE=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZCP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_SRC="$ZCP_ROOT/.agents/skills"
MCP_REGISTRY="$ZCP_ROOT/mcp/mcp_registry.json"
MCP_SCHEMAS_SRC="$ZCP_ROOT/mcp/schemas"
MCP_AUTH_SRC="$ZCP_ROOT/mcp/.mcp-auth"
NLM_AUTH_SRC="$ZCP_ROOT/mcp/.nlm-auth"
TARGET_AGENTS="/var/www/.agents/skills"
GEMINI_SKILLS="$HOME/.gemini/antigravity-cli/skills"
PERSISTENT_BIN="/var/www/.bin"

mkdir -p "$PERSISTENT_BIN" "$HOME/.local/bin"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -i|--interactive) INTERACTIVE=true; shift ;;
        --file|-f) CUSTOM_FILE="$2"; shift 2 ;;
        *)
            if [ -f "$1" ]; then
                CUSTOM_FILE="$1"
            fi
            shift
            ;;
    esac
done

echo "============================================================"
echo "  [6/6] Ingestión de Claves, NLM & MCPs (setup-astrokey.sh v4.5)"
echo "============================================================"

# 0. Dependencias Base de SO y Runtimes (pip, jq, uv)
if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq && sudo apt-get install -y -qq python3-pip python3-venv jq curl unzip 2>/dev/null || true
fi

if ! command -v uv &>/dev/null && ! command -v uvx &>/dev/null; then
    echo "• Instalando uv/uvx runtime para servidores MCP..."
    curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null || true
    for uv_bin in "$HOME/.local/bin/uv" "$HOME/.local/bin/uvx" "/root/.local/bin/uv" "/root/.local/bin/uvx"; do
        if [ -f "$uv_bin" ]; then
            cp "$uv_bin" "$PERSISTENT_BIN/" 2>/dev/null || true
            chmod +x "$PERSISTENT_BIN/$(basename "$uv_bin")" 2>/dev/null || true
            sudo ln -sf "$uv_bin" "/usr/local/bin/$(basename "$uv_bin")" 2>/dev/null || true
        fi
    done
fi

# 1. Instalación Idempotente de NotebookLM CLI & MCP (notebooklm-mcp-cli)
echo "• Verificando motor de NotebookLM (nlm CLI & MCP)..."
if ! command -v nlm &>/dev/null; then
    echo "  📦 Instalando notebooklm-mcp-cli desde PyPI..."
    uv tool install notebooklm-mcp-cli 2>/dev/null || uv pip install --system notebooklm-mcp-cli 2>/dev/null || pip install --break-system-packages notebooklm-mcp-cli 2>/dev/null || pip3 install notebooklm-mcp-cli 2>/dev/null || true
    
    for bin_src in "$HOME/.local/bin/nlm" "$HOME/.local/bin/notebooklm-mcp" "/usr/local/bin/nlm" "/usr/local/bin/notebooklm-mcp"; do
        if [ -f "$bin_src" ]; then
            cp "$bin_src" "$PERSISTENT_BIN/" 2>/dev/null || true
            chmod +x "$PERSISTENT_BIN/$(basename "$bin_src")" 2>/dev/null || true
        fi
    done
fi

if command -v nlm &>/dev/null; then
    echo "  ✅ nlm CLI activo: $(which nlm)"
fi

# 1.1 Parche Idempotente de Gobernanza: DeleteChatTurns [None, conv_id, None, True] en notebooklm_tools
python3 -c '
import glob, os
patterns = [
    "/home/*/.local/share/uv/tools/notebooklm-mcp-cli/lib/python*/site-packages/notebooklm_tools/core/conversation.py",
    "/root/.local/share/uv/tools/notebooklm-mcp-cli/lib/python*/site-packages/notebooklm_tools/core/conversation.py",
]
for p in patterns:
    for f in glob.glob(p):
        if os.path.exists(f):
            with open(f, "r") as fp:
                c = fp.read()
            if "[notebook_id, conversation_id]" in c:
                c = c.replace("[notebook_id, conversation_id]", "[None, conversation_id, None, True]")
                with open(f, "w") as fp:
                    fp.write(c)
' 2>/dev/null || true

# 1b. Instalación Idempotente de lunar-mcp-server (Motor MCP Lunar & BaZi)
echo "• Verificando motor de lunar-mcp-server..."
if ! command -v lunar-mcp-server &>/dev/null && [ ! -f "$PERSISTENT_BIN/lunar-mcp-server" ] && [ ! -f "$HOME/.local/bin/lunar-mcp-server" ] && [ ! -f "/home/zerops/.local/bin/lunar-mcp-server" ]; then
    echo "  📦 Instalando lunar-mcp-server desde PyPI..."
    uv tool install lunar-mcp-server 2>/dev/null || pip install --break-system-packages lunar-mcp-server 2>/dev/null || pip3 install lunar-mcp-server 2>/dev/null || true
    for bin_src in "$HOME/.local/bin/lunar-mcp-server" "/home/zerops/.local/bin/lunar-mcp-server"; do
        if [ -f "$bin_src" ]; then
            cp "$bin_src" "$PERSISTENT_BIN/" 2>/dev/null || true
            chmod +x "$PERSISTENT_BIN/$(basename "$bin_src")" 2>/dev/null || true
            sudo ln -sf "$PERSISTENT_BIN/$(basename "$bin_src")" "/usr/local/bin/$(basename "$bin_src")" 2>/dev/null || true
        fi
    done
fi

if command -v lunar-mcp-server &>/dev/null || [ -f "/home/zerops/.local/bin/lunar-mcp-server" ]; then
    echo "  ✅ lunar-mcp-server activo"
fi

# 2. Resolución de Archivo de Claves (Sin auto-adivinación)
RESOLVED_KEY_FILE=""
if [ -n "$CUSTOM_FILE" ] && [ -f "$CUSTOM_FILE" ]; then
    RESOLVED_KEY_FILE="$CUSTOM_FILE"
    echo "• Usando archivo de claves especificado: $RESOLVED_KEY_FILE"
elif [ -z "$CUSTOM_FILE" ] && [ -t 0 ] && [ "$INTERACTIVE" = false ]; then
    read -r -p "• Ingrese la ruta del archivo de claves astrológicas (.md / .env) [o Enter para continuar]: " USER_ASTRO_FILE
    USER_ASTRO_FILE=$(echo "$USER_ASTRO_FILE" | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
    [ -n "$USER_ASTRO_FILE" ] && [ -f "$USER_ASTRO_FILE" ] && RESOLVED_KEY_FILE="$USER_ASTRO_FILE"
fi

sanitize_val() {
    local val="$1"
    val=$(echo "$val" | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["'"'"']//' -e 's/["'"'"']$//')
    echo "$val"
}

REQUIRED_ASTRO_KEYS=(
    "FREEASTRO_API_KEY:Clave de FreeAstroAPI (Natal, Sideral, BaZi, Védica, Dasha)"
    "ASTROLOGY_API_IO:Clave de Astrology-API.io V3 / AstrologyAPI V1 (Gematría, Core Numbers, Tarot, KP)"
    "VEDASTRO_API_KEY:Clave de VedAstro (Predicciones clásicas y búsqueda semántica BPHS)"
    "ASTROWAY_API_KEY:Clave de AstroWay REST Engine (Swiss Ephemeris 760 Endpoints)"
    "KUNDALI_MCP_KEY:Clave de Servidor MCP Kundali"
    "NASA_API_KEY:Clave de API NASA Ephemeris / NeoWs (Opcional, default: DEMO_KEY)"
)

COLLECTED_EXPORTS=""

# 3. Ingestión desde el archivo resuelto
if [ -n "$RESOLVED_KEY_FILE" ] && [ -f "$RESOLVED_KEY_FILE" ]; then
    CURRENT_KEY=""
    while IFS= read -r raw_line || [ -n "$raw_line" ]; do
        line=$(sanitize_val "$raw_line")
        [ -z "$line" ] && continue
        [[ "$line" =~ ^# ]] && continue
        
        if [[ "$line" =~ ^export[[:space:]]+([A-Za-z0-9_]+)=(.*)$ ]]; then
            k="${BASH_REMATCH[1]}"
            v=$(sanitize_val "${BASH_REMATCH[2]}")
            export "$k=$v"
            COLLECTED_EXPORTS+="$k=$v"$'\n'
        elif [[ "$line" =~ ^([A-Za-z0-9_]+)=(.*)$ ]]; then
            k="${BASH_REMATCH[1]}"
            v=$(sanitize_val "${BASH_REMATCH[2]}")
            export "$k=$v"
            COLLECTED_EXPORTS+="$k=$v"$'\n'
        elif [[ "$line" =~ ^[A-Za-z0-9_]+_?(TOKEN|KEY|API|IO)$ ]]; then
            CURRENT_KEY="$line"
            [ "$CURRENT_KEY" = "ASTRO_WAY_API" ] && CURRENT_KEY="ASTROWAY_API_KEY"
            [ "$CURRENT_KEY" = "ASTRO_API_KEY" ] && CURRENT_KEY="VEDASTRO_API_KEY"
        elif [ -n "$CURRENT_KEY" ]; then
            v=$(sanitize_val "$line")
            export "$CURRENT_KEY=$v"
            COLLECTED_EXPORTS+="$CURRENT_KEY=$v"$'\n'
            echo "  ✓ Ingestada $CURRENT_KEY"
            CURRENT_KEY=""
        fi
    done < "$RESOLVED_KEY_FILE"
fi

# 4. Auditar claves en el entorno
MISSING_KEYS=()

for item in "${REQUIRED_ASTRO_KEYS[@]}"; do
    KEY_NAME="${item%%:*}"
    KEY_DESC="${item#*:}"
    
    RAW_VAL="${!KEY_NAME:-}"
    if [ -n "$RAW_VAL" ]; then
        CLEAN_VAL=$(sanitize_val "$RAW_VAL")
        export "$KEY_NAME=$CLEAN_VAL"
        echo "  ✅ $KEY_NAME: Configurada"
        COLLECTED_EXPORTS+="$KEY_NAME=$CLEAN_VAL"$'\n'
    else
        MISSING_KEYS+=("$KEY_NAME:$KEY_DESC")
    fi
done

# 5. Entrada Interactiva
if [ "$INTERACTIVE" = true ] && [ ${#MISSING_KEYS[@]} -gt 0 ]; then
    echo ""
    echo "• Ingresa las claves astrológicas faltantes (o 'skip' para omitir):"
    for item in "${MISSING_KEYS[@]}"; do
        KEY_NAME="${item%%:*}"
        KEY_DESC="${item#*:}"
        read -r -s -p "  🔑 $KEY_NAME ($KEY_DESC) [o 'skip']: " INPUT_VAL
        echo ""
        CLEAN_INPUT=$(sanitize_val "$INPUT_VAL")
        if [ -n "$CLEAN_INPUT" ] && [ "$CLEAN_INPUT" != "skip" ] && [ "$CLEAN_INPUT" != "none" ]; then
            export "$KEY_NAME=$CLEAN_INPUT"
            COLLECTED_EXPORTS+="$KEY_NAME=$CLEAN_INPUT"$'\n'
            echo "    ✓ $KEY_NAME registrada"
        fi
    done
elif [ ${#MISSING_KEYS[@]} -gt 0 ]; then
    echo "• Aviso: ${#MISSING_KEYS[@]} clave(s) no detectadas en entorno actual."
    echo "  Puedes ingresarlas con: $0 --interactive"
fi

# 6. Persistir en el entorno del sistema y perfiles bash
if [ -n "$COLLECTED_EXPORTS" ]; then
    echo "• Persistiendo variables en /etc/environment, .env y .bashrc..."
    sudo touch /etc/environment 2>/dev/null || true
    while IFS='=' read -r k v; do
        if [ -n "$k" ] && [ -n "$v" ]; then
            sudo sed -i "/^$k=/d" /etc/environment 2>/dev/null || true
            sudo bash -c "echo '$k=\"$v\"' >> /etc/environment" 2>/dev/null || true
        fi
    done <<< "$COLLECTED_EXPORTS"
    
    # Inyectar en subshells de usuario (sin escribir /var/www/.env para proteger el arranque en Zerops)
    for env_file in "$HOME/.env" "/home/zerops/.env"; do
        mkdir -p "$(dirname "$env_file")" 2>/dev/null || true
        touch "$env_file" 2>/dev/null || true
        while IFS='=' read -r k v; do
            if [ -n "$k" ] && [ -n "$v" ]; then
                sed -i "/^$k=/d" "$env_file" 2>/dev/null || true
                echo "$k=$v" >> "$env_file"
            fi
        done <<< "$COLLECTED_EXPORTS"
    done

    # Inyectar en profile.d para que cualquier subshell / login cargue las variables desde /etc/environment
    sudo bash -c "cat << 'PROFILE_EOF' > /etc/profile.d/zerops_env.sh
set -a
[ -f /etc/environment ] && . /etc/environment
set +a
PROFILE_EOF" 2>/dev/null || true

    for rc in "$HOME/.bashrc" "/home/zerops/.bashrc" "/root/.bashrc"; do
        if [ -f "$rc" ]; then
            while IFS='=' read -r k v; do
                if [ -n "$k" ] && [ -n "$v" ]; then
                    sed -i "/export $k=/d" "$rc" 2>/dev/null || true
                    echo "export $k=\"$v\"" >> "$rc"
                fi
            done <<< "$COLLECTED_EXPORTS"
        fi
    done
    sudo chown -R zerops:zerops /home/zerops/.env 2>/dev/null || true
    rm -f /var/www/.env /var/www/gdrive.env 2>/dev/null || true
fi

# 7. Restauración de Sesiones OAuth
if [ -d "$MCP_AUTH_SRC" ]; then
    echo "• Sincronizando caché de sesiones OAuth de MCPs..."
    mkdir -p "$HOME/.mcp-auth" "/home/zerops/.mcp-auth" 2>/dev/null || true
    cp -r "$MCP_AUTH_SRC"/* "$HOME/.mcp-auth/" 2>/dev/null || true
    if [ "$HOME" != "/home/zerops" ]; then
        cp -r "$MCP_AUTH_SRC"/* "/home/zerops/.mcp-auth/" 2>/dev/null || true
    fi
    sudo chown -R zerops:zerops "$HOME/.mcp-auth" "/home/zerops/.mcp-auth" 2>/dev/null || true
    echo "  ✅ Sesiones OAuth de MCPs sincronizadas."
fi

# 8. Restauración y Aprovisionamiento Persistente de Google NotebookLM
if [ -f "$SCRIPT_DIR/setup-nlm-auth.sh" ]; then
    echo "• Invocando motor persistente de NotebookLM (setup-nlm-auth.sh)..."
    bash "$SCRIPT_DIR/setup-nlm-auth.sh" --install
elif [ -f "$ZCP_ROOT/scripts/setup-nlm-auth.sh" ]; then
    echo "• Invocando motor persistente de NotebookLM desde ZCP_ROOT..."
    bash "$ZCP_ROOT/scripts/setup-nlm-auth.sh" --install
elif [ -d "$NLM_AUTH_SRC" ]; then
    echo "• Restaurando sesión de Google NotebookLM desde Google Drive..."
    mkdir -p "$HOME/.notebooklm-mcp-cli" "/home/zerops/.notebooklm-mcp-cli" 2>/dev/null || true
    cp -r "$NLM_AUTH_SRC"/* "$HOME/.notebooklm-mcp-cli/" 2>/dev/null || true
    if [ "$HOME" != "/home/zerops" ]; then
        cp -r "$NLM_AUTH_SRC"/* "/home/zerops/.notebooklm-mcp-cli/" 2>/dev/null || true
    fi
    sudo chown -R zerops:zerops "$HOME/.notebooklm-mcp-cli" "/home/zerops/.notebooklm-mcp-cli" 2>/dev/null || true
    nlm setup add antigravity 2>/dev/null || true
    echo "  ✅ Sesión de NotebookLM restaurada con éxito."
fi

for nlm_candidate in "/var/www/notebook.json" "$ZCP_ROOT/apis/notebook.json" "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/apis/notebook.json"; do
    if [ -f "$nlm_candidate" ]; then
        echo "• Sincronizando sesión de NotebookLM con $nlm_candidate..."
        nlm login --manual -f "$nlm_candidate" --force 2>/dev/null || true
        break
    fi
done

# 9. Despliegue de Esquemas MCP en Antigravity CLI (Optimizado con tarball)
if [ -f "$ZCP_ROOT/mcp/schemas.tar.gz" ]; then
    echo "• Desplegando esquemas MCP en Antigravity (extracción instantánea)..."
    mkdir -p "/home/zerops/.gemini/antigravity-cli/mcp" "$HOME/.gemini/antigravity-cli/mcp" 2>/dev/null || true
    tar -xzf "$ZCP_ROOT/mcp/schemas.tar.gz" -C "/home/zerops/.gemini/antigravity-cli/mcp/" 2>/dev/null || true
    if [ "$HOME" != "/home/zerops" ]; then
        tar -xzf "$ZCP_ROOT/mcp/schemas.tar.gz" -C "$HOME/.gemini/antigravity-cli/mcp/" 2>/dev/null || true
    fi
    sudo chown -R zerops:zerops "/home/zerops/.gemini" 2>/dev/null || true
    echo "  ✅ Esquemas MCP desplegados en milisegundos."
elif [ -d "$MCP_SCHEMAS_SRC" ]; then
    echo "• Desplegando esquemas MCP en Antigravity (/home/zerops/.gemini/antigravity-cli/mcp/)..."
    mkdir -p "/home/zerops/.gemini/antigravity-cli/mcp" "$HOME/.gemini/antigravity-cli/mcp" 2>/dev/null || true
    cp -r "$MCP_SCHEMAS_SRC"/* "/home/zerops/.gemini/antigravity-cli/mcp/" 2>/dev/null || true
    if [ "$HOME" != "/home/zerops" ]; then
        cp -r "$MCP_SCHEMAS_SRC"/* "$HOME/.gemini/antigravity-cli/mcp/" 2>/dev/null || true
    fi
    sudo chown -R zerops:zerops "/home/zerops/.gemini" 2>/dev/null || true
    echo "  ✅ Esquemas MCP desplegados."
fi

# 10. Inyección y Merge de Servidores MCP en Antigravity
echo "• Inyectando y sincronizando configuración de Servidores MCP..."
if [ -f "$MCP_REGISTRY" ]; then
    for cfg in "$HOME/.gemini/antigravity-cli/mcp_config.json" "/var/www/.gemini/config/mcp_config.json" "/home/zerops/.gemini/antigravity-cli/mcp_config.json"; do
        if [ -f "$cfg" ] || [ -d "$(dirname "$cfg")" ]; then
            TMP_EXPANDED=$(mktemp)
            eval "cat << 'ENV_EOF'
$(cat "$MCP_REGISTRY")
ENV_EOF" > "$TMP_EXPANDED" 2>/dev/null || cp "$MCP_REGISTRY" "$TMP_EXPANDED"
            
            if [ -f "$cfg" ]; then
                jq -s '.[0] * .[1]' "$cfg" "$TMP_EXPANDED" > "${cfg}.tmp" && mv "${cfg}.tmp" "$cfg"
            else
                cp "$TMP_EXPANDED" "$cfg"
            fi
            rm -f "$TMP_EXPANDED"
            echo "  ✅ Servidores MCP inyectados en $cfg"
        fi
    done
fi

# 11. Inyección de Suites de Astrología y Branding en AGENTS.md
INJECTOR=$(command -v inject-agent-rule 2>/dev/null || echo "/home/zerops/.local/bin/inject-agent-rule")
if [ -x "$INJECTOR" ]; then
    echo "• Registrando suites de Astrología y Branding (Offloaded to references)..."
    
    mkdir -p "/var/www/.agents/references" "$ZCP_ROOT/.agents/references" 2>/dev/null || true
    if [ -f "$ZCP_ROOT/.agents/references/astro_suites_encyclopedia.md" ]; then
        cp -f "$ZCP_ROOT/.agents/references/astro_suites_encyclopedia.md" "/var/www/.agents/references/astro_suites_encyclopedia.md"
    fi
    if [ -d "$HOME/.gemini/antigravity-cli" ] && [ -f "/var/www/.agents/references/astro_suites_encyclopedia.md" ]; then
        mkdir -p "$HOME/.gemini/antigravity-cli/references" 2>/dev/null || true
        cp -f "/var/www/.agents/references/astro_suites_encyclopedia.md" "$HOME/.gemini/antigravity-cli/references/" 2>/dev/null || true
    fi
    echo "• Suites Astrológica y Branding indexadas en .agents/references/astro_suites_encyclopedia.md y .atl/skill-registry.md (Lean AGENTS.md)"
fi

# 12. Compilación del Registro de Gentle AI
if command -v gentle-ai >/dev/null 2>&1; then
    echo "• Refrescando registro nativo de skills (.atl/skill-registry.md)..."
    gentle-ai skill-registry refresh --force 2>/dev/null || true
    echo "  ✅ Skill registry refrescado con éxito."
fi

echo "============================================================"
echo "  🔑 Ingestión de Claves Astrológicas, NLM & MCPs Finalizado (v4.5)"
echo "============================================================"
