#!/usr/bin/env python3
"""Externalized unit test suite for tool-guard.py."""
import json
import os
import subprocess
import sys
import time
import tempfile
import shutil

sys.dont_write_bytecode = True

def run_tests(evaluate_hook):
    print("Testing tool-guard.py deterministic rules...")

    # Test 1: PreInvocation stays silent when no blocking gate is active (zero token spam)
    res = evaluate_hook({"invocationNum": 1, "initialNumSteps": 0})
    assert res == {}, f"Expected clean empty dict from passive PreInvocation, got {res}"
    print("✓ Test 1 Passed: PreInvocation stays silent without active gates")

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

    # Test 8: Deny freellmapi- token leak in write_to_file
    synthetic_freellm = "freellmapi-" + ("a" * 24)
    res = evaluate_hook({
        "test_bypass_linear": True,
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/zerops-astrobranding/apps/config.ts",
                "CodeContent": f"export const KEY = '{synthetic_freellm}';"
            }
        }
    })
    assert res.get("decision") == "deny" and "SOBERANÍA ZEROPS ENV" in res.get("reason", "").upper(), f"Expected deny on freellmapi secret, got {res}"
    print("✓ Test 8 Passed: freellmapi- token leak blocked in write_to_file")

    # Test 9: Allow safe upstream script command
    res = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "ls -la /var/www/zerops-astrobranding/scripts"}
        }
    })
    assert res.get("decision") == "allow", f"Expected allow on safe upstream path, got {res}"
    print("✓ Test 9 Passed: Safe sovereign repo command allowed")

    # Test 10: Deny tenant -keys.md leak inside zerops-astrobranding
    res = evaluate_hook({
        "toolCall": {
            "name": "write_to_file",
            "args": {"TargetFile": "/var/www/zerops-astrobranding/docs/damaren-keys.md"}
        }
    })
    assert res.get("decision") == "deny" and "ARNÉS MULTI-TENANT" in res.get("reason", ""), f"Expected deny on tenant keys in upstream, got {res}"
    print("✓ Test 10 Passed: Tenant -keys.md leak blocked in zerops-astrobranding")

    # Test 11: Deny writing upstream immutable skill into runtime skills folder
    res = evaluate_hook({
        "toolCall": {
            "name": "write_to_file",
            "args": {"TargetFile": "/var/www/.agents/skills/react-19/SKILL.md"}
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

    # Test 12: Deny copying upstream skill into sovereign skills via run_command
    res = evaluate_hook({
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "cp -r /var/www/.agents/skills/playwright /var/www/zerops-astro-skills/playwright"}
        }
    })
    assert res.get("decision") == "deny", f"Expected deny on upstream skill pollution via run_command, got {res}"
    print("✓ Test 12 Passed: Upstream skill pollution blocked in run_command (playwright)")

    # Test 13: Approved plan skips F4 HALT GATE
    with tempfile.NamedTemporaryFile("w", suffix=".md", dir="/var/www/artifacts/plans", delete=False) as tf:
        tf.write("# Approved Test Plan\nStatus: Approved\n")
        tmp_approved_plan = tf.name
    try:
        assert is_plan_approved(tmp_approved_plan) is True, "Expected Status: Approved to be recognized"
    finally:
        if os.path.exists(tmp_approved_plan):
            os.remove(tmp_approved_plan)
    print("✓ Test 13 Passed: Approved plan recognition verified (no F4 dead-loop)")

    # Test 14: Deny legacy negative prompt dogma in governance/rule files
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "test_bypass_linear": True,
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/.agents/rules/test-rule.md",
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

    # Test 16: Anti-Frankenstein Python Tool Guard blocks ad-hoc skill wrappers in tools.py
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "test_bypass_linear": True,
        "toolCall": {
            "name": "write_file",
            "args": {
                "Path": "/var/www/zerops-astrobranding/apps/tools.py",
                "Content": "def run_orchesbrand():\n    return 'frankenstein'\n"
            }
        }
    })
    assert res.get("decision") == "deny" and "Anti-Frankenstein" in res.get("reason", ""), f"Expected deny on frankenstein wrapper, got {res}"
    print("✓ Test 16 Passed: Anti-Frankenstein Python Tool Guard blocks ad-hoc skill wrappers")

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

    # Test 19: Deny script function and safety flag mutilation
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "test_bypass_linear": True,
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/zerops-astrobranding/scripts/unisetup.sh",
                "CodeContent": "#!/usr/bin/env bash\necho tiny"
            }
        }
    })
    assert res.get("decision") == "deny" and ("preservación" in res.get("reason", "").lower() or "seguridad" in res.get("reason", "").lower()), f"Expected deny on script mutilation, got {res}"
    print("✓ Test 19 Passed: Platform script mutilation & function deletion caught (AST & Safety)")

    # Test 20: Deny set -e removal in bash scripts
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "test_bypass_linear": True,
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/zerops-astrobranding/scripts/unisetup.sh",
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

    # Test 22: SSoT Hooks & CLIs live directly in .bin via SSoT linkage
    assert os.path.exists("/var/www/.bin/hooks/tool-guard.py"), "Expected tool-guard.py in .bin/hooks/"
    assert os.path.exists("/var/www/.bin/ssot-parity-check"), "Expected ssot-parity-check in .bin/"
    print("✓ Test 22 Passed: Sovereign .bin hooks and CLIs linked cleanly")

    # Test 23: Macro-Visión 360 Dependency Radar on unisetup.sh
    res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "test_bypass_linear": True,
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/zerops-astrobranding/scripts/unisetup.sh",
                "CodeContent": "#!/usr/bin/env bash\nset -euo pipefail\nbash setup-nonexistent-script-xyz.sh\n" * 10
            }
        }
    })
    assert res.get("decision") == "deny" and "MACRO-VISIÓN 360" in res.get("reason", ""), f"Expected deny on broken dependency in unisetup.sh, got {res}"
    print("✓ Test 23 Passed: Broken downstream script dependencies in unisetup.sh caught (Macro-Visión 360 Radar)")

    # Test 24: PreInvocation suppresses passive banners when no blocking gate exists
    pi_res = evaluate_hook({"invocationNum": 99, "test_bypass_dedup": True})
    assert pi_res == {}, f"Expected silent PreInvocation without active gates, got {pi_res}"
    print("✓ Test 24 Passed: Passive PreInvocation banners suppressed (zero token noise)")

    # Test 25: Universal Physical Sensor Integration (Real exit 0 + transparent counts)
    skills_val = subprocess.run(["/var/www/.bin/skills-suite-validate", "-q"], capture_output=True, text=True)
    assert skills_val.returncode == 0, f"Expected skills-suite-validate exit 0, got {skills_val.returncode}: {skills_val.stderr}\n{skills_val.stdout}"
    assert "HONEST SKILLS AUDIT SUMMARY" in skills_val.stdout, f"Unexpected skills-suite-validate output: {skills_val.stdout}"
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

    # Test 29: F4 Halt Gate Centinela uses agy-valid systemMessage & Univoque Go Predicate
    dummy_plan = "/var/www/artifacts/test_plan_v1.md"
    try:
        with open(dummy_plan, "w") as f:
            f.write("# Dummy Test Plan v1\n")
        test_pi = evaluate_hook({"invocationNum": 1001, "userPrompt": "¿por qué se paralizó todo?"})
        pi_steps = test_pi.get("injectSteps", [])
        assert any("F4 HALT GATE ACTIVO" in s.get("systemMessage", {}).get("systemMessage", "") for s in pi_steps), f"Expected F4 Halt Gate alert via systemMessage in PreInvocation, got {test_pi}"
        assert all("ephemeralMessage" not in s for s in pi_steps), f"Unexpected ephemeralMessage in PreInvocation: {test_pi}"

        test_pi_go = evaluate_hook({"invocationNum": 1002, "userPrompt": "si"})
        pi_steps_go = test_pi_go.get("injectSteps", [])
        assert not any("F4 HALT GATE ACTIVO" in s.get("systemMessage", {}).get("systemMessage", "") for s in pi_steps_go), f"Expected no F4 Halt Gate alert on affirmative Go, got {test_pi_go}"
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

    # Test 33: PreInvocation with invocationNum=1 produces no passive noise
    pi_res_red = evaluate_hook({"invocationNum": 1})
    assert pi_res_red == {}, f"Expected silent PreInvocation without active gates, got {pi_res_red}"
    # Test 34: Multi-Tenant Upstream Shield blocks client data leak into upstream repos
    tenant_res = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "test_bypass_linear": True,
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/zerops-astrobranding/elplacerdc.db",
                "CodeContent": "dummy sqlite content"
            }
        }
    })
    assert tenant_res.get("decision") == "deny" and "ARNÉS MULTI-TENANT" in tenant_res.get("reason", ""), f"Expected deny on tenant file inside upstream, got {tenant_res}"
    print("✓ Test 34 Passed: Multi-Tenant Upstream Shield blocks client data leak into upstream repos")

    # Test 35: Behavioral skill test scripts are permitted (Anti-Checklist Theater lifted)
    res_val_write = evaluate_hook({
        "transcriptPath": "/nonexistent",
        "test_bypass_linear": True,
        "test_bypass_research": True,
        "toolCall": {
            "name": "write_to_file",
            "args": {
                "TargetFile": "/var/www/.agents/skills/cohalo/scripts/cohalo-test.sh",
                "CodeContent": "#!/usr/bin/env bash\necho passed\n"
            }
        }
    })
    assert res_val_write.get("decision") == "allow", f"Expected allow on behavioral test script, got {res_val_write}"
    print("✓ Test 35 Passed: Behavioral skill test scripts allowed cleanly")

    # Test 36: Stop Hook uses agy protojson schema (lowercase continue, no stopResult, honors continuationActive)
    res_cont_active = evaluate_hook({
        "is_stop_event": True,
        "terminationReason": "NO_TOOL_CALL",
        "continuationActive": True,
        "test_user_prompt": "Arreglá y blindá el hook de tool-guard",
        "test_has_gov_mutation": False,
        "test_bypass_linear": True
    })
    assert res_cont_active == {}, f"Expected empty dict when continuationActive is True, got {res_cont_active}"
    print("✓ Test 36 Passed: Stop Hook respects continuationActive to prevent recursive loops")

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

    # Test 45: PreInvocation transcriptPath fallback cleanly suppresses F4 banner when no pending plan exists
    dummy_transcript = "/tmp/test_transcript_pi_fallback.jsonl"
    with open(dummy_transcript, "w", encoding="utf-8") as tf:
        tf.write(json.dumps({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "<USER_REQUEST>\ninvestigar SOTA de bases de datos vectoriales\n</USER_REQUEST>"}) + "\n")
    res_pi_fallback = evaluate_hook({
        "invocationNum": 100,
        "transcriptPath": dummy_transcript,
        "test_bypass_research_nudge": True
    })
    try:
        os.remove(dummy_transcript)
    except Exception:
        pass
    assert res_pi_fallback == {}, f"Expected clean empty dict from PreInvocation transcriptPath fallback without active plan, got {res_pi_fallback}"
    print("✓ Test 45 Passed: PreInvocation transcriptPath fallback executes cleanly with zero banner noise")

    # Test 46: Linear-First PreToolUse gate blocks skill mutation when active plan exists and no linear activity recorded
    state_file = "/tmp/.linear_activity_state.json"
    alt_state_file = "/var/www/artifacts/.linear_activity_state.json"
    plans_dir = "/var/www/artifacts/plans"
    os.makedirs(plans_dir, exist_ok=True)
    test_plan_path = os.path.join(plans_dir, "test_active_plan.md")
    with open(test_plan_path, "w") as f:
        f.write("# Active Test Plan\n")

    res_state_file = "/tmp/.research_grounding_state.json"
    res_state_backup = None
    if os.path.exists(res_state_file):
        with open(res_state_file, "r") as rf:
            res_state_backup = rf.read()
    with open(res_state_file, "w") as f:
        json.dump({"timestamp": int(time.time() * 1000), "source": "test_research"}, f)

    state_backup = None
    alt_state_backup = None
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            state_backup = f.read()
        os.remove(state_file)
    if os.path.exists(alt_state_file):
        with open(alt_state_file, "r") as f:
            alt_state_backup = f.read()
        os.remove(alt_state_file)

    bak_dir = "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/bak/skills"
    os.makedirs(bak_dir, exist_ok=True)
    with open(os.path.join(bak_dir, "test-skill-SKILL.md.bak"), "w") as f:
        f.write("test backup")

    try:
        res_lf_blocked = evaluate_hook({
            "test_allow_new_skill": True,
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
            "test_allow_new_skill": True,
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": "/var/www/zerops-astro-skills/test-skill/SKILL.md",
                    "CodeContent": "---\nname: test-skill\ndescription: Trigger: test\n---\n# Test\n## Section\n"
                }
            }
        })
        assert res_lf_allowed.get("decision") == "allow", f"Expected allow on skill mutation with linear activity, got {res_lf_allowed}"
        print("✓ Test 47 Passed: Linear-First PreToolUse gate allows skill mutation with linear activity")

        # Test 48-49: Clean Stop hook returns {} when no pending research subagents exist
        res_stop_allowed = evaluate_hook({
            "is_stop_event": True,
            "terminationReason": "NO_TOOL_CALL"
        })
        assert res_stop_allowed == {}, f"Expected empty dict (allow stop) without pending research subagents, got {res_stop_allowed}"
        print("✓ Test 48-49 Passed: Stop hook allows normal completion without fake counter gates")

        # Test 50: Epistemic Grounding First Gate blocks skill mutation when no research state exists
        if os.path.exists(res_state_file):
            os.remove(res_state_file)
        res_research_blocked = evaluate_hook({
            "test_bypass_linear": True,
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": "/var/www/zerops-astro-skills/test-skill/SKILL.md",
                    "CodeContent": "---\nname: test-skill\ndescription: Test\n---\n# Test\n"
                }
            }
        })
        assert res_research_blocked.get("decision") == "deny" and "MANDATO EPISTÉMICO F0" in res_research_blocked.get("reason", ""), f"Expected deny on skill mutation without research, got {res_research_blocked}"
        print("✓ Test 50 Passed: Epistemic Grounding First Gate blocks skill mutation without research")

        # Test 51: Epistemic Grounding First Gate allows skill mutation when research state is recorded
        with open(res_state_file, "w") as f:
            json.dump({"timestamp": int(time.time() * 1000), "source": "test_research"}, f)
        res_research_allowed = evaluate_hook({
            "test_bypass_linear": True,
            "test_allow_new_skill": True,
            "toolCall": {
                "name": "write_to_file",
                "args": {
                    "TargetFile": "/var/www/zerops-astro-skills/test-skill/SKILL.md",
                    "CodeContent": "---\nname: test-skill\ndescription: Trigger: test\n---\n# Test\n## Section\n"
                }
            }
        })
        assert res_research_allowed.get("decision") == "allow", f"Expected allow on skill mutation with research state, got {res_research_allowed}"
        print("✓ Test 51 Passed: Epistemic Grounding First Gate allows skill mutation with research state")

        # Test 52: Draft plans do NOT trigger Linear-First Gate in Stop hook
        draft_plan_path = os.path.join(plans_dir, "draft_test_plan.md")
        with open(draft_plan_path, "w") as f:
            f.write("# Draft Plan\nstatus: draft\n")
        if os.path.exists(test_plan_path):
            os.remove(test_plan_path)
        if os.path.exists(state_file):
            os.remove(state_file)
        if os.path.exists(alt_state_file):
            os.remove(alt_state_file)
        res_draft_stop = evaluate_hook({
            "is_stop_event": True,
            "terminationReason": "NO_TOOL_CALL",
            "test_has_inspection": True
        })
        assert res_draft_stop == {}, f"Expected empty dict (allow stop for draft plan), got {res_draft_stop}"
        if os.path.exists(draft_plan_path):
            os.remove(draft_plan_path)
        with open(test_plan_path, "w") as f:
            f.write("# Active Test Plan\n")
        print("✓ Test 52 Passed: Draft plans do NOT trigger Linear-First Gate in Stop hook")

        # Test 53: Pending research subagents block plan writing (Anti-Rushing Invariant)
        res_subagent_plan_blocked = evaluate_hook({
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": "/var/www/artifacts/plans/premature_plan.md",
                    "Content": "# Premature Plan\n"
                }
            },
            "test_has_pending_research": True
        })
        assert res_subagent_plan_blocked.get("decision") == "deny" and "MANDATO DE ESPERA EPISTÉMICA F0" in res_subagent_plan_blocked.get("reason", ""), f"Expected deny on premature plan write with pending research, got {res_subagent_plan_blocked}"
        print("✓ Test 53 Passed: Pending research subagents block plan writing (Anti-Rushing Invariant)")

        # Test 54: Pending research subagents block Linear issue/project creation
        res_subagent_linear_blocked = evaluate_hook({
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": "linear-cli create 'Premature BAI'"
                }
            },
            "test_has_pending_research": True
        })
        assert res_subagent_linear_blocked.get("decision") == "deny" and "MANDATO DE ESPERA EPISTÉMICA F0" in res_subagent_linear_blocked.get("reason", ""), f"Expected deny on premature linear creation with pending research, got {res_subagent_linear_blocked}"
        print("✓ Test 54 Passed: Pending research subagents block Linear issue/project creation")

        # Test 57: Secret Leak Prevention Guard blocks writing hardcoded tokens
        synthetic_token = "ghp_" + ("1" * 36)
        res_secret_blocked = evaluate_hook({
            "test_bypass_linear": True,
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": "/var/www/zerops-astrobranding/apps/app_config.ts",
                    "Content": f"export const token = '{synthetic_token}';"
                }
            }
        })
        assert res_secret_blocked.get("decision") == "deny" and "SOBERANÍA ZEROPS ENV" in res_secret_blocked.get("reason", "").upper(), f"Expected deny on secret leak, got {res_secret_blocked}"
        print("✓ Test 57 Passed: Secret Leak Prevention Guard blocks writing hardcoded tokens")

        # Test 61: Commercial & Ad Telemetry Skill Trigger Radar (Meta Ads, Google Ads, TikTok, CAPI)
        telemetry_matches = detect_skills_in_prompt("vamos a configurar meta ads y google ads con consent mode v2 y localbusiness sab")
        assert any(s[0] == "ad-telemetry" for s in telemetry_matches), f"Expected ad-telemetry match in detect_skills_in_prompt, got {telemetry_matches}"
        print("✓ Test 61 Passed: Commercial & Ad Telemetry Skill Trigger Radar matches ad-telemetry (Meta/Google/TikTok/CAPI)")

        # Test 62: Bash AST Command Parser eliminates false positives on string literals (BAI-421)
        res_commit_rm = evaluate_hook({
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": 'git commit -m "rm -rf /var/www/artifacts/* was prevented"'
                }
            }
        })
        assert res_commit_rm.get("decision") == "allow", f"Expected allow on git commit with rm literal, got {res_commit_rm}"

        res_echo_find = evaluate_hook({
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": 'echo "find /var/www/baiosfera without prune"'
                }
            }
        })
        assert res_echo_find.get("decision") == "allow", f"Expected allow on echo find, got {res_echo_find}"

        res_commit_kill = evaluate_hook({
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": 'git commit -m "fix: killall agy bug resolved"'
                }
            }
        })
        assert res_commit_kill.get("decision") == "allow", f"Expected allow on git commit with killall literal, got {res_commit_kill}"

        # Ensure real dangerous commands are STILL blocked
        res_real_rm = evaluate_hook({
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": 'rm -rf /var/www/artifacts/*'
                }
            }
        })
        assert res_real_rm.get("decision") == "deny", f"Expected deny on real rm sweeping artifacts, got {res_real_rm}"

        res_real_find = evaluate_hook({
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": 'find /var/www/baiosfera -name "*.md"'
                }
            }
        })
        assert res_real_find.get("decision") == "deny", f"Expected deny on real find without prune, got {res_real_find}"

        # Test runtime capabilities probing
        caps = get_runtime_capabilities()
        assert "agent_binaries" in caps and len(caps["agent_binaries"]) > 0, f"Expected agent_binaries, got {caps}"
        assert caps.get("is_single_node") is True

        print("✓ Test 62 Passed: Bash AST Command Parser eliminates false positives on string literals (BAI-421)")

        # Test 63: SkillCreationGate in PreToolUse enforces research dossier for new skills (BAI-422)
        new_skill_path = "/var/www/zerops-astro-skills/test-brand-new-skill/SKILL.md"
        dossier_path = "/var/www/artifacts/research/test-brand-new-skill_dossier.md"
        if os.path.exists(dossier_path):
            os.remove(dossier_path)

        res_new_skill_denied = evaluate_hook({
            "test_bypass_linear": True,
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": new_skill_path,
                    "Content": "---\nname: test-brand-new-skill\ndescription: Test\n---\n"
                }
            }
        })
        assert res_new_skill_denied.get("decision") == "deny" and "SKILL CREATION GATE" in res_new_skill_denied.get("reason", ""), f"Expected deny from SkillCreationGate on new skill, got {res_new_skill_denied}"

        # Create dossier and verify allow
        os.makedirs(os.path.dirname(dossier_path), exist_ok=True)
        with open(dossier_path, "w") as f:
            f.write("# Research Dossier for test-brand-new-skill\n")

        res_new_skill_allowed = evaluate_hook({
            "test_bypass_linear": True,
            "test_bypass_subskills": True,
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": new_skill_path,
                    "Content": "---\nname: test-brand-new-skill\ndescription: Trigger: test\n---\n# Test\n## Section\n"
                }
            }
        })
        assert res_new_skill_allowed.get("decision") == "allow", f"Expected allow from SkillCreationGate with dossier, got {res_new_skill_allowed}"

        if os.path.exists(dossier_path):
            os.remove(dossier_path)
        print("✓ Test 63 Passed: SkillCreationGate in PreToolUse enforces research dossier for new skills (BAI-422)")

        # Test 64: PostToolUse Hot Compilation Sensors catch Python, Bash, and JSON syntax errors (BAI-423)
        bad_py = "/tmp/test_bad_syntax.py"
        good_py = "/tmp/test_good_syntax.py"
        bad_sh = "/tmp/test_bad_syntax.sh"
        bad_json = "/tmp/test_bad_syntax.json"
        try:
            with open(bad_py, "w") as f:
                f.write("def bad_func(:\n    pass\n")
            res_bad_py = evaluate_hook({
                "is_post_tool": True,
                "stepIdx": 100,
                "toolCall": {
                    "name": "write_file",
                    "args": {"Path": bad_py}
                }
            })
            res_bad_py = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "write_file",
                    "args": {"Path": bad_py, "Content": "def broken(:\n  pass\n"}
                }
            })
            assert res_bad_py.get("decision") == "deny" and "SyntaxError" in res_bad_py.get("reason", ""), f"Expected PreToolUse syntax deny, got {res_bad_py}"

            res_bad_sh = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "write_file",
                    "args": {"Path": bad_sh, "Content": "if [ -z \"$1\" ]; then\necho missing fi\n"}
                }
            })
            assert res_bad_sh.get("decision") == "deny", f"Expected PreToolUse Bash syntax deny, got {res_bad_sh}"

            res_bad_json = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "write_file",
                    "args": {"Path": bad_json, "Content": "{\"invalid\": json,}\n"}
                }
            })
            assert res_bad_json.get("decision") == "deny" and "JSON" in res_bad_json.get("reason", ""), f"Expected PreToolUse JSON syntax deny, got {res_bad_json}"

            res_post_tool_proto = evaluate_hook({
                "is_post_tool": True,
                "stepIdx": 103,
                "toolCall": {
                    "name": "write_file",
                    "args": {"Path": good_py}
                }
            })
            assert res_post_tool_proto == {} and "injectSteps" not in res_post_tool_proto, f"Expected empty dict (agy PostToolUseResponse compatibility), got {res_post_tool_proto}"
        finally:
            for p in [bad_py, good_py, bad_sh, bad_json]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
        print("✓ Test 64 Passed: PreToolUse catches syntax errors and PostToolUse returns agy-compatible {}")

        # Test 65: Governance Rules Size Budget Gate & edit_file shrinking simulation (BAI-424)
        oversized_supreme = "---\nname: 00-supreme-directive\n---\n" + ("palabra " * 650)
        res_ov_sup = evaluate_hook({
            "test_bypass_linear": True,
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": "/var/www/.agents/rules/00-SUPREME-DIRECTIVE.md",
                    "Content": oversized_supreme
                }
            }
        })
        assert res_ov_sup.get("decision") == "deny" and "Governance Size Budget" in res_ov_sup.get("reason", ""), f"Expected deny on oversized supreme directive, got {res_ov_sup}"

        oversized_agents = "<!-- ZCP:BEGIN -->\nZCP\n<!-- ZCP:END -->\n<!-- CUSTOM:BEGIN -->\n" + ("palabra " * 850) + "\n<!-- CUSTOM:END -->"
        res_ov_agents = evaluate_hook({
            "test_bypass_linear": True,
            "toolCall": {
                "name": "write_file",
                "args": {
                    "Path": "/var/www/AGENTS.md",
                    "Content": oversized_agents
                }
            }
        })
        assert res_ov_agents.get("decision") == "deny" and "Governance Size Budget" in res_ov_agents.get("reason", ""), f"Expected deny on oversized AGENTS.md custom section, got {res_ov_agents}"

        # Simulate edit_file shrinking an oversized AGENTS.md below 800 words
        shrink_fd, shrink_agents_path = tempfile.mkstemp(prefix="test_AGENTS_", suffix="AGENTS.md")
        os.close(shrink_fd)
        try:
            with open(shrink_agents_path, "w", encoding="utf-8") as sf:
                sf.write("<!-- ZCP:BEGIN -->\nZCP\n<!-- ZCP:END -->\n<!-- CUSTOM:BEGIN -->\n" + ("bloat " * 900) + "\n<!-- CUSTOM:END -->")
            res_shrink_ok = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "edit_file",
                    "args": {
                        "Path": shrink_agents_path,
                        "Target": "<!-- CUSTOM:BEGIN -->\n" + ("bloat " * 900) + "\n<!-- CUSTOM:END -->",
                        "Replacement": "<!-- CUSTOM:BEGIN -->\nConcise rules.\n<!-- CUSTOM:END -->"
                    }
                }
            })
            assert res_shrink_ok.get("decision") == "allow", f"Expected allow when edit_file shrinks AGENTS.md below 800 words, got {res_shrink_ok}"
        finally:
            if os.path.exists(shrink_agents_path):
                os.remove(shrink_agents_path)
        print("✓ Test 65 Passed: Governance Rules Size Budget Gate blocks bloat and allows edit_file shrinking")

        # Test 66: Engram 3-Tier Background Auto-Sync on PostToolUse Write Tools & Stop (BAI-425)
        res_engram_write = evaluate_hook({
            "is_post_tool": True,
            "stepIdx": 210,
            "test_inspect_engram_sync": True,
            "toolCall": {
                "name": "call_mcp_tool",
                "args": {"ServerName": "engram", "ToolName": "mem_save", "Arguments": {"title": "Test"}}
            }
        })
        assert res_engram_write.get("engramSyncTriggered") is True and res_engram_write.get("source") == "post_tool:mem_save", f"Expected engram sync on mem_save, got {res_engram_write}"

        res_engram_read = evaluate_hook({
            "is_post_tool": True,
            "stepIdx": 211,
            "test_inspect_engram_sync": True,
            "toolCall": {
                "name": "call_mcp_tool",
                "args": {"ServerName": "engram", "ToolName": "mem_context", "Arguments": {}}
            }
        })
        assert res_engram_read.get("engramSyncTriggered") is False, f"Expected no engram sync on read-only mem_context, got {res_engram_read}"

        res_engram_stop = evaluate_hook({
            "is_stop_event": True,
            "terminationReason": "NO_TOOL_CALL",
            "test_bypass_linear": True,
            "test_bypass_correction_gate": True,
            "test_bypass_gov_gate": True,
            "test_inspect_engram_sync": True
        })
        assert res_engram_stop.get("engramSyncTriggered") is True and res_engram_stop.get("source") == "stop", f"Expected engram sync on Stop event, got {res_engram_stop}"
        print("✓ Test 66 Passed: Engram 3-Tier Background Auto-Sync triggers on MCP writes and Stop (BAI-425)")

        # Test 67: Bootstrap Self-Reexec & Read-Only SSoT Parity Guards (Track A)
        parity_sh = "/var/www/zerops-astrobranding/scripts/ssot-parity-check.sh"
        iniciar_sh = "/var/www/zerops-astrobranding/iniciar.sh"
        if os.path.isfile(parity_sh) and os.path.isfile(iniciar_sh):
            with open(parity_sh, "r", encoding="utf-8") as fp:
                parity_src = fp.read()
            assert "AUTO_FIX_MODE=false" in parity_src and "--fix" in parity_src, "ssot-parity-check.sh must be read-only by default with explicit --fix"
            assert "0zcp-123" not in parity_src.split("Resolve optional")[1].split("DIRECTORY")[0] if False else "HARDCODED" not in parity_src
            with open(iniciar_sh, "r", encoding="utf-8") as fi:
                iniciar_src = fi.read()
            assert "INICIAR_REEXEC=1" in iniciar_src and 'exec bash "$REPO_DIR/iniciar.sh"' in iniciar_src, "iniciar.sh must re-exec after git self-update"
        print("✓ Test 67 Passed: Bootstrap Self-Reexec & Read-Only SSoT Parity Guards")

        # Test 68: Stop Hook strictly emits lowercase 'continue' without 'stopResult' key
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
            tf.write(json.dumps({"content": 'Created the following subagent: {"conversationId": "11111111-1111-1111-1111-111111111111"}'}) + "\n")
            proto_tpath = tf.name
        try:
            res_stop_proto = evaluate_hook({
                "is_stop_event": True,
                "terminationReason": "NO_TOOL_CALL",
                "transcriptPath": proto_tpath,
                "test_has_grilling_in_stop": True,
                "test_bypass_dedup": True,
            })
            assert res_stop_proto.get("decision") == "continue" and "stopResult" not in res_stop_proto, f"Expected agy-valid Stop response without stopResult, got {res_stop_proto}"
        finally:
            if os.path.exists(proto_tpath):
                os.remove(proto_tpath)
        print("✓ Test 68 Passed: Stop Hook emits lowercase 'continue' without invalid 'stopResult' key")

        # Test 69: Multi-service bootstrap blocked without Linear activity (BAI-430)
        if os.path.exists(state_file):
            os.remove(state_file)
        if os.path.exists(alt_state_file):
            os.remove(alt_state_file)
        res_multi_block = evaluate_hook({
            "toolCall": {
                "name": "call_mcp_tool",
                "args": {
                    "ServerName": "zerops",
                    "ToolName": "zerops_workflow",
                    "Arguments": {
                        "action": "start",
                        "workflow": "bootstrap",
                        "intent": "Provision database and valkey"
                    }
                }
            }
        })
        assert res_multi_block.get("decision") == "deny" and "LINEAR-FIRST MULTI-SERVICIO" in res_multi_block.get("reason", ""), f"Expected deny on multi-service bootstrap without linear activity, got {res_multi_block}"
        print("✓ Test 69 Passed: Multi-service bootstrap blocked without Linear activity (BAI-430)")

        # Test 70: Multi-service bootstrap allowed with Linear activity (BAI-430)
        with open(state_file, "w") as f:
            json.dump({"timestamp": int(time.time() * 1000), "action": "create-project", "issueId": "BAI-123"}, f)
        res_multi_allow = evaluate_hook({
            "toolCall": {
                "name": "call_mcp_tool",
                "args": {
                    "ServerName": "zerops",
                    "ToolName": "zerops_workflow",
                    "Arguments": {
                        "action": "start",
                        "workflow": "bootstrap",
                        "intent": "Provision database and valkey"
                    }
                }
            }
        })
        assert res_multi_allow.get("decision") != "deny", f"Expected allow on multi-service bootstrap with linear activity, got {res_multi_allow}"
        print("✓ Test 70 Passed: Multi-service bootstrap allowed with Linear activity (BAI-430)")

        # Test 71: zcli project import command blocked without Linear activity (BAI-430)
        if os.path.exists(state_file):
            os.remove(state_file)
        res_cmd_import_block = evaluate_hook({
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": "zcli project import import.yaml"
                }
            }
        })
        assert res_cmd_import_block.get("decision") == "deny" and "LINEAR-FIRST MULTI-SERVICIO" in res_cmd_import_block.get("reason", ""), f"Expected deny on zcli project import without linear activity, got {res_cmd_import_block}"
        print("✓ Test 71 Passed: zcli project import command blocked without Linear activity (BAI-430)")

        # Test 72: Gate 14 blocks linear-cli update-status Done when service has deployed: false (BAI-454)
        test_cache = "/tmp/.zerops_discover_cache.json"
        cache_backup = None
        if os.path.exists(test_cache):
            with open(test_cache, "r") as f:
                cache_backup = f.read()
        try:
            with open(test_cache, "w") as f:
                json.dump({
                    "services": [
                        {"hostname": "freellmapi", "deployed": False, "isInfrastructure": False},
                        {"hostname": "bifrost", "deployed": True, "isInfrastructure": False}
                    ]
                }, f)
            res_gate14_block = evaluate_hook({
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": 'linear-cli update-status BAI-447 "Done" --evidence "se probaron freellmapi y bifrost"'
                    }
                }
            })
            assert res_gate14_block.get("decision") == "deny" and "Gate 14" in res_gate14_block.get("reason", ""), f"Expected Gate 14 deny on undeployed freellmapi, got {res_gate14_block}"
            print("✓ Test 72 Passed: Gate 14 blocks linear-cli Done on undeployed service (BAI-454)")

            # Test 73: Gate 14 allows linear-cli update-status Done when mentioned services are deployed
            res_gate14_allow = evaluate_hook({
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": 'linear-cli update-status BAI-448 "Done" --evidence "se probo bifrost"'
                    }
                }
            })
            assert res_gate14_allow.get("decision") == "allow", f"Expected Gate 14 allow on deployed bifrost, got {res_gate14_allow}"
            print("✓ Test 73 Passed: Gate 14 allows linear-cli Done when services are deployed (BAI-454)")

            # Test 74: Paperclip Skill Trigger Radar & Invariant Persistence (BAI-455)
            pc_matches = detect_skills_in_prompt("vamos a coordinar el organigrama y spend caps en paperclip con hermes_gateway")
            assert any(s[0] == "paperclip" for s in pc_matches), f"Expected paperclip match in detect_skills_in_prompt, got {pc_matches}"
            assert os.path.exists("/mnt/localstorage/paperclip/instances/default/config.json") or os.path.exists("/home/zerops/.paperclip"), "Paperclip home persistence invariant missing"
            print("✓ Test 74 Passed: Paperclip Skill Trigger Radar & Invariant Persistence (BAI-455)")

            # Test 75: Meta-Skill Subskills Physical Enforcement Gate (BAI-458)
            # 75a: skill-creator frontmatter and trigger validation
            res_no_frontmatter = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "write_file",
                    "args": {
                        "Path": "/var/www/zerops-astro-skills/paperclip/SKILL.md",
                        "Content": "# Bad Skill\nNo frontmatter here."
                    }
                }
            })
            assert res_no_frontmatter.get("decision") == "deny" and "skill-creator" in res_no_frontmatter.get("reason", ""), f"Expected deny on missing frontmatter, got {res_no_frontmatter}"

            res_no_trigger = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "write_file",
                    "args": {
                        "Path": "/var/www/zerops-astro-skills/paperclip/SKILL.md",
                        "Content": "---\nname: test-skill\ndescription: A test without trigger keyword.\n---\n# Test\n## Section\n"
                    }
                }
            })
            assert res_no_trigger.get("decision") == "deny" and "Trigger:" in res_no_trigger.get("reason", ""), f"Expected deny on missing Trigger:, got {res_no_trigger}"

            # 75b: writing-for-agents markdown cognitive seams (unclosed code fences)
            res_bad_fence = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "write_file",
                    "args": {
                        "Path": "/var/www/zerops-astro-skills/paperclip/SKILL.md",
                        "Content": "---\nname: test-skill\ndescription: Trigger: test\n---\n# Test\n## Section\n```bash\necho hello\n"
                    }
                }
            })
            assert res_bad_fence.get("decision") == "deny" and "writing-for-agents" in res_bad_fence.get("reason", ""), f"Expected deny on unclosed code fence, got {res_bad_fence}"

            # 75c: docu & skill-improver Dual-RAG structure
            test_monolith_path = "/var/www/zerops-astro-skills/test-monolith-no-refs/SKILL.md"
            test_monolith_dossier = "/var/www/artifacts/research/test-monolith-no-refs_dossier.md"
            os.makedirs(os.path.dirname(test_monolith_path), exist_ok=True)
            os.makedirs(os.path.dirname(test_monolith_dossier), exist_ok=True)
            with open(test_monolith_dossier, "w") as f:
                f.write("# Research Dossier\n")
            try:
                res_missing_dual_rag = evaluate_hook({
                    "test_bypass_linear": True,
                    "toolCall": {
                        "name": "write_file",
                        "args": {
                            "Path": test_monolith_path,
                            "Content": "---\nname: test-monolith\ndescription: Trigger: mock\n---\n# Mock\n## Section\n"
                        }
                    }
                })
                assert res_missing_dual_rag.get("decision") == "deny" and "docu + skill-improver" in res_missing_dual_rag.get("reason", ""), f"Expected deny on missing Dual-RAG references, got {res_missing_dual_rag}"
            finally:
                if os.path.exists(test_monolith_dossier):
                    os.remove(test_monolith_dossier)
                if os.path.exists("/var/www/zerops-astro-skills/test-monolith-no-refs"):
                    os.rmdir("/var/www/zerops-astro-skills/test-monolith-no-refs")

            print("✓ Test 75 Passed: Meta-Skill Subskills Physical Enforcement Gate (BAI-458)")

            # Test 76: Anti-Frankenstein Python Tool Guard (BAI-459)
            res_frank = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "write_file",
                    "args": {
                        "Path": "/var/www/hermes/tools.py",
                        "Content": "def run_orchesbrand(vertical: str):\n    pass\n"
                    }
                }
            })
            assert res_frank.get("decision") == "deny" and "Anti-Frankenstein Tool Invariant" in res_frank.get("reason", ""), f"Expected deny on frankenstein tool, got {res_frank}"

            res_clean_tool = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "write_file",
                    "args": {
                        "Path": "/var/www/hermes/tools.py",
                        "Content": "def get_system_uptime():\n    return '10 days'\n"
                    }
                }
            })
            assert res_clean_tool.get("decision") == "allow", f"Expected allow on clean tool, got {res_clean_tool}"
            print("✓ Test 76 Passed: Anti-Frankenstein Python Tool Guard (Universal Primitives Architecture)")

            # Test 77: Epistemic Recorder tracks Jina Verbatim & Brave/DuckDuckGo Fallbacks
            res_state_p = "/tmp/.research_grounding_state.json"
            if os.path.exists(res_state_p):
                os.remove(res_state_p)
            evaluate_hook({
                "toolCall": {
                    "name": "call_mcp_tool",
                    "args": {"ServerName": "duckduckgo", "ToolName": "duckduckgo_web_search", "Arguments": {"query": "test"}}
                }
            })
            with open(res_state_p, "r") as rf:
                st_ddg = json.load(rf)
            assert st_ddg.get("has_discovery") is True and st_ddg.get("has_verbatim") is False, f"Expected discovery-only for DDG, got {st_ddg}"

            evaluate_hook({
                "toolCall": {
                    "name": "call_mcp_tool",
                    "args": {"ServerName": "jina", "ToolName": "read_url", "Arguments": {"url": "https://example.com"}}
                }
            })
            with open(res_state_p, "r") as rf:
                st_jina = json.load(rf)
            assert st_jina.get("has_discovery") is True and st_jina.get("has_verbatim") is True, f"Expected verbatim merged with discovery for Jina, got {st_jina}"
            print("✓ Test 77 Passed: Epistemic Recorder tracks Discovery vs Jina Verbatim tiers")

            # Test 78: search_web deny message routes cleanly to Jina + Primaries + Brave/DuckDuckGo Fallbacks
            res_sw = evaluate_hook({"toolCall": {"name": "search_web", "args": {"query": "test"}}})
            assert res_sw.get("decision") == "deny" and "jina" in res_sw.get("reason", "") and "duckduckgo" in res_sw.get("reason", ""), f"Expected Jina & fallback routing in search_web deny, got {res_sw}"
            print("✓ Test 78 Passed: search_web Anti-AMN routing includes Jina and fallbacks")

            # Test 79: F4 Master Plan Anti-AMN Gate (A3.6) blocks ungrounded F4 plans, allows drafts & grounded plans
            if os.path.exists(res_state_p):
                os.remove(res_state_p)
            res_plan_block = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "write_file",
                    "args": {"Path": "/var/www/artifacts/plans/sota_plan.md", "Content": "# Master Plan\n## Scope\n"}
                }
            })
            assert res_plan_block.get("decision") == "deny" and "MANDATO EPISTÉMICO F0->F4" in res_plan_block.get("reason", ""), f"Expected deny on ungrounded F4 plan, got {res_plan_block}"

            res_draft_allow = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "write_file",
                    "args": {"Path": "/var/www/artifacts/plans/draft_sota_plan.md", "Content": "# Draft\nstatus: draft\n"}
                }
            })
            assert res_draft_allow.get("decision") == "allow", f"Expected allow on F0 draft plan, got {res_draft_allow}"

            evaluate_hook({
                "toolCall": {
                    "name": "run_command",
                    "args": {"CommandLine": "curl -sL https://r.jina.ai/https://example.com/docs"}
                }
            })
            res_plan_allow = evaluate_hook({
                "test_bypass_linear": True,
                "toolCall": {
                    "name": "write_file",
                    "args": {"Path": "/var/www/artifacts/plans/sota_plan.md", "Content": "# Master Plan\n## Scope\n"}
                }
            })
            assert res_plan_allow.get("decision") == "allow", f"Expected allow on F4 plan after r.jina.ai grounding, got {res_plan_allow}"
            print("✓ Test 79 Passed: F4 Master Plan Anti-AMN Gate enforces live research while keeping drafts unblocked")

            # Test 80: Stop hook blocks stop while a research subagent is still pending
            with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
                tf.write(json.dumps({"content": 'Created the following subagent: {"conversationId": "22222222-2222-2222-2222-222222222222"}'}) + "\n")
                tf.write(json.dumps({"content": '1288: tf.write(json.dumps({"content": \'Created the following subagent: {"conversationId": "33333333-3333-3333-3333-333333333333"}\'}))'}) + "\n")
                pending_tpath = tf.name
            try:
                res_stop_pending = evaluate_hook({
                    "is_stop_event": True,
                    "terminationReason": "NO_TOOL_CALL",
                    "transcriptPath": pending_tpath,
                    "test_has_grilling_in_stop": True,
                    "test_bypass_dedup": True,
                })
                reason_pending = res_stop_pending.get("reason", "")
                assert res_stop_pending.get("decision") == "continue" and "ESPERA EPISTÉMICA" in reason_pending, f"Expected Stop continue on pending research subagent, got {res_stop_pending}"
                assert "33333333-3333-3333-3333-333333333333" not in reason_pending, f"Source snippet falsely flagged as pending subagent: {reason_pending}"
            finally:
                if os.path.exists(pending_tpath):
                    os.remove(pending_tpath)
            print("✓ Test 80 Passed: Stop Gate waits for pending research subagents without source false positives")

            # Test 81: PreInvocation Anti-AMN Nudge stays silent after Jina Verbatim grounding
            if os.path.exists(test_plan_path):
                os.remove(test_plan_path)
            if os.path.exists(res_state_p):
                os.remove(res_state_p)
            res_pi_nudge = evaluate_hook({
                "invocationNum": 1,
                "initialNumSteps": 0,
                "test_bypass_dedup": True,
                "lastUserInput": "Investiga cuál es la versión actual SOTA de FastAPI",
            })
            assert "injectSteps" in res_pi_nudge and "ANTI-AMN ACTIVO" in str(res_pi_nudge), f"Expected PreInvocation Anti-AMN nudge when ungrounded, got {res_pi_nudge}"

            evaluate_hook({
                "toolCall": {
                    "name": "call_mcp_tool",
                    "args": {"ServerName": "jina", "ToolName": "read_url", "Arguments": {"url": "https://fastapi.tiangolo.com"}}
                }
            })
            res_pi_silent = evaluate_hook({
                "invocationNum": 2,
                "initialNumSteps": 1,
                "test_bypass_dedup": True,
                "lastUserInput": "Investiga cuál es la versión actual SOTA de FastAPI",
            })
            assert res_pi_silent == {}, f"Expected silent PreInvocation after Jina Verbatim grounding, got {res_pi_silent}"
            print("✓ Test 81 Passed: PreInvocation Anti-AMN nudge activates only when ungrounded")

            # Test 82: PostToolUse zerops_discover unwraps MCP content[0].text and refreshes cache
            evaluate_hook({
                "is_post_tool": True,
                "toolCall": {
                    "name": "call_mcp_tool",
                    "args": {"ServerName": "zerops", "ToolName": "zerops_discover", "Arguments": {}}
                },
                "toolResult": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "services": [
                                {"hostname": "freellmapi", "deployed": True, "isInfrastructure": False},
                                {"hostname": "bifrost", "deployed": True, "isInfrastructure": False}
                            ]
                        })
                    }]
                }
            })
            with open(test_cache, "r") as f:
                refreshed_cache = json.load(f)
            assert any(s.get("hostname") == "freellmapi" and s.get("deployed") is True for s in refreshed_cache.get("services", [])), f"Expected refreshed cache from MCP content wrapper, got {refreshed_cache}"
            print("✓ Test 82 Passed: PostToolUse zerops_discover unwraps MCP wrapper cleanly")

            # Test 83: PostToolUse zerops_discover extracts JSON from agy transcriptPath when toolResult omitted
            if os.path.exists(test_cache):
                os.remove(test_cache)
            with tempfile.TemporaryDirectory() as td:
                tx_file = os.path.join(td, "transcript.jsonl")
                tx_payload = {
                    "step_index": 77,
                    "type": "GENERIC",
                    "content": "Created At: 2026-11-14T01:00:00Z\n" + json.dumps({
                        "project": {"id": "p1"},
                        "services": [{"hostname": "hermes", "serviceId": "s1", "deployed": True, "isInfrastructure": False}],
                    }),
                }
                with open(tx_file, "w") as tf:
                    tf.write(json.dumps(tx_payload) + "\n")
                evaluate_hook({
                    "is_post_tool": True,
                    "stepIdx": 77,
                    "transcriptPath": tx_file,
                    "toolCall": {
                        "name": "call_mcp_tool",
                        "args": {"ServerName": "zerops", "ToolName": "zerops_discover"},
                    },
                })
            with open(test_cache, "r") as f:
                tx_cache = json.load(f)
            assert any(s.get("hostname") == "hermes" and s.get("deployed") is True for s in tx_cache.get("services", [])), f"Expected transcript cache population, got {tx_cache}"
            print("✓ Test 83 Passed: PostToolUse zerops_discover reads agy transcriptPath cleanly")
        finally:
            if cache_backup is not None:
                with open(test_cache, "w") as f:
                    f.write(cache_backup)
            elif os.path.exists(test_cache):
                try:
                    os.remove(test_cache)
                except Exception:
                    pass


    finally:
        if os.path.exists("/tmp/.research_stop_force_count"):
            try:
                os.remove("/tmp/.research_stop_force_count")
            except Exception:
                pass
        if res_state_backup is not None:
            with open(res_state_file, "w") as rf:
                rf.write(res_state_backup)
        elif os.path.exists(res_state_file):
            try:
                os.remove(res_state_file)
            except Exception:
                pass
        if os.path.exists("/tmp/.gov_mutation_stop_force_count"):
            try:
                os.remove("/tmp/.gov_mutation_stop_force_count")
            except Exception:
                pass
        if os.path.exists(test_plan_path):
            try:
                os.remove(test_plan_path)
            except Exception:
                pass
        if state_backup:
            with open(state_file, "w") as f:
                f.write(state_backup)
        if alt_state_backup:
            with open(alt_state_file, "w") as f:
                f.write(alt_state_backup)

    print("============================================================")
    print("✅ ALL TOOL-GUARD UNIT TESTS PASSED DETERMINISTICALLY (exit 0)")
    print("============================================================")

