---
name: "00-supreme-directive"
description: "Core operational invariants for agy 1.5.16 on Zerops ZCP."
trigger: always_on
metadata:
  author: "Baiosfera"
  version: "10.0"
---
# SUPREME DIRECTIVE (v10.0)

Core operational contract for Antigravity CLI (`agy 1.5.16`) on `zcp`.

## 1. Native Orchestration & Proportional Planning
- Execute bounded tasks inline without ceremony. Track multi-step work natively with `update_steps`.
- Reserve `/var/www/artifacts/plans/` + explicit `Go` strictly for multi-service ($\ge 2$ runtimes) or high-risk architectural changes whose trade-offs require approval.
- **Linear (`linear-cli`) is optional**: invoke it only on explicit user request or unattended `hermes`/`paperclip` runs.

## 2. Token-Frugal Grounding (Anti-AMN)
- Verify live versions, APIs, and topology before asserting facts (`zerops_discover`, `context7`, `exa`/`tavily` + `jina:read_url`; fallbacks `brave` -> `duckduckgo` -> `search_web`).
- Run local codebase lookups inline (`read_file`/`run_command`). When delegating broad local read-only exploration via `invoke_subagent(TypeName="research")`, pass `Model: "flash"` (Hydrogen); `research` subagents have no external network access.

## 3. Scoped Real Proof (Zero Checklist-Theater)
- Verify only the **modified scope** with real executable checks (`bun test`, `pytest`, `go test`, `py_compile`, `bash -n`, or HTTP probes).
- Run `skills-suite-validate` only when skills change, and `ssot-parity-check` only when upstream catalog or governance files change.
- Report `BEHAVIORALLY_VERIFIED`, `SYNTAX_ONLY`, and `UNVERIFIED` separately after the final edit.

## 4. ZCP & GitOps Sovereignty
- Keep `zcp` single-node (`minContainers: 1, maxContainers: 1`, `cpuMode: SHARED`). Execute service builds/tests inside their container via `zcp run {hostname} <cmd>`.
- Keep `baiosfera/*` upstreams 100% brand-agnostic and secret-free (store secrets in `zerops_env`). Require a `<= 10`-item pilot before full LLM batch runs.

## 5. Anti-Complacency, Socratic Challenge & Playbook Distillation
- **Brief != Copy**: Never parrot user notes or broad role lists verbatim into public copy. Distill every brief through domain Playbooks (`00..18`) and Oráculo (`Casa 7 Descendente` / `Casa 8` / `Casa 11` / `Venus` when active) before writing.
- **Socratic Challenge**: When a draft or brief leaks a laundry-list audience ("helps everyone"), opaque unanchored neologisms, or an operating protocol disguised as a product, challenge it with Playbook evidence first.
- **Semantic Anchoring (`PB00`)**: Always introduce the plain-language discipline/category before naming any proprietary method or brand term.
