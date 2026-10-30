# Manual Operativo: Ingesta de Cursos & Upstream Knowledge Engine (v3.0)

**Gobernanza:** Supreme Directive v8.5 & CoHaLo Engineering  
**Repositorios:** `zerops-astrobranding` · `zerops-astro-skills` · `Google Drive SSoT`  
**Tracking Linear:** Proyecto *Ingesta Soberana Anti-Stubs y Playbooks Universales* (`BAI-403` a `BAI-406`)

---

## 1. Filosofía Arquitectónica: Separación Estricta de Responsabilidades

El sistema upstream de conocimiento extrae modelos mentales, heurísticas y playbooks desde las bibliotecas de cursos (`CURSOS/MCV`, `CURSOS/VELOCITYMEDIA`, `DIGITALMARKETER`, `PLATZI`) hacia **Google NotebookLM Pro**.

Opera bajo una frontera técnica infranqueable:

| Componente | Capa / Motor | Responsabilidad Exclusiva |
|---|---|---|
| **`knowledge-sync`** (`knowledge_sync.py`) | **Software Determinista (Python puro, cero LLM, cero tokens)** | **Obrera de datos e infraestructura:** Escanea cursos, perfila la densidad de texto real para clasificar en las 18 especialidades, extrae subtítulos y audio de videos huérfanos, genera compendios limpios de Markdown (`compact`), gestiona la bitácora append-only (`.knowledge_manifest/`) y sube fuentes vía API a NotebookLM. **Python NO razona ni extrae playbooks.** |
| **`knowledge-engine`** | **Cognitiva / LLM (Skill de AGY)** | **Estratega cognitivo:** Ejecutado por un **subagente AGY** que consulta NotebookLM (`nlm chat` / Gemini 1.5 Pro) para interrogar las fuentes indexadas y redactar los playbooks. |
| **Playbooks Universales** (`/var/www/baiosfera/PLAYBOOKS/`) | **Base de Conocimiento SSoT (100% Genérica y Agnóstica)** | **Marcos y heurísticas puras:** Playbooks de Customer Value Journey, Hormozi, StoryBrand, etc. **PROHIBIDO incluir nombres de clientes, marcas o tokens específicos.** Son 100% universales. |
| **Agentes de Proyecto (Downstream)** | **Aplicación a Marcas** | Agentes en workspaces específicos (ej. `ElPlacerDC`, `Catalina Glamur`) que leen los playbooks genéricos de `/var/www/baiosfera/PLAYBOOKS/` y los aplican al contexto particular de su cliente. |

---

## 2. Los 18 Clusters Especializados (CVJ) + Cuaderno Corona

El conocimiento se clasifica en 18 especialidades del **Customer Value Journey (CVJ)** gobernadas por el Cuaderno Corona:

* **Corona:** `categoria_uno` (`[ESTRATEGIA_CATEGORIA_DE_UNO_Y_AUTORIDAD]`) — UUID: `63f2b7ea-bfce-482b-add5-02997157cb47`
1. `copywriting` (`[ESPECIALIDAD_COPY_TITULARES_Y_GANCHOS]`)
2. `ofertas_pricing` (`[ESPECIALIDAD_OFERTAS_IRRESISTIBLES_Y_PRICING]`)
3. `funnels_cro` (`[ESPECIALIDAD_FUNNELS_CHECKOUTS_Y_CRO]`)
4. `trafico_ads` (`[ESPECIALIDAD_META_ADS_CREATIVOS_Y_PAUTA]`)
5. `email_automation` (`[ESPECIALIDAD_EMAIL_MARKETING_Y_AUTOMATION]`)
6. `whatsapp_conversational` (`[ESPECIALIDAD_WHATSAPP_MARKETING_Y_CHATBOTS]`)
7. `growth_retencion` (`[ESPECIALIDAD_GROWTH_RETENCION_Y_LTV]`)
8. `social_content` (`[ESPECIALIDAD_REDES_SOCIALES_Y_COMUNIDAD]`)
9. `video_youtube` (`[ESPECIALIDAD_VIDEO_YOUTUBE_Y_GUIONES]`)
10. `seo_posicionamiento` (`[ESPECIALIDAD_SEO_Y_CONTENIDO_ORGANICO]`)
11. `branding_posicionamiento` (`[ESPECIALIDAD_BRANDING_Y_POSICIONAMIENTO]`)
12. `estrategia_negocios` (`[ESPECIALIDAD_ESTRATEGIA_NEGOCIOS_Y_MODELOS]`)
13. `ventas_high_ticket` (`[ESPECIALIDAD_VENTAS_HIGH_TICKET_Y_CLOSING]`)
14. `ia_automatizacion` (`[ESPECIALIDAD_IA_HERRAMIENTAS_Y_AUTOMATIZACION]`)
15. `lanzamientos` (`[ESPECIALIDAD_LANZAMIENTOS_Y_EVENTOS]`)
16. `ecommerce_stores` (`[ESPECIALIDAD_ECOMMERCE_Y_TIENDAS_ONLINE]`)
17. `product_startup` (`[ESPECIALIDAD_PRODUCTO_UX_UI_Y_STARTUPS]`)
18. `analitica_data` (`[ESPECIALIDAD_ANALITICA_METRICAS_Y_DATA]`)

---

## 3. Comandos CLI (`knowledge-sync`)

El CLI determinista está disponible en `/usr/local/bin/knowledge-sync` (o `python3 -B /var/www/zerops-astrobranding/scripts/knowledge_sync.py`):

### A. Escaneo Semántico y Diagnóstico
```bash
# Escaneo de todas las bibliotecas configuradas
knowledge-sync scan

# Escaneo de un directorio específico
knowledge-sync scan --target /var/www/baiosfera/DIGITALMARKETER
```

### B. Compactación a Compendios Limpios (Anti-Slop)
Agrupa lecciones por curso en archivos Markdown consolidados respetando el presupuesto de ~250.000 palabras por compendio:
```bash
# Modo Dry-Run (inspecciona qué compendios se crearían sin tocar disco)
knowledge-sync compact --dry-run

# Modo Dry-Run filtrado a un cluster específico
knowledge-sync compact --cluster copywriting --dry-run

# Ejecución real de compactación
knowledge-sync compact
```

### C. Aprovisionar Cuadernos en NotebookLM (`init-clusters`)
Descubre los 18 cuadernos en vivo, crea los que falten con sus system prompts especializados y genera `clusters.json`:
```bash
knowledge-sync init-clusters
```

### D. Subir Compendios a NotebookLM (`push`)
Sube los compendios generados al cuaderno correspondiente de forma idempotente:
```bash
# Subir compendios de un cluster específico
knowledge-sync push --cluster copywriting --compendiums

# Subir con límite de seguridad
knowledge-sync push --cluster funnels_cro --compendiums --limit 5
```

### E. Suite de Pruebas Unitarias Deterministas (Exit 0)
```bash
knowledge-sync --test
```

---

## 4. Persistencia en Google Drive SSoT

* **Script ejecutable:** `/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/knowledge_sync.py`
* **Skill del Agente:** `/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/zerops-astro-skills/knowledge-engine/`
* **Documentación SSoT:** `/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/docs/MANUAL_KNOWLEDGE.md`
* **Bitácora de Sincronización:** `/var/www/baiosfera/.knowledge_manifest/`
  * `clusters.json`: Mapeo canónico de los 18 cuadernos con sus UUIDs en NotebookLM.
  * `cluster_events_*.jsonl`: Registro append-only de fuentes subidas con hash MD5 para evitar duplicados.
