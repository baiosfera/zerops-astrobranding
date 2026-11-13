#!/usr/bin/env bash
# ==============================================================================
# Custom Skills Structural, Syntax & Behavioral Validator (Zero Checklist-Theater)
# Separates:
#   - BEHAVIORALLY_VERIFIED: skills with executable test scripts that ran & exited 0
#   - SYNTAX_ONLY: skills checked only for SKILL.md, links, bash -n, python AST
# ==============================================================================
set -euo pipefail

EXCLUDED_REGEX="^(react-19|zustand-5|tailwind-4|ai-sdk-5|nextjs-15|typescript|zod-4|playwright|puppeteer|crawl4ai|firecrawl|angular|django-drf|spring-boot-3|java-21|electron|elixir-antipatterns|pytest|go-testing|hexagonal-architecture-layers-java|react-native|sdd-.*|rdd-.*|github-pr|work-unit-commits|jira-.*|issue-.*|gentle-ai-.*|systemic-issue-triage|judgment-day|comment-writer|cognitive-doc-design|gga|_shared|branch-pr|chained-pr|skill-creator|skill-registry|skill-improver|hermes-ephemeral-.*|pocock.*|karpathy.*|using-superpowers|brainstorming|dispatching-parallel-agents|executing-plans|finishing-a-development-branch|receiving-code-review|requesting-code-review|subagent-driven-development|systematic-debugging|test-driven-development|using-git-worktrees|verification-before-completion|writing-plans|writing-skills|ask-matt|chief-of-staff|claude-handoff|code-review|codebase-design|diagnosing-bugs|domain-modeling|git-guardrails-claude-code|grill-me|grill-with-docs|grilling|handoff|implement|implement-spec|improve-codebase-architecture|loop-me|migrate-to-shoehorn|pr|prototype|retro|scaffold-exercises|setup-matt-pocock-skills|setup-pre-commit|setup-ts-deep-modules|software-factory|tdd|teach|to-questionnaire|to-spec|to-tickets|triage|wait-what|wayfinder|wizard|writing-beats|writing-for-agents|writing-fragments|writing-shape)$"

QUIET=false
STRICT_BUDGET=false
SKILLS_DIR="/var/www/.agents/skills"
for arg in "$@"; do
    case "$arg" in
        -q|--quiet) QUIET=true ;;
        --strict-budget) STRICT_BUDGET=true ;;
        *) [ -d "$arg" ] && SKILLS_DIR="$arg" ;;
    esac
done

TOTAL=0
BEHAV_PASSED=0
SYNTAX_ONLY=0
FAILED=0
WARN_BUDGET=0
FAILED_SKILLS=()

echo "============================================================"
echo "  SKILLS SUITE AUDIT (Syntax + Links + Real Tests)"
echo "============================================================"

