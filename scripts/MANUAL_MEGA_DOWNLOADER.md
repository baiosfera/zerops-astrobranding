# 🚀 MANUAL OFICIAL: MEGA-DOWNLOADER (v1.2.0)

> **Motor Soberano Universal de Descarga, Conversión de Audio Speech y Extracción de Medios para Google NotebookLM Pro bajo Gobernanza Supreme Directive v8.5, meta-script & CoHaLo Engineering.**

---

## 🏛️ 1. Misión y Filosofía Arquitectónica

El ecosistema de cursos de Baiosfera requería una solución definitiva para erradicar la dispersión de descargadores improvisados (`mcv_downloader.py`, `cenof_downloader.py`, `mega_course_processor.py`, etc.). 

**`mega-downloader`** unifica todo el flujo de ingesta, descompresión, transcodificación y preservación bajo tres invariantes soberanos:

1. **FUSE Shield & Staging en NVMe Local**:
   - Todo el I/O pesado (descargas de decenas de gigabytes, descompresión de archivos multipart y transcodificación de video) se ejecuta exclusivamente en NVMe local (`/var/www/localstorage/mega_downloads/`).
   - A Google Drive (`/var/www/baiosfera/CURSOS/...`) únicamente se promueven los archivos finales procesados (`.m4a` y PDFs/documentos). El staging local se purga inmediatamente tras la promoción, manteniendo el disco siempre limpio (<10% de uso).

2. **Estándar Speech para Google NotebookLM**:
   - **Formato obligatorio**: Contenedor `.m4a` con átomo `moov` al inicio (`-movflags +faststart`).
   - **Codec**: AAC 24 kbps mono (`-c:a aac -b:a 24k -ac 1`).
   - **Beneficio**: Reduce el tamaño del archivo un 80-90% respecto a MP3 o video crudo, ofreciendo duración exacta al segundo y scrubbing instantáneo (adelantar y retroceder sin latencia en reproductores web y Google Drive).

3. **Separación Estricta de Responsabilidades**:
   - **`mega-downloader`**: Descarga, transcodifica, limpia y organiza en Google Drive.
   - **`nlm-tutor`**: Sube las fuentes limpias a Google NotebookLM y activa los flujos de aprendizaje socrático (MVLS, Active Recall, Ebbinghaus).

---

## 🛠️ 2. Modos Operativos del CLI

El comando `mega-downloader` está disponible globalmente en `/var/www/.bin/mega-downloader`.

```bash
# Ver versión
mega-downloader --version

# Ejecutar el arnés de pruebas unitarias físicas embebido
mega-downloader --test

# Consultar estado del almacenamiento (NVMe vs Drive)
mega-downloader status
```

---

### Modo 1: Descarga Remota Directa (`mega-downloader url`)

Descarga un curso individual desde Mega.nz, Sync.com o HTTP directo, procesa los medios y los entrega listos en Google Drive:

```bash
# Ejemplo Mega (carpeta grande con reanudación ítem por ítem ante cuota 403):
mega-downloader url "https://mega.nz/folder/A1kAzaBA#6TdBL7LFSme2n5pRYmk2FA" \
  --dest "/var/www/baiosfera/CURSOS/CA/3. CUA/372_Exponential_Marketing_Jurgen_Klaric" \
  --title "Exponential Marketing - Jürgen Klarić" \
  --sequential

# Ejemplo Enlace HTTP directo:
mega-downloader url "https://example.com/recursos/masterclass.mp4" \
  --dest "/var/www/baiosfera/CURSOS/CENOF/Masterclass_Ventas"
```

**Flujo automático**:
1. Detecta el proveedor (`mega`, `sync`, `direct`).
2. Si es Mega, ejecuta `megatools dl` en staging NVMe.
3. Descomprime recursivamente archivos `.rar`, `.zip` y `.7z` (descartando automáticamente partes secundarias `.part2.rar`).
4. Extrae los audios con FFmpeg (`nice -n 19 ionice -c 3 -threads 2`).
5. Renombra a formato canónico `MODULO-{MM}_CLASE-{CC}_{Titulo}.m4a` en `NOTEBOOKLM_AUDIOS/`.
6. Preserva documentos en `DOCS/`.
7. Purga el staging local en NVMe.

