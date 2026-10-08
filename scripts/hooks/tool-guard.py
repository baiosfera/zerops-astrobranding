#!/usr/bin/env python3
"""
tool-guard.py — Native Antigravity Process-Level Gatekeeper & Anti-Sycophancy Harness
Version: 2.4 (SSoT Parity Pre-Push Gate, Plan Inmutability & RegEx Trigger Split)
Execution: <30ms | Zero External Dependencies | 100% Deterministic
Intercepts PreToolUse and PreInvocation events to enforce:
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
    """Detects occurrences of '0zcp-123' not preceded by the canonical Drive prefix."""
    prefix = "/var/www/baiosfera/0ZEROPS-AGY/"
    idx = 0
    while True:
        pos = text.find("0zcp-123", idx)
        if pos == -1:
            break
        if pos < len(prefix) or text[pos - len(prefix):pos] != prefix:
            return True
        idx = pos + len("0zcp-123")
    return False

UPSTREAM_SKILLS_PATTERN = re.compile(
    r'^(react-19|zustand-5|tailwind-4|ai-sdk-5|nextjs-15|typescript|zod-4|playwright|puppeteer|'
    r'crawl4ai|firecrawl|angular|django-drf|spring-boot-3|java-21|electron|elixir-antipatterns|'
    r'pytest|go-testing|hexagonal-architecture-layers-java|react-native|sdd-.*|rdd-.*|'
    r'github-pr|work-unit-commits|jira-.*|issue-.*|gentle-ai-.*|systemic-issue-triage|'
    r'judgment-day|comment-writer|cognitive-doc-design|gga|_shared|branch-pr|chained-pr|'
    r'skill-creator|skill-registry|skill-improver|hermes-ephemeral-.*|pocock.*)$',
    re.IGNORECASE
)

def is_upstream_skill_pollution(path_or_cmd: str) -> str:
    """Detects attempts to write, copy, or sync upstream gentle-ai/pocock skills into Drive SSoT."""
    ssot_skills_prefix = "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/skills"
    if ssot_skills_prefix not in path_or_cmd:
        return ""
    for token in re.split(r'[/ \t\n\'"]+', path_or_cmd):
        token_clean = token.strip()
        if UPSTREAM_SKILLS_PATTERN.match(token_clean):
            return token_clean
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
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/rules/00-SUPREME-DIRECTIVE.md",
        "/var/www/.agents/rules/00-SUPREME-DIRECTIVE.md"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/hooks.json",
        "/var/www/.agents/hooks.json"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/plan-validate.sh",
        "/var/www/.bin/plan-validate"
    ),
    (
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/plan-archive.sh",
        "/var/www/.bin/plan-archive"
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
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.engram/config.json",
        "/var/www/.engram/config.json"
    ),
]

def cleanup_artifacts_lifecycle(purge_executed: bool = False) -> dict:
    """
    Lifecycle Purge Protocol (Supreme Directive v8.3 & Planner v8.6):
    1. Scans /var/www/artifacts/ and /var/www/artifacts/archive/.
    2. Identifies executed plans (files ending with '.executed.md' or '_vN.executed.md').
    3. For any executed plan stem or active plan stem, purges previous '.superseded.md' files.
    4. If purge_executed is True (session-end protocol), purges all '*.executed.md' from archive/.
    5. Handover assets matching HANDOVER_PATTERN are permanent and strictly skipped.
    """
    artifacts_dir = "/var/www/artifacts"
    archive_dir = "/var/www/artifacts/archive"
    purged_superseded = []
    purged_executed = []

    if not os.path.exists(artifacts_dir):
        return {"purged_superseded": purged_superseded, "purged_executed": purged_executed}

    executed_stems = set()
    scan_dirs = [artifacts_dir]
    if os.path.exists(archive_dir):
        scan_dirs.append(archive_dir)

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
                    if sdir == artifacts_dir or stem in executed_stems:
                        try:
                            os.remove(fpath)
                            purged_superseded.append(fpath)
                        except Exception:
                            pass
        except Exception:
            pass

    if purge_executed and os.path.exists(archive_dir):
        try:
            for fname in os.listdir(archive_dir):
                if HANDOVER_PATTERN.search(fname):
                    continue
                if ".executed." in fname:
                    fpath = os.path.join(archive_dir, fname)
                    try:
                        os.remove(fpath)
                        purged_executed.append(fpath)
                    except Exception:
                        pass
        except Exception:
            pass

    return {"purged_superseded": purged_superseded, "purged_executed": purged_executed}

def auto_sync_governance():
    """
    Autonomous Parity Reactor: Keeps SSoT and local runtime in bidirectional
    real-time synchronization. Propagates the newest file state deterministically.
    """
    import shutil
    for ssot_path, runtime_path in CORE_SYNC_PAIRS:
        try:
            ssot_exists = os.path.exists(ssot_path)
            runtime_exists = os.path.exists(runtime_path)
            if not ssot_exists and not runtime_exists:
                continue

            if ssot_exists and not runtime_exists:
                os.makedirs(os.path.dirname(runtime_path), exist_ok=True)
                shutil.copy2(ssot_path, runtime_path)
                if runtime_path.startswith("/var/www/.bin/"):
                    os.chmod(runtime_path, 0o755)
                continue

            if runtime_exists and not ssot_exists:
                os.makedirs(os.path.dirname(ssot_path), exist_ok=True)
                shutil.copy2(runtime_path, ssot_path)
                continue

            ssot_mtime = os.path.getmtime(ssot_path)
            runtime_mtime = os.path.getmtime(runtime_path)

            if abs(ssot_mtime - runtime_mtime) > 1.0:
                if ssot_mtime > runtime_mtime:
                    shutil.copy2(ssot_path, runtime_path)
                    if runtime_path.startswith("/var/www/.bin/"):
                        os.chmod(runtime_path, 0o755)
                else:
                    shutil.copy2(runtime_path, ssot_path)
        except Exception:
            pass

    # Purge bytecode residue deterministically (Invariant 6)
    hooks_pycache = "/var/www/.bin/hooks/__pycache__"
    if os.path.exists(hooks_pycache):
        try:
            import shutil
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
    """
    is_skill = "/.agents/skills/" in target_file or target_file.startswith(".agents/skills/")
    is_script = "/0zcp-123/scripts/" in target_file or "/.bin/" in target_file
    is_rule = target_file.endswith("AGENTS.md") or "/.agents/rules/" in target_file
    is_hook = "/.bin/hooks/" in target_file or "/scripts/hooks/" in target_file

    if not (is_skill or is_script or is_rule or is_hook):
        return True
    if not os.path.exists(target_file):
        return True  # New file being created

    target_mtime = os.path.getmtime(target_file)
    bak_dirs = [
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak/skills",
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak/scripts",
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak/rules",
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak"
    ]

    base_name = os.path.basename(target_file)
    name_stem = os.path.splitext(base_name)[0]
    
    skill_name = ""
    if is_skill and "/.agents/skills/" in target_file:
        parts = target_file.split("/.agents/skills/")
        skill_name = parts[1].split("/")[0] if len(parts) > 1 else ""

    latest_bak_mtime = 0.0
    for bdir in bak_dirs:
        if not os.path.exists(bdir):
            continue
        try:
            for fname in os.listdir(bdir):
                match = False
                if skill_name and skill_name in fname:
                    match = True
                elif name_stem and name_stem in fname:
                    match = True
                elif base_name in fname:
                    match = True
                
                if match:
                    fpath = os.path.join(bdir, fname)
                    if os.path.isfile(fpath) and os.path.getsize(fpath) > 0:
                        mtime = os.path.getmtime(fpath)
                        if mtime > latest_bak_mtime:
                            latest_bak_mtime = mtime
        except Exception:
            pass

    # Pre-Mutation Invariant: A backup must capture the current file state
    # (backup mtime >= target file mtime with 1.0s margin for filesystem precision)
    return latest_bak_mtime >= (target_mtime - 1.0)

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

