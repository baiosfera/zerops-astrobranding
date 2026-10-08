#!/usr/bin/env bash
# ==============================================================================
# skills-sync — SSoT Atomic Skills Synchronization Engine (v1.2)
# Zero LLM Tokens | Bounded Execution < 10s | 100% Deterministic | rsync --delete
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
echo "  🔄 SKILLS SSoT ATOMIC SYNCHRONIZER (skills-sync v1.2)"
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
    source_dir="$LOCAL_SKILLS/$skill"
    if [ ! -d "$source_dir" ]; then
        if [ -d "$SOVEREIGN_REPO/$skill" ]; then
            source_dir="$SOVEREIGN_REPO/$skill"
        else
            continue
        fi
    fi

    drive_skill_dir="$DRIVE_SKILLS/$skill"

    # Deep tree check using rsync --dry-run
    # Si rsync detecta algún cambio (archivos nuevos, modificados, o eliminados), stdout no estará vacío (descontando headers)
    DRIFT_OUTPUT=$(rsync -avnc --delete "$source_dir/" "$drive_skill_dir/" | grep -vE "^building file list|^created directory|^sent|^total size|^$")

    if [ -n "$DRIFT_OUTPUT" ]; then
        DRIFT_COUNT=$((DRIFT_COUNT + 1))
        if [ "$CHECK_ONLY" = true ]; then
            echo "  ⚠️ Drift detectado en: $skill"
        else
            mkdir -p "$drive_skill_dir"
            # Sincronización exacta, borrando zombies en el destino
            rsync -a --delete "$source_dir/" "$drive_skill_dir/"
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
