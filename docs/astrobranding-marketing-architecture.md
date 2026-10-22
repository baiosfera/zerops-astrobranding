# 🏛️ ARQUITECTURA SOTA: MOTOR DE CONOCIMIENTO ASTROBRANDING & MARKETING EN ZEROPS (v1.0 - Octubre 2026)

> **Destino:** Plano de Control ZCP, Agentes Autónomos (AGY, Hermes, Agent-Zero, WhatsAppBot) y Ecosistema Zerops.  
> **SSoT Gobernanza:** Compatible con `00-SUPREME-DIRECTIVE.md` (v8.4) y `prompt-universal-despliegue-zerops.md`.  
> **Ubicación Canónica:** `/var/www/zerops-astrobranding/docs/astrobranding-marketing-architecture.md`

---

## 1. El Diagnóstico del Ecosistema (Radiografía en Vivo)

Tras inspeccionar y auditar en vivo el contenedor `zcp`, las instancias de Zerops, los volúmenes de almacenamiento y las herramientas CLI en `/usr/local/bin` y `/home/zerops/.local/bin`, se constatan los siguientes hechos técnicos comprobados:

1. **Plano de Control vs Runtimes (Invariante Físico Zerops)**:
   - `zcp` es estrictamente el plano de control efímero.
   - Las instancias de producción (`webprod`, `brand`, `evolution`, `valkey`, `nats`, `database`) corren en contenedores Incus LXC aislados.
   - La base de datos es **PostgreSQL 18 (`postgresql:single@18`)**, la cual soporta nativamente **`pgvector` v0.8.7+** con índices HNSW, cuantización escalar y filtrado iterativo.

2. **Diagnóstico de Google NotebookLM MCP (`nlm`)**:
   - `notebooklm-mcp-cli` v0.15.6 está instalado y vinculado a la cuenta `baiosfera.com@gmail.com`.
   - **Limitación en Vivo Verificada**: La autenticación basada en cookies de navegador expira periódicamente (`Authentication expired. Run 'nlm login'`).
   - **Veredicto Arquitectónico**: NotebookLM es insuperable para *síntesis socrática, generación de podcasts de audio, quizzes y estudio humano (vía `nlm-tutor`)*. **NO** puede ser la base de datos de producción 24/7 para un bot de WhatsApp o un checkout web, porque una cookie expirada tumba el runtime conversacional.

3. **Diagnóstico de Bifrost vs Modelos Directos**:
   - Bifrost AI Gateway (`http://bifrost:8080`) corre desacoplado con enrutamiento CEL, latencia sub-100µs y compatibilidad drop-in con OpenAI/Anthropic.
   - Cuenta con soporte para **FreeLLMAPI** (`http://freellmapi:3001`) para tareas ligeras y enrutamiento Pro (`x-tier: production`) para generación de copy de alta conversión, ofertas y ventas.

4. **Astrobranding como Núcleo Innegociable (Oráculo)**:
   - En `/var/www/baiosfera/PROYECTOS/CATALINAGLAMUR/dev/` ya residen los artefactos canónicos: `brandbook.json`, `astrobranding_catalinaglamur.md`, `fase0_author_psychology.md` y `system_prompt.md`.
   - La identidad astronumerológica (ej. Medio Cielo en Virgo, Mercurio Shadbala 7.35 rupas, autoridad emocional, prohibición de términos cliché como "hustle", "abundance", "game-changer") es la **LENTE FILTRANTE OBLIGATORIA**.

---

## 2. La Matriz de Decisión: ¿pgvector vs Qdrant vs NotebookLM?

| Dimensión | PostgreSQL 18 (`pgvector`) | Qdrant Dedicado | NotebookLM Pro |
|---|---|---|---|
| **Costo Adicional Zerops** | **$0 / mes** (ya corre `database:18`) | ~$1.50 - $3.00/mes (LXC extra) | $0 infra (cuota Google One) |
| **Disponibilidad 24/7** | **100% Inmune a caídas de auth** | 100% Inmune | Requiere renovar cookies (`nlm login`) |
| **Consistencia Transaccional** | **ACID Nativo** (joins relacionales con pedidos, leads, perfiles) | Base vectorial aislada | Caja negra sin joins SQL |
| **Latencia P99** | **< 3ms** (HNSW Index con halfvec) | < 2ms | 2,000ms - 8,000ms |
| **Rol en el Ecosistema** | **Memoria Vectorial de Producción 24/7** | Sobrecarga innecesaria para este volumen | **Laboratorio de Destilación y Tutores** |

