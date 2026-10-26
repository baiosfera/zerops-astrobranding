# ⚡ ECOSISTEMA VIVO DE MARKETING, VENTAS Y ATRIBUCIÓN (SOTA Octubre 2026)

> **Marca Activa:** Ecosistema dinámico gobernado por `${PROJECT_NAME}`.  
> **Arquitectura:** NATS JetStream + Valkey 7.2 (BullMQ) + PostgreSQL 18 + Bifrost AI Gateway + Hermes-Agent + Meta CAPI.  
> **Ubicación Canónica:** `/var/www/zerops-astrobranding/docs/living-marketing-ecosystem.md`

---

## 1. El Diagnóstico Crudo de la Realidad

`webprod` está **en línea y saludable** (`https://${hostname}-3000.ny1.zerops.app` / `${DOMAIN}`):
- Catálogo e-commerce activo gobernado por base de datos relacional PostgreSQL 18.
- **Falta Crítica Detectada**:
  1. **Cero Píxeles y Cero CAPI**: No hay eventos del lado del navegador ni del servidor emitiendo a Meta Conversions API ni Google Analytics 4.
  2. **Cero Remarketing Dinámico**: No se capturan carritos abandonados en el blur del checkout.
  3. **Riesgo de Canibalización Email vs WhatsApp**: Sin una cerradura distribuida en Valkey, un usuario que abandona un carrito puede recibir un correo y un mensaje de WhatsApp al mismo tiempo, quemando el número y la reputación de la marca.
  4. **Desconexión entre Cursos y Operativa**: Los cursos tienen el "qué hacer", pero falta el **arnés automático** que transforme una orden en lenguaje natural en campañas vivas.

---

## 2. La Matriz de Agentes: ¿Quién Hace Qué? (Economía Absoluta de Tokens)

| Agente / Capa | Modelo / Motor | Rol Innegociable | Costo / Tokens |
|---|---|---|---|
| **AGY (Antigravity)** | Gemini 3.8 Flash High / Argon4 | **Arquitecto Maestro de Plataforma**: Diseña el código, crea las skills, configura Zerops, repara bugs y gobierna el sistema. | Consumo acotado para ingeniería pura. |
| **Hermes-Agent / Agent-Zero** | Python Daemon en Incus LXC | **Operativo Táctico Autónomo 24/7**: Escucha eventos en NATS (`nats:4222`), procesa colas de marketing en BullMQ, genera lotes de contenido y ejecuta acciones sin intervención humana. | **$0 tokens de AGY** (corre en segundo plano en Zerops). |
| **Bifrost AI Gateway** | `http://bifrost:8080` (DeepSeek V4 Pro) | **Motor de Síntesis e Inferencia**: Provee la inteligencia semántica a Hermes, WhatsAppBot y la Web. Enruta a DeepSeek V4 Pro (`x-tier: production`) para copy persuasivo, y FreeLLMAPI para tareas triviales. | Costo ínfimo por API / Plan propio. |
| **PostgreSQL 18 (`pgvector`)** | SQL Relacional + Vectores | **Memoria Canónica Unificada**: Tablas de pedidos, carritos, perfiles astronumerológicos y fragmentos de cursos de marketing. | **$0 adicional** (ya está en Zerops). |
| **Valkey 7.2** | Memoria RAM ultrarrápida | **Semáforo Anti-Colisión & Fencing**: Evita que Email pise a WhatsApp y almacena tokens de carritos abandonados. | **$0 adicional** (ya está en Zerops). |

---

## 3. El Arbitraje Anti-Colisión: WhatsApp vs Email Marketing

Para que WhatsApp jamás pise a Email Marketing:

```
[ EVENTO: Carrito Abandonado / Lead Capturado ]
                        │
                        ▼
    [ Astro Action / NATS: `cart.abandoned` ]
                        │
                        ▼
      [ BullMQ Worker 1: Email Marketing (Listmonk/Zepto) ]
      - Despacho inmediato (Minuto 15): Correo de asistencia técnica y garantía.
      - Bloqueo en Valkey: `SET lock:contact:cooldown:{phone} 1 EX 21600` (6 horas).
                        │
                        ▼
      [ BullMQ Worker 2: WhatsApp Marketing (Evolution API) ]
      - Se dispara a las 2 horas.
      - Sensor: ¿Existe `lock:contact:cooldown:{phone}`?
        * SI EXISTE Y EL USUARIO YA ABRIÓ/COMPRÓ: Auto-descarte silencioso.
        * SI NO CONVIRTIÓ TRAS 6 HORAS: Envía mensaje concierge ultra-personalizado:
          "Hola [Nombre], soy del atelier de Catalina Glamur en Envigado. 
           Vi que estabas mirando el Enterizo Blanco Studio..."
```

---

## 4. Tracking Dual: Meta CAPI v21.0 + Astro Actions

Cada acción en la web emite eventos en espejo:
1. **Frontend (Browser Pixel)**: Dispara `fbq('track', 'AddToCart', ...)` con un `event_id` único generado en el cliente (`crypto.randomUUID()`).
2. **Backend (Astro Action / Meta CAPI)**: Dispara simultáneamente vía HTTP POST a `graph.facebook.com/v21.0/{PIXEL_ID}/events` con el **mismo `event_id`**.
3. **Resultado**: Coincidencia del 100% (Event Quality Score > 8.5/10), inmunidad contra bloqueadores de anuncios (AdBlock) y cookies de Safari (ITP).

---

## 5. El Protocolo de Lenguaje Natural para el Usuario

No tenés que escribir código ni SQL. A partir de esta arquitectura, tus órdenes en lenguaje natural activan la maquinaria:

1. *"AGY, activa el remarketing de carritos abandonados para activewear"* 
   $\rightarrow$ Conecta el hook de blur en `checkout.astro` con la cola de Valkey y el despachador de Meta CAPI.
2. *"Hermes, genera el calendario de 14 días de contenido en TikTok e Instagram para novias de Medellín"*
   $\rightarrow$ Hermes consulta el Brandbook de Catalina Glamur en PostgreSQL, extrae las fórmulas de VSL y Hooks de los cursos, consulta DeepSeek V4 en Bifrost y entrega una tabla con guiones, audios sugeridos y ángulos de dolor.
3. *"AGY, prepara la campaña de email para clientas de maquillaje de novias"*
   $\rightarrow$ Genera la plantilla en React Email 3.0 (<85KB) respetando la paleta de Catalina Glamur y los disparadores de urgencia sin sonar a spam.
