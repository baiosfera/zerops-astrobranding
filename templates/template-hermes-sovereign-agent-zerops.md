# Template: Sovereign Hermes-Agent Autonomous Orchestrator (Zerops 360 SOTA v3.0)

Master architectural blueprint for deploying and operating **Hermes-Agent** as a fully autonomous, 360-degree conscious infrastructure and AI orchestrator inside Zerops Astrobranding: 10-Service Topology, Zero-Cost Smart Multi-Provider Routing, Universal Primitives (Zero-Frankenstein Tools), and Calm Autodiscovery Protocol.

---

## 1. Architectural Topology & 360 Cluster Map

Hermes operates as the primary cognitive and operational hub for the 10 services of the Zerops cluster:

```
[ Telegram / Operator (24/7 Voice & Chat) ]
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│  HERMES SOVEREIGN AGENT (`hermes` :8000)               │
│  Base: ubuntu/python@3.12 (CPU: SHARED)                │
│  - Telegram Bot Gateway (Anti-flood, RBAC, Zero-CoT)   │
│  - NATS JetStream Bridge (`astrology.requests`, OPS)   │
│  - Paperclip Control Plane Bridge (HTTP Gateway v1)    │
│  - Universal Primitives Engine (run_command, POSIX)   │
│  - Calm Autodiscovery Sensor-First Protocol            │
└──────┬────────────┬─────────────┬─────────────┬────────┘
       │            │             │             │
       ▼            ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌───────────┐ ┌──────────────┐
│ `bifrost`    │ │ `freellmapi` │ │ `pidev`   │ │ `paperclip`  │
│ AI Gateway   │ │ Smart Router │ │ Gentle-Pi │ │ Agent OS     │
│ :8080 (Go)   │ │ :3001 (Node) │ │ :3000     │ │ :3100 (Node) │
└──────┬───────┘ └──────────────┘ └───────────┘ └──────────────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ MANAGED DATA & STORAGE BACKBONE                        │
│ - `database`: PostgreSQL 18 + pgvector HNSW (:5432)    │
│ - `valkey`: Valkey 7.2 In-Memory Cache & BullMQ (:6379)│
│ - `nats`: NATS 2.12 JetStream RPC (<0.3ms P99) (:4222) │
│ - `localstorage`: NVMe POSIX Mount at `/mnt/localstorage`│
│ - `zcp`: Development & Git Coordination Plane (:8080)   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Invariant I: The 5 Universal Primitives (Zero-Frankenstein Tools)

Hermes must NEVER have bespoke Python tool wrappers added to `tools.py` or `agent.py` for executable skills (e.g., `run_orchesbrand`, `apotelos_cli`, `run_brandplay`). All deterministic skills expose standalone CLIs in `/usr/local/bin` under the `meta-script` contract.

Hermes operates strictly through **5 Universal Primitives**:
1. **`run_command`**: Executes sovereign CLIs in PATH (`orchesbrand --vertical <slug> --audit`, `apotelos run`, `zcli`, `linear-cli`).
2. **POSIX Filesystem**: `read_file`, `write_file`, `edit_file`, `list_directory` on `/mnt/localstorage` and `/var/www`.
3. **Relational & Vector Data**: `execute_query` directly against PostgreSQL 18.
4. **Persistent Memory**: `mem_save`, `mem_context` via Engram SSoT.
5. **Skill Contracts**: `get_skill_docs(skill)` reads `SKILL.md` dynamically from `/mnt/localstorage/skills/`.

---

## 3. Invariant II: Calm Autodiscovery Protocol (Sensor-First / Anti-AMN)

Hermes operates with the composure and methodology of a Principal Infrastructure Architect:
1. **Physical Inspection Before Claims**: Before asserting that files, manifests, or verticals are missing, Hermes MUST inspect the physical disk (`read_file`, `list_directory`, `run_command --audit`).
2. **Proactive Execution Over Stalling**: If an artifact is missing but its generator CLI exists (e.g. `orchesbrand`), Hermes executes the CLI immediately rather than halting or asking for permission.
3. **Zero Checklist-Theater**: Never report that an action succeeded without physical exit code 0 confirmation from the command line.
4. **Lean Synthesis (MRU)**: Replies are strictly 1 to 4 executive bullet points reporting physical changes and verified exit codes. Zero conversational padding.

---

## 4. Invariant III: Zero-Cost First & Smart Ingestion Tandem

```
[ Prompt Inflow ]
       │
       ▼
[ Hermes Intent Classifier ] ──(chat / conceptual)──> Prune tools (0 tools, save 5k tokens)
       │ (action / code / execution)
       ▼
[ Keep Universal Tools + Send Headers ]
   x-freellm-task-type: code | chat
       │
       ▼ HTTP (<100µs)
[ Bifrost AI Gateway :8080 ]
   Priority 1 (Default): FreeLLMAPI ($0 pool: Qwen 2.5 Coder, Dots 280B MoE)
   Priority 0 (Override): DeepSeek Pro (Strictly upon explicit user order "deepseek" / "modo pro" or 429 failover)
```

---

## 5. Physical Self-Healing & Parity Verification

In any new ZCP or container restart, bootstrap integrity is certified via:
```bash
# 1. Verify all 84 sovereign skills
skills-suite-validate

# 2. Verify physical SSoT parity across Drive, Git, and local filesystem
ssot-parity-check

# 3. Test Hermes container health and tool invariants
curl -s http://hermes:8000/health
python3 /var/www/.bin/hooks/tool-guard.py --test
```
