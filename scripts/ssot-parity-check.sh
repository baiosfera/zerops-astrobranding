#!/usr/bin/env bash
# ==============================================================================
# SSoT Parity & Anti-Drift Physical Validation Sensor (ssot-parity-check.sh)
# Version: 1.4 (Standard CoHaLo Sensor Standard)
# Zero LLM Tokens | Bounded Execution < 200ms | 100% Deterministic
# ==============================================================================
set -euo pipefail

LOCAL_BASE="/var/www"
DRIVE_BASE="/var/www/baiosfera/0ZEROPS-AGY/0zcp-123"

ERRORS=0

echo "============================================================"
echo "  🔍 RUNNING SSOT PARITY & ANTI-DRIFT SENSOR (v1.4)"
echo "============================================================"

# Helper: Compare two files byte-by-byte
compare_files() {
    local label="$1"
    local local_file="$2"
    local drive_file="$3"

    if [ ! -f "$local_file" ]; then
        echo "❌ Local file missing: $local_file"
        ERRORS=$((ERRORS + 1))
        return
    fi

    if [ ! -f "$drive_file" ]; then
        echo "❌ Drive file missing: $drive_file"
        ERRORS=$((ERRORS + 1))
        return
    fi

    if cmp -s "$local_file" "$drive_file"; then
        echo "✓ Parity verified: $label"
    else
        echo "❌ Parity DRIFT detected in: $label"
        echo "   Local: $local_file ($(stat -c%s "$local_file" 2>/dev/null || stat -f%z "$local_file") bytes)"
        echo "   Drive: $drive_file ($(stat -c%s "$drive_file" 2>/dev/null || stat -f%z "$drive_file") bytes)"
        if [ "$local_file" -nt "$drive_file" ]; then
            echo "   👉 DETECTADO: El archivo local en ZCP es MÁS RECIENTE (editado en caliente)."
            echo "      Acción requerida: Reflejar cambios hacia Drive SSoT:"
            echo "      cp -f \"$local_file\" \"$drive_file\""
            echo "      ⚠️ NUNCA sobreescribas el ZCP con el archivo viejo de Drive!"
        elif [ "$drive_file" -nt "$local_file" ]; then
            echo "   👉 DETECTADO: El archivo en Drive SSoT es MÁS RECIENTE (modificado externamente)."
            echo "      Acción requerida: Sincronizar desde Drive al ZCP:"
            echo "      cp -f \"$drive_file\" \"$local_file\""
        fi
        ERRORS=$((ERRORS + 1))
    fi
}

# 1. Rules & Directives Parity
echo "--- [1/4] Checking Governance Rules & Encyclopedias ---"
compare_files "AGENTS.md" "$LOCAL_BASE/AGENTS.md" "$DRIVE_BASE/AGENTS.md"
compare_files "00-SUPREME-DIRECTIVE.md" "$LOCAL_BASE/.agents/rules/00-SUPREME-DIRECTIVE.md" "$DRIVE_BASE/.agents/rules/00-SUPREME-DIRECTIVE.md"
compare_files "supreme_directive_encyclopedia.md" "$LOCAL_BASE/.agents/references/supreme_directive_encyclopedia.md" "$DRIVE_BASE/.agents/references/supreme_directive_encyclopedia.md"

if [ -f "$LOCAL_BASE/.agents/references/gentle_governance_encyclopedia.md" ] && [ -f "$DRIVE_BASE/.agents/references/gentle_governance_encyclopedia.md" ]; then
    compare_files "gentle_governance_encyclopedia.md" "$LOCAL_BASE/.agents/references/gentle_governance_encyclopedia.md" "$DRIVE_BASE/.agents/references/gentle_governance_encyclopedia.md"
fi

compare_files "skill-registry.md" "$LOCAL_BASE/.atl/skill-registry.md" "$DRIVE_BASE/.atl/skill-registry.md"

if [ -f "$LOCAL_BASE/.agents/references/astro_suites_encyclopedia.md" ] && [ -f "$DRIVE_BASE/.agents/references/astro_suites_encyclopedia.md" ]; then
    compare_files "astro_suites_encyclopedia.md" "$LOCAL_BASE/.agents/references/astro_suites_encyclopedia.md" "$DRIVE_BASE/.agents/references/astro_suites_encyclopedia.md"
