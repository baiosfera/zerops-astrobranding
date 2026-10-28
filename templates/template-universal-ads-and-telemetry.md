# 🚀 PLANTILLA MAESTRA: ECOSISTEMA UNIVERSAL DE ANUNCIOS, TELEMETRÍA TRI-RED Y BRIDGE FRAPPE (v1.0 SOTA)

> **Destino:** Cualquier marca, cliente, tienda o servicio en Zerops (`${PROJECT_NAME}`).  
> **Ubicación Canónica (Monorepo):** `/var/www/zerops-astrobranding/templates/template-universal-ads-and-telemetry.md`  
> **Ubicación SSoT (Google Drive):** `/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/artifacts/templates/template-universal-ads-and-telemetry.md`  
> **Gobernanza:** `00-SUPREME-DIRECTIVE.md` (v8.5) · `ad-telemetry` · `meta-skill` · `meta-script` · `codecraft`  
> **Principios Soberanos:** Cero Hardcoding, Iniciar.sh-First, Motor en Inglés / Pantallas en Español, Desacople a Prueba de Fallos (Fail-Safe Decoupling).

---

## 1. Topología del Sistema Agéntico Tri-Red

```
                                [ TRÁFICO MULTI-RED ]
                     (Meta Ads / Google Ads / TikTok Ads / Orgánico)
                                       │
                                       ▼
                       [ ASTRO 5 SSR (apps/web en Bun) ]
                        - Captura de Cookie 1st-Party (__attr_session, 90 días)
                        - Google Consent Mode v2 (Default Denied en <head>)
                        - Deduplicación Compartida (event_id: UUIDv7)
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
    [ BROWSER SIGNALS (Pixels) ]                 [ ACID TX EN POSTGRESQL 18 ]
    - Meta Pixel (fbq con eventID)               - Anotación de Compra o Lead
    - Google Tag (gtag con transaction_id)       - Inserción en transactional_outbox
    - TikTok Pixel (ttq con event_id)                         │
                │                                             ▼
                │ (Fallback/Deduplicación)       [ DRENADOR CONCURRENTE (Bun.SQL) ]
                │                                SELECT ... FOR UPDATE SKIP LOCKED
                │                                             │
                └──────────────────────┬──────────────────────┘
                                       ▼
                         [ NATS 2.12 JETSTREAM ]
                         - Deduplicación (duplicate_window: 120s)
                         - Topics: commerce.signals.* / leads.signals.*
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
    [ TELEMETRY WORKER (CAPI) ]                   [ BRIDGE DESACOPLADO FRAPPE ]
    - Meta Conversions API (v21+)                 - Frappe CRM (CRM Lead / Deal)
    - Google Ads Enhanced Conversions             - ERPNext (Sales Order / Invoice)
    - TikTok Events API (v1.3)                    - Modo Fail-Safe (No bloquea la web)
    - Candado Distribuido en Valkey 7.2                        │
                                                               ▼
                                                  [ NOTIFICACIÓN WHATSAPP ]
                                                  - Evolution API (Confirmación / Bot)
```

---

## 2. La Regla de Oro: Motor en Inglés, Pantallas en Español

Para evitar incompatibilidades con las APIs globales y a la vez garantizar una experiencia 100% amigable y sin tecnicismos para el cliente y el operador:

1. **El Motor Interno (Inglés Técnico Estricto):**
   - Base de datos (`PostgreSQL 18`), colas (`NATS JetStream`), caché (`Valkey 7.2`) y llamadas a CAPI se mantienen en inglés universal: `Purchase`, `AddToCart`, `Lead`, `service_bookings`, `physical_goods`.
   - **Por qué:** Meta, Google y TikTok rechazan eventos de optimización que no cumplan con su taxonomía internacional.
2. **Las Pantallas y Contenido (100% Español Natural):**
   - Títulos, descripciones de productos, categorías, monedas (`COP`), textos de botones y correos van en español directo.
   - En **Frappe CRM y ERPNext**, la interfaz visual se configura en Español: `Sales Invoice` se lee **"Factura de Venta"**, `Customer` se lee **"Clientes"**, y `CRM Lead` se lee **"Prospectos"**.

---

## 3. Matriz de los 6 Arquetipos de Oferta & Aislamiento de Canales

