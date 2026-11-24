#!/usr/bin/env python3
"""
tool-guard.py — Lean Physical Safety Harness for Antigravity CLI (v4.0)
Execution: <15ms | Zero External Dependencies | Zero Prompt/History Injection
Enforces strictly deterministic physical invariants in PreToolUse & PostToolUse:
  1. Plaintext secret leak prevention (GitHub, Linear, OpenAI, Google, FreeLLMAPI).
  2. Upstream isolation shield (no tenant data/secrets or external skill pollution in baiosfera/*).
  3. Handover asset immunity against accidental overwrites or sweeping deletes.
  4. Fast in-memory syntax pre-flight for .py and .json writes.
  5. Single-node ZCP scale guard (minContainers=1, maxContainers=1).
  6. Process kill guard (protects ancestor PIDs and live TTY agent sessions).
  7. Catastrophic recursive rm guard & unpruned FUSE Google Drive find guard.
  8. LLM batch pilot guard (requires --pilot/--limit/--sample/--dry-run).
  9. Upstream git push clean-tree guard.
 10. Detached Engram 3-tier background sync on PostToolUse memory writes.
"""
import sys
import os

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import json
import re
import shlex
import shutil
import subprocess

HANDOVER_PATTERN = re.compile(r"(_handover|_handoff|_blueprint|_dossier|_roadmap)", re.IGNORECASE)
SWEEPING_ARTIFACTS_RM = re.compile(r"rm\s+.*artifacts/(\*|\.\*)", re.IGNORECASE)
SECRET_PATTERN = re.compile(
    r"\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{22,}|lin_api_[a-zA-Z0-9]{40}|"
    r"sk-[a-zA-Z0-9_-]{20,}|AIzaSy[a-zA-Z0-9_-]{33}|freellmapi-[a-zA-Z0-9]{20,})\b"
)
UPSTREAM_SKILLS_PATTERN = re.compile(
    r"^(react-19|zustand-5|tailwind-4|ai-sdk-5|nextjs-15|typescript|zod-4|playwright|puppeteer|"
    r"crawl4ai|firecrawl|angular|django-drf|spring-boot-3|java-21|electron|elixir-antipatterns|"
    r"pytest|go-testing|hexagonal-architecture-layers-java|react-native|rdd-.*|sdd-.*|"
    r"github-pr|work-unit-commits|jira-.*|issue-.*|gentle-ai-.*|systemic-issue-triage|"
    r"judgment-day|comment-writer|cognitive-doc-design|gga|_shared|branch-pr|chained-pr|"
    r"skill-creator|skill-registry|skill-improver|hermes-ephemeral-.*|pocock.*|karpathy.*|"
    r"using-superpowers|brainstorming|dispatching-parallel-agents|executing-plans|"
    r"finishing-a-development-branch|receiving-code-review|requesting-code-review|"
    r"subagent-driven-development|systematic-debugging|test-driven-development|"
    r"using-git-worktrees|verification-before-completion|writing-plans|writing-skills|"
    r"ask-matt|chief-of-staff|claude-handoff|code-review|codebase-design|diagnosing-bugs|"
    r"domain-modeling|git-guardrails-claude-code|grill-me|grill-with-docs|grilling|handoff|"
    r"implement|implement-spec|improve-codebase-architecture|loop-me|migrate-to-shoehorn|pr|"
    r"prototype|retro|scaffold-exercises|setup-matt-pocock-skills|setup-pre-commit|"
    r"setup-ts-deep-modules|software-factory|tdd|teach|to-questionnaire|to-spec|to-tickets|"
    r"triage|wait-what|wayfinder|wizard|writing-beats|writing-for-agents|writing-fragments|"
    r"writing-shape)$",
    re.IGNORECASE,
)
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
BATCH_SCRIPT_RE = re.compile(
    r"(?:^|/)(?:compile_playbooks?|batch_llm|categorize_transcripts?|mass_inference|transcribe_batch)"
    r"[a-zA-Z0-9_.-]*\.(?:py|ts|js|mjs)$"
)
PILOT_FLAG_RE = re.compile(
    r"(?:^|\s)(?:--pilot|--limit(?:=|\s+)\d+|--max-items(?:=|\s+)\d+|--sample(?:=|\s+)\d+|--dry-run)(?:\s|$)"
)


