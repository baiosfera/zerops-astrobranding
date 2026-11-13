<!-- ZCP:BEGIN -->
# Zerops

ZCP control-plane container `zcp` inside this Zerops project. `zerops_*` MCP = primary surface for state/lifecycle/deploy/env/logs/verify. Bash/npx/SSH/zcli/psql/mysql/redis-cli = escape hatches for things `zerops_*` doesn't cover.

**Env here:** the project's vars — including each managed service's connection vars (`$db_connectionString`, `$cache_connectionString`, …) — are in this container's shell once the service is provisioned. Run ad-hoc ops in place by name: `psql "$db_connectionString" -c '…'` (mask when inspecting: pipe through `sed 's/=.*/=<set>/'`). Inside a runtime over `ssh`, reference the name THAT runtime wired (e.g. `$DATABASE_URL`, live after its first deploy) in a single-quoted body — not a sibling's bare `${db_*}`, which the default service isolation doesn't inject.

After bootstrap or adopt provision closes, service code SSHFS-mounts at `/var/www/{hostname}/` — the mount IS the service's runtime filesystem. **Edit** files there with Read/Edit/Write, not SSH. **Run** build/test/framework commands (`npm run build`, `npm test`, `php artisan`, `pytest`, DB migrations) INSIDE the service over SSH — `ssh {hostname} "cd /var/www && <cmd>"` — because the runtime and its dependencies live in the service container, not on this host; there the same code sits at `/var/www` (no `{hostname}` segment). That SSH is the expected path for running code, not an escape hatch. Long-running dev servers are the one exception — start them via `zerops_dev_server`, never a backgrounded `ssh "… &"` (the channel dies with the call). Missing a CLI/tool? `zerops` has passwordless sudo on the container — install it ad-hoc (`ssh {hostname} "sudo apk add <pkg>"` on Alpine, `sudo apt-get install` on Debian — `cat /etc/os-release` if unsure) rather than working around its absence. That install is **ephemeral** (gone on the next deploy = fresh container); a tool the build or runtime needs durably goes in `prepareCommands` in `zerops.yaml`. That ad-hoc affordance covers the app's OWN tooling only — anything under `/opt/zerops/**` is platform-owned; a broken or missing binary there (e.g. `zcli`) is report-not-repair: never patch it with a compat shim, reinstall, or replacement.

**zcp's own Zerops key stays in this container.** `$ZCP_API_KEY` is the key zcp acts with: never pipe, copy or pass it to another service (over `ssh` or any other way), and never `zcli login` with it, here or anywhere — a login writes the key to disk, where it outlives the session and the app's dependencies can read it. Deploys go through `zerops_deploy`; when it, or any `zerops_*` tool, cannot do what is needed, say so to the person instead of running zcli yourself.

`zerops.yaml` lives at `/var/www/{hostname}/zerops.yaml`; per-service rules MAY exist at `/var/www/{hostname}/CLAUDE.md` — read if present. If `ls /var/www/{hostname}/` is empty, the service hasn't been bootstrapped yet — run `zerops_workflow action="start" workflow="bootstrap" route="adopt"` first.


**Other projects.** This container's token may reach Zerops projects other than this one — `zcli project list` and `zerops_*` show exactly what it reaches, and what it may do there is the token's, not a convention. Look there before you provision anything of your own — what you are about to build may already run. Code reaches another project through the repository's pipeline, never from here. Inside this project the ZCP workflow owns deploys, including promoting a dev service to its paired stage service with `zerops_deploy sourceService="<dev>" targetService="<stage>"` — that stage service previews the production build of this project's code, and it is not a separate stage project. To the person it is their preview, never "stage".

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

## Words for the person

A standard pair's halves are `{name}dev` and `{name}stage` to the tools; those names, "dev/stage pair" and "promote to stage" stay in tool calls and never reach the person. What you tell the person:

