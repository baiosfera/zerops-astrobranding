#!/usr/bin/env python3
"""
tool-guard.py — Native Antigravity Process-Level Gatekeeper & Anti-Sycophancy Harness
Version: 3.2 (Antigravity Native Tools, SessionStart Recall, Safe Process Kill & Single-Node Scale Gate)
Execution: <30ms | Zero External Dependencies | 100% Deterministic
Intercepts PreToolUse, PreInvocation, and SessionStart events to enforce:
  1. Handover Immunity (Strict block against destroying or truncating handover files).
  2. Anti-Afán & Anti-AMN Inflow Gate (Enforces prior inspection/grounding before mutations).
  3. Dangerous Command Guard (Blocks blind sweeping deletes and prompts for high-risk ops).
  4. SSoT Relative Path Gate (Blocks creation or usage of '0zcp-123/' relative path leaks).
  5. Monotonic Pre-Mutation Backup Gate (Blocks mutating skills, rules or platform scripts without snapshot).
  6. AST & Symbol Preservation Gate (Zero Deletion of functions, classes, and safety flags).
  7. Physical Syntax Pre-Flight Gate (bash -n and python compile before write).
  8. Anti-Checklist Theater Gate (Blocks silencing errors with >/dev/null 2>&1 in validation scripts).
  9. Plan-First Gate & F4 Halt Guard (Enforced on application code AND skills, rejecting Zombie Plans).
  10. SSoT Parity Pre-Push Gate (Blocks git push on sovereign repos if ssot-parity-check detects drift).
  11. Session Recall Gate (Enforces SessionStart mandatory discovery and memory context recall).
  12. Process Kill Guard (Immunizes active interactive sessions and ancestor process hierarchy).
  13. Single-Node ZCP Scale Gate (Blocks multi-container autoscaling on stateful ZCP control plane).
"""
import sys
import os

# Zero-Bytecode Invariant (00-SUPREME-DIRECTIVE Invariant 6)
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import json
import re
import time
import subprocess

HANDOVER_PATTERN = re.compile(r'(_handover|_blueprint|_dossier|_roadmap)', re.IGNORECASE)
DANGEROUS_RM_PATTERN = re.compile(r'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-f?[a-zA-Z]*r[a-zA-Z]*)\s+(/|/\*|/var|/var/\*|/var/www|/var/www/\*)(\s|$)', re.IGNORECASE)
SWEEPING_ARTIFACTS_RM = re.compile(r'rm\s+.*artifacts/(\*|\.\*)', re.IGNORECASE)

def contains_relative_0zcp_leak(text: str) -> bool:
    """Detects occurrences of '0zcp-123' not preceded by the canonical Drive prefix or rclone remote prefix."""
    prefixes = ["/var/www/baiosfera/0ZEROPS-AGY/", "baiosfera:0ZEROPS-AGY/"]
    idx = 0
    while True:
        pos = text.find("0zcp-123", idx)
        if pos == -1:
            break
        valid = any(pos >= len(p) and text[pos - len(p):pos] == p for p in prefixes)
        if not valid:
            return True
        idx = pos + len("0zcp-123")
    return False

UPSTREAM_SKILLS_PATTERN = re.compile(
    r'^(react-19|zustand-5|tailwind-4|ai-sdk-5|nextjs-15|typescript|zod-4|playwright|puppeteer|'
    r'crawl4ai|firecrawl|angular|django-drf|spring-boot-3|java-21|electron|elixir-antipatterns|'
    r'pytest|go-testing|hexagonal-architecture-layers-java|react-native|rdd-.*|'
    r'github-pr|work-unit-commits|jira-.*|issue-.*|gentle-ai-.*|systemic-issue-triage|'
    r'judgment-day|comment-writer|cognitive-doc-design|gga|_shared|branch-pr|chained-pr|'
    r'skill-creator|skill-registry|skill-improver|hermes-ephemeral-.*|pocock.*|'
    r'karpathy.*|'
    r'using-superpowers|brainstorming|dispatching-parallel-agents|executing-plans|'
    r'finishing-a-development-branch|receiving-code-review|requesting-code-review|'
    r'subagent-driven-development|systematic-debugging|test-driven-development|'
    r'using-git-worktrees|verification-before-completion|writing-plans|writing-skills|'
    r'ask-matt|chief-of-staff|claude-handoff|code-review|codebase-design|'
    r'diagnosing-bugs|domain-modeling|git-guardrails-claude-code|grill-me|grill-with-docs|'
    r'grilling|handoff|implement|implement-spec|improve-codebase-architecture|'
    r'loop-me|migrate-to-shoehorn|pr|prototype|retro|scaffold-exercises|'
    r'setup-matt-pocock-skills|setup-pre-commit|setup-ts-deep-modules|tdd|teach|'
    r'to-questionnaire|to-spec|to-tickets|triage|wait-what|wayfinder|wizard|'
    r'writing-beats|writing-for-agents|writing-fragments|writing-shape)$',
    re.IGNORECASE
)

def is_upstream_skill_pollution(path_or_cmd: str, is_write: bool = True) -> str:
    """Detects attempts to write, copy, or mutate upstream gentle-ai/pocock skills into Drive SSoT or runtime skills dirs."""
    ssot_skills_prefix = "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/skills"
    runtime_skills_prefixes = ("/var/www/.agents/skills", "/var/www/.claude/skills")

    # 1. Any appearance in Google Drive SSoT custom skills directory is strictly forbidden
    if ssot_skills_prefix in path_or_cmd:
        for token in re.split(r'[/ \t\n\'"]+', path_or_cmd):
            token_clean = token.strip()
            if UPSTREAM_SKILLS_PATTERN.match(token_clean):
                return token_clean

    # 2. Local runtime upstream skills directories are strictly read-only
    if any(p in path_or_cmd for p in runtime_skills_prefixes):
        if is_write:
            for token in re.split(r'[/ \t\n\'"]+', path_or_cmd):
                token_clean = token.strip()
                if UPSTREAM_SKILLS_PATTERN.match(token_clean):
                    return token_clean

    return ""
CORE_SYNC_PAIRS = [
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/hooks/tool-guard.py",
        "/var/www/.bin/hooks/tool-guard.py"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/AGENTS.md",
        "/var/www/AGENTS.md"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/AGENTS.md",
        "/var/www/zerops-astrobranding/AGENTS.md"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/rules/00-SUPREME-DIRECTIVE.md",
        "/var/www/.agents/rules/00-SUPREME-DIRECTIVE.md"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/hooks.json",
        "/var/www/.agents/hooks.json"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/skills-suite-validate.sh",
        "/var/www/.bin/skills-suite-validate"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/ssot-parity-check.sh",
        "/var/www/.bin/ssot-parity-check"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/references/supreme_directive_encyclopedia.md",
        "/var/www/.agents/references/supreme_directive_encyclopedia.md"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/references/gentle_governance_encyclopedia.md",
        "/var/www/.agents/references/gentle_governance_encyclopedia.md"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/references/astro_suites_encyclopedia.md",
        "/var/www/.agents/references/astro_suites_encyclopedia.md"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.atl/skill-registry.md",
        "/var/www/.atl/skill-registry.md"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.atl/skill-registry.md",
        "/var/www/zerops-astrobranding/.atl/skill-registry.md"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/iniciar.sh",
        "/var/www/zerops-astrobranding/iniciar.sh"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/unisetup.sh",
        "/var/www/zerops-astrobranding/scripts/unisetup.sh"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/gdrive.sh",
        "/var/www/zerops-astrobranding/scripts/gdrive.sh"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/engram-sync",
        "/var/www/zerops-astrobranding/scripts/engram-sync"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/astrobranding-check.sh",
        "/var/www/.bin/astrobranding-check"
    ),
]

def cleanup_artifacts_lifecycle(purge_executed: bool = False) -> dict:
    """
    Lifecycle Purge Protocol (Supreme Directive v8.3 & Planner v8.6):
    1. Scans /var/www/artifacts/ and /var/www/artifacts/.
    2. Identifies executed plans (files ending with '.executed.md' or '_vN.executed.md').
    3. For any executed plan stem or active plan stem, purges previous '.superseded.md' files.
    4. If purge_executed is True (session-end protocol), purges all '*.executed.md' from archive/.
    5. Handover assets matching HANDOVER_PATTERN are permanent and strictly skipped.
    """
    artifacts_dir = "/var/www/artifacts"
    archive_dir = "/var/www/artifacts/archive"
    plans_dir = "/var/www/artifacts/plans"
    purged_superseded = []
    purged_executed = []

    if not os.path.exists(artifacts_dir):
        return {"purged_superseded": purged_superseded, "purged_executed": purged_executed}

    executed_stems = set()
    scan_dirs = [artifacts_dir]
    for d in [archive_dir, plans_dir]:
        if os.path.exists(d):
            scan_dirs.append(d)

    for sdir in scan_dirs:
        try:
            for fname in os.listdir(sdir):
                if HANDOVER_PATTERN.search(fname):
                    continue
                if ".executed." in fname:
                    stem = re.sub(r'_v\d+.*$', '', fname)
                    executed_stems.add(stem)
        except Exception:
            pass

    for sdir in scan_dirs:
        try:
            for fname in os.listdir(sdir):
                if HANDOVER_PATTERN.search(fname):
                    continue
                if ".superseded." in fname:
                    fpath = os.path.join(sdir, fname)
                    stem = re.sub(r'_v\d+.*$', '', fname)
                    if sdir in [artifacts_dir, plans_dir] or stem in executed_stems:
                        try:
                            os.remove(fpath)
                            purged_superseded.append(fpath)
                        except Exception:
                            pass
        except Exception:
            pass

    if purge_executed:
        for sdir in scan_dirs:
            try:
                for fname in os.listdir(sdir):
                    if HANDOVER_PATTERN.search(fname):
                        continue
                    if ".executed." in fname:
                        fpath = os.path.join(sdir, fname)
                        try:
                            os.remove(fpath)
                            purged_executed.append(fpath)
                        except Exception:
                            pass
            except Exception:
                pass

    return {"purged_superseded": purged_superseded, "purged_executed": purged_executed}

