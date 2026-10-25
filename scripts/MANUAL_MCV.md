# 📘 GUÍA RÁPIDA: MCV DOWNLOADER & OPTIMIZER (`mcv-download` v10.1.0)

> **Herramienta CLI autónoma para descargar, optimizar bajo arquitectura desacoplada Productor-Consumidor (v10.1.0), soporte nativo de entrega Cursazo S4 (S3 Directo), enrutamiento territorial soberano (`VIP`, `AUTHOR`, `CATEGORIAS`), staging local en NVMe ZFS con cero bloqueos FUSE en rclone, sensores físicos anti-falsos positivos por 4 arquetipos (Video, Audio Puro, Híbrido, Documental), secuenciar rutas curriculares pedagógicas ([P01]..[Pn]) en Markdown nativo GFM con 5 fases Bloom-Dreyfus, omisión de cursos obsoletos (`--skip-historical`), auditar lotes con manifiesto bidireccional y reanudación soberana, consultar metadatos canónicos en vivo en MisCursosVirtuales, purgar MP3 redundantes, monitorear lotes en vivo con telemetría bifásica unificada (`mcv-status`), orquestar tutores socráticos y Decano Curricular con `nlm-tutor` y sincronizar nativamente con Google NotebookLM Pro (hasta 300 fuentes).**

---

## 🚀 Novedades de la Versión 10.0.0 (Soberanía Cursazo S4 & Enrutamiento Territorial)
1. **Proveedor Nativo Cursazo S4 con Detección Dual**:
   - Detecta automáticamente el token firmado `pase` y negocia la sesión con `cursazo.top/entrar`.
   - Consulta el árbol de carpetas (`/api/arbol`) y descarga lección por lección mediante URLs firmadas S3 (`megas4.com`).
   - Cero necesidad de descompresión de archivos `.rar` o `.zip` al recibir directamente los módulos y archivos limpios.
   - Mantiene fallback transparente al parser tradicional si algún curso legacy entrega un `.txt` con enlaces a Mega/Sync/Drive.
2. **Audio-First Remoto en Tiempo Real**:
   - Con `--audio-only` o `--audio-first`, `ffmpeg` extrae el audio `.aac`/`.mp3` directamente desde la URL de S3 en segundos por streaming HTTP Range.
   - Cero gigabytes de video descargados a disco: audios listos para NotebookLM en menos de 2 minutos por curso.
3. **Enrutamiento Territorial Soberano (Fin de Archivos Huérfanos en `/var/www/`)**:
   - **`VIP/`**: Si el curso tiene membresía VIP en MCV o se pasa `--vip` $\to$ `/var/www/baiosfera/CURSOS/MCV/VIP/`.
   - **`AUTHOR/`**: Cursos asociados a un autor o colecciones de autor $\to$ `/var/www/baiosfera/CURSOS/MCV/AUTHOR/<Alias>/`.
   - **`CATEGORIAS/`**: Cursos individuales, nichos temáticos o generales $\to$ `/var/www/baiosfera/CURSOS/MCV/CATEGORIAS/<Categoria>/`.
   - Erradicado el fallback ciego a `os.getcwd()`: la descarga siempre queda ordenada en su territorio canónico.
4. **Saneamiento Epistémico Anti-Checklist Theater**:
   - `--metadata-only` inspecciona el árbol real de Cursazo y documenta el temario completo sin disparar fases multimedia vacías sobre 0 archivos ni marcar falsamente "100% Verificado".

---

## 🧭 Banderas de Carpetización y Control Manual

El script detecta automáticamente el territorio correcto según las etiquetas de MisCursosVirtuales, pero podés forzar la ubicación con las siguientes banderas soberanas:

```bash
# 1. Forzar que un curso vaya a la carpeta VIP (independientemente de su categoría en web):
mcv-download "<URL>" --vip

# 2. Forzar que vaya a la carpeta AUTHOR bajo un alias específico:
mcv-download "<URL>" --dest author --author-dir "Margarita-Pasos"
# o simplemente:
mcv-download "<URL>" --dest author --alias "Pasos"

# 3. Forzar que vaya a una categoría específica dentro de CATEGORIAS/:
mcv-download "<URL>" --dest categoria --category-dir "Ventas"

# 4. Forzar que descargue exactamente en la carpeta donde estás parado en la terminal:
mcv-download "<URL>" --dest current

# 5. Sobrescribir manualmente la ruta destino completa (prioridad máxima):
mcv-download "<URL>" -o "/ruta/personalizada"
```

---

## ⚡ Comandos Esenciales (Cheatsheet)

### 1. Escaneo y Generación Anticipada de Manifiesto (Dry-Run en 1.5s)
No descarga nada; escanea el catálogo, extrae vigencias, genera el manifiesto `.txt` de auditoría y lista los cursos:
```bash
# Ver cursos detectados y generar manifiesto en el directorio del autor:
mcv-download "https://miscursosvirtuales.com/?post_type=product&s=alejandro+lavin" --list

# Filtrar solo cursos vigentes desde cierta fecha:
mcv-download "<URL>" --since 2024-09 --list

# Filtrar con exclusión o inclusión por índices:
mcv-download "<URL>" --only 1,3,5-8 --list
mcv-download "<URL>" --exclude 2,4 --list
```

---

### 2. Reanudación Soberana desde Manifiesto (`.txt`)
Si una descarga se interrumpe o deseas auditar el avance físico en disco:
```bash
# Reanudar un lote pendiente directamente desde el archivo de manifiesto:
mcv-download /var/www/baiosfera/CURSOS/MCV/AUTHOR/Lavin/lavin.txt

# Auditar el estado físico de los cursos en disco sin descargar:
mcv-download /var/www/baiosfera/CURSOS/MCV/AUTHOR/Lavin/lavin.txt --list

# Reanudar aplicando filtros adicionales o subida a NotebookLM:
mcv-download /var/www/baiosfera/CURSOS/MCV/AUTHOR/Lavin/lavin.txt --upload-nlm --only 1,3,5-8
```

---

### 3. Descarga de Lotes con Audio-First y NotebookLM
Al descargar categorías, autores o búsquedas múltiples:
- Crea y actualiza automáticamente el manifiesto en vivo (`<slug>.txt`) en la carpeta destino.
- Si pasas `--upload-nlm`, cada curso sube sus audios a NotebookLM en cuanto culmina su Fase 1.
- Muestra el estado en vivo de cada curso (`[PENDIENTE]`, `[DESCARGANDO...]`, `[OPTIMIZANDO...]`, `[COMPLETADO]`, `[ERROR]`).

```bash
# Descarga desatendida en segundo plano con subida a NotebookLM y Colección Soberana:
mcv-download "https://miscursosvirtuales.com/?post_type=product&s=alejandro+lavin" \
  --since 2024-01 \
  --upload-nlm \
  --collection "Alejandro Lavín" \
  -d
```

---

### 4. Modo Rápido `--audio-only` (Conserva Videos Full)
Ideal cuando quieres estudiar de inmediato con NotebookLM preservando los videos en su resolución original (1080p/720p) sin gastar CPU en transcodificación:
```bash
# Descarga, extrae audios AAC y sube a NotebookLM (omite compresión 360p):
mcv-download "<URL_PRODUCTO>" --audio-only --upload-nlm --collection "BioNeuroEmoción"
```

> **🔄 Reanudación Transparente**: Si más adelante decides comprimir los videos para ahorrar espacio, basta con ejecutar `mcv-download "<URL_PRODUCTO>"` o `mcv-download --optimize-only` en esa carpeta. El sistema detectará que los audios ya existen, los validará en 0 segundos y transcodificará los videos pendientes a 360p.

---

### 4. Optimización Polimórfica (`--optimize-only`)
Permite optimizar contenido existente sin necesidad de URL ni parámetros complejos. Detecta automáticamente si el objetivo es un curso individual o una carpeta de autor con múltiples cursos.

