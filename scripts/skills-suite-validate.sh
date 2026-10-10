#!/usr/bin/env bash
# ==============================================================================
# Gentle AI Custom Skills Suite Validation Runner (Standard v3.2 - Universal Sensor Fallback)
# SSoT-First Custom Skills Scope & Hermes Upstream Invariant
# Zero LLM Tokens | Bounded Execution | 100% Deterministic
# ==============================================================================
set -euo pipefail

EXCLUDED_REGEX="^(react-19|zustand-5|tailwind-4|ai-sdk-5|nextjs-15|typescript|zod-4|playwright|puppeteer|crawl4ai|firecrawl|angular|django-drf|spring-boot-3|java-21|electron|elixir-antipatterns|pytest|go-testing|hexagonal-architecture-layers-java|react-native|sdd-.*|rdd-.*|github-pr|work-unit-commits|jira-.*|issue-.*|gentle-ai-.*|systemic-issue-triage|judgment-day|comment-writer|cognitive-doc-design|gga|_shared|branch-pr|chained-pr|skill-creator|skill-registry|skill-improver|hermes-ephemeral-.*)$"

SKILLS_DIR="${1:-/var/www/.agents/skills}"
SSOT_DIR="/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/skills"
TOTAL=0
PASSED=0
FAILED=0
FAILED_SKILLS=()

echo "============================================================"
echo "  🚀 RUNNING CUSTOM SKILLS SUITE VALIDATION (Standard v3.2)"
echo "============================================================"

# SSoT-First: Si el repositorio soberano en Drive existe, iterar estrictamente
# sobre el conjunto canónico de custom skills, ignorando cualquier artefacto upstream.
TARGET_SKILLS=()
for s in "$SKILLS_DIR"/*; do
    if [ -d "$s" ]; then
        s_name="$(basename "$s")"
        if ! echo "$s_name" | grep -qE "$EXCLUDED_REGEX"; then
            TARGET_SKILLS+=("$s_name")
        fi
    fi
done

for skill_name in "${TARGET_SKILLS[@]}"; do
    skill_path="$SKILLS_DIR/$skill_name"
    TOTAL=$((TOTAL + 1))
    val_script="$skill_path/scripts/${skill_name}-validate.sh"

    if [ ! -d "$skill_path" ]; then
        echo "❌ [$skill_name]: Missing local skill directory ($skill_path)"
        FAILED=$((FAILED + 1))
        FAILED_SKILLS+=("$skill_name (missing dir)")
        continue
    fi

    if [ -f "$val_script" ]; then
        # Validación física de sintaxis de los scripts internos de la skill
        SYNTAX_FAIL=0
        for s_file in "$skill_path"/scripts/*.sh; do
            if [ -f "$s_file" ]; then
                if ! err_out=$(bash -n "$s_file" 2>&1); then
                    echo "❌ [$skill_name]: Syntax error in script $(basename "$s_file"):"
                    echo "   $err_out"
                    SYNTAX_FAIL=1
                fi
            fi
        done

        if [ "$SYNTAX_FAIL" -eq 1 ]; then
            FAILED=$((FAILED + 1))
            FAILED_SKILLS+=("$skill_name (syntax error)")
            continue
        fi

        # Ejecutar sensor capturando diagnóstico real (Anti-Silenciamiento)
        VAL_OUTPUT=$(timeout 10s bash "$val_script" 2>&1) && VAL_EXIT=0 || VAL_EXIT=$?

        if [ "$VAL_EXIT" -eq 0 ]; then
            echo "✓ [$skill_name]: PASSED"
            PASSED=$((PASSED + 1))
        else
            echo "❌ [$skill_name]: FAILED (Exit Code: $VAL_EXIT)"
            echo "$VAL_OUTPUT" | sed 's/^/     /'
            FAILED=$((FAILED + 1))
            FAILED_SKILLS+=("$skill_name")
        fi
    else
        # FALLBACK: SENSOR UNIVERSAL DETERMINISTA PARA SKILLS UPSTREAM / COMUNITARIAS
        UNI_FAIL=0
        # 1. Validar existencia y contenido de SKILL.md
        if [ ! -f "$skill_path/SKILL.md" ] || [ ! -s "$skill_path/SKILL.md" ]; then
            echo "❌ [$skill_name]: Universal Sensor Failed - Missing or empty SKILL.md"
            UNI_FAIL=1
        fi

        # 2. Validar frontmatter mínimo (name:)
        if [ "$UNI_FAIL" -eq 0 ] && ! grep -qE '^name:[[:space:]]*["'\'']?[a-zA-Z0-9_\.\-]+' "$skill_path/SKILL.md"; then
            echo "❌ [$skill_name]: Universal Sensor Failed - Invalid or missing frontmatter name in SKILL.md"
            UNI_FAIL=1
        fi

        # 3. Validar sintaxis de cualquier script de bash existente en la skill
        if [ "$UNI_FAIL" -eq 0 ] && [ -d "$skill_path/scripts" ]; then
            for s_file in "$skill_path"/scripts/*.sh; do
                if [ -f "$s_file" ]; then
                    if ! err_out=$(bash -n "$s_file" 2>&1); then
                        echo "❌ [$skill_name]: Syntax error in script $(basename "$s_file"):"
                        echo "   $err_out"
                        UNI_FAIL=1
                    fi
                fi
            done
        fi

        if [ "$UNI_FAIL" -eq 0 ]; then
            echo "✓ [$skill_name]: PASSED (Universal Sensor)"
            PASSED=$((PASSED + 1))
        else
            FAILED=$((FAILED + 1))
            FAILED_SKILLS+=("$skill_name (universal sensor fail)")
        fi
    fi
done

echo "============================================================"
echo "  📊 VALIDATION SUITE SUMMARY"
echo "  • Total Custom Skills Tested: $TOTAL"
echo "  • Passed (Exit 0):            $PASSED"
echo "  • Failed:                     $FAILED"
echo "============================================================"

if [ "$FAILED" -eq 0 ]; then
    echo "🎉 100% of custom skills passed physical validation successfully!"
    exit 0
else
    echo "💥 Validation failures detected in: ${FAILED_SKILLS[*]}"
    exit 1
fi
