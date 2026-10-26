# 🌐 ESPECIFICACIÓN MAESTRA: ECOSISTEMA VIVO DE MARKETING, VENTAS Y ATRIBUCIÓN (v2.0 SOTA)

> **Destino:** Cualquier proyecto, ZCP o marca cliente en Zerops (`${PROJECT_NAME}`).  
> **Ubicación Canónica:** `/var/www/artifacts/templates/template-living-marketing-ecosystem.md`  
> **Principios:** Agnóstico, Holístico, Cero Hardcoding, Invariante Upstream Inmutable.

---

## 1. Topología del Ecosistema Autónomo

```
                       [ CLIENTE / TRÁFICO WEB ]
                                   │
                                   ▼
                   [ ASTRO 5 SSR (apps/web) ]
                    - Browser Pixel Tracking (Meta / GA4)
                    - Input Blur: Captura de Lead en Checkout
                    - Server Action: Despacho Dual a Meta CAPI v21.0
                                   │
                                   ▼
                    [ BUS DE EVENTOS (NATS 2.12) ]
                    - `lead.captured`
                    - `cart.abandoned`
                    - `order.created`
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
   [ COLA EMAIL (BullMQ/Valkey) ]           [ COLA WHATSAPP (BullMQ/Valkey) ]
   - Minuto 15: Correo Asistencia           - Minuto 120+: Contacto Concierge
   - Registra Bloqueo de Cooldown           - Evalúa si existe Cooldown en Valkey
     `SET lock:contact:{phone} 1 EX 21600`   - Si existe o ya compró: AUTO-DESCARTE
```

---

## 2. Matriz de Agentes & Economía de Tokens

| Capa | Rol Operativo | Modelo / Motor | Costo / Tokens |
|---|---|---|---|
| **AGY (Antigravity)** | Arquitectura de Código, Módulos, Schemas y Debugging | Gemini / Claude CLI | Consumo acotado para ingeniería. |
| **Hermes-Agent / Agent-Zero** | Daemon Autónomo 24/7 en segundo plano | Python Daemon (Incus LXC) | **$0 tokens de AGY**. |
| **Bifrost AI Gateway** | Inferencia y Generación de Copy Persuasivo | DeepSeek V4 Pro (`x-tier: production`) | Costo ínfimo por API / Plan propio. |
| **PostgreSQL 18** | Persistencia Relacional + Búsqueda Vectorial (`pgvector`) | SQL Nativo + HNSW | **$0 adicional** (incluido en Zerops). |
| **Valkey 7.2** | Colas BullMQ, Fencing Tokens y Bloqueo Anti-Colisión | In-Memory Key-Value | **$0 adicional** (incluido en Zerops). |
| **NotebookLM Pro** | Laboratorio de Macro-Síntesis de Cursos y Podcasts | Google Gemini 1.5/2.0 Flash/Pro | $0 (consumo dentro de Google One). |

---

## 3. Protocolo Anti-Colisión (Email Marketing vs WhatsApp Marketing)

Para evitar que una marca sature a un cliente potencial:

1. **Evento `cart.abandoned`**:
   - Se programa en BullMQ la tarea de Email Marketing para ejecutarse a los 15 minutos.
   - El worker de correo envía la plantilla de asistencia (React Email <85KB, RFC 8058 One-Click).
   - El worker de correo escribe en Valkey:
     ```
     SET lock:contact:cooldown:{phone} 1 EX 21600
     ```
     *(Cerradura de 6 horas de enfriamiento).*

2. **Evaluación de WhatsApp Marketing**:
   - A las 2 horas, el worker de WhatsApp despierta para procesar el intento de recuperación.
   - **Sensor Físico**:
     ```bash
     EXISTS lock:contact:cooldown:{phone}
     ```
     * Si la llave existe: el worker aborta silenciosamente la salida de WhatsApp.
     * Si la orden ya figura como `paid` o `pending_cod` en PostgreSQL: el worker aborta.
     * Solo si la clienta no ha convertido y expira el cooldown, se habilita la interacción conversacional por WhatsApp bajo la voz del Brandbook.

---

## 4. Dual-Tagging y Atribución Meta CAPI v21.0

Toda conversión clave (Lead, AddToCart, InitiateCheckout, Purchase) emite un identificador compartido:

```typescript
// Shared Event ID Invariant
const prefix = process.env.PROJECT_PREFIX || 'evt';
const eventId = `${prefix}-${Date.now()}-${crypto.randomUUID()}`;

// 1. Browser:
fbq('track', 'Purchase', { value, currency: 'COP' }, { eventID: eventId });

// 2. Server (Astro Action / API Route):
await fetch(`https://graph.facebook.com/v21.0/${PIXEL_ID}/events`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    data: [{
      event_name: 'Purchase',
      event_time: Math.floor(Date.now() / 1000),
      event_id: eventId,
      user_data: {
        ph: [hashSha256(phone)],
        em: [hashSha256(email)],
        client_ip_address: clientIp,
        client_user_agent: userAgent,
      },
      custom_data: { value, currency: 'COP' }
    }]
  })
});
```

---

## 5. Gobernanza del Upstream vs Downstream

- **Upstream (`/var/www/zerops-astrobranding`)**: Permanece 100% inmutable, agnóstico y libre de nombres, productos, precios o cartas natales de clientes particulares.
- **Downstream (`/var/www/baiosfera/PROYECTOS/${PROJECT_NAME}`)**: Almacena exclusivamente los activos, cartas astronumerológicas (`fase0_*.md`), `brandbook.json` y configuraciones específicas del cliente.
- **Artefactos y Templates (`/var/www/artifacts/templates/`)**: Residencia canónica de especificaciones, arquitecturas y prompts maestros universales.
