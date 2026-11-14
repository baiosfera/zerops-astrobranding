# Template: Tri-Pillar Multi-Agent Autonomous Mesh (v3.0 SOTA CoHaLo)

Canonical architecture blueprint for bootstrapping an autonomous, self-healing, multi-agent organization on Zerops Astrobranding: Tri-Pillar Topology (`hermes` + `paperclip` + `crewai`/`pydanticai`), Zero-Leak Bifrost/FreeLLMAPI Inference Tandem ($0 Default), Indestructible PostgreSQL 18 + LocalStorage SSoT Persistence, Dynamic Gateway v1 SSE Streaming, and Autonomous 24/7 Execution without ZCP.

---

## 1. Architectural Blueprint & Mesh Invariants

```
+---------------------------------------------------------------------------------------------------+
| USER (Founder / Operator — Telegram 24/7 / Voice Notes / WhatsApp Bot / Paperclip UI)              |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                        +-------------------------+-------------------------+
                        |                                                   |
                        v                                                   v
+-------------------------------------------------------+ +-----------------------------------------+
| PILLAR 1: HERMES CHIEF OF STAFF (`hermes` :8000)      | | PILLAR 2: PAPERCLIP GOVERNANCE OS       |
| Runtime: ubuntu/python@3.12                           | | (`paperclip` / `agentdev` :3100)        |
| - Telegram Admin/Client Gateway (Watchdog auto-heal)  | | Base: ubuntu/nodejs@26                  |
| - Paperclip HTTP Gateway v1 (ThreadingHTTPServer)     | | - Org Chart, Budgets, Spend Caps        |
|   * POST /v1/runs -> 202 Accepted {run_id}            | | - Task queues & Issue assignment        |
|   * GET  /v1/runs/:id -> Status & Usage               | | - PostgreSQL 18 SSoT (Zero Embedded DB) |
|   * GET  /v1/runs/:id/events -> SSE streaming         | | - NVMe POSIX LocalStorage at            |
| - Ephemeral Worker Discovery (list_zerops_services)   | |   /mnt/localstorage/paperclip           |
| - Universal Primitives Engine (5 core primitives,     | | - Zero ObjectStorage Overhead           |
|   zero frankenstein tools; CLIs in /usr/local/bin)    | |                                         |
+---------------------------+---------------------------+ +--------------------+--------------------+
                            |                                                  |
                            | (HTTP Gateway v1 / NATS RPC)                     | (Run dispatch)
                            +-------------------------+------------------------+
                                                      |
                                                      v
                        +-------------------------------------------------------+
                        | PILLAR 3: DUAL-ENGINE SWARM MESH                      |
                        | Runtime: Python 3.12 / In-Process & Ephemeral Workers  |
                        | - PydanticAI Engine (<35MB RAM, <100ms):               |
                        |   Deterministic schema extraction & validation        |
                        | - CrewAI Engine (1.15.30+): Macro-swarms & squads     |
                        |   (seo_aeo_geo, general_research, OPB squads)         |
                        | - Ephemeral Video Worker (videoworker Recipe 08):     |
                        |   On-demand Chromium/FFmpeg video rendering           |
                        +---------------------------+---------------------------+
                                                    |
                                                    v
                        +-------------------------------------------------------+
                        | INFERENCE TANDEM (Zero-Leak $0 Default)               |
                        | [A] Bifrost AI Gateway (:8080 - Alpine Go 1.22)       |
                        |     - Virtual Keys & Adaptive CEL Priority Routing    |
                        |     - Semantic Cache (PostgreSQL 18 / Chromem)        |
                        |     - Priority 0: Explicit Pro Override (DeepSeek V3) |
                        |     - Priority 1: FreeLLMAPI ($0 Default)             |
                        | [B] FreeLLMAPI Pool (:3001 - Node.js 24)              |
                        |     - 34+ Free Inference Providers                    |
                        |     - Provisional Token Leases & Circuit Breaker      |
                        +-------------------------------------------------------+
```

