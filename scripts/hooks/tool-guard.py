#!/usr/bin/env python3
"""
tool-guard.py — Native Antigravity Process-Level Gatekeeper & Anti-Sycophancy Harness
Version: 3.2 (Antigravity Native Tools, SessionStart Recall, Safe Process Kill & Single-Node Scale Gate)
Execution: <30ms | Zero External Dependencies | 100% Deterministic
Intercepts PreToolUse, PreInvocation, and SessionStart events to enforce:
  1. Handover Immunity (Strict block against destroying or truncating handover files).
  2. Anti-Afán & Anti-AMN Inflow Gate (Enforces prior inspection/grounding before mutations).
  3. Dangerous Command Guard (Blocks blind sweeping deletes and prompts for high-risk ops).
  4. Upstream Isolation Shield (Blocks tenant keys/db/secrets leaks inside sovereign upstream repos).
  5. Epistemic Grounding First Gate (Enforces research before skill or formal F4 plan creation).
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
import shlex
import shutil

HANDOVER_PATTERN = re.compile(r'(_handover|_blueprint|_dossier|_roadmap)', re.IGNORECASE)
DANGEROUS_RM_PATTERN = re.compile(r'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-f?[a-zA-Z]*r[a-zA-Z]*)\s+(/|/\*|/var|/var/\*|/var/www|/var/www/\*)(\s|$)', re.IGNORECASE)
SWEEPING_ARTIFACTS_RM = re.compile(r'rm\s+.*artifacts/(\*|\.\*)', re.IGNORECASE)

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
    """Detects attempts to write, copy, or mutate external gentle-ai/pocock skills into sovereign skills dirs."""
    protected_prefixes = ("/var/www/zerops-astro-skills", "/var/www/.agents/skills", "/var/www/.claude/skills")
    if is_write and any(p in path_or_cmd for p in protected_prefixes):
        for token in re.split(r'[/ \t\n\'"]+', path_or_cmd):
            token_clean = token.strip()
            if UPSTREAM_SKILLS_PATTERN.match(token_clean):
                return token_clean
    return ""

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


class BashCommandNode:
    """Represents an extracted shell command invocation and its parsed arguments."""
    def __init__(self, command: str, args: list, raw: str):
        self.command = command
        self.args = args
        self.raw = raw

    def __repr__(self):
        return f"BashCommandNode(cmd={self.command}, args={self.args})"

class BashCommandParser:
    """
    Parses a shell command string into a list of executed command invocations (BashCommandNode),
    correctly handling quotes, subshells, chained operators (&&, ||, ;, |, &), and redirections.
    Prevents false positives on string literals (e.g., git commit -m "rm -rf ...").
    """
    COMMAND_SEPARATORS = {";", "&&", "||", "|", "&", "|&", "\n"}
    REDIRECT_TOKENS = {">", ">>", "<", "<<", ">&", "<&"}
    WRAPPER_COMMANDS = {"sudo", "env", "nohup", "exec", "builtin"}

    @classmethod
    def parse(cls, command_line: str) -> list:
        if not command_line or not command_line.strip():
            return []

        try:
            lexer = shlex.shlex(command_line, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            lexer.commenters = ""
            tokens = list(lexer)
        except Exception:
            tokens = command_line.split()

        commands = []
        current = []

        for tok in tokens:
            if tok in cls.COMMAND_SEPARATORS:
                cls._process_segment(current, commands)
                current = []
            else:
                current.append(tok)
        cls._process_segment(current, commands)

        return commands

    @classmethod
    def _process_segment(cls, toks: list, commands: list):
        if not toks:
            return

        filtered = []
        i = 0
        n = len(toks)
        while i < n:
            t = toks[i]
            # Case 1: redirect token followed by target: e.g. '>', '/tmp/out.txt'
            if t in cls.REDIRECT_TOKENS:
                i += 1
                if i < n:
                    i += 1
                continue
            # Case 2: fd followed by redirection, e.g. '2', '>&', '1' or '2', '>', '/dev/null'
            if t.isdigit() and i + 1 < n and toks[i+1] in cls.REDIRECT_TOKENS:
                i += 2
                if i < n:
                    i += 1
                continue
            # Case 3: single token redirection with attached target like >file or 2>file
            if any(t.startswith(op) and len(t) > len(op) for op in [">", "<", "2>", "&>", "1>"]):
                i += 1
                continue

            filtered.append(t)
            i += 1

        if not filtered:
            return

        idx = 0
        # Skip wrappers, env assignments (FOO=bar), and timeout
        while idx < len(filtered):
            tok = filtered[idx]
            if tok in cls.WRAPPER_COMMANDS:
                idx += 1
                continue
            elif "=" in tok and not tok.startswith("-"):
                idx += 1
                continue
            elif tok == "timeout":
                idx += 1
                while idx < len(filtered) and (filtered[idx].startswith("-") or filtered[idx].isdigit() or filtered[idx].endswith("s") or filtered[idx].endswith("m")):
                    idx += 1
                continue
            break

        if idx >= len(filtered):
            return

        cmd_name = os.path.basename(filtered[idx])
        cmd_args = filtered[idx+1:]
        node = BashCommandNode(cmd_name, cmd_args, " ".join(filtered))
        commands.append(node)

        # Handle nested commands in bash -c "..." or sh -c '...'
        if cmd_name in {"bash", "sh", "zsh"}:
            for j, arg in enumerate(cmd_args):
                if arg == "-c" and j + 1 < len(cmd_args):
                    sub_cmds = cls.parse(cmd_args[j+1])
                    commands.extend(sub_cmds)
                    break
        elif cmd_name == "find":
            if "-exec" in cmd_args:
                exec_idx = cmd_args.index("-exec")
                exec_toks = []
                for a in cmd_args[exec_idx+1:]:
                    if a in {";", "+", "\\;"}:
                        break
                    if a != "{}":
                        exec_toks.append(a)
                if exec_toks:
                    cls._process_segment(exec_toks, commands)

def get_runtime_capabilities() -> dict:
    """
    Dynamically probes runtime capabilities without hardcoding SemVer or agent binary names.
    """
    binaries = set()
    for candidate in ["agy", "antigravity", "gemini-cli", "claude"]:
        p = shutil.which(candidate)
        if p:
            binaries.add(candidate)
            try:
                real = os.path.basename(os.path.realpath(p))
                if real:
                    binaries.add(real)
            except Exception:
                pass

    try:
        ancestors = get_process_ancestors()
        for apid in ancestors:
            ainfo = get_process_info(apid)
            comm = ainfo.get("comm", "")
            if comm:
                binaries.add(comm)
    except Exception:
        pass

    if not binaries:
        binaries = {"agy", "antigravity"}

    ls_version = os.environ.get("ANTIGRAVITY_LS_VERSION") or os.environ.get("GEMINI_CLI_VERSION") or ""
    return {
        "agent_binaries": binaries,
        "ls_version": ls_version,
        "has_subagents": True,
        "is_single_node": True
    }

def get_physical_environment_state() -> dict:
    """
    Sonda en microsegundos el estado físico del entorno para erradicar AMN estocástica.
    Verifica presencia de storage, volumenes y configuración local de Zerops.
    """
    has_localstorage = os.path.exists("/var/www/localstorage") or os.path.exists("/mnt/localstorage")
    services = ["zcp"]
    if has_localstorage:
        services.append("localstorage")

    proj_name = os.environ.get("ZEROPS_PROJECT_NAME") or os.environ.get("PROJECT_NAME") or ""
    if not proj_name and os.path.exists("/var/www/zerops-astrobranding/templates/plantilla-universal-web-zerops-v4.md"):
        proj_name = "zerops-astrobranding"

    return {
        "has_localstorage": has_localstorage,
        "services": services,
        "proj_name": proj_name
    }

def is_kill_attempt_dangerous(cmd: str) -> tuple:
    """
    Guard de Kill Soberano (BAI-322 & BAI-421):
    Deniega kill/pkill/killall cuyo objetivo sea:
    1. Un proceso del agente con TTY activo (sesión interactiva viva detectada por capacidades).
    2. Un ancestro de la invocación actual.
    3. Un pkill -f cuyo patrón coincida con la propia shell o un ancestro.
    Decide en tiempo real consultando /proc y get_runtime_capabilities(), nunca por PIDs fijos o nombres hardcodeados.
    Utiliza BashCommandParser para eliminar falsos positivos en strings o argumentos.
    """
    if not re.search(r'\b(kill|pkill|killall)\b', cmd):
        return False, ""

    nodes = BashCommandParser.parse(cmd)
    kill_nodes = [n for n in nodes if n.command in {"kill", "pkill", "killall"}]
    if not kill_nodes:
        return False, ""

    ancestors = get_process_ancestors()
    ancestor_cmdlines = []
    for apid in ancestors:
        ainfo = get_process_info(apid)
        if ainfo["cmdline"]:
            ancestor_cmdlines.append(ainfo["cmdline"])

    runtime_caps = get_runtime_capabilities()
    protected_binaries = runtime_caps["agent_binaries"]

    for node in kill_nodes:
        base_bin = node.command
        args_list = node.args

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
                if any(b in pinfo["cmdline"] or pinfo["comm"] == b for b in protected_binaries) and pinfo["tty"]:
                    return True, (
                        f"ARNÉS DE PROCESOS (Guard de Kill): Se denegó 'kill' sobre el PID {tpid} ({pinfo['comm']}). "
                        f"El proceso es una sesión interactiva viva del agente con TTY asignado ({pinfo['tty']})."
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

            # Check if pattern matches any live agent with TTY in /proc
            for pdir in glob_pids():
                pinfo = get_process_info(pdir)
                if any(b in pinfo["cmdline"] or pinfo["comm"] == b for b in protected_binaries) and pinfo["tty"]:
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
                if any(tgt == b or b in tgt for b in protected_binaries):
                    for pdir in glob_pids():
                        pinfo = get_process_info(pdir)
                        if any(b in pinfo["cmdline"] or pinfo["comm"] == b for b in protected_binaries) and pinfo["tty"]:
                            return True, (
                                f"ARNÉS DE PROCESOS (Guard de Kill): Se denegó 'killall {tgt}'. "
                                f"Hay sesiones interactivas vivas del agente con TTY ({pinfo['tty']})."
                            )

    return False, ""

def is_plan_draft(filepath: str) -> bool:
    try:
        if not filepath or not os.path.exists(filepath):
            return False
        base = os.path.basename(filepath).lower()
        if base.startswith("draft_") or "draft" in base or "grilling" in base:
            return True
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(4096).lower()
            if any(k in content for k in [
                "status: draft", "status: grilling", "estado: borrador",
                "estado: f0", "estado: f1", "fase: f0", "fase: f1",
                "f0 epistemic grounding & grilling", "draft: true", "borrador: true"
            ]):
                return True
    except Exception:
        pass
    return False

def is_plan_approved(filepath: str) -> bool:
    try:
        if not filepath or not os.path.exists(filepath):
            return False
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(4096).lower()
            if any(k in content for k in [
                "status: approved", "estado: aprobado", "approved: true"
            ]):
                return True
    except Exception:
        pass
    return False

def get_pending_research_subagents(transcript_path: str) -> list:
    if not transcript_path or not os.path.exists(transcript_path):
        return []
    launched_research = {}
    completed = set()
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    step = json.loads(line)
                except Exception:
                    continue
                
                content = step.get("content", "")
                if "Created the following subagent:" in content:
                    m = re.search(r"\"conversationId\":\s*\"([^\"]+)\"", content)
                    if m:
                        cid = m.group(1)
                        launched_research[cid] = True
                
                if "sender=" in content:
                    m = re.search(r"sender=([0-9a-fA-F\-]{36})", content)
                    if m:
                        completed.add(m.group(1))
                
                if "Successfully killed" in content:
                    for cid in list(launched_research.keys()):
                        completed.add(cid)
    except Exception:
        pass
    
    pending = [cid for cid in launched_research if cid not in completed]
    return pending

def extract_user_prompt(payload: dict) -> str:
    user_prompt = payload.get("test_user_prompt") or payload.get("userPrompt") or payload.get("lastUserInput") or ""
    if user_prompt:
        return user_prompt
    common = payload.get("common", {})
    if isinstance(common, dict):
        user_prompt = common.get("lastUserInput") or common.get("userPrompt") or ""
        if user_prompt:
            return user_prompt
    stop_args = payload.get("stopHookArgs", {})
    if isinstance(stop_args, dict):
        user_prompt = stop_args.get("lastUserInput") or ""
        if user_prompt:
            return user_prompt
    transcript_path = payload.get("transcriptPath", "") or (common.get("transcriptPath") if isinstance(common, dict) else "")
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
                                    return user_prompt
                    except Exception:
                        pass
        except Exception:
            pass
    return ""

ENGRAM_WRITE_TOOLS = {
    "mem_save",
    "mem_session_summary",
    "mem_update",
    "mem_delete",
    "mem_capture_passive",
    "mem_save_prompt",
    "mem_session_end",
    "mem_merge_projects",
}

def trigger_engram_background_sync(payload: dict, source: str = "post_tool") -> bool:
    """
    Spawns non-blocking background 'engram-sync --push --quiet' (<2ms overhead)
    so every Engram write tool and turn completion atomically flushes local POSIX Hot DB
    out to Zerops LocalStorage (Warm) and Google Drive SSoT (Cold).
    """
    if "--test" in sys.argv or payload.get("test_mode"):
        return True

    sync_candidates = [
        "/usr/local/bin/engram-sync",
        "/var/www/.bin/engram-sync",
        "/var/www/zerops-astrobranding/scripts/engram-sync",
    ]
    sync_bin = next((c for c in sync_candidates if os.path.isfile(c) and os.access(c, os.X_OK)), None)
    if not sync_bin:
        return False

    try:
        subprocess.Popen(
            [sync_bin, "--push", "--quiet"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except Exception:
        return False

RESEARCH_STATE_FILE = "/tmp/.research_grounding_state.json"

RESEARCH_DISCOVERY_SERVERS = {"context7", "exa", "tavily", "jina", "firecrawl", "brave", "duckduckgo"}

RESEARCH_VERBATIM_TOOLS = {
    "read_url", "extract_pdf", "guess_datetime_url", "query-docs",
    "web_fetch_exa", "tavily_extract", "firecrawl_scrape",
    "firecrawl_extract", "firecrawl_research_read_paper", "firecrawl_research_inspect_paper"
}

RESEARCH_MANDATE_PATTERNS = re.compile(
    r'(?i)(?:\b(?:meta-research|estado del arte|sota|anti-amn|sin amn|memoria preentrenada|'
    r'investig[aáe]|investiguen|benchmark|breaking changes?|versi[oó]n actual|[uú]ltima versi[oó]n|'
    r'documentaci[oó]n oficial)\b|\bresearch\b.*?\b(?:en vivo|web|api|sota|fuentes?|mcp|docs?)\b)'
)

RESEARCH_TRANSCRIPT_ANY_TOKENS = (
    "web_search_exa", "web_fetch_exa", "tavily_search", "tavily_extract", "tavily_map",
    "brave_web_search", "duckduckgo_web_search", "context7", "firecrawl",
    '"ServerName": "jina"', '"ServerName":"jina"', "read_url", "extract_pdf",
    "r.jina.ai", "s.jina.ai", '"TypeName": "research"', '"TypeName":"research"', '"typeName": "research"'
)

RESEARCH_TRANSCRIPT_VERBATIM_TOKENS = (
    "read_url", "extract_pdf", "r.jina.ai", "query-docs", "web_fetch_exa",
    "tavily_extract", "firecrawl_scrape", "firecrawl_extract",
    "firecrawl_research_read_paper", '"TypeName": "research"', '"TypeName":"research"', '"typeName": "research"'
)

def _record_research_state(source: str, detail: str, phase: str) -> None:
    """Persist live epistemic activity (discovery vs verbatim) with 2h merge window."""
    now_ms = int(time.time() * 1000)
    prev = {}
    if os.path.exists(RESEARCH_STATE_FILE):
        try:
            with open(RESEARCH_STATE_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if time.time() - (loaded.get("timestamp", 0) / 1000.0) < 7200:
                    prev = loaded
        except Exception:
            prev = {}
    data = {
        "timestamp": now_ms,
        "source": source,
        "detail": detail,
        "phase": phase,
        "has_discovery": bool(prev.get("has_discovery") or phase in ("discovery", "subagent")),
        "has_verbatim": bool(prev.get("has_verbatim") or phase in ("verbatim", "subagent")),
    }
    try:
        with open(RESEARCH_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def _inspect_turn_research(payload: dict) -> tuple:
    """Inspect current turn (since last USER_INPUT) for live research & verbatim reads."""
    if "test_has_research_in_turn" in payload or "test_has_verbatim_in_turn" in payload:
        return bool(payload.get("test_has_research_in_turn", False)), bool(payload.get("test_has_verbatim_in_turn", False)), True

    transcript_path = payload.get("transcriptPath", "") or payload.get("common", {}).get("transcriptPath", "")
    if not transcript_path or not os.path.exists(transcript_path):
        return False, False, bool(payload.get("test_force_research_stop", False))

    has_any = False
    has_verbatim = False
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            t_lines = f.readlines()
        for tl in reversed(t_lines):
            if '"type":"USER_INPUT"' in tl or '"type": "USER_INPUT"' in tl or '"source":"USER_EXPLICIT"' in tl or '"source": "USER_EXPLICIT"' in tl:
                break
            if any(tok in tl for tok in RESEARCH_TRANSCRIPT_ANY_TOKENS):
                has_any = True
            if any(tok in tl for tok in RESEARCH_TRANSCRIPT_VERBATIM_TOKENS):
                has_verbatim = True
            if has_any and has_verbatim:
                break
    except Exception:
        pass
    return has_any, has_verbatim, True

def _extract_zerops_discover_obj(tool_res):
    """Unwrap direct JSON dicts, strings, or MCP content wrappers into a zerops_discover dict."""
    candidates = [tool_res]
    while candidates:
        cur = candidates.pop(0)
        if not cur:
            continue
        if isinstance(cur, str):
            try:
                cur = json.loads(cur)
            except Exception:
                m = re.search(r'\{[\s\S]*"services"[\s\S]*\}', cur)
                if m:
                    try:
                        cur = json.loads(m.group(0))
                    except Exception:
                        cur = None
                else:
                    cur = None
        if isinstance(cur, dict):
            if "services" in cur and isinstance(cur["services"], list):
                return cur
            for key in ("result", "output", "toolResult", "data"):
                if key in cur and cur[key] is not None:
                    candidates.append(cur[key])
            content = cur.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("text"):
                        candidates.append(item["text"])
                    elif isinstance(item, str):
                        candidates.append(item)
    return None

def _read_zerops_discover_from_transcript(transcript_path, step_idx=None):
    """Extract zerops_discover JSON from transcript.jsonl (or transcript_full.jsonl on truncation)."""
    if not transcript_path or not os.path.exists(transcript_path):
        return None
    full_path = os.path.join(os.path.dirname(transcript_path), "transcript_full.jsonl")
    target_path = full_path if os.path.exists(full_path) else transcript_path
    try:
        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            recent = f.readlines()[-200:]
        for idx_pass in (True, False):
            if idx_pass and step_idx is None:
                continue
            for raw_line in reversed(recent):
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    entry = json.loads(raw_line)
                except Exception:
                    continue
                if idx_pass and entry.get("step_index") != step_idx:
                    continue
                if entry.get("type") != "GENERIC":
                    continue
                content = entry.get("content", "")
                if '"services"' in str(content) and '"serviceId"' in str(content):
                    obj = _extract_zerops_discover_obj(content)
                    if obj:
                        return obj
    except Exception:
        pass
    return None

def evaluate_hook(payload: dict) -> dict:
    # 0. SessionStart Handling (Mandatory Anti-AMN Recall with Multi-Hook Deduplication)
    if payload.get("session_start") or payload.get("event") == "SessionStart" or payload.get("hookType") == "SessionStart":
        ss_lock = "/tmp/.tool_guard_session_start.lock"
        now_ts = time.time()
        is_dedup = False
        if os.path.exists(ss_lock) and not payload.get("test_force_session_start") and "--test" not in sys.argv:
            try:
                with open(ss_lock, "r") as f:
                    last_ss = float(f.read().strip())
                    if (now_ts - last_ss) < 10.0:
                        is_dedup = True
            except Exception:
                pass
        if is_dedup:
            return {}
        try:
            with open(ss_lock, "w") as f:
                f.write(str(now_ts))
        except Exception:
            pass

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

    # 0.5 Stop Event Handling (Antigravity Stop Contract: decision='continue' | {})
    if "terminationReason" in payload or payload.get("is_stop_event") or "stopHookArgs" in payload:
        if payload.get("continuationActive"):
            return {}
        term_reason = payload.get("terminationReason") or payload.get("stopHookArgs", {}).get("terminationReason") or "NO_TOOL_CALL"
        if term_reason == "NO_TOOL_CALL":
            transcript_path = payload.get("transcriptPath", "") or payload.get("common", {}).get("transcriptPath", "")
            pending_subagents = get_pending_research_subagents(transcript_path) if not payload.get("test_bypass_research_wait") else []
            if payload.get("test_has_pending_research"):
                pending_subagents = ["subagent-test-pending"]

            if pending_subagents:
                has_grilling_or_conclusion = False
                if transcript_path and os.path.exists(transcript_path):
                    try:
                        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                            t_lines = f.readlines()
                            for l in reversed(t_lines[-5:]):
                                if any(k in l for k in ["❓ **Q", "### Ronda", "Ronda 1", "Estructura Creada", "Tickets BAI", "Master Plan:"]):
                                    has_grilling_or_conclusion = True
                                    break
                    except Exception:
                        pass
                if payload.get("test_has_grilling_in_stop"):
                    has_grilling_or_conclusion = True

                if has_grilling_or_conclusion:
                    return {
                        "decision": "continue",
                        "reason": (
                            f"🏛️ MANDATO DE ESPERA EPISTÉMICA F0 (Supreme Directive Invariante 5): "
                            f"Hay subagentes de 'research' activos en vuelo ({pending_subagents}). "
                            "Esperá a recibir e ingerir los reportes de todos los subagentes antes de concluir."
                        )
                    }

        triggered_stop_sync = trigger_engram_background_sync(payload, source="stop")
        if payload.get("test_inspect_engram_sync"):
            return {"engramSyncTriggered": triggered_stop_sync, "source": "stop"}
        return {}

    # 1. PostToolUse Handling (Engram Auto-Sync & Zerops Cache — agy expects {})
    if payload.get("is_post_tool") or ("stepIdx" in payload and "invocationNum" not in payload and ("error" in payload or "toolResult" in payload or "status" in payload)):
        tool_call = payload.get("toolCall", {})
        tool_args = tool_call.get("args", {})

        # 1a. Non-blocking Engram 3-Tier Push on MCP Memory Mutations (BAI-425)
        if tool_call.get("name") == "call_mcp_tool":
            mcp_srv = str(tool_args.get("ServerName", "")).strip().lower()
            mcp_tool = str(tool_args.get("ToolName", "")).strip()
            if mcp_srv == "engram" and mcp_tool in ENGRAM_WRITE_TOOLS:
                triggered_mcp_sync = trigger_engram_background_sync(payload, source=f"post_tool:{mcp_tool}")
                if payload.get("test_inspect_engram_sync"):
                    return {"engramSyncTriggered": triggered_mcp_sync, "source": f"post_tool:{mcp_tool}"}
                return {}
            if mcp_srv == "zerops" and mcp_tool == "zerops_discover":
                tool_res = payload.get("toolResult") or payload.get("result") or ""
                try:
                    res_obj = _extract_zerops_discover_obj(tool_res) if tool_res else _read_zerops_discover_from_transcript(
                        payload.get("transcriptPath"), payload.get("stepIdx")
                    )
                    if res_obj:
                        with open("/tmp/.zerops_discover_cache.json", "w") as f:
                            json.dump(res_obj, f, indent=2)
                except Exception:
                    pass
            if payload.get("test_inspect_engram_sync"):
                return {"engramSyncTriggered": False, "source": f"ignored:{mcp_srv}:{mcp_tool}"}
        return {}

    # 2. PreInvocation Handling (Zero-Spam F4 Halt Gate via valid systemMessage)
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

        last_inv = last_state.get("invocationNum")
        last_ts = last_state.get("ts", 0)
        if not payload.get("test_bypass_dedup"):
            if payload.get("test_dedup") or (last_inv is not None and inv_num == last_inv and (now_ts - last_ts) < 3.0) or ((now_ts - last_ts) < 2.0 and inv_num == 0):
                return {}

        try:
            with open(state_file, "w") as f:
                json.dump({"invocationNum": inv_num, "ts": now_ts}, f)
        except Exception:
            pass

        user_prompt = extract_user_prompt(payload)
        plans_dir = "/var/www/artifacts/plans"
        has_pending_master_plan = (
            os.path.exists(plans_dir) and any(
                f.endswith(".md") and not any(x in f.lower() for x in [".executed.", ".superseded.", "report", ".test_hide", "draft", "grilling"])
                and not is_plan_draft(os.path.join(plans_dir, f))
                and not is_plan_approved(os.path.join(plans_dir, f))
                for f in os.listdir(plans_dir)
            )
        ) or os.path.exists("/var/www/artifacts/test_plan_v1.md")

        if has_pending_master_plan and user_prompt:
            has_question = ("?" in user_prompt or "¿" in user_prompt)
            has_go = bool(re.search(r'\b(go|adelante|procede|ejecuta|ejecutá|aprobado|dale|si|sí)\b', user_prompt, re.IGNORECASE))
            if has_question or not has_go:
                halt_alert = "⏸️ F4 HALT GATE ACTIVO: Plan maestro pendiente de aprobación ('Go'). No inicies implementación hasta confirmación explícita."
                return {
                    "injectSteps": [
                        {
                            "systemMessage": {
                                "systemMessage": halt_alert
                            }
                        }
                    ]
                }

        if user_prompt and RESEARCH_MANDATE_PATTERNS.search(user_prompt) and not payload.get("test_bypass_research_nudge"):
            res_fresh = False
            if os.path.exists(RESEARCH_STATE_FILE):
                try:
                    with open(RESEARCH_STATE_FILE, "r", encoding="utf-8") as rf:
                        r_data = json.load(rf)
                        if (time.time() - (r_data.get("timestamp", 0) / 1000.0)) < 1800 and r_data.get("has_verbatim", True):
                            res_fresh = True
                except Exception:
                    pass
            if not res_fresh:
                return {
                    "injectSteps": [
                        {
                            "systemMessage": {
                                "systemMessage": (
                                    "🏛️ ANTI-AMN ACTIVO (research F0–F3): Groundeá con 'context7' / 'exa' / 'tavily' + "
                                    "'jina:read_url' (fallbacks F2: 'brave' -> 'duckduckgo') o subagente 'research' antes de emitir afirmaciones técnicas."
                                )
                            }
                        }
                    ]
                }

        return {}

    # 2. PreToolUse Handling
    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    # 0.05 Epistemic Activity Recorder (Records live research execution across discovery & verbatim tiers)
    if tool_name == "invoke_subagent":
        type_name = str(args.get("TypeName", "")).lower()
        prompt_txt = str(args.get("Prompt", "")).lower()
        if type_name in ("research", "meta-research") or any(k in prompt_txt for k in ["research", "investig", "benchmark", "sota", "api", "docs"]):
            _record_research_state("invoke_subagent", type_name or "research", "subagent")
    elif tool_name == "call_mcp_tool":
        server = str(args.get("ServerName", "")).lower()
        mcp_tool = str(args.get("ToolName", "")).lower()
        if server in RESEARCH_DISCOVERY_SERVERS or any(k in mcp_tool for k in ["search", "docs", "scrape", "crawl", "fetch", "read_url", "extract_pdf"]):
            phase = "verbatim" if mcp_tool in RESEARCH_VERBATIM_TOOLS else "discovery"
            _record_research_state("call_mcp_tool", f"{server}:{mcp_tool}", phase)
    elif tool_name == "run_command":
        cmd_raw = str(args.get("CommandLine", ""))
        if "r.jina.ai/" in cmd_raw:
            _record_research_state("run_command", "curl:r.jina.ai", "verbatim")
        elif "s.jina.ai/" in cmd_raw:
            _record_research_state("run_command", "curl:s.jina.ai", "discovery")

    # 0. Anti-AMN & F0 Epistemic Inflow: Enrutamiento afirmativo hacia skill research
    if tool_name == "search_web":
        return {
            "decision": "deny",
            "reason": (
                "Contrato Epistémico F0 (Anti-AMN): Para investigación y grounding en vivo, ejecutá "
                "exclusivamente la skill 'research' mediante 'call_mcp_tool' "
                "(primarios: context7, exa, tavily, jina, firecrawl; fallbacks: brave, duckduckgo) "
                "o mediante subagente 'invoke_subagent' (TypeName: 'research')."
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

    # 0.2 Epistemic Inflow Wait (Anti-Rushing Gate: Wait for subagent research reports before planning/ticketing)
    transcript_path = payload.get("transcriptPath", "")
    pending_research = get_pending_research_subagents(transcript_path) if not payload.get("test_bypass_research_wait") else []
    if payload.get("test_has_pending_research"):
        pending_research = ["subagent-test-pending"]

    if pending_research:
        target_file_check = args.get("Path", "") or args.get("TargetFile", "") or args.get("target_file", "") or args.get("file_path", "")
        if tool_name in ["write_file", "edit_file", "write_to_file", "replace_file_content"]:
            if "/artifacts/plans/" in target_file_check or target_file_check.startswith("artifacts/plans/"):
                return {
                    "decision": "deny",
                    "reason": (
                        f"🏛️ MANDATO DE ESPERA EPISTÉMICA F0 (Supreme Directive Invariante 5): "
                        f"Hay subagentes de 'research' activos en vuelo ({pending_research}). Está terminantemente "
                        "PROHIBIDO apresurarse a redactar o mutar planes antes de recibir e ingerir los reportes de investigación "
                        "de todos los subagentes delegados. Finalizá tu turno sin tool calls para aguardar el retorno del subagente."
                    )
                }
        if tool_name == "run_command":
            cmd_check = args.get("CommandLine", "")
            if any(k in cmd_check for k in ["linear-cli create", "linear-cli create-project"]):
                return {
                    "decision": "deny",
                    "reason": (
                        f"🏛️ MANDATO DE ESPERA EPISTÉMICA F0 (Supreme Directive Invariante 5): "
                        f"Hay subagentes de 'research' activos en vuelo ({pending_research}). Está terminantemente "
                        "PROHIBIDO crear proyectos o tickets en Linear antes de recibir e ingerir sus reportes de investigación. "
                        "Aguardá la culminación de los subagentes antes de formalizar issues."
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

        # 0.25 Invariante Linear-First Multi-Servicio & Bootstrap (BAI-430 / Supreme Directive Invariante 2)
        if args.get("ToolName") in ["zerops_import", "zerops_workflow"]:
            wf_args = args.get("Arguments", {})
            wf_action = wf_args.get("action")
            wf_name = wf_args.get("workflow")
            is_bootstrap = (args.get("ToolName") == "zerops_import") or (wf_action == "start" and wf_name in ["bootstrap", "launch-production"])
            if is_bootstrap and not payload.get("test_bypass_linear"):
                state_file = "/tmp/.linear_activity_state.json"
                alt_state_file = "/var/www/artifacts/.linear_activity_state.json"
                has_linear_recent = False
                for sf in [state_file, alt_state_file]:
                    if os.path.exists(sf):
                        try:
                            with open(sf, "r") as f:
                                l_data = json.load(f)
                                l_ts = l_data.get("timestamp", 0)
                                if time.time() * 1000 - l_ts < 24 * 3600 * 1000:
                                    has_linear_recent = True
                                    break
                        except Exception:
                            pass
                if not has_linear_recent:
                    return {
                        "decision": "deny",
                        "reason": (
                            "🏛️ VIOLACIÓN LINEAR-FIRST MULTI-SERVICIO (Supreme Directive Invariante 2 & meta-plan): "
                            "El aprovisionamiento de infraestructura o importación multi-servicio en Zerops exige "
                            "haber registrado previamente el proyecto o tickets atómicos en Linear ('linear-cli create-project' "
                            "o 'linear-cli create \"BAI: <servicio>\"'). Queda prohibido mutar topología a ciegas en el chat "
                            "sin persistencia física en Linear para evitar saturación de tokens y amnesia."
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

        # A1.1 Multi-Tenant & Sovereign Upstream Isolation Shield
        for upstream_prefix in ("/var/www/zerops-astrobranding/", "/var/www/zerops-astro-skills/"):
            if target_file.startswith(upstream_prefix):
                rel_to_upstream = target_file[len(upstream_prefix):]
                base_name = os.path.basename(rel_to_upstream).lower()
                is_secret_or_db = (
                    any(base_name.endswith(ext) for ext in [".db", ".sqlite", "-keys.md", "_keys.md"])
                    or (base_name.endswith(".env") and base_name not in [".env.example", "env-dev.env", "env-prod.env"])
                )
                tenant_match = re.search(r'\b(elplacerdc|glamur|damaren|juan-damaren)\b', rel_to_upstream, re.IGNORECASE)
                if is_secret_or_db or (tenant_match and base_name.endswith(".json")):
                    label = tenant_match.group(0) if tenant_match else base_name
                    return {
                        "decision": "deny",
                        "reason": (
                            f"ARNÉS MULTI-TENANT (Aislamiento Upstream): Los repositorios soberanos upstream son agnósticos. "
                            f"Mantené credenciales, bases de datos y datos de tenant [{label}] fuera de upstream "
                            "(ej. '/var/www/baiosfera/0ZEROPS-AGY/users-apis/' o repos de cliente aislados)."
                        )
                    }

        # A2. Handover Immunity
        if HANDOVER_PATTERN.search(target_file) and not target_file.startswith("/var/www/artifacts/research/"):
            return {
                "decision": "deny",
                "reason": (
                    f"ARNÉS HANDOVER IMMUNITY: El archivo [{os.path.basename(target_file)}] "
                    "es un activo de relevo inter-sesión protegido contra modificación o sobreescritura."
                )
            }

        # A3.5 Skill Creation Gate & Epistemic Grounding First Gate (Supreme Directive F0 & Invariante 5, BAI-422)
        is_target_skill = (
            "/zerops-astro-skills/" in target_file or
            "/.agents/skills/" in target_file
        )
        if is_target_skill and not payload.get("test_bypass_research"):
            # Extract skill name from path
            skill_name = ""
            if "/.agents/skills/" in target_file:
                parts = target_file.split("/.agents/skills/")
                skill_name = parts[1].strip("/").split("/")[0] if len(parts) > 1 else ""
            elif "/zerops-astro-skills/" in target_file:
                parts = target_file.split("/zerops-astro-skills/")
                skill_name = parts[1].strip("/").split("/")[0] if len(parts) > 1 else ""

            if not skill_name or skill_name.startswith("."):
                is_target_skill = False

        if is_target_skill and not payload.get("test_bypass_research"):

            # Check if research dossier exists for this skill
            dossier_paths = [
                f"/var/www/artifacts/research/{skill_name}_dossier.md",
                f"/var/www/artifacts/{skill_name}_dossier.md",
                f"/var/www/.agents/skills/{skill_name}/references/usage.md",
                f"/var/www/zerops-astro-skills/{skill_name}/references/usage.md",
            ]
            has_dossier = any(os.path.exists(dp) for dp in dossier_paths)

            skill_dir_local = f"/var/www/.agents/skills/{skill_name}"
            skill_dir_zas = f"/var/www/zerops-astro-skills/{skill_name}"
            is_new_skill = not os.path.exists(os.path.join(skill_dir_local, "SKILL.md")) and not os.path.exists(os.path.join(skill_dir_zas, "SKILL.md"))

            res_state_file = "/tmp/.research_grounding_state.json"
            has_research_recent = has_dossier
            if not has_research_recent and os.path.exists(res_state_file):
                try:
                    with open(res_state_file, "r") as f:
                        r_data = json.load(f)
                        if time.time() - (r_data.get("timestamp", 0) / 1000.0) < 7200:
                            has_research_recent = True
                except Exception:
                    pass

            if not has_research_recent:
                transcript_path = payload.get("transcriptPath", "")
                if transcript_path and os.path.exists(transcript_path):
                    try:
                        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                            for line in f.readlines():
                                if any(k in line for k in RESEARCH_TRANSCRIPT_ANY_TOKENS):
                                    has_research_recent = True
                                    break
                    except Exception:
                        pass

            # Strict SkillCreationGate for new skills (BAI-422)
            if is_new_skill and not has_dossier and not payload.get("test_allow_new_skill"):
                return {
                    "decision": "deny",
                    "reason": (
                        f"🏛️ SKILL CREATION GATE / MANDATO EPISTÉMICO F0 (Supreme Directive Invariante 5): "
                        f"Prohibido crear la nueva skill [{skill_name}] desde memoria estocástica pre-entrenada sin investigación técnica previa. "
                        f"Es mandatorio compilar previamente el dossier de investigación en '/var/www/artifacts/research/{skill_name}_dossier.md' "
                        f"mediante un subagente dedicado ('invoke_subagent' con typeName 'research')."
                    )
                }

            if not has_research_recent:
                return {
                    "decision": "deny",
                    "reason": (
                        f"🏛️ MANDATO EPISTÉMICO F0 (Supreme Directive Invariante 5): "
                        f"Para mutar o crear [{os.path.basename(target_file)}], es mandatorio contrastar previamente "
                        "la realidad técnica exterior ejecutando la skill 'research' (vía subagente 'invoke_subagent' con "
                        "typeName 'research' o herramientas MCP: context7, exa, tavily, jina, firecrawl; fallbacks brave/duckduckgo). "
                        "Prohibido definir o mutar skills basándose en memoria pre-entrenada (AMN) o suposiciones."
                    )
                }

        # A3.6 F4 Master Plan Anti-AMN Gate (Enforces live research prior to formal F4 plan creation)
        is_target_final_plan = (
            ("/artifacts/plans/" in target_file or target_file.startswith("artifacts/plans/"))
            and target_file.endswith(".md")
            and not any(x in target_file.lower() for x in [".executed.", ".superseded.", "report", ".test_hide", "draft", "grilling"])
            and not is_plan_draft(target_file)
            and not (content_to_check and any(k in content_to_check.lower() for k in ["status: draft", "estado: borrador", "draft: true", "borrador: true"]))
        )
        if is_target_final_plan and not payload.get("test_bypass_research"):
            has_plan_research = False
            if os.path.exists(RESEARCH_STATE_FILE):
                try:
                    with open(RESEARCH_STATE_FILE, "r", encoding="utf-8") as rf:
                        r_data = json.load(rf)
                        if (time.time() - (r_data.get("timestamp", 0) / 1000.0)) < 7200:
                            has_plan_research = True
                except Exception:
                    pass
            if not has_plan_research:
                transcript_path = payload.get("transcriptPath", "")
                if transcript_path and os.path.exists(transcript_path):
                    try:
                        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as tf:
                            for line in tf.readlines():
                                if any(k in line for k in RESEARCH_TRANSCRIPT_ANY_TOKENS):
                                    has_plan_research = True
                                    break
                    except Exception:
                        pass
            if not has_plan_research:
                return {
                    "decision": "deny",
                    "reason": (
                        f"🏛️ MANDATO EPISTÉMICO F0->F4 (research Anti-AMN): Para formalizar el plan maestro [{os.path.basename(target_file)}], "
                        "contrastá previamente la arquitectura con 'research' (context7 / exa / tavily + jina:read_url o subagente 'research'). "
                        "Los borradores tempranos usan prefijo 'draft_' o 'status: draft'."
                    )
                }

        # A4. Linear-First Epistemic Persistence Gate (Invariante 2 Soberano)
        plans_dir = "/var/www/artifacts/plans"
        has_active_plan = os.path.exists(plans_dir) and any(
            f.endswith(".md") and not any(x in f.lower() for x in [".executed.", ".superseded.", "report", ".test_hide", "draft", "grilling"])
            and not is_plan_draft(os.path.join(plans_dir, f))
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


        # A5. CoHaLo & Skill-Improver Quality Gate
        content_to_check = content_to_check or args.get("CodeContent", "") or args.get("ReplacementContent", "")

        # A5.0 Zerops Env Sovereignty: Secret Leak Prevention Guard
        if content_to_check and not payload.get("test_bypass_secret_scan"):
            secret_pattern = re.compile(
                r'\b(ghp_[a-zA-Z0-9]{36}|lin_api_[a-zA-Z0-9]{40}|sk-[a-zA-Z0-9_-]{20,}|AIzaSy[a-zA-Z0-9_-]{33}|freellmapi-[a-zA-Z0-9]{20,})\b'
            )
            found_secret = secret_pattern.search(content_to_check)
            if found_secret and not any(p in target_file for p in ["/tmp/", "/fixtures/"]):
                return {
                    "decision": "deny",
                    "reason": (
                        f"ARNÉS SOBERANÍA ZEROPS ENV: Se detectó una credencial en texto plano ({found_secret.group(0)[:6]}...) "
                        f"en [{os.path.basename(target_file)}]. Los secretos deben inyectarse en zerops_env y referenciarse "
                        "exclusivamente por variable de entorno ($VAR o process.env), nunca pegados en código ni archivos."
                    )
                }

        # A5.1 Positive Guidance Guard (Blocks negative prompt dogma in governance and skills)
        is_governance = (
            target_file.endswith("AGENTS.md") or
            "/.agents/rules/" in target_file or
            target_file.endswith("00-SUPREME-DIRECTIVE.md") or
            (target_file.endswith("SKILL.md") and ("/.agents/skills/" in target_file or "/zerops-astro-skills/" in target_file))
        )
        if is_governance and content_to_check:
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

            # A5.2.0 Meta-Skill Subskills Enforcement Gate (BAI-458)
            if not payload.get("test_bypass_subskills"):
                # Subskill 1: skill-creator (YAML Frontmatter & Trigger Specification)
                stripped_content = content_to_check.strip()
                if not (stripped_content.startswith("---") or "---\nname:" in content_to_check):
                    return {
                        "decision": "deny",
                        "reason": (
                            "🏛️ ARNÉS META-SKILL (Subskill: skill-creator): 'SKILL.md' debe comenzar con un bloque "
                            "frontmatter YAML delimitado por '---' conteniendo 'name:' y 'description:' con triggers."
                        )
                    }
                if "name:" not in content_to_check or "description:" not in content_to_check:
                    return {
                        "decision": "deny",
                        "reason": (
                            "🏛️ ARNÉS META-SKILL (Subskill: skill-creator): El frontmatter de 'SKILL.md' debe incluir "
                            "obligatoriamente los campos 'name:' y 'description:'."
                        )
                    }
                if "trigger:" not in content_to_check.lower():
                    return {
                        "decision": "deny",
                        "reason": (
                            "🏛️ ARNÉS META-SKILL (Subskill: skill-creator): El campo 'description:' debe incluir la cláusula "
                            "'Trigger: <palabras clave>' para alimentar el radar de activación de agentes."
                        )
                    }

                # Subskill 2: writing-for-agents (Cognitive Seams & Markdown Syntax Gate)
                fence_count = len(re.findall(r'^```', content_to_check, re.MULTILINE))
                if fence_count % 2 != 0:
                    return {
                        "decision": "deny",
                        "reason": (
                            f"🏛️ ARNÉS META-SKILL (Subskill: writing-for-agents): Se detectó un número impar de bloques de código "
                            f"({fence_count} fences '```'). Cerrá todos los bloques de código para evitar contaminación del contexto."
                        )
                    }
                if not re.search(r'^#\s+.+', content_to_check, re.MULTILINE) or not re.search(r'^##\s+.+', content_to_check, re.MULTILINE):
                    return {
                        "decision": "deny",
                        "reason": (
                            "🏛️ ARNÉS META-SKILL (Subskill: writing-for-agents): 'SKILL.md' debe mantener una jerarquía limpia "
                            "con al menos un título H1 ('# ...') y secciones H2 ('## ...') que reduzcan la carga cognitiva del agente."
                        )
                    }

                # Subskill 3: docu & skill-improver (Dual-RAG Structural References Gate)
                skill_dir = os.path.dirname(target_file)
                ref_dir = os.path.join(skill_dir, "references")
                skill_base = os.path.basename(skill_dir)
                is_sovereign_custom = "/zerops-astro-skills/" in target_file or "/.agents/skills/" in target_file
                if is_sovereign_custom and not UPSTREAM_SKILLS_PATTERN.match(skill_base) and skill_base not in ["taste-skill", "impeccable"]:
                    if os.path.exists(skill_dir) and not os.path.exists(ref_dir) and not payload.get("test_allow_new_skill"):
                        return {
                            "decision": "deny",
                            "reason": (
                                f"🏛️ ARNÉS META-SKILL (Subskills: docu + skill-improver): La skill [{skill_base}] debe desacoplar "
                                "su lógica en Dual-RAG con una carpeta 'references/' conteniendo al menos 'usage.md' o 'infra.md'. "
                                "Prohibido crear monolitos sin arquitectura Dual-RAG."
                            )
                        }

        # A5.2.1 Governance Rules Size Budget Gate (00-SUPREME <= 600 words, AGENTS.md custom <= 800 words - BAI-424)
        def _simulate_edit_text(fpath: str, fallback_content: str) -> str:
            if tool_name in ["edit_file", "replace_file_content"] and os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        cur = f.read()
                    t_old = args.get("Target", "") or args.get("TargetContent", "")
                    t_new = args.get("Replacement", "") or args.get("ReplacementContent", "")
                    if t_old and t_old in cur:
                        return cur.replace(t_old, t_new)
                    return cur
                except Exception:
                    pass
            return fallback_content

        if target_file.endswith("00-SUPREME-DIRECTIVE.md") and tool_name in ["write_to_file", "write_file", "edit_file", "replace_file_content"]:
            check_text = _simulate_edit_text(target_file, content_to_check)
            supreme_words = len(check_text.split())
            if supreme_words > 600:
                return {
                    "decision": "deny",
                    "reason": (
                        f"Contrato CoHaLo Governance Size Budget (BAI-424): '00-SUPREME-DIRECTIVE.md' tiene {supreme_words} palabras "
                        "(límite: 600 palabras). Mantené el router canónico condensado y derivá especificaciones "
                        "hacia 'supreme_directive_encyclopedia.md' respetando Dual-RAG."
                    )
                }

        if target_file.endswith("AGENTS.md") and tool_name in ["write_to_file", "write_file", "edit_file", "replace_file_content"]:
            check_text = _simulate_edit_text(target_file, content_to_check)
            custom_match = re.search(r'<!-- CUSTOM:BEGIN -->(.*?)<!-- CUSTOM:END -->', check_text, re.DOTALL)
            if custom_match:
                custom_words = len(custom_match.group(1).split())
                if custom_words > 800:
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Contrato CoHaLo Governance Size Budget (BAI-424): La sección CUSTOM de 'AGENTS.md' tiene {custom_words} palabras "
                            "(límite: 800 palabras). Mantené las directivas de plataforma esenciales y derivá detalles "
                            "hacia 'meta-system/references/infra.md'."
                        )
                    }

        # A5.2.5 Macro-Visión 360 Dependency Radar
        if "/var/www/zerops-astrobranding/scripts/" in target_file and tool_name in ("write_to_file", "replace_file_content", "write_file", "edit_file"):
            if os.path.basename(target_file) == "unisetup.sh":
                for referenced_script in re.findall(r'setup-[a-zA-Z0-9_\-]+\.sh', content_to_check):
                    ref_full = os.path.join("/var/www/zerops-astrobranding/scripts", referenced_script)
                    if not os.path.exists(ref_full):
                        return {
                            "decision": "deny",
                            "reason": (
                                f"Contrato MACRO-VISIÓN 360 (Alineación de Dependencias): 'unisetup.sh' invoca "
                                f"[{referenced_script}], el cual debe residir en '/var/www/zerops-astrobranding/scripts/'. "
                                "Alineá o creá el script aguas abajo antes de incorporarlo al bootstrapper."
                            )
                        }

        # A5.3 AST & Symbol Preservation Guard (Zero Deletion / Lossless Invariant)
        is_protected_code = (
            "/.agents/skills/" in target_file or
            "/zerops-astro-skills/" in target_file or
            "/zerops-astrobranding/scripts/" in target_file or
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

        # A5.6 Anti-Frankenstein Python Tool Guard (Universal Primitives Architecture)
        if ("tools.py" in target_file or "agent.py" in target_file) and tool_name in ["write_to_file", "write_file", "edit_file", "replace_file_content"] and content_to_check:
            frankenstein_patterns = [
                r'def\s+run_orchesbrand\b',
                r'def\s+apotelos_cli\b',
                r'def\s+run_apotelos\b',
                r'def\s+run_brandplay\b',
                r'def\s+run_fontgen\b',
                r'def\s+run_chroma\b',
                r'def\s+run_symbol\b',
                r'def\s+run_kinetic\b',
                r'def\s+run_brandbook\b',
            ]
            for pat in frankenstein_patterns:
                match = re.search(pat, content_to_check)
                if match:
                    func_name = match.group(0)
                    return {
                        "decision": "deny",
                        "reason": (
                            f"VIOLACIÓN DE ARQUITECTURA (Anti-Frankenstein Tool Invariant - Meta-Script): "
                            f"Prohibido crear tools Python ad-hoc para skills computacionales ({func_name}) en [{os.path.basename(target_file)}]. "
                            "Toda skill determinista o ejecutable DEBE compilarse como un CLI autónomo en /usr/local/bin bajo meta-script "
                            "e invocarse exclusivamente mediante la primitiva universal 'run_command'."
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
            if is_bash_script and ("/zerops-astrobranding/scripts/" in target_file or "/.bin/" in target_file or "/scripts/" in target_file or target_file.endswith(".sh")):
                try:
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
            # JSON syntax validation
            elif target_file.endswith(".json"):
                try:
                    json.loads(content_to_check)
                except Exception as e:
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Contrato de Integridad Sintáctica (JSON SyntaxError): {target_file}: {e}"
                        )
                    }

    # B. Command Guards on run_command
    if tool_name == "run_command":
        cmd = args.get("CommandLine", "")

        # Parse command tokens via AST parser to inspect executed commands vs string literals (BAI-421)
        parsed_nodes = BashCommandParser.parse(cmd)
        executed_cmds = {n.command for n in parsed_nodes}

        # B-1. Kill Guard: Anti-Autoaniquilación y Protección de Sesiones Vivas (BAI-322 & BAI-421)
        is_dang_kill, kill_reason = is_kill_attempt_dangerous(cmd)
        if is_dang_kill:
            return {
                "decision": "deny",
                "reason": kill_reason
            }

        # B-0. Linear-First Multi-Servicio & Platform Infra Command Gate (BAI-430)
        if any(k in cmd for k in ["zcli project import", "zcli service import"]):
            if not payload.get("test_bypass_linear"):
                state_file = "/tmp/.linear_activity_state.json"
                alt_state_file = "/var/www/artifacts/.linear_activity_state.json"
                has_linear_recent = False
                for sf in [state_file, alt_state_file]:
                    if os.path.exists(sf):
                        try:
                            with open(sf, "r") as f:
                                l_data = json.load(f)
                                l_ts = l_data.get("timestamp", 0)
                                if time.time() * 1000 - l_ts < 24 * 3600 * 1000:
                                    has_linear_recent = True
                                    break
                        except Exception:
                            pass
                if not has_linear_recent:
                    return {
                        "decision": "deny",
                        "reason": (
                            "🏛️ VIOLACIÓN LINEAR-FIRST MULTI-SERVICIO (Supreme Directive Invariante 2 & meta-plan): "
                            "El aprovisionamiento de infraestructura o importación de servicios en Zerops exige "
                            "haber registrado previamente el proyecto o tickets atómicos en Linear ('linear-cli create-project' "
                            "o 'linear-cli create \"BAI: <servicio>\"'). Registrá el ticket en Linear antes de desplegar."
                        )
                    }

        # B0. SSoT Sovereign Custom Skills Anti-Pollution Shield
        # Only check mutating commands if an actual mutating command was invoked
        is_mutating_cmd = bool(executed_cmds.intersection({"cp", "mv", "rm", "sed", "tee"})) or any(">" in n.raw for n in parsed_nodes)
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

        # B2. Sweeping RM on artifacts / handovers
        # AST-Guarded: Only triggers if 'rm' or 'unlink' command is executed
        rm_nodes = [n for n in parsed_nodes if n.command in {"rm", "unlink"}]
        for rmn in rm_nodes:
            rm_args_str = " ".join(rmn.args)
            if SWEEPING_ARTIFACTS_RM.search(rmn.raw) or any("artifacts/" in a and ("*" in a or ".*" in a) for a in rmn.args) or (HANDOVER_PATTERN.search(rm_args_str) and any(a in ["-f", "-rf", "-r"] or not a.startswith("-") for a in rmn.args)):
                return {
                    "decision": "deny",
                    "reason": (
                        "ARNÉS HANDOVER IMMUNITY: Mantené intactos los artefactos de relevo inter-sesión "
                        "en /var/www/artifacts/ sin invocar comandos destructivos masivos."
                    )
                }

        # B3. Dangerous RM
        # AST-Guarded: Only triggers if 'rm' or 'unlink' targets /var/www or / recursively
        for rmn in rm_nodes:
            is_recursive = any("-r" in a or "-R" in a for a in rmn.args)
            targets = [a for a in rmn.args if not a.startswith("-")]
            if is_recursive and any(t.rstrip("/") in ["", "/var/www", "/var", "/root", "/etc"] for t in targets):
                return {
                    "decision": "force_ask",
                    "reason": "Comando con riesgo de destrucción total del sistema detectado."
                }

        # B4. Google Drive Unpruned find Guard (Anti-Freeze Invariant)
        # AST-Guarded: Only triggers if 'find' command is executed
        find_nodes = [n for n in parsed_nodes if n.command == "find"]
        for fn in find_nodes:
            find_args_str = " ".join(fn.args)
            if re.search(r'(^|\s)(/var/www/?(\s|$)|.*/baiosfera|.*baiosfera)', find_args_str) and not any(a == "-prune" for a in fn.args):
                return {
                    "decision": "deny",
                    "reason": (
                        "Seguridad FUSE / Google Drive: Para buscar en la raíz de /var/www podá (-prune) '/var/www/baiosfera', "
                        "o buscá directamente dentro de una subcarpeta local específica (ej: /var/www/zerops-astrobranding)."
                    )
                }

        # B5. SSoT Parity Pre-Push Gate (Supreme Directive Invariant 3 & Planner Rule 4)
        # AST-Guarded: Only triggers if 'git push' is executed
        git_push_nodes = [n for n in parsed_nodes if n.command == "git" and "push" in n.args]
        if git_push_nodes:
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

                    # Subskill 4: skill-registry & writing-skills (Index Verification on Push)
                    if ("zerops-astro-skills" in repo_dir or "zerops-astro-skills" in cmd) and not payload.get("test_bypass_registry_check"):
                        registry_file = "/var/www/.atl/skill-registry.md"
                        if os.path.exists(registry_file):
                            try:
                                with open(registry_file, "r") as f:
                                    reg_text = f.read()
                                unregistered = []
                                skills_base = "/var/www/zerops-astro-skills"
                                if os.path.exists(skills_base):
                                    for sk in os.listdir(skills_base):
                                        if os.path.isdir(os.path.join(skills_base, sk)) and not sk.startswith(".") and not UPSTREAM_SKILLS_PATTERN.match(sk):
                                            if sk not in reg_text:
                                                unregistered.append(sk)
                                if unregistered:
                                    return {
                                        "decision": "deny",
                                        "reason": (
                                            f"🏛️ ARNÉS META-SKILL (Subskill: skill-registry): Hay skills soberanas sin indexar en '{os.path.basename(registry_file)}': "
                                            f"{unregistered}. Actualizá el registro de skills antes de hacer git push."
                                        )
                                    }
                            except Exception:
                                pass
                except Exception:
                    pass

        # B6. Gate 14: Anti-False-Completion & Zerops Deployment Verification Gate (BAI-454)
        if "linear-cli" in cmd and any(st in cmd for st in ['"Done"', "'Done'", "Done"]):
            cache_file = "/tmp/.zerops_discover_cache.json"
            if not payload.get("test_bypass_linear") and payload.get("transcriptPath"):
                tx_discover = _read_zerops_discover_from_transcript(payload.get("transcriptPath"))
                if tx_discover:
                    try:
                        with open(cache_file, "w") as f:
                            json.dump(tx_discover, f, indent=2)
                    except Exception:
                        pass
            if os.path.exists(cache_file) and not payload.get("test_bypass_linear"):
                try:
                    with open(cache_file, "r") as f:
                        z_data = json.load(f)
                    services = z_data.get("services", [])
                    undeployed = [s.get("hostname") for s in services if s.get("deployed") is False and not s.get("isInfrastructure")]
                    for und in undeployed:
                        if und and re.search(r'\b' + re.escape(und) + r'\b', cmd, re.IGNORECASE):
                            return {
                                "decision": "deny",
                                "reason": (
                                    f"ARNÉS F5 GOBERNANZA FÍSICA (Gate 14 - Anti-Checklist Theater): "
                                    f"El servicio '{und}' figura con deployed: false en Zerops. "
                                    f"Prohibido marcar Done en Linear sin haber ejecutado zerops_deploy formalmente."
                                )
                            }
                except Exception:
                    pass

    return {"decision": "allow"}

def run_tests():
    import importlib.util
    test_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_tool_guard.py")
    spec = importlib.util.spec_from_file_location("test_tool_guard", test_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for k, v in globals().items():
        if not k.startswith("__") and k not in mod.__dict__:
            mod.__dict__[k] = v
    return mod.run_tests(evaluate_hook)

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
            with open("/tmp/last_tool_guard_input.json", "w") as f:
                f.write(raw_input)
    except Exception:
        pass

    is_post_tool = "--post-tool" in sys.argv or ("stepIdx" in payload and "invocationNum" not in payload and ("error" in payload or "toolResult" in payload or "status" in payload))
    if is_post_tool:
        payload["is_post_tool"] = True
        result = evaluate_hook(payload)
        print(json.dumps(result))
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
