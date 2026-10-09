# 🌐 PLANTILLA UNIVERSAL WEB ZEROPS (v4.1.0) — MASTER BLUEPRINT

> **Clasificación:** Blueprint Canónico Universal para Despliegues Web Soberanos en Zerops  
> **Versión:** 4.1.0 (SemVer Canónico — Hardening Audiovisual, Dual-Testing, FUSE Hygiene & Batch Linear)  
> **Gobernanza:** [`Supreme Directive`](file:///var/www/.agents/rules/00-SUPREME-DIRECTIVE.md), [`Planner`](file:///var/www/.agents/skills/planner/SKILL.md) & [`Skill-Improver`](file:///var/www/.agents/skills/skill-improver/SKILL.md)  
> **Stack Base:** Astro 5 SSR (Bun 1.3.9+ / Tailwind CSS 4) + PostgreSQL 18 + Valkey 7.2 + NATS 2.12 + Object Storage S3 + Bifrost AI Gateway + EvolutionGo + Listmonk  
> **Propósito:** Guía de ejecución autónoma para que cualquier agente AGY despliegue una aplicación web, e-commerce o landing para CUALQUIER marca, producto o tema tanto en proyectos nuevos desde cero (*Greenfield*) como en adopción de repositorios preexistentes (*Brownfield*), sin ensayos, sin errores y con dependencias bloqueantes en Linear.

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

## 2. Taxonomía Soberana de Almacenamiento (Las 4 Capas Indivisibles)

Cualquier AGY debe clasificar y persistir los datos estrictamente en su capa designada:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TAXONOMÍA DE ALMACENAMIENTO ZEROPS                   │
├─────────────────┬─────────────────┬──────────────────┬─────────────────┤
│ 1. GDRIVE SSoT  │ 2. LOCALSTORAGE │ 3. OBJECTSTORAGE │ 4. POSTGRESQL   │
│ (Capa Fría)     │ (Capa Caliente) │ (Capa Medios S3) │ (Capa ACID Rel) │
├─────────────────┼─────────────────┼──────────────────┼─────────────────┤
│ • Repositorios  │ • SQLite Engram │ • Fotos producto │ • Tablas leads  │
│ • brandbook.json│ • FreeLLMAPI db │ • PDFs facturas  │ • Tablas orders │
│ • Esquemas SQL  │ • Sockets POSIX │ • Assets >500KB  │ • Bifrost logs  │
│ • Backups bak/  │ • Caché disco   │ • S3 forcePath   │ • Listmonk PG   │
└─────────────────┴─────────────────┴──────────────────┴─────────────────┘
```

1. **Google Drive SSoT (`/var/www/baiosfera/`):** Capa Fría indestructible. Espejo permanente de código fuente, configuraciones maestras y manifiestos de diseño.
2. **`localstorage` (`/mnt/localstorage/`):** Capa Caliente POSIX con semántica nativa mononúcleo. Reservada para SQLite embebido (`engram`, `freellmapi`), sockets y archivos de configuración en caliente.
   > **Regla de Gobernanza:** Un proyecto en Zerops representa una única marca. Está prohibido subdividir el almacenamiento creando carpetas intermedias (ej: `/proyectos/`). Los directorios de la marca se alojan directamente en la raíz (ej: `/var/www/localstorage/<APP_IDENTITY>`).
3. **`objectstorage` (S3 MinIO):** Capa de Medios Públicos y Dinámicos. Toda imagen de catálogo, avatar de usuario o PDF generado en runtime reside aquí, configurado con `forcePathStyle: true` y expuesto vía Cloudflare CDN.
4. **`postgresql` (PostgreSQL 18):** Capa Relacional Transaccional ACID. Tablas de negocio (`clients`, `orders`, `outbox`), esquemas aislados para Listmonk (`search_path=listmonk,public`) y EvolutionGo (`evogo_auth`, `evogo_users`).

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

### Características de Operación:
- **Endpoint Drop-In:** `http://bifrost:8080/v1` (compatible 100% con SDK de OpenAI).
- **Semantic Cache:** Caché vectorial en memoria; consultas repetidas responden en **<2ms con costo $0**. Key dinámica: `${APP_IDENTITY}-cache`.
- **Failover Inteligente:** Si el proveedor principal arroja `429 Too Many Requests`, Bifrost conmuta en sub-milisegundos hacia FreeLLMAPI (:3001) o modelos secundarios sin interrumpir la experiencia de usuario.

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

### Matriz de Perfiles de Despliegue (`--profile`)

Para evitar arquitecturas carcelarias o forzar servicios innecesarios en proyectos sencillos, el scaffolder soporta 4 perfiles modulares:

1. **`minimal` (Landing Estática / Portfolio / Presencia Básica):**
   - Hitos seleccionados: `BAI-0` $\to$ `BAI-1` $\to$ `BAI-3` $\to$ `BAI-6`.
   - Infraestructura: Solo Astro 5 SSR en Bun (cero PostgreSQL, Valkey, NATS o IA satélite ociosos).
2. **`content` (Portal de Contenidos / Blog / Captura de Leads / Reservas):**
   - Hitos seleccionados: `BAI-0` $\to$ `BAI-1` $\to$ `BAI-2` $\to$ `BAI-3` $\to$ `BAI-6`.
   - Infraestructura: Astro 5 SSR + PostgreSQL 18 + S3 Object Storage. Persistencia antes de UI.
3. **`ecommerce` (Tienda Online / Checkout / Venta de Entradas):**
   - Hitos seleccionados: `BAI-0` $\to$ `BAI-1` $\to$ `BAI-2` $\to$ `BAI-3` $\to$ `BAI-4` $\to$ `BAI-6`.
   - Infraestructura: Astro 5 SSR + PostgreSQL 18 + Valkey 7.2 (idempotencia y locks) + S3 Object Storage.
4. **`full-mesh` (Ecosistema Omnicanal Completo con IA y Mensajería):**
   - Hitos seleccionados: Todos (`BAI-0` a `BAI-6`).
   - Infraestructura: Astro 5 SSR + PostgreSQL 18 + Valkey 7.2 + NATS 2.12 + S3 + Bifrost Gateway (:8080) + EvolutionGo (:8085) + Listmonk (:9000).

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

## 10. Contrato Canónico de Evolution Go en Zerops (:8085)

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