### Invariants:
1. **SSoT Persistence**: Managed PostgreSQL 18 holds relational and execution state; persistent NVMe volume (`localstorage`) holds files and secrets. No reliance on volatile container rootfs or unbacked ObjectStorage.
2. **Zero-Leak Budgeting**: Default routing uses FreeLLMAPI ($0). Paperclip spend caps enforce hard stop conditions.
3. **Decoupled Runtimes**: Every service runs in dedicated Incus LXC containers with non-blocking threading.
4. **Ephemeral On-Demand Workers**: Compute-heavy workloads (video rendering, large-scale scrapers) use ephemeral containers spawned via recipe steps, executed, and deleted to maintain zero idle cost.
5. **Dynamic Domain Agnosticism & DB Introspection**: Hermes operates business-agnostically. It strictly forbids hardcoding catalogs, dummy stores, or static products (e.g. no hardcoded clothes, makeup, or services) and equally forbids rigid anti-commerce prohibitions. Instead, it introspects live PostgreSQL 18 tables (`information_schema.tables`, `mentorships`, `products`, `orders`, `bookings`) via `execute_query` to adapt dynamically to any business model (e-commerce, 1:1 mentorships, digital consulting).
6. **CrewAI 1.15.30+ Pydantic Output Bridge**: Dynamic swarms can enforce strict Pydantic schemas at runtime via `output_pydantic` on terminal tasks by supplying `output_schema` to `run_crew_ai`.
7. **Bifrost Governance SSoT Invariant**: When `config_store: postgres` is enabled, PostgreSQL table `governance_virtual_keys` is the exclusive source of truth for Virtual Keys (`vk-production-main`, `vk-hermes-agent`, `vk-crewai`, `vk-pidev`, `vk-pydanticai`). The local `config.json` is not dynamically watched or re-read by the runtime.
8. **Telegram Multi-Media Gateway**: Handles both photos and documents (`filters.Document.ALL`) persisted to `/mnt/localstorage/uploads/` with single-instance polling conflict protection.
9. **Paperclip <-> Hermes Bidirectional Telemetry Bridge**:
   - **Outbound (Paperclip ➔ Hermes)**: Paperclip dispatches heartbeat runs to `http://hermes:8000/v1/runs` and streams execution deltas via SSE (`/v1/runs/:id/events`).
   - **Inbound (Hermes ➔ Paperclip)**: Every conversational turn with the user in Telegram (or external channels) is automatically and asynchronously recorded into Paperclip via `paperclip_bridge.py`:
     * Completed execution recorded in `heartbeat_runs` (source `telegram`, canonical USD/cents keys `cost_usd`, `costUsd`, `cost_cents`, `totalTokens`, `duration_sec`).
     * Financial ledger entry inserted directly into `cost_events` with `biller: deepseek` or `freellmapi`, `billing_type: metered_api`, ensuring Paperclip's Costs Tab (`/costs`) renders the real model breakdown and spend.
     * Live audit event published to `activity_log` for immediate visibility in Paperclip Dashboard.
     * Agent heartbeat timestamp (`last_heartbeat_at`) and accumulated monthly spend (`spent_monthly_cents`) synchronized to the exact sum of `cost_events` ledger.
10. **Symmetric Native CLI Availability (`apotelos`)**: Both ZCP and Hermes runtime containers feature `/usr/local/bin/apotelos` natively installed and linked (`/var/www/scripts/apotelos`). Hermes invokes `apotelos` via `run_command` in its loop, ingesting `/mnt/localstorage/${PROJECT_NAME}/dev/verticals/` and compiling reverse-causality Blackboard manifests without external proxy dependencies.
     * **Bifrost ➔ Paperclip Auto-Reconciliation**: `reconcile_bifrost_to_paperclip()` periodically cross-references Bifrost request logs (`db.logs`) with Paperclip (`cost_events`) to eliminate any billing drift between the LLM gateway and Paperclip.
   - **Conversational Task Operations**: Hermes exposes `paperclip_list_tasks` and `paperclip_create_task` so users can inspect and manage Paperclip Kanban issues directly from Telegram chat without opening a browser.
