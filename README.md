# Zerops AstroBranding Sovereign Platform (Modular Template Monorepo)

> High-Performance, Sovereign Fullstack, AI & Astrological Branding Monorepo Template for Zerops Incus LXC Runtimes.  
> Governed by CoHaLo v8.2, Dual-RAG SSoT Architecture, and Natural-Language Modular Deployment.

---

## 🏛️ Two-Tier Architecture: Control Plane & LXC Runtimes

The ecosystem separates platform orchestration from application execution across two distinct tiers:

1. **Sovereign Control Plane (`zcp`)**:
   - Dedicated orchestrator container running the Zerops MCP, GitOps tools, and Google Drive SSoT synchronization.
   - Does **not** run local dev servers or heavy framework compiles. It executes platform workflows, secret injection, and verifies cluster health.
2. **Dedicated LXC Runtimes**:
   - Each application service (`freellmapi`, `bifrost`, `hermes`, `evolution`, `astrobranding`) runs in its own isolated Incus LXC container.
   - Framework builds (`bun run build`, `npm test`, `pytest`) and dev servers run inside the respective containers over SSH (`ssh {hostname} "cd /var/www && <cmd>"`). Long-running servers are managed via `zerops_dev_server`.

```text
├── apps/
│   ├── astrobranding/      # [Runtime 1] Unified Fullstack (Astro 5 SSR + React 19 Islands + Hono + BullMQ) [:3000]
│   ├── bifrost/            # [Runtime 2] Maxim AI Enterprise Gateway (Go 1.22, chromem semantic cache) [:8080]
│   ├── freellmapi/         # [Runtime 3] Multi-Provider Free LLM Proxy with 429 Circuit Breaker [:3001]
│   ├── evolution/          # [Runtime 4] Native WhatsApp Engine (Go whatsmeow, NATS JetStream events) [:8085]
│   └── hermes/             # [Runtime 5] Autonomous Copilot (Python 3.12, NATS JetStream daemon) [:8000]
├── recipes/
│   ├── steps/              # Sequential Step-by-Step Deployment Recipes (01 to 06)
│   ├── landing-minimal.yaml# Minimal Landing Profile (AstroBranding + LocalStorage)
│   ├── brandview-studio.yaml# Brandview Visualizer Studio (Node 22 + Vite + Hono)
│   ├── ecommerce.yaml      # E-Commerce Store (AstroBranding + Valkey + LocalStorage)
│   └── full-mesh.yaml      # Full 10-Service Enterprise Mesh with Frugal Autoscaling
├── packages/
│   ├── contracts/          # Zod 4 Schemas, 15 Shards, Feeds, Multi-Payment & Frappe DTOs (SSoT)
│   ├── database/           # PostgreSQL 18 (pgvector HNSW + uuidv7() + 15 Shards JSONB + Outbox)
│   └── engine/             # Typed SDKs, Multi-Gateway Payment Drivers, Frappe Client & Astrological Orchestrator
├── docs/
│   ├── MODULARIZATION_ROADMAP.md # Master Roadmap & Execution Matrix for Successor AGYs
│   ├── AUDIT_BIFROST_FREELLMAPI.md # Empirical Cache & Virtual Keys Benchmark Report
│   └── MANUAL_COCKPIT.md   # Operator Guide
├── iniciar.sh              # Cold-Start ZCP Control Plane Bootstrapper (SSoT, Tools, Secrets)
├── zerops.yaml             # Multi-Service Build & Run Manifest for Runtimes
└── import.yaml             # Canonical Cluster Manifest
```

---

## 🧭 Natural Language Modular Deployment Protocol

### 1. Cold-Start Bootstrapping (`iniciar.sh`)
When starting a new ZCP container, running `iniciar.sh` bootstraps the control plane:
- Mounts and synchronizes Google Drive SSoT (`/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/`).
- Installs and verifies global CLI tools in `/usr/local/bin` (`docu-validate`, `research-validate`, `ssot-parity-check`, `bifrost-cli`).
- Clones and tracks repositories (`zerops-astrobranding` and `zerops-astro-skills`).
- **`iniciar.sh` does NOT deploy application runtimes automatically.** The control plane sits clean, waiting for instructions.

### 2. Autonomous Deployment by Natural Language
Operators activate deployments by issuing natural language commands to the agent (AGY), which executes the milestone end-to-end without handholding:

- **"Instala freellmapi y bifrost"**: Deploys Hitos 1 & 2 (`recipes/steps/01-freellmapi.yaml` & `02-bifrost-postgres.yaml`). Sets up SQLite in `localstorage`, PostgreSQL 18, Valkey 7.2, and Bifrost with `chromem` cache.
- **"Instala hermes y nats"**: Deploys Hito 3 (`recipes/steps/03-hermes-nats.yaml`). Sets up NATS 2.12 JetStream and wires Hermes Agent to Bifrost using Virtual Key `sk-bf-f702a2c4-c967-4ea3-90bc-7c8f5dad5cd0`.
- **"Instala evolution"**: Deploys Hito 4 (`recipes/steps/04-evolution.yaml`). Connects WhatsApp Engine to PostgreSQL 18, Valkey, and NATS.
- **"Instala la tienda online / ecommerce"**: Deploys bundle `recipes/ecommerce.yaml`.
- **"Instala brandview studio"**: Deploys bundle `recipes/brandview-studio.yaml`.
- **"Instala el ecosistema completo"**: Deploys bundle `recipes/full-mesh.yaml`.