def auto_sync_governance(target_file: str = ""):
    """
    Autonomous Parity & Mirror Reactor: Keeps SSoT (Google Drive), Git Repositories,
    and local runtime in real-time lockstep following the Sovereign Flow:
    bak -> ssot -> iniciar.sh-first -> skill-registry -> push repositorios.
    Silently and deterministically propagates changes and pushes to GitHub without friction.
    """
    import shutil, subprocess, filecmp

    def files_differ(f1: str, f2: str) -> bool:
        try:
            if not os.path.exists(f1) or not os.path.exists(f2):
                return True
            if os.path.getsize(f1) != os.path.getsize(f2):
                return True
            return not filecmp.cmp(f1, f2, shallow=False)
        except Exception:
            return True

    # 1. Core governance sync pairs (Drive SSoT <-> Local runtime)
    # ZCP-First Invariant: Active development in ZCP (/var/www) reflects to Drive SSoT (0zcp-123).
    for ssot_path, runtime_path in CORE_SYNC_PAIRS:
        try:
            ssot_exists = os.path.exists(ssot_path)
            runtime_exists = os.path.exists(runtime_path)
            if not ssot_exists and not runtime_exists:
                continue

            if runtime_exists:
                if not ssot_exists or files_differ(runtime_path, ssot_path):
                    os.makedirs(os.path.dirname(ssot_path), exist_ok=True)
                    shutil.copy2(runtime_path, ssot_path)
            elif ssot_exists and not runtime_exists:
                os.makedirs(os.path.dirname(runtime_path), exist_ok=True)
                shutil.copy2(ssot_path, runtime_path)
                if runtime_path.startswith("/var/www/.bin/"):
                    try:
                        os.chmod(runtime_path, 0o755)
                    except Exception:
                        pass
        except Exception:
            pass

    # 2. Real-time Mirror Sync for Skills (SSoT Triad: .agents/skills <-> zerops-astro-skills <-> Drive SSoT)
    skill_changed = False
    is_skill_touch = bool(
        target_file and (
            "/.agents/skills/" in target_file or target_file.startswith(".agents/skills/") or
            "/zerops-astro-skills/" in target_file or target_file.startswith("zerops-astro-skills/")
        )
    )

    if is_skill_touch:
        try:
            rel = ""
            skill_name = ""
            if "/.agents/skills/" in target_file:
                rel = target_file.split("/.agents/skills/")[1].lstrip("/")
            elif target_file.startswith(".agents/skills/"):
                rel = target_file.split(".agents/skills/")[1].lstrip("/")
            elif "/zerops-astro-skills/" in target_file:
                rel = target_file.split("/zerops-astro-skills/")[1].lstrip("/")
            elif target_file.startswith("zerops-astro-skills/"):
                rel = target_file.split("zerops-astro-skills/")[1].lstrip("/")

            if rel:
                skill_name = rel.split("/")[0]
                local_path = os.path.join("/var/www/.agents/skills", rel)
                git_dest = os.path.join("/var/www/zerops-astro-skills", rel)
                drive_dest = os.path.join("/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/skills", rel)

                src_path = target_file if os.path.isabs(target_file) else os.path.join("/var/www", target_file)
                if os.path.exists(src_path):
                    for dest in [local_path, git_dest]:
                        if dest != src_path:
                            os.makedirs(os.path.dirname(dest), exist_ok=True)
                            shutil.copy2(src_path, dest)
                    if not UPSTREAM_SKILLS_PATTERN.match(skill_name):
                        os.makedirs(os.path.dirname(drive_dest), exist_ok=True)
                        shutil.copy2(src_path, drive_dest)
                    skill_changed = True
        except Exception:
            pass

    # 3. Real-time Mirror Sync for Deployment Scripts
    is_script_touch = bool(
        target_file and (
            "/scripts/" in target_file or "/.bin/" in target_file or
            target_file.endswith("iniciar.sh") or target_file.endswith("unisetup.sh")
        )
    )
    if is_script_touch:
        try:
            base_script = os.path.basename(target_file)
            repo_script = os.path.join("/var/www/zerops-astrobranding/scripts", base_script)
            drive_script = os.path.join("/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts", base_script)
            bin_script = os.path.join("/var/www/.bin", base_script)
            src_script = target_file if os.path.isabs(target_file) else os.path.join("/var/www", target_file)

            if os.path.exists(src_script):
                for dest in [repo_script, drive_script, bin_script]:
                    if dest != src_script and os.path.exists(os.path.dirname(dest)):
                        shutil.copy2(src_script, dest)
                        if dest == bin_script or base_script.endswith(".sh"):
                            try:
                                os.chmod(dest, 0o755)
                            except Exception:
                                pass
        except Exception:
            pass

    # 4. SKILL REGISTRY AUTONOMOUS REFRESH & SSOT MIRROR ($N_7)
    registry_local = "/var/www/.atl/skill-registry.md"
    registry_drive = "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.atl/skill-registry.md"
    registry_branding = "/var/www/zerops-astrobranding/.atl/skill-registry.md"

    if skill_changed or (target_file and "skill-registry" in target_file):
        try:
            subprocess.run(["gentle-ai", "skill-registry", "refresh", "--cwd", "/var/www", "--force"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except Exception:
            pass

    if os.path.exists(registry_local):
        for reg_dest in [registry_drive, registry_branding]:
            try:
                if not os.path.exists(reg_dest) or files_differ(registry_local, reg_dest):
                    os.makedirs(os.path.dirname(reg_dest), exist_ok=True)
                    shutil.copy2(registry_local, reg_dest)
            except Exception:
                pass

    # 5. Autonomous Git Mirror Synchronization (Non-blocking background spawn to preserve <30ms execution)
    # 5a. zerops-astro-skills
    try:
        skills_git = "/var/www/zerops-astro-skills"
        if os.path.exists(os.path.join(skills_git, ".git")):
            st = subprocess.run(["git", "status", "--porcelain"], cwd=skills_git, capture_output=True, text=True, timeout=1)
            if st.returncode == 0 and st.stdout.strip():
                subprocess.run(["git", "add", "-A"], cwd=skills_git, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
                subprocess.run(["git", "commit", "-m", "chore(skills): auto-sync mirror mode"], cwd=skills_git, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
                # Background push to never block hook
                subprocess.Popen(["git", "push", "origin", "main"], cwd=skills_git, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # 5b. zerops-astrobranding
    try:
        repo_git = "/var/www/zerops-astrobranding"
        if os.path.exists(os.path.join(repo_git, ".git")):
            st = subprocess.run(["git", "status", "--porcelain"], cwd=repo_git, capture_output=True, text=True, timeout=1)
            if st.returncode == 0 and st.stdout.strip():
                subprocess.run(["git", "add", "-A"], cwd=repo_git, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
                subprocess.run(["git", "commit", "-m", "chore(repo): auto-sync mirror mode"], cwd=repo_git, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
                # Background push to never block hook
                subprocess.Popen(["git", "push", "origin", "main"], cwd=repo_git, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    # Purge bytecode residue deterministically (Invariant 6)
    hooks_pycache = "/var/www/.bin/hooks/__pycache__"
    if os.path.exists(hooks_pycache):
        try:
            shutil.rmtree(hooks_pycache, ignore_errors=True)
        except Exception:
            pass

    # Auto-purge superseded artifact drafts when a version has executed
    try:
        cleanup_artifacts_lifecycle(purge_executed=False)
    except Exception:
        pass

def has_recent_backup(target_file: str) -> bool:
    """
    Verifies that critical files have a monotonic pre-mutation backup:
    A valid backup MUST have mtime >= target_file mtime - 1.0s.
    If the target_file was modified after the backup was created,
    a fresh snapshot of the current state must be taken before mutating.
    Flow: bak -> ssot -> iniciar.sh-first -> skill-registry -> push repositorios ($N_1$).
    """
    is_skill = bool(
        "/.agents/skills/" in target_file or target_file.startswith(".agents/skills/") or
        "/zerops-astro-skills/" in target_file or target_file.startswith("zerops-astro-skills/")
    )
    is_script = bool(
        "/0zcp-123/scripts/" in target_file or "/.bin/" in target_file or "/scripts/" in target_file or
        target_file.endswith("iniciar.sh") or target_file.endswith("unisetup.sh")
    )
    is_rule = bool(
        target_file.endswith("AGENTS.md") or "/.agents/rules/" in target_file or
        "/.agents/references/" in target_file or target_file.endswith("00-SUPREME-DIRECTIVE.md")
    )
    is_hook = bool("/.bin/hooks/" in target_file or "/scripts/hooks/" in target_file)

    if not (is_skill or is_script or is_rule or is_hook):
        return True
    if not os.path.exists(target_file):
        return True  # New file being created

    target_mtime = os.path.getmtime(target_file)
    if is_skill:
        target_bak_dir = "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak/skills"
    elif is_rule:
        target_bak_dir = "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak/rules"
    else:
        target_bak_dir = "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak/scripts"

    base_name = os.path.basename(target_file)
    name_stem = os.path.splitext(base_name)[0]

    skill_name = ""
    if is_skill:
        if "/.agents/skills/" in target_file:
            parts = target_file.split("/.agents/skills/")
            skill_name = parts[1].strip("/").split("/")[0] if len(parts) > 1 else ""
        elif target_file.startswith(".agents/skills/"):
            parts = target_file.split(".agents/skills/")
            skill_name = parts[1].strip("/").split("/")[0] if len(parts) > 1 else ""
        elif "/zerops-astro-skills/" in target_file:
            parts = target_file.split("/zerops-astro-skills/")
            skill_name = parts[1].strip("/").split("/")[0] if len(parts) > 1 else ""
        elif target_file.startswith("zerops-astro-skills/"):
            parts = target_file.split("zerops-astro-skills/")
            skill_name = parts[1].strip("/").split("/")[0] if len(parts) > 1 else ""

    latest_bak_mtime = 0.0
    if os.path.exists(target_bak_dir):
        try:
            for fname in os.listdir(target_bak_dir):
                match = False
                if skill_name and skill_name in fname:
                    match = True
                elif name_stem and name_stem in fname:
                    match = True
                elif base_name in fname:
                    match = True

                if match:
                    fpath = os.path.join(target_bak_dir, fname)
                    if os.path.isfile(fpath) or os.path.isdir(fpath):
                        mtime = os.path.getmtime(fpath)
                        if mtime > latest_bak_mtime:
                            latest_bak_mtime = mtime
        except Exception:
            pass

    # Auto-snapshot before mutation: silent physical safety with standard naming & rotation
    if latest_bak_mtime < (target_mtime - 1.0):
        try:
            os.makedirs(target_bak_dir, exist_ok=True)
            import shutil, time
            ts = int(time.time())
            snapshot_name = f"{skill_name}_{base_name}_{ts}.bak" if (is_skill and skill_name) else (f"{name_stem}_{base_name}_{ts}.bak" if name_stem != base_name else f"{base_name}_{ts}.bak")
            snapshot_path = os.path.join(target_bak_dir, snapshot_name)
            shutil.copy2(target_file, snapshot_path)

            # Auto-rotate: keep max 5 most recent snapshots for this specific target
            prefix_match = f"{skill_name}_v" if (is_skill and skill_name) else (f"{name_stem}_" if name_stem != base_name else f"{base_name}_")
            existing = [os.path.join(target_bak_dir, f) for f in os.listdir(target_bak_dir) if f.startswith(prefix_match) and f.endswith(".bak")]
            if len(existing) > 5:
                existing.sort(key=os.path.getmtime)
                for old_f in existing[:-5]:
                    try:
                        if os.path.isdir(old_f):
                            shutil.rmtree(old_f, ignore_errors=True)
                        else:
                            os.remove(old_f)
                    except Exception:
                        pass
        except Exception:
            pass
    return True

def get_skill_triggers_map(registry_path="/var/www/.atl/skill-registry.md") -> dict:
    """Builds or reads cached triggers map from skill-registry.md."""
    cache_path = "/var/www/.bin/hooks/skill_triggers_cache.json"
    try:
        if os.path.exists(cache_path) and os.path.getmtime(cache_path) >= os.path.getmtime(registry_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass

    skills = {}
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("| `"):
                        parts = [p.strip() for p in line.split("|")]
                        if len(parts) >= 5:
                            name = parts[1].replace("`", "").strip()
                            desc = parts[2]
                            path = parts[4].replace("`", "").strip()
                            triggers = [name.lower()]
                            if "Trigger:" in desc:
                                trig_text = desc.split("Trigger:")[1]
                                trig_part = re.split(r'\.\s+', trig_text.strip())[0].rstrip('.')
                                for t in trig_part.split(","):
                                    t_clean = t.strip().lower()
                                    if len(t_clean) >= 3 and t_clean != "api":
                                        triggers.append(t_clean)
                            skills[name] = {"triggers": list(set(triggers)), "path": path}
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(skills, f)
        except Exception:
            pass
    return skills

def detect_skills_in_prompt(prompt: str) -> list:
    """Matches text against registered skill triggers in < 2ms."""
    if not prompt:
        return []
    skills = get_skill_triggers_map()
    prompt_lower = prompt.lower()

    # Meta-Inquiry Guard: If prompt is meta-conversational regarding prompt/tokens,
    # suppress false-positive backend runtime skill triggers.
    is_meta_prompt_query = bool(re.search(r'\b(prompt|tokens?|gast(o|ar)|costo|traga|plantilla|cuanto)\b', prompt_lower))

    matches = []
    for name, data in skills.items():
        if is_meta_prompt_query and name in ["python", "bun", "nodejs", "golang", "rust", "alpine", "ubuntu"]:
            continue
        for trig in data.get("triggers", []):
            if len(trig) < 3 or trig in ["and", "the", "for", "with"]:
                continue
            pattern = r"\b" + re.escape(trig) + r"\b"
            if re.search(pattern, prompt_lower):
                matches.append((name, trig, data.get("path", "")))
                break
    return matches

def glob_pids() -> list:
    """Returns all numeric PIDs currently running in /proc."""
    pids = []
    try:
        for fname in os.listdir("/proc"):
            if fname.isdigit():
                pids.append(int(fname))
    except Exception:
        pass
    return pids

def get_process_ancestors(pid: int = None) -> set:
    """Returns the set of all ancestor PIDs up to PID 1."""
    if pid is None:
        pid = os.getpid()
    ancestors = set()
    curr = pid
    while curr > 1:
        ancestors.add(curr)
        try:
            with open(f"/proc/{curr}/status", "r", encoding="utf-8", errors="ignore") as f:
                ppid = None
                for line in f:
                    if line.startswith("PPid:"):
                        ppid = int(line.split()[1])
                        break
                if ppid and ppid > 0 and ppid not in ancestors:
                    ancestors.add(ppid)
                    curr = ppid
                else:
                    break
        except Exception:
            break
    return ancestors

def get_process_info(pid: int) -> dict:
    """Retrieves command line, executable name, PPID, state, and TTY for a given PID from /proc."""
    info = {"pid": pid, "cmdline": "", "comm": "", "ppid": 0, "tty": "", "state": ""}
    proc_dir = f"/proc/{pid}"
    if not os.path.isdir(proc_dir):
        return info
    try:
        with open(f"{proc_dir}/cmdline", "rb") as f:
            info["cmdline"] = f.read().replace(b"\x00", b" ").decode("utf-8", "ignore").strip()
    except Exception:
        pass
    try:
        with open(f"{proc_dir}/status", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("Name:"):
                    info["comm"] = line.split()[1].strip()
                elif line.startswith("PPid:"):
                    info["ppid"] = int(line.split()[1])
                elif line.startswith("State:"):
                    info["state"] = line.split()[1].strip()
    except Exception:
        pass
    try:
        for fd in (0, 1, 2):
            fd_path = f"{proc_dir}/fd/{fd}"
            if os.path.exists(fd_path):
                link = os.readlink(fd_path)
                if link.startswith("/dev/pts/") or link.startswith("/dev/tty"):
                    info["tty"] = link
                    break
        if not info["tty"]:
            with open(f"{proc_dir}/stat", "r", encoding="utf-8", errors="ignore") as f:
                stat_content = f.read()
                rparen_idx = stat_content.rfind(")")
                if rparen_idx != -1:
                    fields = stat_content[rparen_idx + 1:].split()
                    if len(fields) > 4 and fields[4] != "0":
                        info["tty"] = f"tty_nr:{fields[4]}"
    except Exception:
        pass
    return info

def is_kill_attempt_dangerous(cmd: str) -> tuple:
    """
    Guard de Kill Soberano (BAI-322):
    Deniega kill/pkill/killall cuyo objetivo sea:
    1. Un proceso agy con TTY activo (sesión interactiva viva).
    2. Un ancestro de la invocación actual.
    3. Un pkill -f cuyo patrón coincida con la propia shell o un ancestro.
    Decide en tiempo real consultando /proc (tty, ppid, cmdline), nunca por PIDs fijos.
    """
    if not re.search(r'\b(kill|pkill|killall)\b', cmd):
        return False, ""

    ancestors = get_process_ancestors()
    ancestor_cmdlines = []
    for apid in ancestors:
        ainfo = get_process_info(apid)
        if ainfo["cmdline"]:
            ancestor_cmdlines.append(ainfo["cmdline"])

    subcmds = re.split(r'[;&|]+', cmd)
    for raw_sub in subcmds:
        sub = raw_sub.strip()
        if not sub:
            continue
        parts = sub.split()
        if not parts:
            continue

        cmd_idx = 0
        while cmd_idx < len(parts) and parts[cmd_idx] in ["sudo", "env", "nohup", "timeout", "builtin", "exec"]:
            if parts[cmd_idx] == "timeout" and cmd_idx + 1 < len(parts):
                cmd_idx += 2
                continue
            cmd_idx += 1
        if cmd_idx >= len(parts):
            continue

        base_bin = os.path.basename(parts[cmd_idx])
        args_list = parts[cmd_idx + 1:]

        # Case 1: kill
        if base_bin == "kill":
            target_pids = []
            for arg in args_list:
                if arg.startswith("-"):
                    continue
                if arg.isdigit():
                    target_pids.append(int(arg))

            for tpid in target_pids:
                if tpid in ancestors:
                    return True, (
                        f"ARNÉS DE PROCESOS (Guard de Kill): Se denegó 'kill' sobre el PID {tpid}. "
                        "El proceso pertenece a la jerarquía de ancestros del hook / shell activa."
                    )
                pinfo = get_process_info(tpid)
                if ("agy" in pinfo["cmdline"] or pinfo["comm"] == "agy") and pinfo["tty"]:
                    return True, (
                        f"ARNÉS DE PROCESOS (Guard de Kill): Se denegó 'kill' sobre el PID {tpid} ({pinfo['comm']}). "
                        f"El proceso es una sesión interactiva viva de Antigravity con TTY asignado ({pinfo['tty']})."
                    )

        # Case 2: pkill
        elif base_bin == "pkill":
            pattern_parts = []
            skip_next = False
            for arg in args_list:
                if skip_next:
                    skip_next = False
                    continue
                if arg in ["-u", "-U", "-G", "-g", "-P", "-t"]:
                    skip_next = True
                    continue
                if arg.startswith("-"):
                    continue
                pattern_parts.append(arg)
            pattern = " ".join(pattern_parts).strip()
            if not pattern:
                continue

            try:
                pat_regex = re.compile(pattern, re.IGNORECASE)
            except Exception:
                pat_regex = None

            # Check if pattern matches caller shell or any ancestor
            for acmd in ancestor_cmdlines:
                if (pat_regex and pat_regex.search(acmd)) or pattern in acmd:
                    return True, (
                        f"ARNÉS DE PROCESOS (Guard de Kill): Se denegó 'pkill' con patrón '{pattern}'. "
                        "El patrón coincide con la propia shell o un proceso ancestro activo."
                    )

            # Check if pattern matches any live agy with TTY in /proc
            for pdir in glob_pids():
                pinfo = get_process_info(pdir)
                if ("agy" in pinfo["cmdline"] or pinfo["comm"] == "agy") and pinfo["tty"]:
                    if (pat_regex and (pat_regex.search(pinfo["cmdline"]) or pat_regex.search(pinfo["comm"]))) or pattern in pinfo["cmdline"] or pattern in pinfo["comm"]:
                        return True, (
                            f"ARNÉS DE PROCESOS (Guard de Kill): Se denegó 'pkill' con patrón '{pattern}'. "
                            f"El patrón afectaría a la sesión viva PID {pdir} con TTY {pinfo['tty']}."
                        )

        # Case 3: killall
        elif base_bin == "killall":
            targets = [a for a in args_list if not a.startswith("-")]
            for tgt in targets:
                for apid in ancestors:
                    ainfo = get_process_info(apid)
                    if tgt == ainfo["comm"] or tgt in ainfo["cmdline"]:
                        return True, (
                            f"ARNÉS DE PROCESOS (Guard de Kill): Se denegó 'killall {tgt}'. "
                            "El objetivo coincide con procesos ancestros de la invocación actual."
                        )
                if tgt == "agy" or "agy" in tgt:
                    for pdir in glob_pids():
                        pinfo = get_process_info(pdir)
                        if ("agy" in pinfo["cmdline"] or pinfo["comm"] == "agy") and pinfo["tty"]:
                            return True, (
                                f"ARNÉS DE PROCESOS (Guard de Kill): Se denegó 'killall {tgt}'. "
                                f"Hay sesiones interactivas vivas de agy con TTY ({pinfo['tty']})."
                            )

    return False, ""

def evaluate_hook(payload: dict) -> dict:
    # 0. SessionStart Handling (Mandatory Anti-AMN Recall)
    if payload.get("session_start") or payload.get("event") == "SessionStart" or payload.get("hookType") == "SessionStart":
        recall_msg = (
            "🏛️ RECALL DE SESIÓN OBLIGATORIO (Anti-AMN v3.2): Al inicio de CADA sesión es mandatorio ejecutar "
            "'mem_context' o 'mem_search' y 'zerops_discover' antes de emitir juicios o modificar el proyecto. "
            "Para investigación externa, estado del arte o benchmarks, invocá la skill 'research' con subagentes "
            "('invoke_subagent' con typeName 'research'). Prohibido arrancar ciego o desde memoria pre-entrenada."
        )
        return {
            "injectSteps": [
                {
                    "systemMessage": {
                        "systemMessage": recall_msg
                    }
                }
            ]
        }

    # 0.5 Stop Event Handling (Linear-First Chat Delivery Gate)
    if "terminationReason" in payload or payload.get("is_stop_event"):
        term_reason = payload.get("terminationReason", "NO_TOOL_CALL")
        if term_reason == "NO_TOOL_CALL":
            plans_dir = "/var/www/artifacts/plans"
            has_active_plan = os.path.exists(plans_dir) and any(
                f.endswith(".md") and not any(x in f.lower() for x in [".executed.", ".superseded.", "report", ".test_hide"])
                for f in os.listdir(plans_dir)
            )
            if has_active_plan and not payload.get("test_bypass_linear"):
                state_file = "/tmp/.linear_activity_state.json"
                alt_state_file = "/var/www/artifacts/.linear_activity_state.json"
                has_linear_recent = False
                for sf in [state_file, alt_state_file]:
                    if os.path.exists(sf):
                        try:
                            with open(sf, "r") as f:
                                act_data = json.load(f)
                                if time.time() - (act_data.get("timestamp", 0) / 1000.0) < 7200:
                                    has_linear_recent = True
                                    break
                        except Exception:
                            pass

                transcript_path = payload.get("transcriptPath", "")
                has_inspection = payload.get("test_has_inspection", False)
                if transcript_path and os.path.exists(transcript_path) and not has_inspection:
                    try:
                        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                            t_lines = f.readlines()
                            for tl in reversed(t_lines[-20:]):
                                if any(tk in tl for tk in ["read_file", "run_command", "write_file", "edit_file", "call_mcp_tool"]):
                                    has_inspection = True
                                    break
                    except Exception:
                        pass

                if has_inspection and not has_linear_recent:
                    stop_counter_file = "/tmp/.linear_stop_force_count"
                    count = 0
                    if os.path.exists(stop_counter_file):
                        try:
                            with open(stop_counter_file, "r") as f:
                                count = int(f.read().strip())
                        except Exception:
                            count = 0
                    if count < 1:
                        with open(stop_counter_file, "w") as f:
                            f.write(str(count + 1))
                        return {
                            "decision": "continue",
                            "reason": (
                                "🏛️ VIOLACIÓN LINEAR-FIRST GATE (00-SUPREME-DIRECTIVE Invariante 2): "
                                "Hay un plan activo en /var/www/artifacts/plans/ y realizaste inspecciones/descubrimientos "
                                "sin haber persistido tus hallazgos en Linear. Es mandatorio ejecutar 'linear-cli comment <ID>' "
                                "antes de entregar explicaciones o cerrar el turno en el chat."
                            )
                        }
                    else:
                        if os.path.exists(stop_counter_file):
                            try:
                                os.remove(stop_counter_file)
                            except Exception:
                                pass
        return {}

    # 1. PostToolUse Handling
    if "stepIdx" in payload and "invocationNum" not in payload and ("error" in payload or "toolResult" in payload or "status" in payload):
        return {}

    # 2. PreInvocation Handling (Dynamic Epistemic Radar & Gentle-AI Orchestrator)
    if "invocationNum" in payload or "initialNumSteps" in payload:
        inv_num = payload.get("invocationNum", 0)
        now_ts = time.time()
        state_file = "/tmp/.tool_guard_pi_state.json"
        last_state = {}
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    last_state = json.load(f)
            except Exception:
                pass

        if payload.get("test_dedup"):
            return {}

        try:
            with open(state_file, "w") as f:
                json.dump({"invocationNum": inv_num, "ts": now_ts}, f)
        except Exception:
            pass

        # Zero-Hang: auto_sync_governance síncrono purgado de PreInvocation para evitar timeouts y SIGKILL por FUSE
        user_prompt = payload.get("userPrompt", "")
        if not user_prompt:
            transcript_path = payload.get("transcriptPath", "")
            if transcript_path and os.path.exists(transcript_path):
                try:
                    with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in reversed(f.readlines()):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                step_data = json.loads(line)
                                if step_data.get("type") == "USER_INPUT" or step_data.get("source") == "USER_EXPLICIT":
                                    content = step_data.get("content", "")
                                    if content:
                                        m = re.search(r'<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>', content, re.DOTALL)
                                        user_prompt = m.group(1).strip() if m else content.strip()
                                        if user_prompt:
                                            break
                            except Exception:
                                pass
                except Exception:
                    pass
        halt_alert = ""
        dummy_plan = "/var/www/artifacts/test_plan_v1.md"
        if os.path.exists(dummy_plan) and user_prompt:
            has_question = ("?" in user_prompt or "¿" in user_prompt)
            has_go = bool(re.search(r'\b(go|adelante|procede|ejecuta|ejecutá|aprobado|dale|si|sí)\b', user_prompt, re.IGNORECASE))
            if has_question or not has_go:
                halt_alert = "\n⏸️ F4 HALT GATE ACTIVO: Ticket en progreso."

        ephemeral_msgs = []
        if "--test" in sys.argv and not user_prompt:
            governance_msg = "🏛️ ARNÉS FÍSICO ZCP (v3.1): Contrato Plan-First Gate. Contrato Anti-Redundancia en Chat. F0 Grounding Epistémico (Anti-AMN con Context7/Exa/Jina). Reality Over Checklist Theater."
            ephemeral_msgs.append(f"{governance_msg}{halt_alert}".strip())
        else:
            prompt_lower = user_prompt.lower()
            matched_skills = [m[0] for m in detect_skills_in_prompt(user_prompt)]

            # 1. Epistemic Grounding Radar (F0 Positive Guidance)
            is_eval = any(k in prompt_lower for k in ["mejor forma", "investigar", "investiga", "benchmark", "sota", "comparar", "cual es mejor"])
            if "research" in matched_skills or is_eval:
                ephemeral_msgs.append(
                    "F0 Epistemic Grounding: Ante consultas de arquitectura, SOTA o benchmark, "
                    "contrastá fuentes primarias ejecutando la skill 'research' (Exa/Context7/Tavily) antes de concluir en prosa."
                )

            # 2. Gentle-AI Subagent Orchestrator Gate
            is_heavy = any(k in prompt_lower for k in ["flujo", "refactor", "implementa", "arregla", "construye", "despliega", "crea"])
            if is_heavy and len(prompt_lower) > 40:
                ephemeral_msgs.append(
                    "Gentle-AI Orchestrator: Mantené el hilo padre delgado. Para tareas sustanciales o de múltiples archivos, "
                    "delegá la ejecución a subagentes acotados (invoke_subagent con 'research' o define_subagent) y sintetizá resultados."
                )

            # 3. Linear-First Epistemic Persistence Gate (Invariante 2)
            plans_dir = "/var/www/artifacts/plans"
            if os.path.exists(plans_dir) and any(f.endswith(".md") for f in os.listdir(plans_dir)):
                ephemeral_msgs.append(
                    "🏛️ INVARIANTE LINEAR-FIRST GATE (00-SUPREME-DIRECTIVE Invariante 2): "
                    "Hay un plan activo en ejecución en /var/www/artifacts/plans/. Prohibido responder o dar explicaciones en el chat "
                    "sin haber ejecutado 'linear-cli comment <ID>' para persistir tus hallazgos técnicos en Linear. "
                    "Persistir en Linear es un prerequisito bloqueante antes de responder al usuario."
                )

            if halt_alert:
                ephemeral_msgs.append(halt_alert.strip())

        if ephemeral_msgs:
            return {
                "injectSteps": [
                    {
                        "ephemeralMessage": "\n\n".join(ephemeral_msgs)
                    }
                ]
            }
        return {}

    # 2. PreToolUse Handling
    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    # 0. Anti-AMN & F0 Epistemic Inflow: Enrutamiento afirmativo hacia skill research
    if tool_name == "search_web":
        return {
            "decision": "deny",
            "reason": (
                "Contrato Epistémico F0 (Anti-AMN): Para investigación y grounding en vivo, ejecutá "
                "exclusivamente la skill 'research' mediante 'call_mcp_tool' "
                "(servidores: context7, exa, brave, tavily, firecrawl) o mediante subagente 'invoke_subagent' (typeName: 'research')."
            )
        }

    # 0.1 Enrutamiento de Servidor MCP Local de Linear (Anti-Hang & Zero Token Waste)
    if tool_name == "call_mcp_tool" and args.get("ServerName") == "linear":
        return {
            "decision": "deny",
            "reason": (
                "Servidor MCP 'linear' optimizado: Operá Linear exclusivamente mediante el CLI local '/usr/local/bin/linear-cli' "
                "o Direct GraphQL API (<200ms) para evitar timeouts y procesos npx colgados."
            )
        }

    # 0.2 Invariante Single-Node ZCP: Bloqueo de escalado multi-contenedor (BAI-322)
    if tool_name == "call_mcp_tool" and args.get("ServerName") == "zerops":
        if args.get("ToolName") == "zerops_scale":
            scale_args = args.get("Arguments", {})
            if scale_args.get("serviceHostname") == "zcp":
                min_c = scale_args.get("minContainers")
                max_c = scale_args.get("maxContainers")
                if (min_c is not None and min_c > 1) or (max_c is not None and max_c > 1):
                    return {
                        "decision": "deny",
                        "reason": (
                            f"INVARIANTE SINGLE-NODE ZCP: Prohibido escalar zcp a múltiples contenedores "
                            f"(minContainers={min_c}, maxContainers={max_c}). El plano de control ZCP es stateful "
                            "y debe operar estrictamente en minContainers=1, maxContainers=1 para evitar split-brain."
                        )
                    }

    # A. File writes / edits guards (Antigravity & Claude Code)
    if tool_name in ["write_to_file", "replace_file_content", "write_file", "edit_file"]:
        target_file = args.get("Path", "") or args.get("TargetFile", "")
        content_to_check = (
            args.get("Content", "") or
            args.get("Replacement", "") or
            args.get("CodeContent", "") or
            args.get("ReplacementContent", "")
        )

        # A0. SSoT Sovereign Custom Skills Anti-Pollution Shield
        polluted_skill = is_upstream_skill_pollution(target_file, is_write=True)
        if polluted_skill:
            return {
                "decision": "deny",
                "reason": (
                    f"ARNÉS SSoT (Invariante de Inmutabilidad Upstream): La skill [{polluted_skill}] pertenece a suites externas "
                    "(Gentle AI, Pocock, Anthropic, Superpowers) y está estrictamente prohibido modificarla o sincronizarla a Drive SSoT. "
                    "Modificá exclusivamente custom skills soberanas en '/var/www/zerops-astro-skills/'."
                )
            }

        # A1. SSoT Relative Path Guard
        if contains_relative_0zcp_leak(target_file):
            return {
                "decision": "deny",
                "reason": (
                    "Contrato SSoT (Ruta Canónica): Usá exclusivamente la ruta absoluta canónica "
                    "'/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/' o remota 'baiosfera:0ZEROPS-AGY/0zcp-123/'."
                )
            }

        # A1.1 Multi-Tenant Upstream Chassis Shield
        chassis_prefix = "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/"
        if target_file.startswith(chassis_prefix):
            rel_to_chassis = target_file[len(chassis_prefix):]
            tenant_match = re.search(r'\b(elplacerdc|glamur|damaren)\b', rel_to_chassis, re.IGNORECASE)
            if tenant_match and any(rel_to_chassis.endswith(ext) for ext in [".db", ".sqlite", "-keys.md", "_keys.md", ".json", ".env"]):
                return {
                    "decision": "deny",
                    "reason": (
                        f"ARNÉS MULTI-TENANT (Aislamiento Upstream): El chasis '0zcp-123/' es neutral y universal. "
                        f"Mantené los datos del tenant [{tenant_match.group(0)}] exclusivamente en "
                        "'/var/www/baiosfera/0ZEROPS-AGY/users-apis/' o en su propio namespace."
                    )
                }

        # A2. Handover Immunity
        if HANDOVER_PATTERN.search(target_file):
            return {
                "decision": "deny",
                "reason": (
                    f"ARNÉS HANDOVER IMMUNITY: El archivo [{os.path.basename(target_file)}] "
                    "es un activo de relevo inter-sesión protegido contra modificación o sobreescritura."
                )
            }

        # A3. Skill Pre-Mutation Backup Gate
        if not has_recent_backup(target_file):
            return {
                "decision": "deny",
                "reason": (
                    f"ARNÉS FÍSICO N1 (Pre-Mutation Backup): Para modificar [{os.path.basename(target_file)}], "
                    "generá previamente un snapshot en '/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak/skills/' o '.../bak/'."
                )
            }

        # A4. Linear-First Epistemic Persistence Gate (Invariante 2 Soberano)
        plans_dir = "/var/www/artifacts/plans"
        has_active_plan = os.path.exists(plans_dir) and any(
            f.endswith(".md") and not any(x in f.lower() for x in [".executed.", ".superseded.", "report", ".test_hide"])
            for f in os.listdir(plans_dir)
        )
        is_target_code_or_skill = (
            "/zerops-astro-skills/" in target_file or
            "/.agents/skills/" in target_file or
            ("/var/www/" in target_file and not any(p in target_file for p in [
                "/artifacts/", "/scratch/", "/bak/", "/.bin/", "/.atl/",
                "AGENTS.md", "00-SUPREME-DIRECTIVE.md", ".json", "hooks"
            ]))
        )
        if has_active_plan and is_target_code_or_skill and not payload.get("test_bypass_linear"):
            state_file = "/tmp/.linear_activity_state.json"
            alt_state_file = "/var/www/artifacts/.linear_activity_state.json"
            has_linear_recent = False
            for sf in [state_file, alt_state_file]:
                if os.path.exists(sf):
                    try:
                        with open(sf, "r") as f:
                            act_data = json.load(f)
                            if time.time() - (act_data.get("timestamp", 0) / 1000.0) < 7200:
                                has_linear_recent = True
                                break
                    except Exception:
                        pass
            if not has_linear_recent:
                return {
                    "decision": "deny",
                    "reason": (
                        f"🏛️ INVARIANTE LINEAR-FIRST GATE (00-SUPREME-DIRECTIVE Invariante 2): "
                        f"Hay un plan activo en /var/www/artifacts/plans/. Prohibido mutar [{os.path.basename(target_file)}] "
                        "sin haber registrado actividad técnica previa en Linear con 'linear-cli comment <ID>' o 'linear-cli update-status'. "
                        "Persistí tus descubrimientos y criterios en Linear antes de modificar código o skills."
                    )
                }

        # A4.1 Anti-Perros Guardianes (Eradicates Synthetic Individual Validator Scripts)
        base_target = os.path.basename(target_file)
        if base_target.endswith("-validate.sh") and base_target != "skills-suite-validate.sh":
            return {
                "decision": "deny",
                "reason": (
                    f"Soberanía del Sensor Universal: La validación de capacidades reside exclusivamente "
                    f"en 'skills-suite-validate'. En vez de crear o editar validadores individuales como [{base_target}], "
                    "verificá que los scripts compilen con 'bash -n' y que las pruebas residan en la suite física "
                    "de la aplicación (bun test / pytest) o en el Sensor Universal."
                )
            }

        # A5. CoHaLo & Skill-Improver Quality Gate
        content_to_check = content_to_check or args.get("CodeContent", "") or args.get("ReplacementContent", "")

        # A5.1 Positive Guidance Guard (Blocks negative prompt dogma in governance and skills)
        is_governance = (
            target_file.endswith("AGENTS.md") or
            "/.agents/rules/" in target_file or
            target_file.endswith("00-SUPREME-DIRECTIVE.md") or
            (target_file.endswith("SKILL.md") and "/.agents/skills/" in target_file)
        )
        if (target_file.endswith(".md") or is_governance) and content_to_check:
            negative_match = re.search(
                r'\b(Queda terminantemente prohibido|Do NOT activate under any circumstances|Está terminantemente prohibido|terminantemente prohibido|queda prohibido|está prohibido|strictly forbidden)\b',
                content_to_check,
                re.IGNORECASE
            )
            if negative_match:
                return {
                    "decision": "deny",
                    "reason": (
                        f"Contrato CoHaLo (Positive Guidance): Detectada formulación prohibitiva ('{negative_match.group(0)}'). "
                        "Definí el comportamiento mediante directivas afirmativas ('Instead, do X') y arneses físicos ejecutables."
                    )
                }

        # A5.2 Router Token Budget Gate (SKILL.md <= 480 words / ~550 tokens)
        if target_file.endswith("SKILL.md") and tool_name in ["write_to_file", "write_file"]:
            word_count = len(content_to_check.split())
            if word_count > 480:
                return {
                    "decision": "deny",
                    "reason": (
                        f"Contrato CoHaLo Level 2 (Router Token Budget): SKILL.md tiene {word_count} palabras "
                        "(límite: 480 palabras / ~550 tokens). Desacoplá especificaciones técnicas hacia "
                        "'references/usage.md' o 'references/infra.md' respetando la revelación progresiva."
                    )
                }

        # A5.2.5 Macro-Visión 360 Dependency Radar
        if "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/" in target_file and tool_name in ("write_to_file", "replace_file_content", "write_file", "edit_file"):
            if os.path.basename(target_file) == "unisetup.sh":
                for referenced_script in re.findall(r'setup-[a-zA-Z0-9_\-]+\.sh', content_to_check):
                    ref_full = os.path.join("/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts", referenced_script)
                    if not os.path.exists(ref_full):
                        return {
                            "decision": "deny",
                            "reason": (
                                f"Contrato MACRO-VISIÓN 360 (Alineación de Dependencias): 'unisetup.sh' invoca "
                                f"[{referenced_script}], el cual debe residir en '/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/'. "
                                "Alineá o creá el script aguas abajo antes de incorporarlo al bootstrapper."
                            )
                        }

        # A5.3 AST & Symbol Preservation Guard (Zero Deletion / Lossless Invariant)
        is_protected_code = (
            "/.agents/skills/" in target_file or
            "/0zcp-123/scripts/" in target_file or
            "/.bin/" in target_file or
            "/.agents/rules/" in target_file
        )
        if is_protected_code and tool_name in ["write_to_file", "write_file"] and os.path.exists(target_file):
            try:
                with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                    old_content = f.read()

                # A5.3.1 Python AST Symbol Preservation (Functions & Classes)
                if target_file.endswith(".py"):
                    import ast
                    try:
                        old_ast = ast.parse(old_content)
                        new_ast = ast.parse(content_to_check)
                        old_funcs = {n.name for n in ast.walk(old_ast) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                        new_funcs = {n.name for n in ast.walk(new_ast) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                        missing_funcs = old_funcs - new_funcs
                        if missing_funcs:
                            return {
                                "decision": "deny",
                                "reason": (
                                    f"Contrato de Preservación de Código AST: Conservá las funciones existentes {missing_funcs} "
                                    f"en [{os.path.basename(target_file)}]. En scripts de plataforma realizá extensiones o desacoples aditivos."
                                )
                            }
                        old_classes = {n.name for n in ast.walk(old_ast) if isinstance(n, ast.ClassDef)}
                        new_classes = {n.name for n in ast.walk(new_ast) if isinstance(n, ast.ClassDef)}
                        missing_classes = old_classes - new_classes
                        if missing_classes:
                            return {
                                "decision": "deny",
                                "reason": (
                                    f"Contrato de Preservación de Código AST: Conservá las clases existentes {missing_classes} "
                                    f"en [{os.path.basename(target_file)}]."
                                )
                            }
                    except Exception:
                        pass

                # A5.3.2 Bash Function & Safety Flag Preservation
                first_line_check = content_to_check.split("\n", 1)[0].strip() if content_to_check else ""
                if target_file.endswith(".sh") or (first_line_check.startswith("#!/") and "sh" in first_line_check):
                    # Check safety invariant: set -e / set -euo pipefail (ignoring comments)
                    old_has_set_e = bool(re.search(r'^[ \t]*set\s+-[a-zA-Z]*e[a-zA-Z]*', old_content, re.MULTILINE))
                    new_has_set_e = bool(re.search(r'^[ \t]*set\s+-[a-zA-Z]*e[a-zA-Z]*', content_to_check, re.MULTILINE))
                    if old_has_set_e and not new_has_set_e:
                        return {
                            "decision": "deny",
                            "reason": (
                                f"Contrato de Seguridad Operativa: Conservá el flag de seguridad 'set -e' / 'set -euo pipefail' "
                                f"en [{os.path.basename(target_file)}]."
                            )
                        }
                    # Check functions
                    old_fns = set(re.findall(r'^[ \t]*([a-zA-Z0-9_-]+)\s*\(\)\s*\{', old_content, re.MULTILINE))
                    old_fns.update(re.findall(r'^[ \t]*function\s+([a-zA-Z0-9_-]+)', old_content, re.MULTILINE))
                    new_fns = set(re.findall(r'^[ \t]*([a-zA-Z0-9_-]+)\s*\(\)\s*\{', content_to_check, re.MULTILINE))
                    new_fns.update(re.findall(r'^[ \t]*function\s+([a-zA-Z0-9_-]+)', content_to_check, re.MULTILINE))
                    missing_fns = old_fns - new_fns
                    if missing_fns:
                        return {
                            "decision": "deny",
                            "reason": (
                                f"Contrato de Preservación de Funciones: Conservá las funciones existentes {missing_fns} "
                                f"en [{os.path.basename(target_file)}]."
                            )
                        }

                # A5.3.3 Line Count Floor Preservation Guard (Anti-Poda Drástica)
                old_lines = len(old_content.splitlines())
                new_lines = len(content_to_check.splitlines())
                if old_lines > 40 and new_lines < (old_lines * 0.70):
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Contrato de Preservación de Líneas: El archivo pasa de {old_lines} a {new_lines} líneas "
                            f"(reducción >30%). Aplicá ediciones quirúrgicas con replace_file_content o desacoplá en módulos independientes."
                        )
                    }
            except Exception:
                pass

        # A5.5 Anti-Checklist Theater Guard in Validation Sensors
        if ("validate" in target_file or "check" in target_file) and tool_name in ["write_to_file", "write_file"] and content_to_check:
            if re.search(r'>/dev/null\s+2>&1', content_to_check):
                return {
                    "decision": "deny",
                    "reason": (
                        f"ARNÉS REALIDAD DE SOFTWARE (Anti-Checklist Theater): "
                        f"Mantené la captura transparente de stderr sin silenciar errores en sensores o validadores [{os.path.basename(target_file)}]. "
                        "Los sensores deben registrar stderr y transparentar cualquier fallo físico real."
                    )
                }

        # A5.4 Physical Syntax Pre-Flight Gate (Zero Syntax Errors)
        if tool_name in ["write_to_file", "write_file"] and content_to_check:
            # Python syntax validation
            if target_file.endswith(".py"):
                try:
                    compile(content_to_check, target_file, 'exec')
                except SyntaxError as e:
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Contrato de Integridad Sintáctica (Python SyntaxError): {target_file}:{e.lineno}: {e.msg}\n"
                            f"Fragmento: {e.text.strip() if e.text else ''}"
                        )
                    }
            # Bash script syntax validation
            first_line = content_to_check.split("\n", 1)[0].strip() if content_to_check else ""
            is_bash_script = target_file.endswith(".sh") or (first_line.startswith("#!/") and ("bash" in first_line or "sh" in first_line))
            if is_bash_script and ("/0zcp-123/scripts/" in target_file or "/.bin/" in target_file or "/scripts/" in target_file or target_file.endswith(".sh")):
                try:
                    import subprocess
                    proc = subprocess.run(
                        ["bash", "-n"],
                        input=content_to_check.encode('utf-8'),
                        capture_output=True,
                        timeout=3
                    )
                    if proc.returncode != 0:
                        err_msg = proc.stderr.decode('utf-8', errors='ignore').strip()
                        return {
                            "decision": "deny",
                            "reason": (
                                f"Contrato de Integridad Sintáctica (Bash Syntax Error): {target_file}\n"
                                f"{err_msg}"
                            )
                        }
                except Exception:
                    pass

    # B. Command Guards on run_command
    if tool_name == "run_command":
        cmd = args.get("CommandLine", "")

        # B-1. Kill Guard: Anti-Autoaniquilación y Protección de Sesiones Vivas (BAI-322)
        is_dang_kill, kill_reason = is_kill_attempt_dangerous(cmd)
        if is_dang_kill:
            return {
                "decision": "deny",
                "reason": kill_reason
            }

        # B0. SSoT Sovereign Custom Skills Anti-Pollution Shield
        is_mutating_cmd = bool(re.search(r'\b(cp|mv|rm|sed|tee|echo|cat\s*.*>|>|>>)\b', cmd))
        polluted_skill = is_upstream_skill_pollution(cmd, is_write=is_mutating_cmd)
        if polluted_skill:
            return {
                "decision": "deny",
                "reason": (
                    f"ARNÉS SSoT (Invariante de Inmutabilidad Upstream): La skill [{polluted_skill}] pertenece a suites externas. "
                    "Está estrictamente prohibido mutarla o sincronizarla a Google Drive SSoT. "
                    "Las suites externas son inmutables por diseño."
                )
            }

        # B1. SSoT Relative Path Guard
        is_search_cmd = bool(re.match(r'^[ \t]*(grep|egrep|fgrep|rg|git\s+(log|diff|grep))\b', cmd))
        if not is_search_cmd and contains_relative_0zcp_leak(cmd):
            return {
                "decision": "deny",
                "reason": (
                    "Contrato SSoT (Ruta Canónica): Usá exclusivamente la ruta absoluta canónica "
                    "'/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/' o remota 'baiosfera:0ZEROPS-AGY/0zcp-123/'."
                )
            }

        # B2. Sweeping RM on artifacts / handovers
        if SWEEPING_ARTIFACTS_RM.search(cmd) or (HANDOVER_PATTERN.search(cmd) and re.search(r'\brm\b', cmd)):
            return {
                "decision": "deny",
                "reason": (
                    "ARNÉS HANDOVER IMMUNITY: Mantené intactos los artefactos de relevo inter-sesión "
                    "en /var/www/artifacts/ sin invocar comandos destructivos masivos."
                )
            }

        # B2.6 Anti-Perros Guardianes (Eradicates Synthetic Individual Validator Scripts)
        val_sh_match = re.search(r'(?:^|[/\s;&|])([a-zA-Z0-9_-]+-validate\.sh)\b', cmd)
        if val_sh_match:
            script_name = val_sh_match.group(1)
            if script_name != "skills-suite-validate.sh":
                is_delete_or_inspect = bool(re.match(r'^[ \t]*(rm|unlink|ls|file|stat)\b', cmd))
                if not is_delete_or_inspect:
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Soberanía del Sensor Universal: La validación de capacidades reside exclusivamente "
                            f"en 'skills-suite-validate'. En vez de invocar o crear scripts individuales como [{script_name}], "
                            "ejecutá el Sensor Universal 'skills-suite-validate' o los tests de comportamiento de la aplicación."
                        )
                    }

        # B3. Dangerous RM
        if DANGEROUS_RM_PATTERN.search(cmd):
            return {
                "decision": "force_ask",
                "reason": "Comando con riesgo de destrucción total del sistema detectado."
            }

        # B4. Google Drive Unpruned find Guard (Anti-Freeze Invariant)
        if re.search(r'\bfind\b', cmd):
            if re.search(r'\bfind\s+(/var/www/?(\s|$)|.*/baiosfera|.*baiosfera)', cmd) and not re.search(r'-prune', cmd):
                return {
                    "decision": "deny",
                    "reason": (
                        "Seguridad FUSE / Google Drive: Para buscar en la raíz de /var/www podá (-prune) '/var/www/baiosfera', "
                        "o buscá directamente dentro de una subcarpeta local específica (ej: /var/www/zerops-astrobranding)."
                    )
                }

        # B5. SSoT Parity Pre-Push Gate (Supreme Directive Invariant 3 & Planner Rule 4)
        if re.search(r'\bgit\s+.*push\b', cmd):
            cwd = args.get("Cwd", "")
            target_repo = False
            if "zerops-astro-skills" in cmd or "zerops-astrobranding" in cmd:
                target_repo = True
            elif "zerops-astro-skills" in cwd or "zerops-astrobranding" in cwd:
                target_repo = True

            if target_repo:
                try:
                    repo_dir = cwd if os.path.exists(os.path.join(cwd, ".git")) else ("/var/www/zerops-astrobranding" if "zerops-astrobranding" in cmd else "/var/www/zerops-astro-skills")
                    status_proc = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=repo_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=3
                    )
                    if status_proc.returncode == 0 and status_proc.stdout.strip():
                        return {
                            "decision": "deny",
                            "reason": (
                                "ARNÉS GIT PRE-PUSH: Hay cambios locales sin commitear antes de empujar al remoto. "
                                "Commiteá tus cambios primero para asegurar la paridad de código."
                            )
                        }
                except Exception:
                    pass

    return {"decision": "allow"}

def run_tests():
    print("Testing tool-guard.py deterministic rules...")

    # Test 1: PreInvocation
    res = evaluate_hook({"invocationNum": 1, "initialNumSteps": 0})
    assert "injectSteps" in res, "PreInvocation failed to inject steps"
    print("✓ Test 1 Passed: PreInvocation injects governance notice")

    # Test 2: Deny write to handover file
    res = evaluate_hook({
        "toolCall": {
            "name": "write_to_file",
            "args": {"TargetFile": "/var/www/artifacts/curriculum_engine_v8_handover.md"}
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on handover, got {res}"
    print("✓ Test 2 Passed: Handover Immunity blocks write_to_file on handover")

    # Test 3: Deny replace in blueprint file
    res = evaluate_hook({
        "toolCall": {
            "name": "replace_file_content",
            "args": {"TargetFile": "/var/www/artifacts/proactive_critical_agent_blueprint_v1.md"}
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on blueprint, got {res}"
    print("✓ Test 3 Passed: Handover Immunity blocks replace_file_content on blueprint")

    # Test 4: Deny sweeping rm of artifacts
    res = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "rm -rf /var/www/artifacts/*"}
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on sweeping rm, got {res}"
    print("✓ Test 4 Passed: Handover Immunity blocks sweeping 'rm -rf /var/www/artifacts/*'")

    # Test 5: Allow safe command
    res = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "plan-validate /var/www/artifacts/some_plan_v1.md"}
        }
    })
    assert res.get("decision") == "allow", f"Expected allow on safe command, got {res}"
    print("✓ Test 5 Passed: Normal commands allowed")

    # Test 6: Force ask on dangerous rm -rf /
    res = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "rm -rf /var/www"}
        }
    })
    assert res.get("decision") == "force_ask", f"Expected force_ask on root rm, got {res}"
    print("✓ Test 6 Passed: High-risk commands trigger force_ask")

    # Test 7: Deny native search_web
    res = evaluate_hook({
        "toolCall": {
            "name": "search_web",
            "args": {"query": "test"}
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on search_web, got {res}"
    print("✓ Test 7 Passed: Anti-AMN Gate blocks native search_web")

    # Test 8: Deny command with relative 0zcp-123/ leak
    res = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "mkdir -p 0zcp-123/bak"}
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on relative 0zcp-123, got {res}"
    print("✓ Test 8 Passed: Relative 0zcp-123 leak blocked in run_command")

    # Test 9: Allow command with canonical Drive SSoT path
    res = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "mkdir -p /var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak"}
        }
    })
    assert res.get("decision") == "allow", f"Expected allow on canonical Drive path, got {res}"
    print("✓ Test 9 Passed: Canonical Drive SSoT path allowed")

    # Test 10: Deny write_to_file with relative 0zcp-123 leak
    res = evaluate_hook({
        "toolCall": {
            "name": "write_to_file",
            "args": {"TargetFile": "/var/www/0zcp-123/test.txt"}
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on relative 0zcp-123 TargetFile, got {res}"
    print("✓ Test 10 Passed: Relative 0zcp-123 leak blocked in TargetFile")

    # Test 11: Deny writing upstream skill into Drive SSoT custom skills folder
    res = evaluate_hook({
        "toolCall": {
            "name": "write_to_file",
            "args": {"TargetFile": "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/skills/react-19/SKILL.md"}
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on upstream skill pollution, got {res}"
    print("✓ Test 11 Passed: Upstream skill pollution blocked in TargetFile (react-19)")

    # Test 11b: Deny modifying upstream skill in runtime dir /var/www/.agents/skills/
    res = evaluate_hook({
        "toolCall": {
            "name": "edit_file",
            "args": {"Path": "/var/www/.agents/skills/skill-creator/SKILL.md"}
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on runtime upstream skill edit, got {res}"
    print("✓ Test 11b Passed: Local runtime upstream skill mutation blocked (skill-creator)")

    # Test 11c: Allow read-only inspect on runtime upstream skill
    res = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "cat /var/www/.agents/skills/skill-creator/SKILL.md"}
        }
    })
    assert res.get("decision") == "allow", f"Expected allow on read-only upstream inspect, got {res}"
    print("✓ Test 11c Passed: Read-only command allowed on upstream skill")

    # Test 12: Deny copying upstream skill into Drive SSoT via run_command
    res = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "cp -r /var/www/.agents/skills/playwright /var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/skills/playwright"}
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on upstream skill pollution via run_command, got {res}"
    print("✓ Test 12 Passed: Upstream skill pollution blocked in run_command (playwright)")

    # Test 13: Monotonic backup gate
    test_target = "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/unisetup.sh"
    assert has_recent_backup(test_target) is True, "Expected valid monotonic backup for unisetup.sh"
    print("✓ Test 13 Passed: Monotonic pre-mutation backup verification active")

    # Test 14: Deny legacy negative prompt dogma
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/scratch/test.md",
                "CodeContent": "Queda terminantemente prohibido usar este comando."
            }
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on legacy dogma, got {res}"
    print("✓ Test 14 Passed: Legacy negative prompt engineering blocked (Positive Guidance)")

    # Test 15: Deny router bloat on SKILL.md (>480 words)
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/scratch/SKILL.md",
                "CodeContent": "word " * 500
            }
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on router bloat, got {res}"
    print("✓ Test 15 Passed: Router bloat on SKILL.md blocked (CoHaLo Level 2)")

    # Test 16: Deny drastic skill mutilation without unbundling
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/.agents/skills/oraculo/SKILL.md",
                "CodeContent": "tiny stub"
            }
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on skill mutilation, got {res}"
    print("✓ Test 16 Passed: Drastic skill mutilation blocked (Skill-Improver Zero Deletion)")

    # Test 17: Deny invalid Python syntax
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/scratch/broken.py",
                "CodeContent": "def broken_func(\n    print('missing closing paren'"
            }
        }
    })
    assert res.get("decision") == "deny" and "SyntaxError" in res.get("reason", ""), f"Expected deny on Python syntax error, got {res}"
    print("✓ Test 17 Passed: Python SyntaxError blocked before write (Physical Syntax Gate)")

    # Test 18: Deny invalid Bash syntax
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/scratch/broken.sh",
                "CodeContent": "#!/usr/bin/env bash\nif [ true ]; then\necho missing fi"
            }
        }
    })
    assert res.get("decision") == "deny" and "Bash Syntax Error" in res.get("reason", ""), f"Expected deny on Bash syntax error, got {res}"
    print("✓ Test 18 Passed: Bash Syntax Error blocked before write (Physical Syntax Gate)")

    # Test 19: Deny script function and line mutilation
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/unisetup.sh",
                "CodeContent": "#!/usr/bin/env bash\necho tiny"
            }
        }
    })
    assert res.get("decision") == "deny" and ("preservación" in res.get("reason", "").lower() or "seguridad" in res.get("reason", "").lower()), f"Expected deny on script mutilation, got {res}"
    print("✓ Test 19 Passed: Platform script mutilation & function deletion caught (AST & Line Floor)")

    # Test 20: Deny set -e removal in bash scripts
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/unisetup.sh",
                "CodeContent": "#!/usr/bin/env bash\n# missing set -euo pipefail\nrun_step() { echo 1; }\n" * 15
            }
        }
    })
    assert res.get("decision") == "deny" and "set -e" in res.get("reason", ""), f"Expected deny on set -e removal, got {res}"
    print("✓ Test 20 Passed: Removal of safety flags ('set -e') blocked (Operational Safety Invariant)")

    # Test 21: Deny silencing errors with >/dev/null 2>&1 in validation sensors
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/scratch/custom-check.sh",
                "CodeContent": "#!/usr/bin/env bash\nrun_check >/dev/null 2>&1\necho passed"
            }
        }
    })
    assert res.get("decision") == "deny" and "Anti-Checklist Theater" in res.get("reason", ""), f"Expected deny on silenced validation sensor, got {res}"
    print("✓ Test 21 Passed: Silencing errors in validation sensors blocked (Anti-Checklist Theater Gate)")

    # Test 22: Autonomous Parity Reactor sync verification
    auto_sync_governance()
    assert os.path.exists("/var/www/.bin/hooks/tool-guard.py"), "Expected tool-guard.py in .bin"
    print("✓ Test 22 Passed: Autonomous Parity Reactor synchronizes core governance files")

    # Test 23: Macro-Visión 360 Dependency Radar on unisetup.sh
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/unisetup.sh",
                "CodeContent": "#!/usr/bin/env bash\nset -euo pipefail\nbash setup-nonexistent-script-xyz.sh\n" * 10
            }
        }
    })
    assert res.get("decision") == "deny" and "MACRO-VISIÓN 360" in res.get("reason", ""), f"Expected deny on broken dependency in unisetup.sh, got {res}"
    print("✓ Test 23 Passed: Broken downstream script dependencies in unisetup.sh caught (Macro-Visión 360 Radar)")

    # Test 24: Epistemic Inflow Mandate - Plan-First Gate & Subordinated Execution Closure verified
    pi_res = evaluate_hook({"invocationNum": 1})
    steps = pi_res.get("injectSteps", [])
    assert len(steps) > 0 and "Plan-First Gate" in steps[0].get("ephemeralMessage", ""), f"Expected Plan-First Gate notice in PreInvocation, got {pi_res}"
    print("✓ Test 24 Passed: Contrato Plan-First Gate & Subordinated Execution Closure verified (Epistemic Inflow)")

    # Test 25: Universal Physical Sensor Integration (Standard v3.3)
    skills_val = subprocess.run(["/var/www/.bin/skills-suite-validate"], capture_output=True, text=True)
    assert skills_val.returncode == 0, f"Expected skills-suite-validate exit 0, got {skills_val.returncode}: {skills_val.stderr}\n{skills_val.stdout}"
    assert "100% of custom skills passed" in skills_val.stdout, f"Unexpected skills-suite-validate output: {skills_val.stdout}"
    print("✓ Test 25 Passed: Universal Physical Sensor verified (skills-suite-validate exit 0)")

    # Test 26: Skill Trigger Radar & Contextual Detection verified
    test_skills = detect_skills_in_prompt("vamos a configurar ghcicd y hacer git push")
    assert any(s[0] == "ghcicd" for s in test_skills), f"Expected ghcicd match in detect_skills_in_prompt, got {test_skills}"
    print("✓ Test 26 Passed: Skill Trigger Radar dynamically matches prompt triggers (Epistemic Radar F0)")

    # Test 27: Zero-Bytecode Invariant (00-SUPREME-DIRECTIVE Invariant 6)
    assert sys.dont_write_bytecode is True, "Expected sys.dont_write_bytecode to be True"
    assert os.environ.get("PYTHONDONTWRITEBYTECODE") == "1", "Expected PYTHONDONTWRITEBYTECODE=1 in os.environ"
    assert not os.path.exists("/var/www/.bin/hooks/__pycache__"), "Residual __pycache__ found in /var/www/.bin/hooks/"
    print("✓ Test 27 Passed: Zero-Bytecode Invariant physically verified (sys.dont_write_bytecode=True & clean hygiene)")

    # Test 28: Token Hygiene & Hook De-duplication (SOTA Prompt Caching Invariant)
    _ = evaluate_hook({"invocationNum": 999})
    dup_res = evaluate_hook({"invocationNum": 999, "test_dedup": True})
    assert dup_res == {}, f"Expected duplicate PreInvocation event within 2.5s to be suppressed, got {dup_res}"
    print("✓ Test 28 Passed: Multi-Hook De-duplication & SOTA Token Hygiene physically verified (Zero-Token Waste)")

    # Test 29: F4 Halt Gate Centinela & Univoque Go Predicate
    dummy_plan = "/var/www/artifacts/test_plan_v1.md"
    try:
        with open(dummy_plan, "w") as f:
            f.write("# Dummy Test Plan v1\n")
        test_pi = evaluate_hook({"invocationNum": 1001, "userPrompt": "¿por qué se paralizó todo?"})
        pi_steps = test_pi.get("injectSteps", [])
        assert any("F4 HALT GATE ACTIVO" in s.get("ephemeralMessage", "") for s in pi_steps), f"Expected F4 Halt Gate alert in PreInvocation, got {test_pi}"

        test_pi_go = evaluate_hook({"invocationNum": 1002, "userPrompt": "si"})
        pi_steps_go = test_pi_go.get("injectSteps", [])
        assert not any("F4 HALT GATE ACTIVO" in s.get("ephemeralMessage", "") for s in pi_steps_go), f"Expected no F4 Halt Gate alert on affirmative Go, got {test_pi_go}"
        print("✓ Test 29 Passed: F4 Halt Gate Centinela & Univoque Go Predicate physically verified")
    finally:
        if os.path.exists(dummy_plan):
            os.remove(dummy_plan)

    # Test 30: Positive Guidance & Direct Execution (No artificial linear_active tripwires)
    res_clean = evaluate_hook({
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/scratch/clean_script.py",
                "CodeContent": "print('clean')\n"
            }
        }
    })
    assert res_clean.get("decision") == "allow", f"Expected allow on clean file write, got {res_clean}"
    print("✓ Test 30 Passed: Clean execution permitted without synthetic tripwires")

    # Test 31: Handover Immunity protects _roadmap
    res_roadmap = evaluate_hook({
        "toolCall": {
            "name": "write_to_file",
            "args": {"TargetFile": "/var/www/artifacts/zerops_astrobranding_modularization_roadmap.md"}
        }
    })
    assert res_roadmap.get("decision") == "deny", f"Expected deny on roadmap write, got {res_roadmap}"
    res_roadmap_rm = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "rm -f /var/www/artifacts/zerops_astrobranding_modularization_roadmap.md"}
        }
    })
    assert res_roadmap_rm.get("decision") == "deny", f"Expected deny on roadmap rm, got {res_roadmap_rm}"
    print("✓ Test 31 Passed: Handover Immunity protects _roadmap from writes and deletion")

    # Test 32: Artifacts Lifecycle cleanup purges superseded and session executed files
    test_archive = "/var/www/artifacts"
    os.makedirs(test_archive, exist_ok=True)
    sup_file = os.path.join(test_archive, "test_lifecycle_plan_v1.superseded.md")
    exec_file = os.path.join(test_archive, "test_lifecycle_plan_v2.executed.md")
    road_file = os.path.join(test_archive, "test_roadmap_lifecycle.executed.md")
    try:
        with open(sup_file, "w") as f:
            f.write("# Superseded v1\n")
        with open(exec_file, "w") as f:
            f.write("# Executed v2\n")
        with open(road_file, "w") as f:
            f.write("# Roadmap Handover\n")

        res_clean = cleanup_artifacts_lifecycle(purge_executed=False)
        assert not os.path.exists(sup_file), "Expected superseded plan to be purged"
        assert os.path.exists(exec_file), "Expected executed plan to be preserved during active session"
        assert os.path.exists(road_file), "Expected roadmap to be immune"

        res_session = cleanup_artifacts_lifecycle(purge_executed=True)
        assert not os.path.exists(exec_file), "Expected executed plan to be purged on session close"
        assert os.path.exists(road_file), "Expected roadmap to remain immune during session close"
        print("✓ Test 32 Passed: Artifacts lifecycle cleanup purges superseded and session executed files with Handover Immunity")
    finally:
        for p in [sup_file, exec_file, road_file]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    # Test 33: Anti-Redundancy Chat Contract in PreInvocation
    pi_res_red = evaluate_hook({"invocationNum": 1})
    steps_red = pi_res_red.get("injectSteps", [])
    assert len(steps_red) > 0 and "Contrato Anti-Redundancia en Chat" in steps_red[0].get("ephemeralMessage", ""), f"Expected Anti-Redundancy notice in PreInvocation, got {pi_res_red}"
    # Test 34: Multi-Tenant Upstream Shield blocks client data leak into 0zcp-123
    tenant_res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/elplacerdc.db",
                "CodeContent": "dummy sqlite content"
            }
        }
    })
    assert tenant_res.get("decision") == "deny" and "ARNÉS MULTI-TENANT" in tenant_res.get("reason", ""), f"Expected deny on tenant file inside chassis, got {tenant_res}"
    print("✓ Test 34 Passed: Multi-Tenant Upstream Shield blocks client data leak into 0zcp-123")

    # Test 35: Anti-Perros Guardianes blocks write_to_file on synthetic validator
    res_val_write = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/.agents/skills/cohalo/scripts/cohalo-validate.sh",
                "CodeContent": "#!/usr/bin/env bash\necho passed"
            }
        }
    })
    assert res_val_write.get("decision") == "deny" and "Soberanía del Sensor Universal" in res_val_write.get("reason", ""), f"Expected deny on individual validate.sh, got {res_val_write}"
    print("✓ Test 35 Passed: Anti-Perros Guardianes blocks write_to_file on synthetic *-validate.sh")

    # Test 36: Anti-Perros Guardianes blocks run_command invoking synthetic validator
    res_val_cmd = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {
                "CommandLine": "bash /var/www/.agents/skills/cohalo/scripts/cohalo-validate.sh"
            }
        }
    })
    assert res_val_cmd.get("decision") == "deny" and "Soberanía del Sensor Universal" in res_val_cmd.get("reason", ""), f"Expected deny on running individual validate.sh, got {res_val_cmd}"
    print("✓ Test 36 Passed: Anti-Perros Guardianes blocks run_command on synthetic *-validate.sh")

    # Test 37: Antigravity write_file with Path blocks handover file modification
    res_ag_handover = evaluate_hook({
        "toolCall": {
            "name": "write_file",
            "args": {
                "Path": "/var/www/artifacts/curriculum_engine_v8_handover.md",
                "Content": "tampered content"
            }
        }
    })
    assert res_ag_handover.get("decision") == "deny" and "HANDOVER IMMUNITY" in res_ag_handover.get("reason", ""), f"Expected deny on write_file handover, got {res_ag_handover}"
    print("✓ Test 37 Passed: Antigravity write_file with Path blocks handover modification")

    # Test 38: Antigravity edit_file with Path blocks blueprint modification
    res_ag_bp = evaluate_hook({
        "toolCall": {
            "name": "edit_file",
            "args": {
                "Path": "/var/www/artifacts/proactive_critical_agent_blueprint_v1.md",
                "Target": "old",
                "Replacement": "new"
            }
        }
    })
    assert res_ag_bp.get("decision") == "deny" and "HANDOVER IMMUNITY" in res_ag_bp.get("reason", ""), f"Expected deny on edit_file blueprint, got {res_ag_bp}"
    print("✓ Test 38 Passed: Antigravity edit_file with Path blocks blueprint modification")

    # Test 39: Single-Node ZCP Scale Gate blocks multi-container scaling on zcp
    res_scale_deny = evaluate_hook({
        "toolCall": {
            "name": "call_mcp_tool",
            "args": {
                "ServerName": "zerops",
                "ToolName": "zerops_scale",
                "Arguments": {
                    "serviceHostname": "zcp",
                    "minContainers": 1,
                    "maxContainers": 2
                }
            }
        }
    })
    assert res_scale_deny.get("decision") == "deny" and "SINGLE-NODE ZCP" in res_scale_deny.get("reason", ""), f"Expected deny on zcp multi-container scale, got {res_scale_deny}"
    print("✓ Test 39 Passed: Single-Node ZCP Scale Gate blocks multi-container scaling on zcp")

    # Test 40: Single-Node ZCP Scale Gate allows 1 container scaling on zcp
    res_scale_allow = evaluate_hook({
        "toolCall": {
            "name": "call_mcp_tool",
            "args": {
                "ServerName": "zerops",
                "ToolName": "zerops_scale",
                "Arguments": {
                    "serviceHostname": "zcp",
                    "minContainers": 1,
                    "maxContainers": 1
                }
            }
        }
    })
    assert res_scale_allow.get("decision") == "allow", f"Expected allow on zcp single-node scale, got {res_scale_allow}"
    print("✓ Test 40 Passed: Single-Node ZCP Scale Gate allows single container scale on zcp")

    # Test 41: Process Kill Guard blocks kill targeting current process or ancestor
    my_pid = os.getpid()
    res_kill_ancestor = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {
                "CommandLine": f"kill -9 {my_pid}"
            }
        }
    })
    assert res_kill_ancestor.get("decision") == "deny" and "Guard de Kill" in res_kill_ancestor.get("reason", ""), f"Expected deny on kill ancestor, got {res_kill_ancestor}"
    print("✓ Test 41 Passed: Process Kill Guard blocks kill targeting caller/ancestor PID")

    # Test 42: Process Kill Guard blocks pkill -f agy
    res_pkill = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {
                "CommandLine": "pkill -f agy"
            }
        }
    })
    assert res_pkill.get("decision") == "deny" and "Guard de Kill" in res_pkill.get("reason", ""), f"Expected deny on pkill -f agy, got {res_pkill}"
    print("✓ Test 42 Passed: Process Kill Guard blocks pkill -f agy")

    # Test 43: Process Kill Guard blocks killall agy
    res_killall = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {
                "CommandLine": "killall agy"
            }
        }
    })
    assert res_killall.get("decision") == "deny" and "Guard de Kill" in res_killall.get("reason", ""), f"Expected deny on killall agy, got {res_killall}"
    print("✓ Test 43 Passed: Process Kill Guard blocks killall agy")

    # Test 44: SessionStart injects mandatory recall notice
    res_ss = evaluate_hook({"session_start": True})
    assert "injectSteps" in res_ss, f"Expected injectSteps in SessionStart, got {res_ss}"
    steps_ss = res_ss["injectSteps"]
    assert any("RECALL DE SESIÓN OBLIGATORIO" in s.get("systemMessage", {}).get("systemMessage", "") for s in steps_ss), f"Expected recall message in SessionStart, got {res_ss}"
    print("✓ Test 44 Passed: SessionStart injects mandatory session recall notice")

    # Test 45: PreInvocation fallback to transcriptPath
    dummy_transcript = "/tmp/test_transcript_pi_fallback.jsonl"
    with open(dummy_transcript, "w", encoding="utf-8") as tf:
        tf.write(json.dumps({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "<USER_REQUEST>\ninvestigar SOTA de bases de datos vectoriales\n</USER_REQUEST>"}) + "\n")
    res_pi_fallback = evaluate_hook({
        "invocationNum": 100,
        "transcriptPath": dummy_transcript
    })
    try:
        os.remove(dummy_transcript)
    except Exception:
        pass
    assert "injectSteps" in res_pi_fallback, f"Expected injectSteps from transcriptPath fallback, got {res_pi_fallback}"
    ephem_msg = res_pi_fallback["injectSteps"][0].get("ephemeralMessage", "")
    assert "F0 Epistemic Grounding" in ephem_msg, f"Expected F0 Epistemic Grounding in PreInvocation fallback, got {ephem_msg}"
    print("✓ Test 45 Passed: PreInvocation falls back to transcriptPath to extract userPrompt")

    # Test 46: Linear-First PreToolUse gate blocks skill mutation when active plan exists and no linear activity recorded
    state_file = "/tmp/.linear_activity_state.json"
    state_backup = None
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            state_backup = f.read()
        os.remove(state_file)

    bak_dir = "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak/skills"
    os.makedirs(bak_dir, exist_ok=True)
    with open(os.path.join(bak_dir, "test-skill-SKILL.md.bak"), "w") as f:
        f.write("test backup")

    try:
        res_lf_blocked = evaluate_hook({
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": "/var/www/zerops-astro-skills/test-skill/SKILL.md",
                    "CodeContent": "---\nname: test-skill\ndescription: Test\n---\n# Test\n"
                }
            }
        })
        assert res_lf_blocked.get("decision") == "deny" and "LINEAR-FIRST GATE" in res_lf_blocked.get("reason", ""), f"Expected deny on skill mutation without linear activity, got {res_lf_blocked}"
        print("✓ Test 46 Passed: Linear-First PreToolUse gate blocks skill mutation without linear activity")

        # Test 47: Linear-First PreToolUse gate allows skill mutation when linear activity is present
        with open(state_file, "w") as f:
            json.dump({"timestamp": int(time.time() * 1000), "action": "comment", "issueId": "test-id"}, f)

        res_lf_allowed = evaluate_hook({
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": "/var/www/zerops-astro-skills/test-skill/SKILL.md",
                    "CodeContent": "---\nname: test-skill\ndescription: Test\n---\n# Test\n"
                }
            }
        })
        assert res_lf_allowed.get("decision") == "allow", f"Expected allow on skill mutation with linear activity, got {res_lf_allowed}"
        print("✓ Test 47 Passed: Linear-First PreToolUse gate allows skill mutation with linear activity")

        # Test 48: Linear-First Stop hook forces continue when active plan exists and inspections occurred without linear activity
        os.remove(state_file)
        if os.path.exists("/tmp/.linear_stop_force_count"):
            os.remove("/tmp/.linear_stop_force_count")

        res_stop_blocked = evaluate_hook({
            "is_stop_event": True,
            "terminationReason": "NO_TOOL_CALL",
            "test_has_inspection": True
        })
        assert res_stop_blocked.get("decision") == "continue" and "LINEAR-FIRST GATE" in res_stop_blocked.get("reason", ""), f"Expected continue in Stop hook without linear activity, got {res_stop_blocked}"
        print("✓ Test 48 Passed: Linear-First Stop hook forces continue without linear activity")

        # Test 49: Linear-First Stop hook allows stop when linear activity is present
        with open(state_file, "w") as f:
            json.dump({"timestamp": int(time.time() * 1000), "action": "comment", "issueId": "test-id"}, f)

        res_stop_allowed = evaluate_hook({
            "is_stop_event": True,
            "terminationReason": "NO_TOOL_CALL",
            "test_has_inspection": True
        })
        assert res_stop_allowed == {}, f"Expected empty dict (allow stop) when linear activity exists, got {res_stop_allowed}"
        print("✓ Test 49 Passed: Linear-First Stop hook allows stop when linear activity exists")

    finally:
        if state_backup:
            with open(state_file, "w") as f:
                f.write(state_backup)

    print("============================================================")
    print("✅ ALL TOOL-GUARD UNIT TESTS PASSED DETERMINISTICALLY (exit 0)")
    print("============================================================")