**Decisión Arquitectónica Definitiva**:
- La memoria vectorial unificada y permanente de producción se implementa en **PostgreSQL 18 con `pgvector`**.
- Google NotebookLM se mantiene como el **laboratorio pedagógico y generador de podcasts/resúmenes** para el humano y sesiones socráticas, pero nunca en el camino crítico de inferencia en tiempo real.

---

## 3. El Pipeline de Ingesta Masiva de Cursos a Costo Cero (Zero AGY Tokens)

Para no gastar tokens de Gemini/Claude en el agente CLI (`AGY`) leyendo miles de PDFs, audios o transcripciones:

```
[ Cursos en Drive /var/www/baiosfera/CURSOS/... ]
                        │
                        ▼ (Extracción Determinista Local)
[ Script Python Batch (PyMuPDF / Text Parser / ffmpeg) ]  <-- 0 Tokens LLM
                        │
                        ▼ (Chunking Estructurado con Metadatos)
[ Metadata: Dominio (Offer, Copy, Funnel), Autor, Nivel ]
                        │
                        ▼ (Generación de Embeddings)
  Opción A: Local Python FastEmbed (CPU, $0 costo, 0 tokens)
  Opción B: Bifrost -> FreeLLMAPI / Embedding Provider Económico
                        │
                        ▼ (Carga Vectorial)
[ PostgreSQL 18: Tabla `marketing_knowledge_chunks` (pgvector HNSW) ]
```

---

## 4. El Patrón "Lente Astrobranding" (El Filtro Semántico)

Ningún curso de marketing se aplica de forma genérica o aislada. Toda consulta se somete al siguiente compilador:

```
                  [ SOLICITUD DE ESTRATEGIA / COPY / FUNNEL ]
                                      │
                                      ▼
           [ 1. Recuperación SSoT Astrobranding (Oráculo) ]
           - Arquetipo: Sovereign Mineral Precision
           - Restricciones de Voz: Sin relleno, sin hype, analítico
           - Vocabulario Prohibido: "hustle", "abundance", "game-changer"
           - ICP Resonante: Coach/Consultora $10k+, Cáncer Casa 8, Géminis Casa 7
                                      │
                                      ▼
           [ 2. Búsqueda Vectorial Semántica en PostgreSQL 18 ]
           - Query: "Hormozi Grand Slam Offer + Guarantee Architecture"
           - Contexto Extraído: Cursos Velocity / Platzi / MCV
                                      │
                                      ▼
           [ 3. Síntesis Vía Bifrost AI Gateway (bifrost:8080) ]
           - System Prompt: Identidad Astrobranding Innegociable
           - User Payload: Marco de Marketing extraído de pgvector
           - Headers: `x-tier: production` (si es funnel crítico) o standard
                                      │
                                      ▼
           [ ARTEFACTO FINAL: OFERTA / COPY / FUNNEL 100% ALINEADO ]
```

---

## 5. Matriz de Delegación de Tareas: ¿Quién Ejecuta Qué?

| Tarea | Responsable | Mecanismo | Costo Tokens |
|---|---|---|---|
| **Arquitectura, Código, Esquemas y Rules** | **AGY (Tú)** | Herramientas Nativas / CLI | Alto (Usar quirúrgicamente) |
| **Ingesta de Cursos, OCR y Chunking** | **Python Script Local** | Python en `zcp` | **$0 (Cero Tokens)** |
| **Generación de Embeddings** | **FastEmbed / Bifrost** | Python Batch | **$0 a Despreciable** |
| **Inferencia Web SSR (Astro 5)** | **Bifrost (`bifrost:8080`)** | HTTP Interno Privado | Controlado vía Free Tier / Pro Tier |
| **WhatsApp Bot (Conversaciones)** | **Bifrost (`bifrost:8080`)** | HTTP Interno Privado | FreeLLMAPI (triage) / DeepSeek (cierre) |
| **Generación de Podcasts y Quizzes** | **NotebookLM Pro (`nlm`)** | FastMCP / NLM CLI | $0 (Incluido en Google One) |