fi

# 2. Core Scripts Integrity in Drive
echo "--- [2/4] Checking Core Deployment Scripts in Drive SSoT ---"
CORE_SCRIPTS=(
    "unisetup.sh"
    "setup-gentle.sh"
    "setup-drive.sh"
    "setup-astrokey.sh"
    "setup-zcp.sh"
    "drive-keys.sh"
    "astrobranding-check.sh"
    "skills-suite-validate.sh"
    "ssot-parity-check.sh"
    "engram-sync"
)

for script in "${CORE_SCRIPTS[@]}"; do
    script_path="$DRIVE_BASE/scripts/$script"
    if [ ! -f "$script_path" ]; then
        echo "❌ Missing script in Drive SSoT: $script_path"
        ERRORS=$((ERRORS + 1))
    elif [ ! -s "$script_path" ]; then
        echo "❌ Empty script in Drive SSoT: $script_path"
        ERRORS=$((ERRORS + 1))
    else
        # Syntax check
        if bash -n "$script_path" >/dev/null 2>&1; then
            echo "✓ Script valid: $script"
        else
            echo "❌ Bash syntax error in Drive script: $script_path"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

if [ -f "$LOCAL_BASE/zerops-astrobranding/scripts/engram-sync" ]; then
    compare_files "engram-sync" "$LOCAL_BASE/zerops-astrobranding/scripts/engram-sync" "$DRIVE_BASE/scripts/engram-sync"
fi

# 2.1 Python Tooling Syntax (In-Memory AST, 0 bytes en disco) & Bytecode Hygiene
echo "--- Checking Python Tooling Syntax & Bytecode Hygiene (Zero Disk Writes) ---"
PYTHON_SCRIPTS=(
    "mcv_downloader.py"
    "nlm_tutor.py"
)
for py_script in "${PYTHON_SCRIPTS[@]}"; do
    py_path="$DRIVE_BASE/scripts/$py_script"
    if [ ! -f "$py_path" ]; then
        echo "❌ Missing Python script in Drive SSoT: $py_path"
        ERRORS=$((ERRORS + 1))
    elif python3 -c "import ast; ast.parse(open('$py_path', 'r', encoding='utf-8').read())" >/dev/null 2>&1; then
        echo "✓ Python AST syntax valid (in-memory): $py_script"
    else
        echo "❌ Python syntax error in: $py_path"
        ERRORS=$((ERRORS + 1))
    fi
done

if [ -f "/var/www/baiosfera/CURSOS/MCV/mcv_downloader.py" ]; then
    compare_files "mcv_downloader.py runtime parity" "/var/www/baiosfera/CURSOS/MCV/mcv_downloader.py" "$DRIVE_BASE/scripts/mcv_downloader.py"
fi

if [ -d "$DRIVE_BASE/scripts/__pycache__" ]; then
    echo "❌ Residual __pycache__ directory detected in Drive SSoT scripts!"
    ERRORS=$((ERRORS + 1))
else
    echo "✓ Clean-room hygiene verified: no __pycache__ in scripts directory"
fi

# 3. CLI Symlinks Health
echo "--- [3/4] Checking /usr/local/bin and .bin Symlinks ---"
SYMLINKS=(
    "skills-suite-validate"
    "ssot-parity-check"
    "astrobranding-check"
    "zcp-sync"
)

for symlink in "${SYMLINKS[@]}"; do
    bin_path="/usr/local/bin/$symlink"
    local_bin="/var/www/.bin/$symlink"
    if [ ! -x "$bin_path" ] && [ ! -x "$local_bin" ]; then
        echo "❌ Missing or non-executable binary/symlink in PATH/.bin: $symlink"
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ CLI available & executable in PATH/.bin: $symlink"
    fi
done

