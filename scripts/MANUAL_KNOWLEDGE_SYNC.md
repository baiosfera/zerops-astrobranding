# 📘 GUÍA OPERATIVA Y ARQUITECTÓNICA: KNOWLEDGE-SYNC (`knowledge-sync` v2.2)

> **Motor Soberano de Ingesta Dinámica, Parsers Polimórficos, Compactación Multi-Curso y Curaduría de Cuadernos Temáticos en Google NotebookLM Pro (Gemini Notebook) bajo Gobernanza CoHaLo v8.5 y Frugalidad SHARED.**

---

## 🏛️ 1. Misión y Filosofía Arquitectónica

El ecosistema de aprendizaje de Baiosfera contiene decenas de miles de recursos pedagógicos (videos, subtítulos, guías, diapositivas y notas) distribuidos entre múltiples academias y proveedores (`PLATZI`, `DIGITALMARKETER`, `VELOCITYMEDIA`, `MCV`, `CA`, `SCVIP`).

Subir lecciones individuales fragmentadas desborda de inmediato los límites de cualquier sistema RAG tradicional. `knowledge-sync` resuelve este desafío implementando **fusión de alta densidad**:
- **NotebookLM Pro**: Límite estricto de **300 fuentes por cuaderno**, con ventana masiva de **500.000 palabras por fuente**.
- **Compactación Canónica**: Convierte 20 a 50 lecciones dispersas de un curso en **1 solo compendio maestro** estructurado en Markdown, reduciendo el consumo de fuentes en **>85%**.
- **Cuadernos 100% Temáticos**: No existen cuadernos por proveedor ("Cuaderno Platzi"). Existen **11 Cuadernos por Especialidad** (`FUNNELS`, `COPYWRITING`, `OFERTAS`, etc.) donde convive y se cruza el conocimiento de todas las academias.
- **Playbooks 100% Agnósticos**: Los artefactos generados en `/var/www/baiosfera/PLAYBOOKS/` son frameworks algorítmicos puros, sin menciones a marcas de academias ni autores, listos para transmutarse por las marcas activas de Zerops.

---

## 🚀 2. Capacidades de la Versión 2.2 (Soberana y Blindada)

### 2.1 Compactación y Fusión Multi-Curso (`CourseCompactor`)
- Agrupa lecciones y recursos canónicos mediante la tupla `(provider, cluster, course_dir, course_name)`.
- **Desacoplamiento de Cursos Multi-Tema**: Cursos transversales (ej. Platzi 59) se dividen automáticamente entre sus clusters de destino (`COPYWRITING`, `EMAIL`, etc.) sin contaminación cruzada.
- **Salida en NVMe Local Persistente**: Los compendios se escriben en `/var/www/localstorage/knowledge_cache/compendiums/<cluster>/`, eliminando al 100% la latencia de red y bloqueos del montaje FUSE de Google Drive.

### 2.2 Parsers Polimórficos Deterministas (Zero External Bloat)
- **`.docx` (Guías y Word)**: `DocxParser` nativo con `zipfile` y `xml.etree.ElementTree` leyendo `word/document.xml`. Sin dependencias pesadas de pip/npm (<5ms de ejecución).
- **`.pdf` (Manuales y PDFs)**: `PdfParser` con `/usr/bin/pdftotext` (poppler-utils) con flags `-layout -enc UTF-8` y timeout estricto.
- **`.srt` y `.vtt` (Subtítulos)**: `SubtitlesCleaner` elimina marcas de tiempo (`00:01:23 --> ...`), índices numéricos y tags HTML, preservando prosa continua.
- **`.md` y `.txt` (Notas)**: Ingesta directa en UTF-8 con fallback automático.

### 2.3 Jerarquía de Calidad y Deduplicación por Stem
Para cursos con múltiples formatos por lección (ej. video + audio + subtítulo + markdown), el escáner selecciona **una única fuente canónica**:
`direct_document (.docx/.pdf/.md)` > `subtitle_text (.es.srt > .srt > .es.vtt > .vtt)` > `direct_audio (.aac/.mp3)` > `video_residual (.mp4)`.

---

## ⚡ 3. Cheatsheet de Comandos CLI

### Escaneo y Diagnóstico Rápido
```bash
# Escanear todas las rutas configuradas (sin gastar tokens ni cuota)
knowledge-sync scan

# Escanear un directorio específico con profundidad controlada
knowledge-sync scan --target /var/www/baiosfera/DIGITALMARKETER --max-depth 3
```

### Compactación y Generación de Compendios
```bash
# Simular compactación de un cluster específico sin escribir a disco
knowledge-sync compact --cluster funnels --dry-run

# Compactar todas las lecciones del cluster FUNNELS de DIGITALMARKETER
knowledge-sync compact --cluster funnels --provider DIGITALMARKETER

# Compactar un curso específico y guardar en directorio personalizado
knowledge-sync compact --target "/var/www/baiosfera/PLATZI/59 CONTENT COPY EMAIL SEO STORYTELLING VENTAS/Curso de Copywriting"
```

