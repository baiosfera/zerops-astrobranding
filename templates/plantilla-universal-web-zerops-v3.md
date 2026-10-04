# 🌐 PLANTILLA UNIVERSAL WEB ZEROPS (v3.0.0) — MASTER BLUEPRINT

> **Clasificación:** Blueprint Canónico Universal para Despliegues Web Soberanos en Zerops  
> **Versión:** 3.0.0 (SemVer Canónico)  
> **Gobernanza:** [`Supreme Directive`](file:///var/www/.agents/rules/00-SUPREME-DIRECTIVE.md) & [`Planner`](file:///var/www/.agents/skills/planner/SKILL.md)  
> **Stack Base:** Astro 5 SSR (Bun 1.3.9+ / Tailwind CSS 4) + PostgreSQL 18 + Valkey 7.2 + NATS 2.12 + Object Storage S3 + Bifrost AI Gateway + EvolutionGo + Listmonk  
> **Propósito:** Guía de ejecución autónoma para que cualquier agente AGY despliegue una aplicación web, e-commerce o landing para CUALQUIER marca, producto o tema sin ensayos, sin errores y sin acoplamientos residuales.

---

## 1. Declaración de Identidad Agnóstica & Variables Soberanas

Todo nuevo despliegue adopta su identidad dinámicamente mediante variables de entorno en Zerops (`zerops_env`), erradicando cualquier valor quemado en código:

| Variable | Descripción / Formato | Ejemplo en Producción |
|---|---|---|
| `PROJECT_NAME` | Identidad humana de la marca | `"Glamur AI"` / `"Lumina Shoes"` |
| `APP_IDENTITY` | Slug normalizado en minúsculas (sin espacios) | `"glamur"` / `"luminashoes"` |
| `CLIENT_DOMAIN` | Dominio público principal | `"glamur.ai"` / `"tienda.com"` |
| `PUBLIC_BRAND_NAME` | Nombre visible para el cliente | `"Glamur"` |
| `PUBLIC_CONTACT_EMAIL` | Correo oficial de atención | `"contacto@glamur.ai"` |
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
2. **`localstorage` (`/mnt/localstorage/`):** Capa Caliente POSIX con semántica nativa mononúcleo. Reservada para SQLite embebido (`engram`, `freellmapi`), sockets y archivos de configuración en caliente. Los activos multimedia pesados se canalizan a Object Storage.
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

## 4. Anti-Slop Craft Obligatorio (Web, Email y WhatsApp)

Todo producto construido bajo esta plantilla debe verse, sentirse y leerse como una obra diseñada y redactada por humanos de alto nivel, erradicando los clichés de IA:

### A. Frontend Web (Astro 5 + Tailwind 4)
- **Activación de Habilidades:** Mandatorio consultar [`taste-skill`](file:///var/www/.agents/skills/taste-skill/SKILL.md) e [`impeccable`](file:///var/www/.agents/skills/impeccable/SKILL.md).
- **Calibración de los 3 Diales:**
  * `DESIGN_VARIANCE: 8` — Asimetría intencional, grillas editoriales quebradas, composiciones tipográficas ricas.
  * `MOTION_INTENSITY: 6` — Microinteracciones de entrada suaves y físicas, transiciones sutiles con aceleración natural.
  * `VISUAL_DENSITY: 4` — Espaciado amplio y elegante, respiro visual de alta gama.
- **Directivas de Estilo Humano:**
  * Seleccionar paletas ricas en OKLCH derivadas de `brandbook.json` en sustitución de gradientes morados estándar.
  * Diseñar bloques de contenido asimétricos con jerarquía dinámica en lugar de trípticos de tarjetas iguales.
  * Emparejar fuentes display con tipografías grotesk contemporáneas en lugar de la combinación estándar Inter/Slate.
  * Redactar copys persuasivos y específicos mediante neurocopywriting, reemplazando declaraciones corporativas vacías.

### B. Correo Transaccional (React Email 3.0 Compilador Único)
- **Un Solo Diseñador:** React Email (`.tsx`) es la única fuente de verdad para correos.
- **Inyección en Listmonk (`POST /api/templates`):** Para campañas o envíos vía `/api/tx`, los tags Sprig de Go se insertan en JSX (`{'{{ .Tx.Data.order_id }}'}`). React Email compila a HTML 100% inline (<85 KB anti-clipping de Gmail) y se registra en Listmonk automáticamente.
- **Envío Directo Transaccional (ZeptoMail / SES v2):** La misma plantilla se evalúa en runtime en Bun con props de TypeScript (`renderAsync(<OrderEmail order={order} />)`), entregando en <80ms.
- **Tokens de Marca:** Carga dinámica de colores y tipografías desde `brandbook.json` usando `loadEmailBrandTokens()`.

### C. Canal WhatsApp (EvolutionGo + Bifrost)
- **Tono Concierge Humano:** El bot actúa como un miembro calificado del equipo de atención de la marca.
- **Voz Auténtica:** Abrir las conversaciones con cercanía, resolviendo la necesidad inmediata del usuario sin frases prefabricadas sobre inteligencia artificial.
- **Neurocopywriting:** Respuestas directas, cálidas y concisas, orientadas a facilitar la decisión de compra o clarificar inquietudes al instante.

---

## 5. Protocolo de Aislamiento Multi-Proyecto en Linear

Para crear las tareas de una nueva marca sin contaminar proyectos existentes:

1. **Inspección Previa vía GraphQL:**
   ```bash
   curl -s -H "Authorization: $LINEAR_API_KEY" -H "Content-Type: application/json" \
     -d '{"query":"query { teams(first: 5) { nodes { id name key projects(first: 10) { nodes { id name state } } } } }"}' \
     https://api.linear.app/graphql
   ```
2. **Creación del Proyecto Dedicado:**
   Crear un `projectId` nuevo con el nombre de la marca (ej: `"[Glamur] E-Commerce & Growth Engine"`).
3. **Las 5 Issues Canónicas de Marca:**
   - `[Brand] BAI-0: Infraestructura & AI Gateway (Bifrost + FreeLLMAPI)`
   - `[Brand] BAI-1: Chasis Astro 5 SSR, Brandbook Tokens & GitOps CI/CD`
   - `[Brand] BAI-2: Landings & Anti-Slop Craft con Taste-Skill`
   - `[Brand] BAI-3: Persistencia PostgreSQL, React Email & WhatsApp Concierge`
   - `[Brand] BAI-4: Funnels de Checkout, Pasarelas & Automatizaciones`
4. **Ejecución Acotada:** El agente toma una issue a la vez ($\le 15.000$ tokens), valida físicamente con sensor en terminal (Exit Code 0) y marca `Done` antes de pasar a la siguiente.

---

## 6. GitOps Delivery Canónico (Opción B `ghcicd`)

- **Desarrollo en Zerops:** Todo el trabajo iterativo ocurre en el contenedor efímero `webdev` de Zerops (`/var/www/{hostname}` con hot-reload y subdominios).
- **Producción Inmutable:** Los despliegues a producción se realizan exclusivamente a través de GitHub Actions (`zeropsio/actions@v1.0.2`) al hacer push a la rama `main`, conectado a Cloudflare con SSL Full Strict.
- **Staging Desacoplado y Opcional:** La receta base `06-astro-web.yaml` despliega únicamente el servicio de producción. El entorno staging (`06b-astro-web-staging.yaml`) es estrictamente opt-in para proyectos con QA formal.
- **Cero Costo en Reposo:** Cuando el desarrollo activo concluye, el contenedor de desarrollo puede eliminarse o detenerse; la verdad indestructible reside en el repositorio GitHub (`main`) y en Google Drive SSoT.

---

## 7. Verificación Física & Sensores de Calidad (Exit Code 0)

Antes de dar por entregado cualquier despliegue bajo esta plantilla, el agente debe ejecutar físicamente y comprobar el código de salida 0 de:
1. `skills-suite-validate` — Certificación del catálogo completo de skills.
2. `ssot-parity-check` — Atestación de paridad sin drift entre el contenedor ZCP y Google Drive SSoT.
3. `/health` HTTP 200 — Comprobación física de conectividad de cada servicio desplegado.

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
   - Mensajería: Correo y WhatsApp con voz cálida y bienvenida a la comunidad.
2. **Formulario de Alianzas y Contratación B2B (`AllianceForm.astro`):**
   - Propósito: Co-producción, alquiler de locación privada o talleres de facilitadores.
   - Campos: Nombre/Organización, WhatsApp, Email, Selector de Tipo de Alianza (Organizador de Eventos, Tallerista, Producción, Alquiler Privado), Textarea amplio para detallar la propuesta, Ciudad.
   - **Invariante:** CERO preguntas de modalidad íntima (`pareja` o `single`).
   - Mensajería: Confirmación de recepción curatorial y notificación prioritaria a la dirección de la marca.
3. **Formulario de Checkout & Admisión VIP (`CheckoutForm.astro`):**
   - Propósito: Adquisición de entradas, pases o separación de cupos.
   - Campos: Selector de pases, modalidad de pago (Total o Separación de Cupo), datos de contacto, pasarela de pago segura.

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
