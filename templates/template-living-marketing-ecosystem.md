# 🌐 ESPECIFICACIÓN MAESTRA: ECOSISTEMA VIVO DE MARKETING, VENTAS Y ATRIBUCIÓN (v3.0 SOTA)

> **Destino:** Cualquier proyecto, ZCP o marca cliente en Zerops (`${PROJECT_NAME}`).  
> **Ubicación Canónica:** `/var/www/artifacts/templates/template-living-marketing-ecosystem.md`  
> **Principios:** Agnóstico, Holístico, Cero Hardcoding, Invariante Upstream Inmutable.

---

## 1. Topología del Ecosistema Omnicanal Agnóstico

```
                         [ CLIENTE / TRÁFICO WEB ]
                                     │
                                     ▼
                     [ ASTRO 5 SSR (apps/web) ]
                      - Browser Pixel Tracking (Meta / GA4 / TikTok)
                      - Dynamic Lifecycle Event Dispatcher
                      - Server Action: Despacho Dual a CAPI con SHA-256
                                     │
                                     ▼
                      [ BUS DE EVENTOS (NATS 2.12) ]
                      - TOFU: `lead.captured`, `quiz.completed`
                      - MOFU: `booking.requested`, `resource.accessed`
                      - BOFU: `cart.abandoned`, `checkout.initiated`
                      - POST: `order.created`, `payment.confirmed`
                                     │
               ┌─────────────────────┴─────────────────────┐
               ▼                                           ▼
    [ COLA EMAIL (BullMQ/Valkey) ]             [ COLA WHATSAPP (BullMQ/Valkey) ]
    - Throttled Worker (10/sec)                - Dedicated Worker en Bun/Go (:8085)
    - P1: Transaccional (inmediato)            - Prioridad Lifecycle P2 / Concierge
    - P2/P3: Lifecycle / Nutrición             - Evalúa Cooldown & Quiet Hours
    - Respeta Frequency Cap (24h)              - Si ya convirtió o hay lock: SKIP
```

---

## 2. Matriz de Agentes & Economía de Infraestructura

| Capa | Rol Operativo | Motor en Zerops | Costo Operativo |
|---|---|---|---|
| **AGY (Antigravity)** | Arquitectura de Código, Módulos, Schemas y Debugging | Gemini / Claude CLI | Consumo acotado para ingeniería. |
| **Hermes-Agent / Agent-Zero** | Daemon Autónomo 24/7 en segundo plano | Python Daemon (Incus LXC) | **$0 tokens de AGY**. |
| **Bifrost AI Gateway** | Inferencia y Generación de Copy Persuasivo | DeepSeek V4 Pro (`x-tier: production`) | Costo ínfimo por API. |
| **PostgreSQL 18** | Persistencia Relacional + Búsqueda Vectorial (`pgvector`) | SQL Nativo + HNSW | **$0 adicional** (incluido en Zerops). |
| **Valkey 7.2** | Colas BullMQ, Fencing Tokens y Bloqueo Anti-Colisión | In-Memory Key-Value | **$0 adicional** (incluido en Zerops). |
| **NATS 2.12** | Bus de Eventos Reactivo & JetStream Streaming | Core NATS RPC (<0.3ms P99) | **$0 adicional** (incluido en Zerops). |

---

## 3. Modelo Polimórfico de Ciclo de Vida: TOFU, MOFU, BOFU y Retención

El sistema se adapta dinámicamente al tipo de embudo (`CommercialFunnelType`) sin tiempos ni canales quemados:

### A. TOFU (Top of Funnel — Atracción y Captura)
- **Disparador:** `lead.captured`, `newsletter.subscribed`, `leadmagnet.requested`.
- **Canal Primario:** Email (Entrega inmediata de valor, bienvenida y expectativa).
- **Canal Secundario:** WhatsApp (Opt-in opcional de doble confirmación o entrega directa si solicitado).
- **Objetivo:** Establecer autoridad, entregar la promesa y sembrar el Mecanismo Único de la marca.

### B. MOFU (Middle of Funnel — Consideración y Educación)
- **Disparador:** `resource.accessed`, `quiz.completed`, `case_study.viewed`, `webinar.registered`.
- **Canal Primario:** Secuencia espaciada de Email (Casos de estudio, derribo de objeciones, ecuación de valor).
- **Canal Secundario:** WhatsApp conversacional (Invitación a agendar diagnóstico o demostración interactiva).
- **Objetivo:** Maduración del prospecto hacia la decisión de compra sin presión invasiva.

