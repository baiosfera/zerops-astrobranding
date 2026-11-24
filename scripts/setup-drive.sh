#!/usr/bin/env bash
# ==============================================================================
# Sovereign Google Drive Skills Synchronizer & Auto-Discovery Engine (setup-drive.sh)
# Version: 1.7 (Self-Healing SSoT Triad, Dynamic Skill Inventory & Resilient Parity)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-/var/www}"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -d "$REPO_DIR/.agents" ]; then
    SSOT_ROOT="$REPO_DIR"
elif [ -d "$SCRIPT_DIR/../.agents" ]; then
    SSOT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    SSOT_ROOT="$PROJECT_ROOT"
fi
ZCP_ROOT="$SSOT_ROOT"

SKILLS_SRC="$ZCP_ROOT/.agents/skills"
TARGET_AGENTS="/var/www/.agents/skills"
GEMINI_SKILLS="$HOME/.gemini/antigravity-cli/skills"

echo "============================================================"
echo "  [3/6] Sincronización Custom Skills SSoT (setup-drive.sh v2.0)"
echo "============================================================"

mkdir -p "$TARGET_AGENTS" "$GEMINI_SKILLS" "/home/zerops/.gemini/antigravity-cli/skills" 2>/dev/null || true

DISCOVERED_EXTENSIONS=""

SKILLS_REPO_URL="https://github.com/baiosfera/zerops-astro-skills.git"
SKILLS_LOCAL_CACHE="/var/www/zerops-astro-skills"

# Prioridad 1: Sincronización ultrarrápida desde GitHub a caché local NVMe (<1.5s)
SYNCED_FROM_GITHUB=false
if git ls-remote "$SKILLS_REPO_URL" &>/dev/null; then
    if [ ! -d "$SKILLS_LOCAL_CACHE/.git" ]; then
        git clone --depth 1 "$SKILLS_REPO_URL" "$SKILLS_LOCAL_CACHE" 2>/dev/null || true
    else
        git -C "$SKILLS_LOCAL_CACHE" fetch origin main 2>/dev/null || true
        git -C "$SKILLS_LOCAL_CACHE" reset --hard origin/main 2>/dev/null || git -C "$SKILLS_LOCAL_CACHE" pull --ff-only 2>/dev/null || true
        git -C "$SKILLS_LOCAL_CACHE" clean -fd 2>/dev/null || true
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
            
            # Enlace simbólico canónico desde zerops-astro-skills (sin copias físicas duplicadas)
            if [ -d "$TARGET_AGENTS/$skill_name" ] && [ ! -L "$TARGET_AGENTS/$skill_name" ]; then
                rm -rf "$TARGET_AGENTS/$skill_name"
            fi
            ln -sfn "$skill_dir" "$TARGET_AGENTS/$skill_name"

            # Remover posibles copias congeladas de skills soberanas en perfiles secundarios
            rm -rf "$GEMINI_SKILLS/$skill_name" "/home/zerops/.gemini/config/skills/$skill_name" "/var/www/.claude/skills/$skill_name" 2>/dev/null || true

            # Clasificar si es una extensión dinámica que no pertenece a las suites estándar
            case "$skill_name" in
                alpine|astro*|automation-engine|bazi-lunar|bifrost|bknd|brandbook|bun|business-insights|checkout-funnels|chroma|cloudflare|cohalo|crmfrappe|dckr|devllm-telemetry|docu|email-marketing|erpnext|fastapi|fontgen|freeastroapi|freellmapi|frnt|ghcicd|golang|growth-engine|hebcal|hermes-agent|kinetic|kundali|listmonk|local-storage|shared-storage|nasa|nats|nodejs|notebooklm|oraculo*|orchesbrand|orders-fulfillment|payment-gateways|planner|postgresql|python|qdrant|research|rust|sales-enablement|seo-aeo-geo|social-distrib|symbol|ubuntu|valkey|vedastro|whatsapp-engine|zcp|zmanim)
                    # Skill core / suite soberana conocida
                    ;;
                *)
                    echo "  🔍 Extensión de proyecto descubierta: $skill_name"
                    DISCOVERED_EXTENSIONS+="- **$skill_name**: \`.agents/skills/$skill_name/\` (Dual-RAG project extension)"$'\n'
                    ;;
            esac
        fi
    done

    # Blindaje Soberano Anti-Deriva: Re-enlazar core skills hacia .agents y limpiar copias congeladas
    for core_sk in oraculo planner docu research; do
        if [ -d "$SKILLS_LOCAL_CACHE/$core_sk" ]; then
            [ -d "$TARGET_AGENTS/$core_sk" ] && [ ! -L "$TARGET_AGENTS/$core_sk" ] && rm -rf "$TARGET_AGENTS/$core_sk"
            ln -sfn "$SKILLS_LOCAL_CACHE/$core_sk" "$TARGET_AGENTS/$core_sk"
            rm -rf "$GEMINI_SKILLS/$core_sk" "/home/zerops/.gemini/antigravity-cli/skills/$core_sk" "/home/zerops/.gemini/config/skills/$core_sk" 2>/dev/null || true
        fi
    done

    # Sincronizar bloque CUSTOM de AGENTS.md (preservando ZCP:BEGIN y ZEROPS:REFLOG) y reglas canónicas
    if [ -f "$SSOT_ROOT/AGENTS.md" ]; then
        echo "• Sincronizando sección CUSTOM de AGENTS.md desde SSoT..."
        if [ ! -f "/var/www/AGENTS.md" ]; then
            cp -f "$SSOT_ROOT/AGENTS.md" "/var/www/AGENTS.md" 2>/dev/null || true
        else
            python3 - "$SSOT_ROOT/AGENTS.md" "/var/www/AGENTS.md" << 'EOF_MERGE_AGENTS' || true