# 3.1 Lifecycle Hooks & Gatekeeper Parity
echo "--- Checking Lifecycle Hooks & Tool-Guard Parity ---"
compare_files "hooks/tool-guard.py" "$LOCAL_BASE/.bin/hooks/tool-guard.py" "$DRIVE_BASE/scripts/hooks/tool-guard.py"
compare_files "hooks.json" "$LOCAL_BASE/.agents/hooks.json" "$DRIVE_BASE/.agents/hooks.json"

# 4. Bootstrap Architecture & Zero Secret Leak Parity
echo "--- [4/5] Checking Bootstrap & Zero Secret Leak Parity ---"
if [ -f "$LOCAL_BASE/zerops-astrobranding/iniciar.sh" ]; then
    compare_files "iniciar.sh" "$LOCAL_BASE/zerops-astrobranding/iniciar.sh" "$DRIVE_BASE/scripts/iniciar.sh"
fi
if [ -f "$LOCAL_BASE/zerops-astrobranding/scripts/gdrive.sh" ]; then
    compare_files "scripts/gdrive.sh" "$LOCAL_BASE/zerops-astrobranding/scripts/gdrive.sh" "$DRIVE_BASE/scripts/gdrive.sh"
fi

# Check raw secrets in gdrive.sh
if grep -Eq "(GOCSPX-|ya29\.|1//056)" "$DRIVE_BASE/scripts/gdrive.sh" 2>/dev/null; then
    echo "❌ Secret leak detected in gdrive.sh! Plaintext credentials must not be stored in scripts."
    ERRORS=$((ERRORS + 1))
else
    echo "✓ Zero plaintext secrets verified in gdrive.sh (Drive SSoT)"
fi

# 5. Custom Skills Parity (SSoT Scope)
echo "--- [5/5] Checking Custom Skills Parity across all Sovereign Skills ---"
FAST_PARITY_SCRIPT="$LOCAL_BASE/zerops-astrobranding/scripts/lib/fast-parity.py"
if [ -f "$FAST_PARITY_SCRIPT" ]; then
    if ! python3 "$FAST_PARITY_SCRIPT" "$DRIVE_BASE" "$LOCAL_BASE"; then
        ERRORS=$((ERRORS + 1))
    fi
