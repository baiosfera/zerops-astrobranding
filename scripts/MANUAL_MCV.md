# 📘 GUÍA RÁPIDA: MCV DOWNLOADER & OPTIMIZER (`mcv-download` v5.0.0)

> **Herramienta CLI autónoma para descargar, optimizar bajo arquitectura desacoplada Productor-Consumidor (v5.0.0), staging local en NVMe ZFS con cero bloqueos FUSE en rclone, sensores físicos anti-falsos positivos por 4 arquetipos (Video, Audio Puro, Híbrido, Documental), secuenciar rutas curriculares pedagógicas ([P01]..[Pn]), auditar lotes con manifiesto bidireccional y reanudación soberana, consultar metadatos canónicos en vivo en MisCursosVirtuales, purgar MP3 redundantes, monitorear lotes en vivo con telemetría bifásica unificada (`mcv-status`), orquestar tutores socráticos con `nlm-tutor` y sincronizar nativamente con Google NotebookLM Pro (hasta 300 fuentes).**

---

## 🚀 Novedades de la Versión 5.0.0 (Arquitectura Soberana)
1. **Staging Aislado en NVMe Local (`/var/www/.mcv_staging`)**:
   - Todo el flujo de descarga (Sync, Mega, Drive), descompresión y transcodificación ocurre en disco NVMe ultra-rápido.
   - Elimina de raíz los bloqueos de caché de rclone (`--vfs-cache-max-size 25G`) y errores de archivo ocupado (`EBUSY [Errno 16]`).
   - Promoción atómica final: únicamente el árbol de archivos 100% procesado y verificado se traslada a `/var/www/baiosfera/`.
2. **Sensor de Completitud Físico por 4 Arquetipos**:
   - Clasificación determinista: Arquetipo V (Video 360p), Arquetipo A (Audio Puro), Arquetipo H (Híbrido) y Arquetipo D (Documental).
   - En cursos de audio (ej. David Topi), la presencia de PDFs jamás marcará el curso como completado si faltan lecciones de audio por extraer.
3. **Optimización de Audio para Google NotebookLM Pro**:
   - Formato estándar Raw AAC (`.aac` ADTS 24k mono 16kHz) con 100% de transcripción ASR en Google Cloud STT/Chirp y 25% menos peso que MP3.
   - Soporte ampliado de hasta 300 fuentes por cuaderno (tier Pro Consumer) con espaciado defensivo anti-rate-limit (HTTP 429).
4. **Protección de Cómputo (Máximo 3 vCPUs)**:
   - Cerrojo singleton exclusivo (`fcntl.flock`) para evitar procesos concurrentes no planificados.
   - Transcodificación acotada a `-threads 2` con prioridad `nice -n 10`, dejando siempre libre el 65% de la CPU para el sistema.

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
Analiza los cursos de un autor (locales o remotos), los clasifica cognitivamente por orden de dificultad y prerrequisitos en 4 fases, asigna los códigos `[P01]..[Pn]` y genera `RUTA_DE_APRENDIZAJE.md`. **No descarga nada** (es un comando de inspección).

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

#### C. Crear Cuaderno Maestro `[00]` en NotebookLM
Si sumás `--upload-nlm`, además de la ruta en disco, creará el cuaderno maestro `[00]_GUIA-DE-ESTUDIO` y lo asociará a la colección del autor:
```bash
mcv-download --curriculum --upload-nlm
```

---

## 🛠️ Catálogo Completo de Banderas

| Bandera | Descripción | Ejemplo |
|---|---|---|
| `--curriculum [dir]` | Secuencia pedagógicamente los cursos de un autor (`[P01]..[Pn]`) y genera `RUTA_DE_APRENDIZAJE.md`. Si se omite `dir`, usa el directorio actual sin necesidad de punto. No descarga archivos. | `mcv-download --curriculum` |
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
