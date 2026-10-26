# 🎯 ESPECIFICACIÓN MAESTRA: PIPELINE ASTRO-MARKETING AGNOSTICO & UNIVERSAL (v2.0)

> **Destino:** Cualquier marca, proyecto o cliente en cualquier ZCP (`${PROJECT_NAME}`).  
> **Ubicación Canónica:** `/var/www/artifacts/templates/template-astro-marketing-pipeline.md`  
> **Gobernanza:** SSoT 100% desacoplado de marcas específicas.

---

## 1. Declaración de Variables de Entorno Dinámicas

```bash
# Inyección dinámica por runtime, zcp-sync o iniciar.sh
export ACTIVE_BRAND="${PROJECT_NAME:-BRAND}"
export BRAND_SSOT_PATH="${BRAND_SSOT_PATH:-/mnt/localstorage/${ACTIVE_BRAND}/dev}"
export POSTGRES_URL="${database_connectionString}"
export BIFROST_URL="${BIFROST_URL:-http://bifrost:8080/v1}"
export VALKEY_URL="${valkey_connectionString}"
export NATS_URL="${nats_connectionString:-nats://nats:4222}"
```

---

## 2. Esquema DDL en PostgreSQL 18 (`pgvector`)

```sql
-- Extensión vectorial (v0.8.7+)
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de chunks de conocimiento pedagógico y marcos de cursos (Agnóstica y Universal)
CREATE TABLE IF NOT EXISTS marketing_knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name VARCHAR(100) NOT NULL,       -- ej: 'VelocityMedia', 'MCV', 'Platzi', 'Hormozi'
    course_name VARCHAR(200) NOT NULL,       -- ej: 'GrandSlamOffers', 'Neurocopywriting'
    category VARCHAR(100) NOT NULL,          -- ej: 'copywriting', 'funnels', 'pricing', 'email'
    framework VARCHAR(100),                  -- ej: 'PAS', 'StoryBrand', 'HookStoryOffer'
    content TEXT NOT NULL,                   -- Texto limpio del fragmento pedagógico
    embedding vector(1536),                  -- Vector normalizado
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice HNSW de alta velocidad y bajo consumo de RAM
CREATE INDEX IF NOT EXISTS idx_marketing_chunks_hnsw 
ON marketing_knowledge_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

---

## 3. Protocolo de Ingesta Offline con Python (Cero Costo de Tokens LLM)

Un script Python batch local (`ingest_courses.py`) procesa los archivos en `/var/www/baiosfera/CURSOS/`:
1. **Extracción**: Extrae texto de PDFs, TXTs y transcripciones generadas por `mcv-download`.
2. **Chunking Semántico**: Divide en bloques de 500-800 tokens preservando jerarquía temática.
3. **Embeddings Locales en CPU**: Genera vectores con `fastembed` o vía endpoint económico (`text-embedding-3-small`), sin gastar tokens de agentes orquestadores.
4. **Inserción ACID**: Almacena en la tabla `marketing_knowledge_chunks` de PostgreSQL 18.

---

## 4. El Compilador "Lente Astrobranding" (Inferencia en Runtime)

Todo requerimiento de marketing se somete dinámicamente a la identidad astronumerológica del cliente activo:

```markdown
<SYSTEM_PROMPT>
Eres el Director de Estrategia Comercial y Copywriting de la marca {BRAND_NAME}.
Toda tu comunicación se rige ESTRICTAMENTE por el Brandbook y la carta astronumerológica del proyecto:

[ARQUETIPO Y ESTILO DE VOZ]
- Esencia: {BRAND_ESSENCE}
- Tono: {BRAND_TONE}
- Términos Obligatorios: {PREFERRED_TERMS}
- TÉRMINOS ESTRICTAMENTE PROHIBIDOS: {FORBIDDEN_TERMS}

[PERFIL DEL CLIENTE IDEAL (ICP)]
- {ICP_DESCRIPTION}

[MARCO PEDAGÓGICO DE MARKETING RECUPERADO DE LA BASE DE CONOCIMIENTO]
{RETRIEVED_COURSE_FRAMEWORK}

[MISIÓN]
Aplica el marco pedagógico anterior para resolver el requerimiento comercial, pero FILTRADO Y TRADUCIDO al 100% bajo el arquetipo, el tono y el ICP de {BRAND_NAME}. Jamás suenes como un marketer genérico.
</SYSTEM_PROMPT>
```