10. **Vertical Workspaces & Bounded Contexts Invariant**:
    - The development workspace (`/mnt/localstorage/{project}/dev/`) is organized as a Vertical-First hierarchy:
      * `_shared/`: Global ecosystem topology (`ecosystem.json`) and core brandbook tokens.
      * `verticals/`: Declarative SSoT specifications (`<vertical-slug>.json`, e.g. `brand-core.json`, `service-a.json`).
      * `workspaces/{vertical_slug}/`: Bounded context per vertical with strictly isolated sub-layers: `brand/` (design tokens, theme.css), `strategy/` (dossier.md, seo.md, psychology), `copy/` (landings, offers, emails), and `web/` (page specs and component contracts for PiDev).
    - Prevents multi-brand token contamination and eliminates recursive directory scanning token waste across autonomous swarms.
11. **Headless CrewAI Non-Blocking Telemetry Invariant**:
    - In daemonized container environments (Hermes, ephemeral workers, CLI pipelines), the environment variables `CREWAI_TELEMETRY_OPT_OUT="true"`, `OTEL_SDK_DISABLED="true"`, and `CREWAI_DISABLE_TELEMETRY="true"` are strictly enforced.
    - Eliminates the 20-second interactive terminal prompt (`Share this execution trace? [y/N]`), reducing swarm dispatch latency by over 50% and ensuring zero hangs in unattended execution.
12. **Cognitive Swarm vs. Sovereign Builder Boundary (CrewAI vs. PiDev)**:
    - **CrewAI Boundary (Cognitive Strategy & Content Assemblers)**: Dynamic swarms strictly assemble research dossiers, neurocopywriting, SEO/AEO strategies, and component contracts into structured Markdown/JSON (`workspaces/{vertical_slug}/`). They NEVER modify, compile, or generate frontend source code (`.astro`, `.ts`, `.css` in `webdev`).
    - **PiDev Sovereign Code Authority (Execution & Scaffolding)**: `pidev` (`pi.dev` / Gentle-Pi) is the exclusive sovereign builder for Astro 5 SSR code. It does not perform market strategy or creative design from scratch; it ingests `copy/landing.md` and `web/page-spec.md` produced by CrewAI and compiles them into production Astro 5 SSR components with Tailwind 4 and TypeScript.
13. **Hermes Native ZCP MCP Bridge Invariant (Zero Frankenstein Tools)**:
    - Hermes controls the Zerops infrastructure directly via an async stdio JSON-RPC client (`apps/hermes/mcp_bridge.py`) connecting to `/mnt/localstorage/bin/zcp serve`.
    - Eliminates bespoke Python wrappers and fragile CLI parsing: exposes all 24 native Zerops MCP tools (`zerops_discover`, `zerops_deploy`, `zerops_logs`, `zerops_scale`, `zerops_env`, `zerops_verify`, etc.) with strict typing and 10MB streaming buffers.
    - Preserves `SOUL.md` minimal ($\le 4\text{ KB}$): tool schemas are dynamically registered in the inference API `tools` array, never duplicated as plaintext markdown.
14. **PiDev Codecraft Doctrine & Bifrost Headless Bridge Invariant**:
    - `pidev` runs under sovereign `AGENTS.md` bound to the 5-skill core: `codecraft` (TDD, Karpathy guidelines, deep modules, verification before completion), `impeccable`, `design-taste-frontend` (`taste-skill`), `astro-web`, and `ghcicd`.
    - Headless agentic execution is routed to Bifrost (`http://bifrost:8080/v1`) using Virtual Key `vk-pidev` via `/mnt/localstorage/pidev/pi/models.json` and `auth.json` (`type: "api_key"`).
    - Unattended execution uses `pi --approve --provider bifrost --model bifrost/deepseek-chat -p '<prompt>' < /dev/null`, ensuring automatic project trust, zero stdin blocking, and sub-2s execution latency.

