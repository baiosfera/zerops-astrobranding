#!/usr/bin/env bash
# ==============================================================================
# plan-archive: Deterministic Plan Archival & Hygiene Utility
# Version: 1.1 (Track A/B Sovereign Lifecycle Governance)
# Zero LLM Tokens | Bounded Execution < 100ms | 100% Deterministic
#
# Usage:
#   plan-archive                     # Scans /var/www/artifacts, moves older versions to archive/
#   plan-archive <plan-path>         # Ensures <plan-path> is active, archives older versions of same stem
#   plan-archive <plan-path> --executed  # Marks plan as executed in archive/ and purges superseded drafts
#   plan-archive --clean             # Removes stale superseded versions across active and archive
# ==============================================================================
set -euo pipefail

ARTIFACTS_DIR="/var/www/artifacts"
ARCHIVE_DIR="${ARTIFACTS_DIR}/archive"

mkdir -p "$ARCHIVE_DIR"

MODE="auto"
TARGET_PLAN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --executed)
            MODE="executed"
            shift
            ;;
        --clean)
            MODE="clean"
            shift
            ;;
        --help|-h)
            echo "Usage: plan-archive [plan_path] [--executed] [--clean]"
            echo "  --executed: Mark target plan as executed in archive/ and purge superseded drafts"
            echo "  --clean:    Purge superseded versions leaving only latest active in root and latest in archive"
            exit 0
            ;;
        *)
            if [ -z "$TARGET_PLAN" ]; then
                TARGET_PLAN="$1"
            fi
            shift
            ;;
    esac
done

# If an explicit plan was provided
if [ -n "$TARGET_PLAN" ] && [ -f "$TARGET_PLAN" ]; then
    FNAME="$(basename "$TARGET_PLAN")"
    STEM=$(echo "$FNAME" | sed -E 's/_v[0-9]+.*$//')
    CURRENT_VER=$(echo "$FNAME" | grep -oE '_v[0-9]+([_\.][0-9]+)*' || echo "")

    if [ "$MODE" == "executed" ]; then
        DEST="${ARCHIVE_DIR}/${FNAME}"
        echo "📦 Archiving executed plan: $FNAME -> archive/$FNAME"
        mv -f "$TARGET_PLAN" "$DEST"
        
        # Purga atómica de versiones previas superseded del mismo stem en archive/
        CURRENT_NUM=$(echo "$CURRENT_VER" | grep -oE '[0-9]+' | head -n1 || echo "0")
        for old_f in "$ARCHIVE_DIR"/${STEM}_v*.md; do
            [ -e "$old_f" ] || continue
            OLD_BNAME="$(basename "$old_f")"
            [ "$OLD_BNAME" == "$FNAME" ] && continue
            OLD_NUM=$(echo "$OLD_BNAME" | grep -oE '_v[0-9]+' | grep -oE '[0-9]+' | head -n1 || echo "0")
            if [ "$OLD_NUM" -lt "$CURRENT_NUM" ]; then
                echo "🧹 Purging superseded intermediate version in archive: $OLD_BNAME"
                rm -f "$old_f"
            fi
        done
        exit 0
    fi

    # Normal mode: move older versions of this stem to archive/
    for f in "$ARTIFACTS_DIR"/${STEM}_v*.md; do
        [ -e "$f" ] || continue
        BNAME="$(basename "$f")"
        if [ "$BNAME" != "$FNAME" ]; then
            echo "📦 Archiving superseded version: $BNAME -> archive/$BNAME"
            mv -f "$f" "${ARCHIVE_DIR}/${BNAME}"
        fi
    done
    echo "✓ Active plan preserved in root: $FNAME"
    exit 0
fi

# Auto / Clean mode: scan all plan files in ARTIFACTS_DIR root
echo "============================================================"
echo "  🧹 Running Deterministic Plan Archival (plan-archive)"
echo "============================================================"

# Collect all stems
declare -A HIGHEST_VER
declare -A HIGHEST_FILE

for f in "$ARTIFACTS_DIR"/*_v[0-9]*.md; do
    [ -e "$f" ] || continue
    BNAME="$(basename "$f")"
    STEM=$(echo "$BNAME" | sed -E 's/_v[0-9]+.*$//')
    VER=$(echo "$BNAME" | grep -oE '_v[0-9]+' | sed 's/_v//')
    
    if [ -z "${HIGHEST_VER[$STEM]:-}" ] || [ "$VER" -gt "${HIGHEST_VER[$STEM]}" ]; then
        HIGHEST_VER[$STEM]="$VER"
        HIGHEST_FILE[$STEM]="$f"
    fi
done

ARCHIVED_COUNT=0
for f in "$ARTIFACTS_DIR"/*_v[0-9]*.md; do
    [ -e "$f" ] || continue
    BNAME="$(basename "$f")"
    STEM=$(echo "$BNAME" | sed -E 's/_v[0-9]+.*$//')
    
    if [ "$f" != "${HIGHEST_FILE[$STEM]}" ]; then
        echo "  → Archiving superseded: $BNAME -> archive/$BNAME"
        mv -f "$f" "${ARCHIVE_DIR}/${BNAME}"
        ARCHIVED_COUNT=$((ARCHIVED_COUNT + 1))
    else
        echo "  ✓ Keeping active: $BNAME"
    fi
done

# Purga de versiones intermedias obsoletas dentro de archive/
declare -A ARCHIVE_HIGHEST_VER
declare -A ARCHIVE_HIGHEST_FILE
for f in "$ARCHIVE_DIR"/*_v[0-9]*.md; do
    [ -e "$f" ] || continue
    BNAME="$(basename "$f")"
    STEM=$(echo "$BNAME" | sed -E 's/_v[0-9]+.*$//')
    VER=$(echo "$BNAME" | grep -oE '_v[0-9]+' | sed 's/_v//')
    if [ -z "${ARCHIVE_HIGHEST_VER[$STEM]:-}" ] || [ "$VER" -gt "${ARCHIVE_HIGHEST_VER[$STEM]}" ]; then
        ARCHIVE_HIGHEST_VER[$STEM]="$VER"
        ARCHIVE_HIGHEST_FILE[$STEM]="$f"
    fi
done

PURGED_ARCHIVE=0
for f in "$ARCHIVE_DIR"/*_v[0-9]*.md; do
    [ -e "$f" ] || continue
    BNAME="$(basename "$f")"
    STEM=$(echo "$BNAME" | sed -E 's/_v[0-9]+.*$//')
    if [ -n "${ARCHIVE_HIGHEST_FILE[$STEM]:-}" ] && [ "$f" != "${ARCHIVE_HIGHEST_FILE[$STEM]}" ]; then
        echo "  🧹 Purging obsolete draft in archive: $BNAME"
        rm -f "$f"
        PURGED_ARCHIVE=$((PURGED_ARCHIVE + 1))
    fi
done

echo "------------------------------------------------------------"
echo "✅ Plan hygiene complete: $ARCHIVED_COUNT superseded plan(s) moved to archive/, $PURGED_ARCHIVE stale draft(s) purged from archive/."
exit 0
