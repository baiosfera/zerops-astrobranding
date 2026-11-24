#!/usr/bin/env bash
# ==============================================================================
# Custom Skills Fast Structural & Behavioral Validator (v2.0)
# Default mode (<0.4s): single in-process Python pass + batched bash -n
# Pass --with-tests (or --full) to execute per-skill *test*.py / *-test.sh suites.
# ==============================================================================
set -euo pipefail

QUIET=false
STRICT_BUDGET=false
WITH_TESTS=false
SKILLS_DIR="/var/www/.agents/skills"

for arg in "$@"; do
    case "$arg" in
        -q|--quiet) QUIET=true ;;
        --strict-budget) STRICT_BUDGET=true ;;
        --with-tests|--full) WITH_TESTS=true ;;
        *) [ -d "$arg" ] && SKILLS_DIR="$arg" ;;
    esac
done

exec python3 -B - "$SKILLS_DIR" "$QUIET" "$STRICT_BUDGET" "$WITH_TESTS" << 'EOF'
import ast
import os
import re
import subprocess
import sys

skills_dir = sys.argv[1]
quiet = sys.argv[2] == "true"
strict_budget = sys.argv[3] == "true"
with_tests = sys.argv[4] == "true"

EXCLUDED_RE = re.compile(
    r"^(react-19|zustand-5|tailwind-4|ai-sdk-5|nextjs-15|typescript|zod-4|playwright|puppeteer|"
    r"crawl4ai|firecrawl|angular|django-drf|spring-boot-3|java-21|electron|elixir-antipatterns|"
    r"pytest|go-testing|hexagonal-architecture-layers-java|react-native|sdd-.*|rdd-.*|"
    r"github-pr|work-unit-commits|jira-.*|issue-.*|gentle-ai-.*|systemic-issue-triage|"
    r"judgment-day|comment-writer|cognitive-doc-design|gga|_shared|branch-pr|chained-pr|"
    r"skill-creator|skill-registry|skill-improver|hermes-ephemeral-.*|pocock.*|karpathy.*|"
    r"using-superpowers|brainstorming|dispatching-parallel-agents|executing-plans|"
    r"finishing-a-development-branch|receiving-code-review|requesting-code-review|"
    r"subagent-driven-development|systematic-debugging|test-driven-development|"
    r"using-git-worktrees|verification-before-completion|writing-plans|writing-skills|"
    r"ask-matt|chief-of-staff|claude-handoff|code-review|codebase-design|diagnosing-bugs|"
    r"domain-modeling|git-guardrails-claude-code|grill-me|grill-with-docs|grilling|handoff|"
    r"implement|implement-spec|improve-codebase-architecture|loop-me|migrate-to-shoehorn|"
    r"pr|prototype|retro|scaffold-exercises|setup-matt-pocock-skills|setup-pre-commit|"
    r"setup-ts-deep-modules|software-factory|tdd|teach|to-questionnaire|to-spec|to-tickets|"
    r"triage|wait-what|wayfinder|wizard|writing-beats|writing-for-agents|writing-fragments|"
    r"writing-shape)$"
)

NAME_RE = re.compile(r'^name:\s*["\']?[a-zA-Z0-9_.\-]+', re.MULTILINE)
DESC_RE = re.compile(r"^description:\s*", re.MULTILINE)
LINK_RE = re.compile(r"\(file:///([^)#]+)")

total = 0
struct_ok = 0
behav_ok = 0
failed = 0
warn_budget = 0
failed_skills = []
sh_files = []  # (skill_name, path)
test_files = []  # (skill_name, path)

print("============================================================")
print("  SKILLS SUITE AUDIT (Fast In-Process + Scoped Tests)")
print("============================================================")

