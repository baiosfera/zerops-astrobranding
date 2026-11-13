#!/usr/bin/env bash
# ==============================================================================
# SSoT Parity & Integrity Sensor (ssot-parity-check.sh)
# Read-only by default (ZERO silent rsync masking). Pass --fix to sync explicitly.
# Zero hardcoded 0zcp-123 or tenant leaks.
# ==============================================================================
set -euo pipefail

LOCAL_BASE="/var/www"
CATALOG_REPO="$LOCAL_BASE/zerops-astrobranding"
SKILLS_REPO="$LOCAL_BASE/zerops-astro-skills"

ERRORS=0
WARNINGS=0
AUTO_FIX_MODE=false
ALLOW_UNPUSHED=false

for _arg in "$@"; do
    case "$_arg" in
        --fix) AUTO_FIX_MODE=true ;;
        --allow-unpushed) ALLOW_UNPUSHED=true ;;
    esac
done
[ "${AUTO_FIX:-0}" = "1" ] && AUTO_FIX_MODE=true
[ "${SKIP_UNPUSHED:-0}" = "1" ] && ALLOW_UNPUSHED=true

# Resolve optional Drive project archive dynamically (never hardcode 0zcp-123)
PROJECT_KEY="$(echo "${ENGRAM_PROJECT:-${PROJECT_NAME:-}}" | tr '[:upper:]' '[:lower:]')"
DRIVE_BASE="${DRIVE_SSOT_DIR:-}"
if [ -z "$DRIVE_BASE" ] && [ -n "$PROJECT_KEY" ] && [ -d "$LOCAL_BASE/baiosfera/0ZEROPS-AGY/$PROJECT_KEY" ]; then
    DRIVE_BASE="$LOCAL_BASE/baiosfera/0ZEROPS-AGY/$PROJECT_KEY"
fi

echo "============================================================"
echo "  SSOT PARITY & INTEGRITY AUDIT (Read-Only=$([ "$AUTO_FIX_MODE" = true ] && echo false || echo true))"
echo "============================================================"

