#!/usr/bin/env bash
# ==============================================================================
# SSoT Parity & Integrity Sensor (ssot-parity-check.sh)
# Fast read-only parity audit (<0.5s). Pass --fix to sync, --with-tests for CLI suites.
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
WITH_TESTS=false

for _arg in "$@"; do
    case "$_arg" in
        --fix) AUTO_FIX_MODE=true ;;
        --allow-unpushed) ALLOW_UNPUSHED=true ;;
        --with-tests|--full) WITH_TESTS=true ;;
    esac
done
[ "${AUTO_FIX:-0}" = "1" ] && AUTO_FIX_MODE=true
[ "${SKIP_UNPUSHED:-0}" = "1" ] && ALLOW_UNPUSHED=true

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

compare_agents_md() {
    local src_file="$1"
    local dst_file="$2"
    if [ ! -f "$src_file" ] || [ ! -f "$dst_file" ]; then
        compare_files "AGENTS.md" "$src_file" "$dst_file"
        return
    fi
    local src_custom dst_custom
    src_custom=$(python3 -B -c 'import re,sys; s=open(sys.argv[1]).read(); m=re.search(r"<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->", s, flags=re.S); print(m.group(0).strip() if m else "")' "$src_file")
    dst_custom=$(python3 -B -c 'import re,sys; s=open(sys.argv[1]).read(); m=re.search(r"<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->", s, flags=re.S); print(m.group(0).strip() if m else "")' "$dst_file")
    if [ -n "$src_custom" ] && [ "$src_custom" = "$dst_custom" ]; then
        echo "✓ Parity verified: AGENTS.md (CUSTOM block exact; ZCP:BEGIN preserved)"
    elif [ "$AUTO_FIX_MODE" = true ] && [ -n "$src_custom" ]; then
        python3 -B - "$src_file" "$dst_file" << 'EOF_FIX_AGENTS'
import re, sys
src = open(sys.argv[1], "r", encoding="utf-8").read()
dst = open(sys.argv[2], "r", encoding="utf-8").read()
m = re.search(r"<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->", src, flags=re.S)
if m:
    block = m.group(0)
    if re.search(r"<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->", dst, flags=re.S):
        out = re.sub(r"<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->", lambda _: block, dst, count=1, flags=re.S)
    else:
        out = dst.rstrip() + "\n\n" + block + "\n"
    open(sys.argv[2], "w", encoding="utf-8").write(out)
EOF_FIX_AGENTS
        echo "⚡ Synced (--fix): AGENTS.md CUSTOM block ($src_file -> $dst_file)"
    else
        echo "❌ DRIFT detected in AGENTS.md CUSTOM block:"
        echo "   SSoT:   $src_file"
        echo "   Target: $dst_file"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "--- [1/4] Governance & Harness SSoT Parity ---"
compare_agents_md "$CATALOG_REPO/AGENTS.md" "$LOCAL_BASE/AGENTS.md"
compare_files "00-SUPREME-DIRECTIVE.md (.agents)" "$CATALOG_REPO/.agents/rules/00-SUPREME-DIRECTIVE.md" "$LOCAL_BASE/.agents/rules/00-SUPREME-DIRECTIVE.md"
compare_files "00-SUPREME-DIRECTIVE.md (~/.gemini/config/rules)" "$CATALOG_REPO/.agents/rules/00-SUPREME-DIRECTIVE.md" "${HOME:-/home/zerops}/.gemini/config/rules/00-SUPREME-DIRECTIVE.md"
if [ -f "${HOME:-/home/zerops}/.gemini/config/rules/gentle-ai-02-engram-protocol.md" ]; then
    compare_files "gentle-ai-02-engram-protocol.md (~/.gemini/config/rules)" "$CATALOG_REPO/scripts/templates/gentle-ai-02-engram-protocol.md" "${HOME:-/home/zerops}/.gemini/config/rules/gentle-ai-02-engram-protocol.md"
fi
if [ -e "${HOME:-/home/zerops}/.gemini/antigravity-cli/rules/00-SUPREME-DIRECTIVE.md" ]; then
    if [ "$AUTO_FIX_MODE" = true ]; then
        rm -f "${HOME:-/home/zerops}/.gemini/antigravity-cli/rules/00-SUPREME-DIRECTIVE.md"
        echo "⚡ Removed obsolete rule copy (~/.gemini/antigravity-cli/rules/00-SUPREME-DIRECTIVE.md)"
    else
        echo "❌ Stale rule file exists in dead path: ~/.gemini/antigravity-cli/rules/00-SUPREME-DIRECTIVE.md"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "✓ Dead rule path clean (~/.gemini/antigravity-cli/rules)"
fi

rules_check_out=$(python3 -B - << 'EOF_RULES_CHECK'
import json, os, sys
home = os.path.expanduser("~")
rules_dir = os.path.join(home, ".gemini", "config", "rules")
obsolete = [
    "gentle-ai-03-orchestrator-part1.md",
    "gentle-ai-03-orchestrator-part2.md",
    "gentle-ai-04-agent-routing-part1.md",
    "gentle-ai-04-agent-routing-part2.md",
]
found_obs = [f for f in obsolete if os.path.lexists(os.path.join(rules_dir, f))]
total_bytes = os.path.getsize("/var/www/AGENTS.md") if os.path.exists("/var/www/AGENTS.md") else 0
if os.path.isdir(rules_dir):
    for f in os.listdir(rules_dir):
        fp = os.path.join(rules_dir, f)
        if f.endswith(".md") and os.path.exists(fp):
            total_bytes += os.path.getsize(fp)
errors = []
if found_obs:
    errors.append(f"Obsolete ODD rules present in {rules_dir}: {found_obs}")
if total_bytes > 30000:
    errors.append(f"Rules budget overflow: {total_bytes} bytes > 30000 bytes cap")

cfg_path = os.path.join(home, ".gemini", "config", "config.json")
if os.path.isfile(cfg_path):
    cfg = json.load(open(cfg_path, "r", encoding="utf-8"))
    if cfg.get("plugins", {}).get("gentle-ai-engram", {}).get("enabled", True) is not False:
        errors.append("Duplicate plugin gentle-ai-engram still enabled in ~/.gemini/config/config.json")
mcp_path = os.path.join(home, ".gemini", "config", "mcp_config.json")
if os.path.isfile(mcp_path):
    mcp = json.load(open(mcp_path, "r", encoding="utf-8"))
    engram_srv = mcp.get("mcpServers", {}).get("engram", {})
    if engram_srv.get("command") != "/var/www/.bin/engram-mcp" or engram_srv.get("cwd") != "/var/www":
        errors.append(f"Engram MCP misconfigured in mcp_config.json: command={engram_srv.get('command')} cwd={engram_srv.get('cwd')}")

if errors:
    for e in errors:
        print("ERR:" + e)
    sys.exit(1)
print(f"OK:rules_bytes={total_bytes}")
EOF_RULES_CHECK
) && {
    echo "✓ Rules budget (<30KB) & Engram singleton verified (${rules_check_out#OK:})"
} || {
    echo "$rules_check_out" | sed 's/^ERR:/❌ /'
    ERRORS=$((ERRORS + 1))
}

compare_files "hooks.json" "$CATALOG_REPO/.agents/hooks.json" "$LOCAL_BASE/.agents/hooks.json"
compare_files "hooks/tool-guard.py" "$CATALOG_REPO/scripts/hooks/tool-guard.py" "$LOCAL_BASE/.bin/hooks/tool-guard.py"
compare_files "hooks/test_tool_guard.py" "$CATALOG_REPO/scripts/hooks/test_tool_guard.py" "$LOCAL_BASE/.bin/hooks/test_tool_guard.py"

echo "--- [2/4] CLI Links & Hygiene ---"
LINK_PAIRS=(
    "skills-suite-validate:$CATALOG_REPO/scripts/skills-suite-validate.sh"
    "ssot-parity-check:$CATALOG_REPO/scripts/ssot-parity-check.sh"
    "linear-cli:$CATALOG_REPO/scripts/linear-cli"
    "inject-agent-rule:$CATALOG_REPO/scripts/inject-agent-rule"
    "apotelos:$CATALOG_REPO/scripts/apotelos"
    "brand-play:$CATALOG_REPO/scripts/brand-play"
    "orchesbrand:$CATALOG_REPO/bin/orchesbrand"
    "anti-slop-linter:$CATALOG_REPO/scripts/anti_slop_linter.py"
    "mega-downloader:$CATALOG_REPO/scripts/mega_downloader.py"
    "engram-sync:$CATALOG_REPO/scripts/engram-sync"
    "engram-mcp:$CATALOG_REPO/scripts/engram-mcp"
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

if [ "$WITH_TESTS" = true ]; then
    echo "--- [Optional] Behavioral CLI Self-Tests (--with-tests) ---"
    for cli_cmd in "apotelos test" "brand-play test" "mega-downloader --test"; do
        bin_name="${cli_cmd%% *}"
        if command -v "$bin_name" >/dev/null; then
            if out=$(PYTHONDONTWRITEBYTECODE=1 $cli_cmd 2>&1); then
                echo "✓ $cli_cmd PASSED"
            else
                echo "❌ $cli_cmd FAILED:"
                echo "$out"
                ERRORS=$((ERRORS + 1))
            fi
        fi
    done
fi

echo "--- [3/4] Custom Skills Symlink Isolation & Anti-Shadow ---"
if [ -d "$SKILLS_REPO" ]; then
    dangling=0
    shadow_errs=0
    for sk in "$LOCAL_BASE/.agents/skills"/*; do
        [ -e "$sk" ] || [ -L "$sk" ] || continue
        if [ -L "$sk" ] && [ ! -e "$sk" ]; then
            echo "❌ Broken skill symlink: $sk -> $(readlink "$sk")"
            ERRORS=$((ERRORS + 1))
            dangling=$((dangling + 1))
        fi
    done
    [ "$dangling" -eq 0 ] && echo "✓ Zero broken symlinks in $LOCAL_BASE/.agents/skills"

    for sov in "$SKILLS_REPO"/*/; do
        [ -f "${sov}SKILL.md" ] || continue
        sov_name="$(basename "$sov")"
        if [ ! -L "$LOCAL_BASE/.agents/skills/$sov_name" ]; then
            echo "❌ Missing sovereign symlink in .agents/skills: $sov_name"
            ERRORS=$((ERRORS + 1))
            shadow_errs=$((shadow_errs + 1))
        fi
        for sec_dir in "${HOME:-/home/zerops}/.gemini/antigravity-cli/skills" "${HOME:-/home/zerops}/.gemini/config/skills" "$LOCAL_BASE/.claude/skills"; do
            if [ -e "$sec_dir/$sov_name" ]; then
                echo "❌ Frozen shadow copy of sovereign skill in $sec_dir/$sov_name"
                ERRORS=$((ERRORS + 1))
                shadow_errs=$((shadow_errs + 1))
            fi
        done
    done
    for noise_sk in jira-epic jira-task gentle-ai-bench gentle-ai-collab-perfect rdd-advisory-transport rdd-defect-workflow migrate-to-shoehorn scaffold-exercises django-drf angular using-superpowers brainstorming writing-plans executing-plans subagent-driven-development dispatching-parallel-agents finishing-a-development-branch using-git-worktrees requesting-code-review receiving-code-review test-driven-development systematic-debugging grill-me grilling grill-with-docs pr github-pr ask-matt claude-handoff handoff wayfinder teach retro loop-me software-factory chief-of-staff implement implement-spec improve-codebase-architecture setup-ts-deep-modules to-questionnaire to-spec to-tickets triage writing-beats writing-fragments writing-shape git-guardrails-claude-code issue-creation issue-root-resolution skill-registry; do
        for check_dir in "$LOCAL_BASE/.agents/skills" "${HOME:-/home/zerops}/.gemini/antigravity-cli/skills" "${HOME:-/home/zerops}/.gemini/config/skills" "$LOCAL_BASE/.claude/skills" "$LOCAL_BASE/localstorage/skills"; do
            if [ -e "$check_dir/$noise_sk" ] || [ -L "$check_dir/$noise_sk" ]; then
                echo "❌ Pruned external skill still present: $check_dir/$noise_sk"
                ERRORS=$((ERRORS + 1))
                shadow_errs=$((shadow_errs + 1))
            fi
        done
    done
    [ "$shadow_errs" -eq 0 ] && echo "✓ Zero shadowed sovereign skills & zero pruned noise across all skill paths"

    if [ -d "$LOCAL_BASE/localstorage/skills" ]; then
        if [ -L "$LOCAL_BASE/localstorage/skills/oraculo" ]; then
            echo "❌ /var/www/localstorage/skills/oraculo is an unresolved symlink (Hermes requires rsync -aL)"
            ERRORS=$((ERRORS + 1))
        elif [ ! -f "$LOCAL_BASE/localstorage/skills/oraculo/SKILL.md" ]; then
            echo "❌ /var/www/localstorage/skills missing live sovereign skills"
            ERRORS=$((ERRORS + 1))
        else
            echo "✓ /var/www/localstorage/skills dereferenced & live for Hermes"
        fi
    fi
fi

echo "--- [4/4] Git Cleanliness & Remote Parity ---"
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
