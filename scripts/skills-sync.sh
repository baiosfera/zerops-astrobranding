#!/usr/bin/env bash
# ==============================================================================
# skills-sync — SSoT Atomic Skills Synchronization Engine (v1.1)
# Zero LLM Tokens | Bounded Execution < 10s | 100% Deterministic
# ==============================================================================
set -euo pipefail

LOCAL_SKILLS="/var/www/.agents/skills"
DRIVE_SKILLS="/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/skills"
SOVEREIGN_REPO="/var/www/zerops-astro-skills"

CHECK_ONLY=false
if [ "${1:-}" = "--check" ]; then
    CHECK_ONLY=true
fi

if [ ! -d "$LOCAL_SKILLS" ]; then
    echo "❌ Error: Directorio local de skills no existe: $LOCAL_SKILLS"
    exit 1
fi

if [ ! -d "$DRIVE_SKILLS" ]; then
    echo "❌ Error: Directorio SSoT de skills en Google Drive no existe: $DRIVE_SKILLS"
    exit 1
fi

echo "============================================================"
echo "  🔄 SKILLS SSoT ATOMIC SYNCHRONIZER (skills-sync v1.1)"
echo "============================================================"

SYNCED=0
DRIFT_COUNT=0

# Determinar universo canónico de skills soberanas desde zerops-astro-skills y Drive SSoT
declare -A SOVEREIGN_SET
if [ -d "$SOVEREIGN_REPO" ]; then
    for s_path in "$SOVEREIGN_REPO"/*; do
        [ -d "$s_path" ] || continue
        s_name="$(basename "$s_path")"
        [ "$s_name" = ".git" ] && continue
        SOVEREIGN_SET["$s_name"]=1
    done
fi

for s_path in "$DRIVE_SKILLS"/*; do
    [ -d "$s_path" ] || continue
    s_name="$(basename "$s_path")"
    SOVEREIGN_SET["$s_name"]=1
done

for skill in "${!SOVEREIGN_SET[@]}"; do
    local_md="$LOCAL_SKILLS/$skill/SKILL.md"
    if [ ! -f "$local_md" ]; then
        if [ -f "$SOVEREIGN_REPO/$skill/SKILL.md" ]; then
            local_md="$SOVEREIGN_REPO/$skill/SKILL.md"
        else
            continue
        fi
    fi

    drive_skill_dir="$DRIVE_SKILLS/$skill"
    drive_md="$drive_skill_dir/SKILL.md"

    if [ ! -f "$drive_md" ] || ! cmp -s "$local_md" "$drive_md"; then
        DRIFT_COUNT=$((DRIFT_COUNT + 1))
        if [ "$CHECK_ONLY" = true ]; then
            echo "  ⚠️ Drift detectado en: $skill"
        else
            mkdir -p "$drive_skill_dir"
            cp -f "$local_md" "$drive_md"
            source_dir="$(dirname "$local_md")"
            for sub in references scripts assets resources; do
                if [ -d "$source_dir/$sub" ]; then
                    mkdir -p "$drive_skill_dir/$sub"
                    cp -rf "$source_dir/$sub"/* "$drive_skill_dir/$sub/" 2>/dev/null || true
                fi
            done
            echo "  ✓ Sincronizada a SSoT: $skill"
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

echo "------------------------------------------------------------"
echo "✅ Sincronización completada: $SYNCED de ${#SOVEREIGN_SET[@]} skill(s) actualizadas en SSoT Drive."

if command -v ssot-parity-check >/dev/null 2>&1; then
    echo "• Ejecutando sensor de atestación física (ssot-parity-check)..."
    ssot-parity-check
fi
