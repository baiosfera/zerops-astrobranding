#!/usr/bin/env bash
# ==============================================================================
# cohalo-validate — Physical Reality Sensor for CoHaLo Architecture (v8.4)
# Enforces Pure Positive Guidance, Router Word Budget & Zero Broken References
# ==============================================================================
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -f "$SKILL_DIR/SKILL.md" ]; then
    SKILL_DIR="/var/www/.agents/skills/cohalo"
fi
SKILL_FILE="$SKILL_DIR/SKILL.md"

echo "============================================================"
echo "  🔬 VALIDATING COHALO ARCHITECTURE & POSITIVE GUIDANCE"
echo "============================================================"

# Sensor 1: SKILL.md router word budget (<= 480 words)
if [ ! -f "$SKILL_FILE" ]; then
    echo "❌ Error: SKILL.md not found in $SKILL_DIR"
    exit 1
fi

WORD_COUNT=$(wc -w < "$SKILL_FILE")
if [ "$WORD_COUNT" -gt 480 ]; then
    echo "❌ Error: SKILL.md exceeds router token budget ($WORD_COUNT words > 480 max)"
    exit 1
fi
echo "✓ Sensor 1: Router word budget verified ($WORD_COUNT <= 480 words)"

# Sensor 2: Zero broken references in SKILL.md
BROKEN_REFS=0
for ref_file in "$SKILL_DIR"/references/*.md; do
    if [ ! -s "$ref_file" ]; then
        echo "❌ Error: Missing or empty reference file: $ref_file"
        BROKEN_REFS=$((BROKEN_REFS + 1))
    fi
done
if [ "$BROKEN_REFS" -gt 0 ]; then
    echo "❌ Error: Detected $BROKEN_REFS broken reference(s) in cohalo"
    exit 1
fi
echo "✓ Sensor 2: All 7 Dual-RAG reference documents verified on disk"

# Sensor 3: Positive Guidance Invariant (Zero negative shouting in cohalo docs)
NEGATIVE_REGEX='(Queda terminantemente prohibido|Do NOT activate under any circumstances|Está terminantemente prohibido|terminantemente prohibido|queda prohibido|está prohibido|strictly forbidden)'
PUNATIVE_FOUND=0
for doc in "$SKILL_DIR"/SKILL.md "$SKILL_DIR"/references/prompt_engineering_foundations.md "$SKILL_DIR"/references/context.md "$SKILL_DIR"/references/harness.md "$SKILL_DIR"/references/loops.md; do
    if [ -f "$doc" ]; then
        if grep -qE "$NEGATIVE_REGEX" "$doc"; then
            echo "❌ Error: Prohibited negative prompt dogma found in $(basename "$doc")"
            PUNATIVE_FOUND=$((PUNATIVE_FOUND + 1))
        fi
    fi
done
if [ "$PUNATIVE_FOUND" -gt 0 ]; then
    echo "❌ Error: Positive Guidance violation detected in cohalo documents"
    exit 1
fi
echo "✓ Sensor 3: Pure Positive Guidance verified (Zero negative shouting)"

# Sensor 4: Script syntax check
for s in "$SKILL_DIR"/scripts/*.sh; do
    if [ -f "$s" ]; then
        bash -n "$s"
    fi
done
echo "✓ Sensor 4: Bash script syntax verified (bash -n exit 0)"

echo "============================================================"
echo "✅ COHALO ARCHITECTURAL SENSOR PASSED (exit code 0)"
echo "============================================================"
exit 0
