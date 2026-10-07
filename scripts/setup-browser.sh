#!/usr/bin/env bash
# ==============================================================================
# Setup Browser & Search MCP Servers for Zerops ZCP
# Version: 3.5 (High-Density RFC Suites, Centralized bak/ SSoT, Lean AGENTS.md)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZCP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="/var/www"
PERSISTENT_BIN="$PROJECT_ROOT/.bin"
PERSISTENT_AGENTS="$PROJECT_ROOT/.agents"
PERSISTENT_GEMINI="$PROJECT_ROOT/.gemini"

mkdir -p "$PERSISTENT_BIN" "$PERSISTENT_AGENTS/skills" "$PERSISTENT_GEMINI/config"

echo "============================================================"
echo "  [3/4] Desplegando MCP Search Hub, research & docu Skills (v3.1)"
echo "============================================================"

# 1. Configurar Servidores MCP con las API keys del entorno
[ -f /etc/environment ] && set -a && . /etc/environment 2>/dev/null && set +a || true
[ -f "$HOME/.bashrc" ] && set -a && . "$HOME/.bashrc" 2>/dev/null && set +a || true
[ -f "$PROJECT_ROOT/.env" ] && set -a && . "$PROJECT_ROOT/.env" 2>/dev/null && set +a || true

mkdir -p "$PERSISTENT_GEMINI/config" "$PERSISTENT_GEMINI/antigravity-cli"

cat > "$PERSISTENT_GEMINI/config/mcp_config.json" << EOF
{
  "mcpServers": {
    "brave": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY:-}"
      },
      "disabled": false
    },
    "context7": {
      "disabled": false,
      "serverUrl": "https://mcp.context7.com/mcp"
    },
    "duckduckgo": {
      "command": "npx",
      "args": ["-y", "duckduckgo-mcp-server"],
      "disabled": false
    },
    "engram": {
      "args": [
        "mcp"
      ],
      "command": "/var/www/.bin/engram",
      "disabled": false
    },
    "exa": {
      "command": "npx",
      "args": ["-y", "exa-mcp-server"],
      "env": {
        "EXA_API_KEY": "${EXA_API_KEY:-}"
      },
      "disabled": false
    },
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "${FIRECRAWL_API_KEY:-}"
      },
      "disabled": false
    },
    "jina": {
      "command": "npx",
      "args": ["-y", "@jina-ai/mcp-server"],
      "env": {
        "JINA_API_KEY": "${JINA_API_KEY:-}"
      },
      "disabled": false
    },
    "tavily": {
      "command": "npx",
      "args": ["-y", "tavily-mcp"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY:-}"
      },
      "disabled": false
    },
    "zerops": {
      "args": [
        "serve"
      ],
      "command": "zcp",
      "description": "Zerops platform MCP server",
      "trust": true
    }
  }
}
EOF

# Sincronizar configuración MCP en todos los perfiles
cp "$PERSISTENT_GEMINI/config/mcp_config.json" "$PERSISTENT_GEMINI/antigravity-cli/mcp_config.json"

for base_dir in "$HOME/.gemini" "/home/zerops/.gemini" "/root/.gemini"; do
    if [ -d "$base_dir" ] || [ "$base_dir" = "$HOME/.gemini" ]; then
        mkdir -p "$base_dir/config" "$base_dir/antigravity-cli" 2>/dev/null || true
        ln -sf "$PERSISTENT_GEMINI/config/mcp_config.json" "$base_dir/config/mcp_config.json" 2>/dev/null || true
        ln -sf "$PERSISTENT_GEMINI/antigravity-cli/mcp_config.json" "$base_dir/antigravity-cli/mcp_config.json" 2>/dev/null || true
    fi
done

# 2. Skills de Scraping y Browser gestionadas de forma centralizada por setup-drive.sh

# 3. Reglas de Scraping indexadas canónicamente en setup-gentle.sh y .atl/skill-registry.md (Lean AGENTS.md)
echo "• Skills de Scraping y Browser preservadas canónicamente en AGENTS.md y .atl/skill-registry.md."

echo "============================================================"
echo "  MCP Servers, research & docu Skills v3.5 Desplegados"
echo "============================================================"