---

## 🤖 Service Interactions & Data Stores

| Service | Runtime | Uses PostgreSQL 18? | Uses Valkey 7.2? | Uses NATS 2.12? | Persistence / Storage | Verified Status |
|---|---|---|---|---|---|---|
| **FreeLLMAPI** | Node.js 24 | No | No | No | SQLite / JSON on Zerops POSIX volume `localstorage` | **Active** (port 3001, 3.7ms cache) |
| **Bifrost** | Go 1.22 (Alpine) | **Yes** (`config_store` & `logs_store`) | **Yes** (KV & Locks) | No | Embedded `chromem` Semantic Cache | **Active** (port 8080, 2.91ms cache, 5 Virtual Keys) |
| **Hermes-Agent** | Python 3.12 (Ubuntu) | No | No | **Yes** (RPC / Events) | Bifrost proxy via Virtual Key | *Prepared in Hito 3* |
| **EvolutionGo** | Go 1.22 (Alpine) | **Yes** (`evogo_auth`) | **Yes** (QR/Sessions) | **Yes** (Chat events) | Dedicated DB in PostgreSQL 18 | *Prepared in Hito 4* |
| **Listmonk** | Go (Alpine) | **Yes** (`listmonk_db`) | No | No | Relational store in PostgreSQL 18 | *Prepared in Hito 5* |
| **AstroBranding** | Bun 1.3.9 (Ubuntu) | **Yes** (Shards & Orders) | **Yes** (BullMQ queues) | **Yes** (Pub/Sub) | S3 Object Storage for exported assets | *Prepared in Hito 6* |

### Critical Architectural Finding: Valkey 7.2 & Semantic Cache
- Zerops `valkey:single@7.2` provides high-speed key-value storage but does not include the proprietary Redis Stack module RediSearch (`FT.*`).
- In Bifrost, configuring `vector_store.type: "redis"` against Valkey silently disables semantic caching.
- **Sovereign Rule**: Bifrost semantic cache uses embedded `chromem` (`vector_store.type: "chromem"`) or Qdrant. Under `chromem`, DeepSeek V4 Pro inference latency dropped from **1730 ms** to **2.91 ms** (**98.6% reduction**).

---

## 💳 Multi-Gateway Payment Architecture & Frappe CRM/ERPNext Sync

The application features a pluggable, environment-driven payment strategy pattern:

1. **Dynamic Gateway Discovery (`/api/v1/payments/gateways`)**:
   - Inspects active environment keys at runtime (`DLOCALGO_*`, `WOMPI_*`, `EPAYCO_*`).
   - Renders only the available gateways in the interactive checkout tabbed interface (`/checkout`).
2. **Unified Webhook Processing (`/api/webhooks/:gateway`)**:
   - Cryptographic signature validation for each gateway.
   - Transactional Outbox Pattern in PostgreSQL 18 with native deduplication (`pay-${gateway}-${txId}`).
3. **Automated Post-Settlement Business Sync**:
   - **Frappe CRM v1.83+**: Automatically marks the corresponding `CRM Deal` as `Won` and updates lead value.
   - **ERPNext**: Generates or links the `Customer` and automatically issues the `Sales Invoice` (`ASTRO-REPORT`).

---

## ⚡ Frugal-First Autoscaling Standard

All runtime containers in Zerops deploy with elastic auto-scaling:

```yaml
minContainers: 1
maxContainers: 2
verticalAutoscaling:
  cpuMode: SHARED         # Minimum starting cost; scales elastically
  minFreeRamGB: 0.25      # Triggers scale if free RAM drops below 250MB
  minFreeRamPercent: 10   # Dynamic buffer
```

Omission of rigid `minCpu`/`maxCpu`/`minRam`/`maxRam` keeps panel controls clear and allows native platform scaling (0.125 GB to 48 GB RAM).

---

## 🛠️ Remote Runtime Commands (SSH to Container)

Because `zcp` is the control plane, all framework and application commands run inside their respective LXC containers:

```bash
# Run build inside the AstroBranding container
ssh astrobranding "cd /var/www && bun run build"

# Run tests inside the AstroBranding container
ssh astrobranding "cd /var/www && bun run test"

# Run migrations or diagnostics inside Bifrost
ssh bifrost "cd /var/www && ./bifrost --version"

# Inspect PostgreSQL directly from zcp using injected environment vars
psql "$db_connectionString" -c "\dt"
```

---

## 🔗 Connected Repositories & SSoT Ecosystem

- **Skills Soberanas (65 skills v8.2)**: [github.com/elplacerdc/zerops-astro-skills](https://github.com/elplacerdc/zerops-astro-skills)
- **Brandview Visualizer Studio**: [github.com/elplacerdc/brandview](https://github.com/elplacerdc/brandview)
- **Roadmap & Matrix for Successor AGYs**: [`docs/MODULARIZATION_ROADMAP.md`](docs/MODULARIZATION_ROADMAP.md)