---

## 2. Indestructible SSoT Persistence Contract

Paperclip AI and Hermes run with zero data loss across container restarts, stop/start cycles, and full Zerops redeployments (`zerops_deploy`):

1. **PostgreSQL 18 Managed Lakehouse**:
   - `DATABASE_URL: ${database_connectionString}` is supplied to Paperclip.
   - Automatically disables `@embedded-postgres`, saving **~400 MB RAM** per instance and keeping swap completely clear.
   - Managed DB cluster handles migrations, relations, and ACID transaction guarantees.

2. **POSIX LocalStorage NVMe Volume**:
   - Volume `localstorage` is mounted at `/mnt/localstorage` with single-kernel POSIX semantics.
   - Paperclip storage is strictly isolated to `/mnt/localstorage/paperclip`:
     * `PAPERCLIP_HOME: "/mnt/localstorage/paperclip"`
     * `PAPERCLIP_STORAGE_PROVIDER: "local_disk"`
     * `PAPERCLIP_STORAGE_LOCAL_DIR: "/mnt/localstorage/paperclip/storage"`
     * `PAPERCLIP_SECRETS_MASTER_KEY_FILE: "/mnt/localstorage/paperclip/secrets/master.key"`
   - Daily automated `.tar.gz` snapshots provided natively by Zerops platform.
   - **Zero ObjectStorage Overhead**: S3 is not needed for Paperclip governance, eliminating bucket sprawl and redundant billing.

3. **Hermes Affirmative System Prompt Invariant (Anti-Pink Elephant)**:
   - System prompt in `apps/hermes/prompts.py` follows Nous Research SOTA (arXiv:2408.11857 / arXiv:2402.07896):
     * **Lean Affirmative Guidance**: Explicitly defines role, identity, and affirmative operating principles.
     * **Decoupled API Tool Schemas**: Tools are passed strictly in the API `tools` array. Never duplicate tool definitions in plaintext markdown inside the system prompt.
     * **Zero Pink Elephants**: Zero negative prohibitions ("never do X", "do not output Y") that prime autoregressive attention on forbidden tokens.
     * **Proportional Intent Handling**: Conceptual and hypothetical questions receive architectural explanations in 1-3 concise paragraphs without tool calls; operational requests trigger tools to collect physical proof.
     * **Executive Brevity & Code Policy**: Conversational responses remain brief and natural. Scripts, playbooks, and code files are authored to workspace/git via tools (`write_file`, `pidev_dispatch_task`), reserving raw code blocks in chat strictly for explicit user requests.
     * **Dynamic Self-Discovery**: Inspect live services (`list_zerops_services`) and database tables (`execute_query`) dynamically rather than hardcoding pre-existing catalogs or service stacks.


---

## 3. Infrastructure Configuration Blueprint (`zerops.yaml` snippet)

