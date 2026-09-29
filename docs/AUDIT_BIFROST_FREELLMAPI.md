# Auditoría de Arquitectura: Bifrost, FreeLLMAPI, Gobernanza de Virtual Keys y Caché

## 1. Análisis de SOTA & Lecciones de los Videos Técnicos

### A. Video 1: Alex Hitt — *FreeLLMAPI: Stack 16 Free LLM Providers Behind One API*
- **Tesis Central**: Unificación de capas gratuitas de múltiples proveedores (Groq, Cerebras, OpenCode, HuggingFace, GitHub Models) bajo una sola API `/v1` compatible con OpenAI.
- **Mecanismos Clave**:
  1. **Seguimiento proactivo de cuotas**: Rastreo de RPM, RPD, TPM y TPD a nivel de `(proveedor, modelo, key)` para frenar o rotar antes de recibir un HTTP 429.
  2. **Traducción de Tool Calling**: Convierte el schema de llamadas a herramientas de OpenAI al formato nativo de Gemini y Anthropic en tiempo real.
  3. **Failover con Handoff de Contexto**: Al fallar un proveedor, transfiere el prompt intacto al siguiente modelo de la cadena.
  4. **Cifrado de Secretos**: Almacenamiento con AES-256-GCM en base de datos local SQLite.

### B. Video 2: DevCovery — *Stop Letting 429s Block You! Auto-Rotates Keys*
- **Tesis Central**: Blindaje del flujo de trabajo de desarrollo y producción contra bloqueos por límite de tasa (429).
- **Mecanismos Clave**:
  1. **Rotación Multi-Key**: Múltiples llaves por proveedor organizadas en un pool rotativo.
  2. **Gestión de Cooldown**: Ante un 429 o 5xx, la llave entra en enfriamiento automático sin interrumpir la petición del cliente.
  3. **Sticky Sessions**: Fijación de modelo por 30 minutos para mantener coherencia en conversaciones iterativas.
  4. **Perfiles de Enrutamiento Nombrados**: Selección de modelos por casos de uso (`auto:coding`, `auto:fast`, `auto:reasoning`).

### C. Valor Añadido por la Capa Bifrost en Nuestro Ecosistema
FreeLLMAPI resuelve la multiplexación de capas gratuitas, pero **no** ofrece gobernanza empresarial, control de presupuestos en dólares ni persistencia relacional para equipos. Bifrost actúa como el orquestador soberano:
1. **Fallback Híbrido (Free $\to$ Comercial)**: Regla CEL que conmuta de FreeLLMAPI a DeepSeek V4 Pro si todos los proveedores gratuitos están saturados.
2. **Gobernanza de Virtual Keys**: Límites de gasto, rate limits y segregación de claves por aplicación.
3. **Persistencia Relacional**: 65 tablas en PostgreSQL 18 para logs de auditoría transaccionales y métricas de Prometheus.

---

## 2. Pruebas Físicas de Rendimiento: Con Caché vs Sin Caché

Ejecución física real en vivo contra `https://bifrost-252-8080.ny1.zerops.app`:

### A. Proveedor FreeLLMAPI (`freellmapi/auto`)
- **Paso 1 (Sin Caché / Miss - `x-bf-cache-ttl: 0`)**:
  - Latencia HTTP: **579.90 ms**
  - Header: `X-Freellm-Cache: MISS`
  - Tokens: 61
- **Paso 2 (Primer Hit)**:
  - Latencia HTTP: **20.24 ms**
  - Header: `X-Freellm-Cache: HIT`
- **Paso 3 (Hit Directo en Gateway)**:
  - Latencia HTTP: **15.78 ms**
  - Registro interno en PostgreSQL `logs`: **3.72 ms**
  - **Reducción de Latencia**: **97.3%**

### B. Proveedor DeepSeek Comercial (`deepseek/deepseek-chat`)
- **Paso 1 (Inferencia viva - Miss / Poblar Caché)**:
  - Latencia HTTP externa: **1769.73 ms**
  - Registro interno en PostgreSQL `logs`: **1730.08 ms**
  - Tokens: 119
