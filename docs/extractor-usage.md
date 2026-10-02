# 🌌 Guía Operativa del Extractor y Ensamblador Oráculo (`omni_engine.py`)

Guía técnica para ejecutar de forma autónoma el pipeline de extracción astronómica, astrológica y metafísica en la plataforma Zerops (`skill oraculo v4.9`).

---

## 1. Arquitectura de 3 Niveles: Caché, Micro-Auditorías y Compilación

El pipeline opera en tres capas estrictamente desacopladas para garantizar idempotencia, inmutabilidad y trazabilidad total:

1. **Nivel 1: Caché en Disco (`raw/json/cache/`)**:
   - Cada proveedor y endpoint persiste su respuesta validada en un archivo JSON independiente:
     `{provider}_{endpoint}_{client_hash}.json`
   - **Invariante de No Sobreescritura Cruzada**: Los archivos tienen nombres únicos según la API (`astroway_...`, `astrologyapi_...`, `freeastro_...`, `vedastro_...`, `nasa_...`).
   - Ejecutar una API individual **NO sobreescribe** la caché de las otras APIs. Las respuestas se acumulan de forma aditiva.

2. **Nivel 2: Micro-Auditorías Atómicas por API (`raw/json/audit/`)**:
   - Cada ejecución (`-x` o batch) genera un comprobante inmutable e independiente por proveedor:
     `raw/json/audit/audit_{provider}.json`
   - Registra de forma indeleble: latencia real de red, status HTTP, total de endpoints solicitados/exitosos/fallidos, créditos consumidos y timestamp UTC.
   - **Trazabilidad Forense**: Incluso si una API se carga posteriormente desde caché (`status=CACHED, latency=0.0 ms`), su comprobante atómico en `audit/` preserva la historia de la llamada original.

3. **Nivel 3: Compilación y Canon 12-15-10 (`raw/json/dumps/` y `raw/feeds/`)**:
   - Ensambla el Data Lake final:
     * **12 Shards Físicos JSON** en `raw/json/dumps/` (incluyendo TCM Health y Shodashavarga D1–D60).
     * **15 Shards Relacionales JSONB** en `client_dumps_15_shards.json` para PostgreSQL (`client_dumps`).
     * **10 Feeds Gold Markdown** en `raw/feeds/` (`fase0` a `fase9`) para los agentes downstream.
     * **Macro-Auditoría Consolidada**: `extraction_health_audit.md` y `audit/health_ledger.json`.
   - Requiere los datos completos de los motores primarios. Si faltan datos en la fase de compilación, el **Fail-Fast Gate** aborta para evitar generar shards corruptos o incompletos.

---

## 2. Flujo Recomendado: Ejecución Incremental en Cascada (API por API)

Si deseás extraer las APIs una por una de manera controlada para auditar cuotas o depurar:

### Paso 1: Extraer cada API por separado con la bandera `-x` (`--extract`)
La bandera `-x` realiza las llamadas HTTP, valida la ausencia de errores o mocks, persiste en `raw/json/cache/`, genera el micro-audit en `raw/json/audit/audit_{provider}.json` y sale limpiamente sin intentar compilar shards incompletos.

```bash
# 1. AstroWay (Western, Human Design, Vargas, BaZi, ACG, Yogas)
python3 /var/www/.agents/skills/oraculo/scripts/omni_engine.py /ruta/consultante.md -x --apis astroway

# 2. AstrologyAPI (Cábala, Numerología, Tránsitos, Sinastría)
python3 /var/www/.agents/skills/oraculo/scripts/omni_engine.py /ruta/consultante.md -x --apis astrologyapi

# 3. FreeAstroAPI (Natal Tropical, BaZi True Solar, Profecciones, TCM)
python3 /var/www/.agents/skills/oraculo/scripts/omni_engine.py /ruta/consultante.md -x --apis freeastroapi

# 4. VedAstro (HoroscopePredictions Yogas, Planetas, Casas)
python3 /var/www/.agents/skills/oraculo/scripts/omni_engine.py /ruta/consultante.md -x --apis vedastro

# 5. NASA Horizons & Servidores MCP Locales
python3 /var/www/.agents/skills/oraculo/scripts/omni_engine.py /ruta/consultante.md -x --apis nasa,mcp
```
*(El orden de ejecución es completamente libre; podés correrlas en la secuencia que prefieras).*

### Paso 2: Compilar todo desde la caché verificada con `-c` (`--compile`)
Una vez acumuladas las APIs en caché y sus micro-auditorías en disco, ejecutás:
```bash
python3 /var/www/.agents/skills/oraculo/scripts/omni_engine.py /ruta/consultante.md -c
```
- Lee los datos acumulados en la caché local (**0 llamadas de red adicionales, 0 créditos consumidos**).
- Indexa los micro-audits de `raw/json/audit/` y preserva la telemetría real.
- Valida la salud física y consistencia del conjunto de datos.
- Genera los 12 Shards Físicos JSON, los 15 Shards Relacionales, los 10 Feeds Gold Markdown, el `omni_dump_mega.json` y el `health_ledger.json`.

