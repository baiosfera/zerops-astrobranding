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
| - Universal CoHaLo Dynamic Skill Harness (141 skills) | | - Zero ObjectStorage Overhead           |
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
        HERMES_MODEL_NAME: "hermes-3-llama-3.1-8b"
        BIFROST_VIRTUAL_KEY: "vk-hermes-agent"
        NATS_URL: ${nats_connectionString}
      start: python3 apps/hermes/main.py

  # Paperclip AI Platform (Node.js 26)
  - setup: paperclip
    build:
      base: ubuntu/nodejs@26
      prepareCommands:
        - npm install -g paperclipai
      deployFiles:
        - apps/agentdev
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
        - sudo mkdir -p /mnt/localstorage/paperclip/storage /mnt/localstorage/paperclip/secrets && sudo chown -R zerops:zerops /mnt/localstorage/paperclip
      envVariables:
        PORT: "3100"
        HOST: "0.0.0.0"
        NODE_ENV: "production"
        DATABASE_URL: ${database_connectionString}
        PAPERCLIP_HOME: "/mnt/localstorage/paperclip"
        PAPERCLIP_STORAGE_PROVIDER: "local_disk"
        PAPERCLIP_STORAGE_LOCAL_DIR: "/mnt/localstorage/paperclip/storage"
        PAPERCLIP_SECRETS_MASTER_KEY_FILE: "/mnt/localstorage/paperclip/secrets/master.key"
      start: node apps/agentdev/src/server.mjs
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

### When to Use PydanticAI vs CrewAI
- **PydanticAI (`apps/hermes/tools.py` -> `extract_structured_data`)**:
  - Memory: <35 MB RAM.
  - Latency: <100ms.
  - Purpose: Schema extraction, classification, parameter extraction, and deterministic validation before mutations.
- **CrewAI (`apps/hermes/agent.py` -> `run_crew_ai`)**:
  - Memory: ~120-200 MB RAM per active squad.
  - Latency: 5s - 60s multi-agent deliberation.
  - Purpose: Creative research, SEO audits, complex decision trees, and multi-step autonomous workflows.

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

# Check Paperclip database and env
ssh paperclip "paperclipai env"
```

---

## 8. 24/7 Autonomous Execution Without ZCP

All services (`hermes`, `paperclip`, `crewai`, `bifrost`, `freellmapi`, `webprod`, `evolution`, `database`, `valkey`, `nats`, `localstorage`) run in independent Incus LXC containers.
The control plane container (`zcp`) can be stopped (`zcli service stop zcp`) without affecting live Telegram operations, Paperclip governance, or scheduled autonomous swarms.
