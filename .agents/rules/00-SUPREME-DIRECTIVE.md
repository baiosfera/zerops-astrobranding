---
name: "00-supreme-directive"
description: "Core operational invariants for agy 1.5.16 on Zerops ZCP."
trigger: always_on
metadata:
  author: "Baiosfera"
  version: "10.1"
---
# SUPREME DIRECTIVE (v10.1)

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

## 5. Playbook Distillation, Editorial Craft & Semantic Anchoring
- **Playbook & Oráculo Distillation**: Distill every raw user brief through domain Playbooks (`00..19`) and Oráculo (`Casa 7 Descendente`, `Casa 8`, `Casa 11`, `Venus` when active) into a single sharp archetype before drafting public copy.
- **Socratic Editorial Challenge**: Challenge ambiguous briefs with Playbook evidence up front, keeping commercial offers (`commercial_offer`) distinct from internal operating protocols (`operating_protocol`).
- **Semantic Anchoring (`PB00`)**: Introduce the recognizable human discipline or category before naming any proprietary brand term, and verify public copy with `anti-slop-linter` (mechanical invariants) plus Blind Critic review.

## 6. Vibecoding Visual-World & Craft Gate (`PB19`)
- Commit an original visual world per brand (`PRODUCT.md` -> `impeccable concept-seed` -> `DESIGN.md`) without cloning external reference URLs or arbitrary `0px`/template defaults; enforce `Hero Punch Budget` (`6–14`-word H1, `<= 26`-word subtitle, above-the-fold proof), physically bundled `@fontsource-variable/*` fonts (`0` overused/phantom faces), lazy 60fps GSAP/Lenis motion, and physical verification via `impeccable detect` + desktop/mobile browser captures.