def evaluate_hook(payload: dict) -> dict:
    # 0. Autonomous Parity Reactor: continuous real-time sync between SSoT and local runtime
    auto_sync_governance()

    # 1. PostToolUse Handling
    if "stepIdx" in payload and "invocationNum" not in payload and ("error" in payload or "toolResult" in payload or "status" in payload):
        return {}

    # 2. PreInvocation Handling
    if "invocationNum" in payload or "initialNumSteps" in payload:
        # Anti-Duplicate & Token Hygiene Cache (SOTA Prompt Caching Invariant)
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

        # Deduplicate identical invocation events firing within 2.5s (multi-hooks.json artifact)
        if payload.get("test_dedup") or ("--test" not in sys.argv):
            if last_state.get("invocationNum") == inv_num and (now_ts - last_state.get("ts", 0)) < 2.5:
                return {}

        try:
            with open(state_file, "w") as f:
                json.dump({"invocationNum": inv_num, "ts": now_ts}, f)
        except Exception:
            pass

        user_prompt = payload.get("userPrompt", "")
        transcript_path = payload.get("transcriptPath", "")
        if not user_prompt and transcript_path and os.path.exists(transcript_path):
            try:
                with open(transcript_path, "rb") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 16384))
                    for line in reversed(f.readlines()):
                        try:
                            d = json.loads(line.decode("utf-8", errors="ignore"))
                            if d.get("type") == "USER_INPUT":
                                user_prompt = d.get("content", "")
                                break
                        except Exception:
                            pass
            except Exception:
                pass

        matched_skills = detect_skills_in_prompt(user_prompt)
        skill_alert = ""
        if matched_skills:
            items = [f"[{m[0]}] ('{m[1]}')" for m in matched_skills[:4]]
            primary_path = matched_skills[0][2]
            skill_alert = f"\n🎯 RADAR DE SKILLS ACTIVO (MANDATORIO F0): Detectado requerimiento para {', '.join(items)}. Debés ejecutar 'view_file' en {primary_path} antes de proponer o ejecutar código."

        # Check active plan & F4 Halt Centinela (Linear Integration)
        halt_alert = ""
        linear_active_file = "/var/www/artifacts/linear_active.json"
        active_linear_id = None
        if os.path.exists(linear_active_file):
            try:
                with open(linear_active_file, "r") as f:
                    linear_data = json.load(f)
                    active_linear_id = linear_data.get("issueId")
            except Exception:
                pass

        if active_linear_id and user_prompt:
            has_question = ("?" in user_prompt or "¿" in user_prompt)
            has_go = bool(re.search(r'\b(go|adelante|procede|ejecuta|ejecutá|aprobado|dale|si|sí)\b', user_prompt, re.IGNORECASE))
            if has_question or not has_go:
                halt_alert = (
                    f"\n⏸️ F4 HALT GATE ACTIVO: Ticket Linear en progreso [{active_linear_id}]. "
                    "El usuario planteó una consulta o no dio 'Go' unívoco. "
                    "PROHIBIDO mutar código de aplicación. Respondé en chat y permanecé en F4."
                )

        # SOTA Prompt Caching & Token Hygiene:
        # Only inject the full governance banner on invocation <= 1 or when new skills/halt alerts are detected.
        # Do not spam the context on every intermediate tool turn.
        is_first_invocation = (inv_num <= 1)
        if not is_first_invocation and not skill_alert and not halt_alert:
            return {}

        governance_msg = (
            "🛡️ GOBERNANZA FÍSICA ZCP (v2.1): Freno de Mano F4 & Plan-First Gate Obligatorio (Cierre Subordinado a Go), "
            "Contrato Anti-Redundancia en Chat (Zero Token Bloat: solo link al plan en F4; atestación exit 0 en <=3 líneas en F5), "
            "Handover Immunity, Backup Monótono, Candado SSoT y Radar 360°."
        ) if is_first_invocation else "🛡️ RADAR ZCP:"

        return {
            "injectSteps": [
                {
                    "ephemeralMessage": f"{governance_msg}{skill_alert}{halt_alert}".strip()
                }
            ]
        }

    # 2. PreToolUse Handling
    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    # 0. Anti-AMN & F0 Epistemic Inflow: Bloqueo determinista de search_web nativo
    if tool_name == "search_web":
        return {
            "decision": "deny",
            "reason": (
                "INTERCEPCIÓN DETERMINISTA F0 (Anti-AMN): La herramienta nativa 'search_web' está deprecada y bloqueada en este entorno. "
                "Para investigación y grounding en vivo, ejecutá exclusivamente la skill 'research' mediante 'call_mcp_tool' "
                "(servidores: tavily, exa, brave) o mediante subagente 'invoke_subagent' (typeName: 'research')."
            )
        }

    # 0.1 Intercepción Determinista de Servidor MCP Local de Linear (Anti-Hang & Zero Token Waste)
    if tool_name == "call_mcp_tool" and args.get("ServerName") == "linear":
        return {
            "decision": "deny",
            "reason": (
                "INTERCEPCIÓN DETERMINISTA: El servidor MCP local 'linear' está PROHIBIDO y extirpado. "
                "Operá Linear exclusivamente mediante el CLI local '/usr/local/bin/linear-cli' o Direct GraphQL API "
                "(<200ms) para evitar timeouts, colapso de procesos npx y consumo innecesario de tokens."
            )
        }

    # A. File writes / edits guards
    if tool_name in ["write_to_file", "replace_file_content"]:
        target_file = args.get("TargetFile", "")

        # A0. SSoT Sovereign Custom Skills Anti-Pollution Shield
        polluted_skill = is_upstream_skill_pollution(target_file)
        if polluted_skill:
            return {
                "decision": "deny",
                "reason": (
                    f"VIOLACIÓN DE SOBERANÍA SSoT: Prohibido escribir la skill upstream [{polluted_skill}] "
                    "en '/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/skills/'. "
                    "Esa carpeta en Google Drive SSoT es EXCLUSIVA para tus 65 custom skills. "
                    "Las skills upstream de gentle-ai y pocock se ejecutan en caliente en ZCP."
                )
            }

        # A1. SSoT Relative Path Guard
        if contains_relative_0zcp_leak(target_file):
            return {
                "decision": "deny",
                "reason": (
                    "VIOLACIÓN DE RUTA SSoT: Prohibido usar la ruta relativa '0zcp-123/'. "
                    "La ruta canónica y absoluta hacia Google Drive SSoT es '/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/'."
                )
            }

        # A2. Handover Immunity
        if HANDOVER_PATTERN.search(target_file):
            return {
                "decision": "deny",
                "reason": (
                    f"VIOLACIÓN DE HANDOVER IMMUNITY: El archivo [{os.path.basename(target_file)}] "
                    "es un activo de relevo inter-sesión protegido contra modificación o sobreescritura."
                )
            }



        # A3. Skill Pre-Mutation Backup Gate
        if not has_recent_backup(target_file):
            return {
                "decision": "deny",
                "reason": (
                    f"VIOLACIÓN DE ARNÉS FÍSICO N1 (Pre-Mutation Backup): No podés modificar [{os.path.basename(target_file)}] "
                    "sin haber generado previamente un snapshot versionado en '/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak/skills/' o '.../bak/'."
                )
            }

        # A4. Anti-Afán & Anti-AMN Inflow Gate
        transcript_path = payload.get("transcriptPath", "")
        is_plan_draft = "/artifacts/" in target_file and "_v" in target_file
        
        has_inspection = False
        if transcript_path and os.path.exists(transcript_path):
            try:
                with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                recent_lines = lines[-25:] if len(lines) > 25 else lines
                inspection_keywords = [
                    "view_file", "call_mcp_tool", "research", "zerops_",
                    "read_url_content", "plan-validate", "skills-suite-validate",
                    "ssot-parity-check", "planner-validate", "docu-validate"
                ]
                for line in recent_lines:
                    if any(k in line for k in inspection_keywords):
                        has_inspection = True
                        break
            except Exception:
                has_inspection = True
        else:
            has_inspection = True

        if not has_inspection and not is_plan_draft:
            return {
                "decision": "deny",
                "reason": (
                    "VIOLACIÓN ANTI-AFÁN / ANTI-AMN: No podés mutar archivos sin haber inspeccionado código "
                    "(view_file) o investigado (research) en pasos recientes."
                )
            }

        # A4.2 Plan-First Gate & F4 Halt Guard (Anti-Desbocado Invariant)
        # Skills (whether in .agents/skills/ or elsewhere) require Plan-First Gate and user Go!
        is_governance_asset = (
            "/artifacts/" in target_file or
            "/bak/" in target_file or
            ("/.agents/" in target_file and "/skills/" not in target_file) or
            "/.bin/" in target_file or
            "/.atl/" in target_file or
            "/scripts/" in target_file or
            "/scratch/" in target_file or
            target_file.endswith("AGENTS.md") or
            target_file.endswith("00-SUPREME-DIRECTIVE.md")
        ) and ("/skills/" not in target_file and "zerops-astro-skills" not in target_file)
        if not is_governance_asset:
            linear_active_file = "/var/www/artifacts/linear_active.json"
            has_active_plan = os.path.exists(linear_active_file)
            
            # BAI-FAST Bypass (Exceptuar tareas rapidas <10 lineas o bypass explicito)
            is_fast_bypass = False
            if "BAI-FAST" in payload.get("userPrompt", ""):
                is_fast_bypass = True
            elif tool_name in ["write_to_file", "replace_file_content"]:
                c2c = args.get('CodeContent', '') or args.get('ReplacementContent', ''); lines_changed = len(c2c.splitlines()) if c2c else 0
                if lines_changed < 10 and not has_active_plan:
                    is_fast_bypass = True
                    
            if not has_active_plan and not is_fast_bypass:
                return {
                    "decision": "deny",
                    "reason": (
                        f"VIOLACIÓN DE ARNÉS OBSESIVO (Plan-First Gate): Prohibido mutar [{os.path.basename(target_file)}] "
                        f"(código de aplicación o skill) sin contar con un plan arquitectural validado "
                        "mediante 'linear-cli' (generando 'linear_active.json') y el respectivo 'Go' del usuario."
                    )
                }

        # A5. CoHaLo & Skill-Improver Quality Gate
        content_to_check = args.get("CodeContent", "") or args.get("ReplacementContent", "")

        # A5.1 Positive Guidance Guard (Blocks obsolete negative prompt dogma)
        if target_file.endswith(".md") and content_to_check:
            legacy_match = re.search(r'\b(Queda terminantemente prohibido|Do NOT activate under any circumstances|Está terminantemente prohibido)\b', content_to_check, re.IGNORECASE)
            if legacy_match:
                return {
                    "decision": "deny",
                    "reason": (
                        f"VIOLACIÓN DE COHALO / POSITIVE GUIDANCE: Detectado prompt engineering negativo obsoleto ('{legacy_match.group(0)}'). "
                        "Reemplazalo por directivas positivas y arneses físicos ejecutables."
                    )
                }

        # A5.2 Router Token Budget Gate (SKILL.md <= 480 words / ~550 tokens)
        if target_file.endswith("SKILL.md") and tool_name == "write_to_file":
            word_count = len(content_to_check.split())
            if word_count > 480:
                return {
                    "decision": "deny",
                    "reason": (
                        f"VIOLACIÓN DE COHALO LEVEL 2 (Router Bloat): SKILL.md tiene {word_count} palabras "
                        "(límite: 480 palabras / ~550 tokens). Desacoplá especificaciones técnicas hacia "
                        "'references/usage.md' o 'references/infra.md' respetando la revelación progresiva."
                    )
                }

        # A5.2.5 Macro-Visión 360 Dependency Radar
        if "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/" in target_file and tool_name in ("write_to_file", "replace_file_content"):
            if os.path.basename(target_file) == "unisetup.sh":
                for referenced_script in re.findall(r'setup-[a-zA-Z0-9_\-]+\.sh', content_to_check):
                    ref_full = os.path.join("/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts", referenced_script)
                    if not os.path.exists(ref_full):
                        return {
                            "decision": "deny",
                            "reason": (
                                f"VIOLACIÓN DE MACRO-VISIÓN 360 (Dependencia Rota): 'unisetup.sh' invoca "
                                f"[{referenced_script}] pero dicho script no existe en '/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/'. "
                                "Creá o alineá el script aguas abajo antes de incorporarlo al bootstrapper."
                            )
                        }

        # A5.3 AST & Symbol Preservation Guard (Zero Deletion / Lossless Invariant)
        is_protected_code = (
            "/.agents/skills/" in target_file or
            "/0zcp-123/scripts/" in target_file or
            "/.bin/" in target_file or
            "/.agents/rules/" in target_file
        )
        if is_protected_code and tool_name == "write_to_file" and os.path.exists(target_file):
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
                                    f"VIOLACIÓN DE PRESERVACIÓN DE SÍMBOLOS AST: Se eliminaron funciones críticas {missing_funcs} "
                                    f"en [{os.path.basename(target_file)}]. En scripts de plataforma no podés amputar lógica existente sin desacople."
                                )
                            }
                        old_classes = {n.name for n in ast.walk(old_ast) if isinstance(n, ast.ClassDef)}
                        new_classes = {n.name for n in ast.walk(new_ast) if isinstance(n, ast.ClassDef)}
                        missing_classes = old_classes - new_classes
                        if missing_classes:
                            return {
                                "decision": "deny",
                                "reason": (
                                    f"VIOLACIÓN DE PRESERVACIÓN DE SÍMBOLOS AST: Se eliminaron clases críticas {missing_classes} "
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
                                f"VIOLACIÓN DE SEGURIDAD OPERATIVA: Se eliminó el flag de seguridad 'set -e' / 'set -euo pipefail' "
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
                                f"VIOLACIÓN DE PRESERVACIÓN DE FUNCIONES: Se eliminaron funciones críticas {missing_fns} "
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
                            f"VIOLACIÓN DE PRESERVACIÓN DE LÍNEAS (Poda no autorizada): El archivo pasa de {old_lines} a {new_lines} líneas "
                            f"(reducción >30%). Si requerís refactorizar, usá replace_file_content quirúrgico o desacoplá en módulos."
                        )
                    }
            except Exception:
                pass

        # A5.5 Anti-Checklist Theater Guard in Validation Sensors
        if ("validate" in target_file or "check" in target_file) and tool_name == "write_to_file" and content_to_check:
            if re.search(r'>/dev/null\s+2>&1', content_to_check):
                return {
                    "decision": "deny",
                    "reason": (
                        f"VIOLACIÓN DE REALIDAD DE SOFTWARE (Anti-Checklist Theater): "
                        f"Prohibido silenciar errores con '>/dev/null 2>&1' en sensores o validadores [{os.path.basename(target_file)}]. "
                        "Los sensores deben capturar stderr y transparentar cualquier fallo físico real."
                    )
                }

        # A5.4 Physical Syntax Pre-Flight Gate (Zero Syntax Errors)
        if tool_name == "write_to_file" and content_to_check:
            # Python syntax validation
            if target_file.endswith(".py"):
                try:
                    compile(content_to_check, target_file, 'exec')
                except SyntaxError as e:
                    return {
                        "decision": "deny",
                        "reason": (
                            f"VIOLACIÓN DE SINTAXIS REAL (Python SyntaxError): {target_file}:{e.lineno}: {e.msg}\n"
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
                                f"VIOLACIÓN DE SINTAXIS REAL (Bash Syntax Error): {target_file}\n"
                                f"{err_msg}"
                            )
                        }
                except Exception:
                    pass

    # B. Command Guards on run_command
    if tool_name == "run_command":
        cmd = args.get("CommandLine", "")

        # B0. SSoT Sovereign Custom Skills Anti-Pollution Shield
        polluted_skill = is_upstream_skill_pollution(cmd)
        if polluted_skill:
            return {
                "decision": "deny",
                "reason": (
                    f"VIOLACIÓN DE SOBERANÍA SSoT: Prohibido copiar o sincronizar la skill upstream [{polluted_skill}] "
                    "hacia '/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/.agents/skills/'. "
                    "Esa carpeta en Google Drive SSoT es EXCLUSIVA para tus 65 custom skills."
                )
            }

        # B1. SSoT Relative Path Guard
        if contains_relative_0zcp_leak(cmd):
            return {
                "decision": "deny",
                "reason": (
                    "VIOLACIÓN DE RUTA SSoT: Prohibido usar la ruta relativa '0zcp-123/'. "
                    "La ruta canónica y absoluta hacia Google Drive SSoT es '/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/'."
                )
            }

        # B2. Sweeping RM on artifacts / handovers
        if SWEEPING_ARTIFACTS_RM.search(cmd) or (HANDOVER_PATTERN.search(cmd) and re.search(r'\brm\b', cmd)):
            return {
                "decision": "deny",
                "reason": (
                    "VIOLACIÓN DE HANDOVER IMMUNITY: Prohibido ejecutar comandos destructivos o comodines (*) "
                    "que puedan destruir artefactos de relevo inter-sesión en /var/www/artifacts/."
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
            if re.search(r'\bfind\s+.*(/var/www|/baiosfera|baiosfera)', cmd) and not re.search(r'-prune', cmd):
                return {
                    "decision": "deny",
                    "reason": (
                        "VIOLACIÓN DE RENDIMIENTO FUSE / GDRIVE: Prohibido ejecutar 'find' sobre '/var/www' o "
                        "'/baiosfera' sin podar (-prune) '/var/www/baiosfera'. "
                        "Google Drive remoto contiene 5TB y miles de archivos que colapsan I/O y CPU. "
                        "Usá exclusión canónica: find /var/www -path /var/www/baiosfera -prune -o <resto_del_comando> "
                        "o buscá directamente dentro de la subcarpeta local específica."
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
                    parity_proc = subprocess.run(
                        ["/usr/local/bin/ssot-parity-check"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        timeout=15
                    )
                    if parity_proc.returncode != 0:
                        return {
                            "decision": "deny",
                            "reason": (
                                "VIOLACIÓN DE PARIDAD SSoT (CANDADO PRE-PUSH): Prohibido ejecutar 'git push' en repositorios "
                                "de infraestructura o skills mientras exista drift contra Google Drive SSoT. "
                                "El sensor 'ssot-parity-check' detectó discrepancias. Ejecutá 'skills-sync' primero "
                                "para restituir la paridad absoluta antes de empujar cambios al remoto."
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
    assert res.get("decision") == "deny" and ("PRESERVACIÓN" in res.get("reason", "") or "SEGURIDAD" in res.get("reason", "")), f"Expected deny on script mutilation, got {res}"
    print("✓ Test 19 Passed: Platform script mutilation & function deletion blocked (AST & Line Floor)")

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
                "TargetFile": "/var/www/scratch/custom-validate.sh",
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
    assert res.get("decision") == "deny" and "VIOLACIÓN DE MACRO-VISIÓN 360" in res.get("reason", ""), f"Expected deny on broken dependency in unisetup.sh, got {res}"
    print("✓ Test 23 Passed: Broken downstream script dependencies in unisetup.sh blocked (Macro-Visión 360 Radar)")

    # Test 24: Epistemic Inflow Mandate - Plan-First Gate & Subordinated Execution Closure verified
    pi_res = evaluate_hook({"invocationNum": 1})
    steps = pi_res.get("injectSteps", [])
    assert len(steps) > 0 and "Plan-First Gate Obligatorio" in steps[0].get("ephemeralMessage", ""), f"Expected Plan-First Gate notice in PreInvocation, got {pi_res}"
    print("✓ Test 24 Passed: Plan-First Gate Obligatorio & Subordinated Execution Closure verified (Epistemic Inflow Mandate)")

    # Test 25: Zero-Local Isolation & Mandatory Web Grounding Invariant (Physical Research Sensor)
    research_val = subprocess.run(["bash", "/var/www/.agents/skills/research/scripts/research-validate.sh"], capture_output=True, text=True)
    assert research_val.returncode == 0, f"Expected research-validate.sh exit 0, got {research_val.returncode}: {research_val.stderr}\n{research_val.stdout}"
    assert "Rule 9 y Zero-Local Isolation Invariant validados físicamente" in research_val.stdout, f"Missing Zero-Local Isolation confirmation in research-validate output: {research_val.stdout}"
    print("✓ Test 25 Passed: Zero-Local Isolation & Mandatory Web Grounding verified (Physical Research Sensor)")

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

    # Test 30: Plan-First Gate for Skills & Non-Governance Assets
    # Hermetically isolate zero-plan state by temporarily hiding any active plans in artifacts/
    active_plans_backup = []
    artifacts_dir = "/var/www/artifacts"
    try:
        if os.path.exists(artifacts_dir):
            for f in os.listdir(artifacts_dir):
                if f.endswith(".md") and "_v" in f and not any(x in f.lower() for x in [".executed.", ".superseded.", "report"]):
                    old_path = os.path.join(artifacts_dir, f)
                    tmp_path = os.path.join(artifacts_dir, f + ".test_hide")
                    os.rename(old_path, tmp_path)
                    active_plans_backup.append((old_path, tmp_path))

        res_skill = evaluate_hook({
            "transcriptPath": "/nonexistent",
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": "/var/www/.agents/skills/dummy-test-skill/SKILL.md",
                    "CodeContent": "---\nname: dummy-test-skill\ndescription: Test\n---\n# Dummy Test Skill"
                }
            }
        })
        assert res_skill.get("decision") == "deny" and "Plan-First Gate" in res_skill.get("reason", ""), f"Expected deny on skill mutation without plan, got {res_skill}"
        print("✓ Test 30 Passed: Skill mutation without active plan blocked (Plan-First Gate for Skills)")
    finally:
        for old_p, tmp_p in active_plans_backup:
            if os.path.exists(tmp_p):
                os.rename(tmp_p, old_p)

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
    print("✓ Test 33 Passed: Anti-Redundancy Chat Contract & Zero Token Bloat physically verified in PreInvocation")

    print("============================================================")
    print("✅ ALL TOOL-GUARD UNIT TESTS PASSED DETERMINISTICALLY (exit 0)")
    print("============================================================")

def main():
    if "--test" in sys.argv:
        run_tests()
        sys.exit(0)

    if "--cleanup-archive" in sys.argv:
        res = cleanup_artifacts_lifecycle(purge_executed=False)
        print(json.dumps(res))
        sys.exit(0)

    if "--cleanup-session" in sys.argv:
        res = cleanup_artifacts_lifecycle(purge_executed=True)
        print(json.dumps(res))
        sys.exit(0)

    if "--post-tool" in sys.argv:
        auto_sync_governance()
        print(json.dumps({}))
        sys.exit(0)


    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({}))
            sys.exit(0)
        payload = json.loads(raw_input)
        
        # Determine event type
        is_post_tool = "--post-tool" in sys.argv or ("stepIdx" in payload and "invocationNum" not in payload and ("error" in payload or "toolResult" in payload or "status" in payload))
        if is_post_tool:
            auto_sync_governance()
            print(json.dumps({}))
            sys.exit(0)
            
    except Exception as e:
        print(json.dumps({}))
        sys.exit(0)


    result = evaluate_hook(payload)
    print(json.dumps(result))
    sys.exit(0)

if __name__ == "__main__":
    main()