---

### Modo 2: Escaneo de Recibos y Manifiestos (`mega-downloader scan`)

Para procesar carpetas con decenas de recibos de compra (`.txt`, `.docx`):

```bash
# Escanea recibos y genera el manifiesto JSON
mega-downloader scan "/var/www/baiosfera/CURSOS/CA/3. CUA/txt-mega" \
  --output "/var/www/localstorage/mega_downloads/mega_links_manifest.json"
```

El manifiesto extrae automáticamente las URLs públicas de Mega y los nombres de cursos para ser procesados secuencialmente respetando las cuotas de red.

---

### Modo 3: Saneamiento y Reparación Local (`mega-downloader reprocess`)

**Para cursos existentes con audios `.aac` sin duración o cursos con videos pesados huérfanos sin audio**:

```bash
# Sanea un curso completo en Google Drive o NVMe:
mega-downloader reprocess "/var/www/baiosfera/CURSOS/CENOF/Mentoria-de-Ventas-2022-2024-Luis-Monge-Malo"
```

**Acciones que ejecuta `--reprocess`**:
* **Reparación de `.aac` planos**: Aplica remuxing atómico instantáneo (`-c copy -movflags +faststart`) a `.m4a`. En <0.2s por archivo, habilita la duración exacta y la barra de navegación web.
* **Videos sin audio**: Extrae el audio a `.m4a` 24k mono y los deposita en `NOTEBOOKLM_AUDIOS/`.
* **Audios `.mp3` pesados**: Los transcodifica a M4A Speech ligero.
* **Documentos sueltos**: Mueve PDFs y guías dispersas a `DOCS/`.
* **Idempotencia**: Saltea automáticamente cualquier lección que ya cuente con su `.m4a` válido con duración confirmada.

---

## 📁 3. Estructura Canónica de Salida

Cada curso procesado por `mega-downloader` queda estructurado de la siguiente forma en Google Drive:

```text
/var/www/baiosfera/CURSOS/<CATEGORIA>/<NOMBRE_CURSO>/
├── NOTEBOOKLM_AUDIOS/
│   ├── MODULO-01_CLASE-01_Introduccion.m4a
│   ├── MODULO-01_CLASE-02_Fundamentos.m4a
│   └── MODULO-02_CLASE-01_Estrategia.m4a
├── DOCS/
│   ├── DOC_Guia_de_Ejercicios.pdf
│   └── DOC_Plantilla_Financiera.xlsx
└── README_REPORTE.txt
```

---

## 🔄 4. Conexión con `nlm-tutor`

Una vez que `mega-downloader` finaliza la descarga y conversión del curso:

```bash
# 1. mega-downloader prepara el contenido en Google Drive
mega-downloader url "<URL>" --dest "/var/www/baiosfera/CURSOS/CENOF/MiCurso"

# 2. nlm-tutor toma las fuentes limpias y activa el flujo socrático en NotebookLM
nlm-tutor ingest "/var/www/baiosfera/CURSOS/CENOF/MiCurso" --setup
```

---

## 🛡️ 5. Gobernanza y Mantenimiento

* **Zero Bytecode Residue**: Todo script se invoca con `python3 -B` y contiene `sys.dont_write_bytecode = True`. Prohibida la existencia de `__pycache__` en repositorios y Google Drive.
* **Compilación AST**: Cualquier cambio en `mega_downloader.py` debe ser verificado con:
  ```bash
  python3 -B -m py_compile /var/www/zerops-astrobranding/scripts/mega_downloader.py
  mega-downloader --test
  ```
* **Git SSoT**: La versión canónica reside en `/var/www/zerops-astrobranding/scripts/mega_downloader.py`.
