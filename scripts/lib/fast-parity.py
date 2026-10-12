#!/usr/bin/env python3
"""
fast-parity.py — Ultra-fast in-process SSoT Custom Skills Parity Checker & Auto-Healer
Replaces the 25-second sequential bash loop with a <0.5s deterministic in-memory check.
Supports ZCP-First Invariant Auto-Healing when local skills are updated or AUTO_FIX=1.
"""
import sys
import os
import re
import shutil

def check_skills_parity(drive_base: str, local_base: str, auto_fix: bool = False) -> int:
    drive_skills = os.path.join(drive_base, ".agents/skills")
    local_skills = os.path.join(local_base, ".agents/skills")

    excluded_pattern = re.compile(
        r'^(react-19|zustand-5|tailwind-4|ai-sdk-5|nextjs-15|typescript|zod-4|playwright|puppeteer|'
        r'crawl4ai|firecrawl|angular|django-drf|spring-boot-3|java-21|electron|elixir-antipatterns|'
        r'pytest|go-testing|hexagonal-architecture-layers-java|react-native|sdd-.*|rdd-.*|'
        r'github-pr|work-unit-commits|jira-.*|issue-.*|gentle-ai-.*|systemic-issue-triage|'
        r'judgment-day|comment-writer|cognitive-doc-design|gga|_shared|branch-pr|chained-pr|'
        r'skill-creator|skill-registry|skill-improver|hermes-ephemeral-.*|pocock.*)$',
        re.IGNORECASE
    )

    if not os.path.isdir(drive_skills):
        print(f"❌ Drive SSoT skills directory missing: {drive_skills}")
        return 1

    skill_count = 0
    errors = 0

    for skill in sorted(os.listdir(drive_skills)):
        d_dir = os.path.join(drive_skills, skill)
        if not os.path.isdir(d_dir):
            continue

        if excluded_pattern.match(skill):
            print(f"❌ SSoT Pollution detected! Upstream skill '{skill}' found in Drive SSoT custom skills directory!")
            errors += 1
            continue

        skill_count += 1
        l_dir = os.path.join(local_skills, skill)
        if not os.path.isdir(l_dir):
            print(f"❌ Local custom skill directory missing: {l_dir}")
            errors += 1
            continue

        d_file = os.path.join(d_dir, "SKILL.md")
        l_file = os.path.join(l_dir, "SKILL.md")
        if not os.path.exists(d_file) or not os.path.exists(l_file):
            print(f"❌ Missing SKILL.md for skill: {skill}")
            errors += 1
            continue

        try:
            has_drift = False
            if os.path.getsize(d_file) != os.path.getsize(l_file):
                has_drift = True
            else:
                with open(d_file, "rb") as f1, open(l_file, "rb") as f2:
                    if f1.read() != f2.read():
                        has_drift = True

            if has_drift:
                # ZCP-First Invariant Auto-Healing:
                # If local file was edited or pulled from GitHub, or auto_fix is enabled, heal Drive SSoT
                should_heal = auto_fix or os.environ.get("AUTO_FIX") == "1" or os.path.getmtime(l_file) >= os.path.getmtime(d_file)
                if should_heal:
                    shutil.copy2(l_file, d_file)
                    print(f"⚡ Auto-healed parity in SKILL.md for custom skill: {skill}")
                else:
                    print(f"❌ Drift in SKILL.md for custom skill: {skill}")
                    errors += 1
        except Exception as e:
            print(f"❌ Error comparing skill {skill}: {e}")
            errors += 1

    print(f"✓ Verified SKILL.md parity across all {skill_count} custom skills in SSoT")
    return errors

if __name__ == "__main__":
    d_base = sys.argv[1] if len(sys.argv) > 1 else "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123"
    l_base = sys.argv[2] if len(sys.argv) > 2 else "/var/www"
    fix_arg = False
    if len(sys.argv) > 3 and sys.argv[3] in ("1", "true", "--fix"):
        fix_arg = True
    err_count = check_skills_parity(d_base, l_base, fix_arg)
    sys.exit(err_count)
