# 🏛️ Directivas Operativas para Agentes Antigravity (AGY)

Este repositorio es una **plantilla de monorepo soberano, agnóstico y multi-ZCP** optimizada para la plataforma **Zerops (Incus LXC runtimes)**. Sintetiza la arquitectura de contratos estrictos, Transactional Outbox y guardián de capas de `di-sukharev/vibe`, con el modelo de mismo origen en puerto 3000 de `xanthous-tech/hono-astro-remix-template` (Astro 5 SSR + islas React 19 + API Hono en Bun nativo).

---

## 🛑 Principio Arquitectónico Fundacional (Anti-AMN)

1. **Este contenedor es el Plano de Control (`zcp`)**:
   - Este entorno es **únicamente** la consola de orquestación y administración de Zerops (`zcp@1`).
   - **Acá NO corre la aplicación ni sus bases de datos.**
   - No intentes levantar servidores de desarrollo (`bun run dev`) ni ejecutar builds pesados en este contenedor.
2. **Los Runtimes Viven en Zerops (Incus LXC)**:
   - La aplicación y sus dependencias se despliegan en una malla soberana de **10 servicios independientes** aprovisionados mediante [`import.yaml`](file:///var/www/zerops-astrobranding/import.yaml).
   - El servicio principal (`astrobranding`) corre en su propio contenedor Incus LXC nativo (**`ubuntu/bun@1.3.9`** en el puerto `:3000`).
   - Las compilaciones de producción (`bun install`, `bun run build`) las ejecuta el pipeline nativo de Zerops declarado en [`zerops.yaml`](file:///var/www/zerops-astrobranding/zerops.yaml), **nunca** el agente en el host de control.
3. **Herramientas Nativas de Plataforma**:
   - Para interactuar con Zerops, usá exclusivamente los tools MCP de Zerops (`zerops_workflow`, `zerops_import`, `zerops_discover`, `zerops_events`, `zerops_logs`, `zerops_verify`, `zerops_delete`).
   - Jamás uses `zcli` dentro de este contenedor ni intentes instalarlo: el contenedor `zcp` ya está enlazado a la API nativa de la plataforma.

---

## 🏛️ Desarrollo Conjunto Obligatorio con `zerops-astro-skills`

Este repositorio NO se programa ni se despliega en el vacío:
1. **SSoT de Skills Soberanas (`zerops-astro-skills`)**:
   - Cada servicio, runtime, base de datos y framework cuenta con una skill viva en `/var/www/zerops-astro-skills/<nombre>/SKILL.md` (y su réplica activa en `.agents/skills/`).
   - **Regla Mandatoria**: ANTES de diseñar, modificar, configurar o desplegar un servicio (`freellmapi`, `local-storage`, `bifrost`, `postgresql`, `valkey`, `nats`, `hermes`, `evolution`, `listmonk`, `astro-web`, `bknd`, `frnt`), el agente DEBE leer físicamente su `SKILL.md` y cumplir sus Invariantes Duros.
   - Si al desplegar un servicio se descubre un comportamiento de producción, un gotcha o una optimización, el agente DEBE auditar y actualizar la skill correspondiente en `zerops-astro-skills` bajo una rama descriptiva (`feat/<servicio>-audit`).

---

## 🚀 Protocolo de Inicialización y Despliegue Quirúrgico

Para evitar desplegar contenedores vacíos o placeholders rotos, el aprovisionamiento se realiza hito por hito mediante las recetas quirúrgicas de [`recipes/steps/`](recipes/steps/) usando [`scripts/deploy-step.sh`](scripts/deploy-step.sh):

### Hito 1: Almacenamiento Local + FreeLLMAPI Multi-Provider Proxy
- **Receta:** `recipes/steps/01-freellmapi.yaml` (`localstorage` + `freellmapi`).
- **Skill:** [`freellmapi`](/var/www/zerops-astro-skills/freellmapi/SKILL.md) y [`local-storage`](/var/www/zerops-astro-skills/local-storage/SKILL.md).
- **Inyección de Claves en ZCP Limpio:**
  Ejecutar el inyector soberano de credenciales:
  ```bash
  ./scripts/seed-freellmapi-keys.sh [--keys /ruta/a/keys.md]
  ```
  O inyectar `FREEAPI_CONFIG_JSON` directamente en `zerops_env`.
- **Sensor de Validación Física:**
  - Health check: `curl -s http://freellmapi:3001/api/ping` $\to$ `{"status":"ok"}`.
  - Inferencia real: `curl -s POST http://freellmapi:3001/v1/chat/completions` con `model: "auto"` $\to$ HTTP 200 con header `_routed_via`.

### Hito 2: Datos Relacionales + Caché + Bifrost AI Gateway
- **Receta:** `recipes/steps/02-bifrost-postgres.yaml` (`database` postgresql:single@18, `valkey:single@7.2`, `bifrost`).
- **Skills:** [`bifrost`](/var/www/zerops-astro-skills/bifrost/SKILL.md), [`postgresql`](/var/www/zerops-astro-skills/postgresql/SKILL.md), [`valkey`](/var/www/zerops-astro-skills/valkey/SKILL.md).
- **Invariante:** Bifrost DEBE persistir en PostgreSQL (`BIFROST_DB_TYPE=postgres`) y consumir FreeLLMAPI como upstream en `http://freellmapi:3001/v1`.

### Hito 3: RPC de Ultra-Baja Latencia + Agente Autónomo Hermes
- **Receta:** `recipes/steps/03-hermes-nats.yaml` (`nats:single@2.12`, `hermes` ubuntu/python@3.12).
- **Skills:** [`nats`](/var/www/zerops-astro-skills/nats/SKILL.md), [`hermes-agent`](/var/www/zerops-astro-skills/hermes-agent/SKILL.md).

### Hito 4: Gateway Omnicanal WhatsApp (Evolution)
- **Receta:** `recipes/steps/04-evolution.yaml` (`evolution` alpine/go@1.22 en PostgreSQL + NATS).
- **Skill:** [`whatsapp-engine`](/var/www/zerops-astro-skills/whatsapp-engine/SKILL.md).

### Hito 5: Email Marketing Soberano (Listmonk)
- **Receta:** `recipes/steps/05-listmonk.yaml` (`listmonk` alpine/go@1.22 en PostgreSQL).
- **Skill:** [`listmonk`](/var/www/zerops-astro-skills/listmonk/SKILL.md), [`email-marketing`](/var/www/zerops-astro-skills/email-marketing/SKILL.md).

### Hito 6: Webapp Agnóstica SSR + S3 Object Storage
- **Receta:** `recipes/steps/06-astro-web.yaml` (`objectstorage`, `astrobranding` ubuntu/bun@1.3.9).
- **Skills:** [`astro-web`](/var/www/zerops-astro-skills/astro-web/SKILL.md), [`bun`](/var/www/zerops-astro-skills/bun/SKILL.md), [`frnt`](/var/www/zerops-astro-skills/frnt/SKILL.md).

### Consolidación Final: Blueprint de 1-Solo-Paso
Una vez que cada hito individual ha sido desplegado, auditado y validado en vivo, se compila [`import.yaml`](import.yaml) consolidado para levantar la infraestructura completa fluida en una sola importación.
3. Zerops aprovisiona la infraestructura en cascada estricta por prioridades:
   - **Prioridad 10 (Datos y Colas):** `database` (PostgreSQL 18), `valkey` (Valkey 7.2), `nats` (NATS 2.12), `objectstorage` (S3) y `localstorage` (volumen POSIX).
   - **Prioridad 8 (Inferencia Upstream):** `freellmapi` (Node.js 24 + SQLite).
   - **Prioridad 6 (Gateways):** `bifrost` (Go v2.0.0, AI Gateway en `:8080`) y `evolution` (Go WhatsApp Engine en `:8085`).
   - **Prioridad 4 (Agente Autónomo):** `hermes` (Python 3.12 en Ubuntu).
   - **Prioridad 2 (Webapp Fullstack):** `astrobranding` (Bun 1.3.9 en `:3000`).

### 5. Adopción y Montajes Automáticos
Una vez creados los servicios, ZCP adopta los runtimes y monta el código en `/var/www/<hostname>/`:
```json
zerops_workflow action="start" workflow="bootstrap" route="adopt"
zerops_workflow action="complete" step="discover" scope=["astrobranding", "bifrost", "evolution", "freellmapi", "hermes"]
zerops_workflow action="complete" step="provision" attestation="Servicios verificados y montados"
```

---

## 🏛️ Invariantes Técnicos del Monorepo

- **Agnosticismo Total**: Prohibido hardcodear rutas absolutas de usuarios específicos, correos de cuentas o claves fijas. Todo debe operar con variables de entorno o archivos pasados por parámetro.
- **SSoT en `packages/contracts`**: Los tipos y validadores residen en Zod dentro de `packages/contracts`. Ni el frontend ni el backend inventan esquemas duplicados.
- **Lakehouse Astrológico & Protección de Créditos (`packages/engine`)**: El motor de extracción universal (`executeUniversalExtraction`) implementa clientes tipados para los 15 shards astrológicos en `packages/engine/src/clients/`. Opera **por defecto con `dryRun: true`** usando fixtures canónicas deterministas para que los tests y desarrollos tengan **costo CERO** en créditos de APIs de pago.
- **Brand Identity Preview Studio**: Disponible en `/desk/studio`, implementa canvas interactivo SVG de geometría sagrada, motor de contraste perceptual APCA ($L_c$) y exportación de tokens W3C DTCG (`$value`, `$type`).
- **Gabinete Clínico & Fase 0**: Disponible en `/desk` y `/fase0`, conectando el blueprint ontológico del consultante/autor con los feeds Gold de la plataforma.
- **Patrón Transactional Outbox**: Las operaciones críticas de negocio se registran en la tabla `task_outbox` de PostgreSQL 18 con UUIDv7 nativo antes de emitir eventos hacia NATS JetStream o BullMQ.
- **Bifrost como Front Door de IA**: Todo el tráfico LLM pasa por `http://bifrost:8080/v1` con enrutamiento declarativo CEL y caché semántica en Valkey 7.2.
- **Mismo Origen Web**: La landing comercial, el gabinete del consultante (`/app`), el panel del coach (`/desk`), el estudio visual (`/desk/studio`) y las rutas `/api` conviven bajo el mismo origen en el puerto 3000 de `apps/astrobranding`.

---

## 🧪 Comandos Deterministas de Verificación (Exit Code 0 Obligatorio)

Antes de cualquier entrega o push a git, ejecutar en la raíz:
```bash
bun run check        # Verificación estricta de tipos TypeScript (tsc --noEmit)
bun run check:arch   # Guardián estático de fronteras arquitectónicas (scripts/architecture-check.mjs)
./setup.sh           # Pre-vuelo de entorno y validación de import.yaml con zcp-validate
```