for name in sorted(os.listdir(skills_dir)):
    if EXCLUDED_RE.match(name):
        continue
    entry = os.path.join(skills_dir, name)
    if os.path.islink(entry) and not os.path.isdir(entry):
        print(f"❌ [{name}]: Broken symlink -> {os.readlink(entry)}")
        total += 1
        failed += 1
        failed_skills.append(f"{name} (broken symlink)")
        continue
    if not os.path.isdir(entry):
        continue

    total += 1
    skill_path = os.path.realpath(entry)
    skill_md = os.path.join(skill_path, "SKILL.md")
    fail_flag = False

    if not os.path.isfile(skill_md) or os.path.getsize(skill_md) == 0:
        print(f"❌ [{name}]: Missing or empty SKILL.md")
        fail_flag = True
    else:
        content = open(skill_md, "r", encoding="utf-8", errors="replace").read()
        if not NAME_RE.search(content):
            print(f"❌ [{name}]: Missing frontmatter 'name:' in SKILL.md")
            fail_flag = True
        elif not DESC_RE.search(content):
            print(f"❌ [{name}]: Missing frontmatter 'description:' in SKILL.md")
            fail_flag = True

        if not fail_flag and name not in ("taste-skill", "impeccable"):
            wc = len(content.split())
            if wc > 480:
                warn_budget += 1
                if strict_budget:
                    print(f"❌ [{name}]: SKILL.md exceeds 480 words ({wc} words)")
                    fail_flag = True
                elif not quiet:
                    print(f"⚠️ [{name}]: BUDGET_WARN ({wc} > 480 words)")

        if not fail_flag:
            for link_path in LINK_RE.findall(content):
                abs_link = "/" + link_path.lstrip("/")
                if not os.path.exists(abs_link):
                    print(f"❌ [{name}]: Broken file link: {abs_link}")
                    fail_flag = True
                    break

    if not fail_flag:
        for root, dirs, files in os.walk(skill_path):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "node_modules")]
            rel_depth = os.path.relpath(root, skill_path)
            if rel_depth != "." and rel_depth.count(os.sep) >= 2:
                continue
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                if fname.endswith(".py"):
                    try:
                        ast.parse(open(fpath, "r", encoding="utf-8").read(), filename=fpath)
                    except SyntaxError as e:
                        print(f"❌ [{name}]: Python syntax error in {fname}:{e.lineno}: {e.msg}")
                        fail_flag = True
                        break
                elif fname.endswith(".sh") and os.path.basename(root) == "scripts":
                    sh_files.append((name, fpath))

                if with_tests and (
                    (fname.endswith(".py") and "test" in fname)
                    or (fname.endswith("-test.sh"))
                    or (fname.endswith(".sh") and os.path.basename(root) == "tests")
                ):
                    test_files.append((name, fpath))
            if fail_flag:
                break

    if fail_flag:
        failed += 1
        failed_skills.append(name)

# Single batched bash -n check for all skill scripts/*.sh
failed_set = set(failed_skills)
if sh_files:
    bash_check = subprocess.run(
        ["bash", "-c", 'for f in "$@"; do bash -n "$f" || { echo "FAIL:$f"; exit 1; }; done', "_"] + [p for _, p in sh_files],
        capture_output=True,
        text=True,
    )
    if bash_check.returncode != 0:
        bad_line = bash_check.stdout.strip().splitlines()[-1] if bash_check.stdout.strip() else ""
        bad_path = bad_line.replace("FAIL:", "")
        bad_skill = next((sn for sn, sp in sh_files if sp == bad_path), "unknown")
        print(f"❌ [{bad_skill}]: Bash syntax error in {os.path.basename(bad_path)}:\n{bash_check.stderr.strip()}")
        if bad_skill not in failed_set:
            failed += 1
            failed_skills.append(bad_skill)
            failed_set.add(bad_skill)

skills_with_tests = set()
if with_tests and test_files:
    for sn, tf in sorted(test_files):
        if sn in failed_set:
            continue
        cmd = ["python3", "-B", tf] if tf.endswith(".py") else ["bash", tf]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"❌ [{sn}]: Behavioral test FAILED: {os.path.basename(tf)}")
            print((res.stdout + res.stderr)[-1000:])
            failed += 1
            failed_skills.append(sn)
            failed_set.add(sn)
        else:
            skills_with_tests.add(sn)

behav_ok = len(skills_with_tests)
struct_ok = total - failed - behav_ok

print("============================================================")
print("  SKILLS AUDIT SUMMARY")
print(f"  • Total Custom Skills Audited:               {total}")
print(f"  • STRUCTURALLY_VERIFIED (AST/syntax/links):  {struct_ok}")
print(f"  • BEHAVIORALLY_VERIFIED (tests exit 0):      {behav_ok}")
print(f"  • Word Budget Warnings (>480w):              {warn_budget}")
print(f"  • Failed:                                    {failed}")
print("============================================================")

if failed > 0:
    print("💥 Failures:", ", ".join(failed_skills))
    sys.exit(1)

print(f"✅ Audit completed with 0 failures ({behav_ok} behaviorally verified, {struct_ok} structurally verified).")
sys.exit(0)
EOF