compare_files() {
    local label="$1"
    local src_file="$2"
    local dst_file="$3"

    if [ ! -f "$src_file" ]; then
        echo "❌ Source missing ($label): $src_file"
        ERRORS=$((ERRORS + 1))
        return
    fi
    if [ ! -f "$dst_file" ]; then
        if [ "$AUTO_FIX_MODE" = true ]; then
            mkdir -p "$(dirname "$dst_file")"
            cp -f "$src_file" "$dst_file"
            echo "⚡ Created missing mirror ($label): $dst_file"
            return
        fi
        echo "❌ Mirror missing ($label): $dst_file"
        ERRORS=$((ERRORS + 1))
        return
    fi
    if cmp -s "$src_file" "$dst_file"; then
        echo "✓ Parity verified: $label"
    elif [ "$AUTO_FIX_MODE" = true ]; then
        cp -f "$src_file" "$dst_file"
        echo "⚡ Synced (--fix): $label ($src_file -> $dst_file)"
    else
        echo "❌ DRIFT detected in $label:"
        echo "   SSoT:   $src_file"
        echo "   Target: $dst_file"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "--- [1/5] Governance & Harness SSoT Parity ---"
compare_files "AGENTS.md" "$CATALOG_REPO/AGENTS.md" "$LOCAL_BASE/AGENTS.md"
compare_files "00-SUPREME-DIRECTIVE.md (.agents)" "$CATALOG_REPO/.agents/rules/00-SUPREME-DIRECTIVE.md" "$LOCAL_BASE/.agents/rules/00-SUPREME-DIRECTIVE.md"
compare_files "00-SUPREME-DIRECTIVE.md (~/.gemini)" "$CATALOG_REPO/.agents/rules/00-SUPREME-DIRECTIVE.md" "${HOME:-/home/zerops}/.gemini/antigravity-cli/rules/00-SUPREME-DIRECTIVE.md"
compare_files "hooks.json" "$CATALOG_REPO/.agents/hooks.json" "$LOCAL_BASE/.agents/hooks.json"
compare_files "hooks/tool-guard.py" "$CATALOG_REPO/scripts/hooks/tool-guard.py" "$LOCAL_BASE/.bin/hooks/tool-guard.py"
compare_files "hooks/test_tool_guard.py" "$CATALOG_REPO/scripts/hooks/test_tool_guard.py" "$LOCAL_BASE/.bin/hooks/test_tool_guard.py"

echo "--- [2/5] CLI Links & Python AST / Hygiene ---"
LINK_PAIRS=(
    "skills-suite-validate:$CATALOG_REPO/scripts/skills-suite-validate.sh"
    "ssot-parity-check:$CATALOG_REPO/scripts/ssot-parity-check.sh"
    "linear-cli:$CATALOG_REPO/scripts/linear-cli"
    "apotelos:$CATALOG_REPO/scripts/apotelos"
    "brand-play:$CATALOG_REPO/scripts/brand-play"
    "orchesbrand:$CATALOG_REPO/bin/orchesbrand"
    "anti-slop-linter:$CATALOG_REPO/scripts/anti_slop_linter.py"
    "engram-sync:$CATALOG_REPO/scripts/engram-sync"
    "zcp-sync:$CATALOG_REPO/scripts/zcp-sync"
    "skills-sync:$CATALOG_REPO/scripts/skills-sync.sh"
)
for pair in "${LINK_PAIRS[@]}"; do
    name="${pair%%:*}"
    target="${pair#*:}"
    bin_link="$LOCAL_BASE/.bin/$name"
    local_link="${HOME:-/home/zerops}/.local/bin/$name"
    if [ ! -f "$target" ]; then
        echo "❌ Missing SSoT script: $target"
        ERRORS=$((ERRORS + 1))
        continue
    fi
    if [ ! -L "$bin_link" ] || [ "$(readlink -f "$bin_link")" != "$(readlink -f "$target")" ]; then
        if [ "$AUTO_FIX_MODE" = true ]; then
            chmod +x "$target" 2>/dev/null || true
            ln -sfn "$target" "$bin_link"
            ln -sfn "$bin_link" "$local_link" 2>/dev/null || true
            echo "⚡ Linked (--fix): $bin_link -> $target"
        else
            echo "❌ Link drift: $bin_link does not point to $target"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "✓ CLI symlink exact: $name"
    fi
done

if [ -d "$CATALOG_REPO/scripts/__pycache__" ]; then
    echo "❌ Residual __pycache__ in $CATALOG_REPO/scripts"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ Zero __pycache__ in scripts"
fi

echo "--- [3/5] Behavioral CLI Self-Tests ---"
if command -v apotelos >/dev/null; then
    if out=$(PYTHONDONTWRITEBYTECODE=1 apotelos test 2>&1); then
        echo "✓ apotelos test PASSED"
    else
        echo "❌ apotelos test FAILED:"
        echo "$out"
        ERRORS=$((ERRORS + 1))
    fi
fi
if command -v brand-play >/dev/null; then
    if out=$(PYTHONDONTWRITEBYTECODE=1 brand-play test 2>&1); then
        echo "✓ brand-play test PASSED"
    else
        echo "❌ brand-play test FAILED:"
        echo "$out"
        ERRORS=$((ERRORS + 1))
    fi
fi

echo "--- [4/5] Custom Skills Symlink Isolation ---"
if [ -d "$SKILLS_REPO" ]; then
    dangling=0
    for sk in "$LOCAL_BASE/.agents/skills"/*; do
        [ -e "$sk" ] || [ -L "$sk" ] || continue
        if [ -L "$sk" ] && [ ! -e "$sk" ]; then
            echo "❌ Broken skill symlink: $sk -> $(readlink "$sk")"
            ERRORS=$((ERRORS + 1))
            dangling=$((dangling + 1))
        fi
    done
    [ "$dangling" -eq 0 ] && echo "✓ Zero broken symlinks in $LOCAL_BASE/.agents/skills"
fi

echo "--- [5/5] Git Cleanliness & Remote Parity ---"
check_git_repo() {
    local repo_dir="$1"
    local repo_name
    repo_name="$(basename "$repo_dir")"
    [ -d "$repo_dir/.git" ] || return 0
    local dirty
    dirty=$(git -C "$repo_dir" status --porcelain 2>&1 || true)
    if [ -n "$dirty" ]; then
        echo "❌ Uncommitted changes in $repo_name:"
        echo "$dirty" | sed 's/^/   /'
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ Working tree clean: $repo_name"
    fi
    local unpushed
    unpushed=$(git -C "$repo_dir" cherry -v origin/main 2>&1 || true)
    if [ -n "$unpushed" ]; then
        if [ "$ALLOW_UNPUSHED" = true ]; then
            echo "ℹ️ Unpushed commits in $repo_name (allowed by flag)"
            WARNINGS=$((WARNINGS + 1))
        else
            echo "❌ Unpushed commits in $repo_name:"
            echo "$unpushed" | sed 's/^/   /'
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "✓ origin/main parity verified: $repo_name"
    fi
}

check_git_repo "$SKILLS_REPO"
check_git_repo "$CATALOG_REPO"

if [ -n "$DRIVE_BASE" ]; then
    echo "ℹ️ Project Drive archive detected ($PROJECT_KEY): $DRIVE_BASE"
else
    echo "• Project Drive archive: N/A (not configured for active project)"
fi

echo "------------------------------------------------------------"
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ SSoT Parity Check PASSED (0 errors, $WARNINGS warning(s))."
    exit 0
else
    echo "❌ SSoT Parity Check FAILED with $ERRORS error(s)."
    exit 1
fi