import re, sys
src_p, dst_p = sys.argv[1], sys.argv[2]
src = open(src_p, "r", encoding="utf-8").read()
dst = open(dst_p, "r", encoding="utf-8").read()
m_src = re.search(r'<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->', src, flags=re.S)
if not m_src:
    sys.exit(0)
block = m_src.group(0)
if re.search(r'<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->', dst, flags=re.S):
    updated = re.sub(r'<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->', lambda _: block, dst, count=1, flags=re.S)
else:
    updated = dst.rstrip() + "\n\n" + block + "\n"
if updated != dst:
    with open(dst_p, "w", encoding="utf-8") as wf:
        wf.write(updated)
EOF_MERGE_AGENTS
        fi
    fi
    if [ -d "$SSOT_ROOT/.agents/rules" ]; then
        echo "• Sincronizando reglas de gobernanza (.agents/rules -> ~/.gemini/config/rules)..."
        mkdir -p "/var/www/.agents/rules" "/home/zerops/.gemini/config/rules" 2>/dev/null || true
        cp -rn "$SSOT_ROOT/.agents/rules"/* "/var/www/.agents/rules/" 2>/dev/null || true
        [ -f "/var/www/.agents/rules/00-SUPREME-DIRECTIVE.md" ] && ln -sfn "/var/www/.agents/rules/00-SUPREME-DIRECTIVE.md" "/home/zerops/.gemini/config/rules/00-SUPREME-DIRECTIVE.md" 2>/dev/null || true
    fi
    sudo chown -R zerops:zerops /var/www/.agents /home/zerops/.gemini 2>/dev/null || true
    echo "  ✅ Sincronización de Drive finalizada."
else
    echo "  ℹ️ No se detectó directorio de Google Drive en $SKILLS_SRC (Omitiendo)."
fi

# Purgar skills ruidosas/podadas y copias congeladas que sombreen .agents/skills
for noise_sk in jira-epic jira-task gentle-ai-bench gentle-ai-collab-perfect rdd-advisory-transport rdd-defect-workflow migrate-to-shoehorn scaffold-exercises django-drf angular using-superpowers brainstorming writing-plans executing-plans subagent-driven-development dispatching-parallel-agents finishing-a-development-branch using-git-worktrees requesting-code-review receiving-code-review test-driven-development systematic-debugging grill-me grilling grill-with-docs pr github-pr ask-matt claude-handoff handoff wayfinder teach retro loop-me software-factory chief-of-staff implement implement-spec improve-codebase-architecture setup-ts-deep-modules to-questionnaire to-spec to-tickets triage writing-beats writing-fragments writing-shape git-guardrails-claude-code issue-creation issue-root-resolution skill-registry; do
    rm -rf "$TARGET_AGENTS/$noise_sk" "$GEMINI_SKILLS/$noise_sk" "/home/zerops/.gemini/antigravity-cli/skills/$noise_sk" "/home/zerops/.gemini/config/skills/$noise_sk" "/var/www/.claude/skills/$noise_sk" 2>/dev/null || true
done
rm -rf /var/www/.atl 2>/dev/null || true

echo "============================================================"
echo "  Custom Skills Sync & Auto-Discovery Finalizado (v2.0)"
echo "============================================================"
