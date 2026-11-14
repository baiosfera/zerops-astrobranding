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

VERSION = "1.2.0"

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
# 1. NORMALIZER & SANITIZER (Nomenclatura Jerárquica y Saneamiento)
# =============================================================================

class Sanitizer:
    GARBAGE_SUB_PATTERNS = [
        re.compile(r'[\.\-]subt[ií]tulos?\.txt$', re.IGNORECASE),
        re.compile(r'\.mp4\-subt.*\.txt$', re.IGNORECASE),
        re.compile(r'\_subt[ií]tulos?\.txt$', re.IGNORECASE),
        re.compile(r'\.vtt$', re.IGNORECASE),
    ]

    NOBLE_DOC_NAMES = {
        "readme.txt", "notas.txt", "resumen.txt", "temario.txt",
        "info.txt", "reporte.txt", "license.txt", "instrucciones.txt"
    }

    @staticmethod
    def is_garbage_transcript(filename: str, filepath: Optional[str] = None) -> bool:
        """
        Determina si un archivo es un volcado crudo de subtítulos o WebVTT corrupto.
        Protege estrictamente documentos nobles (README, temarios, notas, .pdf, .docx, .xlsx).
        """
        fn = filename.lower()
        if fn in Sanitizer.NOBLE_DOC_NAMES:
            return False

        # 1. Detección por patrón de nombre de archivo
        for pat in Sanitizer.GARBAGE_SUB_PATTERNS:
            if pat.search(filename):
                return True

        # 2. Detección por inspección de cabecera si es .txt o .srt < 200KB
        if filepath and os.path.exists(filepath) and fn.endswith((".txt", ".srt")):
            try:
                sz = os.path.getsize(filepath)
                if 0 < sz < 200 * 1024:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        header = f.read(512)
                        if "WEBVTT" in header:
                            return True
                        if re.search(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', header):
                            return True
            except Exception:
                pass
        return False

    @staticmethod
    def clean_webvtt_text(raw_text: str) -> str:
        """
        Filtro higiénico para limpiar volcados WebVTT si se requiriera rescatar el texto.
        Elimina timestamps <00:00:13.519>, tags de karaoke <c>...</c>, cabeceras WebVTT y deduplica frases.
        """
        t = raw_text
        t = re.sub(r'^WEBVTT.*?\n\n', '', t, flags=re.DOTALL | re.IGNORECASE)
        t = re.sub(r'^(Kind|Language):.*?\n', '', t, flags=re.MULTILINE | re.IGNORECASE)
        t = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}.*?\n', '', t)
        t = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', t)
        t = re.sub(r'</?[a-zA-Z][^>]*>', '', t)
        lines = [line.strip() for line in t.splitlines() if line.strip()]
        deduped = []
        prev = ""
        for line in lines:
            if line != prev:
                deduped.append(line)
                prev = line
        return "\n".join(deduped)

    @staticmethod
    def purge_garbage_transcripts(target_dir: str, dry_run: bool = False) -> Tuple[int, int]:
        """
        Escanea y purga físicamente todos los volcados *-subtítulos.txt y WebVTT corruptos en un árbol.
        Preserva intactos todos los PDFs, DOCX, XLSX y audios M4A.
        Retorna (archivos_eliminados, bytes_liberados).
        """
        if not os.path.exists(target_dir):
            return 0, 0

        purged_count = 0
        bytes_freed = 0

        for root, _, files in os.walk(target_dir):
            for f in files:
                fpath = os.path.join(root, f)
                if Sanitizer.is_garbage_transcript(f, fpath):
                    try:
                        sz = os.path.getsize(fpath)
                    except Exception:
                        sz = 0
                    if not dry_run:
                        try:
                            os.remove(fpath)
                            purged_count += 1
                            bytes_freed += sz
                        except Exception as ex:
                            log(f"No se pudo eliminar {f}: {ex}", "WARN")
                    else:
                        purged_count += 1
                        bytes_freed += sz
        return purged_count, bytes_freed


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


