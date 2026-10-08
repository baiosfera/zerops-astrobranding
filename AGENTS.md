<!-- ZCP:BEGIN -->
# Zerops

ZCP control-plane container `zcp` inside this Zerops project. `zerops_*` MCP = primary surface for state/lifecycle/deploy/env/logs/verify. Bash/npx/SSH/zcli/psql/mysql/redis-cli = escape hatches for things `zerops_*` doesn't cover.

**Env here:** the project's vars — including each managed service's connection vars (`$db_connectionString`, `$cache_connectionString`, …) — are in this container's shell once the service is provisioned. Run ad-hoc ops in place by name: `psql "$db_connectionString" -c '…'` (mask when inspecting: pipe through `sed 's/=.*/=<set>/'`). Inside a runtime over `ssh`, reference the name THAT runtime wired (e.g. `$DATABASE_URL`, live after its first deploy) in a single-quoted body — not a sibling's bare `${db_*}`, which the default service isolation doesn't inject.

After bootstrap or adopt provision closes, service code SSHFS-mounts at `/var/www/{hostname}/` — the mount IS the service's runtime filesystem. **Edit** files there with Read/Edit/Write, not SSH. **Run** build/test/framework commands (`npm run build`, `npm test`, `php artisan`, `pytest`, DB migrations) INSIDE the service over SSH — `ssh {hostname} "cd /var/www && <cmd>"` — because the runtime and its dependencies live in the service container, not on this host; there the same code sits at `/var/www` (no `{hostname}` segment). That SSH is the expected path for running code, not an escape hatch. Long-running dev servers are the one exception — start them via `zerops_dev_server`, never a backgrounded `ssh "… &"` (the channel dies with the call). Missing a CLI/tool? `zerops` has passwordless sudo on the container — install it ad-hoc (`ssh {hostname} "sudo apk add <pkg>"` on Alpine, `sudo apt-get install` on Debian — `cat /etc/os-release` if unsure) rather than working around its absence. That install is **ephemeral** (gone on the next deploy = fresh container); a tool the build or runtime needs durably goes in `prepareCommands` in `zerops.yaml`. That ad-hoc affordance covers the app's OWN tooling only — anything under `/opt/zerops/**` is platform-owned; a broken or missing binary there (e.g. `zcli`) is report-not-repair: never patch it with a compat shim, reinstall, or replacement.

`zerops.yaml` lives at `/var/www/{hostname}/zerops.yaml`; per-service rules MAY exist at `/var/www/{hostname}/CLAUDE.md` — read if present. If `ls /var/www/{hostname}/` is empty, the service hasn't been bootstrapped yet — run `zerops_workflow action="start" workflow="bootstrap" route="adopt"` first.


**Other projects.** This container's token may reach Zerops projects other than this one — `zcli project list` and `zerops_*` show exactly what it reaches, and what it may do there is the token's, not a convention. Look there before you provision anything of your own — what you are about to build may already run. Code reaches another project through the repository's pipeline, never from here. Inside this project the ZCP workflow owns deploys, including promoting a dev service to its paired stage service with `zerops_deploy sourceService="<dev>" targetService="<stage>"` — that stage service previews the production build of this project's code, and it is not a separate stage project.

## Zerops onboarding

