---
name: "00-supreme-directive"
description: "Trigger: always_on, supreme, 00-supreme, cohalo, invariants, anti-amn, engram. Unified supervisor for agy on zcp."
trigger: always_on
metadata:
  author: "Baiosfera"
  version: "9.0"
---
# SUPREME DIRECTIVE: SOTA GROUNDING & UNIFIED WORKFLOW (v9.0)

Core architectural supervisor for Antigravity CLI (`agy`) on `zcp`. Encyclopedia: [`supreme_directive_encyclopedia.md`](file:///var/www/.agents/references/supreme_directive_encyclopedia.md).

## Execution State Machine (Unified F0–F5 + Bounded Delegation)

Tasks acotadas y reversibles se ejecutan directo inline (leer, editar, probar). Solo iniciativas multi-servicio o $\ge 3$ pasos activan el ciclo completo (sin archivos `odd/tasks/*.md` paralelos):

| Fase | Nombre | Propósito | Sensor / Evidencia |
|---|---|---|---|
| **F0** | **Epistemic Inflow** | Investigar fuentes primarias con subagentes `research` (MCP: Context7/Exa/Brave/Tavily/Firecrawl) y esperar reportes antes de concluir. | Reportes reales + URLs. |
| **F1** | **Clarification Gate** | Resolver dudas críticas con 1 pregunta concreta en chat o `draft_*.md`. Sin ticketaje Linear todavía. | Respuesta explícita. |
| **F2–F3** | **Alignment & Feedforward** | Alinear Dual-RAG (`references/`) y validar sintaxis/tipos en frío. | Linters / AST (exit 0). |
| **F4** | **Plan & Approval Gate** | Plan condensado en `/var/www/artifacts/plans/`, alta de `BAI-*` en Linear solo para épicas multi-servicio/multi-sesión y solicitud de `Go`. | Plan con criterios + `Go`. |
| **F5** | **Execution & Parity** | Pruebas reales (`bun test`/`pytest`/CLI smoke), archivar plan cerrado en `archive/`, `ssot-parity-check`, `git push` y `mem_save`. | Exit code 0 + SSoT limpio. |

## 7 Sovereign Invariants (Positive Guidance)

| Invariante Soberano | Contrato Afirmativo de Ejecución | Sensor / Validación |
|---|---|---|
| **1. Real Behavior Tests & Sensor-First** | Validar comportamiento real (no teatro de regex). Los bloqueos duros residen en `tool-guard.py` (`decision: "deny"`) con tests deterministas (`--test` exit 0). | `skills-suite-validate` · `ssot-parity-check` · `tool-guard.py --test` |
| **2. Proportional Tracking & Engram** | Linear exclusivamente para épicas multi-servicio tras `Go`. Auto-archivar planes cerrados en `artifacts/plans/archive/`. Persistir decisiones en `mem_save`. | Linear `BAI-*` · `mem_save` |
| **3. ZCP-First, Single-Node & SHARED** | `zcp` siempre a 1 contenedor (`minContainers: 1, maxContainers: 1`, `cpuMode: SHARED`). Builds y tests de apps por SSH en su contenedor dedicado. | `zerops_discover` · SSHFS `/var/www/` |
| **4. Hilo Delgado & Delegación Acotada** | Delegar exploraciones largas o unidades paralelas independientes a subagentes `agy` (`flash`); verificador independiente solo en cambios de alto riesgo. | Subagentes acotados · `git status` |
| **5. Anti-AMN & Arranque con Engram** | Verificar fecha presente (`date -u`), estado físico real e investigación externa vía `research`. Iniciar sesión con `mem_current_project` y `mem_context`. | `mem_context` inicial · Evidencia viva |
| **6. Claridad Sin Complacencia** | Reportar únicamente rutas, símbolos y salidas observadas tras la última edición. En F4 pedir `Go`; en F5 informar qué quedó verificado y próximo paso. | Salidas exit 0 observadas |
| **7. Doble Dominio (Software vs Prompts)** | **Código**: AST preservado, sintaxis válida (`py_compile`/`bash -n`), tests exit 0, sin límite de tokens.<br>**Skills/Reglas**: Positive Guidance, `SKILL.md` $\le 480$ palabras + `references/`. | `py_compile` / `bash -n` · `<= 480` palabras |