### Ingesta Idempotente hacia Google NotebookLM Pro
```bash
# Subir compendios consolidados hacia los 11 cuadernos temáticos (Recomendado)
knowledge-sync push --compendiums --cluster funnels --limit 10

# Subir compendios con delay defensivo anti-rate-limit (jitter automático)
knowledge-sync push --compendiums --cluster copywriting --delay 6.0

# Subida clásica archivo por archivo (solo para casos puntuales)
knowledge-sync push --cluster ofertas --limit 5
```

### Auditoría y Suite de Pruebas Físicas
```bash
# Ejecutar las 8 pruebas unitarias deterministas (exit code 0)
knowledge-sync --test
```

---

## 🗺️ 4. Mapa Canónico de los 11 Clusters y Cuadernos

Los cuadernos en Google NotebookLM Pro están indexados con títulos canónicos:

| Cluster Key | Cuaderno en NotebookLM | Especialidad y Cobertura |
|---|---|---|
| `funnels` | `[ESPECIALIDAD_FUNNELS]` | Embudos de venta, VSL, tripwires, webinars, carritos. |
| `copywriting` | `[ESPECIALIDAD_COPYWRITING]` | Fórmulas de persuasión, ganchos, storytelling, cartas de venta. |
| `ofertas` | `[ESPECIALIDAD_OFERTAS]` | Gran Slam Offers (Hormozi), pricing, garantías, bonus stacks. |
| `ecommerce` | `[ESPECIALIDAD_ECOMMERCE]` | Tiendas online, logística, pasarelas, AOV, checkout optimization. |
| `email_marketing` | `[ESPECIALIDAD_EMAIL_MARKETING]` | Secuencias automatizadas, lead nurturing, entregabilidad, reactivación. |
| `whatsapp_funnels` | `[ESPECIALIDAD_WHATSAPP_FUNNELS]` | Chatbots, mensajería conversacional, cierres 1 a 1, scripts WA. |
| `paid_ads` | `[ESPECIALIDAD_MEDIA_BUYING]` | Meta Ads, Google Ads, TikTok Ads, creativos, segmentación. |
| `branding` | `[ESPECIALIDAD_BRANDING]` | Identidad visual, arquetipos de marca, diseño corporativo, posicionamiento. |
| `ux_ui` | `[ESPECIALIDAD_UX_UI]` | Arquitectura de información, wireframes, diseño centrado en usuario, CRO. |
| `automatizaciones` | `[ESPECIALIDAD_AUTOMATIZACIONES]` | Webhooks, N8N, Zapier, Make, flujos event-driven, CRM sync. |
| `ia_prompting` | `[ESPECIALIDAD_IA_PROMPTING]` | Prompt engineering, agentes autónomos, LLMs, RAG, flujos agénticos. |

---

## 🔄 5. Flujo Operativo Completo (Workflow E2E)

```
┌─────────────────────────────────┐
│  /var/www/baiosfera/CURSOS/...  │  <- Cursos crudos (Videos, SRTs, PDFs, DOCX)
└────────────────┬────────────────┘
                 │
                 ▼ 1. knowledge-sync scan
┌─────────────────────────────────┐
│   Clasificación & Stem Dedupe   │  <- Asigna cluster y descarta formatos duplicados
└────────────────┬────────────────┘
                 │
                 ▼ 2. knowledge-sync compact
┌─────────────────────────────────┐
│  /var/www/localstorage/...      │  <- Genera Compendios Markdown por (Curso, Cluster)
└────────────────┬────────────────┘
                 │
                 ▼ 3. knowledge-sync push --compendiums
┌─────────────────────────────────┐
│  Google NotebookLM Pro (Gemini) │  <- Ingesta directa a los 11 cuadernos temáticos
└────────────────┬────────────────┘
                 │
                 ▼ 4. Síntesis Agéntica (knowledge-engine)
┌─────────────────────────────────┐
│  /var/www/baiosfera/PLAYBOOKS/  │  <- Playbooks 100% Agnósticos (Zero-Brand Slop)
└────────────────┬────────────────┘
                 │
                 ▼ 5. Infusión de Marca Local (Brandbook Tokens)
┌─────────────────────────────────┐
│   astro-web / frnt / bknd       │  <- Componentes y Copy de Producción en Zerops
└─────────────────────────────────┘
```

---

## 🛠️ 6. Mantenimiento y Recuperación ante Fallos

1. **Persistencia SSoT de Dependencias**:
   - `poppler-utils` (`pdftotext`) está declarado en [`setup-zcp.sh`](file:///var/www/zerops-astrobranding/scripts/setup-zcp.sh) tanto en el repositorio local como en Google Drive SSoT ([`setup-zcp.sh` en Drive](file:///var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/setup-zcp.sh)).
   - En un reinicio en frío, `iniciar.sh -> unisetup.sh -> setup-zcp.sh` garantiza su instalación automática.
2. **Idempotencia Absoluta**:
   - Cada compendio y archivo genera una huella SHA-256 única. Si el archivo no ha cambiado, `push` lo omite automáticamente sin consumir ancho de banda ni cuotas de API.
3. **Limpieza de Almacenamiento Local**:
   - Si se desea regenerar compendios desde cero:
     ```bash
     rm -rf /var/www/localstorage/knowledge_cache/compendiums/
     knowledge-sync compact
     ```