for s in "$SKILLS_DIR"/*; do
    [ -e "$s" ] || continue
    skill_name="$(basename "$s")"
    if echo "$skill_name" | grep -qE "$EXCLUDED_REGEX"; then
        continue
    fi
    if [ -L "$s" ] && [ ! -d "$s" ]; then
        echo "❌ [$skill_name]: Broken symlink -> $(readlink "$s")"
        FAILED=$((FAILED + 1))
        TOTAL=$((TOTAL + 1))
        FAILED_SKILLS+=("$skill_name (broken symlink)")
        continue
    fi
    [ -d "$s" ] || continue

    TOTAL=$((TOTAL + 1))
    skill_path="$(readlink -f "$s")"
    fail_flag=0

    # 1. SKILL.md presence + frontmatter (name + description)
    if [ ! -s "$skill_path/SKILL.md" ]; then
        echo "❌ [$skill_name]: Missing or empty SKILL.md"
        fail_flag=1
    elif ! grep -qE '^name:[[:space:]]*["'\'']?[a-zA-Z0-9_.\-]+' "$skill_path/SKILL.md"; then
        echo "❌ [$skill_name]: Missing frontmatter 'name:' in SKILL.md"
        fail_flag=1
    elif ! grep -qE '^description:[[:space:]]*' "$skill_path/SKILL.md"; then
        echo "❌ [$skill_name]: Missing frontmatter 'description:' in SKILL.md"
        fail_flag=1
    fi

    # 2. Word budget telemetry (<= 480w for sovereign custom skills, excluding imported taste-skill/impeccable)
    if [ "$fail_flag" -eq 0 ] && [ "$skill_name" != "taste-skill" ] && [ "$skill_name" != "impeccable" ]; then
        word_count="$(wc -w < "$skill_path/SKILL.md" | tr -d ' ')"
        if [ "$word_count" -gt 480 ]; then
            WARN_BUDGET=$((WARN_BUDGET + 1))
            if [ "$STRICT_BUDGET" = true ]; then
                echo "❌ [$skill_name]: SKILL.md exceeds 480 words ($word_count words)"
                fail_flag=1
            elif [ "$QUIET" = false ]; then
                echo "⚠️ [$skill_name]: BUDGET_WARN ($word_count > 480 words)"
            fi
        fi
    fi

    # 3. Bash syntax validation
    if [ "$fail_flag" -eq 0 ] && [ -d "$skill_path/scripts" ]; then
        for s_file in "$skill_path"/scripts/*.sh; do
            [ -f "$s_file" ] || continue
            if ! err_out=$(bash -n "$s_file" 2>&1); then
                echo "❌ [$skill_name]: Bash syntax error in $(basename "$s_file"):"
                echo "   $err_out"
                fail_flag=1
                break
            fi
        done
    fi

    # 4. Python AST validation (zero __pycache__ on disk)
    if [ "$fail_flag" -eq 0 ]; then
        while IFS= read -r py_file; do
            [ -f "$py_file" ] || continue
            if ! err_out=$(python3 -B -c "import ast,sys; ast.parse(open(sys.argv[1],'r',encoding='utf-8').read())" "$py_file" 2>&1); then
                echo "❌ [$skill_name]: Python syntax error in $(basename "$py_file"):"
                echo "   $err_out"
                fail_flag=1
                break
            fi
        done < <(find "$skill_path" -maxdepth 3 -name "*.py" 2>/dev/null || true)
    fi

    # 5. Local file:/// link verification
    if [ "$fail_flag" -eq 0 ]; then
        while IFS= read -r link; do
            [ -n "$link" ] || continue
            link_path="${link#file://}"
            if [ ! -e "$link_path" ]; then
                echo "❌ [$skill_name]: Broken file link: $link_path"
                fail_flag=1
                break
            fi
        done < <(grep -oE '\(file:///[^)]+\)' "$skill_path/SKILL.md" | tr -d '()' | sed 's/#.*//' || true)
    fi

    # 6. Executable behavioral tests if present
    ran_tests=0
    if [ "$fail_flag" -eq 0 ]; then
        while IFS= read -r t_file; do
            [ -f "$t_file" ] || continue
            ran_tests=$((ran_tests + 1))
            if [[ "$t_file" == *.py ]]; then
                if ! t_out=$(PYTHONDONTWRITEBYTECODE=1 python3 -B "$t_file" 2>&1); then
                    echo "❌ [$skill_name]: Behavioral test FAILED: $(basename "$t_file")"
                    echo "$t_out" | tail -n 20
                    fail_flag=1
                    break
                fi
            elif [[ "$t_file" == *.sh ]]; then
                if ! t_out=$(bash "$t_file" 2>&1); then
                    echo "❌ [$skill_name]: Behavioral test FAILED: $(basename "$t_file")"
                    echo "$t_out" | tail -n 20
                    fail_flag=1
                    break
                fi
            fi
        done < <(find "$skill_path" -maxdepth 3 -type f \( -name "*test*.py" -o -name "*-test.sh" -o -path "*/tests/*.sh" \) 2>/dev/null | sort)
    fi

    if [ "$fail_flag" -ne 0 ]; then
        FAILED=$((FAILED + 1))
        FAILED_SKILLS+=("$skill_name")
    elif [ "$ran_tests" -gt 0 ]; then
        BEHAV_PASSED=$((BEHAV_PASSED + 1))
        [ "$QUIET" = false ] && echo "✓ [$skill_name]: BEHAVIORALLY_VERIFIED ($ran_tests test script(s) exit 0)"
    else
        SYNTAX_ONLY=$((SYNTAX_ONLY + 1))
        [ "$QUIET" = false ] && echo "• [$skill_name]: SYNTAX_ONLY (no executable test suite)"
    fi
done

echo "============================================================"
echo "  HONEST SKILLS AUDIT SUMMARY"
echo "  • Total Custom Skills Audited:               $TOTAL"
echo "  • BEHAVIORALLY_VERIFIED (tests ran exit 0):  $BEHAV_PASSED"
echo "  • SYNTAX_ONLY (no executable test suite):    $SYNTAX_ONLY"
echo "  • Word Budget Warnings (>480w):              $WARN_BUDGET"
echo "  • Failed:                                    $FAILED"
echo "============================================================"

if [ "$FAILED" -gt 0 ]; then
    echo "💥 Failures: ${FAILED_SKILLS[*]}"
    exit 1
fi

echo "✅ Audit completed with 0 failures ($BEHAV_PASSED behaviorally verified, $SYNTAX_ONLY syntax/structure only)."
exit 0
