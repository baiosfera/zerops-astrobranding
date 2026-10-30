# Manual Operativo: Pipelines de Branding & Brandview

Guía concisa de arquitectura y ejecución para generar identidades de marca soberanas a partir de los 15 shards astrológicos.

---

## 1. Los 2 Scripts: ¿Para qué sirve cada uno?

El ecosistema de branding opera en dos capas complementarias:

### A. `brandbook_pipeline_runner.py` (Capa de Fundamentos & Tokens)
* **Propósito:** Generar la estrategia de marca, tokens W3C DTCG y briefs canónicos.
* **Qué hace:**
  1. Ingesta los 15 shards astrológicos del cliente.
  2. Invoca **Bifrost** (DeepSeek) para razonar el posicionamiento, arquetipos y psicología de autor profunda.
  3. Ejecuta **`fontgen_engine`** para generar la terna tipográfica (`font_manifest.json` y `fontgen_[MARCA].md`).
  4. Calcula la paleta bipolar OKLCH (Rueda Polar Solar 360° + Yong Shen).
  5. Emite los 7 archivos canónicos (`brandbook.json`, `brandbook-theme.css`, `astrobranding_[marca].md`, `coach_technical_sheet.md`, `fase0_author_psychology.md`, `system_prompt.md`).
* **Destino:** `/var/www/baiosfera/PROYECTOS/[MARCA]/dev/` y `/var/www/baiosfera/ASTROLOGÍA/DIAG/[MARCA]/raw/llm/`.

### B. `compile_brandview_state.py` (Capa del Showcase Interactivo)
* **Propósito:** Alimentar la interfaz web interactiva de **Brandview Studio** (`brandview_state.json`).
* **Por qué se creó:** Brandview Studio es una aplicación web (Astro/React) donde el usuario prueba en tiempo real su marca (cambiar entre 3 ecosistemas de fuentes, alternar paletas claro/oscuro, ver animaciones del isotipo a 60fps y disparar efectos de sonido). Esa app necesita un único estado consolidado (`brandview_state.json`) que une:
  1. Tipografía (3 ecosistemas de `fontgen`).
  2. Color (Dark/Light en OKLCH con validación WCAG/APCA de `chroma`).
  3. Símbolo (Lockups e isotipos SVG vectoriales de `symbol`).
  4. Movimiento (Timelines GSAP y sound bank procedural de `kinetic`).

---

## 2. Requisitos Previos

Antes de ejecutar, verificar que los servicios base respondan en local:
```bash
# Verificar Bifrost (debe responder {"status":"ok"})
curl -s http://bifrost:8080/health

# Verificar FreeLLMAPI (debe responder 200 o {"status":"healthy"})
curl -s http://freellmapi:3001/health
```

---

## 3. Orden y Comandos de Ejecución

### Paso 1: Generar el Brandbook y Manifiesto Tipográfico
```bash
python3 -B /var/www/.bin/brandbook_pipeline_runner.py --brand DAMAREN
```
*(Nota: también accesible directamente en `/var/www/zerops-astrobranding/scripts/brandbook_pipeline_runner.py`)*

### Paso 2: Compilar el Estado para Brandview Studio
```bash
python3 -B /var/www/zerops-astrobranding/scripts/compile_brandview_state.py --brand DAMAREN
```
*Genera `brandview_state.json` en `/var/www/baiosfera/PROYECTOS/DAMAREN/dev/` y `/var/www/localstorage/DAMAREN/dev/`.*

### Paso 3: Sincronizar SSoT (Google Drive)
```bash
zcp-sync DAMAREN
```