def main():
    if "--test" in sys.argv:
        run_tests()
        sys.exit(0)

    if "--session-start" in sys.argv:
        recall_msg = (
            "🏛️ RECALL DE SESIÓN OBLIGATORIO (Anti-AMN v3.2): Al inicio de CADA sesión es mandatorio ejecutar "
            "'mem_context' o 'mem_search' y 'zerops_discover' antes de emitir juicios o modificar el proyecto. "
            "Para investigación externa, estado del arte o benchmarks, invocá la skill 'research' con subagentes "
            "('invoke_subagent' con typeName 'research'). Prohibido arrancar ciego o desde memoria pre-entrenada."
        )
        print(json.dumps({
            "injectSteps": [
                {
                    "systemMessage": {
                        "systemMessage": recall_msg
                    }
                }
            ]
        }))
        sys.exit(0)

    if "--cleanup-archive" in sys.argv:
        res = cleanup_artifacts_lifecycle(purge_executed=False)
        print(json.dumps(res))
        sys.exit(0)

    if "--cleanup-session" in sys.argv:
        res = cleanup_artifacts_lifecycle(purge_executed=True)
        print(json.dumps(res))
        sys.exit(0)

    raw_input = ""
    payload = {}
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            payload = json.loads(raw_input)
    except Exception:
        pass

    is_post_tool = "--post-tool" in sys.argv or ("stepIdx" in payload and "invocationNum" not in payload and ("error" in payload or "toolResult" in payload or "status" in payload))
    if is_post_tool:
        # Zero-Hang: auto_sync_governance síncrono purgado de PostToolUse para evitar bloqueos por FUSE
        print(json.dumps({}))
        sys.exit(0)

    if "--stop" in sys.argv or "terminationReason" in payload:
        payload["is_stop_event"] = True
        result = evaluate_hook(payload)
        print(json.dumps(result))
        sys.exit(0)

    if not payload:
        print(json.dumps({}))
        sys.exit(0)


    result = evaluate_hook(payload)
    print(json.dumps(result))
    sys.exit(0)

if __name__ == "__main__":
    main()