Para cumplir con la **Política de Comercio 19 de Meta** y las directrices de **Google Merchant Center**, nunca se mezclan servicios ni productos digitales en el feed de Shopping:

| Arquetipo (`OfferingArchetype`) | Descripción | Canal de Anuncios | Mapeo en Frappe / ERPNext |
|---|---|---|---|
| **`physical_goods`** | Ropa, cosméticos, accesorios con envío físico | Feed XML Maestro (`/api/catalog/feed.xml`) | `Sales Order` (Descuenta inventario en bodega) |
| **`courses_education`** | Talleres, masterclasses, cursos en video | Campañas Web Directas de Conversión | `Sales Invoice` directa (Servicio no inventariable) |
| **`memberships_mrr`** | Membresías VIP, suscripciones recurrentes | Campañas Web Directas (`Subscribe` + `predicted_ltv`) | `Subscription` / Auto-Repeat en ERPNext |
| **`events_ticketing`** | Eventos presenciales, desfiles, boletas | Campañas Web Directas (`CompleteRegistration`) | `Sales Invoice` con código de acceso/QR |
| **`digital_products`** | Ebooks, guías PDF, presets descargables | Campañas Web Directas (`Purchase` digital) | `Sales Invoice` con entrega de enlace/archivo |
| **`service_bookings`** | Citas de maquillaje, atelier, asesorías 1 a 1 | WhatsApp Ads / Formulario de Reserva | `CRM Lead` / `CRM Deal` en Frappe CRM |

---

## 4. Modelo Agnóstico de Presencia de Marca (SAB vs Tienda Física)

El sistema se adapta dinámicamente al perfil del negocio para potenciar el SEO local sin violar las normas de Google Business Profile:

1. **`service_area_business` (SAB - Servicios sin local abierto al público, ej: atención a domicilio):**
   - Genera Schema.org `@type: "ProfessionalService"` con `areaServed: ["Medellín", "Envigado", "Sabaneta"]`.
   - **Oculta la dirección física y no crea pines falsos en Google Maps** (evita la suspensión fulminante de la cuenta de Google).
2. **`physical_storefront` (Tienda o atelier abierto al público):**
   - Genera `@type: "BeautySalon"` o `"Store"` con dirección completa, coordenadas GPS exactas, horarios de apertura y `hasMap` con el CID de Google Maps.
3. **`pure_online_national` / `pure_online_global`:**
   - Genera `@type: "OnlineStore"` u `"Organization"` con políticas de envío y devoluciones a nivel nacional o internacional.

---

## 5. Atribución 1st-Party & Google Consent Mode v2

### A. Invariante de Consent Mode v2 en `<head>`
Todo proyecto debe inyectar el script síncrono antes de cargar GTM o píxeles:
- Inicializa en `denied` las 4 señales: `ad_storage`, `ad_user_data`, `ad_personalization`, `analytics_storage`.
- Si el usuario ya aceptó previamente, lee de `localStorage` y actualiza inmediatamente con `gtag('consent', 'update', ...)`.

### B. Cookie de Atribución Raíz (`__attr_session`, 90 días)
- Almacenada en el dominio raíz (`.tudominio.com`) para viajar entre subdominios (`shop.`, `checkout.`, `@`).
- Captura `first_touch` (origen original) y `last_touch` (campaña de conversión).
- Captura Click-IDs: `gclid`, `gbraid`, `wbraid`, `ttclid` y formatea Meta `fbc` estrictamente como `fb.1.${timestamp}.${fbclid}` (nunca el `fbclid` crudo).
- Se adjunta automáticamente al pedido en `orders.attribution_data`.

---

## 6. Bridge Desacoplado a Frappe CRM y ERPNext (Fail-Safe Decoupling)

La integración con Frappe está construida en modo **Lego desacoplado**:

```typescript
import { getFrappeMappingForArchetype } from '@astrobranding/contracts';

// 1. Cada arquetipo sabe a qué DocType de Frappe apunta
const mapping = getFrappeMappingForArchetype(offering.archetype);

// 2. Si Frappe está configurado y activo:
if (process.env.FRAPPE_URL && process.env.FRAPPE_API_KEY) {
  try {
    await syncToFrappe(mapping, payload);
  } catch (error) {
    // Fail-Safe: Se registra en outbox para reintento posterior, la web NUNCA falla
    console.warn('[Frappe Bridge] Fallback to outbox queue:', error.message);
  }
}
```

