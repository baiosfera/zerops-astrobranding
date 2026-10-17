#!/usr/bin/env bash
# ==============================================================================
# Sovereign Google Drive Skills Synchronizer & Auto-Discovery Engine (setup-drive.sh)
# Version: 1.7 (Self-Healing SSoT Triad, Dynamic Skill Inventory & Resilient Parity)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-/var/www}"
DRIVE_MOUNT="${GDRIVE_MOUNT_DIR:-/var/www/baiosfera}"
DRIVE_SSOT="$DRIVE_MOUNT/0ZEROPS-AGY/0zcp-123"

if [ -d "$DRIVE_SSOT" ]; then
    SSOT_ROOT="$DRIVE_SSOT"
elif [ -d "$SCRIPT_DIR/../../0ZEROPS-AGY/0zcp-123" ]; then
    SSOT_ROOT="$(cd "$SCRIPT_DIR/../../0ZEROPS-AGY/0zcp-123" && pwd)"
elif [ -d "$(cd "$SCRIPT_DIR/.." && pwd)/.agents" ]; then
    SSOT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    SSOT_ROOT="$PROJECT_ROOT"
fi
ZCP_ROOT="$SSOT_ROOT"

SKILLS_SRC="$SSOT_ROOT/.agents/skills"
TARGET_AGENTS="/var/www/.agents/skills"
GEMINI_SKILLS="$HOME/.gemini/antigravity-cli/skills"

echo "============================================================"
echo "  [3/6] Sincronización Google Drive & Auto-Discovery de Skills (v1.7)"
echo "============================================================"

mkdir -p "$TARGET_AGENTS" "$GEMINI_SKILLS" "/home/zerops/.gemini/antigravity-cli/skills" 2>/dev/null || true
mkdir -p "$ZCP_ROOT/bak/scripts" "$ZCP_ROOT/bak/rules" "$ZCP_ROOT/bak/skills" "$ZCP_ROOT/bak/apis" "$ZCP_ROOT/bak/mcp" 2>/dev/null || true

DISCOVERED_EXTENSIONS=""

SKILLS_REPO_URL="https://github.com/baiosfera/zerops-astro-skills.git"
SKILLS_LOCAL_CACHE="/var/www/zerops-astro-skills"

# Prioridad 1: Sincronización ultrarrápida desde GitHub a caché local NVMe (<1.5s)
SYNCED_FROM_GITHUB=false
if git ls-remote "$SKILLS_REPO_URL" &>/dev/null; then
    if [ ! -d "$SKILLS_LOCAL_CACHE/.git" ]; then
        git clone --depth 1 "$SKILLS_REPO_URL" "$SKILLS_LOCAL_CACHE" 2>/dev/null || true
    else
        git -C "$SKILLS_LOCAL_CACHE" pull --ff-only 2>/dev/null || true
    fi
    if [ -d "$SKILLS_LOCAL_CACHE" ]; then
        SKILLS_SRC="$SKILLS_LOCAL_CACHE"
        SKILL_COUNT=$(find "$SKILLS_LOCAL_CACHE" -mindepth 1 -maxdepth 1 -type d ! -name ".*" | wc -l)
        echo "• Sincronizando $SKILL_COUNT skills soberanas desde GitHub ($SKILLS_REPO_URL)..."
        SYNCED_FROM_GITHUB=true
    fi
fi