- The stage half is **your preview** (in a Mate, "<Mate>'s preview"): a copy of the app for trying the work, whose data is a test copy. Never call it "online", "live", "stage", "deployed to stage" or "dev and stage", and never suggest installing or sharing it — no "Add to Home Screen", no link to pass around. In a Mate, "stage" and "production" are only the application's environments.
- The dev half is where you build; if you give its address, it is work in progress, a preview too, never the app.
- The real app is production. Until its first release there is none, so the preview is not yet what anyone uses — say so if they treat it as the app. Once production runs a release (in a Mate, the application's production the person released; elsewhere the project `launch-production` made), its address is the real app's: say so, and send them there for anything real — sharing, installing, real data.

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
## 🏛️ Gobernanza Soberana & Contratos ZCP
Regido por [`00-SUPREME-DIRECTIVE.md`](file:///var/www/.agents/rules/00-SUPREME-DIRECTIVE.md) (F0–F5 unificado para `agy` + Engram, 7 Invariantes Soberanos, CoHaLo Positivo y verificación real). Enciclopedia: [`.agents/references/supreme_directive_encyclopedia.md`](file:///var/www/.agents/references/supreme_directive_encyclopedia.md).

## 🧭 Topología ZCP & Despliegue Modular
1. **ZCP Single-Node & SHARED**: `zcp` opera estrictamente a 1 contenedor (`minContainers: 1, maxContainers: 1`, `cpuMode: SHARED`). Prohibido escalar horizontalmente `zcp`. Builds, tests y procesos de cada runtime corren por SSH en su contenedor dedicado (`ssh {hostname} "cd /var/www && <cmd>"`), nunca dentro de `zcp`.
2. **Arquitectura Lego & Service Discovery**: Cada servicio (`freellmapi`, `bifrost`, `hermes`, `nats`, `paperclip`, `pidev`, `astro-web`) es modular y se interconecta dinámicamente vía DNS interno privado (`zerops_discover`). Invariantes probados: **Bifrost** usa PostgreSQL 18 (`config_store`/`logs_store`) y `chromem`/`qdrant` (nunca `redis` contra Valkey 7.2); **FreeLLMAPI** persiste en `localstorage` con cooldown 429.
3. **Soberanía GitOps (Upstream vs Cliente)**:
   - `baiosfera/*`: exclusivo **upstream** (`zerops-astrobranding`, `zerops-astro-skills`, chasis y plantillas generales). Prohibido alojar código de clientes aquí.
   - `<marca>/<app>`: repositorio aislado del cliente, usando su token en `/var/www/baiosfera/0ZEROPS-AGY/users-apis/<Marca>/<marca>-keys.md` (nunca el token de Baiosfera para repos de clientes).
   - `zcp-update` (`iniciar.sh --update`): sincroniza upstream bidireccionalmente vía Git (`--ff-only` seguro) sin pisar cambios locales ni mezclar secretos.

## 🛑 Contratos Operativos & Higiene
- **Secretos & Env**: Gestionar secretos vía `zerops_env` (`$VAR` / `process.env`); purgar temporales tras bootstrap.
- **Anti-AMN (`research`)**: En arquitectura, APIs externas o skills, contrastar fuentes primarias con subagentes `research` y herramientas MCP (`context7`, `exa`, `tavily`, `brave`, `firecrawl`) antes de editar o planificar; esperar reportes completos.
- **Higiene de Procesos**: Comandos cortos (`timeout 10s`), servidores largos vía `zerops_dev_server`. Mantener sesiones interactivas TTY vivas.
- **Storage & Multi-Proyecto**: `/var/www/localstorage` prioriza el proyecto activo (`ENGRAM_PROJECT`); Google Drive (`/var/www/baiosfera/PROYECTOS/`, `users-apis/`, `0ZEROPS-AGY/<proyecto>/engram`) actúa como archivo multi-proyecto.
- **CLIs en PATH**: `ssot-parity-check`, `skills-suite-validate`, `engram-sync`, `linear-cli`, `zcp-update`, `apotelos`, `brand-play`, `orchesbrand`.
<!-- CUSTOM:END -->