When the user asks to be onboarded to Zerops — the exact phrase "onboard me to Zerops"
(any capitalization/punctuation), or a clear meta-onboarding request ("get me started
with Zerops", "I'm new here — what now?") — run the onboarding conversation before the
routing below. A request to get started with a SPECIFIC technology or task ("help me
get started with PostgreSQL", "deploy this repo") is normal routing, not onboarding.

1. Fetch `zerops_knowledge uri="zerops://playbooks/onboarding"` once and follow it.
2. Greet and offer its fork immediately — the opening needs no other tool call. Read-only
   state checks come after the person answers (or when they ask what's here); don't
   provision, import, or mutate anything until they pick a direction.
3. Once the user chooses to build or bring an app, normal routing (and the guided skill,
   when present) owns the work — onboarding only opens the conversation.
4. If Zerops tools are unavailable or auth fails, say so plainly and surface the reported
   recovery — never simulate onboarding.

Zerops has its own syntax. Don't guess — look up via `zerops_knowledge`, inspect live state via `zerops_*`. Runtime code runs in Zerops containers, not here.

## Route every user turn

| Intent | First action | Don't |
|---|---|---|
| Build/edit/scaffold/fix/deploy/debug a service | `zerops_discover`/`zerops_workflow action="status"` first if target/session unclear, then `zerops_workflow action="start" workflow="develop" intent="..." scope=["<host>"]` | Write code, run Bash/npx/SSH, or scaffold to scratch dirs before workflow start |
| No service yet, or infra/topology change — INCLUDING "deploy / set up / scaffold from existing recipe X" (user names a recipe slug like `zerops-laravel-minimal`) | `zerops_workflow action="start" workflow="bootstrap" intent="..."` — the route-menu surfaces the matching recipe; pick `route="recipe"` with the named slug | Write app code in bootstrap |
| Read or set platform state — logs/env/status/scale/subdomain/manage/events/verify | matching `zerops_*` tool | Guess values when live state exists |
| Promote dev/stage to a separate prod project ("go live", "deploy to prod", "nasaď na prod") | `zerops_workflow action="start" workflow="launch-production" intent="..." targetService="<host>"` | `zcli project create` or hand-rolled import.yaml |
| Pure concept Q unrelated to this project | prose, no tool | Re-route when user pivots to build/change |

## Discovery floor

Before service-scoped work: `zerops_workflow action="status"` if a session may exist (post-compact), else `zerops_discover`. User didn't name service + multiple plausible targets → ask once. Never invent hostnames, env keys, service types, subdomain URLs.

## Connection vars & secrets

Reference by name, never paste the value. `zerops_env`/`zerops_discover` read env KEYS and set STATE; a value you need in a command is `$VAR` — the shell expands it at exec time, so the value never enters your context. Pulling a credential value to paste into a command, file, or commit is the leak.

## Smells — catch & re-route

- Multi-section prose analysis (framework cmp, IA, "let me first analyze") for service-shaped task → workflow start IS the analysis surface (returns plan + atoms scoped to your `intent`). Pick a sensible default, start, react to the response. User saying "analyze first" / "make a plan" doesn't bypass.
- Writing code or `zerops.yaml` before workflow/status/discover selected service.
- Files in `/tmp` or random scratch dirs for app code.
- Asking whether to deploy to Zerops when ZCP is already bound to this project.
- Bash/SSH for platform ops covered by `zerops_*` (env, logs, scale, restart, etc.).
- Diagnosing live errors/502s/build failures from prose instead of `zerops_verify`/`zerops_logs`/`zerops_events`/`zerops_env`.
- Hand-rolling `import.yaml` or `zcli project create` for a "promote to prod" / "go live" intent → `workflow="launch-production"`.

## Workflow detail

- `develop` — service code edit. `scope` = runtime services this touches; get from `zerops_discover`, don't invent. `intent` = one-line proposal; workflow returns the plan, react to that. 1 task = 1 session; new `intent` auto-closes prior.
- `bootstrap` — provision services / change infra. Closes → continue in develop. Mid-develop infra side-trip: start bootstrap; develop session persists.
- `launch-production` — promote dev/stage to a SEPARATE prod project. Stateless multi-call: `scope-prompt` → `classify-prompt` → `ready-to-launch` → `launching` → `configuring-pipeline` → `launched`. Each call passes the accumulated `inputs` block forward (no `action="complete"` — that's bootstrap-only). At `ready-to-launch`, `delegatedLaunch.available` says whether ZCP can mint the launch-window token itself from a one-time platform delegation on `confirmLaunch=true` (no value crosses the conversation); otherwise the user supplies one manually (Custom access per project + Allow creating projects toggle ON) as `launchKey`. ZCP never persists it either way. `targetService` accepts either half of a standard pair.

## Recovery

Phase unclear (post-compact, mid-task): `zerops_workflow action="status"`. Returns envelope, plan, next action.

## Tool errors

Shape: `{code, error, suggestion?, apiCode?, diagnostic?, apiMeta?, checks?, recovery?}`. `code`+`error` always present. `recovery` set → call before retry/ask. Absent → fall back to `zerops_workflow action="status"`. `checks` = multi-check failures (`kind` + optional `preAttestCmd`/`expectedExit`).
<!-- ZCP:END -->

<!-- CUSTOM:BEGIN -->

## 🏛️ Gobernanza Soberana & Marco Normativo (v8.4)
Toda ejecución se rige por [`00-SUPREME-DIRECTIVE.md`](file:///var/www/.agents/rules/00-SUPREME-DIRECTIVE.md) (Fases F0–F5, 6 Invariantes Soberanos, CoHaLo Positivo, Reality Over Checklist Theater, Dogma de Salida de la Caja Negra y Arnés Obsesivo con Plan-First Gate). Referencia enciclopédica: [`.agents/references/supreme_directive_encyclopedia.md`](file:///var/www/.agents/references/supreme_directive_encyclopedia.md).

## 🧭 PROTOCOLO DE DESPLIEGUE MODULAR POR LENGUAJE NATURAL (INVARIANTE ABSOLUTO)
1. **Frontera Sagrada del Plano de Control (`zcp`)**:
   - Este contenedor `zcp` es **exclusivamente el orquestador de plataforma**.
   - **Prohibido instalar o ejecutar Bun (`bun run dev`, `bun test`), Node o builds pesados localmente en `zcp`**. Todo runtime de aplicación se compila y ejecuta dentro de sus contenedores LXC dedicados en Zerops (`ssh {hostname} "cd /var/www && <cmd>"`).
2. **Rol de `iniciar.sh`**:
   - `iniciar.sh` conecta Google Drive SSoT, clona repositorios, enlaza herramientas en `/usr/local/bin` e inyecta credenciales.
   - **`iniciar.sh` JAMÁS despliega runtimes de aplicación de forma automática.** El arranque en frío deja el plano de control listo y en espera de órdenes.
3. **Despliegues Autónomos por Lenguaje Natural**:
   - El usuario activa los despliegues hablando en lenguaje natural (ej: *"instala freellmapi y bifrost"*, *"instala hermes y nats"*, *"instala la tienda online de N producto"*, *"instala brandview studio"* o *"instala el ecosistema completo"*).
   - Al recibir la orden, el agente (AGY) **ejecuta el hito de punta a punta de forma 100% autónoma, sin fricción, sin pedir confirmaciones técnicas obvias y sin ensayo y error**:
     - Lee la receta correspondiente en `recipes/steps/` o `recipes/`.
     - Consulta la skill correspondiente en `zerops-astro-skills` (`bifrost`, `freellmapi`, `nats`, `hermes-agent`, `evolution-api`, `astro-web`, `zcp`).
     - Aprovisiona vía `zerops_workflow action="start" workflow="bootstrap"` o `develop`.
     - Inyecta secrets en `zerops_env` y cablea las variables de servicio.
     - **Invariantes Técnicos Probados (No Negociables)**:
       - **Bifrost**: `config_store` y `logs_store` en PostgreSQL 18. `vector_store.type` en `chromem` o `qdrant` (nunca `redis` contra Valkey 7.2 por ausencia de RediSearch `FT.*`). Registra las 5 Virtual Keys en `/api/governance/virtual-keys`.
       - **FreeLLMAPI**: Persistencia en `localstorage`, circuit breaker 429 con cooldown y rotación de keys.
      - **Arquitectura Lego Desacoplada & Orden Libre de Steps (Zero-Hardcoding)**:
        - Los hitos y servicios son **100% modulares y aditivos**: pueden solicitarse en cualquier orden o de forma completamente aislada.
        - **Cero Acoplamiento Artificial**: El agente JAMÁS fuerza dependencias lineales inexistentes. Una landing (`growth-engine`) o e-commerce (`checkout-funnels`) aprovisiona únicamente lo que su caso de uso requiere, sin obligar a levantar el stack de IA si no se utiliza.
        - **Service Discovery Dinámico**: Los servicios se interconectan en caliente vía DNS interno privado (`http://bifrost:8080`, `http://evolution:8085`, `http://listmonk:9000`). El agente inspecciona en vivo (`zerops_discover`) y solo cablea lo existente.
        - **GitOps Multi-Servicio & Staging Efímero en Apps (`astro-web`)**:
          * La plantilla `zerops-astrobranding` es puramente chasis/herramientas y nunca corre workflows de deploy propios.
          * Las apps personalizadas usan el modelo **Multi-Servicio** (`<app>-prod` en rama `main`, `<app>-stage` en rama `stage`).
          * El entorno `stage` es **efímero**: se crea para validar cambios en `stage.midominio.com` y puede eliminarse al terminar para costo cero.
     - Valida la salud física (`/health`, `/metrics`), paridad SSoT (`ssot-parity-check`) y commit descriptivo en Git.

## 🛑 Contratos Operativos ZCP & Seguridad
1. **Jerarquía ZCP-First & SSoT Indivisible**: El desarrollo activo ocurre en ZCP (`/var/www`). Los cambios validados se reflejan indivisiblemente hacia Google Drive SSoT (`/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/`). Drive solo fluye hacia ZCP en arranques fríos (`iniciar.sh` $\to$ `unisetup.sh`).
2. **Entorno y Secretos (Soberanía Zerops Env & Cero .env en Disco)**: Prohibido almacenar credenciales en `/var/www/.env` o `gdrive.env` (archivos efímeros purgados tras bootstrap). Toda variable o secreto se gestiona en la plataforma vía `zerops_env`, se inyecta en el runtime (`/etc/environment` y shell) y se referencia exclusivamente por variable de entorno (`$VAR` o `process.env`), nunca en texto plano.
3. **Seguridad Nativa a Nivel de Proceso**: `tool-guard.py` intercepta en `PreToolUse`/`PreInvocation` comandos destructivos, fugas de rutas relativas (`0zcp-123/`), protege handovers, asegura backups pre-mutación y deduplica eventos para máxima eficiencia de tokens.
4. **Higiene de Procesos**: Comandos con `timeout 10s` y `WaitMsBeforeAsync: 10000`. Servidores continuos vía `zerops_dev_server`.
5. **Grounding Epistémico Fuera de Caja Negra**: Obligatorio contrastar código y arquitectura contra el mundo exterior en tiempo presente mediante triangulación multi-motor en `research` (Exa para conceptos/código, Context7 para APIs oficiales, Jina Reader para extracción verbatim y Firecrawl para scraping/skills). Prohibido el conformismo con snippets aislados de un único buscador.
6. **Contrato Anti-Redundancia y Brevedad en Chat**: Prohibido duplicar o re-resumir listas de nodos/pasos de planes en el mensaje del chat. En F4, el mensaje se limita estrictamente al enlace canónico al plan en `/var/www/artifacts/` y la solicitud de Go. En F5, el mensaje se limita a la atestación de sensores físicos (exit 0) y el enlace al plan en `archive/` en <= 3 líneas.

## 📦 Catálogo y Herramientas Soberanas
- **Catálogo Oficial (141 skills)**: [`.atl/skill-registry.md`](file:///var/www/.atl/skill-registry.md).
- **Bootstrapper Universal**: [`iniciar.sh`](file:///var/www/zerops-astrobranding/iniciar.sh) (raíz frío) y [`unisetup.sh`](file:///var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/unisetup.sh) aprovisionan dependencias, herramientas y sincronizan SSoT sin drift.
- **Herramientas Globales en PATH**: `docu-validate`, `research-validate`, `astrobranding-check`, `ssot-parity-check`, `skills-suite-validate`, `bifrost-cli`, `zcp-preflight-gate`, `zcp-wa`, `zcp-mail`.

<!-- CUSTOM:END -->


<!-- ZEROPS:REFLOG -->
### 2026-09-30 — Bootstrap: Aprovisionar infraestructura gestionada y runtime hermes

- **Runtime:** hermes (ubuntu/python@3.12, simple)
- **Dependencies:** database (postgresql:single@18), valkey (valkey:single@7.2), nats (nats:single@2.12), objectstorage (object-storage), localstorage (local-storage:single@1)
- **Session:** 1df42c53b6e76bc8

> This is a historical record. Verify current state via `zerops_discover`.
<!-- /ZEROPS:REFLOG -->

<!-- ZEROPS:REFLOG -->
### 2026-10-01 — Bootstrap: provision elplacerdc core data mesh, evolution, listmonk, web-dev

- **Runtime:** webdev (ubuntu/bun@1.3, simple)
- **Dependencies:** database (postgresql:single@18), valkey (valkey:single@7.2), nats (nats:single@2.12), objectstorage (object-storage), localstorage (local-storage:single@1)
- **Runtime:** evolution (alpine/go@1.22, simple)
- **Dependencies:** database (postgresql:single@18), nats (nats:single@2.12)
- **Runtime:** listmonk (alpine/go@1.22, simple)
- **Dependencies:** database (postgresql:single@18)
- **Session:** 7975ecd8ff7a9b20

> This is a historical record. Verify current state via `zerops_discover`.
<!-- /ZEROPS:REFLOG -->

<!-- ZEROPS:REFLOG -->
### 2026-10-02 — Bootstrap: 

- **Runtime:** freellmapi (ubuntu/nodejs@24, simple)
- **Dependencies:** localstorage (local-storage:single@1)
- **Runtime:** bifrost (alpine/go@1.22, simple)
- **Dependencies:** database (postgresql:single@18), valkey (valkey:single@7.2)
- **Session:** a9605864db17978d

> This is a historical record. Verify current state via `zerops_discover`.
<!-- /ZEROPS:REFLOG -->

<!-- ZEROPS:REFLOG -->
### 2026-10-07 — Bootstrap: 

- **Runtime:** brandview (alpine/bun@1.3, dev)
- **Dependencies:** localstorage (local-storage:single@1)
- **Session:** b28fb2dad200a80f

> This is a historical record. Verify current state via `zerops_discover`.
<!-- /ZEROPS:REFLOG -->