#### A. Ejecución Directa en el Directorio Actual
Puedes navegar a la carpeta y ejecutar el comando sin rutas ni puntos:
```bash
cd "/var/www/baiosfera/CURSOS/MCV/AUTHOR/Lavin"
mcv-download --optimize-only
```

#### B. Optimización de un Autor Completo (Multi-Curso)
Si la carpeta contiene múltiples subcarpetas de cursos:
- Detecta automáticamente todos los cursos contenidos.
- Los procesa secuencialmente en lote de forma aislada.
- No contamina la raíz del autor con carpetas de audio.
```bash
mcv-download --optimize-only "/var/www/baiosfera/CURSOS/MCV/AUTHOR/Lavin" \
  --upload-nlm \
  --collection "Alejandro Lavín"
```

#### C. Optimización de un Curso Individual (Multi-Módulo Atómico)
- **Precedencia Atómica (`cdir-first`)**: Si la carpeta contiene submódulos numerados (`1. `, `01. `, `Módulo`), videos o `NOTEBOOKLM_AUDIOS`, se reconoce automáticamente como un **único curso**, evitando la fragmentación en múltiples cuadernos.
- **Búsqueda Canónica Online**: Si la carpeta no posee `metadata.json`, consulta el catálogo en vivo de MisCursosVirtuales para extraer el autor real, título canónico y fecha de publicación exacta (`datePublished` de JSON-LD).
```bash
mcv-download --optimize-only "/var/www/baiosfera/CURSOS/MCV/BASIC/Dopamine Mastery 2024" \
  --upload-nlm \
  --collection "Dopamina & Foco"
```

---

### 5. Motor Curricular Pedagógico (`--curriculum`)
Analiza los cursos de un autor (locales o remotos), los clasifica cognitivamente por orden de dificultad y correlatividad en **5 fases (Bloom-Dreyfus)** (`[F1]` Fundamentos, `[F2]` Métodos, `[F3]` Integración, `[F4]` Especialización, `[F5]` Negocio), asigna los códigos `[P01]..[Pn]` y genera `RUTA_DE_APRENDIZAJE_<Alias>.md` en Markdown estándar con tablas GFM responsivas. **No descarga nada** por defecto (es un comando de inspección).

#### A. Generar Ruta Pedagógica en el Directorio Actual
El argumento de directorio es opcional (por defecto `.`), por lo que **no es necesario colocar el punto**:
```bash
cd "/var/www/baiosfera/CURSOS/MCV/AUTHOR/Topi"
mcv-download --curriculum
```

#### B. Generar Ruta Indicando Ruta Explícita
```bash
mcv-download --curriculum "/var/www/baiosfera/CURSOS/MCV/AUTHOR/Topi"
```

#### C. Crear Cuaderno Maestro `[00]` y Configurar Decano Curricular en NotebookLM
Si sumás `--upload-nlm`, además de la ruta en disco, creará el cuaderno maestro `[00]_GUIA-DE-ESTUDIO`, subirá la `RUTA_DE_APRENDIZAJE_<Alias>.md`, lo asociará a la colección del autor y configurará automáticamente el **Decano Curricular** (`DEAN_CURRICULAR_PROMPT` e informe sintético):
```bash
mcv-download --curriculum --upload-nlm
```

#### D. Descarga Masiva Curricular Omitiendo Históricos (`--download --skip-historical`)
Para descargar secuencialmente según la ruta pedagógica `[P01]..[Pn]` y omitir automáticamente cursos desactualizados marcados como `[⚠️ Histórico]`:
```bash
mcv-download "https://miscursosvirtuales.com/autor/alejandro-lavin/" --curriculum --download --skip-historical
```

---

## 🛠️ Catálogo Completo de Banderas