### C. BOFU (Bottom of Funnel — Decisión y Cierre)
- **Disparador:** `cart.abandoned`, `checkout.initiated`, `pricing.high_intent`, `booking.pending`.
- **Cadencia Dinámica:** Parametrizable según vertical (e.g. Asistencia por Email a los 30 min; Concierge por WhatsApp a las 3 horas si no convirtió).
- **Incentivo Seguro:** Techo dinámico de descuento (`BoundedDiscount`) calculado sobre el margen bruto real, protegiendo la rentabilidad.

### D. POST-CONVERSION (Onboarding y Retención)
- **Disparador:** `order.created`, `payment.confirmed`, `contract.signed`.
- **Prioridad P1 (Transaccional):** Despacho instantáneo de factura, recibo o credenciales (ignora topes de frecuencia).
- **Seguimiento Logístico / Activación:** Notificación por WhatsApp con estado de envío, acceso al área de miembros o pasos de onboarding.

---

## 4. Protocolo de Anti-Colisión, Frequency Capping y Fencing Tokens

Para erradicar la fatiga de contactos y evitar mensajes duplicados entre canales:

1. **Jerarquía de Mensajes (Message Prioritization)**:
   - **P1_TRANSACTIONAL**: Confirmaciones de compra, facturación, OTP. Despacho inmediato, **ignora topes de frecuencia**.
   - **P2_LIFECYCLE**: Asistencia en checkout, recordatorios de cita agendada. Despacho prioritario pero sujeto a `Quiet Hours`.
   - **P3_PROMOTIONAL**: Newsletters, promociones masivas, lanzamientos. Sujeto a **Frequency Cap de 24 horas** y supresión cruzada.

2. **Supresión Cruzada (Cross-Channel Mutual Exclusion)**:
   - Si un canal conversacional de alta prioridad (WhatsApp) está activo o en ventana de respuesta, el worker de Email suprime automáticamente los correos promocionales salientes mediante consulta a Valkey:
     ```bash
     EXISTS lock:contact:active_chat:{phone}
     ```
   - Si la llave existe: el correo promocional se descarta o pospone.

3. **Ventana de Horas de Silencio (Quiet Hours)**:
   - Los canales invasivos (WhatsApp / SMS) nunca despachan mensajes comerciales fuera del rango permitido local (por defecto: 08:00 a 21:00).
   - Los eventos ocurridos durante horas de silencio se encolan para liberación programada al inicio de la siguiente ventana válida.

4. **Transición Monotónica de Estado (Fencing Tokens)**:
   - Cada cambio de etapa (ej. de Lead a Checkout, o de Checkout a Purchase) incrementa un contador de versión en Valkey:
     ```bash
     HINCRBY contact:state:{contact_id} stage_version 1
     ```
   - Los jobs demorados en BullMQ contrastan `job.version == current_version`. Si la versión cambió (el usuario ya compró o avanzó de etapa), el job se auto-descarta de forma silenciosa e idempotente.

---

## 5. Dual-Tagging y Atribución CAPI Agnóstica

Toda conversión clave emite un identificador compartido (`eventId`) desacoplado de monedas o países fijos:

```typescript
// Shared Event ID Invariant
const prefix = process.env.PROJECT_PREFIX || 'evt';
const eventId = `${prefix}-${Date.now()}-${crypto.randomUUID()}`;
const currency = process.env.PUBLIC_CURRENCY || 'USD';

// 1. Browser:
fbq('track', eventName, { value, currency }, { eventID: eventId });

// 2. Server (Astro Action / API Route):
await fetch(`https://graph.facebook.com/v21.0/${PIXEL_ID}/events`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    data: [{
      event_name: eventName,
      event_time: Math.floor(Date.now() / 1000),
      event_id: eventId,
      user_data: {
        ph: phone ? [hashSha256(phone)] : undefined,
        em: email ? [hashSha256(email)] : undefined,
        client_ip_address: clientIp,
        client_user_agent: userAgent,
      },
      custom_data: { value, currency }
    }]
  })
});
```

---

## 6. Gobernanza del Upstream vs Downstream

- **Upstream (`/var/www/zerops-astrobranding`)**: Permanece 100% inmutable, agnóstico y libre de nombres, productos, precios, monedas o géneros específicos.
- **Downstream (`/var/www/baiosfera/PROYECTOS/${PROJECT_NAME}`)**: Almacena exclusivamente los activos, cartas astronumerológicas, `brandbook.json` y configuraciones específicas del cliente.
- **Artefactos y Templates (`/var/www/artifacts/templates/`)**: Residencia canónica de especificaciones, arquitecturas y contratos maestros universales.
