# 🚀 ESPECIFICACIÓN MAESTRA: ECOSISTEMA AGÉNTICO DE META ADS, CAPI Y CREATIVOS (v1.0 SOTA)

> **Destino:** Cualquier marca, cliente o e-commerce en Zerops (`${PROJECT_NAME}`).  
> **Ubicación Canónica (Monorepo):** `/var/www/zerops-astrobranding/templates/template-meta-ads-agentic.md`  
> **Ubicación SSoT (Google Drive):** `/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/artifacts/templates/template-meta-ads-agentic.md`  
> **Principios:** Cero Hardcoding, Invariante Upstream Inmutable, Deduplicación de Señales, Guardrails Físicos Anti-Quema de Presupuesto.

---

## 1. Topología del Sistema Agéntico

```
                       [ TRÁFICO META / INSTAGRAM ]
                                    │
                                    ▼
                    [ ASTRO 5 SSR (apps/web) ]
                     - Meta Pixel en Cliente (Browser)
                     - Shared Event ID: `${PROJECT_PREFIX}-${Date.now()}-${uuid}`
                     - Inyección de Cookies: `_fbp` y `_fbc`
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
       [ BROWSER EVENT (Pixel) ]        [ SERVER EVENT (CAPI v21+) ]
        `fbq('track', eventName, ...)`   `/api/meta/capi` (Bun Action)
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
                 [ DEDUPLICACIÓN EXACTA EN META (100%) ]
                 [ MONITOREO DATASET QUALITY API (EMQ) ]
                                    │
                                    ▼
                     [ BUS DE EVENTOS (NATS 2.12) ]
                     - `marketing.signals.lead`
                     - `marketing.signals.checkout`
                     - `marketing.signals.purchase`
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
[ POSTGRESQL 18 + VALKEY 7.2 ]                   [ CREATIVE ENGINE (videoworker) ]
- Auditoría de conversiones                      - Render dinámico Playwright + GSAP
- Telemetría de ROAS real                        - Formatos 9:16 y 1:1 con catálogo real
- Fencing tokens anti-duplicados                 - Almacenamiento en Object Storage / CDN
           │
           ▼
[ BUCLE AGÉNTICO CON GUARDRAILS (hermes / bifrost) ]
- Análisis de costo por adquisición (CPA) y fatiga creativa
- Kill-switch presupuestario: Ninguna campaña se escala sin autorización humana
- Alertas en tiempo real a WhatsApp vía Evolution API
```

---

## 2. Invariante de Variables de Entorno (Vault Soberano)

Cada proyecto o cliente inyecta dinámicamente sus credenciales en `zerops_env` sin modificar una sola línea de código del motor:

```bash
# Identidad del Proyecto
PROJECT_NAME="mi-marca"
PROJECT_PREFIX="mar"

# Credenciales de Meta (Shared Vault)
META_PIXEL_ID="${META_PIXEL_ID}"              # ID numérico de 15-16 dígitos del Dataset
META_CAPI_TOKEN="${META_CAPI_TOKEN}"          # Token del Sistema / Dataset Quality API
META_TEST_EVENT_CODE=""                        # Opcional: Para pruebas en vivo en Events Manager

# Infraestructura Zerops
DATABASE_URL="${database_connectionString}"
VALKEY_URL="${valkey_connectionString}"
NATS_URL="${nats_connectionString}"
```

---

## 3. Protocolo de Tracking Dual y Deduplicación Exacta

### A. Formato Canónico del `event_id`
Para que Meta no cobre dos veces ni duplique métricas en el Administrador de Anuncios, el navegador y el servidor emiten **estrictamente el mismo `event_id`**:

$$\text{event\_id} = \text{PREFIX} + \text{"-"} + \text{TIMESTAMP} + \text{"-"} + \text{UUIDv4}$$

### B. Normalización y Hasheo Criptográfico (SHA-256)
Todo dato de usuario enviado a la Conversions API debe normalizarse antes del hash:
- **Email**: `trim().toLowerCase()`, luego SHA-256.
- **Teléfono**: Remover espacios, guiones y signos; formatear en estándar internacional E.164 (ej: `573001234567`), luego SHA-256.
- **Cookies Meta**: Enviar sin hashear los valores de `_fbp` y `_fbc` capturados desde el request HTTP para alcanzar un **Event Match Quality (EMQ) $\ge 8.5/10$**.

---

## 4. Esquema DDL en PostgreSQL 18 (`meta_tracking`)

```sql
-- Tabla de auditoría de señales y conversiones Meta
CREATE TABLE IF NOT EXISTS meta_conversion_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(120) NOT NULL UNIQUE,
    event_name VARCHAR(64) NOT NULL,
    user_email_hash CHAR(64),
    user_phone_hash CHAR(64),
    fbp VARCHAR(120),
    fbc VARCHAR(120),
    order_id VARCHAR(64),
    value NUMERIC(12, 2),
    currency CHAR(3) DEFAULT 'COP',
    client_ip INET,
    user_agent TEXT,
    capi_status VARCHAR(32) DEFAULT 'PENDING', -- PENDING, SENT, FAILED
    capi_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_meta_events_name_created 
ON meta_conversion_events (event_name, created_at DESC);

-- Tabla de guardrails y auditoría agéntica de campañas
CREATE TABLE IF NOT EXISTS meta_campaign_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id VARCHAR(64) NOT NULL,
    campaign_name VARCHAR(255) NOT NULL,
    daily_budget NUMERIC(12, 2) NOT NULL,
    roas_actual NUMERIC(6, 2),
    cpa_actual NUMERIC(12, 2),
    agent_action VARCHAR(64) NOT NULL, -- ALERT_TRIGGERED, PROPOSAL_CREATED, PAUSE_REQUESTED
    human_approved BOOLEAN DEFAULT FALSE,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 5. Fábrica de Creativos Agnóstica (`videoworker`)

El servicio `videoworker` opera desacoplado de las marcas:
1. **Contrato de Catálogo**: Lee `/mnt/localstorage/${PROJECT_NAME}/catalog.json` que define fotos reales de productos, nombres, precios y beneficios.
2. **Plantillas GSAP**:
   - `promo-portada-hero`: 1920x1080 (Desktop) y 1080x1920 (Mobile).
   - `lookbook-reels`: 1080x1920 vertical a 60fps con Smart Crop matemático en FFmpeg (`focusX` y `focusY` por prenda).
3. **Invariante Ético y Anti-Baneos**: Prohibido el uso de stock genérico ajeno a la marca o promesas falsas de salud/ingresos que gatillen suspensiones algorítmicas en Meta.

---

## 6. Guardrails de Seguridad Agéntica (Invariante Soberano)

Para operar con agentes autónomos (Hermes, Antigravity, Bifrost) sin riesgo financiero:
1. **Regla de Solo Lectura por Defecto**: El agente analiza Insights, calcula ROAS y audita el rendimiento 24/7.
2. **Escritura Pausada**: Cualquier anuncio, conjunto o campaña generada por el agente nace estrictamente en estado `PAUSED`.
3. **Kill-Switch Presupuestario**: Prohibido modificar presupuestos automáticamente si:
   - El aumento diario supera el 20%.
   - El presupuesto excede el tope absoluto definido en `${MAX_DAILY_BUDGET_USD}`.
   - El CPA supera en un 50% el CPA objetivo fijado por el dueño del negocio.
4. **Notificaciones Proactivas**: Toda recomendación o advertencia se envía directamente por WhatsApp al dueño del negocio antes de cualquier ejecución física.
