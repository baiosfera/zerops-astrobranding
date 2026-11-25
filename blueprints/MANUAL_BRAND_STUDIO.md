# Manual Práctico de `brand-studio` 360° (Con o Sin Oráculo · Playbooks Obligatorios · UTMs y Píxeles)

> **Audiencia:** Fundadores, estrategas y operadores en cualquier proyecto Zerops (`zcp`). Escrito en lenguaje directo y práctico, sin asumir conocimientos de programación.

---

## 1. Visión General del Sistema (Arquitectura 360°)

```mermaid
flowchart TD
    IN["1. Entrada: Con Oráculo O Cuestionario Simple (brand_brief.json) + URLs de Referencia"] --> F1["Fase 1: Posicionamiento + Keyword Research en vivo (Google/IA real)"]
    F1 --> F2["Fase 2: Dirección de Arte (3 Paletas Vivas + Envato Full-Color)"]
    F2 --> GATE{"PAUSA HUMANA: ¿Te gustan los colores y fuentes?"}
    GATE -- "Ajustar / Otras URLs" --> F2
    GATE -- "Aprobado" --> F3["Fase 3: Embudo Inverso + UTMs + Píxeles + Remarketing (apotelos validate-chain)"]
    F3 --> F4["Fase 4: Escuadrón de Copy sobre 18 Playbooks -> copy/*.md (SSoT humana)"]
    F4 --> F5["Fase 5: Juez Adversario Ciego (Auditoría real sin checklist-theater)"]
    F5 --> WEB["astro-web: Compila web, Schema @graph, /llms.txt y Píxeles por Dominio"]
```

### ¿Por qué corre directo aquí (`brand-studio`) y no en Hermes / CrewAI?
Las pruebas reales mostraron que `hermes` tiene solo 512 MB de RAM y depende de modelos gratuitos en `freellmapi`/`bifrost` propensos a timeouts y caídas. Por eso:
- **`brand-studio` (Nativo en Antigravity `run_workflow`)** se encarga de toda la **creación de marca, investigación SERP, dirección de arte, estrategia de embudo y copywriting** usando modelos de frontera y herramientas reales de búsqueda web. Funciona idéntico en cualquier `zcp` nuevo tras ejecutar `iniciar.sh`.
- **`hermes` + `crewai` + `pydanticai`** quedan únicamente para tareas operativas automáticas 24/7 *después* de lanzar (alertas por Telegram, reportes diarios de pauta o clasificación rápida de leads), cuando `bifrost` esté operativo.

---

## 2. Cómo Arrancar una Marca (Con Oráculo o Sin Oráculo)

El sistema acepta **dos caminos de entrada** y ambos producen la misma estructura limpia en `/mnt/localstorage/<Proyecto>/dev/workspaces/<vertical>/`:

1. **Camino A — Con Oráculo:** ya tenés `astrobranding_<marca>.md` y `client_dumps_15_shards.json`. Oráculo aporta el enfoque psicológico, narrativo y diferenciador del fundador, **pero ya NO impone colores lavados ni tipografías por fórmula matemática**.
2. **Camino B — Sin Oráculo (cliente tradicional):** creás un archivo simple `brand_brief.json` con:
   - Tu rol principal (por ejemplo: *Estratega Digital*, *Mentor de Marcas*).
   - Términos o siglas propias que **sí querés enseñar al público** (`public_brand_concepts`, por ejemplo `OPB`, `CO1`).
   - Qué vendés, a quién y tus precios base.
   - Entre **2 y 4 URLs de páginas de referencia** (solo para entender tensión de color, ritmo visual o mecánica de embudo, nunca para copiarles).

---

## 3. Cómo Trabajar la Fase Visual (Colores Reales y Fuentes de Envato)

### Paletas con carácter real (`chroma_engine v5.0`)
- Podés pasar colores curados (`--palette-json`) o un color principal exacto (`--seed-hex "#F50023"`). El motor **conserva intacto tu color** (sin apagarlo a tonos pastel) y calcula automáticamente si el texto encima del botón debe ser negro puro (`#0a0a0a`) o blanco (`#ffffff`) para máxima legibilidad y contraste.

### Previsualización de fuentes Envato a color real (`envato_font_preview v4.0`)
- Ya no ves solo letras negras o blancas aburridas. La galería HTML (`brand/previews/preview_gallery.html`) renderiza **4 tarjetas reales** para cada fuente:
  1. Nombre de tu marca en **Color Primario** sobre el fondo.
  2. Nombre de tu marca en **Color Acento** sobre superficie secundaria.
  3. **Tarjeta Invertida de Marca** (fondo en color primario y marca encima con contraste real).
  4. **Mini Hero + Botón CTA Real** con la fuente de lectura de Google Fonts debajo.