else
    SKILL_COUNT=0
    EXCLUDED_REGEX="^(react-19|zustand-5|tailwind-4|ai-sdk-5|nextjs-15|typescript|zod-4|playwright|puppeteer|crawl4ai|firecrawl|angular|django-drf|spring-boot-3|java-21|electron|elixir-antipatterns|pytest|go-testing|hexagonal-architecture-layers-java|react-native|sdd-.*|rdd-.*|github-pr|work-unit-commits|jira-.*|issue-.*|gentle-ai-.*|systemic-issue-triage|judgment-day|comment-writer|cognitive-doc-design|gga|_shared|branch-pr|chained-pr|skill-creator|skill-registry|skill-improver|hermes-ephemeral-.*|pocock.*)$"

    for drive_skill_dir in "$DRIVE_BASE/.agents/skills"/*; do
        if [ ! -d "$drive_skill_dir" ]; then
            continue
        fi
        skill="$(basename "$drive_skill_dir")"

        # Anti-Pollution Shield: Ensure no upstream/framework skills were mistakenly copied into SSoT
        if echo "$skill" | grep -qE "$EXCLUDED_REGEX"; then
            echo "❌ SSoT Pollution detected! Upstream skill '$skill' found in Drive SSoT custom skills directory!"
            ERRORS=$((ERRORS + 1))
            continue
        fi

        SKILL_COUNT=$((SKILL_COUNT + 1))
        local_skill_dir="$LOCAL_BASE/.agents/skills/$skill"

        if [ ! -d "$local_skill_dir" ]; then
            echo "❌ Local custom skill directory missing: $local_skill_dir"
            ERRORS=$((ERRORS + 1))
            continue
        fi

        if [ ! -f "$local_skill_dir/SKILL.md" ] || [ ! -f "$drive_skill_dir/SKILL.md" ]; then
            echo "❌ Missing SKILL.md for skill: $skill"
            ERRORS=$((ERRORS + 1))
            continue
        fi

        if ! cmp -s "$local_skill_dir/SKILL.md" "$drive_skill_dir/SKILL.md"; then
            echo "❌ Drift in SKILL.md for custom skill: $skill"
            ERRORS=$((ERRORS + 1))
        fi
    done
    echo "✓ Verified SKILL.md parity across all $SKILL_COUNT custom skills in SSoT"
fi

# Deep tree parity for core orchestration skills
CORE_SKILLS=("oraculo" "planner" "docu" "research")
for skill in "${CORE_SKILLS[@]}"; do
    local_skill_dir="$LOCAL_BASE/.agents/skills/$skill"
    drive_skill_dir="$DRIVE_BASE/.agents/skills/$skill"
    DIFF_OUT=$(diff -rq --exclude="__pycache__" --exclude="*.pyc" --exclude="*.bak" "$local_skill_dir" "$drive_skill_dir" 2>&1 || true)
    if [ -n "$DIFF_OUT" ]; then
        echo "❌ Drift or missing files detected in core skill $skill:"
        echo "$DIFF_OUT" | sed 's/^/   /'
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ Deep tree parity verified for core skill: $skill"
    fi
done

echo "--- [6/6] Checking Git Cold-Boot Upstream Repositories (iniciar.sh-First Invariant) ---"

check_git_sovereign_repo() {
    local repo_dir="$1"
    local repo_name="$(basename "$repo_dir")"
    if [ ! -d "$repo_dir/.git" ]; then
        return
    fi
    local uncommitted
    uncommitted=$(git -C "$repo_dir" status --porcelain 2>/dev/null || true)
    if [ -n "$uncommitted" ]; then
        echo "❌ Uncommitted changes detected in sovereign repo: $repo_name"
        echo "$uncommitted" | sed 's/^/   /'
        ERRORS=$((ERRORS + 1))
    else
        echo "✓ Working tree clean in sovereign repo: $repo_name"
    fi

    local unpushed
    unpushed=$(git -C "$repo_dir" cherry -v origin/main 2>/dev/null || true)
    if [ -n "$unpushed" ]; then
        if [ "${SKIP_UNPUSHED:-0}" = "1" ] || [ "${1:-}" = "--allow-unpushed" ] || [ "${ALLOW_UNPUSHED:-0}" = "1" ]; then
            echo "ℹ️ Commits pendientes por empujar (permitido en contexto pre-push): $repo_name"
        else
            echo "❌ Unpushed commits detected in sovereign repo: $repo_name (iniciar.sh cold boot will drift!)"
            echo "$unpushed" | sed 's/^/   /'
            echo "   👉 Acción requerida: cd $repo_dir && git push origin main"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "✓ Git push parity verified (up to date with origin/main): $repo_name"
    fi
}

check_git_sovereign_repo "/var/www/zerops-astro-skills"
check_git_sovereign_repo "$LOCAL_BASE/zerops-astrobranding"

for skill in "${CORE_SKILLS[@]}"; do
    local_skill_dir="$LOCAL_BASE/.agents/skills/$skill"
    repo_skill_dir="/var/www/zerops-astro-skills/$skill"
    if [ -d "$repo_skill_dir" ]; then
        DIFF_REPO=$(diff -rq --exclude="__pycache__" --exclude="*.pyc" --exclude="*.bak" "$local_skill_dir" "$repo_skill_dir" 2>&1 || true)
        if [ -n "$DIFF_REPO" ]; then
            echo "❌ Drift detected between local skill and git repo (zerops-astro-skills/$skill):"
            echo "$DIFF_REPO" | sed 's/^/   /'
            ERRORS=$((ERRORS + 1))
        else
            echo "✓ Git repo tree parity verified: zerops-astro-skills/$skill"
        fi
    fi
done

echo "------------------------------------------------------------"
if [ "$ERRORS" -eq 0 ]; then
    if command -v engram-sync >/dev/null 2>&1; then
        echo "• Sincronizando memoria Engram hacia Google Drive SSoT..."
        engram-sync --push >/dev/null 2>&1 || true
    fi
    echo "✅ SSoT Parity Check PASSED (exit code 0). Zero drift detected."
    exit 0
else
    echo "❌ SSoT Parity Check FAILED with $ERRORS discrepancy/discrepancies."
    exit 1
fi