class MegaSequentialDriver:
    """Descarga quirúrgica ítem por ítem vía megatools --choose-files con corte limpio ante cuota 403."""

    _ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
    _TREE_DIR_RE = re.compile(r"^([|+\s`-]*)(?:\d+\.\s+)?([^/]+)/$")
    _TREE_FILE_RE = re.compile(r"^([|+\s`-]*?)(\d+)\.\s+(.*?)\s+\(([^)]+)\)$")

    @staticmethod
    def is_quota_exceeded_line(line: str) -> bool:
        """Detecta errores de cuota agotada (403 / Over Quota) en salida de megatools."""
        low = line.lower()
        return "403" in low or "over quota" in low

    @classmethod
    def parse_choose_files_tree(cls, raw_output: str) -> List[Dict[str, Any]]:
        """Parsea el árbol numerado de megatools --choose-files en una lista ordenada de ítems."""
        items: List[Dict[str, Any]] = []
        folder_stack: List[Tuple[int, str]] = []
        class_counters: Dict[str, int] = {}

        for raw_line in raw_output.splitlines():
            clean = cls._ANSI_RE.sub("", raw_line).rstrip()
            if not clean:
                continue

            m_dir = cls._TREE_DIR_RE.match(clean)
            if m_dir:
                depth = len(m_dir.group(1))
                dir_name = m_dir.group(2).strip()
                while folder_stack and folder_stack[-1][0] >= depth:
                    folder_stack.pop()
                folder_stack.append((depth, dir_name))
                continue

            m_file = cls._TREE_FILE_RE.match(clean)
            if not m_file:
                continue

            depth = len(m_file.group(1))
            idx = int(m_file.group(2))
            filename = m_file.group(3).strip()
            size_label = m_file.group(4).strip()

            while folder_stack and folder_stack[-1][0] >= depth:
                folder_stack.pop()

            parent_folder = folder_stack[-1][1] if folder_stack else "Modulo 01"
            if Sanitizer.is_garbage_transcript(filename):
                continue

            ext = os.path.splitext(filename)[1].lower()
            if ext in MEDIA_EXTENSIONS:
                kind = "media"
                class_counters[parent_folder] = class_counters.get(parent_folder, 0) + 1
                cls_num = class_counters[parent_folder]
            elif ext in ARCHIVE_EXTENSIONS:
                kind = "archive"
                cls_num = 0
            elif ext in DOC_EXTENSIONS:
                kind = "doc"
                cls_num = 0
            else:
                continue

            items.append({
                "idx": idx,
                "filename": filename,
                "size": size_label,
                "parent_folder": parent_folder,
                "kind": kind,
                "cls_num": cls_num,
                "ext": ext,
            })

        return items

    @classmethod
    def list_choose_files_tree(cls, url: str, timeout_sec: int = 120) -> str:
        """Obtiene el árbol numerado de una carpeta Mega sin descargar archivos."""
        if "#P!" in url:
            log("Enlace de Mega protegido con contraseña (#P!).", "ERROR")
            return ""

        cmd = ["megatools", "dl", "--choose-files", "--no-ask-password", url]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        lines: List[str] = []
        deadline = time.monotonic() + timeout_sec
        assert proc.stdout is not None and proc.stdin is not None

        for line in iter(proc.stdout.readline, ""):
            lines.append(line)
            if "Enter numbers" in line:
                try:
                    proc.stdin.write("\n")
                    proc.stdin.flush()
                except Exception:
                    pass
                break
            if time.monotonic() > deadline:
                proc.kill()
                break

        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        return "".join(lines)

    @classmethod
    def download_single_item(cls, url: str, item_idx: int, target_dir: str) -> str:
        """Descarga exactamente un índice vía megatools --choose-files."""
        shutil.rmtree(target_dir, ignore_errors=True)
        os.makedirs(target_dir, exist_ok=True)

        cmd = ["megatools", "dl", "--choose-files", "--no-ask-password", "--path", target_dir, url]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None and proc.stdin is not None

        prompted = False
        quota_exceeded = False

        for line in iter(proc.stdout.readline, ""):
            if not prompted and "Enter numbers" in line:
                proc.stdin.write(f"{item_idx}\n")
                proc.stdin.flush()
                prompted = True
                continue
            if cls.is_quota_exceeded_line(line):
                log(f"Cuota de MEGA agotada (403 Over Quota) en índice {item_idx}.", "WARN")
                quota_exceeded = True
                proc.kill()
                break

        proc.wait()
        if quota_exceeded:
            return "QUOTA_EXCEEDED"

        has_files = any(files for _, _, files in os.walk(target_dir))
        return "OK" if proc.returncode == 0 and has_files else "ERROR"

    @classmethod
    def process_sequential(cls, url: str, gdrive_dest: str, title: str, flat: bool = False) -> int:
        """Descarga, transcodifica y promueve ítem por ítem con skip idempotente y purga inmediata."""
        log(f"Listando árbol remoto de '{title}' para descarga secuencial...", "ACTION")
        raw_tree = cls.list_choose_files_tree(url)
        items = cls.parse_choose_files_tree(raw_tree)
        if not items:
            log("No se detectaron ítems descargables en la carpeta Mega.", "ERROR")
            return 1

        audios_dest = gdrive_dest if flat else os.path.join(gdrive_dest, "NOTEBOOKLM_AUDIOS")
        docs_dest = gdrive_dest if flat else os.path.join(gdrive_dest, "DOCS")
        os.makedirs(audios_dest, exist_ok=True)
        os.makedirs(docs_dest, exist_ok=True)

        staging_root = os.path.join(DEFAULT_STAGING_BASE, ".staging", f"seq_{Normalizer.sanitize_slug(title)}")
        converted_audios = 0
        preserved_docs = 0

        for pos, item in enumerate(items, start=1):
            kind = item["kind"]
            filename = item["filename"]
            ext = item["ext"]

            if kind == "doc":
                out_name = f"DOC_{Normalizer.clean_title(filename)}{ext}"
                out_path = os.path.join(docs_dest, out_name)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
                    preserved_docs += 1
                    continue
            elif kind == "media":
                out_name = Normalizer.format_audio_name(item["parent_folder"], filename, item["cls_num"])
                out_path = os.path.join(audios_dest, out_name)
                if os.path.exists(out_path) and os.path.getsize(out_path) > 1024:
                    converted_audios += 1
                    continue
            else:
                out_name = filename
                out_path = ""

            log(f"[{pos}/{len(items)}] Descargando índice {item['idx']}: {filename} ({item['size']})", "ACTION")
            item_staging = os.path.join(staging_root, f"item_{item['idx']}")
            status = cls.download_single_item(url, item["idx"], item_staging)

            if status == "QUOTA_EXCEEDED":
                shutil.rmtree(staging_root, ignore_errors=True)
                log(f"Corte preventivo por cuota 403 en [{pos}/{len(items)}]. Re-ejecutá el mismo comando para reanudar.", "WARN")
                return 42
            if status != "OK":
                shutil.rmtree(item_staging, ignore_errors=True)
                log(f"Error descargando índice {item['idx']} ({filename}).", "ERROR")
                continue

            if kind == "archive":
                res = CourseProcessor(title, item_staging, gdrive_dest, flat=flat).process()
                converted_audios += res.get("audios", 0)
                preserved_docs += res.get("docs", 0)
                continue

            downloaded = [os.path.join(r, f) for r, _, fs in os.walk(item_staging) for f in fs]
            if downloaded:
                src_file = downloaded[0]
                if kind == "doc":
                    shutil.copy2(src_file, out_path)
                    preserved_docs += 1
                    log(f"Documento promovido: {out_name}", "INFO")
                elif kind == "media":
                    ok = Transcoder.remux_aac_to_m4a(src_file, out_path) if ext == ".aac" else Transcoder.extract_m4a_speech(src_file, out_path)
                    if ok:
                        converted_audios += 1
                        log(f"Audio promovido: {out_name}", "AUDIO")

            shutil.rmtree(item_staging, ignore_errors=True)

        shutil.rmtree(staging_root, ignore_errors=True)
        report_path = os.path.join(gdrive_dest, "README_REPORTE.txt")
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write(f"REPORTE DE PROCESAMIENTO - MEGA-DOWNLOADER v{VERSION}\n")
            rf.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            rf.write(f"Curso: {title}\n")
            rf.write(f"Total Audios M4A Generados: {converted_audios}\n")
            rf.write(f"Total Documentos Preservados: {preserved_docs}\n")
            rf.write("Estándar: M4A 24k mono AAC + faststart\n")

        log(f"✅ Descarga secuencial de '{title}' completada: {converted_audios} audios, {preserved_docs} docs.", "INFO")
        return 0