class BashCommandNode:
    def __init__(self, command: str, args: list, raw: str):
        self.command = command
        self.args = args
        self.raw = raw


class BashCommandParser:
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

        commands, current = [], []
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
        filtered, i, n = [], 0, len(toks)
        while i < n:
            t = toks[i]
            if t in cls.REDIRECT_TOKENS:
                i += 2
                continue
            if t.isdigit() and i + 1 < n and toks[i + 1] in cls.REDIRECT_TOKENS:
                i += 3
                continue
            if any(t.startswith(op) and len(t) > len(op) for op in (">", "<", "2>", "&>", "1>")):
                i += 1
                continue
            filtered.append(t)
            i += 1

        idx = 0
        while idx < len(filtered):
            tok = filtered[idx]
            if tok in cls.WRAPPER_COMMANDS or ("=" in tok and not tok.startswith("-")):
                idx += 1
            elif tok == "timeout":
                idx += 1
                while idx < len(filtered) and (
                    filtered[idx].startswith("-")
                    or filtered[idx].isdigit()
                    or filtered[idx].endswith(("s", "m"))
                ):
                    idx += 1
            else:
                break

        if idx >= len(filtered):
            return

        cmd_name = os.path.basename(filtered[idx])
        cmd_args = filtered[idx + 1 :]
        commands.append(BashCommandNode(cmd_name, cmd_args, " ".join(filtered)))

        if cmd_name in {"bash", "sh", "zsh"}:
            for j, arg in enumerate(cmd_args):
                if arg == "-c" and j + 1 < len(cmd_args):
                    commands.extend(cls.parse(cmd_args[j + 1]))
                    break
        elif cmd_name == "find" and "-exec" in cmd_args:
            exec_toks = []
            for a in cmd_args[cmd_args.index("-exec") + 1 :]:
                if a in {";", "+", "\\;"}:
                    break
                if a != "{}":
                    exec_toks.append(a)
            if exec_toks:
                cls._process_segment(exec_toks, commands)


def is_upstream_skill_pollution(path_or_cmd: str) -> str:
    if "/var/www/zerops-astro-skills" not in path_or_cmd:
        return ""
    for token in re.split(r'[/ \t\n\'"]+', path_or_cmd):
        t = token.strip()
        if UPSTREAM_SKILLS_PATTERN.match(t):
            return t
    return ""


def _glob_pids() -> list:
    try:
        return [int(f) for f in os.listdir("/proc") if f.isdigit()]
    except Exception:
        return []


def _get_process_ancestors(pid: int = None) -> set:
    curr = os.getpid() if pid is None else pid
    ancestors = set()
    while curr > 1:
        ancestors.add(curr)
        try:
            with open(f"/proc/{curr}/status", "r", encoding="utf-8", errors="ignore") as f:
                ppid = next((int(l.split()[1]) for l in f if l.startswith("PPid:")), None)
            if ppid and ppid > 0 and ppid not in ancestors:
                curr = ppid
            else:
                break
        except Exception:
            break
    return ancestors


def _get_process_info(pid: int) -> dict:
    info = {"pid": pid, "cmdline": "", "comm": "", "tty": ""}
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
                    break
    except Exception:
        pass
    try:
        for fd in (0, 1, 2):
            link = os.readlink(f"{proc_dir}/fd/{fd}")
            if link.startswith(("/dev/pts/", "/dev/tty")):
                info["tty"] = link
                break
    except Exception:
        pass
    return info


