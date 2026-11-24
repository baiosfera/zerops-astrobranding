#!/usr/bin/env python3
"""Focused deterministic unit tests for lean tool-guard.py v4.0."""
import os
import sys

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def run_tests(evaluate_hook) -> int:
    # 1. Plaintext secret blocked
    r = evaluate_hook({
        "toolCall": {
            "name": "write_file",
            "args": {"Path": "/var/www/app.ts", "Content": "const tok = 'ghp_" + "A" * 36 + "';"}
        }
    })
    assert r.get("decision") == "deny" and "Secret Guard" in r.get("reason", ""), r

    # 2. Upstream tenant/secret isolation + external skill shield
    r = evaluate_hook({
        "toolCall": {"name": "write_file", "args": {"Path": "/var/www/zerops-astrobranding/prod.env", "Content": "FOO=1"}}
    })
    assert r.get("decision") == "deny" and "Upstream Multi-Tenant" in r.get("reason", ""), r

    r = evaluate_hook({
        "toolCall": {"name": "write_file", "args": {"Path": "/var/www/zerops-astro-skills/brainstorming/SKILL.md", "Content": "x"}}
    })
    assert r.get("decision") == "deny" and "Upstream Shield" in r.get("reason", ""), r

    # 3. Handover immunity
    r = evaluate_hook({
        "toolCall": {"name": "write_file", "args": {"Path": "/var/www/artifacts/handoff/test_handoff.md", "Content": "overwrite"}}
    })
    assert r.get("decision") == "deny" and "Handover Immunity" in r.get("reason", ""), r

    # 4. In-memory syntax pre-flight (.py & .json)
    r_py = evaluate_hook({
        "toolCall": {"name": "write_file", "args": {"Path": "/tmp/bad.py", "Content": "def broken(:\n  pass"}}
    })
    assert r_py.get("decision") == "deny" and "Python SyntaxError" in r_py.get("reason", ""), r_py

    r_json = evaluate_hook({
        "toolCall": {"name": "write_file", "args": {"Path": "/tmp/bad.json", "Content": "{bad json"}}
    })
    assert r_json.get("decision") == "deny" and "JSON SyntaxError" in r_json.get("reason", ""), r_json

    # 5. Single-node ZCP scale guard
    r = evaluate_hook({
        "toolCall": {
            "name": "call_mcp_tool",
            "args": {"ServerName": "zerops", "ToolName": "zerops_scale", "Arguments": {"serviceHostname": "zcp", "maxContainers": 2}}
        }
    })
    assert r.get("decision") == "deny" and "Single-Node" in r.get("reason", ""), r

    # 6. Process kill guard protects current/ancestor PID
    r = evaluate_hook({
        "toolCall": {"name": "run_command", "args": {"CommandLine": f"kill -9 {os.getpid()}"}}
    })
    assert r.get("decision") == "deny" and "Kill Guard" in r.get("reason", ""), r

    # 7. Catastrophic rm & sweeping artifacts rm
    r_rm = evaluate_hook({
        "toolCall": {"name": "run_command", "args": {"CommandLine": "rm -rf /var/www"}}
    })
    assert r_rm.get("decision") == "force_ask", r_rm

    r_sw = evaluate_hook({
        "toolCall": {"name": "run_command", "args": {"CommandLine": "rm -f /var/www/artifacts/*"}}
    })
    assert r_sw.get("decision") == "deny" and "Handover Immunity" in r_sw.get("reason", ""), r_sw

    # 8. Quoted commit message with rm -rf is NOT blocked (AST parser)
    r_git = evaluate_hook({
        "toolCall": {"name": "run_command", "args": {"CommandLine": 'git commit -m "docs: explain rm -rf /var/www guard"'}}
    })
    assert r_git.get("decision") == "allow", r_git

    # 9. Unpruned FUSE Drive find guard
    r_find = evaluate_hook({
        "toolCall": {"name": "run_command", "args": {"CommandLine": "find /var/www -name '*.md'"}}
    })
    assert r_find.get("decision") == "deny" and "FUSE Drive Guard" in r_find.get("reason", ""), r_find

    r_find_ok = evaluate_hook({
        "toolCall": {"name": "run_command", "args": {"CommandLine": "find /var/www -path /var/www/baiosfera -prune -o -name '*.md'"}}
    })
    assert r_find_ok.get("decision") == "allow", r_find_ok

    # 10. LLM batch pilot guard
    r_batch = evaluate_hook({
        "toolCall": {"name": "run_command", "args": {"CommandLine": "python3 /tmp/compile_playbooks.py"}}
    })
    assert r_batch.get("decision") == "deny" and "Pilot Guard" in r_batch.get("reason", ""), r_batch
    r_batch_ok = evaluate_hook({
        "toolCall": {"name": "run_command", "args": {"CommandLine": "python3 /tmp/compile_playbooks.py --pilot --limit 5"}}
    })
    assert r_batch_ok.get("decision") == "allow", r_batch_ok

    # 11. PostToolUse triggers engram sync ONLY on engram write tools
    r_eng = evaluate_hook({
        "is_post_tool": True,
        "test_inspect_engram_sync": True,
        "toolCall": {"name": "call_mcp_tool", "args": {"ServerName": "engram", "ToolName": "mem_save"}}
    })
    assert r_eng.get("engramSyncTriggered") is True, r_eng

    r_eng_read = evaluate_hook({
        "is_post_tool": True,
        "test_inspect_engram_sync": True,
        "toolCall": {"name": "call_mcp_tool", "args": {"ServerName": "engram", "ToolName": "mem_search"}}
    })
    assert r_eng_read.get("engramSyncTriggered") is False, r_eng_read

    # 12. Legacy bureaucracy removed: dead-function deletion allowed, zero Linear-First blocks, zero injectSteps
    r_del = evaluate_hook({
        "toolCall": {"name": "write_file", "args": {"Path": "/var/www/zerops-astrobranding/scripts/hooks/tool-guard.py", "Content": "def main():\n    return 0\n"}}
    })
    assert r_del.get("decision") == "allow", r_del

    r_lin = evaluate_hook({
        "toolCall": {"name": "call_mcp_tool", "args": {"ServerName": "zerops", "ToolName": "zerops_workflow", "Arguments": {"action": "start", "workflow": "bootstrap"}}}
    })
    assert r_lin.get("decision") == "allow", r_lin

    r_pi = evaluate_hook({"invocationNum": 0, "initialNumSteps": 0, "lastUserInput": "investiga estado del arte sota"})
    assert r_pi == {} and "injectSteps" not in r_pi, r_pi

    print("✅ All 12 lean tool-guard v4.0 unit test groups PASSED (exit 0).")
    return 0


if __name__ == "__main__":
    import tool_guard
    sys.exit(run_tests(tool_guard.evaluate_hook))