* **Si Frappe está inactivo o apagado (como hoy):** La web sigue vendiendo al 100%, el cliente compra normalmente y el evento queda guardado en el outbox transaccional de PostgreSQL.
* **Cuando se enciende Frappe en el futuro:** El cartero lee los eventos acumulados y crea los prospectos en el CRM y las facturas en ERPNext sin tocar una sola línea de código en la web.

---

## 7. Inventario de Variables de Entorno en `zerops_env`

```bash
# Identidad y Presencia
PROJECT_NAME="catalinaglamur"
BRAND_PRESENCE_MODEL="service_area_business" # o physical_storefront / pure_online_national

# Telemetría y Píxeles
META_PIXEL_ID="1547000523905487"
META_CAPI_ACCESS_TOKEN="<secret>"
GOOGLE_ADS_CONVERSION_ID="AW-XXXXXXXXX"
TIKTOK_PIXEL_ID="XXXXXXXXXXXXXX"
TIKTOK_EVENTS_TOKEN="<secret>"
GTM_ID="GTM-XXXXXXX"

# Conexión Opcional Frappe Cloud (Fail-Safe)
FRAPPE_URL="https://catalinaglamur.v.frappe.cloud"
FRAPPE_API_KEY="<secret>"
FRAPPE_API_SECRET="<secret>"
FRAPPE_SITE_NAME="frontend"
```

---

## 8. Contrato Soberano de Coexistencia: GitOps CI/CD vs. Mutaciones en Caliente (Telegram / Hermes)

Para prevenir el **Split-Brain / Overwrite Hazard** entre cambios del comerciante desde el celular y despliegues formales de código:

1. **PostgreSQL es el Único System of Record (SoR)**:
   - Los datos comerciales (precios, stock, imágenes y estado activo) pertenecen exclusivamente a la base de datos viva PostgreSQL, modificada en caliente vía Telegram (Hermes Agent), panel administrativo o CRM.
   - Git es el SoR exclusivo para código fuente, componentes UI, CSS y esquemas DDL (`db:migrate`).

2. **Aislamiento en `zerops.yaml`**:
   - En el runtime de producción (`webprod`), `initCommands` ejecuta **ÚNICAMENTE** migraciones con `zsc execOnce`:
     ```yaml
     initCommands:
       - case "$DATABASE_URL" in ${*|"") echo "ℹ️ DB no aprovisionada" ;; *) zsc execOnce ${appVersionId} -- bun run db:migrate || true ;; esac
     start: exec bun run apps/web/dist/server/entry.mjs
     ```
   - **Prohibido ejecutar `db:seed` en los `initCommands` de producción**: `initCommands` se ejecuta en cada reinicio, failover y auto-escalado horizontal de Incus LXC; invocar seeds ahí destruiría los precios y stock del comerciante.

3. **Ingesta Aditiva y Upsert Selectivo a Nivel de Columna**:
   - Cuando el desarrollador introduce o actualiza productos desde código (`seed.ts`), el upsert actualiza únicamente metadata descriptiva (`name`, `description`, `category`):
     ```sql
     ON CONFLICT (slug) DO UPDATE SET
       name = EXCLUDED.name,
       description = EXCLUDED.description,
       category = EXCLUDED.category;
     -- base_price, stock, images y is_active NUNCA se sobreescriben en conflicto
     ```
   - Prohibido ejecutar sentencias destructivas (`DELETE FROM services` o `DELETE FROM products`) dentro de scripts de inicialización.

4. **Blindaje de Red y Host Filtering en Astro SSR**:
   - Para evitar vulnerabilidades de DNS Rebinding (CVE GHSA-vg6x-rcgg-rjx6) y bloqueos de Vite 6 en entornos de desarrollo o previews, `allowedHosts` utiliza comodines seguros con punto inicial:
     ```javascript
     server: {
       host: "0.0.0.0",
       port: 3000,
       allowedHosts: [".zerops.app", `.${process.env.PRIMARY_DOMAIN || 'midominio.com'}`, "localhost"]
     }
     ```
   - En producción SSR (`dist/server/entry.mjs`), Astro corre en modo standalone con Node/Bun nativo sin el dev server de Vite.

