#!/usr/bin/env bash
# ==============================================================================
# skills-sync — SSoT Atomic Skills Synchronization Engine (v1.2)
# Zero LLM Tokens | Bounded Execution < 10s | 100% Deterministic | rsync --delete
# ==============================================================================
set -euo pipefail

LOCAL_SKILLS="/var/www/.agents/skills"
PROJ_KEY="$(echo "${ENGRAM_PROJECT:-${PROJECT_NAME:-}}" | tr '[:upper:]' '[:lower:]')"
DRIVE_SKILLS="${PROJ_KEY:+/var/www/baiosfera/0ZEROPS-AGY/$PROJ_KEY/.agents/skills}"
SOVEREIGN_REPO="/var/www/zerops-astro-skills"

CHECK_ONLY=false
if [ "${1:-}" = "--check" ]; then
    CHECK_ONLY=true
fi

if [ ! -d "$LOCAL_SKILLS" ]; then
    echo "❌ Error: Directorio local de skills no existe: $LOCAL_SKILLS"
    exit 1
fi

HAS_DRIVE=false
if [ -n "$DRIVE_SKILLS" ] && [ -d "$DRIVE_SKILLS" ]; then
    HAS_DRIVE=true
else
    echo "ℹ️ Drive SSoT no configurado/encontrado ($DRIVE_SKILLS); verificando paridad git <-> local."
fi

echo "============================================================"
echo "  🔄 SKILLS SSoT ATOMIC SYNCHRONIZER (skills-sync v1.2)"
echo "============================================================"

SYNCED=0
DRIFT_COUNT=0

# Anti-Pollution Shield: Upstream / framework skills remain purely in runtime/git, not in SSoT custom skills
EXCLUDED_REGEX="^(react-19|zustand-5|tailwind-4|ai-sdk-5|nextjs-15|typescript|zod-4|playwright|puppeteer|crawl4ai|firecrawl|angular|django-drf|spring-boot-3|java-21|electron|elixir-antipatterns|pytest|go-testing|hexagonal-architecture-layers-java|react-native|sdd-.*|rdd-.*|github-pr|work-unit-commits|jira-.*|issue-.*|gentle-ai-.*|systemic-issue-triage|judgment-day|comment-writer|cognitive-doc-design|gga|_shared|branch-pr|chained-pr|skill-creator|skill-registry|skill-improver|hermes-ephemeral-.*|pocock.*|karpathy.*|using-superpowers|brainstorming|dispatching-parallel-agents|executing-plans|finishing-a-development-branch|receiving-code-review|requesting-code-review|subagent-driven-development|systematic-debugging|test-driven-development|using-git-worktrees|verification-before-completion|writing-plans|writing-skills|ask-matt|chief-of-staff|claude-handoff|code-review|codebase-design|diagnosing-bugs|domain-modeling|git-guardrails-claude-code|grill-me|grill-with-docs|grilling|handoff|implement|implement-spec|improve-codebase-architecture|loop-me|migrate-to-shoehorn|pr|prototype|retro|scaffold-exercises|setup-matt-pocock-skills|setup-pre-commit|setup-ts-deep-modules|software-factory|tdd|teach|to-questionnaire|to-spec|to-tickets|triage|wait-what|wayfinder|wizard|writing-beats|writing-for-agents|writing-fragments|writing-shape)$"