- **Cómo probar fuentes que TÚ encontraste en Envato Elements:**
  Copiá las URLs exactas de Envato y ejecutá:
  ```bash
  envato-font-preview \
    --envato-urls "https://elements.envato.com/fonts/...,https://app.envato.com/fonts/..." \
    --chroma /mnt/localstorage/<Proyecto>/dev/workspaces/<vertical>/brand/chroma_manifest.json \
    --texts "TU MARCA,TU SLOGAN" \
    --out /mnt/localstorage/<Proyecto>/dev/workspaces/<vertical>/brand/previews
  ```
- La Fase 2 se **detiene obligatoriamente** hasta que des tu visto bueno visual. Solo después se redacta el copy final.

---

## 4. Tu Copy es Tuyo: Cómo Editar `copy/*.md` sin Perder Cambios

Dentro de `workspaces/<vertical>/`:
- **`copy/*.md` es tu archivo editable maestro (SSoT):** podés cambiar frases, historias, objeciones o precios directamente en los `.md`.
- **`web/copy_strings.es.json` NO es para editar a mano:** es un diccionario estructurado para que Astro 5 cargue rápido los textos de botones, calculadoras y FAQs sin errores.
- Cuando edites cualquier `.md`, pedile al agente (o corré en consola):
  ```bash
  brand-play sync-copy --workspace /mnt/localstorage/<Proyecto>/dev/workspaces/<vertical> --check
  ```
  Si detecta que editaste algo (`NEEDS_RECONCILIATION`), el agente actualiza `web/copy_strings.es.json` antes de compilar la web, garantizando que **tus cambios humanos nunca se pierdan ni queden pisados**.

---

## 5. Guía Sencilla de UTMs, Píxeles y Concatenación Total

### ¿Qué es un UTM y para qué sirve?
Un **UTM** es una etiqueta invisible al final de un enlace que le dice a tu web y a tus reportes **qué campaña, qué plataforma y qué anuncio/video exacto trajo a ese cliente**. El visitante ve exactamente la misma página, pero vos podés medir qué creativo produce citas y ventas reales (y cuáles solo traen clics vacíos).

Sus 5 partes:
1. `utm_source`: de qué plataforma viene (`meta`, `google`, `instagram`, `youtube`, `linkedin`, `whatsapp`, `email`).
2. `utm_medium`: cómo llegó (`paid_social` si es pauta en redes, `cpc` si es búsqueda en Google, `organic` si es contenido gratis, `email`).
3. `utm_campaign`: nombre de la campaña (ej. `captacion_consultores_co`).
4. `utm_content`: **la más importante para vender** — identifica el video, imagen o ángulo exacto (ej. `video_nomina_3m_v1` vs `carrusel_ia_v2`).
5. `utm_term`: la palabra buscada en Google Ads (ej. `mentor_de_marcas`).

### Regla de Oro: Dónde SÍ van y dónde NUNCA van
- **SÍ VAN** en todo enlace **EXTERNO** que apunta hacia tu web: anuncios de Meta/Google/TikTok/LinkedIn, link de bio en Instagram/LinkedIn, descripciones de YouTube, botones de correos y enlaces enviados por WhatsApp.
- **NUNCA VAN** en enlaces **INTERNOS** dentro de tu propia web (ej. botones que llevan del inicio `/` hacia `/ready-now` o `/checkout`), porque poner un UTM interno **sobrescribe y borra el anuncio original que te trajo al cliente**.

### Cómo se concatena todo en `brand-studio` (Fase 3)
Cada pieza se valida con `apotelos validate-chain strategy/concatenation_matrix.json` antes de construir la web:
1. **Intención / Palabra Clave (`1 intención = 1 URL`)** → página exacta con `/llms.txt` y `Schema.org @graph` para Google y motores de IA.
2. **Anuncio + UTM externo** → la persona entra y la web guarda su origen en una cookie propia de 90 días (`__attr_session`) junto al ID del clic (`fbclid` o `gclid`).
3. **Copy + Oferta + Filtro** → si la persona califica, el servidor dispara el evento `Lead` por Browser Pixel + CAPI con el mismo `event_id` (sin duplicar, y usando variables aisladas por dominio, ej. `DOMINIO1_META_PIXEL_ID` vs `DOMINIO2_META_PIXEL_ID`).
4. **Remarketing + Mensajería** → quienes no completan el siguiente paso entran a audiencias específicas de remarketing y secuencias congruentes de correo y WhatsApp.

---

## 6. Cómo Usarlo en Cualquier ZCP Nuevo

En cualquier proyecto o servidor ZCP recién creado:
1. Ejecutá `iniciar.sh --update` (instala todas las skills, Playbooks `00..17`, `orchesbrand`, `apotelos`, `brand-play`, `brand_studio.py` y este manual en `/var/www/artifacts/blueprints/`).
2. Verificá que el sistema está sano con `ssot-parity-check --with-tests` y `skills-suite-validate --strict-budget --with-tests`.
3. Pedile al agente activar `brand-studio` indicando proyecto, vertical, país y (opcional) tus URLs de referencia y enlaces de Envato.