- **Paso 2 (Hit de Caché Semántico Activo con `chromem`)**:
  - Latencia HTTP externa: **24.00 ms**
  - Registro interno en PostgreSQL `logs`: **2.91 ms**
  - **Reducción de Latencia**: **98.6%** (De 1730ms a 2.91ms).
- **Causa Raíz Resuelta**: Valkey 7.2 carecía del módulo RediSearch (`FT.*`). Al configurar `vector_store.type: chromem`, el plugin `semantic_cache` inicializó en estado `active`, habilitando la caché vectorial en caliente.

---

## 3. Guía Arquitectónica: Modelos de Embeddings y Estrategias de Caché

### A. ¿Qué es un modelo de embeddings en el contexto del Gateway?
Un modelo de embeddings convierte texto libre en vectores numéricos de punto flotante (ej: 1536 dimensiones). En lugar de comparar si dos textos son idénticos carácter por carácter (Exact Match), evalúa la distancia coseno para determinar si dos preguntas significan lo mismo.

### B. Comparativa de Estrategias: Exact Match vs Semantic Caching

| Criterio | Exact Match Cache (Hash SHA-256) | Semantic Cache (Embeddings Vectoriales) |
|---|---|---|
| **Funcionamiento** | Hash criptográfico del prompt | Similitud coseno vectorial sobre embeddings |
| **Latencia adicional** | < 1 ms (directo en Valkey) | 50 - 150 ms (para generar el embedding) |
| **Tasa de Acierto (Hit Rate)** | Media (solo preguntas 100% idénticas) | Alta (preguntas con distinta redacción) |
| **Riesgo de Falso Positivo** | Cero absoluto | Posible si el threshold es < 0.82 |
| **Dependencia Externa** | Ninguna (Valkey puro) | Requiere endpoint/modelo de embeddings |
| **Costo Computacional** | Prácticamente nulo | Costo de tokens de embeddings |

### C. Veredicto y Recomendación del Arquitecto Senior
1. **Fase Actual (Construcción & Agentes Autónomos)**:
   - **Priorizar Exact Match Cache en Valkey**. Los agentes de desarrollo, pipelines CI/CD y prompts de sistema se benefician masivamente de hash exacto sin riesgo de desalinear respuestas.
2. **Fase Conversacional (WhatsApp Bot / CRM)**:
   - **Activar Semantic Cache con embeddings** cuando el bot de atención al cliente interactúe con usuarios humanos que formulan la misma consulta con distintas palabras.
   - Usar un modelo de embeddings ligero (`text-embedding-3-small` o local vía HuggingFace).

---

## 4. Gobernanza de Virtual Keys en Producción

### A. Ubicación en la Plataforma
- **Dashboard Web**: Accesible en `https://bifrost-252-8080.ny1.zerops.app/workspace/governance/rbac` bajo la sección de Gobernanza y Virtual Keys.
- **Base de Datos**: Tabla relacional `governance_virtual_keys` en PostgreSQL 18.
- **API Administrativa**: `GET /api/governance/virtual-keys` y `POST /api/governance/virtual-keys`.

### B. Claves Soberanas Registradas en el Ecosistema

| Nombre de la Clave | ID en Gateway | Prefijo de Llave Virtual | Ámbito de Uso |
|---|---|---|---|
| **Production Sovereign Key** | `vk-production-main` | `sk-bf-e60f18ef...` | Clave maestra del entorno de producción |
| **Hermes Agent Autonomous** | `b1d77788-a64a...` | `sk-bf-f702a2c4...` | Agente autónomo de backend y mesh |
| **AstroBranding Production** | `9abaddac-33aa...` | `sk-bf-9eef443c...` | Aplicación web frontend Astro 5 |
| **Evolution WhatsApp Bot** | `2a06eb8b-e15f...` | `sk-bf-426d0421...` | Gateway de mensajería y bot comercial |
| **Antigravity AGY Operator** | `9cb0cbcd-c8bf...` | `sk-bf-e948df3c...` | Control plane y operador del sistema |

---

## 5. Herramientas de Operador: `bifrost-cli`

- **Instalación Global**: Binario compilado y enlazado en `/usr/local/bin/bifrost-cli` y `/usr/local/bin/bifrost`.
- **Uso**: `bifrost-cli -config <path>` para depuración, benchmarking y conexión interactiva con el gateway.
