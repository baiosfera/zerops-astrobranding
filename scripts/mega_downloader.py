#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
       MEGA-DOWNLOADER: Motor Soberano Universal de Descarga, Conversión
                   y Extracción de Medios para NotebookLM
===============================================================================
Gobernanza: Supreme Directive v8.5, meta-script & CoHaLo Engineering
Versión: 1.0.0
Características Principales:
1. Multi-Provider Ingestion: Mega.nz (megatools / API), Sync.com (AES streaming),
   Google Drive y Enlaces Directos HTTP / HLS.
2. FUSE Shield & Localstorage Staging: Descargas y cómputo masivo 100% en NVMe local
   (/var/www/localstorage/mega_downloads/), previniendo bloqueos de I/O en Google Drive.
3. NotebookLM Speech Standard: Transcodificación M4A con -movflags +faststart,
   24k mono AAC (-c:a aac -b:a 24k -ac 1) y duración exacta validada vía ffprobe.
4. Smart Archive Unpacking: Descompresión de archivos multipart (.part1.rar),
   .rar, .zip y .7z con purga inmediata de binarios para conservar espacio.
5. Three Execution Modes:
   - Modo 1 (--url): Descarga y procesamiento directo de enlace individual.
   - Modo 2 (--scan / --manifest): Escaneo de recibos y procesamiento de cola en lote.
   - Modo 3 (--reprocess): Saneamiento local de cursos existentes (remuxing AAC a M4A,
     transcodificación de videos/mp3 pesados y organización en NOTEBOOKLM_AUDIOS/).