def is_kill_attempt_dangerous(cmd: str) -> tuple:
    if not re.search(r"\b(kill|pkill|killall)\b", cmd):
        return False, ""
    kill_nodes = [n for n in BashCommandParser.parse(cmd) if n.command in {"kill", "pkill", "killall"}]
    if not kill_nodes:
        return False, ""

    ancestors = _get_process_ancestors()
    ancestor_cmds = [c for c in (_get_process_info(p)["cmdline"] for p in ancestors) if c]
    protected = {"agy", "antigravity", "gemini-cli", "claude"}
    for cand in protected.copy():
        p = shutil.which(cand)
        if p:
            try:
                protected.add(os.path.basename(os.path.realpath(p)))
            except Exception:
                pass

    for node in kill_nodes:
        if node.command == "kill":
            for arg in node.args:
                if not arg.startswith("-") and arg.isdigit():
                    tpid = int(arg)
                    if tpid in ancestors:
                        return True, f"Kill Guard: denied 'kill' on ancestor PID {tpid}."
                    pinfo = _get_process_info(tpid)
                    if pinfo["tty"] and any(b in pinfo["cmdline"] or pinfo["comm"] == b for b in protected):
                        return True, f"Kill Guard: denied 'kill' on live TTY agent PID {tpid} ({pinfo['comm']})."
        elif node.command == "pkill":
            parts, skip = [], False
            for a in node.args:
                if skip:
                    skip = False
                elif a in {"-u", "-U", "-G", "-g", "-P", "-t"}:
                    skip = True
                elif not a.startswith("-"):
                    parts.append(a)
            pattern = " ".join(parts).strip()
            if not pattern:
                continue
            try:
                pat_re = re.compile(pattern, re.IGNORECASE)
            except Exception:
                pat_re = None
            for acmd in ancestor_cmds:
                if (pat_re and pat_re.search(acmd)) or pattern in acmd:
                    return True, f"Kill Guard: denied 'pkill' matching active ancestor ({pattern})."
            for pid in _glob_pids():
                pinfo = _get_process_info(pid)
                if pinfo["tty"] and any(b in pinfo["cmdline"] or pinfo["comm"] == b for b in protected):
                    if (pat_re and (pat_re.search(pinfo["cmdline"]) or pat_re.search(pinfo["comm"]))) or pattern in pinfo["cmdline"]:
                        return True, f"Kill Guard: denied 'pkill' targeting live TTY agent PID {pid}."
        elif node.command == "killall":
            for tgt in (a for a in node.args if not a.startswith("-")):
                if any(tgt in acmd for acmd in ancestor_cmds):
                    return True, f"Kill Guard: denied 'killall {tgt}' matching ancestor."
                if any(tgt == b or b in tgt for b in protected):
                    for pid in _glob_pids():
                        pinfo = _get_process_info(pid)
                        if pinfo["tty"] and any(b in pinfo["cmdline"] or pinfo["comm"] == b for b in protected):
                            return True, f"Kill Guard: denied 'killall {tgt}' with live TTY session."
    return False, ""


def trigger_engram_background_sync(payload: dict) -> bool:
    if "--test" in sys.argv or payload.get("test_mode"):
        return True
    sync_bin = next(
        (c for c in ("/usr/local/bin/engram-sync", "/var/www/.bin/engram-sync", "/var/www/zerops-astrobranding/scripts/engram-sync")
         if os.path.isfile(c) and os.access(c, os.X_OK)),
        None,
    )
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


def _deny(reason: str) -> dict:
    return {"decision": "deny", "reason": reason}


