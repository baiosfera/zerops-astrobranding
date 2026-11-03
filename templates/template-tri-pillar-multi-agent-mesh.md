# Template: Tri-Pillar Multi-Agent Autonomous Mesh (v1.0 SOTA CoHaLo)

Canonical architecture blueprint for bootstrapping an autonomous, self-healing, multi-agent organization on Zerops Astrobranding.

---

## 1. Architectural Blueprint & Mesh Invariants

The architecture establishes three specialized agentic pillars coordinated through standard protocols:

```
                                  ┌────────────────────────┐
                                  │   OPERATOR / FOUNDER   │
                                  │  (Telegram / Web UI)   │
                                  └───────────┬────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
     ┌─────────────────────────────────┐             ┌─────────────────────────────────┐
     │   PILLAR 1: HERMES COPILOT      │             │   PILLAR 2: PAPERCLIP OS        │
     │   (Chief of Staff & Gateway)    │◄───────────►│   (Governance & Budget Caps)    │
     │   - Telegram Bot with Watchdog  │ HTTP Gateway│   - Org Chart & Issue Assignment│
     │   - Paperclip Gateway v1 Server │    v1 /     │   - PostgreSQL 18 SSoT          │
     │   - ThreadingHTTPServer (:8000) │  NATS RPC   │   - NVMe POSIX LocalStorage     │
     └────────────────┬────────────────┘             └────────────────┬────────────────┘
                      │                                               │
                      └───────────────────────┬───────────────────────┘
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │  PILLAR 3: DUAL-ENGINE SWARMS   │
                             │  - PydanticAI (<35MB, <100ms)   │
                             │  - CrewAI Dynamic Swarms        │
                             │  - Ephemeral Video Workers      │
                             └────────────────┬────────────────┘
                                              │
                                              ▼
                             ┌─────────────────────────────────┐
                             │  INFERENCE TANDEM ($0 DEFAULT)  │
                             │  - Bifrost AI Gateway (:8080)   │
                             │  - FreeLLMAPI Pool (:3001)      │
                             └─────────────────────────────────┘
```

### Invariants:
1. **SSoT Persistence**: Managed PostgreSQL 18 holds relational and execution state; persistent NVMe volume (`localstorage`) holds files and secrets. No reliance on volatile container rootfs or unbacked ObjectStorage.
2. **Zero-Leak Budgeting**: Default routing uses FreeLLMAPI ($0). Paperclip spend caps enforce hard stop conditions.
3. **Decoupled Runtimes**: Every service runs in dedicated Incus LXC containers with non-blocking threading.
4. **Ephemeral On-Demand Workers**: Compute-heavy workloads (video rendering, large-scale scrapers) use ephemeral containers spawned via recipe steps, executed, and deleted to maintain zero idle cost.

---

## 2. Infrastructure Configuration Blueprint

### A. Zerops Service Manifest (`zerops.yaml` snippet)

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

## 3. Paperclip HTTP Gateway v1 Protocol Specification

Hermes exposes an HTTP Gateway v1 server compatible with Paperclip agent orchestration:

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

## 4. Dual-Engine Swarm Execution

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

## 5. Verification & Telemetry Sensor Suite

```bash
# 1. Verify Hermes Gateway
curl -i http://hermes:8000/health

# 2. Test Paperclip Run Creation
curl -X POST http://hermes:8000/v1/runs \
  -H "Content-Type: application/json" \
  -d '{"task": "Health check audit", "tier": "free"}'

# 3. Stream SSE Events (replace <run_id>)
curl -N http://hermes:8000/v1/runs/<run_id>/events

# 4. Check Paperclip Database Connection
ssh paperclip "paperclipai env"
```
