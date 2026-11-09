# Paperclip Governance & Spend Caps Watchdog (Zerops Native)

## 1. Architectural Overview

Paperclip (`:3100`) is Pillar 2 of the Sovereign Tri-Pillar Architecture (`hermes` + `paperclip` + `crewai`).
It operates as the organization's governance, budget, and autonomous agency manager:
- **Org Chart & Agent Hierarchy**: Defines CEO, department leads, and autonomous workers.
- **Spend Caps & Budget Control**: Hard ceilings on token spend, tool runs, and external API consumption.
- **Task Queues & Issue Assignment**: Integrates with Linear and Hermes HTTP Gateway v1 for task execution.
- **SSoT Managed Database**: Uses native PostgreSQL 18 cluster via `DATABASE_URL` (completely disabling `@embedded-postgres` and saving ~400 MB RAM).
- **POSIX LocalStorage**: Persistent runtime configuration, logs, and sqlite/attachments isolated at `/mnt/localstorage/paperclip`.

---

## 2. Security Architecture & Deployment Modes

Paperclip is configured in **authenticated public mode**:
```json
{
  "server": {
    "deploymentMode": "authenticated",
    "exposure": "public",
    "bind": "lan",
    "host": "0.0.0.0",
    "port": 3100
  }
}
```

### The First-Admin Bootstrap Mechanism
In public authenticated mode, Paperclip **intentionally disables browser-based self-signup** for claiming the initial instance. This prevents unauthorized network visitors from navigating to the public URL and declaring themselves CEO/Superadmin.

Instead, the operator must generate a cryptographically signed, one-time invite token from the host terminal:
```bash
paperclipai auth bootstrap-ceo
# Or using npx:
npx paperclipai auth bootstrap-ceo
```
Output:
```text
Created bootstrap CEO invite.
Invite URL: https://paperclip-<subdomain>.zerops.app/invite/pcp_bootstrap_<token>
Expires: <timestamp>
```
Opening this link in any browser grants one-time authorization to create the first CEO/admin account and activate the instance.

---

## 3. Persistent Storage & Config Schema

### File System Layout
Paperclip state resides on the persistent NVMe volume mounted at `/mnt/localstorage/paperclip`:
```text
/mnt/localstorage/paperclip/
├── instances/
│   └── default/
│       ├── config.json       # Declarative JSON validated by Zod
│       ├── data/             # Backups and local cache
│       ├── logs/             # File logging
│       └── secrets/          # Key storage
└── storage/                  # Local disk asset storage
```

### Critical Invariant: `~/.paperclip` Symlink
The upstream CLI (`paperclipai`) defaults to looking at `$HOME/.paperclip/instances/default/config.json`.
On Zerops, persistent storage is at `/mnt/localstorage/paperclip`.
Therefore, a canonical symlink must always exist in the user's home directory:
```bash
ln -sfn /mnt/localstorage/paperclip ~/.paperclip
export PAPERCLIP_HOME="/mnt/localstorage/paperclip"
```
This is auto-provisioned by `iniciar.sh` and `setup-zcp.sh`.

---

## 4. Build & Runtime Lifecycle in Zerops

Paperclip is a `pnpm` monorepo containing:
- `@paperclipai/plugin-sdk`
- `@paperclipai/ui`
- `@paperclipai/db`
- `@paperclipai/server`

During Zerops build, `build:runtime` emits runtime JS into `server/dist-runtime/`.
Because Zerops builds in `/build/source`, `zerops.yaml` includes a path replacement:
```bash
sed -i 's|/build/source|/var/www|g' server/dist-runtime/*.mjs
```
The runtime entrypoint `start.sh` auto-seeds `config.json` if missing, sets the database connection, links `~/.paperclip`, and boots `server/dist-runtime/index.mjs`.