```yaml
  # Hermes Agent (Python 3.12)
  - setup: hermes
    build:
      base: ubuntu/python@3.12
      buildCommands:
        - cd apps/hermes && pip install --upgrade pip setuptools wheel && pip install --target=./vendor -r requirements.txt
      deployFiles:
        - apps/hermes
      cacheFiles:
        - /root/.cache/pip
    run:
      base: ubuntu/python@3.12
      volume:
        hostname: localstorage
        mountPath: /mnt/localstorage
        readOnly: false
      ports:
        - port: 8000
          httpSupport: true
      initCommands:
        - sudo mkdir -p /mnt/localstorage/hermes && sudo chown -R zerops:zerops /mnt/localstorage/hermes
      envVariables:
        PORT: "8000"
        PYTHONPATH: "./apps/hermes/vendor:./apps/hermes"
        DATABASE_URL: ${database_connectionString}
        HERMES_MODEL_ENDPOINT: "http://bifrost:8080/v1"
        HERMES_MODEL_NAME: "auto"
        BIFROST_VIRTUAL_KEY: "vk-hermes-agent"
        NATS_URL: ${nats_connectionString}
      start: python3 apps/hermes/main.py

  # Paperclip AI Platform (Ubuntu 26 / Node.js 26 pnpm monorepo)
  - setup: paperclip
    build:
      base: ubuntu/nodejs@26
      prepareCommands:
        - sudo apt-get update && sudo apt-get install -y --no-install-recommends ca-certificates curl git build-essential python3
        - sudo corepack enable || sudo npm install -g pnpm@latest
      buildCommands:
        - pnpm install --no-frozen-lockfile
        - pnpm --filter @paperclipai/ui build
        - pnpm --filter @paperclipai/plugin-sdk build
        - PAPERCLIP_TSC_EMIT_ONLY=1 pnpm --filter @paperclipai/server build
        - pnpm --filter @paperclipai/server build:runtime
        - sed -i 's|/build/source|/var/www|g' server/dist-runtime/*.mjs
      deployFiles:
        - .
      cache:
        - node_modules
        - .pnpm-store
    run:
      base: ubuntu/nodejs@26
      volume:
        hostname: localstorage
        mountPath: /mnt/localstorage
        readOnly: false
      ports:
        - port: 3100
          httpSupport: true
      initCommands:
        - sudo mkdir -p /mnt/localstorage/paperclip/storage /mnt/localstorage/paperclip/instances/default && sudo chown -R zerops:zerops /mnt/localstorage/paperclip && sudo chmod -R 777 /mnt/localstorage/paperclip
        - pnpm --filter @paperclipai/db migrate || true
      envVariables:
        PORT: "3100"
        HOST: "0.0.0.0"
        NODE_ENV: "production"
        SERVE_UI: "true"
        DATABASE_URL: "postgresql://${database_user}:${database_password}@${database_hostname}:${database_port}/paperclip"
        BETTER_AUTH_SECRET: ${PAPERCLIP_BETTER_AUTH_SECRET}
        PAPERCLIP_TOOL_ACTION_SIGNING_SECRET: ${PAPERCLIP_SIGNING_SECRET}
        PAPERCLIP_STORAGE_PROVIDER: "local_disk"
        PAPERCLIP_STORAGE_LOCAL_DIR: "/mnt/localstorage/paperclip/storage"
        PAPERCLIP_HOME: "/mnt/localstorage/paperclip"
        PAPERCLIP_DEPLOYMENT_MODE: "authenticated"
        PAPERCLIP_DEPLOYMENT_EXPOSURE: "public"
        PAPERCLIP_BIND: "lan"
        PAPERCLIP_AUTH_BASE_URL_MODE: "explicit"
        PAPERCLIP_AUTH_PUBLIC_BASE_URL: "https://${zerops_subdomain}"
        BETTER_AUTH_URL: "https://${zerops_subdomain}"
        BETTER_AUTH_TRUSTED_ORIGINS: "https://${zerops_subdomain}"
        PAPERCLIP_ADMIN_EMAIL: ${PAPERCLIP_ADMIN_EMAIL}
        PAPERCLIP_ADMIN_PASSWORD: ${PAPERCLIP_ADMIN_PASSWORD}
        HERMES_GATEWAY_URL: "http://hermes:8000"
      start: bash start.sh
      healthCheck:
        httpGet:
          port: 3100
          path: /api/health
```

---

## 4. Paperclip HTTP Gateway v1 Protocol Specification

Hermes exposes an HTTP Gateway v1 server compatible with Paperclip agent orchestration using `ThreadingHTTPServer`:

### Endpoints
- `POST /v1/runs`: Submits an execution brief.
  - Body: `{"task": string, "tier": "free"|"pro", "budget_limit_cents": number}`
  - Returns: `202 Accepted` with `run_id` and `stream_url`.
- `GET /v1/runs/:id`: Fetches current run status, result, and token consumption.
- `GET /v1/runs/:id/events`: Subscribes to real-time Server-Sent Events (SSE).

### SSE Event Stream Protocol
| Event Type | Payload Fields | Description |
|---|---|---|
| `run.started` | `task_id`, `brief` | Dispatched when execution begins |
| `tool.call` | `name`, `arguments` | Dispatched prior to tool execution |
| `tool.result` | `name`, `status`, `output` | Dispatched after tool completion |
| `token.delta` | `content` | Live streaming text output |
| `run.completed` | `result`, `usage` (`cost_cents`) | Terminal event reporting results and usage |

---

## 5. Dual-Engine Swarm Execution

### When to Use PydanticAI vs CrewAI (Invariante: CrewAI es Obligatorio)
> **Invariante Arquitectónico:** **CrewAI (`1.15.30+`) es un pilar primario NO OPCIONAL** de la malla Tri-Pillar y del pipeline Apotelos (`crewai_engine/`). `PydanticAI` lo complementa para extracciones rápidas, nunca lo reemplaza ni se desinstala `crewai`.

- **PydanticAI (`apps/hermes/tools.py` -> `extract_structured_data`)**:
  - Memory: <35 MB RAM.
  - Latency: <100ms.
  - Purpose: Schema extraction, classification, parameter extraction, and deterministic validation before mutations.
- **CrewAI (`apps/hermes/agent.py` -> `run_crew_ai`)**:
  - Memory: ~120-200 MB RAM per active squad.
  - Latency: 5s - 60s multi-agent deliberation.
  - Purpose: Creative research, SEO audits, complex decision trees, and multi-step autonomous workflows.

### 5.1 Coding Agent Benchmark: PiDev vs. Aider vs. Goose
- **Pi Coding Agent (`pi.dev` / Gentle-Pi) — Sovereign Web Builder**:
  * Runtime: Native `ubuntu/nodejs@26` (V8 / TypeScript isomorphic with Astro 5 & Tailwind 4).
  * Architecture: Minimal harness (<1k tokens system prompt), QuickJS WASI sandboxed AST pre-flight, and native HTTP (`server.mjs`:3000) + NATS RPC daemon (`rpc.coding.execute`).
  * Role: Exclusive builder for frontend Astro 5 SSR code in `/var/www/webdev`. Ingests structured specs from `workspaces/{slug}/` and compiles them without needing creative/business deliberation.
- **Aider (Paul Gauthier) — High-Risk Multi-File Refactorer (Optional Standalone)**:
  * Runtime: Dedicated Python 3.12 / uv with native Tree-sitter C extensions.
  * Architecture: SOTA in SWE-bench; Tree-sitter AST symbol graphs & PageRank repo-map (~1k tokens dense graph), automatic atomic git commits, and `--architect` mode.
  * Decision: Discarded as container daemon in `pidev` due to heavyweight dual-runtime penalty (+300MB RAM, C compilers in Node container). Kept as an optional ephemeral worker for massive multi-file refactoring touching >10 cross-module files.
- **Goose (Block / AAIF) — Desktop Generalist (Discarded for Code Container)**:
  * Runtime: Rust native binary (~40MB).
  * Architecture: Native MCP client and YAML recipe runner (`goose run --recipe`).
  * Decision: Lacks AST symbol indexing, code-aware diff matchers, and git-native commit hygiene. Discarded for containerized Astro 5 code generation due to high diff-hallucination risk in frontmatter and JSX fences.

---

## 6. Universal CoHaLo Dynamic Skill Harness (141 Skills)

Instead of hardcoded tools, the mesh leverages the CoHaLo contract (`.atl/skill-registry.md`):