# Determinar universo canónico de skills soberanas desde zerops-astro-skills y Drive SSoT
declare -A SOVEREIGN_SET
if [ -d "$SOVEREIGN_REPO" ]; then
    for s_path in "$SOVEREIGN_REPO"/*; do
        [ -d "$s_path" ] || continue
        s_name="$(basename "$s_path")"
        [ "$s_name" = ".git" ] && continue
        if echo "$s_name" | grep -qE "$EXCLUDED_REGEX"; then
            continue
        fi
        SOVEREIGN_SET["$s_name"]=1
    done
fi

if [ "$HAS_DRIVE" = true ]; then
    for s_path in "$DRIVE_SKILLS"/*; do
        [ -d "$s_path" ] || continue
        s_name="$(basename "$s_path")"
        if echo "$s_name" | grep -qE "$EXCLUDED_REGEX"; then
            continue
        fi
        SOVEREIGN_SET["$s_name"]=1
    done
fi

for skill in "${!SOVEREIGN_SET[@]}"; do
    source_dir="$LOCAL_SKILLS/$skill"
    if [ ! -d "$source_dir" ]; then
        if [ -d "$SOVEREIGN_REPO/$skill" ]; then
            source_dir="$SOVEREIGN_REPO/$skill"
        else
            continue
        fi
    fi

    if [ "$HAS_DRIVE" = true ]; then
        target_dir="$DRIVE_SKILLS/$skill"
    else
        target_dir="$SOVEREIGN_REPO/$skill"
    fi

    if [ "$(readlink -f "$source_dir")" = "$(readlink -f "$target_dir")" ]; then
        continue
    fi

    DRIFT_OUTPUT=$(rsync -avnc --delete "$source_dir/" "$target_dir/" 2>/dev/null | grep -vE "^building file list|^created directory|^sent|^total size|^$" || true)

    if [ -n "$DRIFT_OUTPUT" ]; then
        DRIFT_COUNT=$((DRIFT_COUNT + 1))
        if [ "$CHECK_ONLY" = true ]; then
            echo "  ⚠️ Drift detectado en: $skill"
        else
            if [ "$HAS_DRIVE" = true ]; then
                mkdir -p "$target_dir"
                rsync -a --delete "$source_dir/" "$target_dir/"
            fi
            if [ -d "$SOVEREIGN_REPO" ]; then
                mkdir -p "$SOVEREIGN_REPO/$skill"
                rsync -a --delete --exclude=".git" "$source_dir/" "$SOVEREIGN_REPO/$skill/"
            fi
            echo "  ✓ Sincronizada SSoT: $skill"
            SYNCED=$((SYNCED + 1))
        fi
    fi
done

if [ "$CHECK_ONLY" = true ]; then
    if [ "$DRIFT_COUNT" -eq 0 ]; then
        echo "✅ Paridad absoluta: 0 drifts detectados en las ${#SOVEREIGN_SET[@]} skills soberanas."
        exit 0
    else
        echo "❌ Se detectaron $DRIFT_COUNT skill(s) con drift. Ejecutá 'skills-sync' para resolver."
        exit 1
    fi
fi

# Clean secondary shadow copies of sovereign skills, purge Group E, sync localstorage & refresh index
for sov_sk in "${!SOVEREIGN_SET[@]}"; do
    rm -rf "$HOME/.gemini/antigravity-cli/skills/$sov_sk" "$HOME/.gemini/config/skills/$sov_sk" "/var/www/.claude/skills/$sov_sk" 2>/dev/null || true
done
for noise_sk in jira-epic jira-task gentle-ai-bench gentle-ai-collab-perfect rdd-advisory-transport rdd-defect-workflow migrate-to-shoehorn scaffold-exercises django-drf angular using-superpowers brainstorming writing-plans executing-plans subagent-driven-development dispatching-parallel-agents finishing-a-development-branch using-git-worktrees requesting-code-review receiving-code-review test-driven-development systematic-debugging grill-me grilling grill-with-docs pr github-pr ask-matt claude-handoff handoff wayfinder teach retro loop-me software-factory chief-of-staff implement implement-spec improve-codebase-architecture setup-ts-deep-modules to-questionnaire to-spec to-tickets triage writing-beats writing-fragments writing-shape git-guardrails-claude-code issue-creation issue-root-resolution skill-registry; do
    rm -rf "$LOCAL_SKILLS/$noise_sk" "$HOME/.gemini/antigravity-cli/skills/$noise_sk" "$HOME/.gemini/config/skills/$noise_sk" "/var/www/.claude/skills/$noise_sk" "/var/www/localstorage/skills/$noise_sk" 2>/dev/null || true
done
if [ -d "/var/www/localstorage" ]; then
    mkdir -p "/var/www/localstorage/skills"
    rsync -aL --delete --exclude="__pycache__" --exclude="*.pyc" --exclude="*.bak" --exclude=".git" --exclude="AGENTS.md" "$LOCAL_SKILLS/" "/var/www/localstorage/skills/" 2>/dev/null || true
fi
rm -rf /var/www/.atl 2>/dev/null || true

echo "------------------------------------------------------------"
echo "✅ Sincronización completada: $SYNCED de ${#SOVEREIGN_SET[@]} skill(s) actualizadas en SSoT Drive."

if command -v ssot-parity-check >/dev/null 2>&1; then
    echo "• Ejecutando sensor de atestación física (ssot-parity-check)..."
    ssot-parity-check
fi
