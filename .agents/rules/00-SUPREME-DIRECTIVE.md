---
name: "00-supreme-directive"
description: "Trigger: always_on, supreme, 00-supreme, cohalo, invariants, anti-amn, engram. Unified supervisor for agy on zcp."
trigger: always_on
metadata:
  author: "Baiosfera"
  version: "9.1"
---
# SUPREME DIRECTIVE: SOTA GROUNDING & UNIFIED WORKFLOW (v9.1)

Core architectural supervisor for Antigravity CLI (`agy`) on `zcp`. Encyclopedia: [`supreme_directive_encyclopedia.md`](file:///var/www/.agents/references/supreme_directive_encyclopedia.md).

## Execution State Machine (Unified F0–F5 + Bounded Delegation)

Tasks acotadas y reversibles se ejecutan directo inline (leer, editar, probar). Iniciativas multi-servicio o $\ge 3$ pasos activan el ciclo F0–F5 usando `/var/www/artifacts/plans/` y Engram (sin archivos `odd/tasks/*.md` paralelos):

| Fase | Nombre | Propósito | Sensor / Evidencia |
|---|---|---|---|
| **F0** | **Epistemic Inflow** | Investigar fuentes primarias con subagentes `research` (MCP: Context7/Exa/Tavily/Jina/Firecrawl; fallbacks Brave/DuckDuckGo) y esperar reportes completos antes de concluir. | Reportes reales + URLs. |
| **F1** | **Clarification Gate** | Resolver dudas críticas con 1 pregunta concreta en chat o `draft_*.md`. Reservar mutaciones de código y creación de épicas Linear hasta F4 `Go`. | Respuesta explícita. |
| **F2–F3** | **Alignment & Feedforward** | Alinear Dual-RAG (`references/`) y validar sintaxis/tipos en frío sin silenciar errores. | Linters / AST (exit 0). |
| **F4** | **Plan & Approval Gate** | Presentar plan condensado (`draft_*.md` $\to$ plan aprobado), criterios ejecutables de cierre y esperar `Go` explícito antes de ejecutar o crear/cerrar épicas Linear. | Plan aprobado + `Go`. |
| **F5** | **Execution & Reality Proof** | Pruebas reales ejecutables (`bun test`/`pytest`/build/smoke), distinguir `BEHAVIORALLY_VERIFIED` de `SYNTAX_ONLY`/`UNVERIFIED`, archivar plan en `archive/`, `ssot-parity-check`, `git push` y `mem_save`. | Exit code 0 real + SSoT limpio. |

## 7 Sovereign Invariants (Positive Guidance)

| Invariante Soberano | Contrato Afirmativo de Ejecución | Sensor / Validación |
|---|---|---|
| **1. Zero Checklist-Theater & Real Proof** | Reportar solo lo ejecutado y observado tras el último cambio. Separar `BEHAVIORALLY_VERIFIED` (tests/builds/sondas reales) de `SYNTAX_ONLY` o `UNVERIFIED`. Marcar Linear `Done` exige evidencia real del alcance exacto. | `skills-suite-validate` · `ssot-parity-check` · `tool-guard.py --test` |
| **2. Proportional Tracking & Engram** | Linear únicamente tras `Go` en F4 para épicas multi-servicio. Archivar planes cerrados en `artifacts/plans/archive/`. Persistir decisiones y causas raíz en `mem_save`. | Linear `BAI-*` · `mem_save` |
| **3. ZCP-First, Single-Node & SHARED** | `zcp` opera siempre a 1 contenedor (`minContainers: 1, maxContainers: 1`, `cpuMode: SHARED`). Builds y tests de runtimes corren por SSH en su contenedor dedicado o plantilla Git. | `zerops_discover` · SSHFS `/var/www/` |
| **4. Hilo Delgado & Delegación Acotada** | Delegar exploraciones largas o unidades paralelas independientes a subagentes `agy`; verificador read-only separado en cambios de alto riesgo. | Subagentes acotados · `git status` |
| **5. Anti-AMN & Arranque Soberano** | Verificar fecha presente (`date -u`), estado físico vivo e investigación externa vía `research`. Iniciar sesión con `mem_current_project` y `mem_context`. | `mem_context` inicial · Evidencia viva |
| **6. Claridad Sin Complacencia** | En F4 detenerse y pedir `Go` antes de ejecutar o cerrar hitos. En F5 informar rutas/comandos/salidas observadas, ítems `UNVERIFIED` y próximo paso real. | Salidas exit 0 observadas |
| **7. Doble Dominio & Soberanía GitOps** | **Código**: AST preservado, sintaxis válida, tests reales exit 0, sin secretos en texto plano.<br>**Skills/Catálogo**: Positive Guidance, `SKILL.md` $\le 480$ palabras + `references/`, upstream (`baiosfera/*`) 100% libre de marcas o tokens de clientes. | `py_compile` / `bash -n` · `<= 480` palabras |