1. **COntext (Dual-RAG Progressive Disclosure)**:
   - Dynamic domain loading from `/mnt/localstorage/skills/<skill>/SKILL.md`.
   - `Agent.backstory`: Hydrated with the skill's `## Hard Rules` (Positive Guidance).
   - `Task.description`: Hydrated with `## Activation Contract`.
   - `Task.expected_output`: Hydrated with `## Output Contract`.
   - JIT reference tools allow agents to inspect `references/usage.md` and `references/infra.md` without polluting context.

2. **HArness (Dynamic Execution & Ephemeral Workers)**:
   - Dynamic inspection of Zerops topology via `list_zerops_services()`.
   - Ephemeral workers (like `videoworker`) are spun up on-demand via Recipe 08, execute batch renders, and can be terminated for zero idle cost.
   - Deterministic JSON output parsing via PydanticAI `extract_structured_data`.

3. **LOop (Frugal $0 Execution & Circuit Breakers)**:
   - LLMs default to `tier="free"` routing via Bifrost -> FreeLLMAPI.
   - Spend caps in Paperclip automatically suspend runs if limits are exceeded.

---

## 7. Operational Diagnostics

```bash
# Check Bifrost AI Gateway health and version
bifrost-cli status --base-url http://bifrost:8080

# List virtual keys and spend policies
bifrost-cli keys list --base-url http://bifrost:8080

# Check Hermes Gateway health
curl -s http://hermes:8000/health

# Stream SSE Events (replace <run_id>)
curl -N http://hermes:8000/v1/runs/<run_id>/events

# Generate Paperclip First-Admin Bootstrap CEO Invite URL (from host terminal or ZCP)
paperclipai auth bootstrap-ceo
# Output: https://paperclip-<subdomain>.zerops.app/invite/pcp_bootstrap_<token>
```

---

## 8. 24/7 Autonomous Execution Without ZCP

All services (`hermes`, `paperclip`, `crewai`, `bifrost`, `freellmapi`, `webprod`, `evolution`, `database`, `valkey`, `nats`, `localstorage`) run in independent Incus LXC containers.
The control plane container (`zcp`) can be stopped (`zcli service stop zcp`) without affecting live Telegram operations, Paperclip governance, or scheduled autonomous swarms.

## 9. Frugalidad de Disco, RAM y `deployFiles` (Invariante Anti-Bloat)

* **`zcp` (`verticalAutoscaling`):** Configurar `minCpu: 1`, `minRam: 1`, `minFreeRamGB: 0.75` (`SHARED`) para evitar reservas de ~5.7 GB RAM innecesarias. Limpiar `~/.npm/_cacache`, `~/.npm/_npx` huérfanos (ej. `paperclipai`) y `~/.cache/uv` vía `iniciar.sh` / `zcp-update`.
* **`paperclip` (`deployFiles`):** Nunca desplegar `devDependencies`, `.git`, `tests`, `docs`, `ui/src`, `ui/storybook` ni `.map` al contenedor de `run`. Compilar `@paperclipai/db` (`node packages/db/dist/migrate.js`) y ejecutar `CI=true pnpm prune --prod` al final de `buildCommands`.
* **`hermes` (`vendor/` & CrewAI obligatorio):** **CrewAI (`1.15.30+`) es pilar primario NO OPCIONAL** de la arquitectura (nunca omitir `crewai`). Su huella en `vendor/` (`~460–500 MB` por `lancedb`/`pyarrow`/`onnxruntime`/`chromadb`) es el **baseline esperado de producción**. Optimizar instalando con `pip install --no-cache-dir` y purgando `__pycache__` en `./vendor`.
* **PostgreSQL (`database`):** El perfil `oltp-hobby` fija `minCpu: 1`. Los datos suelen ser <200 MB; vigilar retención de `db.public.logs` de Bifrost (~42 KB/fila).