| Bandera | Descripción | Ejemplo |
|---|---|---|
| `--vip` | Fuerza el destino a `/var/www/baiosfera/CURSOS/MCV/VIP/` (se activa automático si el curso es VIP en web). | `--vip` |
| `--dest <modo>` | Regla de carpetización manual: `auto` (defecto), `vip`, `author`, `categoria`, o `current` (directorio actual). | `--dest author` |
| `--author-dir <nombre>` | Define la subcarpeta específica dentro de `/var/www/baiosfera/CURSOS/MCV/AUTHOR/`. | `--author-dir "Pasos"` |
| `--category-dir <nombre>` | Define la subcarpeta específica dentro de `/var/www/baiosfera/CURSOS/MCV/CATEGORIAS/`. | `--category-dir "Ventas"` |
| `--category <nombre>` | Sobrescribe la etiqueta de categoría del curso en los reportes y metadatos. | `--category "Marketing"` |
| `--curriculum [dir]` | Secuencia pedagógicamente los cursos de un autor (`[P01]..[Pn]`) y genera `RUTA_DE_APRENDIZAJE_<Alias>.md`. Si se omite `dir`, usa el directorio actual sin necesidad de punto. No descarga archivos. | `mcv-download --curriculum` |
| `--skip-historical` | Omite automáticamente cursos desactualizados marcados como `[⚠️ Histórico]` en la descarga masiva con `--curriculum --download`. | `--skip-historical` |
| `--collection "Nombre"` | Crea o asigna el cuaderno a la colección nativa en Google NotebookLM. | `--collection "Alejandro Lavín"` |
| `--alias "Autor"` | Define el alias del autor para la estructura de carpetas (`AUTHOR/<Alias>`). | `--alias Lavin` |
| `--since YYYY-MM` | Filtra cursos con vigencia `>=` a esa fecha. | `--since 2024-09` |
| `--only <indices>` | Descarga únicamente los números indicados (ej: `1,2,5-8` o ruta a `.txt`). | `--only 1-5` |
| `--exclude <indices>` | Excluye los números indicados de la descarga (ej: `3,7` o ruta a `.txt`). | `--exclude 2,4` |
| `--upload-nlm` | Ingesta audios y markdown a NotebookLM tempranamente tras Fase 1. | `--upload-nlm` |
| `--audio-only` | Extrae audios para NotebookLM y preserva videos originales sin comprimir a 360p. | `--audio-only` |
| `--optimize-only [dir]` | Optimiza carpetas existentes (individual o autor completo). Si se omite `dir`, usa el directorio actual `.`. | `--optimize-only` |
| `--audio-format` | Formato para NotebookLM: `aac` (24k mono, 25% más liviano, por defecto) o `mp3`. | `--audio-format aac` |
| `-d` / `--detach` | Ejecuta en segundo plano como demonio inmune a cierres de terminal. | `-d` |
| `-f` / `--foreground` | Ejecuta en primer plano pegado a la consola. | `-f` |
| `--list` / `--dry-run` | Muestra la tabla de cursos y conteo sin descargar nada. | `--list` |
| `-o <dir>` | Directorio raíz donde guardar los cursos. | `-o "/var/www/baiosfera/CURSOS"` |
| `-w` / `--watch` | Monitoriza continuamente en vivo el progreso de descargas. | `-w` |
| `--status` | Muestra telemetría instantánea y procesos en ejecución. | `--status` |

---

## 📊 Monitoreo de Progreso en Vivo (0 Tokens de IA)

```bash
# Ver estado instantáneo del demonio:
mcv-status

# Ver monitoreo continuo en terminal:
mcv-status -w

# Monitorear manifiesto de lote en disco (ejemplo):
cat "/var/www/baiosfera/CURSOS/MCV/AUTHOR/Lavin/lavin.txt"
```

---

## 📁 Estructura del Curso Procesado

```text
[YYYY-MM] Nombre-Del-Curso/
├── Nombre-Del-Curso.md              # Reporte completo con enlaces y metadatos
├── NOTEBOOKLM_AUDIOS/               # Audios listos para NotebookLM (AAC 24k mono)
│   ├── M01_L01_Clase.aac
│   └── ...                          # (MP3 redundantes purgados)
└── Módulo 01 - Fundamentos/
    ├── 1. Clase.mp4                 # (360p ligero o full original si --audio-only)
    └── Recursos.pdf
```