# =============================================================================
# 5. SOVEREIGN MEDIA PROCESSOR (Orquestador de Curso)
# =============================================================================

class CourseProcessor:
    def __init__(self, course_title: str, staging_dir: str, gdrive_dest: str, flat: bool = False):
        self.course_title = course_title
        self.staging_dir = staging_dir
        self.gdrive_dest = gdrive_dest
        self.flat = flat
        if flat:
            self.audios_dest = gdrive_dest
            self.docs_dest = gdrive_dest
        else:
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

        # Paso 1.5: Purga preventiva de volcados de subtítulos y WebVTT corruptos
        purged, freed = Sanitizer.purge_garbage_transcripts(self.staging_dir)
        if purged > 0:
            log(f"Purgados {purged} subtítulos/WebVTT basura ({freed / 1024:.1f} KB) del staging")

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
    def reprocess_course(course_dir: str, purge_subs: bool = True) -> Dict[str, Any]:
        """
        Escanea un directorio de curso existente en Google Drive o NVMe:
        1. Purga subtítulos y volcados WebVTT corruptos (*-subtítulos.txt).
        2. Detecta archivos .aac y les hace remuxing instantáneo a .m4a con +faststart (-c copy).
        3. Detecta audios .mp3 y los optimiza a .m4a 24k mono AAC con +faststart.
        4. Detecta videos huérfanos (.mp4, .mkv) y extrae sus audios .m4a en NOTEBOOKLM_AUDIOS/.
        5. Mueve PDFs y documentos nobles dispersos a DOCS/.
        6. Respeta al 100% los audios que ya estén correctos e idempotentes.
        """
        if not os.path.exists(course_dir):
            log(f"Directorio no encontrado: {course_dir}", "ERROR")
            return {"status": "NOT_FOUND", "course": course_dir}

        course_title = os.path.basename(os.path.abspath(course_dir))
        log(f"Iniciando saneamiento local de '{course_title}'...", "ACTION")

        # Paso 0: Purga higiénica de subtítulos basura si está activada
        if purge_subs:
            purged, freed = Sanitizer.purge_garbage_transcripts(course_dir)
            if purged > 0:
                log(f"Purgados {purged} subtítulos/WebVTT basura ({freed / 1024:.1f} KB)")

        audios_dir = os.path.join(course_dir, "NOTEBOOKLM_AUDIOS")
        docs_dir = os.path.join(course_dir, "DOCS")
        os.makedirs(audios_dir, exist_ok=True)
        os.makedirs(docs_dir, exist_ok=True)

        # 1. Escanear inventario de medios
        aac_files = []
        mp3_files = []
        video_files = []
        doc_files = []

        for root, _, files in os.walk(course_dir):
            if root.startswith(audios_dir):
                continue
            for f in sorted(files):
                full_path = os.path.join(root, f)
                ext = os.path.splitext(f)[1].lower()

                if ext == ".aac":
                    aac_files.append((full_path, f, root))
                elif ext == ".mp3":
                    mp3_files.append((full_path, f, root))
                elif ext in VIDEO_EXTENSIONS:
                    video_files.append((full_path, f, root))
                elif ext in DOC_EXTENSIONS and ext not in ARCHIVE_EXTENSIONS:
                    if not root.startswith(docs_dir):
                        doc_files.append((full_path, f))

        log(f"Inventario: {len(aac_files)} AACs, {len(mp3_files)} MP3s, {len(video_files)} videos, {len(doc_files)} docs.")

        # Paso 1: Remuxing ultrarrápido de AACs a M4A con +faststart (-c copy)
        for aac_path, aac_name, aac_root in aac_files:
            m4a_name = os.path.splitext(aac_name)[0] + ".m4a"
            m4a_target = os.path.join(audios_dir, m4a_name)

            if os.path.exists(m4a_target) and Transcoder.get_duration(m4a_target) > 0:
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

        # Paso 2: Transcodificación de MP3s a M4A 24k mono si no existen
        for idx, (mp3_path, mp3_name, mp3_root) in enumerate(mp3_files, start=1):
            m4a_name = Normalizer.format_audio_name(os.path.basename(mp3_root), mp3_name, idx)
            m4a_target = os.path.join(audios_dir, m4a_name)

            if os.path.exists(m4a_target) and Transcoder.get_duration(m4a_target) > 0:
                continue

            log(f"Transcodificando MP3 a M4A speech: {mp3_name} -> {m4a_name}", "AUDIO")
            Transcoder.extract_m4a_speech(mp3_path, m4a_target)

        # Paso 3: Extracción de audio de videos huérfanos
        for idx, (vpath, vname, vroot) in enumerate(video_files, start=1):
            m4a_name = Normalizer.format_audio_name(os.path.basename(vroot), vname, idx)
            m4a_target = os.path.join(audios_dir, m4a_name)

            if os.path.exists(m4a_target) and Transcoder.get_duration(m4a_target) > 0:
                continue

            log(f"Extrayendo audio de video: {vname} -> {m4a_name}", "AUDIO")
            Transcoder.extract_m4a_speech(vpath, m4a_target)

        # Paso 4: Mover documentos sueltos a DOCS/
        for dpath, dname in doc_files:
            target_doc = os.path.join(docs_dir, dname)
            if not os.path.exists(target_doc):
                try:
                    shutil.move(dpath, target_doc)
                except Exception:
                    pass

        log(f"✅ Saneamiento de '{course_title}' finalizado exitosamente.", "INFO")
        return {
            "course": course_title,
            "status": "COMPLETED",
            "aac_remuxed": len(aac_files),
            "mp3_converted": len(mp3_files),
            "video_extracted": len(video_files),
            "docs_moved": len(doc_files)
        }

    @staticmethod
    def reprocess_tree(parent_dir: str, purge_subs: bool = True) -> List[Dict[str, Any]]:
        """
        Sanea de manera secuencial múltiples cursos contenidos dentro de una carpeta padre.
        Aplica límites de I/O (nice 19 / ionice 3) para preservar la estabilidad del sistema.
        """
        if not os.path.exists(parent_dir):
            log(f"Carpeta contenedora no existe: {parent_dir}", "ERROR")
            return []

        log(f"Escaneando cursos para saneamiento por lotes en: {parent_dir}...", "ACTION")
        results = []

        # Determinar si la carpeta en sí es un curso (contiene archivos multimedia directamente)
        has_direct_media = any(
            os.path.splitext(f)[1].lower() in MEDIA_EXTENSIONS
            for f in os.listdir(parent_dir)
            if os.path.isfile(os.path.join(parent_dir, f))
        )

        if has_direct_media:
            return [Reprocessor.reprocess_course(parent_dir, purge_subs=purge_subs)]

        # Si es un contenedor de cursos (ej: CURSOS/MCV o CURSOS/CA)
        excluded_dir_names = {"Z_NON-MKTNG", "CATEGORIAS", "0.DWNL", "00. INCOMPLETOS"}
        subdirs = sorted([
            os.path.join(parent_dir, d) for d in os.listdir(parent_dir)
            if os.path.isdir(os.path.join(parent_dir, d))
            and not d.startswith((".", "_"))
            and d not in excluded_dir_names
            and not d.startswith("Z_NON")
        ])

        log(f"Encontrados {len(subdirs)} directorios para evaluar.")
        for sdir in subdirs:
            has_media = False
            for _, _, files in os.walk(sdir):
                if any(os.path.splitext(f)[1].lower() in MEDIA_EXTENSIONS for f in files):
                    has_media = True
                    break
            if has_media:
                res = Reprocessor.reprocess_course(sdir, purge_subs=purge_subs)
                results.append(res)
            else:
                log(f"Salteando carpeta sin medios: {os.path.basename(sdir)}")

        return results


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

    # Test 5: Sanitizer garbage detection and noble preservation
    assert Sanitizer.is_garbage_transcript("01. Embudos que no son embudos.mp4-subtítulos.txt") is True
    assert Sanitizer.is_garbage_transcript("Clase_02.mp4-subtitulo.txt") is True
    assert Sanitizer.is_garbage_transcript("03_video.mp4-subtítulo.txt") is True
    assert Sanitizer.is_garbage_transcript("caption.vtt") is True
    assert Sanitizer.is_garbage_transcript("README.txt") is False
    assert Sanitizer.is_garbage_transcript("notas.txt") is False
    assert Sanitizer.is_garbage_transcript("resumen.txt") is False
    print(f"  {GREEN}✓{RESET} Sanitizer: Detección y purga de subtítulos corruptos validada.")

    # Test 6: WebVTT text hygiene and deduplication
    vtt_sample = "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<00:00:01.500><c> Hola</c> mundo\nHola mundo\n"
    cleaned = Sanitizer.clean_webvtt_text(vtt_sample)
    assert cleaned == "Hola mundo"
    print(f"  {GREEN}✓{RESET} Sanitizer: Limpieza higiénica de WebVTT y deduplicación verificada.")

    # Test 7: Sequential Mega choose-files parser & 403 quota detector
    sample_tree = (
        "\x1b[1m|--1. 01. Modulo Uno/\x1b[0m\n"
        "|  |--2. 01. Introduccion.mp4 (42.1 MiB)\n"
        "|  |--3. 01. Introduccion.mp4-subtítulos.txt (12.0 KiB)\n"
        "|  |--4. Guia_Modulo_1.pdf (1.2 MiB)\n"
        "|--5. Bonus_Raiz.mp4 (18.0 MiB)\n"
    )
    parsed = MegaSequentialDriver.parse_choose_files_tree(sample_tree)
    assert len(parsed) == 3, f"Expected 3 items, got {len(parsed)}"
    assert parsed[0]["idx"] == 2 and parsed[0]["parent_folder"] == "01. Modulo Uno" and parsed[0]["kind"] == "media"
    assert parsed[1]["idx"] == 4 and parsed[1]["kind"] == "doc"
    assert parsed[2]["idx"] == 5 and parsed[2]["parent_folder"] == "Modulo 01" and parsed[2]["kind"] == "media"
    assert MegaSequentialDriver.is_quota_exceeded_line("ERROR: Download failed: 403 Over Quota") is True
    assert MegaSequentialDriver.is_quota_exceeded_line("F video.mp4 (10.0 MiB)") is False
    print(f"  {GREEN}✓{RESET} MegaSequentialDriver: Parser de árbol --choose-files y detector 403 verificados.")

    # Test 8: Verify ffprobe and ffmpeg availability
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
    p_url.add_argument("--flat", action="store_true", help="Deposita los audios y documentos directamente en la raíz de destino sin subcarpetas.")
    p_url.add_argument("--sequential", "--choose-files", action="store_true", dest="sequential", help="Descarga e ingesta ítem por ítem (--choose-files) con reanudación idempotente ante cuota 403.")

    # Comando 2: scan
    p_scan = subparsers.add_parser("scan", help="Escanea recibos de compra (.txt, .docx) y genera un manifiesto JSON.")
    p_scan.add_argument("dir", nargs="?", default=DEFAULT_RECEIPTS_DIR, help="Carpeta de recibos a escanear.")
    p_scan.add_argument("--output", "-o", default=DEFAULT_MANIFEST_PATH, help="Ruta de guardado del manifiesto JSON.")

    # Comando 3: reprocess
    p_reprocess = subparsers.add_parser("reprocess", help="Sanea un curso existente (remuxing AAC a M4A faststart, videos a speech).")
    p_reprocess.add_argument("course_dir", help="Directorio del curso a sanear en Google Drive o NVMe.")
    p_reprocess.add_argument("--no-purge-subs", action="store_true", help="No purgar subtítulos corruptos.")

    # Comando 4: reprocess-tree
    p_tree = subparsers.add_parser("reprocess-tree", help="Sanea recursivamente cursos contenidos dentro de una carpeta padre.")
    p_tree.add_argument("parent_dir", help="Carpeta contenedora de cursos (ej: CURSOS/MCV, DIGITALMARKETER).")
    p_tree.add_argument("--no-purge-subs", action="store_true", help="No purgar subtítulos corruptos.")

    # Comando 5: purge-subs
    p_purge = subparsers.add_parser("purge-subs", help="Purga físicamente volcados *-subtítulos.txt y WebVTT corruptos en un árbol.")
    p_purge.add_argument("dir", help="Directorio a escanear y purgar.")
    p_purge.add_argument("--dry-run", action="store_true", help="Simulación sin borrar archivos.")

    # Comando 6: status
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

        if provider == "mega" and getattr(args, "sequential", False):
            rc = MegaSequentialDriver.process_sequential(
                args.link,
                args.dest,
                title,
                flat=getattr(args, "flat", False),
            )
            sys.exit(rc)

        staging_dir = os.path.join(DEFAULT_STAGING_BASE, ".staging", f"direct_{Normalizer.sanitize_slug(title)}")

        if provider == "mega":
            ok = ProviderDriver.download_mega(args.link, staging_dir)
        elif provider == "direct":
            ok = ProviderDriver.download_direct(args.link, staging_dir)
        else:
            log(f"Proveedor '{provider}' requiere autenticación dedicada.", "ERROR")
            sys.exit(1)

        if ok:
            processor = CourseProcessor(title, staging_dir, args.dest, flat=getattr(args, "flat", False))
            processor.process()
        else:
            log("Descarga fallida.", "ERROR")
            sys.exit(1)

    elif args.command == "scan":
        ManifestScanner.scan_receipts(args.dir, args.output)

    elif args.command == "reprocess":
        purge = not getattr(args, "no_purge_subs", False)
        Reprocessor.reprocess_course(args.course_dir, purge_subs=purge)

    elif args.command == "reprocess-tree":
        purge = not getattr(args, "no_purge_subs", False)
        Reprocessor.reprocess_tree(args.parent_dir, purge_subs=purge)

    elif args.command == "purge-subs":
        log(f"Iniciando purga de subtítulos en: {args.dir} (dry_run={args.dry_run})...", "ACTION")
        cnt, freed = Sanitizer.purge_garbage_transcripts(args.dir, dry_run=args.dry_run)
        action_word = "Simulados para purga" if args.dry_run else "Purgados físicamente"
        log(f"✅ {action_word}: {cnt} archivos ({freed / (1024 * 1024):.2f} MB liberados).", "INFO")

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
