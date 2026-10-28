# 🌐 PLANTILLA UNIVERSAL WEB ZEROPS (v4.4.0) — MASTER BLUEPRINT

> **Clasificación:** Blueprint Canónico Universal para Despliegues Web Soberanos en Zerops  
> **Versión:** 4.4.0 (SemVer Canónico — Worker Desacoplado WhatsApp AI Agent en Bun, Ingesta NATS <15ms, Tool Calling contra PostgreSQL 18 & Memoria Híbrida)  
> **Gobernanza:** [`Supreme Directive`](file:///var/www/.agents/rules/00-SUPREME-DIRECTIVE.md), [`Planner`](file:///var/www/.agents/skills/planner/SKILL.md) & [`Skill-Improver`](file:///var/www/.agents/skills/skill-improver/SKILL.md)  
> **Stack Base:** Astro 5 SSR (Bun 1.3.9+ / Tailwind CSS 4) + PostgreSQL 18 + Valkey 7.2 + NATS 2.12 + Object Storage S3 + Bifrost AI Gateway + EvolutionGo + Listmonk  
> **Propósito:** Guía de ejecución autónoma para que cualquier agente AGY despliegue una aplicación web, e-commerce o landing para CUALQUIER marca, producto o tema tanto en proyectos nuevos desde cero (*Greenfield*) como en adopción de repositorios preexistentes (*Brownfield*), sin ensayos, sin errores y con dependencias bloqueantes en Linear.

---

## 0.0 Protocolo Maestro de Orquestación de Infraestructura Zerops-First (Lego Desacoplado & Matriz de Skills)

> [!IMPORTANT]
> **El Plano de Control `zcp` es el Arquitecto de Plataforma:**
> Este contenedor `zcp` no compila ni ejecuta aplicaciones localmente: su misión exclusiva es **orquestar la plataforma Zerops** vía las herramientas MCP (`zerops_*`) y gobernar los contenedores LXC dedicados.
> Todo nuevo despliegue comienza obligatoriamente con el **Discovery Floor** (`zerops_discover`) para conocer el estado físico del clúster antes de proponer o mutar código.

### 1. Las Dos Rutas de Infraestructura (Adopción vs Greenfield)

```
┌────────────────────────────────────────────────────────────────────────┐
│             ORQUESTACIÓN DE INFRAESTRUCTURA ZEROPS-FIRST               │
├───────────────────────────────────┬────────────────────────────────────┤
│ RUTA A: ADOPCIÓN (SERVICIOS LIVE) │ RUTA B: GREENFIELD / MODULAR       │
├───────────────────────────────────┼────────────────────────────────────┤
│ Si `zerops_discover` detecta      │ Si el proyecto está limpio o se    │
│ servicios `adoptable`:            │ solicita aprovisionamiento:        │
│ • Ejecutar inmediatamente:        │ • Ecosistema completo: importar    │
│   zerops_workflow action="start"  │   `import.yaml` (prioridades 10-2) │
│   workflow="bootstrap"            │ • Módulo específico: importar      │
│   route="adopt"                   │   receta atómica en recipes/steps/ │
│ • Vincula servicios existentes    │ • Orquestar vía zerops_import o    │
│   sin recreación destructiva.     │   zerops_workflow route="classic"  │
└───────────────────────────────────┴────────────────────────────────────┘
```

### 2. Matriz Canónica de Orquestación: Servicio $\leftrightarrow$ Receta $\leftrightarrow$ Skill en `zerops-astro-skills`

Para que cualquier agente AGY despliegue el stack sin ensayos ni errores, cada componente de Zerops cuenta con una receta YAML canónica y una skill rectora en `zerops-astro-skills`:

| Servicio Zerops | Tipo de Servicio | Prioridad | Receta Canónica en `recipes/` | Skill Rectora en `zerops-astro-skills` |
|---|---|---|---|---|
| **`database`** | `postgresql:single@18` (profile: `oltp-hobby`) | 10 | `services/01-database.yaml` | [`postgresql`](file:///var/www/.agents/skills/postgresql/SKILL.md) (ACID, pgvector HNSW, JSON_TABLE, uuidv7) |
| **`valkey`** | `valkey:single@7.2` (profile: `hobby`) | 10 | `services/02-valkey.yaml` | [`valkey`](file:///var/www/.agents/skills/valkey/SKILL.md) (Locks atómicos, sliding rate limit, caché) |
| **`nats`** | `nats:single@2.12` | 10 | `services/03-nats.yaml` | [`nats`](file:///var/www/.agents/skills/nats/SKILL.md) (JetStream, RPC <0.3ms, Nats-Msg-Id) |
| **`localstorage`** | `local-storage:single@1` | 10 | `services/06-localstorage.yaml` | [`local-storage`](file:///var/www/.agents/skills/local-storage/SKILL.md) (POSIX kernel, run.volume, SQLite WAL) |
| **`objectstorage`** | `object-storage` (S3 MinIO) | 10 | `services/04-objectstorage.yaml` | [`object-storage`](file:///var/www/.agents/skills/object-storage/SKILL.md) (Assets >500KB, Pre-Signed URLs) |
| **`freellmapi`** | `ubuntu/nodejs@24` | 8 | `steps/01-freellmapi.yaml` | [`freellmapi`](file:///var/www/.agents/skills/freellmapi/SKILL.md) (Free proxy multi-provider, port 3001) |
| **`bifrost`** | `alpine/go@1.22` | 6 | `steps/02-bifrost-postgres.yaml` | [`bifrost`](file:///var/www/.agents/skills/bifrost/SKILL.md) (AI Gateway, Virtual Keys, CEL routing, port 8080) |
| **`evolution`** | `alpine/go@1.22` | 6 | `steps/04-evolution.yaml` | [`whatsapp-engine`](file:///var/www/.agents/skills/whatsapp-engine/SKILL.md) (whatsmeow Go, port 8085, takeover 2h) |
| **`listmonk`** | `alpine/go@1.22` | 5 | `steps/05-listmonk.yaml` | [`listmonk`](file:///var/www/.agents/skills/listmonk/SKILL.md) / [`email-marketing`](file:///var/www/.agents/skills/email-marketing/SKILL.md) (Newsletter, port 9000) |
| **`hermes`** | `ubuntu/python@3.12` | 4 | `services/10-hermes.yaml` | [`hermes-agent`](file:///var/www/.agents/skills/hermes-agent/SKILL.md) (Nous Hermes Co-Pilot, Telegram Gateway) |
| **`whatsappbot`** | `ubuntu/bun@1.3` | 3 | `steps/07-whatsapp-bot.yaml` | [`whatsapp-engine`](file:///var/www/.agents/skills/whatsapp-engine/SKILL.md) (Worker NATS JetStream, Tool Calling, memoria híbrida, port 3005) |
| **`webdev / webprod`**| `ubuntu/bun@1.3` | 2 | `steps/06-astro-web.yaml` | [`astro-web`](file:///var/www/.agents/skills/astro-web/SKILL.md) / [`bun`](file:///var/www/.agents/skills/bun/SKILL.md) / [`frnt`](file:///var/www/.agents/skills/frnt/SKILL.md) (SSR, port 3000) |
| **Meta-Orquestador** | `zcp@1` | 1 | Chasis raíz | [`zcp`](file:///var/www/.agents/skills/zcp/SKILL.md) / [`bknd`](file:///var/www/.agents/skills/bknd/SKILL.md) (Control plane, 22 MCP tools) |

### 3. Arquitectura Lego Desacoplada (Zero-Hardcoding de Dependencias)
- **Aprovisionamiento Frugal y Modular:** Los servicios son 100% independientes y aditivos. Si el usuario solicita *"despliega una landing o e-commerce"*, el agente aprovisiona únicamente `database`, `valkey`, `localstorage` y `webdev/webprod`, sin obligar a levantar el stack de IA (`bifrost`/`hermes`) si la marca no lo requiere.
- **Service Discovery Dinámico:** Los microservicios se comunican en caliente a través de la red privada VXLAN de Zerops por DNS interno (`http://bifrost:8080`, `http://evolution:8085`, `http://freellmapi:3001`, `http://listmonk:9000`). El agente inspecciona el entorno en vivo y solo cablea lo existente.
- **Invariantes de Autoescalado Elástico:**
  * Modo de CPU: `cpuMode: SHARED` obligatorio en todos los manifiestos de arranque (cero `DEDICATED` innecesario).
  * Colchón Dual Dinámico: `minFreeRamGB: 0.25` y `minFreeRamPercent: 10` para prevenir OOM sin inflar costos.
  * Omitir techos fijos (`maxCpu`, `maxRam`) en manifiestos salvo circuit breakers específicos.

---

## 0. Protocolo de Activación por Lenguaje Natural & Discriminación (Greenfield vs Brownfield)

> [!IMPORTANT]
> **Contrato Soberano de Lenguaje Natural (Cero Comandos para el Humano):**
> El usuario NUNCA debe memorizar comandos de terminal, URLs de repositorios ni códigos de tarea (`BAI-*`). El usuario activa el flujo hablando en lenguaje natural (ej: *"AGY, despliega la web de [Marca] desde cero"* o *"AGY, adopta el repositorio existente en [Ruta] y rediséñalo"*).
> **El agente AGY asume la ejecución autónoma de punta a punta:** crea el proyecto y las issues en Linear, ejecuta los scripts de scaffolding, compila los tokens y orquesta los despliegues sin fricción técnica.

Antes de iniciar cualquier acción sobre el código o la infraestructura, el agente evalúa el estado para clasificar la ruta operativa de forma autónoma:

```
┌────────────────────────────────────────────────────────────────────────┐
│             PUERTA DE ENLACE INICIAL: DISCOVERY & CLASIFICACIÓN        │
├───────────────────────────────────┬────────────────────────────────────┤
│ RUTA A: GREENFIELD (DESDE CERO)   │ RUTA B: BROWNFIELD (PREEXISTENTE)  │
├───────────────────────────────────┼────────────────────────────────────┤
│ 1. Clonar chasis upstream         │ 1. Auditoría visual: impeccable    │
│    (zerops-astrobranding)         │ 2. Extracción de tokens: brandbook │
│ 2. Desacoplar repo cliente        │ 3. Detección de fallos: rdd-*      │
│ 3. Configurar remote upstream     │ 4. Adaptación a Bun 1.3 & Astro 5  │
│ 4. Ingestión brandbook inicial    │ 5. Normalización zerops.yaml       │
└───────────────────────────────────┴────────────────────────────────────┘
```

### Puerta Condicional A: Proyecto Greenfield (Desde Cero)
1. **Adopción de Chasis Upstream:**
   ```bash
   git clone https://github.com/usuario/zerops-astrobranding.git /var/www/<hostname>
   cd /var/www/<hostname>
   git remote rename origin upstream
   git remote add origin https://github.com/usuario/<repo-cliente>.git
   ```
2. **Ingestión de Identidad:** Cargar `brandbook.json` en estándar W3C DTCG v6.3.0 y compilar variables `@theme` en Tailwind CSS 4.
3. **Aprovisionamiento Linear:** Ejecutar `node --experimental-strip-types scripts/linear-scaffold.ts <APP_IDENTITY> "<PROJECT_NAME>"`.


### 4. Erradicación de Errores Sistémicos (Lecciones Aprendidas SSoT)
- **Secuestro del Puerto 3000 (Astro/Vite):** Nunca confíes ciegamente en `bun run dev`. Procesos zombies de NodeJS (`entry.mjs`) suelen secuestrar el puerto 3000, forzando a Astro a levantar en el 3001 y rompiendo el proxy inverso de Zerops (`webdev-278-3000`). **Regla obligatoria:** Antes de iniciar el dev server, ejecuta `fuser -k 3000/tcp || pkill node` y levanta con `bun run dev --host 0.0.0.0 --port 3000`.
- **Tailwind 4 + Astro 5:** Para que los estilos se generen correctamente en SSR, es obligatorio usar el plugin de Vite en `astro.config.mjs` (`import tailwindcss from "@tailwindcss/vite"; vite: { plugins: [tailwindcss()] }`) y cargar `@import "tailwindcss";` en el archivo CSS global importado por `Layout.astro`.

### 5. Invariantes Soberanos de WhatsApp Bot & Bifrost LLM Gateway
- **Desacople Físico en Bun LXC & Early Webhook ACK (<15ms)**: NUNCA ejecutar el bot en Astro SSR ni dentro del plano de control `zcp`. El webhook de Evolution API responde inmediatamente `200 OK` (<15ms) antes de cualquier inferencia para evitar tormentas de reintentos y mensajes duplicados. El procesamiento asíncrono reside en un worker agéntico dedicado en Ubuntu Bun 1.3 (`whatsappbot`, puerto 3005) consumiendo `http://bifrost:8080` vía la red privada de Zerops.
- **Guardia de Descarte de Webhooks Antiguos / Replay Storm**: En reinicios de contenedor o reconexiones de Evolution API, Evolution vuelca su buffer de mensajes pendientes o viejos. El bot DEBE extraer el timestamp del mensaje (`extractMessageEpochMs`) y validar la antigüedad: si `(Date.now() - messageEpochMs) / 1000 > 120s`, el webhook se descarta en el acto como `ignored_stale_message`, erradicando por completo el storm de respuestas robóticas a conversaciones cerradas.
- **Lock Atómico de Deduplicación de 24 Horas**: Todo mensaje entrante adquiere un lock atómico distribuido en Valkey (`SET lock:wa:${messageId} 1 NX EX 86400`). El TTL de 24 horas previene reprocesamiento ante reintentos de red o reconexiones dentro del día.
- **Monotonicidad y Soberanía de `#stop`**: Comandos `#stop`, `#off`, `#silencio`, `#desactivar` establecen silencio permanente (10 años, `EX 315360000`). Los mensajes manuales subsiguientes enviados por el operador humano en ese chat DEBEN verificar el estado activo y **preservar el `#stop` de por vida**, sin degradarlo jamás a la pausa temporal por defecto (2 horas). El bot solo reanuda su atención automática ante el comando explícito `#bot`. Comandos de silencio temporal `#mute` pausan por 24 horas (86400s).
- **Persistencia SSoT en PostgreSQL & Re-hidratación Automática de Valkey**: El estado de takeover (`bot_status`: `'stopped'` | `'muted'` | `'active'`, `bot_stopped_at`, `bot_mute_until`) se persiste atómicamente en `leads.metadata` (JSONB) en PostgreSQL SSoT. Ante cualquier reinicio de contenedor o cache-miss en Valkey, la consulta a `isHumanTakeover` consulta PostgreSQL y **re-hidrata en caliente la memoria RAM de Valkey**, garantizando tolerancia absoluta a reinicios fríos.
- **Resolución Multi-Identificador en Intervención Humana (JID vs LID)**: Cuando el operador humano escribe desde WhatsApp Web o celular (`fromMe: true`), el webhook (Evolution API / whatsmeow) DEBE bloquear el identificador remoto de la conversación (`key.remoteJid` / `info.Chat`), NUNCA el LID del emisor (`info.Sender`). Se debe guardar y consultar el takeover simétricamente para todas las representaciones del cliente (teléfono `@s.whatsapp.net` y `@lid`).
- **CoHaLo Positivo & Detección Dinámica Lego (Cero Prohibiciones Negativas)**: Erradicar del código y prompts del bot avisos negativos o defensivos ("NO AFILIADOS", "NO MEMBRESIAS", "NO PAGOS"). Todo funciona en torno a la verdad viva de PostgreSQL: si la tabla `afiliados` o el campo de membresía no existe en el proyecto limpio, el bot asume que no existe y no lo ofrece.
- **Dual-Tier Predictive Intent Routing (Anti-Cascade)**: Erradica el failover reactivo por 429. Clasifica la intención a priori: intenciones críticas (ventas, tickets, reservas, pagos, catálogo, tool calling) envían la cabecera `x-tier: production` a Bifrost para acceder de inmediato al tier Pro (DeepSeek V4). Consultas informativas o FAQs rutinarias usan FreeLLMAPI con timeout estricto de 2.5s y Circuit Breaker con cooldown de 120s.
- **Pacing Humano Simulado (1.5s–3.0s)**: Antes de enviar la respuesta final, emitir presencia `composing` y aplicar un retardo simulado entre 1.5s y 3.0s según longitud del texto, evitando baneos de Meta por respuestas instantáneas robóticas.
- **Frontera Sagrada del Plano de Control `zcp` (Efímero)**: El contenedor `zcp` es exclusivamente un entorno de edición, auditoría y despliegue; permanece apagado en producción. Los servicios productivos (Bifrost, Evolution, Whatsappbot, PostgreSQL, Valkey) corren 24/7 en sus propios contenedores LXC. `bifrost-cli` en `zcp` es un arnés interactivo TUI de desarrollo, nunca un proxy en la ruta crítica de producción.
- **Preservación Contextual de Mensajes Citados**: Extraer siempre `contextInfo.quotedMessage` e inyectarlo en el prompt del usuario (`[Mensaje citado: "..."]\n<texto>`) para que el LLM comprenda preguntas de seguimiento contextuales sin perder el hilo.
- **Soporte y Transcripción de Notas de Voz**: Extraer `audioMessage`, recuperar audio base64 o descargarlo vía `/message/downloadmedia` de Evolution API y transcribirlo mediante Bifrost `/v1/audio/transcriptions` (OpenAI Whisper upstream / FreeLLMAPI Groq). En caso de no poder decodificarse, responder con calidez de marca en lugar de descartar el mensaje en silencio.
- **Grounding Irrefutable de Rutas Web (Zero 404s)**: El System Prompt del bot debe fundamentarse en el catálogo de rutas verificadas del proyecto Astro. El LLM tiene estrictamente prohibido inventar o sintetizar URLs fuera de la lista blanca provista.
- **Blindaje Cultural Positivo y Voz Anti-Slop**: Evitar términos polisémicos con connotaciones locales distorsionadas (ej. 'anfitriona' en Bogotá). Definir la ontología del equipo con roles claros (facilitadores éticos, artistas, curadores) sin prompting negativo torpe. Mantener tuteo cálido ("tú") y respuestas concisas en 1 o 2 párrafos sin viñetas de soporte técnico innecesarias.

### Puerta Condicional B: Proyecto Brownfield (Código Preexistente)
1. **Auditoría de Interfaz (Anti-Slop):** Ejecutar `impeccable audit` o `taste-skill` para identificar anti-patrones, gradientes clichés o inconsistencias tipográficas.
2. **Extracción y Normalización de Tokens:** Extraer paletas y tipografías existentes hacia `/brand/brandbook.json` mediante `impeccable extract`, convirtiendo colores hexadecimales al espacio `oklch()`.
3. **Contención de Defectos Previos (`rdd-defect-workflow`):** Si el repositorio presenta bugs abiertos, exigir un recibo reproducible en `main` antes de cualquier refactor. Presupuesto estricto $\le 400$ líneas de cambio.
4. **Armonización de Runtime Zerops:**
   - Asegurar que `zerops.yaml` utilice el runtime nativo `ubuntu/bun@1.3.9` para prevenir incompatibilidades con bibliotecas nativas compiladas con musl libc.
   - Configurar el remote upstream: `git remote add upstream https://github.com/usuario/zerops-astrobranding.git` para recibir mejoras del chasis central.

---

## 1. Declaración de Identidad Agnóstica & Variables Soberanas

Todo nuevo despliegue adopta su identidad dinámicamente mediante variables de entorno en Zerops (`zerops_env`), erradicando cualquier valor quemado en código:

| Variable | Descripción / Formato | Ejemplo en Producción |
|---|---|---|
| `PROJECT_NAME` | Identidad humana de la marca | `"Acme Platform"` / `"Lumina Shoes"` |
| `APP_IDENTITY` | Slug normalizado en minúsculas (sin espacios) | `"acme"` / `"luminashoes"` |
| `CLIENT_DOMAIN` | Dominio público principal | `"acme.com"` / `"tienda.com"` |
| `PUBLIC_BRAND_NAME` | Nombre visible para el cliente | `"Acme"` |
| `PUBLIC_CONTACT_EMAIL` | Correo oficial de atención | `"contacto@acme.com"` |
| `PUBLIC_WHATSAPP_PHONE`| Teléfono para el canal WhatsApp (E.164) | `"+573001234567"` |

> [!NOTE]
> **Gestión Soberana de Secretos:** Toda variable y secreto se inyecta a través de `zerops_env` y se referencia mediante `${VAR}` en manifiestos y `process.env.VAR` en runtime, preservando la raíz del contenedor limpia y sin dependencias de archivos locales.

---

## 2. Taxonomía Soberana de Almacenamiento (Local Storage vs Object Storage)

Cualquier AGY debe clasificar y persistir los datos según la necesidad real y fase de madurez del proyecto, **sin empaquetar servicios innecesarios por defecto**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TAXONOMÍA DE ALMACENAMIENTO ZEROPS                   │
├─────────────────┬─────────────────┬──────────────────┬─────────────────┤
│ 1. GDRIVE SSoT  │ 2. LOCALSTORAGE │ 3. OBJECTSTORAGE │ 4. POSTGRESQL   │
│ (Capa Fría)     │ (Bloques POSIX) │ (S3 MinIO - Opt) │ (Capa ACID Rel) │
├─────────────────┼─────────────────┼──────────────────┼─────────────────┤
│ • Repositorios  │ • Fotos Catálogo│ • Escalado Multi-│ • Tablas leads  │
│ • brandbook.json│ • Medios Marca  │   host horizontal│ • Tablas orders │
│ • Esquemas SQL  │ • SQLite Engram │ • Cloudflare CDN │ • DIAN CUFE / ID│
│ • Backups bak/  │ • FreeLLMAPI db │ • Blobs >100GB   │ • Bifrost logs  │
│ • Manifiestos   │ • Brandbook SSoT│ • S3 forcePath   │ • Listmonk PG   │
└─────────────────┴─────────────────┴──────────────────┴─────────────────┘
```

1. **Google Drive SSoT (`/var/www/baiosfera/`):** Capa Fría indestructible. Espejo permanente de código fuente, configuraciones maestras y manifiestos de diseño.
2. **`localstorage` (`/mnt/localstorage/`):** Capa Primaria de Persistencia POSIX (<0.1ms latencia NVMe).
   - **Uso Estándar Starter (Fase 1):** Es el **almacenamiento por defecto** para e-commerce ligero y marcas. Las fotos de productos (`/mnt/localstorage/${PROJECT_NAME}/media/productos/`), bases de datos SQLite locales (`engram`, `freellmapi`) y el Brandbook SSoT (`/mnt/localstorage/${PROJECT_NAME}/dev/`) residen aquí.
   - **Regla de Prioridad de Marca en Local Storage (Sin Cárcel Obligatoria):** Cada entorno Zerops (`$PROJECT_NAME`) aísla su `localstorage` prioritariamente para su marca activa (`/mnt/localstorage/${PROJECT_NAME}/dev/`) para evitar colisiones de personalidad y saturación de disco local. Google Drive SSoT (`/var/www/baiosfera/PROYECTOS/`) es el repositorio universal donde conviven todas las marcas. El operador puede ejecutar `zcp-sync <MARCA>` libremente sin restricciones ni bloqueos cuando requiera sincronizar ad-hoc otras marcas para pruebas o diagnósticos.
   - **Restricción de Infraestructura (Ley de Co-Location):** Todos los contenedores que montan el mismo `localstorage` se ejecutan forzosamente en el mismo nodo físico de Zerops.
3. **`objectstorage` (S3 MinIO - Estrictamente Opcional / On-Demand):**
   - **¿Cuándo SÍ se aprovisiona?**
     a) **Escalado Horizontal Masivo:** Cuando el frontend (`web`) requiere autoescalar a N réplicas distribuidas en múltiples servidores físicos (rompiendo la restricción de Co-Location).
     b) **Offloading Directo a CDN:** Cuando se desea servir gigabytes de fotos directamente desde Cloudflare Edge sin consumir ancho de banda ni CPU del contenedor web.
     c) **Expansión a ERPNext / Frappe CRM:** Cuando el archivo digital tributario (XMLs CUFE, PDFs DIAN y adjuntos de clientes) amerita archivado masivo desacoplado mediante el plugin `frappe_s3_attachment`.
   - **¿Cuándo NO se aprovisiona?** En fases iniciales, tiendas en arranque o plataformas transaccionales estándar. Si el proyecto no lo usa activamente, **no se aprovisiona** para evitar costos inoficiosos.
4. **`postgresql` (PostgreSQL 18):** Capa Relacional Transaccional ACID. Tablas de negocio (`clients`, `orders`, `leads`, `outbox`), facturación electrónica (`dian_cufe`), esquemas de Listmonk y EvolutionGo.

### Puente de Evolución Sin Fricción: De PostgreSQL Ligero a Frappe CRM & ERPNext
- **Fase Inicial (Lean):** El e-commerce gestiona pedidos, pasarelas de pago y datos de facturación en PostgreSQL 18 (`orders` y `offerings`). Los assets de producto se sirven desde `localstorage`. Cero overhead.
- **Fase de Maduración (ERPNext / Frappe):** Cuando el negocio activa ERPNext y Frappe CRM:
  * **Conexión Desacoplada & Outbox Transaccional:** Toda sincronización hacia Frappe DocTypes (`Sales Order`, `Sales Invoice`, `Customer`, `CRM Lead`) se encola atómicamente en `task_outbox` (`type: "frappe_sync"`).
  * **Resiliencia Fail-Safe Absoluta:** Cero llamadas HTTP síncronas bloqueantes en los endpoints de checkout o webhooks de pasarela. Si la instancia de Frappe está en hibernación, suspendida o responde `403/502`, la tienda sigue vendiendo con normalidad (Cero Fallas en Checkout). El worker `drainTaskOutbox` procesa y reintenta con retroceso exponencial (*exponential backoff*).
  * **Mapeo Canónico de 6 Arquetipos de Oferta:** `@astrobranding/contracts` provee la función canónica `getFrappeMappingForArchetype()` para traducir los 6 arquetipos de oferta a los DocTypes respectivos de Frappe, manteniendo las etiquetas visibles en español para el cliente.
  * **Archivos y Facturas:** Si Frappe corre en Frappe Cloud o en contenedor dedicado en Zerops, los comprobantes PDF/XML se gestionan vía API REST o, si el volumen lo exige, se aprovisiona `recipes/services/04-objectstorage.yaml` de forma aditiva para almacenar los adjuntos pesados en MinIO S3 sin alterar la lógica del frontend.

---

## 3. Hub Neuronal Central: Maxim AI Bifrost Gateway (:8080)

Bifrost es la puerta de enlace de IA obligatoria para todos los servicios (Astro-Web, EvolutionGo, Hermes, Scripts ZCP). Ningún cliente habla con proveedores LLM directamente.

### Virtual Keys Agnósticas por Rol Funcional
Bifrost expone 5 Virtual Keys desacopladas de nombres de clientes:
1. `vk-web-client`: Autenticación desde Astro 5 SSR para generación de copys, resúmenes y búsqueda semántica.
2. `vk-bot-whatsapp`: Autenticación para EvolutionGo en atención conversacional.
3. `vk-agent-orchestrator`: Autenticación para agentes autónomos (Hermes-Agent / subagentes).
4. `vk-admin-operator`: Autenticación para el operador en ZCP / AGY / CLI.
5. `vk-system-core`: Autenticación para workers en segundo plano y outbox drain.

> [!IMPORTANT]
> **Autenticación Obligatoria:** Toda llamada a `http://bifrost:8080/v1` DEBE incluir la cabecera `Authorization: Bearer <vk>` (o `x-bf-vk`). Llamadas sin Virtual Key son rechazadas.

### Características de Operación & Enrutamiento Híbrido CEL:
- **Endpoint Drop-In:** `http://bifrost:8080/v1` (compatible 100% con SDK de OpenAI).
- **Zero-Wait 429 & Dual-Tier Enrutamiento Predictivo:**
  * **Free Tier (`freellmapi:3001` / Qwen 2.5 72B / Llama 3.3 70B):** Atiende consultas fácticas, FAQs, horarios, dirección de sedes, eventos vigentes y conversación general (<1s latencia, $0 costo).
  * **Pro Tier (DeepSeek V3 / R1):** Activado directamente (sin esperar timeouts 429) cuando la intención es transaccional (generar enlaces de pago dLocal Go/Wompi, comisiones de afiliados o reclamos graves). Se invoca mediante `x-routing-tier: pro` o `model: "deepseek/deepseek-chat"`.
- **Semantic Cache:** Caché vectorial en memoria; consultas repetidas responden en **<2ms con costo $0**. Key dinámica: `${APP_IDENTITY}-cache`. Motor de vector store obligatorio: `chromem` (Go puro embebido).
- **Persistencia SSoT:** Bifrost almacena su configuración y logs en PostgreSQL 18 (`config_store` y `logs_store` tipo `postgres`). Prohibido usar SQLite o Valkey para el vector store (Valkey carece de `RediSearch FT.*`).

---

## 4. Gated Workflow de Skills & Anti-Slop Craft Obligatorio

Todo producto construido bajo esta plantilla debe orquestar el ecosistema de 141 skills divididas en 4 dimensiones operativas:

### A. Arte, Vibe-Craft & Experiencia Sensorial
- **`fontgen`**: Dirección tipográfica con jerarquías Display + Grotesk en 6 capas funcionales.
- **`kinetic`**: Microinteracciones a 60fps con GSAP, curvas `cubic-bezier(0.16, 1, 0.3, 1)` y SFX procedurales.
- **`chroma`**: Modelado matemático de paletas en **OKLCH**, contraste APCA Lc >= 82 y WCAG 2.2 AAA (>= 7:1).
- **`taste-skill` e `impeccable`**: Calibración estricta de los 3 Diales:
  * `DESIGN_VARIANCE: 8` — Asimetría intencional y grillas editoriales dinámicas.
  * `MOTION_INTENSITY: 6` — Entradas físicas suaves con aceleración natural.
  * `VISUAL_DENSITY: 4` — Espaciado amplio y respiro visual de alta gama.

### B. Frontend Reactivo & Arquitectura de Componentes
- **`tailwind-4`**: Tokens transpilados directamente a `@theme` CSS-first sin sobrecarga de runtime.
- **`react-19`**: Islas interactivas compiladas con el **React Compiler** nativo (cero `useMemo`/`useCallback` artesanales).
- **`zustand-5`**: Estado global del cliente seguro con persistencia en `localStorage` e hidratación anti-flicker.
- **`zod-4`**: Validación de esquemas estricta en las Astro Actions.

### C. Conversión, Funnels & Transaccional
- **`ad-telemetry`**: Orquestador universal multi-red de publicidad y telemetría (Meta CAPI, Google Ads Enhanced Conversions, TikTok Events API, Consent Mode v2, Atribución 1st-party cookie 90 días, Schema SAB vs Storefront y Outbox transaccional).
- **`checkout-funnels`**: Funnels de alta conversión con 1-Click Upsells y Meta CAPI.
- **`payment-gateways`**: Firmas SHA-256 e idempotencia en Valkey (60s lock).
- **`growth-engine`**: Neurocopywriting basado en la Oferta Hormozi y StoryBrand.
- **`email-marketing`**: React Email 3.0 compilado inline (<85KB) con entregabilidad DMARC/DKIM.

### D. Borde, Seguridad & Plataforma
- **`cloudflare`**: Edge CDN, SSL Full Strict y Turnstile anti-bot sin captchas invasivos.
- **`automation-engine`**: Colas de eventos desacopladas con BullMQ y NATS JetStream (:4222).
- **`seo-aeo-geo`**: Schema.org JSON-LD (`Product`/`ProfessionalService`), `/llms.txt` y OpenGraph <300KB.
- **`rdd-defect-workflow`**: Contención forense de bugs con prueba física en `main` ($\le 400$ líneas).

---

## 5. Protocolo de Linear Automatizado (`linear-scaffold.ts`) & Malla Lego Desacoplada

La creación y seguimiento de tareas se rige por el estándar **Project-as-Code** mediante el manifiesto declarativo [`linear_template.json`](file:///var/www/artifacts/templates/linear_template.json) y el script ejecutable `linear-scaffold.ts`:

```bash
# Simulación determinista previa (sin mutar Linear)
node --experimental-strip-types scripts/linear-scaffold.ts <APP_IDENTITY> "<PROJECT_NAME>" --dry-run --profile <minimal|content|ecommerce|full-mesh>

# Aprovisionamiento real con gating de dependencias en Linear
node --experimental-strip-types scripts/linear-scaffold.ts <APP_IDENTITY> "<PROJECT_NAME>" --profile <perfil>
```

> [!IMPORTANT]
> **Mandato de Trazabilidad Viva en Linear (Anti-Checklist Theater & Blindaje de Contexto):**
> Las issues creadas en Linear (`BAI-*`) NO son un registro pasivo post-facto; son el **motor de ejecución y guía obligatoria del agente**:
> 1. **Inicio de Hito:** Transicionar el estado inmediatamente vía `linear-cli update-status <ID> "In Progress"`.
> 2. **Ejecución y DoD:** Toda acción de código se guía por los criterios de la Definition of Done de la issue en Linear para no perder contexto ni mutilar funcionalidades.
> 3. **Cierre con Sensor Físico:** Al terminar, es OBLIGATORIO registrar comentario con la prueba física (`linear-cli comment <ID> "✅ Atestación física exit 0: [detalles]"`) y transicionar a `linear-cli update-status <ID> "Done"`.
> 4. **Respeto a Bloqueos:** Prohibido tocar o dar por iniciada una tarea bloqueada (`gate:blocked`) hasta que su dependencia directa esté en `Done`.
> 5. **Soberanía de Linear-CLI y Direct GraphQL API:** Linear opera exclusivamente mediante el binario físico `/usr/local/bin/linear-cli` o consumo directo de la API GraphQL (`https://api.linear.app/graphql`), garantizando respuestas deterministas en <200ms con cero latencia y preservación absoluta de tokens de contexto.

### Taxonomía de los 7 Hitos Lego (`BAI-0` a `BAI-6`)

Los hitos se clasifican estrictamente en **CORE** (invariantes arquitectónicos obligatorios) y **OPT-IN** (módulos activados exclusivamente según la necesidad del proyecto):

| Hito | Tipo | Nombre / Alcance | Bloqueado Por | Salida / DoD |
|---|---|---|---|---|
| **`BAI-0`** | `[CORE]` | **Scope, Topología Lego & Clasificación** | *(Ninguno)* | Greenfield vs Brownfield resuelto, perfil Lego seleccionado, servicios base activos en Zerops. |
| **`BAI-1`** | `[CORE]` | **Chasis Astro 5 SSR, Tokens & GitOps** | `BAI-0` | Repositorio downstream enlazado a upstream, tokens W3C DTCG transpilados a Tailwind 4 `@theme`, build limpio en Bun 1.3. |
| **`BAI-2`** | `[OPT-IN]` | **Contratos de Datos, Persistencia PostgreSQL 18 & Mesh API** | `BAI-1` | Modelado relacional en PostgreSQL 18, upsert defensivo anti-500, normalización E.164, endpoints `/api/*` probados con Zod. Cero mocks antes de UI. |
| **`BAI-3`** | `[CORE]` | **Landings de Alto Impacto, Server Islands & Anti-Slop** | `BAI-2` *(o `BAI-1` en minimal)* | Server Islands (`server:defer`), diales calibrados (Variance 8, Motion 6, Density 4), microinteracciones GSAP 60fps, CLS = 0. |
| **`BAI-4`** | `[OPT-IN]` | **Motor Transaccional, Checkout Funnels & Pasarelas** | `BAI-3` | Funnels con debounce anti-doble clic, firmas criptográficas SHA-256 (Wompi/ePayco/Stripe), idempotencia en Valkey (60s lock). |
| **`BAI-5`** | `[OPT-IN]` | **Automatización Omnicanal & Asistentes de IA** | `BAI-3` | WhatsApp ágil con EvolutionGo (:8085), Email documental Listmonk (<85KB), Virtual Keys en Bifrost AI Gateway (:8080). |
| **`BAI-6`** | `[CORE]` | **Atestación Física Multi-Superficie, SEO-AEO-GEO & Go-Live** | `BAI-3` / `BAI-4` / `BAI-5` | Habilitar Ingress (`zerops_subdomain action="enable"`), Atestación Pública (HTTP 200 en URL externa), Playwright E2E exit code 0, Schema.org, OpenGraph <300KB. |

### Modelo Lego Desacoplado por Slots de Capacidad (Soberanía Frugal)

> [!WARNING]
> **Deconstrucción de Perfiles Rígidos y Pipelines Waterfall:**
> Los perfiles predefinidos (`minimal`, `content`, `ecommerce`, `full-mesh`) son **arquetipos referenciales de conveniencia**, NO verdades absolutas ni camisas de fuerza.
> En Zerops, imponer stacks completos artificiales genera desperdicio de recursos y fragilidad operativa.
> El estándar real es el **Aprovisionamiento Frugal por Slots de Capacidad**: el agente evalúa la intención de negocio y cablea exclusivamente los bloques funcionales que el caso de uso requiere hoy.

#### Matriz de Slots de Capacidad Aditivos:
1. **Slot Frontend (Invariante):** Astro 5 SSR en Bun 1.3 con `@astrojs/node` en modo standalone (`os: ubuntu`, `HOST: 0.0.0.0`, puerto 3000). Despliega `dist/`, `package.json` y `node_modules` (evitar `bun build --target bun` monolítico que rompe addons nativos como `sharp`).
2. **Slot Persistencia Relacional (Aditivo):** PostgreSQL 18 (`oltp-hobby`). Solo si el proyecto maneja estado relacional (leads, usuarios, pedidos).
3. **Slot Caché & Idempotencia (Aditivo):** Valkey 7.2 (`hobby`). Para locks atómicos de pasarelas, sesiones y rate-limiting.
4. **Slot Eventos & Mensajería (Aditivo):** NATS 2.12 JetStream (`<0.3ms P99`). Para arquitecturas orientadas a eventos y workers de fondo.
5. **Slot Almacenamiento S3 (Aditivo):** Object Storage (MinIO S3). Para media, comprobantes y assets pesados (>500KB).
6. **Slot Automatización Omnicanal & IA (Aditivo):** Maxim AI Bifrost (:8080), EvolutionGo WhatsApp (:8085) o Listmonk (:9000). Solo bajo demanda explícita.

#### Invariantes Físicos de Hardware y Red Zerops (Octubre 2026):
- **Base OS Ubuntu:** Build y run DEBEN usar `os: ubuntu`. Vite/Rollup y los bindings C nativos fallan en Alpine/musl.
- **Red Privada VXLAN:** Llamadas inter-servicio SIEMPRE por `http://` (nunca `https://`) resolviendo el hostname directo (`http://db:5432`, `http://bifrost:8080`).
- **Autoscaling Elástico:** `cpuMode: SHARED`, `minFreeRamGB: 0.25`, `minFreeRamPercent: 10`. Omitir techos artificiales (`maxRam`/`maxCpu`) que provocan caídas por OOMKilled; Zerops factura por consumo real por segundo.
- **Pirámide de 4 Sensores Físicos (Anti-Checklist Theater):**
  * Capa 0: `bun x tsc --noEmit` (Exit Code 0).
  * Capa 1: `bun run build` dentro del contenedor con artefactos generados (Exit Code 0).
  * Capa 2: `bun test` de comportamiento (Exit Code 0).
  * Capa 3: `curl -Ifs http://0.0.0.0:3000/health` (HTTP 200 OK) y `zerops_verify` pass.

### Invariante de Persistencia Previa (`BAI-2` antes de `BAI-3`)
En proyectos que requieren persistencia relacional, los contratos de datos (`BAI-2`) **preceden obligatoriamente** a la construcción de las interfaces de usuario (`BAI-3`). Esto erradica el desarrollo contra mocks volátiles y asegura que cada componente visual se conecte desde el primer día a esquemas tipados y APIs vivas.

### Extensibilidad Soberana para Nuevos Runtimes
Si un proyecto requiere runtimes especializados (ej: microservicios Python con FastAPI, búsqueda vectorial con Qdrant, o CMS con Directus), estos se agregan como recetas complementarias en `recipes/steps/` sin romper el linaje de los hitos web. El agente opera con service discovery dinámico en Zerops (`zerops_discover`), cableando únicamente los servicios presentes.

---

## 6. GitOps Delivery Canónico & Linaje Upstream GitOps

- **Linaje Upstream Soberano:** El proyecto del cliente mantiene `upstream` hacia `zerops-astrobranding` para recibir actualizaciones de chasis, plantillas y tooling.
- **Desarrollo en Zerops:** Todo el trabajo iterativo ocurre en el contenedor efímero `webdev` de Zerops (`/var/www/{hostname}` con hot-reload y subdominios).
- **Producción Inmutable:** Los despliegues a producción se realizan exclusivamente a través de GitHub Actions (`zeropsio/actions@v1.0.2`) al hacer push a la rama `main`, conectado a Cloudflare con SSL Full Strict.
- **Staging Desacoplado y Opcional:** La receta base `06-astro-web.yaml` despliega únicamente el servicio de producción. El entorno staging (`06b-astro-web-staging.yaml`) es estrictamente opt-in para proyectos con QA formal.

---

## 7. Verificación Física & Sensores de Calidad (Exit Code 0)

> [!CAUTION]
> **Miopía de Orquestador (Checklist Theater):** Hacer `curl http://nombre-servicio:3000` desde el contenedor ZCP NO prueba que la app sea accesible por el usuario. Es obligatorio probar el *Ingress Público*.

Antes de dar por entregado cualquier despliegue bajo esta plantilla, el agente debe ejecutar físicamente y comprobar el código de salida 0 de:
1. `astro-web-validate.sh` — Verificación de AST, Server Islands y tokens de diseño.
2. `skills-suite-validate` — Certificación del catálogo completo de skills.
3. `ssot-parity-check` — Atestación de paridad sin drift entre el contenedor ZCP y Google Drive SSoT.
4. **Verificación de Ingress Público:** Habilitar el subdominio (`zerops_subdomain action="enable"`) y realizar `curl -s -o /dev/null -w "%{http_code}" https://<subdominio-publico>` verificando un HTTP 200 OK desde el exterior. El ping interno al puerto (ej: `:3000`) es insuficiente.

---

## 8. Resiliencia Relacional & Upsert Defensivo en PostgreSQL 18

En aplicaciones con captación de leads y pasarelas de pago, los usuarios reingresan frecuentemente, alternan entre correo corporativo y personal, o ingresan números de teléfono con o sin prefijo de país (`310...` $\leftrightarrow$ `+57310...` $\leftrightarrow$ `57310...`).

### Regla de Oro: Cero Errores 500 en Pasarela por Restricciones de BD
Un cliente que intenta pagar jamás debe recibir un error `500 Internal Server Error` provocado por violaciones de clave única (`duplicate key value violates unique constraint "leads_email_key"` o `"leads_whatsapp_key"`).

### Patrón Canónico de Normalización y Upsert
1. **Generación de Variantes Telefónicas:**
   ```typescript
   export function getPhoneVariants(phone?: string | null): string[] {
     if (!phone) return [];
     const digits = phone.replace(/\D/g, "");
     if (!digits) return [];
     const variants = new Set<string>();
     variants.add(phone.trim());
     variants.add(digits);
     if (digits.length === 10 && digits.startsWith("3")) {
       variants.add(`57${digits}`);
       variants.add(`+57${digits}`);
     } else if (digits.length === 12 && digits.startsWith("573")) {
       const raw10 = digits.slice(2);
       variants.add(raw10);
       variants.add(`+57${raw10}`);
       variants.add(digits);
     }
     return Array.from(variants);
   }
   ```
2. **Búsqueda Multi-Variante:** Consultar `leads` evaluando `email = $1 OR whatsapp = ANY($2)`.
3. **Actualización Segura Sin Colisión Forzada:**
   - Si se detecta un registro previo, actualizar nombre, ciudad, rol y `metadata`.
   - **Solo** actualizar el campo `email` o `whatsapp` si el nuevo valor no pertenece a otra fila de la base de datos. Si ya está ocupado por otro registro, conservar el valor original sin forzar un `UPDATE` que dispararía la restricción `UNIQUE`.
4. **Fallback Transaccional en Inserciones:** Si por concurrencia un `INSERT` captura el error `23505` (unique violation), capturar la excepción y re-consultar el registro existente en lugar de colapsar la respuesta HTTP.

---

## 9. Desacople Estricto de Formularios por Intención de Negocio

Todo ecosistema web debe separar con absoluta nitidez sus formularios según el propósito y la audiencia, evitando mezclar conceptos íntimos o comunitarios con intenciones corporativas:

```
┌────────────────────────────────────────────────────────────────────────┐
│             TRÍADA DE FORMULARIOS POR INTENCIÓN DE NEGOCIO             │
├─────────────────────┬──────────────────────┬───────────────────────────┤
│ 1. COMUNIDAD B2C    │ 2. ALIANZAS B2B      │ 3. ADMISIÓN VIP & CHECKOUT│
│ (`LeadForm.astro`)  │ (`AllianceForm.astro`)│ (`CheckoutForm.astro`)    │
├─────────────────────┼──────────────────────┼───────────────────────────┤
│ • Registro general  │ • Contratación sede  │ • Selección de pases/cupo │
│ • Roles personales  │ • Talleristas/Eventos│ • Modalidad pago (40%/100%)│
│ • Cultura/Bienvenida│ • Textarea propuesta │ • dLocal Go / Nequi / PSE │
│ • Origen: comunidad │ • CERO roles pareja  │ • Origen: checkout_evento │
│ • Remitente: Marca  │ • Origen: alianza_b2b│ • Credencial sellada + QR │
└─────────────────────┴──────────────────────┴───────────────────────────┘
```

1. **Formulario de Comunidad B2C (`LeadForm.astro`):**
   - Propósito: Registro en lista de novedades y eventos comunitarios.
   - Campos: Nombre o alias, WhatsApp, Email, Modalidad comunitaria (`pareja`, `mujer_sola`, `hombre_solo`), Ciudad.
2. **Formulario de Alianzas y Contratación B2B (`AllianceForm.astro`):**
   - Propósito: Co-producción, alquiler de locación privada o talleres de facilitadores.
   - Campos: Nombre/Organización, WhatsApp, Email, Selector de Tipo de Alianza, Textarea amplio para detallar la propuesta, Ciudad.
   - **Invariante:** CERO preguntas de modalidad íntima (`pareja` o `single`).
3. **Formulario de Checkout & Admisión VIP (`CheckoutForm.astro`):**
   - Propósito: Adquisición de entradas, pases o separación de cupos.
   - Campos: Selector de pases, modalidad de pago, datos de contacto, pasarela de pago segura.

---

## 10. Contrato Canónico de Evolution Go & Bot Inteligente en Zerops (:8085)

Evolution Go es un motor ultra-frugal compilado en Go (`whatsmeow`) que consume apenas ~25-45 MB de RAM.

### Invariantes de Infraestructura y Red Interna
1. **Puerto Canónico:** El servicio expone su API HTTP en el **puerto `8085`** (el puerto 8080 pertenece exclusivamente a Bifrost AI Gateway).
2. **Topología de Nombres de Entorno:**
   - En `zerops.yaml` (run.envVariables): `EVOLUTION_URL: "http://evolution:8085"`
   - En código Astro / Node / Bun:
     ```typescript
     const EVOLUTION_API_URL = process.env.EVOLUTION_URL || process.env.EVOLUTION_API_URL || "http://evolution:8085";
     const EVOLUTION_API_KEY = process.env.EVOLUTION_API_KEY || process.env.GLOBAL_API_KEY;
     ```
3. **Autenticación:** Las peticiones deben incluir la cabecera `apikey: <tu_api_key>` (o `ApiKey`).
4. **Contrato de Envío de Texto (`POST /send/text`):**
   ```bash
   curl -s -X POST http://evolution:8085/send/text \
     -H "apikey: $EVOLUTION_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "number": "573100000000",
       "text": "Hola ✨ Mensaje transaccional con voz de marca."
     }'
   ```
   *Nota:* El número debe enviarse sin signos `+`, normalizado con código de país (ej. `573...` para Colombia).

### Invariantes del Bot Inteligente & Webhook Omnicanal:
1. **Cero Prompts Hardcodeados (`bot-knowledge.ts`):**
   - El bot NUNCA debe hardcodear fechas de eventos en piedra en el código.
   - Debe implementar un servicio dinámico `bot-knowledge.ts` que calcule la fecha actual en tiempo presente continuo (`America/Bogota` UTC-5), filtre automáticamente eventos caducados (`event.date >= currentIsoDate`) e inyecte la sede física permanente y las pasarelas activas descubiertas dinámicamente vía `process.env`.
2. **Ventana Deslizante de Intervención Humana (Human Takeover):**
   - Cuando el dueño o un operador responde manualmente desde el celular (`fromMe: true`), el webhook intercepta el mensaje y silencia el bot automáticamente en Valkey (`wa:human_takeover:${phone}`) por **2 horas (7200s)**. Cada mensaje manual renueva la ventana de 2 horas.
   - **Comandos de Escape del Operador:**
     * `#bot`: Cancela inmediatamente el takeover humano y reactiva el bot para ese contacto.
     * `#mute`: Silencia el bot por 24 horas (86400s) para casos donde el cliente requiere atención humana extendida.
3. **Tuteo Mandatario ("TÚ"):**
   - La voz de marca del bot debe dirigirse SIEMPRE al usuario usando el pronombre "tú" ('¿cómo estás?', 'te esperamos', 'cuéntame'). Está estrictamente prohibido el uso de "usted" o tratamientos fríos y distantes.
4. **Módulo Desacoplado de Afiliados / Embajadores (Opcional & Pluggable):**
   - **Feature Detection Dinámico**: Si el proyecto o marca NO implementa programa de afiliados ni existe tabla en base de datos, el bot y la web operan con tarifa plena sin mencionar jamás referidos, enlaces ni códigos `?ref`. Lo que no existe en el catálogo, se asume inexistente sin avisos negativos.
   - **Estrategia Aislada (Strategy Pattern)**: Si el proyecto habilita afiliados, la mecánica de recompensas y descuentos se desacopla mediante estrategias (`SingleUsePerDomainStrategy`, `ContinuousDiscountStrategy`, `StandardRateStrategy`). Cada marca define sus reglas en su propio repositorio downstream sin contaminar la plantilla universal.
   - **Frequency Capping (Valkey)**: Si se sugiere el enlace de embajador, se registra `wa:affiliate_pitched:${phone}` con TTL de 7 días (604800s) para evitar fatiga.
5. **Simulación Realista de Presencia:**
   - Antes de enviar la respuesta generada por Bifrost, el webhook debe aplicar una pausa de lectura y simulación de digitación proporcional al largo del texto (entre 3.5s y 8s) para garantizar un ritmo conversacional humano.
6. **Desacople Asíncrono con NATS JetStream:**
   - El webhook de WhatsApp responde HTTP `200 OK` en `<10ms` inyectando `Nats-Msg-Id` en el stream `events.whatsapp.incoming` para deduplicación atómica a nivel de hardware, delegando la inferencia y el despacho a workers sin bloquear las conexiones HTTP de entrada.

---

## 11. Gobernanza de Pasarelas Digitales (dLocal Go & Webhooks)

dLocal Go es la pasarela líder para cobros en moneda local en Latinoamérica (Colombia: Tarjetas, PSE, Nequi, Daviplata).

### Invariantes de Integración
1. **Bifurcación Dinámica de Entornos:**
   - Sandbox: `https://api-sbx.dlocalgo.com/v1/payments` (cuando `DLOCAL_GO_ENV=sandbox`).
   - Producción (Live): `https://api.dlocalgo.com/v1/payments` (cuando `DLOCAL_GO_ENV=live` o producción).
2. **Prevención de Multi-Click (Debounce en Frontend):**
   - Todo botón de pago debe deshabilitarse inmediatamente al primer clic (`button.disabled = true`) y mostrar un indicador visual de carga, impidiendo la creación de múltiples órdenes concurrentes.
3. **Idempotencia de Órdenes en Backend (60s Lock):**
   - Antes de insertar un nuevo ticket de pago, verificar si existe una orden en estado `pendiente` creada por el mismo contacto en los últimos 60 segundos con los mismos parámetros. Si existe, reutilizar el `id` y `ticket_hash` para evitar órdenes huérfanas.
4. **Autoridad Exclusiva por Webhook:**
   - La creación de la sesión de pago es únicamente una intención de compra.
   - **Prohibido:** Enviar WhatsApps de "reserva confirmada" o emitir credenciales digitales definitivas al momento de crear la orden.
   - **Obligatorio:** El despacho de credenciales con código QR y mensajes de confirmación se ejecuta **únicamente** cuando el webhook autenticado de dLocal Go confirma el estado `PAID` o `COMPLETED` en `/api/webhooks/dlocal`.
5. **Credenciales Digitales con QR Real:**
   - Los tickets deben generar un código QR SVG real (vía librerías como `qrcode`) codificando la URL pública de validación (`https://tudominio.com/ticket?hash=...`), erradicando códigos de barras decorativos en CSS.

---

## 12. Directrices de Copywriting Anti-Slop y Voz de Marca Agnóstica

Todo despliegue debe adherirse a principios rigurosos de comunicación clara, sin importar el nicho de negocio:
- **Erradicación de Clichés y Humo (Anti-Hype):** Prohibido el uso de adjetivos inflados genéricos ("revolucionario", "mágico", "único en su clase", "disruptivo"). La propuesta de valor se demuestra mediante hechos, especificaciones claras y beneficios comprobables.
- **Claridad y Sobriedad:** Utilizar lenguaje directo, profesional y enfocado en resolver el problema del usuario sin sobrecargar con jerga técnica o corporativa innecesaria.

---

## 13. Normalización Telefónica E.164 con Auto-Deducción Colombia (+57)

En despliegues para Colombia o con alta concentración de usuarios locales, la ausencia de código de país en formularios de contacto provoca que los enlaces `wa.me/` o el gateway EvolutionGo ruteen los números a los Países Bajos (+31, ej: `wa.me/3101234567`), provocando fallas críticas donde WhatsApp informa que el número no existe.

### Regla Canónica de Normalización:
1. **Detección Automática de Colombia (+57):**
   - Si el número ingresado contiene 10 dígitos y empieza por `3` (ej: `3101234567`), se infiere automáticamente que es un móvil colombiano y se normaliza a `+573101234567`.
2. **Preservación Internacional:**
   - Si el número ya incluye indicativo con prefijo `+` (ej: `+1...`, `+34...`, `+52...`), se respeta el código internacional suministrado.
3. **Generación de la Terna de Salida:**
   - Todo servicio debe exportar la función canónica `normalizePhone(raw)` que retorne:
     * `canonical`: Formato E.164 con signo más (ej: `+573101234567`) para almacenamiento e identificación.
     * `whatsappDigits`: Cadena pura de dígitos sin signo ni espacios (ej: `573101234567`) para la API de EvolutionGo y enlaces `https://wa.me/573101234567`.
     * `display`: Formato legible amigable para correos y UI (ej: `+57 310 123 4567`).

```typescript
export interface NormalizedPhone {
  canonical: string;
  whatsappDigits: string;
  display: string;
}

export function normalizePhone(raw: string): NormalizedPhone {
  const cleaned = raw.replace(/[^\d+]/g, '').trim();
  if (!cleaned) return { canonical: '', whatsappDigits: '', display: '' };

  let canonical = cleaned;
  if (!canonical.startsWith('+')) {
    const digitsOnly = canonical.replace(/\D/g, '');
    if (digitsOnly.length === 10 && digitsOnly.startsWith('3')) {
      canonical = `+57${digitsOnly}`;
    } else if (digitsOnly.length === 12 && digitsOnly.startsWith('57')) {
      canonical = `+${digitsOnly}`;
    } else {
      canonical = `+${digitsOnly}`;
    }
  }

  const digits = canonical.replace(/\D/g, '');
  let display = canonical;
  if (canonical.startsWith('+57') && digits.length === 12) {
    display = `+57 ${digits.slice(2, 5)} ${digits.slice(5, 8)} ${digits.slice(8)}`;
  }

  return { canonical, whatsappDigits: digits, display };
}
```

---

## 14. Deduplicación Multi-Canal Relacional y Detección de Conflicto Cruzado (409)

En ecosistemas con múltiples variantes de negocio (ej: Comunidad B2C, Alianzas B2B, Admisión VIP), un usuario puede interactuar con más de un canal a lo largo del tiempo.

### Principios Innegociables de Persistencia:
1. **Rastreo de Canales en Metadata (`registered_channels`):**
   - El modelo de datos de leads debe almacenar en `metadata.registered_channels` un arreglo JSONB con los slugs de las variantes donde el contacto se ha registrado (ej: `['comunidad', 'alianzas', 'vip']`).
2. **Supresión Idempotente de Notificaciones (`already_registered`):**
   - Si un usuario ya existe en la base de datos y vuelve a enviar el formulario de un canal donde YA figuraba en `registered_channels`, la API debe:
     * Retornar `{ success: true, already_registered: true, message: 'Ya estabas registrado en esta lista.' }`.
     * **SUPRIMIR** el disparo de correos o mensajes de WhatsApp hacia ese canal para evitar saturación comunicativa.
3. **Expansión Multi-Canal Transparente:**
   - Si el usuario existe pero solicita un canal NUEVO (ej: estaba en `comunidad` y ahora postula a `vip`), el sistema actualiza `metadata.registered_channels` incorporando el nuevo canal y **SOLO** dispara la notificación de bienvenida correspondiente a esa nueva intención.
4. **Detección Estricta de Conflicto Cruzado (HTTP 409 Conflict):**
   - Si el email ingresado pertenece al contacto A, pero el teléfono ingresado pertenece al contacto B, el backend **JAMÁS** debe mutar silenciosamente los datos ni sobreescribir la identidad.
   - Debe abortar inmediatamente con `HTTP 409 Conflict` y alertar: *"El correo electrónico o número de WhatsApp ingresado ya está asociado a otro contacto. Por favor verifica tus datos."*

---

## 15. Desacople Estratégico de Contenido Multi-Mensajería (WhatsApp vs Email)

Cuando un evento o registro dispara tanto WhatsApp como correo electrónico, enviar mensajes idénticos palabra por palabra crea fatiga comunicativa y devalúa la experiencia del usuario.

### Matriz de Roles y Responsabilidades:
| Dimensión | Canal WhatsApp (EvolutionGo) | Canal Email (Listmonk / SMTP) |
|---|---|---|
| **Rol Estratégico** | Mayordomía ejecutiva, conserje ágil, canal conversacional. | Dossier institucional, manifiesto formal, respaldo legal. |
| **Tono y Registro** | Cálido, personal, directo, 1-a-1, inmediato. | Soberano, detallado, documental, editorial. |
| **Extensión** | 2 a 3 párrafos cortos (lectura en < 15 segundos). | Estructura completa (bienvenida, manifiesto, reglas, soporte). |
| **Referencia Cruzada** | Cita breve: *"Te dejamos un dossier formal en tu correo."* | Cita formal: *"Activamos tu línea de atención en WhatsApp."* |
| **Regla de No-Redundancia** | **Prohibido duplicar el cuerpo del texto.** Solo se repiten eslóganes, slogans y activos mnemotécnicos de marca. |

---

## 16. Calificación de Leads por Transparencia de Oferta

Para servicios prémium, ofertas B2B de alto valor o experiencias de capacidad limitada en cualquier industria:
1. **Calificación Natural por Transparencia:**
   - Exponer rangos de inversión o criterios de acceso claros en la narrativa y landing page para alinear expectativas antes de la captura del lead. Esto actúa como un filtro natural de audiencia, mejorando el ratio de conversión y optimizando el tiempo del equipo comercial o de soporte.
2. **Claridad de Roles y Expectativas:**
   - Definir con precisión el alcance del servicio y los puntos de contacto humano (soporte, ejecutivos de cuenta o equipo operativo) sin ambigüedades.

---

## 17. Pipeline Canónico de Medios Audiovisuales & Streaming Web (`faststart` + Local NVMe I/O)

La entrega de video en entornos web modernos exige latencia mínima en el primer fotograma y economía estricta de ancho de banda. Los videos capturados desde dispositivos móviles (Android/iOS) suelen codificarse a tasas elevadas (12 a 25 Mbps) y ubican el metadato estructural (`moov` atom) al final del archivo (`mdat` primero), requiriendo reorganización para permitir la reproducción inmediata en el navegador.

```
┌────────────────────────────────────────────────────────────────────────┐
│              PIPELINE CANÓNICO DE STREAMING AUDIOVISUAL                │
├────────────────────────────────────────────────────────────────────────┤
│ 1. ORIGEN: Dispositivo Móvil / S3 / Almacenamiento Local (moov final)  │
│                                   │                                    │
│ 2. TRANSCODIFICACIÓN AISLADA: Ejecución en NVMe Local (/tmp)            │
│    setsid ffmpeg -nostdin -i raw.mp4 -c:v libx264 -crf 28              │
│           -preset veryfast -movflags +faststart -c:a aac /tmp/opt.mp4 │
│                                   │                                    │
│ 3. POSTER GENERATION: Extracción de fotograma clave en t=1s (WebP/JPG) │
│                                   │                                    │
│ 4. TRANSFERENCIA ATÓMICA: Copia directa al volumen público montado     │
│    cp /tmp/opt.mp4 ./public/media/... && cp /tmp/opt.webp ...          │
└────────────────────────────────────────────────────────────────────────┘
```

### Invariantes Técnicos de Transcodificación:
1. **Aislamiento de E/S en Disco Local (NVMe `/tmp`):**
   - Transcodificar exclusivamente hacia y desde almacenamiento local efímero (`/tmp`). Las operaciones de codificación masiva requieren acceso a disco local de alta velocidad para evitar demoras en buffers de red.
2. **Desacople de Proceso en Fondo (`setsid` & `-nostdin`):**
   - Al ejecutar optimizaciones de video en segundo plano dentro de entornos de agentes o contenedores, invocar `setsid` y la bandera `-nostdin`. Esto garantiza la persistencia del proceso de transcodificación de forma autónoma e independiente de la sesión de terminal activa.
3. **Invariante `moov` al Inicio (`-movflags +faststart`):**
   - Todo archivo `.mp4` para entrega web debe reorganizar su índice de cuadros al principio del archivo mediante `-movflags +faststart`, habilitando buffering progresivo instantáneo (<100ms) desde el primer paquete recibido.
4. **Optimización de Tasa y Perfil Web:**
   - Video: Códec `libx264`, perfil High, `preset veryfast`, factor de tasa constante `crf 26-28` (reducción de tamaño superior al 85% preservando nitidez visual).
   - Audio: Códec `aac`, tasa de 128 kbps stereo.
   - En componentes visuales, acompañar todo elemento `<video>` con su respectivo `poster="..."` y la directiva `preload="none"`.

---

## 18. Arquitectura de Testing Dual Desacoplada (Bun Test Invariants vs Playwright E2E)

Para mantener la velocidad de compilación y la robustez del testing sin colisiones de herramientas, los proyectos bajo esta plantilla separan de manera estricta los tests unitarios de dominio de los tests de integración en navegador real.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   MATRIZ DE TESTING DUAL DESACOPLADA                   │
├───────────────────────────────────┬────────────────────────────────────┤
│ CAPA 1: INVARIANTES DE DOMINIO    │ CAPA 2: E2E INTERACTIVO EN VIVO    │
│ Runner: Bun Test (bun:test)       │ Runner: Playwright (@playwright)   │
│ Directorio: tests/unit/           │ Directorio: tests/playwright/      │
│ Extensión: *.test.ts              │ Extensión: *.spec.ts               │
│ Enfoque: Schemas, Regex, AST,     │ Enfoque: DOM real, clics, flujos   │
│          Matemáticas de precios,  │          OTP, validación de QR,    │
│          Consistencia de Layout.  │          Seguridad de /adminn.     │
│ Velocidad: < 100 ms (en memoria)  │ Velocidad: ~ 10-20 s (Chromium)    │
└───────────────────────────────────┴────────────────────────────────────┘
```

### Reglas de Configuración en `package.json`:
1. **Prevención de Colisión de Discovery:**
   - Delimitar de forma explícita las rutas de ejecución en los scripts de `package.json` para que cada ejecutor procese únicamente los archivos compatibles con su arnés:
     ```json
     {
       "scripts": {
         "test": "bun test tests/unit",
         "test:unit": "bun test tests/unit",
         "test:e2e": "playwright test",
         "test:all": "bun test tests/unit && playwright test"
       }
     }
     ```
2. **Aprovisionamiento de Navegadores y Librerías del Sistema en LXC:**
   - En contenedores Linux Ubuntu (base Zerops), Playwright requiere tanto el binario del navegador como sus bibliotecas compartidas del sistema operativo (`libnspr4`, `libnss3`, `libgbm1`, `fontconfig`).
   - El script de aprovisionamiento o `prepareCommands` debe contemplar:
     ```bash
     npx playwright install chromium
     sudo npx playwright install-deps
     ```

---

## 19. Higiene Operativa ZCP: Blindaje FUSE / Google Drive SSoT y Cierre por Lotes en Linear

El contenedor de plano de control `zcp` opera con una jerarquía de almacenamiento híbrida: código local activo en `/var/www/{hostname}` y réplica permanente en Google Drive SSoT (`/var/www/baiosfera/` montado vía FUSE).

### Invariantes de Rendimiento de E/S:
1. **Aislamiento de Alcance en Comandos de Sistema:**
   - Acotar comandos exploratorios (`find`, `which`, `grep`) a la carpeta de trabajo local (`Cwd`), podando explícitamente (`-path /var/www/baiosfera -prune`) el árbol de Google Drive para garantizar respuestas inmediatas y preservar el presupuesto de E/S.
2. **Cierre de Hitos por Lotes en Linear (`update-status-batch`):**
   - La regla F5 de la Supreme Directive exige certificar la paridad física (`ssot-parity-check`) antes de marcar una tarea como completada (`Done`).
   - Al procesar múltiples tareas en lote (ej: 10 o 25 issues atómicas), estructurar el cierre en tres fases deterministas:
     * Fase 1: Ejecutar `ssot-parity-check` una sola vez para atestiguar la integridad global del hito (código de salida 0).
     * Fase 2: Invocar la actualización masiva de estados hacia la API GraphQL de Linear mediante script directo o comando batch.
     * Fase 3: Purgar el archivo de bloqueo físico `/var/www/artifacts/linear_active.json`.

---

## 20. Fortaleza Administrativa Agnóstica: Ofuscación de Rutas, Anti-Indexación y Trazabilidad Transaccional

Para aplicaciones que integran paneles de control sin depender de un CMS monolítico:

### 1. Ofuscación de Rutas y Hard-404:
- Definir la ruta del panel administrativo mediante variable de entorno o convención ofuscada (ej: `/adminn`, `/manage`, o `${ADMIN_PATH}`).
- En `src/middleware.ts`, retornar `HTTP 404 Not Found` en las rutas genéricas `/admin` y `/admin/`, canalizando el tráfico exclusivamente a la ruta designada.

### 2. Blindaje Anti-Indexación y Caché Cero:
- En toda respuesta bajo la ruta administrativa, suministrar cabeceras HTTP de protección:
  ```http
  X-Robots-Tag: noindex, nofollow, noarchive, nosnippet, noimageindex
  Cache-Control: no-store, no-cache, must-revalidate, max-age=0
  ```
- Declarar reglas explícitas en `public/robots.txt`:
  ```txt
  User-agent: *
  Disallow: /admin/
  Disallow: /adminn/
  Disallow: /api/admin/
  ```

### 3. Directorio Unificado de Usuarios (Registro = Lead = Embajador/Cliente):
- Consolidar la gestión de contactos en una sola entidad relacional integral, simplificando consultas y permitiendo eliminación en cascada transaccional limpia.

### 4. Categorización Transaccional Estricta (Pago Real vs Cortesía Manual):
- Al emitir pases o accesos desde el panel administrativo, clasificar las operaciones según su naturaleza financiera:
  * **Pago Real en Sitio / Efectivo:** Registrar monto y método de pago, habilitando la acreditación correspondiente a afiliados.
  * **Cortesía Manual ($0):** Registrar el pase con monto cero y trazabilidad administrativa, preservando el cálculo de comisiones intacto.

---

## 21. Contrato de Dominio Inmutable & F5 Reality Gate (Anti-Checklist Theater Universal)

Para cualquier proyecto o marca desplegada bajo esta plantilla, la integridad del software se rige por contratos de dominio deterministas y verificación física en tiempo de ejecución:

### 1. Capa de Dominio Centralizada (`src/domain/`):
- **Set Aditivo Monótono de Etiquetas (Tags):** Las etiquetas de clasificación y canales de un contacto (`metadata.tags`, `registered_channels`) son conjuntos aditivos estrictos. Ninguna mutación o actualización de perfil puede sobrescribir, truncar o descartar etiquetas previamente adquiridas por el usuario.
- **Cero Lógica Dispersa en Vistas y Endpoints:** Los controladores API (`/api/leads/register`) y paneles administrativos (`/adminn`) consumen exclusivamente las funciones de mutación y consulta de la capa de dominio, erradicando queries SQL manuales con condiciones `OR` fragmentadas.

### 2. Sensor Físico F5 en Linear y CI/CD (Reality Over Checklist Theater):
- **Cierre Subordinado a la Suite de Pruebas:** El script soberano `linear-cli update-status <ID> "Done"` ejecuta obligatoriamente la suite de pruebas físicas en el runtime activo (`ssh <service> "cd /var/www && (npm test || bun test)"`).
- **Atestación Física de Calidad:** La paridad de archivos en Google Drive o el estado limpio de Git son condiciones necesarias pero jamás suficientes. El cierre a 'Done' se consuma exclusivamente cuando la suite completa de pruebas físicas de aplicación finaliza con código de salida 0.

---

## 22. Matriz Universal de Lecciones de Batalla & Blindajes Físicos (Síntesis de 230 BAI en Producción)

Esta sección consolida de forma 100% agnóstica a cualquier marca los descubrimientos, anomalías resueltas y blindajes arquitectónicos extraídos directamente de 230 tickets de producción (`BAI-*`). Cualquier agente AGY que despliegue infraestructura o software en Zerops debe adherirse a estos 8 axiomas probados:

### 1. Maxim AI Bifrost & FreeLLMAPI (Inferencia & Gateway de IA)
- **Persistencia Duradera Obligatoria:** Las configuraciones de modelos y registros de logs de Bifrost (`config_store` y `logs_store`) DEBEN residir en PostgreSQL 18. Queda estrictamente prohibido usar SQLite local efímero dentro del contenedor de Bifrost, ya que cualquier reinicio, escalado o despliegue borra las llaves y modelos configurados.
- **Incompatibilidad Vectorial con Valkey:** `vector_store.type` en Bifrost debe configurarse exclusivamente como `chromem` (en memoria embebido) o `qdrant` (motor vectorial dedicado). **JAMÁS configurar `redis` apuntando a Valkey 7.2**, ya que Valkey es un motor de caché y datos en memoria puro que no incluye los módulos propietarios de Redis Stack (`FT.SEARCH`, `FT.CREATE`), lo que provoca fallos silenciosos de arranque o pánico en el binario de Go.
- **Gobernanza por Virtual Keys:** Configurar siempre las Virtual Keys en `/api/governance/virtual-keys` con límites presupuestarios y de tasa para aislar el consumo de la web pública, bots conversacionales y paneles internos.
- **Transcripción de Audio en Streaming (<400ms):** Descargar notas de voz autenticadas desde el motor de mensajería (Evolution) y procesarlas directamente contra Groq Whisper (`whisper-large-v3-turbo`) con token Bearer, omitiendo almacenamiento intermedio en disco para máxima velocidad y privacidad.

### 2. Valkey 7.2 vs Redis Stack (Caché, Locks & Human Takeover)
- **Frontera de Capacidades:** Valkey 7.2 es el motor canónico de alto rendimiento para estructuras de datos estándar (KV, Hashes, Sets, Sorted Sets, Pub/Sub, colas BullMQ). No intentar cargar módulos RediSearch ni RedisJSON.
- **Locks Atómicos de Idempotencia en Pagos y Webhooks:** En pasarelas de pago y webhooks asíncronos (Wompi, ePayco, Stripe, dLocal), adquirir inmediatamente un lock atómico de 60 segundos en Valkey:
  `SET lock:webhook:{transaccion_id} 1 NX EX 60`
  Si la clave ya existe (colisión), responder `HTTP 200` de inmediato sin re-ejecutar la lógica. Esto erradica acreditaciones dobles de saldo, reservas duplicadas o sobrepagos de comisiones.
- **Human Takeover & Ventana de Silencio (2 Horas):** Cuando un operador humano interviene en una conversación desde WhatsApp Web o la app móvil, el backend debe registrar una clave en Valkey:
  `SET bot:takeover:{jid} 1 EX 7200`
  Mientras esta clave exista, el bot de IA permanece en **silencio absoluto**, persistiendo el historial en memoria para reactivarse limpiamente solo si el cliente reanuda el contacto después de 2 horas de inactividad.

### 3. EvolutionGo & Motor de Mensajería WhatsApp
- **Especialización de Canal (Transaccional vs Campañas Masivas):** WhatsApp está reservado para comunicación de alta inmediatez y valor (<15 segundos de lectura, códigos OTP, pases con QR, alertas críticas). Campañas masivas o envíos que superen 500 destinatarios DEBEN despacharse por email (Listmonk) para blindar el número contra reportes de spam y baneos por parte de Meta.
- **Blindaje Relacional Anti-Starvation & Aislamiento de Pool (SQLSTATE 53300):** EvolutionGo/whatsmeow gestiona sus sesiones criptográficas en `evogo_auth` y datos de usuario en `evogo_users`. En escenarios de micro-cortes, rotación de sockets o sesiones desvinculadas (`LoggedOut`), los ciclos de reconexión instancian nuevos pools `database/sql` sin cerrar los anteriores (upstream issues #106, #118). Si PostgreSQL no tiene límites por base de datos, acumula decenas de conexiones `idle` hasta copar el 100% de los slots de la base compartida, bloqueando a `webprod` y APIs con `FATAL: remaining connection slots are reserved for roles with the SUPERUSER attribute`.
  * **Invariante de Aislamiento de Base de Datos Satélite**: Toda base de datos satélite de Evolution DEBE inicializarse con cuota física y timeout de recolección de conexiones ociosas:
    ```sql
    ALTER DATABASE evogo_auth WITH CONNECTION LIMIT 15;
    ALTER DATABASE evogo_users WITH CONNECTION LIMIT 15;
    ALTER DATABASE evogo_auth SET idle_session_timeout = '5min';
    ALTER DATABASE evogo_users SET idle_session_timeout = '5min';
    ALTER DATABASE evogo_auth SET idle_in_transaction_session_timeout = '30s';
    ALTER DATABASE evogo_users SET idle_in_transaction_session_timeout = '30s';
    ```
  * Esto garantiza un radio de impacto acotado (*blast radius* $\le 30$ conns), dejando siempre libre la mayoría del pool para el tráfico transaccional web y reservando intactos los 3 slots de superuser para administración.
- **Silencio Ante Acuses de Cortesía:** Ante respuestas de cortesía o confirmación breve del usuario de 1 o 2 palabras ("ok", "gracias", "listo", "vale", "dale", "perfecto"), el bot NO debe generar respuestas con modelos de lenguaje ni gastar tokens; registra el acuse en la base de datos y calla.
- **Normalización Canónica E.164:** Todo número telefónico capturado o procesado debe normalizarse al formato E.164 (`+` seguido de código de país y dígitos numéricos limpios) antes de interactuar con la base de datos o las APIs de mensajería.

### 4. Listmonk & Automation Engine (Email Marketing Soberano)
- **Desacople Asíncrono Estricto (Zero 504 Gateway Timeout):** La sincronización de suscriptores o disparo de campañas en Listmonk NUNCA debe bloquear la ruta HTTP crítica de un checkout o registro web. Si Listmonk o el relay SMTP tienen latencia, el usuario experimenta un error 504 y la compra se cancela. Estas operaciones se ejecutan de forma asíncrona mediante eventos NATS o workers desacoplados en background.
- **Tupla Inmutable WhatsApp-Email:** La identidad del contacto se modela como un par indivisible `(whatsapp, email)`. Si un contacto interactúa a través de un nuevo formulario usando su email previamente registrado, el sistema no duplica la fila: unifica la metadata y preserva el historial.
- **Presupuesto HTML de Plantillas (<85KB):** Todo correo transaccional o de marketing debe compilarse con un peso de HTML inferior a 85KB. Si excede 102KB, Gmail trunca el cuerpo ("Mensaje recortado"), ocultando los enlaces de baja obligatoria (RFC 8058) y afectando la reputación del dominio (SPF/DKIM/DMARC).

### 5. PostgreSQL 18 & Modelado de Datos
- **Blindaje Universal Anti-Starvation & Aislamiento de Pool (SQLSTATE 53300)**:
  PostgreSQL asigna un número finito de conexiones concurrentes (`max_connections`, usualmente 100 en perfiles estándar de Zerops), reservando 3 para superusuarios (`postgres`) y telemetría de plataforma. Cuando servicios satélites (como motores de WhatsApp, workers o listeners) reconectan sin control o cuando endpoints web abren conexiones dedicadas en lugar de atómicas, el pool global se agota y los usuarios reciben `FATAL: remaining connection slots are reserved for roles with the SUPERUSER attribute`.
  * **Invariante de Cuotas Físicas por Base de Datos (`CONNECTION LIMIT`)**:
    Toda base de datos principal (`db`) y satélite (`evogo_auth`, `evogo_users`, colas) DEBE inicializarse con cuotas estrictas y timeouts de recolección de conexiones ociosas:
    ```sql
    ALTER DATABASE db WITH CONNECTION LIMIT 60;
    ALTER DATABASE evogo_auth WITH CONNECTION LIMIT 15;
    ALTER DATABASE evogo_users WITH CONNECTION LIMIT 15;
    ALTER DATABASE db SET idle_session_timeout = '2min';
    ALTER DATABASE db SET idle_in_transaction_session_timeout = '30s';
    ALTER DATABASE evogo_auth SET idle_session_timeout = '2min';
    ALTER DATABASE evogo_auth SET idle_in_transaction_session_timeout = '30s';
    ALTER DATABASE evogo_users SET idle_session_timeout = '2min';
    ALTER DATABASE evogo_users SET idle_in_transaction_session_timeout = '30s';
    ALTER ROLE db SET idle_session_timeout = '2min';
    ALTER ROLE db SET idle_in_transaction_session_timeout = '30s';
    ```
    Esto garantiza un radio de impacto acotado (*blast radius* total $\le 90$ conexiones), protegiendo permanentemente al menos 10 slots libres para administración y telemetría.
  * **Invariante de Pooling Transaccional (Erradicación de `pool.connect()` no transaccional)**:
    Prohibido llamar `await pool.connect()` para consultas simples en rutas de checkout, webhooks o APIs. Usar estrictamente `pool.query(text, params)` (o Drizzle/Kysely ORM). `pool.query()` toma y retorna el socket atómicamente en un solo tick, erradicando retención de conexiones concurrentes y fugas por excepciones no capturadas.
    `pool.connect()` queda restringido EXCLUSIVAMENTE a transacciones atómicas (`BEGIN ... COMMIT/ROLLBACK`) dentro de un bloque estructurado con `try ... finally { client.release(); }`.
  * **Manejo Defensivo y Sanitización de Errores de Base de Datos en Frontera Web**:
    Todo endpoint de pago o captura debe capturar excepciones de saturación (`code === '53300'`, `connection slots`, `timeout exceeded`) y responder `HTTP 503 Service Unavailable` con mensaje amigable al usuario ("En este momento estamos experimentando alta demanda en el sistema de pagos. Por favor intenta de nuevo en unos instantes"), NUNCA filtrando volcados o mensajes internos de PostgreSQL al usuario final.
  * **Soporte PgBouncer con TLS (`:6432`)**:
    Si un servicio de alta concurrencia se conecta a través del puerto gestionado de PgBouncer (`${database_connectionTlsString}` / `:6432`), el pool cliente en Node/Bun debe configurarse con `ssl: { rejectUnauthorized: false }` para satisfacer el requerimiento de cifrado de PgBouncer en Zerops.
- **Sizing de Conexiones (`max_connections`) & Multiplexación PgBouncer**:
  En Zerops Incus LXC, `max_connections` se calibra automáticamente según la RAM del contenedor (50 conexiones por GiB en perfiles OLTP: 20 en 256MB, 50 en 1GB, 100 en 2GB, 200 en 4GB, 500 en 16GB+). 3 slots se reservan para superuser y hasta 4 para telemetría interna de la plataforma.
  * **El Mito de los 100 max_connections como "Ideal"**: 100 no es un valor óptimo de concurrencia activa, sino un techo de seguridad de memoria. Conforme a la fórmula canónica de PostgreSQL/HikariCP (`Pool Size = (CPU Cores * 2) + 1`), el throughput máximo de CPU se alcanza con pocas conexiones activas concurrentes (~10 a 20). Valores superiores a 100-200 sin pooling provocan degradación severa por context-switching del kernel y contención en `ProcArrayLock`/snapshots de visibilidad MVCC.
  * **Estrategia de Conexión en Alta Demanda**: Para cargas con cientos de clientes concurrentes, conectar los servicios a través del puerto gestionado de PgBouncer (`6432`), el cual acepta miles de clientes multiplexándolos limpiamente sobre una cuota reducida de backends reales.
- **Upsert Defensivo Universal (`ON CONFLICT`):** Todo endpoint público de captura debe implementar operaciones `INSERT ... ON CONFLICT DO UPDATE` o `DO NOTHING`. Ninguna tabla pública debe fallar con error HTTP 500 por violaciones de clave única ante reintentos de red del cliente.
- **Acumulación Monótona de Etiquetas:** El arreglo de etiquetas de un contacto (`metadata.tags`, `metadata.registered_channels`) debe tratarse como un conjunto aditivo estricto (`Set`). Al actualizar el perfil de un usuario, las nuevas etiquetas se añaden mediante unión matemática; jamás se sobreescribe ni se trunca el array preexistente.
- **Entidades de Negocio Dinámicas en PostgreSQL 18 & Tiempo Presente Continuo:** En sitios con agendas, cartelera o eventos temporales, la consulta en el servidor (`Astro SSR`) y en el worker agéntico (`whatsappbot`) debe filtrar en tiempo real sobre PostgreSQL:
  `WHERE fecha_fin >= NOW()` (usando la zona horaria del proyecto).
  Lo que ocurrió en el pasado (`fecha_fin < NOW()`) se reconoce como memoria histórica/archivo y nunca se ofrece como próximo ni reservable.
  Prohibido usar crons o regeneraciones estáticas para ocultar eventos pasados, ya que los usuarios verán fechas vencidas si el cron se retrasa o el caché estático persiste.
- **CoHaLo Positivo, Sustracción Elegante & Cero Negative Prompting:** Prohibido llenar código, prompts o plantillas con directivas defensivas o restrictivas ("NO MESAS VIP", "NO SOMOS UN BAR SWINGER", "NO AFILIADOS", "NO BOT", "NO PAGOS", "NO MEMBRESIAS"). La verdad de catálogo define afirmativamente lo que existe. Lo que no está registrado en base de datos se asume inexistente sin avisos negativos en código o respuestas.
- **Sesión Global de Cliente & Autofill Fricción Cero:** Persistencia de perfil autenticado (`user_profile`: alias, teléfono, correo, rol) en `localStorage`/cookies tras verificación OTP. Todos los formularios de compra, checkout y reserva se autocompletan en caliente, eliminando fricción y solicitudes redundantes de OTP.
- **Arquitectura Lego Desacoplada de Afiliados (Zero Brand Contamination):** Feature detection dinámico. Si un proyecto limpio (`iniciar.sh-first`) no define módulo de afiliados ni tabla en BD, el bot y la web operan al 100% sin mencionar jamás embajadores, enlaces de referidos ni códigos `?ref`. Si implementa afiliados, la lógica de liquidación se aísla bajo Strategy Pattern (`SingleUsePerDomainStrategy`, `ContinuousDiscountStrategy`, `StandardRateStrategy`). Cero filtración de reglas de una marca hacia plantillas base universales.

### 6. Storage Híbrido: POSIX NVMe vs Object Storage S3
- **Video Web Progresivo en Almacenamiento Local (Zero S3 Bandwidth Egress):** Videos de landing pages, fondos o héroes deben transcodificarse en local a 720p H.264 (~800kbps) ubicando el índice `moov` al inicio (`-movflags +faststart`) y servirse directamente desde `/public/media`. Esto habilita streaming HTTP por rangos de bytes instantáneo (<100ms) sin costos de egress en S3.
- **S3 MinIO Reservado para Contenido Dinámico:** El almacenamiento S3 se utiliza exclusivamente para archivos adjuntos generados por usuarios, respaldos de base de datos o activos pesados (>500KB), sirviéndose siempre con URLs prefirmadas de expiración corta.
- **Permisos de Montaje POSIX:** Al usar `local-storage:single@1`, verificar que las carpetas montadas en `/mnt/localstorage` pertenezcan a `zerops:zerops` (`uid:gid 1000:1000`) para evitar bloqueos por permisos en contenedores no-root.

### 7. GitOps & Ciclo de Vida de Plataforma Zerops
- **Variable de Entorno `HOST: "0.0.0.0"` Mandatoria:** Los adaptadores de servidor (Astro Node standalone, Bun, Fastify) escuchan por defecto en `127.0.0.1`. En Zerops, esto impide que el balanceador L7 alcance el puerto, arrojando error `502 Bad Gateway`. Declarar siempre `HOST: "0.0.0.0"` en `envVariables`.
- **Base OS Ubuntu para Compilaciones Complejas:** Usar `os: ubuntu` en servicios con dependencias nativas C (`glibc`, `sharp`, `canvas`, `musl-dev`). Alpine es excelente para binarios estáticos de Go, pero introduce incompatibilidades con bundlers modernos basados en Node/Bun.
- **Empaquetado Limpio:** En `deployFiles` de aplicaciones Astro, transferir `dist/`, `package.json` y `node_modules`. No empaquetar con `bun build --target bun` monolítico cuando existan addons binarios nativos.
- **Staging Efímero de Costo Cero:** Utilizar el esquema multi-servicio de Zerops (`webstage` en rama `stage`, `webprod` en rama `main`). El servicio de stage se activa únicamente para validar en vivo antes de promover y se puede detener para mantener costos controlados.

### 8. Fortaleza Administrativa, Anti-Indexación & Finanzas
- **Ofuscación y Retorno 404 Estricto:** La URL del panel administrativo debe residir en una ruta ofuscada (ej: `/adminn`). Las rutas comunes (`/admin`) deben devolver `HTTP 404 Not Found` en el middleware.
- **Blindaje Anti-Rastreadores:** Servir cabeceras `X-Robots-Tag: noindex, nofollow, noarchive, nosnippet` y `Cache-Control: no-store` en todas las respuestas del panel de gestión.
- **Diferenciación Transaccional Financiera:** Separar explícitamente en la base de datos las transacciones con pago monetario real (que generan cálculo de saldo y comisiones para afiliados) de los pases de cortesía o manuales ($0), evitando distorsiones contables y pagos indebidos.

---

## 23. Arquitectura Canónica del Bot de WhatsApp Desacoplado (SOTA Zerops-First)

Para cualquier proyecto o marca desplegada en Zerops, el agente conversacional de WhatsApp **NUNCA debe residir en el backend SSR de la aplicación web** (`/api/webhooks/whatsapp.ts`). La arquitectura soberana exige el desacople total en un worker dedicado que opera bajo **7 Invariantes Canónicos**:

### 1. Desacople Operativo & Aislamiento de Ciclo de Vida:
- **Servicio Dedicado (`whatsappbot`):** Ejecutado en runtime `ubuntu/bun@1.3` con autoescalado elástico (`cpuMode: SHARED`, `minFreeRamGB: 0.25`).
- **Resiliencia ante Deploys Web:** Los despliegues o reinicios de la web (`webprod`) tienen impacto CERO sobre la atención al cliente por WhatsApp. El bot permanece 100% activo sin caerse ni provocar tormentas de reintentos por timeouts de Evolution Go.
- **Ingesta en 2 Niveles (<15ms ACK):**
  * **Nivel Ingress:** Endpoint ultraliviano recibe el webhook `messages.upsert` de Evolution Go, publica el evento en NATS JetStream (`events.whatsapp.incoming`) o responde inmediatamente con `HTTP 200 {"status": "acknowledged"}` en <15ms antes de iniciar decodificación de audio o inferencia LLM.
  * **Nivel Worker:** El servicio `whatsappbot` procesa la lógica conversacional de forma asíncrona, eliminando en un 100% las tormentas de reintentos y timeouts.

### 2. Ingesta Agnóstica de Marca desde SSoT Local Storage (Zero Hardcoding):
- **Cero Acoplamiento a Marcas Específicas:** Ningún archivo de plantilla, script, skill o receta debe contener cadenas quemadas (`elplacerdc`, `Segi`, `The Corset Society`, etc.).
- **Resolución Dinámica de Identidad:** La personalidad, arquetipo, dialecto regional, políticas y catálogo se leen dinámicamente desde:
  `/mnt/localstorage/${PROJECT_NAME}/dev/brandbook.json` y `/mnt/localstorage/${PROJECT_NAME}/dev/system_prompt.md`.
- **Sanitización Dinámica de Enlaces:** El validador post-LLM restringe los enlaces emitidos estrictamente a los dominios canónicos declarados en el brandbook activo (`canonical_urls`) y canales de mensajería oficiales (`wa.me`), erradicando enlaces rotos o 404s.

### 3. Introspección Defensiva de Esquemas en PostgreSQL 18:
- **Adaptabilidad a Cualquier Dominio:** No todas las marcas tienen afiliados, tickets o comercio electrónico. El bot debe inspeccionar dinámicamente `information_schema.tables` y `information_schema.columns`.
- **Ejecución Defensiva:** Si la base de datos no contiene tablas como `afiliados`, `event_tickets` u `orders`, el worker captura la ausencia de forma limpia y devuelve perfiles vacíos sin generar excepciones SQL ni respuestas HTTP 500.
- **Generación Canónica de URLs de Afiliado:** Los enlaces de referidos derivan siempre del host canónico de la marca activa (`${APP_URL}/?ref=${alias}`), jamás de dominios predefinidos.

### 4. Ingesta Robusta de Audio en Evolution Go (`whatsmeow`) & Whisper Turbo:
- **Doble Ruta de Extracción de Medios:** Evolution Go entrega el payload base64 en `data.Message.base64` (`msgObj.base64`). Si el webhook no lo incluye inline, el worker invoca automáticamente `POST /message/downloadmedia` pasando `{ message: msgObj }`.
- **Compatibilidad con Variantes de Audio:** Detecta indistintamente `audioMessage`, `AudioMessage`, `mediaType: "audio"` o `mimetype: audio/...`.
- **Transcripción de Streaming (<350ms):** Envía el buffer de audio a Groq Whisper Large v3 Turbo (`whisper-large-v3-turbo`) con respaldo multi-llave y respuesta empática en caso de audios inaudibles.

### 5. Identidad WhatsApp Multi-Device & Filtrado de `@lid`:
- **El Problema de los Linked Device IDs (`@lid`):** En cuentas multi-dispositivo, Evolution API entrega eventos con identificadores `chatJid` o `senderJid` terminados en `@lid`. Despachar mensajes de vuelta a un `@lid` falla silenciosamente en el motor Go.
- **Resolución Prioritaria a Números E.164:** El worker filtra y descarta identificadores `@lid`, extrayendo el número real desde `SenderAlt` o JIDs con `@s.whatsapp.net`, normalizando a dígitos numéricos limpios para el despacho de mensajes.

### 6. Prevención de Self-Shadowing en Zerops Vault:
- **Invariante de Variables de Entorno en Zerops:** Declarar en `zerops.yaml` una variable con su propio nombre referenciado desde el vault (ej: `GROQ_API_KEY: ${GROQ_API_KEY}`) causa el error de preflight `whatsappbot_env_self_shadow`.
- **Mapeo con Nombres Distintos:** Las variables secretas del vault deben nombrarse de forma explícita y mapearse a la variable de entorno del runtime:
  `GROQ_API_KEY: ${WHISPER_GROQ_API_KEY}`.

### 7. Ingesta SSoT en Tiempo Real, Adaptación Dinámica de Rol/Género y Regla SSoT > Historial:
- **Ficha Completa de Usuario en Tiempo Real:** El bot extrae todos los datos del usuario en cada turno (`alias`, `email`, `ciudad`, `rol`, `afiliado`, `métricas`, `membresías`).
- **Tratamiento Diferenciado por Rol / Género:**
  * `hombre_solo`: Perfil individual masculino $\to$ trato en masculino singular ("Embajador", "bienvenido", "tú").
  * `mujer_sola`: Perfil individual femenino $\to$ trato en femenino singular ("Embajadora", "bienvenida", "tú").
  * `pareja`: Cuenta compartida de pareja $\to$ trato estricto en plural ("ustedes", "pareja", "chicos", "ambos", "como pareja", "Embajadores"). Nunca tratar como mujer u hombre individual.
  * `otro` o no especificado $\to$ tono cercano, neutral y respetuoso.
- **Regla de Verdad Absoluta en Tiempo Real (SSoT > Historial):** La ficha leída de PostgreSQL es la verdad absoluta en el milisegundo actual. Si el usuario actualizó su nombre, rol o enlace, el LLM tiene la instrucción estricta de IGNORAR el historial antiguo de Valkey y confirmar de inmediato la información actualizada, prohibiendo alucinaciones como "los cambios tardan unos minutos en sincronizarse".
- **Deduplicación Preventiva de Leads:** Las búsquedas telefónicas emplean normalización de variantes y coincidencia de sufijo de 10 dígitos con ordenamiento por completitud (`alias_nombre IS NOT NULL`) y recencia. La inserción de nuevos leads verifica la existencia previa antes de crear filas para no fragmentar identidades con números sin prefijo `+`.
- **Esquema Relacional Sincronizado:** Toda tabla de usuarios y afiliados debe contar con columna `updated_at TIMESTAMPTZ DEFAULT NOW()` para evitar excepciones en rutas de actualización del perfil web.

### 8. Protocolo de Desmantelamiento y Limpieza en la Aplicación Web (`webdev`/`webprod`):
Una vez que el worker `whatsappbot` esté verificado y recibiendo el tráfico de Evolution Go:
- **Archivos a purgar en el frontend:**
  * `src/pages/api/webhooks/whatsapp.ts`: Reducir a un forwarder ultraliviano a NATS o worker directo (`fetch("http://whatsappbot:3005/webhook", ...)`).
  * `src/services/bot-knowledge.ts`: Purgar completamente (elimina el array estático de 15KB y lógica pesada).
  * `tests/whatsapp_bot_sota.test.ts` y `tests/bot_knowledge.test.ts`: Migrar a la suite del nuevo microservicio.
- **Archivos a preservar en el frontend:**
  * `src/services/evolution.ts` y `src/services/notifications.ts`: Permanecen activos para las alertas y confirmaciones transaccionales de compra de entradas/reservas web.
- **Certificación de paridad limpia:**
  * Compilar y testear en `webdev` (`bun run build && bun test`) certificando exit code 0.
  * Promover a `webprod` para erradicar cualquier residuo zombi del frontend.

---

## 24. Ecosistema Universal Ads-First, Pixel-First & Outbox Telemetry

Toda solución web y marca en Zerops implementa el estándar unificado de telemetría y conversión definido en [`template-universal-ads-and-telemetry.md`](file:///var/www/artifacts/templates/template-universal-ads-and-telemetry.md), orquestado por la skill [`ad-telemetry`](file:///var/www/.agents/skills/ad-telemetry/SKILL.md) y los contratos `@astrobranding/contracts`:

### 1. Triangulación Publicitaria Multi-Red (Meta + Google + TikTok)
- **Meta Conversions API (CAPI) + Píxel Web:** Deduplicación estricta por tupla `(event_name, event_id)` con hashing SHA-256 en servidor (`em`, `ph`, `client_ip_address`, `client_user_agent`).
- **Google Ads Enhanced Conversions:** Soporte nativo para Consent Mode v2 (`ad_storage`, `ad_user_data`, `ad_personalization`, `analytics_storage` en `'denied'` por defecto antes del consentimiento del usuario).
- **TikTok Events API v1.3:** Trazabilidad determinista con `ttclid` de 1st-party cookie.

### 2. Regla de Oro: Núcleo Técnico en Inglés, Vistas e Interfaz en Español
- **Núcleo Técnico (Inmutable):** Tablas de base de datos (`offerings`, `task_outbox`, `orders`), eventos de telemetría (`Purchase`, `AddToCart`, `Lead`), contratos TypeScript y colas NATS/Valkey se nombran estrictamente en **inglés**.
- **Interfaz Humana & Frappe/CRM (100% en Español):** Vistas para clientes, formularios, catálogos en tienda, tableros de anuncios (Business Manager, Google Ads en español) y DocTypes de Frappe Desk (*Factura de Venta*, *Clientes*, *Pedidos*) se presentan en **español** para máxima usabilidad.

### 3. Agnosticismo de Presencia (SAB vs Storefront Físico)
- **Local Físico (`physical_storefront`):** Expone Schema.org `Store`/`LocalBusiness` con dirección postal completa y coordenadas para Google Business Profile.
- **Negocio de Área de Servicio (`service_area_business`, SAB):** Oculta dirección residencial para proteger privacidad; declara `areaServed` y `serviceType` evitando rechazos de verificación y suspensiones automáticas en Google y Meta.

### 4. 6 Arquetipos Universales de Oferta & Mapeo a Frappe DocTypes
Los productos o servicios se tipifican en 6 arquetipos (`offerings.ts`), mapeándose a través de `getFrappeMappingForArchetype()`:
- `physical_goods` $\to$ DocType `Sales Order` + feed XML de catálogo.
- `courses_education` $\to$ DocType `Sales Invoice` + enrolamiento en LMS.
- `memberships_mrr` $\to$ DocType `Subscription` / `Sales Invoice` recurrente.
- `events_ticketing` $\to$ DocType `Sales Invoice` + ticket/QR emitido.
- `digital_products` $\to$ DocType `Sales Invoice` + link de descarga segura.
- `service_bookings` $\to$ DocType `CRM Lead` / `Opportunity` + webhook de calendario.

### 5. Puente Outbox Transaccional Desacoplado para Frappe / ERPNext
- **Persistencia Atómica:** La tienda guarda pedidos y señales en `task_outbox` en la misma transacción ACID de PostgreSQL 18.
- **Cero Bloqueo:** El worker `drainTaskOutbox` procesa las tareas asíncronamente. Si Frappe Cloud está en mantenimiento, en espera de activación o responde 403/502, el checkout jamás se interrumpe y las tareas se reintentan con retroceso exponencial.





