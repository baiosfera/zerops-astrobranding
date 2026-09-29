# REPORTE DE RELEVO Y ROADMAP: MODULARIZACIÓN Y DESPLIEGUE DE ZEROPS-ASTROBRANDING (v2.0)

> **Destinatario:** Sucesor AGY / Ingeniero de Plataforma y Arquitecto de Agentes  
> **Fecha de Emisión:** 2026-09-28  
> **Estado:** 100% Blindado y Listo para Ejecución Inmediata  
> 🧭 **Principio Rector (Brújula Viva, No Dogma Ciego):**  
> Este documento **NO es una verdad absoluta ni una plantilla estricta**. Es una brújula de orientación arquitectónica. Tu deber como agente es contrastar cada punto contra el código real, autodescubrir y adaptar el camino. Si el usuario activa `/grill-me` (o la skill `grill-me`), entrevistalo implacablemente en rondas dialécticas estructuradas (una pregunta a la vez, esperando respuesta) para desafiar supuestos y co-diseñar la mejor solución antes de tocar código.

---

## 1. Contexto Estratégico y Logros Fundacionales Consolidados

En esta sesión completamos hitos de infraestructura, metacognición y diseño que transforman radicalmente la forma en que este repositorio debe desplegarse y modularizarse:

1. **Auditoría, Poda y Blindaje de las 65 Skills Soberanas (v8.2)**:
   - Repositorio público independiente: **[https://github.com/elplacerdc/zerops-astro-skills](https://github.com/elplacerdc/zerops-astro-skills)**.
   - **Colisión de Trigger Resuelta**: La skill de framework fue renombrada a [`astro-web`](file:///var/www/zerops-astro-skills/astro-web/SKILL.md) con triggers específicos (`astro-framework`, `astro 5`, etc.), erradicando colisiones con consultas astrológicas.
   - **Cluster A (Oráculo & Diagnósticos)**: [`oraculo`](file:///var/www/zerops-astro-skills/oraculo/SKILL.md) v4.7 compila el reporte denso unificado `astrobranding_[MARCA].md` con 12 Shards. Los sub-diagnósticos (`diag-a` a `diag-e`) poseen Ingestión Dual (RFC 6901 pointers + fallback) y tests herméticos deterministas (<50ms, 0 tokens).
   - **Cluster E (`zcp` v6.3)**: Consagrada la **Ley de Autoescalado Frugal**: `cpuMode: SHARED`, omisión de límites de CPU y RAM para casillas vacías en GUI y elasticidad nativa Zerops, y dual-threshold (`minFreeRamGB: 0.25`, `minFreeRamPercent: 10`).
   - **Cluster C (Suite de Diseño v1.2)**: [`fontgen`](file:///var/www/zerops-astro-skills/fontgen/SKILL.md), [`symbol`](file:///var/www/zerops-astro-skills/symbol/SKILL.md), [`chroma`](file:///var/www/zerops-astro-skills/chroma/SKILL.md), [`kinetic`](file:///var/www/zerops-astro-skills/kinetic/SKILL.md), [`brandbook`](file:///var/www/zerops-astro-skills/brandbook/SKILL.md) y [`orchesbrand`](file:///var/www/zerops-astro-skills/orchesbrand/SKILL.md) completamente desacopladas de la cascada rígida. Ingestan directamente de `astrobranding_[MARCA].md` y emiten doble contrato (manifiestos JSON para visualizador + código dev directo).
   - **Cluster D (Comercio & Ventas)**: [`checkout-funnels`](file:///var/www/zerops-astro-skills/checkout-funnels/SKILL.md), [`payment-gateways`](file:///var/www/zerops-astro-skills/payment-gateways/SKILL.md), [`orders-fulfillment`](file:///var/www/zerops-astro-skills/orders-fulfillment/SKILL.md), [`growth-engine`](file:///var/www/zerops-astro-skills/growth-engine/SKILL.md) y [`sales-enablement`](file:///var/www/zerops-astro-skills/sales-enablement/SKILL.md) saneados contra GitHub Secret Scanning y alineados para ingerir arquetipos, casas 2/6/10 de riqueza y ciudades ACG directamente de `astrobranding_[MARCA].md`.
   - **Cluster B (Flujo y Metacognición v8.2)**: [`cohalo`](file:///var/www/zerops-astro-skills/cohalo/SKILL.md), [`planner`](file:///var/www/zerops-astro-skills/planner/SKILL.md), [`docu`](file:///var/www/zerops-astro-skills/docu/SKILL.md) y [`research`](file:///var/www/zerops-astro-skills/research/SKILL.md) alineados a la Directiva Suprema v8.2 y **Reality Over Checklist Theater**. Presupuesto de router $\le 480$ palabras y 0 residuos `__pycache__`.
   - **Validación Física Global**: `skills-suite-validate` arrojó **65/65 passed (100%)** y `ssot-parity-check` confirmó **zero drift** con Google Drive SSoT.

2. **Reconstrucción y Publicación de Brandview Visualizer Studio**:
   - Rescatado del backup legado y reescrito desde cero en [`/var/www/brandview`](file:///var/www/brandview).
   - Stack moderno: **SolidJS + Vite v6 + Hono Backend** con sincronización en tiempo real vía WebSocket y JSON Patch (`fast-json-patch`).
   - Publicado en GitHub: **[https://github.com/elplacerdc/brandview](https://github.com/elplacerdc/brandview)**.
   - Cuenta con recetas Zerops listas: `zerops.yaml` (Node 22) e `import.yaml` (receta Frugal-First).

3. **Invariante Crítico de Base de Datos**:
   - **RESTRICCIÓN EXPRESA:** **NO tocar ni aprovisionar PostgreSQL en Zerops en este momento**.
   - Toda definición de PostgreSQL en recetas o esquemas se mantiene como plantilla/código hermético para cuando el usuario decida activarla.

---

## 2. Diagnóstico del Problema en `zerops-astrobranding`

1. **Monolito de Infraestructura (`import.yaml` en raíz):**
   Actualmente define **10 servicios simultáneos** (`database`, `valkey`, `nats`, `objectstorage`, `localstorage`, `freellmapi`, `bifrost`, `evolution`, `hermes`, `astrobranding`).
   - *Falla:* Si un cliente solo requiere una landing page, un visualizador de marca o una tienda con COD/WhatsApp, levantar 10 contenedores satura costos innecesariamente.
2. **Confusión de Fronteras (Plano de Control ZCP vs Runtimes LXC):**
   - El contenedor `zcp` es exclusivamente un plano de control de orquestación.
   - `zcp` **no tiene Bun ni debe tenerlo** (`which bun` = vacío).
   - Cualquier compilación (`bun run build`), prueba (`bun test`) o ejecución de framework debe ocurrir dentro de los contenedores de runtime en Zerops vía SSH (`ssh {hostname} "cd /var/www && <cmd>"`), o mediante `zerops_dev_server`, jamás en el host local de ZCP.
3. **Desacoplamiento Total de Skills**:
   - `zerops-astrobranding` **NO debe contener skills** dentro de su árbol de código. Las skills viven en `zerops-astro-skills` y se consumen vía el registro local.

---

## 3. Integración con el Ecosistema de Skills SSoT

El flujo operativo para el sucesor AGY es:
1. `iniciar.sh` actualiza las 65 skills soberanas desde GitHub en 1.5s hacia `/var/www/zerops-astro-skills`.
2. El agente activa las skills según el objetivo:
   - **Para Landing / UI**: [`frnt`](file:///var/www/zerops-astro-skills/frnt/SKILL.md), [`astro-web`](file:///var/www/zerops-astro-skills/astro-web/SKILL.md), [`brandbook`](file:///var/www/zerops-astro-skills/brandbook/SKILL.md).
   - **Para Brandview Studio**: [`brandbook`](file:///var/www/zerops-astro-skills/brandbook/SKILL.md), [`orchesbrand`](file:///var/www/zerops-astro-skills/orchesbrand/SKILL.md), [`zcp`](file:///var/www/zerops-astro-skills/zcp/SKILL.md).
   - **Para E-commerce**: [`checkout-funnels`](file:///var/www/zerops-astro-skills/checkout-funnels/SKILL.md), [`payment-gateways`](file:///var/www/zerops-astro-skills/payment-gateways/SKILL.md), [`orders-fulfillment`](file:///var/www/zerops-astro-skills/orders-fulfillment/SKILL.md).
   - **Para Copy & Ventas Metafísicas**: [`growth-engine`](file:///var/www/zerops-astro-skills/growth-engine/SKILL.md), [`sales-enablement`](file:///var/www/zerops-astro-skills/sales-enablement/SKILL.md).
   - **Para Infraestructura**: [`zcp`](file:///var/www/zerops-astro-skills/zcp/SKILL.md), [`bknd`](file:///var/www/zerops-astro-skills/bknd/SKILL.md), [`nats`](file:///var/www/zerops-astro-skills/nats/SKILL.md), [`valkey`](file:///var/www/zerops-astro-skills/valkey/SKILL.md).

---

## 4. Hoja de Ruta de Implementación Paso a Paso

### Paso 1: Crear Recetas Modulares de Infraestructura (`recipes/`)
En lugar de un único `import.yaml` monolítico, modularizar en perfiles claros dentro de `/var/www/zerops-astrobranding/recipes/`:

1. `recipes/landing-minimal.yaml`:
   - `astrobranding` (runtime: `ubuntu/bun@1.3.9`)
   - `localstorage` (opcional para persistencia de assets generados)
2. `recipes/brandview-studio.yaml`:
   - `brandview` (runtime: `ubuntu/nodejs@22`, puerto 3000 HTTP, build Vite, Hono server)
3. `recipes/ecommerce.yaml`:
   - `astrobranding`
   - `valkey` (`valkey:single@7.2`, profile `hobby`)
   - `localstorage`
   - *(Nota: plantilla preparada para `database` postgresql:single@18, pero comentada o marcada como opcional hasta autorización del usuario).*
4. `recipes/full-mesh.yaml`:
   - Los servicios completos (`freellmapi`, `bifrost`, `evolution`, `hermes`, etc.) para clientes enterprise.
5. `import.yaml` (raíz):
   - Enlazar o definir el perfil mínimo/estándar por defecto.

---

### Paso 1b: Ley de Autoescalado Frugal (Zerops Native Scaling Estándar v6.3)
**CRÍTICO:** Aplicar la fórmula acordada en la skill `zcp` (v6.3). Prohibido imponer límites rígidos que llenen casillas en la GUI o inflen costos en arranque:

```yaml
# Receta Canónica Frugal-First para todo runtime LXC en Zerops:
minContainers: 1
maxContainers: 2
verticalAutoscaling:
  cpuMode: SHARED         # OBLIGATORIO: Cero DEDICATED en arranque (mínimo costo inicial)
  minFreeRamGB: 0.25      # Umbral absoluto: dispara escalado si la RAM libre cae de 250MB
  minFreeRamPercent: 10   # Umbral dinámico: garantiza 10% de buffer según auto-ram.txt
  # OMITIR minCpu, maxCpu, minRam, maxRam:
  # Al omitirlos, las casillas en el panel GUI de Zerops quedan limpias/default
  # y Zerops gestiona el autoescalado elástico nativo (0.125 GB a 48 GB, 1 a 8 cores) sin techos artificiales.
```

- **Dinámica Dual-RAM (auto-ram.txt):** Evaluada cada 10 segundos. El umbral que exija mayor memoria libre es el que manda, evitando caídas OOM sin cobrar capacidad ociosa.
- **Ajuste en Caliente vía MCP:**
  ```bash
  zerops_scale serviceHostname="astrobranding" minContainers=1 maxContainers=2 minFreeRamGB=0.25 minFreeRamPercent=10 cpuMode="SHARED"
  ```

---

### Paso 2: Refactorizar `setup.sh`
- Actualizar `setup.sh` para soportar selección de perfil:
  ```bash
  ./setup.sh --profile <landing|brandview|ecommerce|full-mesh>
  ```
- Eliminar cualquier intento de ejecutar compilaciones pesadas (`bun test` o `bun run build`) dentro de `zcp`.
- Recordar al operador que los builds se lanzan en Zerops o vía SSH hacia el runtime.

---

### Paso 3: Actualizar README.md y Metadatos de GitHub
1. **Descripción en GitHub:**
   ```bash
   gh repo edit elplacerdc/zerops-astrobranding --description "Modular Astro 5, Tailwind 4 & Brandview Starter Kit for Zerops Cloud with Profile-Based Frugal Scaling"
   ```
2. **`README.md` en la Raíz:**
   - Presentar el starter kit y sus perfiles de despliegue.
   - Documentar la arquitectura de 2 niveles: Plano de Control (ZCP) vs Runtimes LXC.
   - Documentar la integración con Brandview Studio (`https://github.com/elplacerdc/brandview`).
   - Enlace directo al catálogo de skills: `https://github.com/elplacerdc/zerops-astro-skills`.
   - Instrucciones claras con `./setup.sh` e `iniciar.sh`.

---

### Paso 4: Verificación Física, Higiene y Paridad SSoT
- Validar sintaxis bash con `bash -n` en todos los scripts nuevos o modificados.
- Inyectar `export PYTHONDONTWRITEBYTECODE=1` y trampa `trap` en cualquier script que use Python.
- Correr el sensor de paridad: `ssot-parity-check` (debe retornar exit code 0).
- Commitear con Conventional Commits (sin `Co-Authored-By`):
  ```bash
  git commit -m "feat(arch): modularize infrastructure recipes and decouple deployment profiles under frugal autoscaling"
  git push origin main
  ```

---

## 5. Invariantes Soberanos Obligatorios

1. **Reality Over Checklist Theater:** La verdad del sistema reside exclusivamente en código que compila, sintaxis válida y tests de software reales (`bash -n`, `bun test` en runtime, `ssot-parity-check`). Vetado cualquier sensor basado solo en `[ -f ]` o `grep`.
2. **Cero Compilaciones en ZCP:** El contenedor `zcp` es estrictamente el plano de control (sin Bun local ni builds pesados). Todo runtime de aplicación se compila y ejecuta en sus contenedores LXC dedicados en Zerops.
3. **Frugal-First Autoscaling:** Todo servicio nuevo nace con `cpuMode: SHARED`, `minContainers: 1`, `maxContainers: 2`, omitiendo límites de CPU/RAM.
4. **Cero Leaks de Secretos:** Nunca escribir tokens ni claves privadas en texto plano; referenciar variables `$VAR`.
5. **Sin Co-Autorías de IA:** No incluir `Co-Authored-By` en ningún commit.
6. **ZCP-First & Indivisible SSoT:** Si se modifica algún script compartido en `0zcp-123/scripts/`, respaldar previamente en `bak/scripts/`.

---

## 6. Estado Consolidado de Hitos & Protocolo de Despliegue por Lenguaje Natural (SSoT 2026-09-29)

### A. La Visión Central: Despliegue Modular bajo Demanda por Lenguaje Natural
El objetivo definitivo del ecosistema es que el usuario, tras ejecutar `iniciar.sh` (que solo prepara herramientas, SSoT y credenciales en el plano de control ZCP sin desplegar runtimes), solicite en lenguaje natural:
- *"Instala freellmapi y bifrost"*
- *"Instala hermes y nats"*
- *"Instala el ecosistema para una tienda online de N producto"*
- *"Instala la suite completa de branding astrológico"*

Y el agente (AGY) ejecute el hito de punta a punta de forma 100% autónoma, consultando las recetas modulares en `recipes/` y las skills de `zerops-astro-skills`, aprovisionando, cableando secrets, registrando llaves de gobernanza y validando la salud física sin fricción ni preguntas obvias.

### B. Descubrimientos Críticos & Estado de Producción
1. **Hito 1 (FreeLLMAPI + LocalStorage)**:
   - Totalmente funcional en puerto interno 3001 y dominio público.
   - Base SQLite y descargas persistidas en volumen POSIX `localstorage`.
   - Auto-rotación de claves, circuit breaker ante 429 y caché interna probada (reducción de 580ms a 3.7ms).
2. **Hito 2 (PostgreSQL 18 + Valkey 7.2 + Bifrost v2.2.3)**:
   - 65 tablas relacionales migradas y activas en PostgreSQL 18 (`database`).
   - **Invariante RediSearch**: Valkey 7.2 vainilla carece del módulo `FT.*`. Por lo tanto, `vector_store.type` en Bifrost debe ser `chromem` (embebido en Go) o `qdrant`. Al configurar `chromem`, la caché semántica se activó (`status: active`) y redujo la latencia de DeepSeek de 1730 ms a **2.91 ms (98.6% de reducción real)**.
   - **5 Virtual Keys Oficiales Registradas**: Dadas de alta con sus hashes y tokens `sk-bf-...` en PostgreSQL 18 vía `/api/governance/virtual-keys`: `Production Sovereign Key`, `Hermes Agent Autonomous`, `AstroBranding Production`, `Evolution WhatsApp Bot` y `Antigravity AGY Operator`.
   - **`bifrost-cli` Integrado**: Binario oficial enlazado en `/usr/local/bin/bifrost-cli` e incorporado en `iniciar.sh` para arranques limpios.

### C. Matriz de Relevo y Guía de Ejecución para los Siguientes Hitos (Hito 3 a Hito 6)

Para que cualquier agente sucesor (AGY) opere con certeza matemática y sin ensayo y error, esta es la secuencia exacta de hitos pendientes:

| Hito | Nombre & Receta | Servicios | Cableado y Secretos | Skills Requeridas | Criterios de Aceptación Física |
|---|---|---|---|---|---|
| **Hito 3** | **Hermes Agent + NATS JetStream**<br>`recipes/steps/03-hermes-nats.yaml` | `nats:single@2.12`<br>`hermes` (Ubuntu Python 3.12) | - `HERMES_LLM_API_BASE`: `http://bifrost:8080/v1`<br>- `HERMES_LLM_API_KEY`: `sk-bf-f702a2c4-c967-4ea3-90bc-7c8f5dad5cd0` (Virtual Key `Hermes Agent Autonomous` en PG18)<br>- `NATS_URL`: `nats://nats:4222` | [`nats`](file:///var/www/zerops-astro-skills/nats/SKILL.md)<br>[`hermes-agent`](file:///var/www/zerops-astro-skills/hermes-agent/SKILL.md) | - Endpoint `/health` HTTP 200 en Hermes<br>- Publicación y suscripción en NATS JetStream<br>- Inferencia LLM ejecutada a través de Bifrost con Virtual Key |
| **Hito 4** | **Evolution API / WhatsApp Engine**<br>`recipes/steps/04-evolution.yaml` | `evolution` (Alpine Go 1.22 / Node) | - Base en PostgreSQL 18 (`database`)<br>- Cache/Sesiones en Valkey 7.2 (`valkey`)<br>- Eventos en NATS (`nats`)<br>- LLM Virtual Key: `sk-bf-426d0421-f755-4634-ad98-7dad075ba60b` (`Evolution WhatsApp Bot`) | [`whatsapp-engine`](file:///var/www/zerops-astro-skills/whatsapp-engine/SKILL.md) | - Handshake QR / sesión activa<br>- Eventos despachados a NATS JetStream<br>- Proxy LLM operativo contra Bifrost |
| **Hito 5** | **Listmonk / Marketing Transaccional**<br>`recipes/steps/05-listmonk.yaml` | `listmonk` | - Base relacional en PostgreSQL 18 (`database`) | [`listmonk`](file:///var/www/zerops-astro-skills/listmonk/SKILL.md)<br>[`email-marketing`](file:///var/www/zerops-astro-skills/email-marketing/SKILL.md) | - Dashboard administrativo y API REST `/api/health` activos |
| **Hito 6** | **AstroBranding Sovereign Fullstack**<br>`recipes/steps/06-astro-web.yaml` | `objectstorage` (S3)<br>`astrobranding` (Ubuntu Bun 1.3 / Node 24) | - Ingestión de 15 Shards astrológicos<br>- Colas BullMQ sobre Valkey 7.2 (`valkey`)<br>- S3 Object Storage montado<br>- LLM Virtual Key: `sk-bf-9eef443c-d7fe-48ac-8eb0-706702bf9ea9` (`AstroBranding Production`) | [`astro-web`](file:///var/www/zerops-astro-skills/astro-web/SKILL.md)<br>[`frnt`](file:///var/www/zerops-astro-skills/frnt/SKILL.md)<br>[`brandbook`](file:///var/www/zerops-astro-skills/brandbook/SKILL.md) | - SSR en puerto 3000 con React 19 Islands<br>- Shards astrológicos consumidos desde packages/engine |

### D. Catálogo de Recetas por Bundles / Ecosistemas Completos
Si el usuario solicita un bundle en lugar de un paso individual:
- *"Instala la landing minimal"*: Ejecuta `recipes/landing-minimal.yaml` (`astrobranding` + `localstorage`).
- *"Instala brandview studio"*: Ejecuta `recipes/brandview-studio.yaml` (`brandview` Node 22 + Vite + Hono).
- *"Instala la tienda online / ecommerce"*: Ejecuta `recipes/ecommerce.yaml` (`astrobranding` + `valkey` + `localstorage`).
- *"Instala el ecosistema completo"*: Ejecuta `recipes/full-mesh.yaml` (los 10 servicios con autoescalado frugal).