if [ -d "$SKILLS_SRC" ]; then
    echo "• Escaneando catálogo de skills soberanas ($SKILLS_SRC)..."
    for skill_dir in "$SKILLS_SRC"/*; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            
            # Sincronización activa soberana: actualizar o desplegar la skill hacia el workspace local
            mkdir -p "$TARGET_AGENTS/$skill_name"
            if command -v rsync >/dev/null 2>&1; then
                rsync -a --delete --exclude="__pycache__" --exclude="*.pyc" --exclude="*.bak" "$skill_dir/" "$TARGET_AGENTS/$skill_name/"
            else
                cp -rf "$skill_dir"/* "$TARGET_AGENTS/$skill_name/" 2>/dev/null || true
            fi

            # Replicar en el directorio de Gemini/Antigravity
            if [ -d "$GEMINI_SKILLS" ]; then
                mkdir -p "$GEMINI_SKILLS/$skill_name"
                if command -v rsync >/dev/null 2>&1; then
                    rsync -a --exclude="__pycache__" --exclude="*.pyc" "$skill_dir/" "$GEMINI_SKILLS/$skill_name/" 2>/dev/null || true
                else
                    cp -rf "$skill_dir"/* "$GEMINI_SKILLS/$skill_name/" 2>/dev/null || true
                fi
            fi
            if [ -d "/home/zerops/.gemini/antigravity-cli/skills" ] && [ "$HOME" != "/home/zerops" ]; then
                mkdir -p "/home/zerops/.gemini/antigravity-cli/skills/$skill_name"
                if command -v rsync >/dev/null 2>&1; then
                    rsync -a --exclude="__pycache__" --exclude="*.pyc" "$skill_dir/" "/home/zerops/.gemini/antigravity-cli/skills/$skill_name/" 2>/dev/null || true
                else
                    cp -rf "$skill_dir"/* "/home/zerops/.gemini/antigravity-cli/skills/$skill_name/" 2>/dev/null || true
                fi
            fi

            # Clasificar si es una extensión dinámica que no pertenece a las suites estándar
            case "$skill_name" in
                alpine|astro*|automation-engine|bazi-lunar|bifrost|bknd|brandbook|bun|business-insights|checkout-funnels|chroma|cloudflare|cohalo|crmfrappe|dckr|devllm-telemetry|directus|docu|email-marketing|erpnext|fastapi|fontgen|freeastroapi|freellmapi|frnt|ghcicd|golang|growth-engine|hebcal|hermes-agent|kinetic|kundali|listmonk|local-storage|shared-storage|nasa|nats|nodejs|notebooklm|oraculo*|orchesbrand|orders-fulfillment|payment-gateways|planner|postgresql|python|qdrant|research|rust|sales-enablement|seo-aeo-geo|social-distrib|symbol|ubuntu|valkey|vedastro|whatsapp-engine|zcp|zmanim)
                    # Skill core / suite soberana conocida
                    ;;
                *)
                    echo "  🔍 Extensión de proyecto descubierta: $skill_name"
                    DISCOVERED_EXTENSIONS+="- **$skill_name**: \`.agents/skills/$skill_name/\` (Dual-RAG project extension)"$'\n'
                    ;;
            esac
        fi
    done

    # AUTO-HEALING SSoT DRIVE PARITY (Garantizar paridad bidireccional absoluta)
    DRIVE_SSOT_SKILLS="$SSOT_ROOT/.agents/skills"
    if [ -d "$DRIVE_SSOT_SKILLS" ]; then
        if [ "$SYNCED_FROM_GITHUB" = true ]; then
            echo "• Verificando paridad y auto-sanando Google Drive SSoT desde GitHub..."
            for s_dir in "$TARGET_AGENTS"/*; do
                [ -d "$s_dir" ] || continue
                s_name=$(basename "$s_dir")
                case "$s_name" in
                    react-19|zustand-5|tailwind-4|ai-sdk-5|nextjs-15|typescript|zod-4|playwright|puppeteer|crawl4ai|firecrawl|angular|django-drf|spring-boot-3|java-21|electron|elixir-antipatterns|pytest|go-testing|hexagonal-architecture-layers-java|react-native|sdd-*|rdd-*|github-pr|work-unit-commits|jira-*|issue-*|gentle-ai-*|systemic-issue-triage|judgment-day|comment-writer|cognitive-doc-design|gga|_shared|branch-pr|chained-pr|skill-creator|skill-registry|skill-improver|hermes-ephemeral-*|pocock*)
                        continue
                        ;;
                esac
                d_skill_md="$DRIVE_SSOT_SKILLS/$s_name/SKILL.md"
                l_skill_md="$s_dir/SKILL.md"
                if [ -f "$l_skill_md" ]; then
                    if [ ! -f "$d_skill_md" ]; then
                        mkdir -p "$DRIVE_SSOT_SKILLS/$s_name"
                        cp -f "$l_skill_md" "$d_skill_md" 2>/dev/null || true
                    elif ! cmp -s "$l_skill_md" "$d_skill_md"; then
                        cp -f "$l_skill_md" "$d_skill_md" 2>/dev/null || true
                    fi
                fi
                case "$s_name" in
                    oraculo|planner|docu|research)
                        if command -v rsync >/dev/null 2>&1; then
                            rsync -a --delete --exclude="__pycache__" --exclude="*.pyc" --exclude="*.bak" "$s_dir/" "$DRIVE_SSOT_SKILLS/$s_name/" 2>/dev/null || true
                        fi
                        ;;
                esac
            done
        else
            echo "• Sincronizando skills desde Google Drive SSoT (modo fallback)..."
            for s_dir in "$DRIVE_SSOT_SKILLS"/*; do
                [ -d "$s_dir" ] || continue
                s_name=$(basename "$s_dir")
                if command -v rsync >/dev/null 2>&1; then
                    rsync -a --exclude="__pycache__" --exclude="*.pyc" "$s_dir/" "$TARGET_AGENTS/$s_name/" 2>/dev/null || true
                else
                    cp -rf "$s_dir"/* "$TARGET_AGENTS/$s_name/" 2>/dev/null || true
                fi
            done
        fi
    fi

    # Sincronizar AGENTS.md y reglas de gobernanza desde SSoT
    if [ -f "$SSOT_ROOT/AGENTS.md" ]; then
        echo "• Sincronizando AGENTS.md desde Drive SSoT..."
        cp -f "$SSOT_ROOT/AGENTS.md" "/var/www/AGENTS.md" 2>/dev/null || true
    fi
    if [ -d "$SSOT_ROOT/.agents/rules" ]; then
        echo "• Sincronizando reglas de gobernanza (.agents/rules)..."
        mkdir -p "/var/www/.agents/rules" "/home/zerops/.gemini/antigravity-cli/rules" 2>/dev/null || true
        cp -rn "$SSOT_ROOT/.agents/rules"/* "/var/www/.agents/rules/" 2>/dev/null || true
    fi
    sudo chown -R zerops:zerops /var/www/.agents /home/zerops/.gemini 2>/dev/null || true
    echo "  ✅ Sincronización de Drive finalizada."
else
    echo "  ℹ️ No se detectó directorio de Google Drive en $SKILLS_SRC (Omitiendo)."
fi

# Garantizar paridad de catálogo entre workspace (.agents/skills) y perfil Antigravity
if [ -d "$TARGET_AGENTS" ]; then
    mkdir -p "$GEMINI_SKILLS" "/home/zerops/.gemini/antigravity-cli/skills" 2>/dev/null || true
    cp -rn "$TARGET_AGENTS/"* "$GEMINI_SKILLS/" 2>/dev/null || true
    [ "$HOME" != "/home/zerops" ] && cp -rn "$TARGET_AGENTS/"* "/home/zerops/.gemini/antigravity-cli/skills/" 2>/dev/null || true
fi

# Las extensiones descubiertas residen canónicamente en .atl/skill-registry.md para no inflar el prompt de sistema
echo "• Extensiones de proyecto indexadas en .atl/skill-registry.md (Lean AGENTS.md)"

# Compilación del Registro de Gentle AI
if command -v gentle-ai >/dev/null 2>&1; then
    echo "• Refrescando registro nativo de skills (.atl/skill-registry.md)..."
    gentle-ai skill-registry refresh --force 2>/dev/null || true
    echo "  ✅ Skill registry refrescado con éxito."
fi

echo "============================================================"
echo "  Google Drive Skills Sync & Auto-Discovery Finalizado (v1.6)"
echo "============================================================"