---

## 3. Flujo All-in-One: Extracción Concurrente y Compilación Inmediata

Si deseás ejecutar todas las APIs concurrentemente en una sola pasada:
```bash
python3 /var/www/.agents/skills/oraculo/scripts/omni_engine.py /ruta/consultante.md
```
*Si alguna API ya fue extraída previamente, el motor la carga automáticamente desde la caché sin volver a consumir la API externa.*

---

## 4. Catálogo de Banderas y Proveedores

### Banderas de Control CLI:
| Bandera | Propósito | Ejemplo |
|---|---|---|
| `-x`, `--extract` | **Solo extracción**: Guarda en caché y genera micro-audit en `audit/` sin compilar. | `-x --apis astroway` |
| `-c`, `--compile` | **Solo compilación**: Ensambla shards, feeds y ledger consolidado desde caché. | `-c` |
| `--apis <lista>` | Filtra proveedores a ejecutar (separados por coma). | `--apis astroway,vedastro` |
| `--exclude <lista>` | Excluye proveedores específicos de la ejecución. | `--exclude vedastro,mcp` |
| `--refresh-pro` | Fuerza la re-extracción ignorando la caché existente. | `-x --apis astroway --refresh-pro` |
| `--dry-run` | Valida parámetros y geocodificación sin escribir disco. | `--dry-run` |
| `--client-dir <dir>` | Define directorio de salida personalizado. | `--client-dir /var/www/output/JUAN_AGY` |

### Proveedores Soportados:
- `astroway`: AstroWay REST Engine (Swiss Ephemeris, Vargas, HD, BaZi, ACG, Yogas).
- `freeastroapi` o `freeastro`: FreeAstroAPI Engine (Natal Tropical, BaZi, Profecciones, TCM Health).
- `astrologyapi`: Astrology-API.io (9 macro endpoints, Cábala, Numerología, Sinastría).
- `vedastro`: VedAstro PRO (Yogas parasharíes, planetas, casas).
- `nasa`: NASA JPL Horizons (6 asteroides: Ceres, Pallas, Juno, Vesta, Chiron, Eris).
- `mcp`: Servidores MCP locales (Lunar BaZi, Zmanim solar, Kundali Jyotish).

---

## 5. Estructura Canónica del Data Lake Generado (Canon 12-15-10)

Directorio de salida: `/var/www/baiosfera/ASTROLOGÍA/DIAG/<CONSULTANTE>_AGY/` (o el indicado en `--client-dir`):
```text
raw/
├── json/
│   ├── cache/                          # Caché aditiva por proveedor
│   │   ├── astroway_full_extract_*.json
│   │   ├── astrologyapi_full_extract_*.json
│   │   ├── freeastro_full_extract_*.json
│   │   └── vedastro_full_extract_*.json
│   ├── audit/                          # Micro-Auditorías Atómicas & Ledger
│   │   ├── audit_astroway.json         # Telemetría de red AstroWay
│   │   ├── audit_astrologyapi.json     # Telemetría de red AstrologyAPI
│   │   ├── audit_freeastro.json        # Telemetría de red FreeAstroAPI
│   │   ├── audit_vedastro.json         # Telemetría de red VedAstro
│   │   ├── audit_hebcal_nasa.json      # Telemetría de red NASA & Hebcal
│   │   ├── audit_mcp.json              # Telemetría MCPs locales
│   │   └── health_ledger.json          # Consolidado forense JSON
│   ├── dumps/                          # 12 Shards Físicos JSON Bronze y Manifiestos
│   │   ├── shard_01_astro_western_tropical.json
│   │   ├── shard_02_astro_human_design.json
│   │   ├── ...
│   │   ├── shard_11_astro_chinese_tcm_health.json
│   │   ├── shard_12_astro_vedic_shodashavarga.json
│   │   ├── manifest.json               # Manifiesto Silver Tier
│   │   └── client_dumps_15_shards.json # Proyección de 15 Shards JSONB para PostgreSQL
│   ├── omni_dump_mega.json             # Data Lake consolidado (Silver Tier)
│   └── extraction_health_audit.md      # Macro-Auditoría de salud y balance de créditos
└── feeds/                              # 10 Feeds Gold en Markdown (Fases 0 a 9)
    ├── feed_astrobranding_fase0_author_psychology.md
    ├── feed_astrobranding_fase1_vocational_financial.md
    └── ...
```

---

## 6. Seguridad y Fail-Fast Gate

- **Código de salida 0**: Extracción o compilación limpia y exitosa.
- **Código de salida 2**: `ExtractionFatalError`. El Fail-Fast Gate interrumpe la ejecución si detecta errores de red, fallos en endpoints críticos o placeholders/mocks (`0.000°`).
- **Invariante Anti-Poisoning**: Respuestas fallidas o con código de error **NUNCA** se persisten en caché.