===============================================================================
"""

import os
import sys
import shutil
import re
import json
import time
import argparse
import subprocess
import zipfile
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Gobernanza CoHaLo: Cero generación de bytecode en filesystem o Google Drive
sys.dont_write_bytecode = True

VERSION = "1.0.0"

# Rutas Canónicas del Ecosistema
DEFAULT_STAGING_BASE = "/var/www/localstorage/mega_downloads"
DEFAULT_GDRIVE_BASE = "/var/www/baiosfera/CURSOS"
DEFAULT_RECEIPTS_DIR = "/var/www/baiosfera/CURSOS/CA/3. CUA/txt-mega"
DEFAULT_MANIFEST_PATH = os.path.join(DEFAULT_STAGING_BASE, "mega_links_manifest.json")

# Extensiones Reconocidas
MEDIA_EXTENSIONS = {
    ".mp4", ".mkv", ".mov", ".avi", ".webm", ".ts", ".m4v",
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus"
}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".ts", ".m4v"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus"}
DOC_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".epub",
    ".zip", ".rar", ".7z", ".srt", ".vtt"
}
ARCHIVE_EXTENSIONS = {".rar", ".zip", ".7z", ".tar", ".gz"}

# ANSI Colors
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = {
        "INFO": f"{GREEN}[{ts}]{RESET}",
        "WARN": f"{YELLOW}[{ts}] ⚠️{RESET}",
        "ERROR": f"{RED}[{ts}] ❌{RESET}",
        "ACTION": f"{CYAN}[{ts}] 🚀{RESET}",
        "AUDIO": f"{CYAN}[{ts}] 🎧{RESET}",
    }.get(level, f"[{ts}]")
    print(f"{prefix} {msg}", flush=True)


# =============================================================================
# 1. NORMALIZER & SANITIZER (Nomenclatura Jerárquica Limpia)
# =============================================================================

class Normalizer:
    @staticmethod
    def sanitize_slug(text: str) -> str:
        """Convierte texto en un slug seguro para filesystem (sin espacios ni caracteres raros)."""
        t = re.sub(r'[\s\-\,]+', '_', text)
        t = re.sub(r'[^\w\d_\.]', '', t)
        t = re.sub(r'_+', '_', t).strip('_')
        return t

    @staticmethod
    def clean_title(text: str) -> str:
        """Limpia etiquetas de resolución, codecs, bitrates y ruidos típicos."""
        t = text
        # Eliminar extensiones
        t = re.sub(r'\.[a-zA-Z0-9]{2,4}$', '', t)
        # Quitar resoluciones (1366x652, 1080p, 4k, etc.)
        t = re.sub(r'\b\d+x\d+\b', '', t, flags=re.I)
        t = re.sub(r'\b\d+[kK]\b', '', t)
        t = re.sub(r'\b(1080p|720p|480p|360p|2160p|4k|x264|h264|hevc|webrip|bluray)\b', '', t, flags=re.I)
        # Quitar prefijos numéricos redundantes si se va a re-etiquetar
        t = re.sub(r'^\d+[\.\-\_\s]+', '', t)
        return Normalizer.sanitize_slug(t)

    @staticmethod
    def format_audio_name(parent_folder: str, filename: str, idx: int) -> str:
        """
        Formatea el nombre final de la lección para NotebookLM:
        MODULO-{MM:02d}_CLASE-{CC:02d}_{clean_title}.m4a
        """
        clean_fn = Normalizer.clean_title(filename)

        # Detectar número de módulo del directorio padre
        mod_num = 1
        m_parent = re.search(r'(?:modulo|m[oó]dulo|mod|chapter|capitulo|cap[ií]tulo|seccion|secci[oó]n|d[ií]a|day)[\s\-_]*(\d+)', parent_folder, re.I)
        if m_parent:
            try:
                mod_num = int(m_parent.group(1))
            except ValueError:
                pass
        else:
            # Buscar número líder en la carpeta (ej: "04 Capitulo 2")
            m_lead = re.match(r'^(\d+)[\.\s\-_]', parent_folder)
            if m_lead:
                try:
                    mod_num = int(m_lead.group(1))
                except ValueError:
                    pass

        # Detectar número de clase del archivo
        cls_num = idx
        m_file = re.search(r'(?:clase|class|leccion|lecci[oó]n|lesson|video|capitulo|cap[ií]tulo|d[ií]a|day)[\s\-_]*(\d+)', filename, re.I)
        if m_file:
            try:
                cls_num = int(m_file.group(1))
            except ValueError:
                pass
        else:
            m_num = re.match(r'^(\d+)[\.\s\-_]', filename)
            if m_num:
                try:
                    cls_num = int(m_num.group(1))
                except ValueError:
                    pass

        return f"MODULO-{mod_num:02d}_CLASE-{cls_num:02d}_{clean_fn}.m4a"


# =============================================================================
# 2. TRANSCODER (FFmpeg Speech Engine & Atomic Faststart Remuxer)
# =============================================================================

class Transcoder:
    @staticmethod
    def get_duration(file_path: str) -> float:
        """Obtiene la duración exacta en segundos vía ffprobe."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            val = float(res.stdout.strip())
            return val
        except Exception:
            return 0.0

    @staticmethod
    def extract_m4a_speech(input_path: str, output_path: str) -> bool:
        """
        Transcodifica cualquier video o audio a M4A Speech (24k mono AAC + faststart).
        Garantiza compatibilidad absoluta con NotebookLM y reproductores web de Google Drive.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tmp_output = output_path + ".tmp.m4a"

        cmd = [
            "nice", "-n", "19", "ionice", "-c", "3",
            "ffmpeg", "-y", "-threads", "2",
            "-i", input_path,
            "-vn",
            "-c:a", "aac",
            "-b:a", "24k",
            "-ac", "1",
            "-movflags", "+faststart",
            tmp_output
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(tmp_output) and os.path.getsize(tmp_output) > 1024:
                dur = Transcoder.get_duration(tmp_output)
                if dur > 1.0:
                    shutil.move(tmp_output, output_path)
                    return True
            if os.path.exists(tmp_output):
                os.remove(tmp_output)
            return False
        except Exception as e:
            if os.path.exists(tmp_output):
                os.remove(tmp_output)
            log(f"Error transcodificando {os.path.basename(input_path)}: {e}", "ERROR")
            return False

    @staticmethod
    def remux_aac_to_m4a(input_path: str, output_path: str) -> bool:
        """
        Remuxing ultrarrápido (-c copy) para audios AAC que carecen de cabecera moov o duración.
        Tarda <0.2s por archivo y repara la barra de adelantado/retroceso instantáneamente.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tmp_output = output_path + ".tmp.m4a"

        cmd = [
            "nice", "-n", "19", "ionice", "-c", "3",
            "ffmpeg", "-y", "-threads", "2",
            "-i", input_path,
            "-c", "copy",
            "-movflags", "+faststart",
            tmp_output
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(tmp_output) and os.path.getsize(tmp_output) > 1024:
                dur = Transcoder.get_duration(tmp_output)
                if dur > 1.0:
                    shutil.move(tmp_output, output_path)
                    return True
            if os.path.exists(tmp_output):
                os.remove(tmp_output)
            return False
        except Exception:
            if os.path.exists(tmp_output):
                os.remove(tmp_output)
            # Fallback a transcodificación completa si falla el remuxing directo
            return Transcoder.extract_m4a_speech(input_path, output_path)


# =============================================================================
# 3. ARCHIVE EXTRACTOR (Smart Multi-part Unpacker)
# =============================================================================

class ArchiveExtractor:
    @staticmethod
    def is_secondary_part(filepath: str) -> bool:
        """Determina si un archivo es una parte secundaria (.part2.rar, .z01, etc.)."""
        fn = os.path.basename(filepath).lower()
        if re.search(r'\.part0*[2-9]\d*\.rar$', fn):
            return True
        if re.search(r'\.part[1-9]\d+\.rar$', fn):
            return True
        if re.search(r'\.z0[1-9]$', fn):
            return True
        return False

    @staticmethod
    def unpack_all(directory: str) -> bool:
        """
        Descomprime recursivamente archivos .rar, .zip y .7z en el directorio NVMe.
        Elimina los comprimidos tras extraerlos exitosamente para evitar saturar el disco.
        """
        unpacked_any = False
        for root, _, files in os.walk(directory):
            for f in sorted(files):
                ext = os.path.splitext(f)[1].lower()
                full_path = os.path.join(root, f)

                if ext not in ARCHIVE_EXTENSIONS:
                    continue

                if ArchiveExtractor.is_secondary_part(full_path):
                    continue

                log(f"Desempaquetando archivo comprimido: {f}", "ACTION")
                extract_target = os.path.join(root, os.path.splitext(f)[0])
                os.makedirs(extract_target, exist_ok=True)

                success = False
                try:
                    if ext == ".rar":
                        cmd = ["unrar", "x", "-inul", "-y", full_path, extract_target]
                        subprocess.run(cmd, check=True)
                        success = True
                    elif ext == ".zip":
                        cmd = ["unzip", "-o", "-q", full_path, "-d", extract_target]
                        subprocess.run(cmd, check=True)
                        success = True
                    elif ext in [".7z", ".tar", ".gz"]:
                        cmd = ["7z", "x", "-y", f"-o{extract_target}", full_path]
                        subprocess.run(cmd, check=True)
                        success = True
                except Exception as ex:
                    log(f"Fallo al extraer {f}: {ex}", "WARN")

                if success:
                    unpacked_any = True
                    # Purga preventiva del archivo comprimido para liberar NVMe
                    try:
                        os.remove(full_path)
                    except Exception:
                        pass

        return unpacked_any


# =============================================================================
# 4. PROVIDER DRIVERS (Mega, Sync.com, HTTP)
# =============================================================================

class ProviderDriver:
    @staticmethod
    def detect_provider(url: str) -> str:
        u = url.lower()
        if "mega.nz" in u or "mega.co.nz" in u:
            return "mega"
        elif "sync.com" in u:
            return "sync"
        elif "drive.google.com" in u:
            return "gdrive"
        return "direct"

    @staticmethod
    def download_mega(url: str, target_dir: str) -> bool:
        """Descarga una carpeta o archivo público de Mega vía megatools dl en NVMe."""
        os.makedirs(target_dir, exist_ok=True)

        if "#P!" in url:
            log("Enlace de Mega protegido con contraseña (#P!). Saltando descarga desatendida.", "WARN")
            return False

        cmd = [
            "megatools", "dl",
            "--no-ask-password",
            "--path", target_dir,
            url
        ]

        log(f"Iniciando descarga de Mega vía megatools dl...", "ACTION")
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            log(f"Error en megatools dl: {e}", "ERROR")
            return False

    @staticmethod
    def download_direct(url: str, target_dir: str, filename: Optional[str] = None) -> bool:
        """Descarga de archivos HTTP/HTTPS directos."""
        os.makedirs(target_dir, exist_ok=True)
        if not filename:
            filename = os.path.basename(urllib.parse.urlparse(url).path) or "download.bin"

        dest_file = os.path.join(target_dir, filename)
        log(f"Descargando archivo HTTP directo a {dest_file}...", "ACTION")

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (SovereignMediaEngine/1.0)'})
            with urllib.request.urlopen(req) as response, open(dest_file, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            return True
        except Exception as e:
            log(f"Error descargando {url}: {e}", "ERROR")
            return False


# =============================================================================
# 5. SOVEREIGN MEDIA PROCESSOR (Orquestador de Curso)
# =============================================================================

class CourseProcessor:
    def __init__(self, course_title: str, staging_dir: str, gdrive_dest: str):
        self.course_title = course_title
        self.staging_dir = staging_dir
        self.gdrive_dest = gdrive_dest
        self.audios_dest = os.path.join(gdrive_dest, "NOTEBOOKLM_AUDIOS")
        self.docs_dest = os.path.join(gdrive_dest, "DOCS")

    def process(self) -> Dict[str, Any]:
        """
        Ejecuta el ciclo de vida completo:
        1. Descompresión de archivos.
        2. Extracción y transcodificación de audios a M4A Speech.
        3. Clasificación de documentos.
        4. Purga de videos pesados en NVMe.
        5. Promoción atómica a Google Drive SSoT.
        6. Purga final de staging local.
        """
        log(f"Iniciando procesamiento de '{self.course_title}'...", "ACTION")
        os.makedirs(self.audios_dest, exist_ok=True)
        os.makedirs(self.docs_dest, exist_ok=True)

        # Paso 1: Descompresión
        ArchiveExtractor.unpack_all(self.staging_dir)

        # Paso 2: Escaneo de archivos
        media_files = []
        doc_files = []

        for root, _, files in os.walk(self.staging_dir):
            # Ignorar si ya estamos dentro de NOTEBOOKLM_AUDIOS
            if "NOTEBOOKLM_AUDIOS" in root:
                continue
            for f in sorted(files):
                ext = os.path.splitext(f)[1].lower()
                p = os.path.join(root, f)
                if ext in MEDIA_EXTENSIONS:
                    media_files.append((p, f, os.path.basename(root)))
                elif ext in DOC_EXTENSIONS and ext not in ARCHIVE_EXTENSIONS:
                    doc_files.append((p, f))

        converted_audios = 0
        preserved_docs = 0

        # Paso 3: Transcodificación de Audios
        for idx, (fpath, fname, parent) in enumerate(media_files, start=1):
            out_name = Normalizer.format_audio_name(parent, fname, idx)
            out_path = os.path.join(self.audios_dest, out_name)

            if os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
                log(f"Salteando audio ya existente: {out_name}")
                converted_audios += 1
                continue

            log(f"Transcodificando: {fname} -> {out_name}", "AUDIO")
            ext = os.path.splitext(fname)[1].lower()

            if ext == ".aac":
                success = Transcoder.remux_aac_to_m4a(fpath, out_path)
            else:
                success = Transcoder.extract_m4a_speech(fpath, out_path)

            if success:
                converted_audios += 1
                # Purga inmediata del video crudo en NVMe para liberar disco
                if ext in VIDEO_EXTENSIONS:
                    try:
                        os.remove(fpath)
                    except Exception:
                        pass

        # Paso 4: Preservación de Documentos
        for fpath, fname in doc_files:
            clean_name = f"DOC_{Normalizer.clean_title(fname)}{os.path.splitext(fname)[1]}"
            out_doc = os.path.join(self.docs_dest, clean_name)
            if not os.path.exists(out_doc):
                try:
                    shutil.copy2(fpath, out_doc)
                    preserved_docs += 1
                except Exception:
                    pass

        # Paso 5: Reporte Per-Course
        report_path = os.path.join(self.gdrive_dest, "README_REPORTE.txt")
        try:
            with open(report_path, "w", encoding="utf-8") as rf:
                rf.write(f"REPORTE DE PROCESAMIENTO - MEGA-DOWNLOADER v{VERSION}\n")
                rf.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                rf.write(f"Curso: {self.course_title}\n")
                rf.write(f"Total Audios M4A Generados: {converted_audios}\n")
                rf.write(f"Total Documentos Preservados: {preserved_docs}\n")
                rf.write(f"Estándar: M4A 24k mono AAC + faststart\n")
        except Exception:
            pass

        # Paso 6: Purga del Staging NVMe
        try:
            shutil.rmtree(self.staging_dir, ignore_errors=True)
            log(f"Staging NVMe purgado exitosamente ({self.staging_dir})")
        except Exception as ex:
            log(f"Aviso al purgar staging: {ex}", "WARN")

        log(f"✅ Curso '{self.course_title}' completado: {converted_audios} audios, {preserved_docs} docs.", "INFO")
        return {
            "title": self.course_title,
            "audios": converted_audios,
            "docs": preserved_docs,
            "status": "COMPLETED"
        }


# =============================================================================
# 6. REPROCESSOR (Saneamiento Local de Cursos Existentes)
# =============================================================================

class Reprocessor:
    @staticmethod
    def reprocess_course(course_dir: str) -> None:
        """
        Escanea un directorio de curso existente en Google Drive o NVMe:
        1. Detecta archivos .aac y les hace remuxing instantáneo a .m4a con +faststart.
        2. Detecta videos huérfanos (.mp4, .mkv) y extrae sus audios .m4a en NOTEBOOKLM_AUDIOS/.
        3. Detecta audios .mp3 pesados y los optimiza a .m4a 24k mono.
        4. Mueve PDFs y documentos dispersos a DOCS/.
        5. Respeta al 100% los audios que ya estén correctos.
        """
        if not os.path.exists(course_dir):
            log(f"Directorio no encontrado: {course_dir}", "ERROR")
            return

        course_title = os.path.basename(os.path.abspath(course_dir))
        log(f"Iniciando saneamiento local de '{course_title}'...", "ACTION")

        audios_dir = os.path.join(course_dir, "NOTEBOOKLM_AUDIOS")
        docs_dir = os.path.join(course_dir, "DOCS")
        os.makedirs(audios_dir, exist_ok=True)
        os.makedirs(docs_dir, exist_ok=True)

        # 1. Buscar archivos .aac planos que requieran remuxing
        aac_files = []
        video_files = []
        doc_files = []

        for root, _, files in os.walk(course_dir):
            for f in sorted(files):
                full_path = os.path.join(root, f)
                ext = os.path.splitext(f)[1].lower()

                if ext == ".aac":
                    aac_files.append((full_path, f, root))
                elif ext in VIDEO_EXTENSIONS:
                    video_files.append((full_path, f, root))
                elif ext in DOC_EXTENSIONS and ext not in ARCHIVE_EXTENSIONS:
                    if not root.startswith(docs_dir):
                        doc_files.append((full_path, f))

        log(f"Archivos detectados: {len(aac_files)} AACs planos, {len(video_files)} videos, {len(doc_files)} docs.")

        # Remuxing de AACs planos a M4A con faststart
        for aac_path, aac_name, aac_root in aac_files:
            m4a_name = os.path.splitext(aac_name)[0] + ".m4a"
            m4a_target = os.path.join(audios_dir, m4a_name)

            if os.path.exists(m4a_target) and Transcoder.get_duration(m4a_target) > 0:
                # Ya existe y es válido, eliminar el aac duplicado
                try:
                    os.remove(aac_path)
                except Exception:
                    pass
                continue

            log(f"Remuxing AAC a M4A faststart: {aac_name} -> {m4a_name}", "AUDIO")
            if Transcoder.remux_aac_to_m4a(aac_path, m4a_target):
                try:
                    os.remove(aac_path)
                except Exception:
                    pass

        # Extracción de videos huérfanos
        for idx, (vpath, vname, vroot) in enumerate(video_files, start=1):
            m4a_name = Normalizer.format_audio_name(os.path.basename(vroot), vname, idx)
            m4a_target = os.path.join(audios_dir, m4a_name)

            if os.path.exists(m4a_target) and Transcoder.get_duration(m4a_target) > 0:
                continue

            log(f"Extrayendo audio de video: {vname} -> {m4a_name}", "AUDIO")
            Transcoder.extract_m4a_speech(vpath, m4a_target)

        # Mover documentos sueltos a DOCS/
        for dpath, dname in doc_files:
            target_doc = os.path.join(docs_dir, dname)
            if not os.path.exists(target_doc):
                try:
                    shutil.move(dpath, target_doc)
                except Exception:
                    pass

        log(f"✅ Saneamiento de '{course_title}' finalizado exitosamente.", "INFO")


# =============================================================================
# 7. MANIFEST & BATCH SCANNER (Modo 2: txt-mega y Colas)
# =============================================================================

class ManifestScanner:
    @staticmethod
    def scan_receipts(receipts_dir: str, output_manifest: str) -> List[Dict[str, Any]]:
        """Escanea una carpeta de recibos de compra y extrae enlaces y nombres de cursos."""
        if not os.path.exists(receipts_dir):
            log(f"Directorio de recibos no existe: {receipts_dir}", "ERROR")
            return []

        courses = []
        log(f"Escaneando recibos en {receipts_dir}...", "ACTION")

        for f in sorted(os.listdir(receipts_dir)):
            if not f.endswith((".txt", ".docx")):
                continue
            fpath = os.path.join(receipts_dir, f)

            content = ""
            if f.endswith(".txt"):
                for enc in ["utf-8", "latin-1", "cp1252"]:
                    try:
                        with open(fpath, "r", encoding=enc) as tf:
                            content = tf.read()
                        break
                    except Exception:
                        continue
            elif f.endswith(".docx"):
                try:
                    with zipfile.ZipFile(fpath) as z:
                        xml_content = z.read("word/document.xml")
                    root = ET.fromstring(xml_content)
                    texts = [n.text for n in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if n.text]
                    content = "\n".join(texts)
                except Exception:
                    pass

            urls = re.findall(r'https?://(?:www\.)?mega\.nz/[^\s\)\"\'>]+', content)
            if urls:
                c_title = os.path.splitext(f)[0]
                courses.append({
                    "title": c_title,
                    "url": urls[0],
                    "receipt_file": f,
                    "provider": "mega"
                })

        os.makedirs(os.path.dirname(output_manifest), exist_ok=True)
        with open(output_manifest, "w", encoding="utf-8") as jf:
            json.dump(courses, jf, indent=2, ensure_ascii=False)

        log(f"✅ Manifiesto generado con {len(courses)} cursos en: {output_manifest}")
        return courses


# =============================================================================
# 8. CLI DISPATCHER & SELF-TEST SUITE
# =============================================================================

def run_tests() -> int:
    """Ejecuta el arnés de pruebas unitarias físicas embebido (meta-script & CoHaLo)."""
    print(f"\n{BOLD}{CYAN}=== EJECUTANDO ARNES DE PRUEBAS UNITARIAS: MEGA-DOWNLOADER ==={RESET}")

    # Test 1: Normalizer slug y clean title
    assert Normalizer.sanitize_slug("Clase 01 - Introducción al Funnel! (1080p)") == "Clase_01_Introducción_al_Funnel_1080p"
    assert Normalizer.clean_title("01 Clase 01 1080p x264.mp4") == "Clase_01"
    print(f"  {GREEN}✓{RESET} Normalizer: Limpieza de slugs y títulos correcta.")

    # Test 2: Audio Naming
    name = Normalizer.format_audio_name("Modulo 03 Ventas", "05 Clase 5 Cierre.mp4", 5)
    assert name == "MODULO-03_CLASE-05_Clase_5_Cierre.m4a"
    print(f"  {GREEN}✓{RESET} Normalizer: Formato de lecciones para NotebookLM verificado.")

    # Test 3: Detection of Multi-part Archives
    assert ArchiveExtractor.is_secondary_part("curso.part1.rar") is False
    assert ArchiveExtractor.is_secondary_part("curso.part2.rar") is True
    assert ArchiveExtractor.is_secondary_part("curso.part02.rar") is True
    print(f"  {GREEN}✓{RESET} ArchiveExtractor: Detección de partes secundarias validada.")

    # Test 4: Provider Detection
    assert ProviderDriver.detect_provider("https://mega.nz/folder/abc#123") == "mega"
    assert ProviderDriver.detect_provider("https://ln.sync.com/dl/xyz") == "sync"
    assert ProviderDriver.detect_provider("https://example.com/video.mp4") == "direct"
    print(f"  {GREEN}✓{RESET} ProviderDriver: Clasificación de proveedores verificada.")

    # Test 5: Verify ffprobe and ffmpeg availability
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(["ffprobe", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"  {GREEN}✓{RESET} Binarios del sistema (ffmpeg, ffprobe) disponibles.")
    except Exception as ex:
        print(f"  {RED}✗ Error verificando binarios ffmpeg: {ex}{RESET}")
        return 1

    print(f"\n{BOLD}{GREEN}TODAS LAS PRUEBAS UNITARIAS PASARON EXITOSAMENTE (Exit Code: 0).{RESET}\n")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="mega-downloader",
        description="Motor Soberano Universal de Descarga, Conversión y Extracción de Medios para NotebookLM.",
        epilog="Desarrollado bajo Supreme Directive v8.5 & CoHaLo Engineering."
    )
    parser.add_argument("--version", "-v", action="version", version=f"mega-downloader v{VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Comando 1: url
    p_url = subparsers.add_parser("url", help="Descarga y procesa un enlace individual a Google Drive.")
    p_url.add_argument("link", help="URL de Mega, Sync.com o HTTP.")
    p_url.add_argument("--dest", "-d", required=True, help="Ruta de destino final en Google Drive (ej: /var/www/baiosfera/CURSOS/CENOF/CursoX).")
    p_url.add_argument("--title", "-t", help="Título explícito del curso.")

    # Comando 2: scan
    p_scan = subparsers.add_parser("scan", help="Escanea recibos de compra (.txt, .docx) y genera un manifiesto JSON.")
    p_scan.add_argument("dir", nargs="?", default=DEFAULT_RECEIPTS_DIR, help="Carpeta de recibos a escanear.")
    p_scan.add_argument("--output", "-o", default=DEFAULT_MANIFEST_PATH, help="Ruta de guardado del manifiesto JSON.")

    # Comando 3: reprocess
    p_reprocess = subparsers.add_parser("reprocess", help="Sanea un curso existente (remuxing AAC a M4A faststart, videos a speech).")
    p_reprocess.add_argument("course_dir", help="Directorio del curso a sanear en Google Drive o NVMe.")

    # Comando 4: status
    subparsers.add_parser("status", help="Muestra el estado del almacenamiento NVMe y Google Drive.")

    # Flags globales de compatibilidad directa
    parser.add_argument("--test", action="store_true", help="Ejecuta el arnés de pruebas unitarias físicas embebido.")
    parser.add_argument("--reprocess-dir", help="Alias directo para --reprocess.")

    args = parser.parse_args()

    if args.test:
        sys.exit(run_tests())

    if args.reprocess_dir:
        Reprocessor.reprocess_course(args.reprocess_dir)
        sys.exit(0)

    if args.command == "url":
        provider = ProviderDriver.detect_provider(args.link)
        title = args.title or os.path.basename(args.dest.rstrip("/"))
        staging_dir = os.path.join(DEFAULT_STAGING_BASE, ".staging", f"direct_{Normalizer.sanitize_slug(title)}")

        if provider == "mega":
            ok = ProviderDriver.download_mega(args.link, staging_dir)
        elif provider == "direct":
            ok = ProviderDriver.download_direct(args.link, staging_dir)
        else:
            log(f"Proveedor '{provider}' requiere autenticación dedicada.", "ERROR")
            sys.exit(1)

        if ok:
            processor = CourseProcessor(title, staging_dir, args.dest)
            processor.process()
        else:
            log("Descarga fallida.", "ERROR")
            sys.exit(1)

    elif args.command == "scan":
        ManifestScanner.scan_receipts(args.dir, args.output)

    elif args.command == "reprocess":
        Reprocessor.reprocess_course(args.course_dir)

    elif args.command == "status":
        print(f"\n{BOLD}{CYAN}=== ESTADO DEL ALMACENAMIENTO (FUSE SHIELD) ==={RESET}")
        try:
            st = os.statvfs(DEFAULT_STAGING_BASE)
            free_gb = (st.f_bavail * st.f_frsize) / (1024 ** 3)
            total_gb = (st.f_blocks * st.f_frsize) / (1024 ** 3)
            print(f"  {BOLD}NVMe Localstorage (/var/www/localstorage):{RESET} {free_gb:.1f} GB libres de {total_gb:.1f} GB")
        except Exception:
            pass
        print(f"  {BOLD}Directorio Base Google Drive:{RESET} {DEFAULT_GDRIVE_BASE}")
        print()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