def evaluate_hook(payload: dict) -> dict:
    if payload.get("is_post_tool") or (
        "stepIdx" in payload and "invocationNum" not in payload and ("error" in payload or "toolResult" in payload or "status" in payload)
    ):
        tool_call = payload.get("toolCall", {})
        tool_args = tool_call.get("args", {})
        if tool_call.get("name") == "call_mcp_tool":
            srv = str(tool_args.get("ServerName", "")).strip().lower()
            mtool = str(tool_args.get("ToolName", "")).strip()
            if srv == "engram" and mtool in ENGRAM_WRITE_TOOLS:
                ok = trigger_engram_background_sync(payload)
                if payload.get("test_inspect_engram_sync"):
                    return {"engramSyncTriggered": ok, "source": f"post_tool:{mtool}"}
                return {}
        if payload.get("test_inspect_engram_sync"):
            return {"engramSyncTriggered": False}
        return {}

    if "invocationNum" in payload or "initialNumSteps" in payload or payload.get("session_start") or "terminationReason" in payload:
        return {}

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    if tool_name == "call_mcp_tool" and args.get("ServerName") == "zerops" and args.get("ToolName") == "zerops_scale":
        sargs = args.get("Arguments", {})
        if sargs.get("serviceHostname") == "zcp":
            min_c, max_c = sargs.get("minContainers"), sargs.get("maxContainers")
            if (min_c is not None and min_c > 1) or (max_c is not None and max_c > 1):
                return _deny(f"ZCP Single-Node Guard: zcp must stay at minContainers=1, maxContainers=1 (got {min_c}/{max_c}).")

    if tool_name in {"write_file", "edit_file", "write_to_file", "replace_file_content"}:
        target = args.get("Path", "") or args.get("TargetFile", "")
        content = args.get("Content", "") or args.get("Replacement", "") or args.get("CodeContent", "") or args.get("ReplacementContent", "")

        if content and not payload.get("test_bypass_secret_scan") and not any(p in target for p in ("/tmp/", "/fixtures/")):
            m = SECRET_PATTERN.search(content)
            if m:
                return _deny(f"Secret Guard: plaintext credential ({m.group(0)[:6]}...) blocked in {os.path.basename(target)}. Use zerops_env + $VAR.")

        polluted = is_upstream_skill_pollution(target)
        if polluted:
            return _deny(f"Upstream Shield: external skill '{polluted}' does not belong in /var/www/zerops-astro-skills/.")

        for up_prefix in ("/var/www/zerops-astrobranding/", "/var/www/zerops-astro-skills/"):
            if target.startswith(up_prefix):
                rel = target[len(up_prefix) :]
                base = os.path.basename(rel).lower()
                is_secret_file = base.endswith((".db", ".sqlite", "-keys.md", "_keys.md")) or (
                    base.endswith(".env") and base not in {".env.example", "env-dev.env", "env-prod.env"}
                )
                tenant_m = re.search(r"\b(elplacerdc|glamur|damaren|juan-damaren)\b", rel, re.IGNORECASE)
                if is_secret_file or (tenant_m and base.endswith(".json")):
                    return _deny(f"Upstream Multi-Tenant Shield: '{base}' cannot be written inside {up_prefix}.")

        if HANDOVER_PATTERN.search(target) and not any(p in target for p in ("/var/www/artifacts/research/", "/tmp/")):
            return _deny(f"Handover Immunity: '{os.path.basename(target)}' is protected against overwrite.")

        if tool_name in {"write_file", "write_to_file"} and content:
            if target.endswith(".py"):
                try:
                    compile(content, target, "exec")
                except SyntaxError as e:
                    return _deny(f"Python SyntaxError in {target}:{e.lineno}: {e.msg}")
            elif target.endswith(".json"):
                try:
                    json.loads(content)
                except Exception as e:
                    return _deny(f"JSON SyntaxError in {target}: {e}")

    if tool_name == "run_command":
        cmd = args.get("CommandLine", "")
        nodes = BashCommandParser.parse(cmd)

        dang_kill, kill_reason = is_kill_attempt_dangerous(cmd)
        if dang_kill:
            return _deny(kill_reason)

        cmd_no_quotes = re.sub(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", " ", cmd)
        for n in nodes:
            if n.command in {"cp", "mv", "tee", "ln", "rsync"} or (n.command == "sed" and any(a.startswith("-i") for a in n.args)):
                pol = is_upstream_skill_pollution(" ".join([n.command] + n.args))
                if pol:
                    return _deny(f"Upstream Shield: external skill '{pol}' cannot be copied into zerops-astro-skills.")
        if re.search(r"(?:^|[\s;|&])[12]?>>?(?!\s*&)", cmd_no_quotes):
            pol = is_upstream_skill_pollution(cmd_no_quotes)
            if pol:
                return _deny(f"Upstream Shield: external skill '{pol}' cannot be redirected into zerops-astro-skills.")

        rm_nodes = [n for n in nodes if n.command in {"rm", "unlink"}]
        for rmn in rm_nodes:
            rm_str = " ".join(rmn.args)
            if SWEEPING_ARTIFACTS_RM.search(rmn.raw) or any("artifacts/" in a and ("*" in a or ".*" in a) for a in rmn.args) or (
                HANDOVER_PATTERN.search(rm_str) and any(a in {"-f", "-rf", "-r"} or not a.startswith("-") for a in rmn.args)
            ):
                return _deny("Handover Immunity: sweeping or handover deletion blocked in /var/www/artifacts/.")
            is_rec = any("-r" in a or "-R" in a for a in rmn.args)
            targets = [a for a in rmn.args if not a.startswith("-")]
            if is_rec and any(t.rstrip("/") in {"", "/var/www", "/var", "/root", "/etc"} for t in targets):
                return {"decision": "force_ask", "reason": "Catastrophic recursive delete targeting protected root path."}

        for fn in (n for n in nodes if n.command == "find"):
            fstr = " ".join(fn.args)
            if re.search(r"(^|\s)(/var/www/?(\s|$)|.*/baiosfera|.*baiosfera)", fstr) and "-prune" not in fn.args:
                return _deny("FUSE Drive Guard: prune '/var/www/baiosfera' with -prune or search inside a local subfolder.")

        if any(n.command == "git" and "push" in n.args for n in nodes):
            cwd = args.get("Cwd", "")
            for repo_name in ("zerops-astrobranding", "zerops-astro-skills"):
                if repo_name in cmd or repo_name in cwd:
                    repo_dir = cwd if os.path.exists(os.path.join(cwd, ".git")) else f"/var/www/{repo_name}"
                    try:
                        proc = subprocess.run(["git", "status", "--porcelain"], cwd=repo_dir, capture_output=True, text=True, timeout=3)
                        if proc.returncode == 0 and proc.stdout.strip():
                            return _deny(f"Upstream Pre-Push Guard: commit dirty changes in {repo_name} before git push.")
                    except Exception:
                        pass

        for n in nodes:
            if n.command in {"python", "python3", "uv", "bun", "node"}:
                joined = " ".join(n.args)
                if any(t in joined for t in ("pytest", "unittest", "test_")):
                    continue
                if any(BATCH_SCRIPT_RE.search(a) for a in n.args) and not PILOT_FLAG_RE.search(cmd):
                    return _deny("LLM Batch Pilot Guard: run batch scripts with --pilot, --limit <=10, --sample, or --dry-run first.")

    return {"decision": "allow"}


def run_tests() -> int:
    import importlib.util
    test_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_tool_guard.py")
    spec = importlib.util.spec_from_file_location("test_tool_guard", test_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run_tests(evaluate_hook)


def main():
    if "--test" in sys.argv:
        sys.exit(run_tests())

    raw = ""
    payload = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            payload = json.loads(raw)
    except Exception:
        pass

    if "--post-tool" in sys.argv:
        payload["is_post_tool"] = True
        print(json.dumps(evaluate_hook(payload)))
        sys.exit(0)

    if not payload or "--session-start" in sys.argv or "--stop" in sys.argv:
        print(json.dumps({}))
        sys.exit(0)

    print(json.dumps(evaluate_hook(payload)))
    sys.exit(0)


if __name__ == "__main__":
    main()
