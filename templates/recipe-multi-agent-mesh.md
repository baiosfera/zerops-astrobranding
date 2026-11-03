# Multi-Agent Mesh Recipe & Platform REST APIs Manual (v3.0 SOTA CoHaLo)

Sovereign Multi-Agent Architecture for Zerops Astrobranding: Tri-Pillar Topology (`hermes` + `paperclip` + `crewai`/`pydanticai`), Zero-Leak Bifrost/FreeLLMAPI Inference Tandem ($0 Default), Indestructible PostgreSQL 18 + LocalStorage SSoT Persistence, Dynamic Gateway v1 SSE Streaming, and Autonomous 24/7 Execution without ZCP.

---

## 1. Tri-Pillar Sovereign Topology

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

## 3. Paperclip HTTP Gateway v1 Protocol

Hermes implements the official Paperclip HTTP agent specification in `apps/hermes/main.py` using `ThreadingHTTPServer` to avoid thread blocking:

### A. Run Dispatch
```http
POST /v1/runs
Content-Type: application/json

{
  "task": "Generar auditoria SEO de la tienda online",
  "tier": "free",
  "budget_limit_cents": 50
}
```
*Response: `202 Accepted`*
```json
{
  "run_id": "run_1730598000_a1b2",
  "status": "queued",
  "stream_url": "/v1/runs/run_1730598000_a1b2/events"
}
```

### B. SSE Real-Time Event Stream
```http
GET /v1/runs/:run_id/events
Accept: text/event-stream
```
Streams standard Server-Sent Events (`text/event-stream`):
- `run.started`: Run initialized with task brief.
- `tool.call`: Tool name and invocation arguments.
- `tool.result`: Tool execution output.
- `token.delta`: Streaming text tokens for live Paperclip UI rendering.
- `run.completed`: Final result and token usage:
  ```json
  {
    "type": "run.completed",
    "result": "Auditoría completada exitosamente.",
    "usage": {
      "prompt_tokens": 1250,
      "completion_tokens": 420,
      "total_tokens": 1670,
      "cost_cents": 0
    }
  }
  ```

---

## 4. Universal CoHaLo Dynamic Skill Harness (141 Skills)

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

## 5. Operational Diagnostics

```bash
# Check Bifrost AI Gateway health and version
bifrost-cli status --base-url http://bifrost:8080

# List virtual keys and spend policies
bifrost-cli keys list --base-url http://bifrost:8080

# Check Hermes Gateway health
curl -s http://hermes:8000/health

# Check Paperclip deployment env variables
ssh paperclip "paperclipai env"
```

---

## 6. 24/7 Autonomous Execution Without ZCP

All services (`hermes`, `paperclip`, `crewai`, `bifrost`, `freellmapi`, `webprod`, `evolution`, `database`, `valkey`, `nats`, `localstorage`) run in independent Incus LXC containers.
The control plane container (`zcp`) can be stopped (`zcli service stop zcp`) without affecting live Telegram operations, Paperclip governance, or scheduled autonomous swarms.
