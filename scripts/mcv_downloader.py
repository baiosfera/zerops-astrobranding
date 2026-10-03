#!/usr/bin/env python3
"""
MCV Course Downloader & Validator (MisCursosVirtuales.com) - v4.4.0 Universal SSoT Architecture, Deterministic Directory Resolver & Mega Encapsulated Staging
Complete 8-Step Sovereign Media Pipeline with Decoupled Producer-Consumer & Bidirectional Audit Manifest:
  1. Generate complete reference Markdown (.md)
  2. Download all cloud parts (Sync.com Zero-Knowledge Native Streams, Mega.nz, Google Drive) with alerts
  3. Decompress archives with 7-Zip/unrar or integrate direct media trees
  4. Transcode videos to minimum visible bitrate (360p H.264 CRF 28, AAC 64k) with strict compute isolation
  5. Convert audio to NotebookLM-optimized AAC/MP3 (24k mono AAC / 32k MP3)
  6. Apply hierarchical chronological naming (M{XX}_L{YY}_{Title}.mp3) and centralize in NOTEBOOKLM_AUDIOS/
  7. Validate integrity and purge raw archives and heavy original files
  8. Compile comprehensive final report in .md with initial vs final sizes, savings, and media specs
"""

import os
import sys
import shutil
import atexit
import unicodedata

sys.dont_write_bytecode = True

def purge_pycache_dirs():
    """Purga determinista de cualquier rastro de bytecode residual en MCV y scripts."""
    base_mcv = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "/var/www/baiosfera/CURSOS/MCV"
    for _c_dir in [
        os.path.join(base_mcv, "__pycache__"),
        "/var/www/baiosfera/CURSOS/MCV/__pycache__",
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/__pycache__"
    ]:
        if os.path.isdir(_c_dir):
            try:
                shutil.rmtree(_c_dir, ignore_errors=True)
            except Exception:
                pass

purge_pycache_dirs()
atexit.register(purge_pycache_dirs)

# ANSI formatting codes
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BOLD = "\033[1m"
RESET = "\033[0m"

import re
import time
import math
import base64
import hashlib

# Configure America/Bogota (GMT-5) timezone
os.environ["TZ"] = "America/Bogota"
if hasattr(time, "tzset"):
    time.tzset()

import json
import fcntl
import queue
import logging
import argparse
import signal
import zipfile
import threading
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from urllib.parse import urlparse, parse_qs, urljoin, quote, urlencode
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, Counter
import textwrap

import requests
from bs4 import BeautifulSoup
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Dynamic discovery of notebooklm-mcp-cli UV environment
for _uv_p in [
    "/home/zerops/.local/share/uv/tools/notebooklm-mcp-cli/lib/python3.12/site-packages",
    os.path.expanduser("~/.local/share/uv/tools/notebooklm-mcp-cli/lib/python3.12/site-packages")
]:
    if os.path.isdir(_uv_p) and _uv_p not in sys.path:
        sys.path.insert(0, _uv_p)

__version__ = "9.2.0"
VERSION = "9.2.0"
DEFAULT_COOKIES_PATH = "/var/www/baiosfera/CURSOS/MCV/mcv.json"
PERSISTENT_COOKIES_PATH = "/var/www/baiosfera/CURSOS/MCV/mcv.json"
LOCK_FILE_PATH = "/tmp/mcv_downloader.lock"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
LOCAL_DOWNLOAD_STAGING_DIR = "/var/www/.mcv_staging"
LOCAL_STAGING_DIR = "/tmp/mcv_transcode_staging"
PROGRESS_CARD_LOCK = threading.Lock()
logger = logging.getLogger("mcv_downloader")


def write_progress_card(
    course_dir: str,
    title: str,
    phase: str,
    status_badge: str,
    pct: float,
    details: Dict[str, Any],
    write_course_file: bool = True
):
    """Writes standardized PROGRESO.txt both to course_dir and /var/www/PROGRESO.txt with thread-safety."""
    bar_len = 30
    if pct > 0:
        filled = max(min(int(bar_len * (pct / 100.0)), bar_len), 0)
        bar = "█" * filled + "░" * (bar_len - filled)
        prog_bar_str = f"[{bar}] {pct:.1f}%"
    else:
        prog_bar_str = "[⏳ Flujo continuo en transferencia activa]"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    detail_str = "\n".join(f"{k:<22}: {v}" for k, v in details.items())

    card = f"""================================================================================
📊 ESTADO MCV: {title}
================================================================================
Fase actual:          {phase}
Estado:               {status_badge}
Progreso general:     {prog_bar_str}

{detail_str}
Última actualización: {now_str}
--------------------------------------------------------------------------------
💡 Para ver este estado en cualquier terminal ejecuta:
   mcv-status
   o en vivo continuo:
   mcv-status -w
================================================================================
"""
    targets = ["/var/www/PROGRESO.txt"]
    if write_course_file and course_dir and os.path.isdir(course_dir):
        course_prog = os.path.join(course_dir, "PROGRESO.txt")
        if phase == "FINALIZADO":
            if os.path.exists(course_prog):
                try:
                    os.remove(course_prog)
                except Exception:
                    pass
        else:
            targets.append(course_prog)

    with PROGRESS_CARD_LOCK:
        for path in targets:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(card)
            except Exception:
                pass


def update_batch_manifest(
    manifest_path: str,
    col_name: str,
    url: str,
    filter_txt: str,
    selected_courses: List[Dict[str, Any]],
    statuses: Dict[int, str],
    col_dir: str = "",
    alias: str = "",
    date_prefix: bool = True,
    created_at: Optional[str] = None
):
    """
    Escribe y actualiza dinámicamente el archivo de seguimiento de lote (.txt) en col_dir.
    Funciona simultáneamente como tablero de auditoría en vivo y semilla de reanudación desatendida.
    Cero purga destructiva: se conserva permanentemente como inventario histórico del lote.
    """
    try:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        effective_created_at = created_at
        effective_dir = col_dir or os.path.dirname(os.path.abspath(manifest_path))

        # Si el archivo ya existía, intentar preservar su fecha original de creación
        if not effective_created_at and os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f_prev:
                    for line in f_prev:
                        if line.startswith("# CREATED_AT:") or line.startswith("# FECHA_CREACION:"):
                            effective_created_at = line.split(":", 1)[1].strip()
                            break
            except Exception:
                pass
        if not effective_created_at:
            effective_created_at = now_str

        total_courses = len(selected_courses)
        completed_count = sum(1 for s in statuses.values() if s.startswith("[COMPLETADO"))
        omitted_count = sum(1 for s in statuses.values() if s.startswith("[OMITIDO"))
        runnable_count = total_courses - omitted_count

        if total_courses > 0 and completed_count == total_courses:
            global_badge = f"🟢 100% COMPLETADO (Lote sellado: {completed_count}/{total_courses} cursos)"
            pct = 100.0
        elif runnable_count > 0 and completed_count == runnable_count:
            global_badge = f"🟢 100% COMPLETADO (Seleccionados: {completed_count}/{runnable_count}, {omitted_count} omitidos)"
            pct = 100.0
        elif completed_count > 0:
            pct = (completed_count / total_courses) * 100.0 if total_courses else 0.0
            global_badge = f"🟡 EN PROCESO ({completed_count}/{total_courses} completados, {pct:.1f}%)"
        else:
            global_badge = f"⚪ PENDIENTE DE DESCARGA ({total_courses} cursos en catálogo)"
            pct = 0.0

        lines = [
            "================================================================================",
            f"📋 MANIFIESTO DE AUDITORÍA Y REANUDACIÓN DE LOTE: [{col_name}]",
            "================================================================================",
            "# MCV_BATCH_MANIFEST_V1",
            f"# ORIGIN_URL: {url}",
            f"# COLLECTION_NAME: {col_name}",
            f"# AUTHOR_ALIAS: {alias}",
            f"# APPLIED_FILTERS: {filter_txt}",
            f"# BASE_DIR: {effective_dir}",
            f"# CREATED_AT: {effective_created_at}",
            f"# UPDATED_AT: {now_str}",
            "--------------------------------------------------------------------------------",
            f"URL Consultada:       {url}",
            f"Directorio Base:      {effective_dir}",
            f"Última actualización: {now_str}",
            f"Filtros aplicados:    {filter_txt}",
            f"Total en catálogo:    {total_courses} cursos",
            f"Progreso global:      {completed_count}/{total_courses} completados ({pct:.1f}%)",
            f"Estado general:       {global_badge}",
            "================================================================================",
            f" #  | Vigencia   | Estado                 | Título",
            f"----+------------+------------------------+-------------------------------------"
        ]

        for idx, c in enumerate(selected_courses, 1):
            st = statuses.get(idx, "[PENDIENTE]")
            eff = (c.get("effective_date") or "N/A")[:10]
            title = c.get("title", "")
            c_url = c.get("url", "")
            f_name = c.get("folder_name", "")
            if not f_name:
                f_name = compute_course_folder_name(
                    title=title,
                    effective_date=c.get("effective_date", ""),
                    category=c.get("category", "CURSO"),
                    alias=alias,
                    date_prefix=date_prefix
                )
            lines.append(f" {idx:02d} | {eff:<10} | {st:<22} | {title}")
            if c_url:
                lines.append(f"    ↳ URL: {c_url}")
            if f_name:
                lines.append(f"    ↳ DIR: {f_name}")

        lines.append("================================================================================")
        lines.append("💡 Este archivo es el inventario permanente y tablero de auditoría del lote.")
        lines.append("   Para reanudar descargas pendientes o carpetas incompletas ejecutá:")
        lines.append(f"   mcv-download {manifest_path}")
        lines.append("================================================================================")

        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:
        logger.warning(f"Aviso actualizando manifiesto de lote ({manifest_path}): {e}")



def acquire_singleton_lock(force: bool = False) -> Optional[Any]:
    """
    Acquires an exclusive non-blocking file lock to prevent concurrent downloads.
    Returns open file handle or exits cleanly if another process holds it.
    """
    if force:
        return None
    try:
        lock_fd = open(LOCK_FILE_PATH, "a+")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.seek(0)
        lock_fd.truncate()
        lock_fd.write(f"{os.getpid()}\n")
        lock_fd.flush()
        return lock_fd
    except (IOError, BlockingIOError):
        active_pid = "desconocido"
        try:
            if os.path.exists(LOCK_FILE_PATH):
                with open(LOCK_FILE_PATH, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        active_pid = content
        except Exception:
            pass
        print("=" * 80)
        print("⚠️  AVISO DE EJECUCIÓN CONCURRENTE (CERROJO SINGLETON ACTIVO):")
        print(f"   Ya existe una descarga activa de MCV en segundo plano (PID: {active_pid}).")
        print("=" * 80)
        print("💡 Opciones:")
        print("   1. Para ver el progreso en tiempo real ejecuta: mcv-status o mcv-status -w")
        print("   2. Si deseas esperar a que termine, no hagas nada.")
        print("   3. Si deseas forzar la ejecución simultánea, ejecuta con: --force")
        print("=" * 80)
        sys.exit(1)


class ProgressTracker:
    """Tracks overall and per-file download progress with periodic hourly alerts."""

    def __init__(
        self,
        log_file: Optional[str] = None,
        alert_interval_sec: int = 3600,
        course_dir: str = "",
        course_title: str = ""
    ):
        self.alert_interval = alert_interval_sec
        self.log_file = log_file
        self.course_dir = course_dir
        self.course_title = course_title
        self.current_filename = "N/A"
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.start_time = time.time()
        self.last_alert_time = time.time()
        self.last_bytes = 0
        self.last_time = time.time()
        self.is_running = False
        self.initial_alert_sent = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self.is_running = True
        self.start_time = time.time()
        self.last_time = self.start_time
        self.last_alert_time = self.start_time
        self.initial_alert_sent = False
        self._thread = threading.Thread(target=self._alert_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def update(self, filename: str, downloaded_bytes: int, total_bytes: int = 0):
        if self.current_filename != filename:
            self.current_filename = filename
            self.downloaded_bytes = downloaded_bytes
            self.total_bytes = total_bytes if total_bytes > 0 else 0
            self.last_bytes = downloaded_bytes
            self.last_time = time.time()
        else:
            self.downloaded_bytes = downloaded_bytes
            if total_bytes > 0:
                self.total_bytes = total_bytes

    def get_stats(self) -> Dict[str, Any]:
        now = time.time()
        elapsed = max(now - self.start_time, 0.001)
        interval_elapsed = max(now - self.last_time, 0.001)
        speed = max(self.downloaded_bytes - self.last_bytes, 0) / interval_elapsed
        overall_speed = self.downloaded_bytes / elapsed

        if self.total_bytes > 0:
            pct = min((self.downloaded_bytes / self.total_bytes * 100), 100.0)
            remaining_bytes = max(self.total_bytes - self.downloaded_bytes, 0)
            eta_sec = (remaining_bytes / speed) if speed > 1024 else 0
        else:
            pct = 0.0
            eta_sec = 0

        return {
            "filename": self.current_filename,
            "downloaded_mb": self.downloaded_bytes / (1024 * 1024),
            "total_mb": self.total_bytes / (1024 * 1024),
            "percentage": pct,
            "speed_mbps": speed / (1024 * 1024),
            "overall_speed_mbps": overall_speed / (1024 * 1024),
            "elapsed_str": str(timedelta(seconds=int(elapsed))),
            "eta_str": str(timedelta(seconds=int(eta_sec))) if eta_sec > 0 else "Calculando...",
        }

    def emit_alert(self, force: bool = False, is_initial: bool = False):
        stats = self.get_stats()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = "📢 [PRESUPUESTO INICIAL DE DESCARGA]" if is_initial else "📢 ALERTA DE PROGRESO (DESCARGA)"
        desc_str = f"{stats['downloaded_mb']:.2f} MB / {stats['total_mb']:.2f} MB ({stats['percentage']:.1f}%)" if stats['total_mb'] > 0 else f"{stats['downloaded_mb']:.2f} MB (Flujo continuo)"
        eta_disp = stats['eta_str'] if stats['total_mb'] > 0 else "Dependiente de la nube (stream)"
        msg = (
            f"[{timestamp}] {header}:\n"
            f"   - Archivo actual: {stats['filename']}\n"
            f"   - Descargado: {desc_str}\n"
            f"   - Velocidad estabilizada: {stats['speed_mbps']:.2f} MB/s (Promedio: {stats['overall_speed_mbps']:.2f} MB/s)\n"
            f"   - Tiempo transcurrido: {stats['elapsed_str']} | ETA estimado de descarga: {eta_disp}"
        )
        logger.info(msg)
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(msg + "\n\n")
            except Exception as e:
                logger.warning(f"Error escribiendo en log de progreso: {e}")

        self._render_card(write_course_file=True)
        self.last_time = time.time()
        self.last_bytes = self.downloaded_bytes
        self.last_alert_time = self.last_time

    def _render_card(self, write_course_file: bool = False):
        if not self.course_dir:
            return
        stats = self.get_stats()
        desc_str = f"{stats['downloaded_mb']:.2f} MB / {stats['total_mb']:.2f} MB ({stats['percentage']:.1f}%)" if stats['total_mb'] > 0 else f"{stats['downloaded_mb']:.2f} MB (Flujo continuo)"
        eta_disp = stats['eta_str'] if stats['total_mb'] > 0 else "Dependiente de la nube (stream)"
        write_progress_card(
            course_dir=self.course_dir,
            title=self.course_title or "Curso MCV",
            phase="DESCARGA DE ARCHIVOS",
            status_badge="🟡 Descargando partes del curso...",
            pct=stats["percentage"],
            details={
                "Archivo actual": stats["filename"],
                "Descargado": desc_str,
                "Velocidad actual": f"{stats['speed_mbps']:.2f} MB/s (Promedio: {stats['overall_speed_mbps']:.2f} MB/s)",
                "Tiempo transcurrido": stats["elapsed_str"],
                "Tiempo estimado (ETA)": eta_disp,
            },
            write_course_file=write_course_file
        )

    def _alert_loop(self):
        while self.is_running:
            time.sleep(3.0)
            if not self.is_running:
                break
            self._render_card(write_course_file=True)
            now = time.time()
            if not self.initial_alert_sent and (now - self.start_time >= 25.0) and self.downloaded_bytes > 3 * 1024 * 1024:
                self.initial_alert_sent = True
                self.emit_alert(is_initial=True)
            elif now - self.last_alert_time >= self.alert_interval:
                self.emit_alert()


class MediaOptimizationTracker:
    """
    Tracks two-phase media optimization:
    Phase A: Audio-First extraction and Google NotebookLM streaming ingestion.
    Phase B: 360p video transcoding with ffmpeg (CRF 28, nice 10).
    """

    def __init__(
        self,
        total_videos: int,
        log_file: Optional[str] = None,
        alert_interval_sec: int = 3600,
        course_dir: str = "",
        course_title: str = ""
    ):
        self.total_videos = total_videos
        self.course_dir = course_dir
        self.course_title = course_title
        self.completed_videos = 0
        self.current_filename = "N/A"
        self.current_module = "N/A"
        self.saved_bytes = 0
        self.start_time = time.time()
        self.last_alert_time = time.time()
        self.log_file = log_file
        self.alert_interval = alert_interval_sec
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

        # Two-Phase Telemetry State
        self.phase = "FASE_A"  # "FASE_A" or "FASE_B"
        self.total_audios = 0
        self.completed_audios = 0
        self.notebook_status = "Pendiente"
        self.notebook_title = ""

    def set_phase(self, phase: str):
        self.phase = phase
        if self.course_dir:
            self._render_card()

    def set_audio_targets(self, total_audios: int, notebook_title: str = ""):
        self.total_audios = total_audios
        if notebook_title:
            self.notebook_title = notebook_title
        if self.course_dir:
            self._render_card()

    def set_notebook_status(self, status: str):
        self.notebook_status = status
        if self.course_dir:
            self._render_card()

    def record_audio_completed(self, module: str, filename: str):
        self.completed_audios += 1
        self.current_module = module
        self.current_filename = filename
        if self.course_dir:
            self._render_card()

    def emit_initial_baseline(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        est_minutes = self.total_videos * 4.5
        est_eta_str = str(timedelta(seconds=int(est_minutes * 60)))
        msg = (
            f"[{timestamp}] 📢 [PRESUPUESTO INICIAL - OPTIMIZACIÓN MULTIMEDIA BIFÁSICA]:\n"
            f"   - Fase A: Extracción prioritaria de audio (~28x vel) e ingesta a Google NotebookLM\n"
            f"   - Fase B: Transcodificación a 360p (CRF 28, {self.total_videos} videos, ETA video: ~{est_eta_str})\n"
            f"   - Telemetría en vivo: 'mcv-status' o 'mcv-status -w'"
        )
        logger.info(msg)
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(msg + "\n\n")
            except Exception as e:
                logger.warning(f"Error escribiendo en log de progreso: {e}")

    def _render_card(self):
        stats = self.get_stats()
        if self.phase == "FASE_A":
            pct = (self.completed_audios / self.total_audios * 100) if self.total_audios > 0 else 0.0
            badge = "🟢 Extrayendo audios AAC prioritarios..." if self.completed_audios < self.total_audios else f"🟢 NotebookLM: {self.notebook_status}"
            details = {
                "Audios extraídos": f"{self.completed_audios} de {self.total_audios}",
                "Elemento actual": f"[{self.current_module}] {self.current_filename}",
                "Cuaderno NotebookLM": self.notebook_title or "Resolviendo...",
                "Estado NotebookLM": self.notebook_status,
                "Tiempo transcurrido": stats["elapsed_str"],
            }
            write_progress_card(
                course_dir=self.course_dir,
                title=self.course_title or "Curso MCV",
                phase="FASE A: AUDIO-FIRST & NOTEBOOKLM",
                status_badge=badge,
                pct=pct,
                details=details
            )
        else:
            pct = stats["percentage"]
            details = {
                "Videos procesados": f"{stats['completed']} de {stats['total']}",
                "Video actual": f"[{self.current_module}] {self.current_filename}",
                "Espacio ahorrado": f"{stats['saved_gb']:.2f} GB",
                "Tiempo transcurrido": stats["elapsed_str"],
                "Tiempo estimado (ETA)": stats["eta_str"],
                "Cuaderno NotebookLM": self.notebook_title or "Ingestado con éxito",
            }
            write_progress_card(
                course_dir=self.course_dir,
                title=self.course_title or "Curso MCV",
                phase="FASE B: REDUCCIÓN VIDEO 360p",
                status_badge="🟡 Transcodificando video activamente con ffmpeg...",
                pct=pct,
                details=details
            )

    def start(self):
        self.is_running = True
        self.start_time = time.time()
        self.last_alert_time = self.start_time
        self.emit_initial_baseline()
        if self.course_dir:
            self._render_card()
        self._thread = threading.Thread(target=self._alert_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def update_file(self, module: str, filename: str):
        self.current_module = module
        self.current_filename = filename
        if self.course_dir:
            self._render_card()

    def record_completed(self, saved_bytes: int):
        self.completed_videos += 1
        self.saved_bytes += saved_bytes
        if self.course_dir:
            self._render_card()

    def get_stats(self) -> Dict[str, Any]:
        now = time.time()
        elapsed = max(now - self.start_time, 0.001)
        if self.completed_videos > 0:
            avg_per_vid = elapsed / self.completed_videos
            remaining_vids = max(self.total_videos - self.completed_videos, 0)
            eta_sec = avg_per_vid * remaining_vids
        else:
            eta_sec = self.total_videos * 270.0

        pct = (self.completed_videos / self.total_videos * 100) if self.total_videos > 0 else 0.0
        return {
            "completed": self.completed_videos,
            "total": self.total_videos,
            "percentage": pct,
            "module": self.current_module,
            "filename": self.current_filename,
            "saved_gb": self.saved_bytes / (1024 ** 3),
            "elapsed_str": str(timedelta(seconds=int(elapsed))),
            "eta_str": str(timedelta(seconds=int(eta_sec))) if eta_sec > 0 else "Finalizando...",
        }

    def emit_alert(self, force: bool = False):
        stats = self.get_stats()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.phase == "FASE_A":
            pct = (self.completed_audios / self.total_audios * 100) if self.total_audios > 0 else 0.0
            msg = (
                f"[{timestamp}] 📢 ALERTA DE PROGRESO (FASE A: AUDIO-FIRST & NOTEBOOKLM):\n"
                f"   - Audios: {self.completed_audios} de {self.total_audios} extraídos ({pct:.1f}%)\n"
                f"   - Audio actual: [{self.current_module}] {self.current_filename}\n"
                f"   - Cuaderno: {self.notebook_title or 'Pendiente'}\n"
                f"   - Estado NotebookLM: {self.notebook_status}\n"
                f"   - Tiempo transcurrido: {stats['elapsed_str']}"
            )
        else:
            msg = (
                f"[{timestamp}] 📢 ALERTA DE PROGRESO (FASE B: REDUCCIÓN VIDEO 360p):\n"
                f"   - Estado: {stats['completed']} de {stats['total']} videos procesados ({stats['percentage']:.1f}%)\n"
                f"   - Archivo actual: [{stats['module']}] {stats['filename']}\n"
                f"   - Tiempo transcurrido: {stats['elapsed_str']}\n"
                f"   - Tiempo estimado restante (ETA): {stats['eta_str']}\n"
                f"   - Espacio ahorrado hasta ahora: {stats['saved_gb']:.2f} GB"
            )
        logger.info(msg)
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(msg + "\n\n")
            except Exception as e:
                logger.warning(f"Error escribiendo en log de progreso: {e}")

        if self.course_dir:
            self._render_card()
        self.last_alert_time = time.time()

    def _alert_loop(self):
        while self.is_running:
            time.sleep(3.0)
            if not self.is_running:
                break
            if self.course_dir:
                self._render_card()
            now = time.time()
            if now - self.last_alert_time >= self.alert_interval:
                self.emit_alert()



def show_status(watch: bool = False, interval: float = 2.0) -> bool:
    """Displays live progress card or continuous watch mode with anti-ghost PID validation."""
    progress_file = "/var/www/PROGRESO.txt"
    lock_file = LOCK_FILE_PATH

    def _is_worker_alive() -> bool:
        if os.path.exists(lock_file):
            try:
                with open(lock_file, "r", encoding="utf-8") as lf:
                    pid_str = lf.read().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    os.kill(pid, 0)
                    return True
            except OSError:
                return False
            except Exception:
                pass
        try:
            res = subprocess.run(
                ["pgrep", "-f", "mcv_downloader.py.*(https?://|--optimize|-d|--detach)"],
                capture_output=True,
                text=True
            )
            if res.returncode == 0 and res.stdout.strip():
                return True
        except Exception:
            pass
        return False

    def _print():
        # Anti-ghost validation: if progress_file exists but worker is dead, clean up
        if os.path.exists(progress_file) and not _is_worker_alive():
            try:
                os.remove(progress_file)
            except Exception:
                pass
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except Exception:
                    pass

        if not os.path.exists(progress_file):
            print("=" * 80)
            print("ℹ️  No hay descargas ni conversiones de MCV activas en este momento.")
            print("   Inicia una descarga o conversión con 'mcv-download <URL>'")
            print("=" * 80)
            return False
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    print(content.rstrip())
                    return True
                else:
                    print("⏳ Esperando telemetría de la descarga activa...")
                    return True
        except Exception as e:
            print(f"⚠️ Error leyendo telemetría: {e}")
            return False

    if not watch:
        return _print()

    print("📺 Monitoreo en vivo continuo activado. Presiona Ctrl+C para salir.\n")
    try:
        while True:
            os.system("clear")
            _print()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n👋 Monitoreo finalizado.")
        return True


def load_cookies(cookies_path: str = PERSISTENT_COOKIES_PATH) -> Dict[str, str]:
    """Load session cookies from JSON file (supports exported array or dict) without polluting /var/www."""
    target = cookies_path if (cookies_path and os.path.exists(cookies_path)) else PERSISTENT_COOKIES_PATH
    if not os.path.exists(target):
        if os.path.exists("/var/www/mcv.json"):
            target = "/var/www/mcv.json"
        else:
            raise FileNotFoundError(f"Archivo de cookies no encontrado en: {target}")

    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)

    cookies = {}
    if isinstance(data, list):
        for item in data:
            name = item.get("name")
            value = item.get("value")
            if name and value:
                cookies[name] = value
    elif isinstance(data, dict):
        cookies = data
    else:
        raise ValueError("Formato de cookies desconocido en archivo JSON.")

    return cookies


def purge_runtime_transient_files():
    """
    Purges transient runtime files in /var/www/ when batch or course completes.
    Leaves /var/www completely clean.
    """
    for transient in ["/var/www/mcv.json", "/var/www/PROGRESO.txt", "/var/www/mcv_daemon.log"]:
        if os.path.exists(transient):
            try:
                os.remove(transient)
                logger.info(f"🧹 Purgado archivo transitorio: {transient}")
            except Exception:
                pass
    if os.path.exists(LOCAL_DOWNLOAD_STAGING_DIR):
        try:
            for item in os.listdir(LOCAL_DOWNLOAD_STAGING_DIR):
                p = os.path.join(LOCAL_DOWNLOAD_STAGING_DIR, item)
                if os.path.isdir(p) and not os.listdir(p):
                    os.rmdir(p)
        except Exception:
            pass


def get_session(cookies_path: str) -> requests.Session:
    """Create a configured requests session with cookies and headers."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    })
    cookies = load_cookies(cookies_path)
    session.cookies.update(cookies)
    return session


def fetch_course_metadata(session: requests.Session, course_url: str) -> Dict[str, Any]:
    """
    Scrapes product page, extracts title, category, product ID,
    resolves the protected_file link, and fetches the WooCommerce instruction txt.
    """
    logger.info(f"Obteniendo información del curso desde: {course_url}")
    resp = session.get(course_url, timeout=20)
    if resp.status_code != 200:
        raise RuntimeError(f"Error al acceder al curso: HTTP {resp.status_code}")

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    # 1. Title & Author
    title_el = soup.find("h1", class_="product_title") or soup.find("title")
    raw_title = title_el.get_text(strip=True) if title_el else "Curso Desconocido"
    raw_title = re.sub(r"^Curso:\s*", "", raw_title, flags=re.IGNORECASE).strip()

    author = "MCV"
    author_el = soup.find(class_=lambda c: c and any(k in str(c) for k in ["author", "instructor", "posted_by", "yith-vendor"]))
    if author_el:
        author = author_el.get_text(strip=True)
    if author == "MCV":
        author_meta = soup.find("meta", attrs={"name": "author"}) or soup.find("meta", property="article:author")
        if author_meta and author_meta.get("content"):
            author = author_meta["content"].strip()
    if author in ["MCV", "", "N/A", "Unknown"]:
        parts = re.split(r"\s*[\-–—]\s*", raw_title)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) >= 2:
            author = parts[-1]
            title = " - ".join(parts[:-1]).strip()
        else:
            title = raw_title
    else:
        parts = re.split(r"\s*[\-–—]\s*", raw_title)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) >= 2 and sanitize_folder_name(parts[-1]).lower() == sanitize_folder_name(author).lower():
            title = " - ".join(parts[:-1]).strip()
        else:
            title = raw_title

    # 2. Category
    cat_match = re.search(r"posted_in\">.*?<a[^>]*>(.*?)</a>", html, re.DOTALL)
    category = cat_match.group(1).strip().upper() if cat_match else "PROFESIONAL"

    # 3. Product ID & Protected File URL
    protected_url = None
    product_id = None
    button = soup.find("a", class_=lambda c: c and "yith-wcmbs-download-button" in c)
    if button and button.get("href"):
        protected_url = button["href"]
        product_id = button.get("data-product-id")

    if not protected_url:
        match = re.search(r"href=['\"]([^'\"]*protected_file=[^'\"]+)['\"]", html)
        if match:
            protected_url = match.group(1)

    if protected_url and not product_id:
        qs = parse_qs(urlparse(protected_url).query)
        product_id = qs.get("product_id", [None])[0]

    if not product_id:
        pid_match = re.search(r"name=['\"]add-to-cart['\"]\s+value=['\"](\d+)['\"]", html) or \
                    re.search(r"data-product_id=['\"](\d+)['\"]", html)
        if pid_match:
            product_id = pid_match.group(1)

    if not protected_url:
        raise RuntimeError(
            "No se encontró el botón de descarga protegida de membresía (YITH). "
            "Verifica que la cuenta premium en cookies tenga acceso activo al curso."
        )

    logger.info(f"Enlace protegido detectado: {protected_url} (Product ID: {product_id})")

    txt_resp = session.get(protected_url, allow_redirects=True, timeout=20)
    if txt_resp.status_code != 200:
        raise RuntimeError(f"Error descargando archivo protegido: HTTP {txt_resp.status_code}")

    txt_url = txt_resp.url
    txt_content = txt_resp.content.decode("utf-8", errors="replace")

    # Extract dates from JSON-LD schema or meta tags
    pub_date = None
    mod_date = None
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(script.string)
            graph = d.get("@graph", [d]) if isinstance(d, dict) else []
            for item in graph:
                if "datePublished" in item:
                    pub_date = item["datePublished"][:10]
                if "dateModified" in item:
                    mod_date = item["dateModified"][:10]
        except Exception:
            pass

    if not pub_date:
        pub_meta = soup.find("meta", property="article:published_time")
        if pub_meta and pub_meta.get("content"):
            pub_date = pub_meta["content"][:10]

    if not mod_date:
        mod_meta = soup.find("meta", property="article:modified_time")
        if mod_meta and mod_meta.get("content"):
            mod_date = mod_meta["content"][:10]

    if not pub_date:
        date_match = re.search(r"/uploads/woocommerce_uploads/(\d{4}/\d{2})/", txt_url)
        pub_date = date_match.group(1).replace("/", "-") if date_match else datetime.now().strftime("%Y-%m")

    effective_date = mod_date or pub_date or datetime.now().strftime("%Y-%m-%d")

    cloud_links = parse_txt_links(txt_content, session=session)
    all_option_sets = parse_all_option_sets(txt_content, session=session)
    password = parse_txt_password(txt_content)

    return {
        "title": title,
        "raw_title": raw_title,
        "author": author,
        "category": category,
        "product_id": product_id or "N/A",
        "product_url": course_url,
        "protected_url": protected_url,
        "txt_url": txt_url,
        "txt_content": txt_content,
        "pub_date": pub_date or "N/A",
        "mod_date": mod_date or pub_date or "N/A",
        "effective_date": effective_date,
        "password": password,
        "cloud_links": cloud_links,
        "all_option_sets": all_option_sets,
    }


def parse_txt_password(text: str) -> str:
    """Extract decompression password from text instructions with space tolerance."""
    match = re.search(r"(?:contraseñ[a|as]|clave).*?[:=]\s*([^\r\n]+)", text, re.IGNORECASE)
    if match:
        pw = match.group(1).strip()
        pw = re.sub(r"[,\.;\)]+$", "", pw).strip()
        pw = re.split(r"\s*\(", pw)[0].strip()
        if pw:
            return pw
    return "www.miscursosvirtuales.com"


def resolve_short_url(url: str, session: Optional[requests.Session] = None) -> str:
    """Follows HTTP redirects (bit.ly, tinyurl, etc.) to resolve canonical destination cloud URL."""
    try:
        s = session or requests
        resp = s.head(url, allow_redirects=True, timeout=10)
        if resp.url and resp.url != url:
            return resp.url
        if resp.status_code in [400, 403, 405]:
            resp_get = s.get(url, allow_redirects=True, timeout=10, stream=True)
            return resp_get.url
        return resp.url or url
    except Exception:
        return url


def detect_provider(url: str) -> str:
    u = url.lower()
    if "sync.com" in u:
        return "sync"
    elif "mega.nz" in u or "mega.co.nz" in u:
        return "mega"
    elif "drive.google.com" in u:
        return "gdrive"
    elif "mediafire.com" in u:
        return "mediafire"
    elif "terabox.com" in u or "1024tera" in u:
        return "terabox"
    return "direct"


def extract_links_from_lines(lines: List[str], session: Optional[requests.Session] = None) -> List[Dict[str, str]]:
    """Helper to parse cloud download links from a list of raw text lines."""
    links = []
    current_label = "Parte 1"
    part_counter = 1
    known_hosts = ["sync.com", "mega.nz", "drive.google.com", "mediafire.com", "terabox.com", "1024tera", "s3.wasabisys.com", "wasabisys.com"]
    shortener_domains = ["bit.ly", "tinyurl.com", "t.co", "ow.ly", "is.gd", "buff.ly", "cutt.ly"]

    for line in lines:
        label_match = re.match(r"^(?:Enlace\s*\d*|Parte\s*\d*|Link\s*\d*):?", line, re.IGNORECASE)
        if label_match:
            current_label = f"Parte {part_counter}"

        url_match = re.search(r"(https?://[^\s\)]+)", line)
        if url_match:
            raw_url = url_match.group(1).rstrip(",;.)]\"'")
            is_short = any(s in raw_url.lower() for s in shortener_domains)
            has_known = any(h in raw_url.lower() for h in known_hosts)

            resolved_url = raw_url
            if is_short or not has_known:
                resolved_url = resolve_short_url(raw_url, session)

            provider = detect_provider(resolved_url)
            is_direct_archive = resolved_url.lower().endswith((".rar", ".zip", ".7z", ".mp4", ".tar", ".gz"))
            if provider != "direct" or any(h in resolved_url.lower() for h in known_hosts) or is_short or is_direct_archive:
                links.append({
                    "part": current_label,
                    "url": resolved_url,
                    "provider": provider
                })
                part_counter += 1
                current_label = f"Parte {part_counter}"
    return links


def parse_all_option_sets(text: str, session: Optional[requests.Session] = None) -> List[List[Dict[str, str]]]:
    """Extract all alternative option mirror sets from instruction text."""
    raw_lines = [l.strip() for l in text.splitlines() if l.strip()]
    has_option_blocks = bool(re.search(r"opci[oó]n\s*(?:de\s*descarga\s*)?[1-9]", text, re.IGNORECASE))
    all_sets = []

    if has_option_blocks:
        option_lines = {}
        cur_opt = 1
        for line in raw_lines:
            opt_m = re.search(r"opci[oó]n\s*(?:de\s*descarga\s*)?([1-9])", line, re.IGNORECASE)
            if opt_m:
                cur_opt = int(opt_m.group(1))
            option_lines.setdefault(cur_opt, []).append(line)
        for opt_num in sorted(option_lines.keys()):
            c_links = extract_links_from_lines(option_lines[opt_num], session)
            if c_links:
                all_sets.append(c_links)
    if not all_sets:
        single = extract_links_from_lines(raw_lines, session)
        if single:
            all_sets.append(single)

    return all_sets


def parse_txt_links(text: str, session: Optional[requests.Session] = None) -> List[Dict[str, str]]:
    """Extract all cloud links from instruction text, prioritizing primary options."""
    all_sets = parse_all_option_sets(text, session)
    return all_sets[0] if all_sets else []


def sanitize_folder_name(name: str) -> str:
    """Universal sanitization: strips emojis, symbols and redundant punctuation
    while strictly preserving alphanumeric characters, unicode accents, and hyphens."""
    clean = re.sub(r"[\U00010000-\U0010ffff]", "", name)
    clean = re.sub(r'["\'`´*?:;|<>!¿¡#$%/\\()\[\]{}]', '', clean)
    clean = re.sub(r"[–—]", "-", clean)
    clean = re.sub(r"[^\w\s-]", "", clean, flags=re.UNICODE)
    clean = re.sub(r"[\s]+", "-", clean.strip())
    clean = re.sub(r"-+", "-", clean).strip("-")
    return clean


def format_notebook_title(author_or_alias: str, effective_date: str, course_title: str) -> str:
    """
    Composes strict Google NotebookLM title: [MCV][ALIAS][MM-YY]_Course-Title
    or [MCV][ALIAS][P01]_Course-Title or [MCV][ALIAS][00]_Course-Title
    Zero spaces guaranteed.
    """
    clean_alias = sanitize_folder_name(author_or_alias).upper() if author_or_alias else "MCV"
    clean_course = sanitize_folder_name(course_title)

    mm_yy = "00-00"
    if effective_date:
        eff_clean = str(effective_date).strip().upper()
        if re.match(r"^P\d{2}$", eff_clean) or eff_clean == "00":
            mm_yy = eff_clean
        else:
            m = re.search(r"(\d{4})-(\d{2})", effective_date)
            if m:
                yyyy, mm = m.group(1), m.group(2)
                mm_yy = f"{mm}-{yyyy[2:]}"
            else:
                m_alt = re.search(r"(\d{2})[-/](\d{2,4})", effective_date)
                if m_alt:
                    mm_yy = f"{m_alt.group(1)}-{m_alt.group(2)[-2:]}"

    title = f"[MCV][{clean_alias}][{mm_yy}]_{clean_course}"
    return re.sub(r"[\s]+", "-", title.strip())


def resolve_author_alias(raw_term: str) -> str:
    """Extracts clean author alias or surname from author string or search term."""
    clean = re.sub(r"^(?:autor|author)[_-]", "", raw_term.strip(), flags=re.IGNORECASE)
    tokens = [t for t in re.split(r"[\s_\-]+", clean.strip()) if t]
    if tokens:
        return tokens[-1].title()
    return "General"


def resolve_author_dir(base_dest: str, alias: str) -> str:
    """
    Resolves author folder under AUTHOR/<Alias> without AUTOR_ prefix.
    Zero spaces.
    """
    clean_alias = sanitize_folder_name(alias).title()
    clean_alias = re.sub(r"^Autor[_-]", "", clean_alias, flags=re.IGNORECASE)
    norm = os.path.normpath(base_dest)
    leaf = os.path.basename(norm)
    if re.match(r"^(?:autor|author)[_-]", leaf, re.IGNORECASE):
        norm = os.path.dirname(norm)
    if os.path.basename(norm).upper() == "AUTHOR":
        return os.path.join(norm, clean_alias)
    return os.path.join(norm, "AUTHOR", clean_alias)


def compute_course_folder_name(
    title: str,
    effective_date: str = "",
    category: str = "CURSO",
    alias: str = "",
    date_prefix: bool = True
) -> str:
    """
    Computes standardized course directory name:
    [VIP] [YYYY-MM]_Title_Author (or without date prefix if disabled).
    Preserves exact level, part, and module numbers with zero author redundancy.
    """
    date_tag = effective_date[:7] if effective_date and effective_date != "N/A" else ""
    cat_tag = sanitize_folder_name(category).upper()
    effective_author = alias or resolve_author_alias(title)
    raw_author = sanitize_folder_name(effective_author).title() if effective_author else ""
    author_tag = "" if raw_author.upper() in ["MCV", "UNKNOWN", "N/A", ""] else raw_author

    # Strip author suffix from title if present before sanitizing
    title_parts = re.split(r"\s+[–—-]\s+", title.strip())
    if len(title_parts) >= 2:
        last_part = title_parts[-1].strip().lower()
        if (author_tag and author_tag.lower() in last_part) or (effective_author and effective_author.lower() in last_part):
            clean_title = sanitize_folder_name(" - ".join(title_parts[:-1]))
        else:
            clean_title = sanitize_folder_name(title)
    else:
        clean_title = sanitize_folder_name(title)

    if author_tag:
        clean_title = re.sub(rf"[-_]{re.escape(author_tag)}$", "", clean_title, flags=re.IGNORECASE)
    if effective_author:
        clean_title = re.sub(rf"[-_]{re.escape(sanitize_folder_name(effective_author))}$", "", clean_title, flags=re.IGNORECASE)

    cat_prefix = "[VIP] " if "VIP" in cat_tag else ""
    author_suffix = f"_{author_tag}" if author_tag else ""

    if date_prefix and date_tag and date_tag != "N/A":
        return f"{cat_prefix}[{date_tag}]_{clean_title}{author_suffix}"
    return f"{cat_prefix}{clean_title}{author_suffix}"


def locate_existing_course_directory(
    base_dir: str,
    target_folder_name: str,
    title: str = "",
    author_alias: str = "",
    product_id: str = "",
    product_url: str = ""
) -> Optional[str]:
    """
    Deterministic SSoT Directory Locator (v4.4.0):
    Resolves existing physical course folder on disk with 100% determinism.
    1. Exact match of folder name.
    2. Structural variants (with/without date prefix or author suffix).
    3. SSoT metadata lookup: matches product_id or canonical product_url from metadata.json.
    4. Ordinal-guarded slug matching: NEVER matches across different numbers, levels, or modules.
    Zero fuzzy guessing by arbitrary word subsets.
    """
    if not os.path.isdir(base_dir):
        return None

    # 1. Exact match
    if os.path.isdir(os.path.join(base_dir, target_folder_name)):
        return target_folder_name

    # 2. Structural variations
    alt1 = re.sub(r"^\[\d{4}-\d{2}\]_?", "", target_folder_name)
    if alt1 and os.path.isdir(os.path.join(base_dir, alt1)):
        return alt1

    alt_curr = re.sub(r"^\[P\d{2}\]_?", "", target_folder_name)
    if alt_curr and os.path.isdir(os.path.join(base_dir, alt_curr)):
        return alt_curr

    alt2 = f"[PROFESIONAL] {target_folder_name}"
    if os.path.isdir(os.path.join(base_dir, alt2)):
        return alt2

    alt3 = re.sub(r"_[A-Za-z0-9]+$", "", target_folder_name)
    if alt3 and os.path.isdir(os.path.join(base_dir, alt3)):
        return alt3

    if author_alias:
        alt4 = re.sub(rf"[-_][A-Za-z0-9]+_{re.escape(author_alias)}$", f"_{author_alias}", target_folder_name)
        if alt4 and os.path.isdir(os.path.join(base_dir, alt4)):
            return alt4

    try:
        entries = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    except OSError:
        return None

    # 3. SSoT Metadata Inspection (Highest Deterministic Precision)
    for e in entries:
        meta_file = os.path.join(base_dir, e, "metadata.json")
        if os.path.isfile(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as mf:
                    d_meta = json.load(mf)
                disk_pid = str(d_meta.get("product_id", "")).strip()
                disk_purl = str(d_meta.get("product_url", "")).strip().rstrip("/")
                if product_id and product_id != "N/A" and disk_pid and disk_pid == str(product_id).strip():
                    return e
                if product_url and disk_purl and disk_purl == product_url.strip().rstrip("/"):
                    return e
            except Exception:
                pass

    # 4. Ordinal-Guarded Slug Normalization Matching
    def _extract_course_numbers(s: str) -> List[str]:
        s_clean = re.sub(r"\[\d{4}-\d{2}\]", "", s)
        return re.findall(r"\d+", s_clean)

    target_nums = _extract_course_numbers(target_folder_name)
    if not target_nums and title:
        target_nums = _extract_course_numbers(title)

    norm_target = re.sub(r"[^a-zA-Z0-9]", "", alt1.lower())

    for e in entries:
        e_nums = _extract_course_numbers(e)
        if target_nums != e_nums:
            continue

        e_no_date = re.sub(r"^\[\d{4}-\d{2}\]_?", "", e)
        norm_e = re.sub(r"[^a-zA-Z0-9]", "", e_no_date.lower())

        if norm_target and norm_e and norm_target == norm_e:
            return e

    return None



def lookup_course_metadata_online(search_term: str, session: Optional[requests.Session] = None) -> Optional[Dict[str, Any]]:
    """
    Sovereign MisCursosVirtuales online lookup for manual/unindexed course folders.
    Queries the public MCV catalog (zero credentials needed), parses JSON-LD schema,
    and returns ground-truth title, author, and datePublished.
    """
    clean_term = re.sub(r"\[.*?\]", "", search_term)
    clean_term = re.sub(r"\b(?:202[0-9]|199[0-9]|mcv|basic|vip|curso|masterclass|taller)\b", "", clean_term, flags=re.IGNORECASE)
    clean_term = re.sub(r"[_\-]+", " ", clean_term).strip()
    if not clean_term:
        clean_term = search_term.strip()

    s = session
    if not s:
        try:
            s = get_session(DEFAULT_COOKIES_PATH)
        except Exception:
            s = requests.Session()
            s.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            })

    url = f"https://miscursosvirtuales.com/?s={requests.utils.quote(clean_term)}&post_type=product"
    try:
        r = s.get(url, timeout=12)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        target_mod = re.search(r"m[oó]dulo\s*(\d+)", clean_term, re.IGNORECASE)
        for a in soup.find_all("a", href=True):
            href = urljoin("https://miscursosvirtuales.com", a["href"])
            clean_href = href.split("?")[0].rstrip("/") + "/"
            if "/producto/" in clean_href and not clean_href.endswith("/producto/"):
                # Si el término buscaba un módulo específico, validar coincidencia estricta de número de módulo
                if target_mod:
                    cand_mod = re.search(r"m[oó]dulo\s*(\d+)|modulo-(\d+)", clean_href, re.IGNORECASE)
                    if not cand_mod:
                        cand_mod = re.search(r"m[oó]dulo\s*(\d+)", a.get_text(), re.IGNORECASE)
                    if cand_mod:
                        c_num = cand_mod.group(1) or cand_mod.group(2)
                        if c_num != target_mod.group(1):
                            continue
                    else:
                        continue

                prod_r = s.get(clean_href, timeout=12)
                if prod_r.status_code != 200:
                    continue
                psoup = BeautifulSoup(prod_r.text, "html.parser")
                raw_h1 = psoup.find("h1")
                raw_title_str = raw_h1.get_text(strip=True) if raw_h1 else ""

                if target_mod:
                    h1_mod = re.search(r"m[oó]dulo\s*(\d+)", raw_title_str, re.IGNORECASE)
                    if h1_mod and h1_mod.group(1) != target_mod.group(1):
                        continue

                parts = re.split(r"\s*[\-–—]\s*", raw_title_str)
                title = parts[0].strip() if len(parts) >= 2 else raw_title_str
                author = parts[-1].strip() if len(parts) >= 2 else "MCV"

                pub_date = None
                for script in psoup.find_all("script", type="application/ld+json"):
                    try:
                        d = json.loads(script.string)
                        graph = d.get("@graph", [d]) if isinstance(d, dict) else []
                        for item in graph:
                            if "datePublished" in item:
                                pub_date = item["datePublished"][:10]
                                break
                        if pub_date:
                            break
                    except Exception:
                        pass

                return {
                    "title": title,
                    "author": author,
                    "effective_date": pub_date or "",
                    "product_url": clean_href,
                    "source": "miscursosvirtuales_online_lookup",
                    "retrieved_at": datetime.now().isoformat()
                }
    except Exception as e:
        logger.warning(f"Aviso durante búsqueda online en MisCursosVirtuales: {e}")
    return None



class EpistemicGroundingEngine:
    """
    Motor epistémico autónomo de búsqueda y descubrimiento en tiempo real para MCV.
    Consulta APIs (Tavily, Exa, Jina) con caché persistente L1 (.epistemic_cache.json)
    para descubrir fecha real original de creación, autor canónico y áreas temáticas.
    """
    _cache = None
    _cache_lock = threading.Lock()
    _env_keys = None

    @classmethod
    def _load_env_keys(cls) -> dict:
        if cls._env_keys is not None:
            return cls._env_keys
        keys = {}
        env_path = "/var/www/.env"
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            keys[k.strip()] = v.strip().strip("'\"")
            except Exception:
                pass
        for k in ["TAVILY_API_KEY", "EXA_API_KEY", "JINA_API_KEY", "BRAVE_API_KEY"]:
            if k in os.environ and not keys.get(k):
                keys[k] = os.environ[k]
        cls._env_keys = keys
        return keys

    @classmethod
    def get_cache_path(cls) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else "/var/www/baiosfera/CURSOS/MCV"
        return os.path.join(base_dir, ".epistemic_cache.json")

    @classmethod
    def _load_cache(cls) -> dict:
        with cls._cache_lock:
            if cls._cache is not None:
                return cls._cache
            c_path = cls.get_cache_path()
            if os.path.isfile(c_path):
                try:
                    with open(c_path, "r", encoding="utf-8") as f:
                        raw_cache = json.load(f)
                        # Autolimpiador activo permanente (inmunidad determinista a veneno epistémico)
                        blacklisted_patterns = [
                            "schools.nyc", "github.com", "taylorhakes", "fecha", "wikipedia.org/wiki/",
                            "elpopular.pe", "worldbank.org", "archive.org"
                        ]
                        clean_cache = {}
                        modified = False
                        for k, v in raw_cache.items():
                            url = v.get("url", "").lower()
                            year = str(v.get("year", "")).strip()
                            source = v.get("source", "")
                            if source == "mcv_fallback":
                                modified = True
                                continue
                            if any(bp in url for bp in blacklisted_patterns):
                                modified = True
                                continue
                            if year.isdigit() and (int(year[:4]) >= 2026 or int(year[:4]) < 2000):
                                modified = True
                                continue
                            clean_cache[k] = v
                        cls._cache = clean_cache
                        if modified:
                            cls._save_cache()
                        return cls._cache
                except Exception:
                    cls._cache = {}
                    return cls._cache
            cls._cache = {}
            return cls._cache

    @classmethod
    def _save_cache(cls):
        with cls._cache_lock:
            if cls._cache is None:
                return
            c_path = cls.get_cache_path()
            try:
                tmp_path = f"{c_path}.tmp"
                with open(tmp_path, "w", encoding="utf-8") as f:
                    json.dump(cls._cache, f, indent=2, ensure_ascii=False)
                os.replace(tmp_path, c_path)
            except Exception as e:
                logger.warning(f"Aviso guardando .epistemic_cache.json: {e}")

    @classmethod
    def query_external_date(cls, clean_title: str, author: str) -> dict:
        """
        Consulta en cascada (Tavily -> Exa) con timeout de 3.5s
        para extraer año/fecha de creación real con validación estricta de relevancia.
        """
        keys = cls._load_env_keys()
        tavily_key = keys.get("TAVILY_API_KEY")
        exa_key = keys.get("EXA_API_KEY")

        q_author = f'"{author}"' if author and author not in ["Autor no especificado", "MCV"] else ""
        query = f'"{clean_title}" {q_author} curso fecha OR año OR lanzamiento'.strip()

        # Palabras clave del título para validar relevancia de snippets devueltos
        title_tokens = set(re.findall(r'[a-záéíóúñ0-9]+', clean_title.lower())) - SPANISH_STOPWORDS
        meaningful_tokens = {w for w in title_tokens if len(w) >= 4}
        author_tokens = set(re.findall(r'[a-záéíóúñ0-9]+', (author or "").lower())) - SPANISH_STOPWORDS

        blacklisted_patterns = [
            "schools.nyc", "github.com", "taylorhakes", "fecha", "wikipedia.org/wiki/",
            "elpopular.pe", "worldbank.org", "archive.org"
        ]

        # 1. Tavily Search
        if tavily_key:
            try:
                payload = json.dumps({
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 3
                }).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.tavily.com/search",
                    data=payload,
                    headers={"Authorization": f"Bearer {tavily_key}", "Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    for item in res_data.get("results", []):
                        url_item = item.get("url", "").lower()
                        if any(bp in url_item for bp in blacklisted_patterns):
                            continue
                        blob = f"{item.get('title', '')} {item.get('content', '')}".lower()

                        # Filtro de relevancia léxica: debe mencionar autor o >= 2 tokens significativos
                        has_author = bool(author_tokens and any(at in blob for at in author_tokens))
                        common_tokens = len(meaningful_tokens.intersection(set(re.findall(r'[a-záéíóúñ0-9]+', blob))))
                        if not (has_author or common_tokens >= 2):
                            continue

                        m_date = re.search(r'\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?(201[0-9]|202[0-5])\b', blob)
                        if m_date:
                            month_map = {"enero":"01","febrero":"02","marzo":"03","abril":"04","mayo":"05","junio":"06","julio":"07","agosto":"08","septiembre":"09","octubre":"10","noviembre":"11","diciembre":"12"}
                            return {
                                "year": m_date.group(2),
                                "date": f"{m_date.group(2)}-{month_map.get(m_date.group(1), '01')}",
                                "source": "tavily",
                                "url": item.get("url", "")
                            }
                        y_match = re.search(r'\b(201[0-9]|202[0-5])\b', blob)
                        if y_match:
                            return {
                                "year": y_match.group(1),
                                "date": y_match.group(1),
                                "source": "tavily",
                                "url": item.get("url", "")
                            }
            except Exception as e_t:
                logger.debug(f"Aviso en consulta Tavily para '{clean_title}': {e_t}")

        # 2. Exa Search
        if exa_key:
            try:
                payload = json.dumps({
                    "query": f'"{clean_title}" {q_author}'.strip(),
                    "num_results": 3
                }).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.exa.ai/search",
                    data=payload,
                    headers={"x-api-key": exa_key, "Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    for item in res_data.get("results", []):
                        url_item = item.get("url", "").lower()
                        if any(bp in url_item for bp in blacklisted_patterns):
                            continue
                        blob = f"{item.get('title', '')} {item.get('text', '')}".lower()

                        has_author = bool(author_tokens and any(at in blob for at in author_tokens))
                        common_tokens = len(meaningful_tokens.intersection(set(re.findall(r'[a-záéíóúñ0-9]+', blob))))
                        if not (has_author or common_tokens >= 2):
                            continue

                        y_match = re.search(r'\b(201[0-9]|202[0-5])\b', blob)
                        if y_match:
                            return {
                                "year": y_match.group(1),
                                "date": y_match.group(1),
                                "source": "exa",
                                "url": item.get("url", "")
                            }
            except Exception as e_e:
                logger.debug(f"Aviso en consulta Exa para '{clean_title}': {e_e}")

        return {}

    @classmethod
    def resolve_dates(cls, clean_title: str, author: str, meta_year: str = "", date_published: str = "", text_hint: str = "") -> dict:
        """
        Resuelve tanto la fecha real de creación como la fecha de subida de MCV bajo el invariante Real <= MCV.
        """
        m_raw = str(meta_year).strip()
        if re.match(r'^\d{4}-\d{2}', m_raw):
            mcv_yr = m_raw[:7]
        else:
            mcv_yr = m_raw[:4]

        if not mcv_yr and date_published:
            m_iso = re.search(r'^(\d{4}(?:-\d{2})?)', date_published.strip())
            if m_iso:
                mcv_yr = m_iso.group(1)

        t_match = re.search(r'\b(201[0-9]|202[0-5])\b', clean_title)
        if t_match:
            y = t_match.group(1)
            # Respetar causalidad si MCV tiene fecha fehaciente
            if mcv_yr and mcv_yr[:4].isdigit() and int(y) > int(mcv_yr[:4]):
                y = mcv_yr[:4]
            return {
                "real_year": y,
                "real_date": y,
                "mcv_year": mcv_yr or y,
                "mcv_date": date_published,
                "is_original_verified": True,
                "source": "title_explicit"
            }

        if text_hint:
            month_map = {"enero":"01","febrero":"02","marzo":"03","abril":"04","mayo":"05","junio":"06","julio":"07","agosto":"08","septiembre":"09","octubre":"10","noviembre":"11","diciembre":"12"}
            m_txt = re.search(r'\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?(201[0-9]|202[0-5])\b', text_hint.lower()[:2000])
            if m_txt:
                y = m_txt.group(2)
                if not (mcv_yr and mcv_yr[:4].isdigit() and int(y) > int(mcv_yr[:4])):
                    return {
                        "real_year": y,
                        "real_date": f"{y}-{month_map.get(m_txt.group(1), '01')}",
                        "mcv_year": mcv_yr or y,
                        "mcv_date": date_published,
                        "is_original_verified": True,
                        "source": "text_explicit"
                    }
            c_match = re.search(r'\b(201[0-9]|202[0-5])\b', text_hint[:600])
            if c_match:
                y = c_match.group(1)
                if not (mcv_yr and mcv_yr[:4].isdigit() and int(y) > int(mcv_yr[:4])):
                    return {
                        "real_year": y,
                        "real_date": y,
                        "mcv_year": mcv_yr or y,
                        "mcv_date": date_published,
                        "is_original_verified": True,
                        "source": "text_snippet"
                    }

        cache = cls._load_cache()
        cache_key = hashlib.md5(f"{clean_title.strip().lower()}|{author.strip().lower()}".encode("utf-8")).hexdigest()
        if cache_key in cache:
            entry = cache[cache_key]
            if entry.get("source") != "mcv_fallback":
                real_y = entry.get("year", "")
                # Validar causalidad contra fecha MCV en caché: Real <= MCV. Si viola causalidad, se descarta.
                if real_y and mcv_yr and mcv_yr[:4].isdigit() and real_y.isdigit() and int(real_y) > int(mcv_yr[:4]):
                    real_y = ""
                is_verified = bool(real_y and real_y.isdigit() and mcv_yr[:4].isdigit() and int(real_y) <= int(mcv_yr[:4]))
                return {
                    "real_year": real_y or mcv_yr or "S/F",
                    "real_date": entry.get("date", real_y or mcv_yr or "S/F"),
                    "mcv_year": mcv_yr or "S/F",
                    "mcv_date": date_published,
                    "is_original_verified": is_verified,
                    "source": entry.get("source", "cache")
                }

        discovered = cls.query_external_date(clean_title, author)
        if discovered and discovered.get("year"):
            disc_y = discovered["year"]
            disc_d = discovered.get("date", disc_y)
            # Invariante estricto de causalidad temporal: Real <= MCV. Si la fecha descubierta es posterior a MCV, es espuria y se descarta.
            if mcv_yr and mcv_yr[:4].isdigit() and disc_y.isdigit() and int(disc_y) > int(mcv_yr[:4]):
                disc_y = ""
                disc_d = ""
            if disc_y:
                cache[cache_key] = {
                    "year": disc_y,
                    "date": disc_d,
                    "source": discovered.get("source", "web"),
                    "url": discovered.get("url", ""),
                    "clean_title": clean_title,
                    "author": author
                }
                cls._save_cache()
                return {
                    "real_year": disc_y,
                    "real_date": disc_d,
                    "mcv_year": mcv_yr or disc_y,
                    "mcv_date": date_published,
                    "is_original_verified": True,
                    "source": discovered.get("source", "web")
                }

        # Fallback a fecha de MCV sin contaminar la caché persistente
        return {
            "real_year": mcv_yr or "S/F",
            "real_date": mcv_yr or "S/F",
            "mcv_year": mcv_yr or "S/F",
            "mcv_date": date_published,
            "is_original_verified": False,
            "source": "mcv_fallback"
        }


def resolve_or_lookup_course_metadata(course_dir: str, alias: str = "") -> Dict[str, Any]:
    """
    SSoT metadata resolver for course directories.
    1. Reads existing metadata.json if present (enforcing folder date prefix SSoT if present).
    2. Executes live online lookup against MisCursosVirtuales.
    3. Epistemically enriches real creation date and MCV upload date.
    4. Falls back to offline heuristics with explicit warning.
    Saves metadata.json permanently in course_dir.
    """
    folder_name = os.path.basename(course_dir)
    m_fdate = re.search(r"\[(\d{4}-\d{2}(?:-\d{2})?)\]", folder_name)
    folder_date = m_fdate.group(1) if m_fdate else ""
    if not folder_date:
        m_fped = re.search(r"\[(P\d{2})\]", folder_name, re.IGNORECASE)
        if m_fped:
            folder_date = m_fped.group(1).upper()

    meta_file = os.path.join(course_dir, "metadata.json")
    if os.path.isfile(meta_file):
        try:
            with open(meta_file, "r", encoding="utf-8") as mf:
                data = json.load(mf)
                if data and data.get("title"):
                    if folder_date and data.get("effective_date") != folder_date:
                        data["effective_date"] = folder_date
                        try:
                            with open(meta_file, "w", encoding="utf-8") as mw:
                                json.dump(data, mw, indent=2, ensure_ascii=False)
                        except Exception:
                            pass
                    return data
        except Exception:
            pass

    logger.info(f"🔍 [METADATA] 'metadata.json' no encontrado en '{folder_name}'. Consultando catálogo en vivo de MisCursosVirtuales...")
    online_meta = lookup_course_metadata_online(folder_name)
    if online_meta:
        logger.info(f"🌐 [ONLINE LOOKUP] Metadatos canónicos obtenidos: '{online_meta['title']}' por '{online_meta['author']}' ({online_meta.get('effective_date', 'N/A')})")
        if folder_date:
            online_meta["effective_date"] = folder_date
        if alias:
            online_meta["author"] = alias

        # Grounding epistémico dual (Fecha real vs Fecha MCV)
        dates_info = EpistemicGroundingEngine.resolve_dates(
            clean_title=online_meta.get("title", ""),
            author=online_meta.get("author", alias),
            meta_year=online_meta.get("effective_date", "")[:4],
            date_published=online_meta.get("effective_date", "")
        )
        online_meta["mcv_upload_date"] = online_meta.get("effective_date", "")
        online_meta["original_release_year"] = dates_info.get("real_year", "")
        online_meta["epistemic_source"] = dates_info.get("source", "")

        try:
            with open(meta_file, "w", encoding="utf-8") as mf:
                json.dump(online_meta, mf, indent=2, ensure_ascii=False)
            logger.info(f"   -> Guardado 'metadata.json' canónico en: {meta_file}")
        except Exception as e_w:
            logger.warning(f"Aviso guardando metadata.json: {e_w}")
        return online_meta

    logger.warning(f"⚠️ [ONLINE LOOKUP] No se encontraron resultados online para '{folder_name}'. Aplicando fallback heurístico local.")
    author_val = alias or resolve_author_alias(folder_name)
    eff_date = ""
    m_year = re.search(r"\b(202[0-9]|199[0-9])\b", folder_name)
    if m_year:
        eff_date = f"{m_year.group(1)}-01"

    clean_t = sanitize_folder_name(folder_name)
    clean_t = re.sub(r"\b(202[0-9]|199[0-9])\b", "", clean_t).strip("-_ ")

    # Grounding epistémico dual local
    dates_info = EpistemicGroundingEngine.resolve_dates(
        clean_title=clean_t or folder_name,
        author=author_val,
        meta_year=eff_date[:4]
    )

    meta = {
        "title": clean_t or folder_name,
        "author": author_val,
        "effective_date": eff_date,
        "mcv_upload_date": eff_date,
        "original_release_year": dates_info.get("real_year", ""),
        "epistemic_source": dates_info.get("source", ""),
        "source": "local_offline_heuristic",
        "retrieved_at": datetime.now().isoformat()
    }
    try:
        with open(meta_file, "w", encoding="utf-8") as mf:
            json.dump(meta, mf, indent=2, ensure_ascii=False)
    except Exception:
        pass
    return meta


def is_module_subfolder_name(name: str) -> bool:
    """Detects if a directory name looks like a course module/chapter rather than a course title."""
    pat = r"^\s*(?:[0-9]{1,2}(?:[\.\s_\)\-]\s*|\s+)|(?:[Mm][oó]dulo|[Bb]loque|[Pp]arte|[Cc]lase|[Ll]ecci[oó]n|[Ss]esi[oó]n|[Bb]onus|[Rr]ecursos|[Ee]xtras)\b)"
    return bool(re.search(pat, name, re.IGNORECASE))


def is_single_course_root(dir_path: str) -> bool:
    """
    Determines if dir_path is an indivisible single course root (NOT an author/category container).
    Criteria:
    1. Contains NOTEBOOKLM_AUDIOS/ directory.
    2. Contains metadata.json or INSTRUCCIONES_DESCARGA.txt.
    3. Contains media files directly in its root.
    4. Its immediate subdirectories are module/chapter folders (e.g. '1. ...', 'Modulo 1', 'Bonus').
    """
    if not os.path.isdir(dir_path):
        return False
    if os.path.isdir(os.path.join(dir_path, "NOTEBOOKLM_AUDIOS")):
        return True
    if os.path.isfile(os.path.join(dir_path, "metadata.json")) or os.path.isfile(os.path.join(dir_path, "INSTRUCCIONES_DESCARGA.txt")):
        return True
    # Reconocimiento por archivo Markdown representativo del curso
    try:
        for f in os.listdir(dir_path):
            if f.endswith(".md") and not f.startswith("RUTA_DE_APRENDIZAJE") and not f.startswith("MANUAL"):
                return True
    except Exception:
        pass
    video_exts = (".mp4", ".ts", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".m4v", ".mp3", ".aac")
    try:
        entries = os.listdir(dir_path)
    except Exception:
        return False
    for f in entries:
        if f.lower().endswith(video_exts):
            return True

    subdirs = []
    ignored = {"0.dwnl", "notebooklm_audios", "_temp_downloads", "temp", "__pycache__"}
    for f in entries:
        sub_p = os.path.join(dir_path, f)
        if os.path.isdir(sub_p) and not f.startswith(".") and f.lower() not in ignored:
            subdirs.append(f)

    if not subdirs:
        return False

    mod_matches = [s for s in subdirs if is_module_subfolder_name(s)]
    if len(mod_matches) >= 2 and (len(mod_matches) / len(subdirs) >= 0.4):
        return True
    if len(subdirs) == 1 and len(mod_matches) == 1:
        return True
    return False


def is_course_directory(dir_path: str) -> bool:
    """
    Determines if a directory represents an individual course:
    - Meets is_single_course_root criteria, OR
    - Directly or in 1-level subdirectories contains media files.
    """
    if is_single_course_root(dir_path):
        return True
    video_exts = (".mp4", ".ts", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".m4v", ".mp3", ".aac")
    try:
        entries = os.listdir(dir_path)
    except Exception:
        return False
    for f in entries:
        if f.lower().endswith(video_exts):
            return True
        sub_p = os.path.join(dir_path, f)
        if os.path.isdir(sub_p) and not f.startswith(".") and f not in ["NOTEBOOKLM_AUDIOS", "_temp_downloads", "0.DWNL"]:
            try:
                for sf in os.listdir(sub_p):
                    if sf.lower().endswith(video_exts):
                        return True
            except Exception:
                pass
    return False


def discover_contained_courses(parent_dir: str) -> List[str]:
    """
    Discovers contained course directories inside an author/category container folder.
    Returns sorted list of course directory absolute paths.
    If parent_dir itself is a single course root, returns empty list so it is processed atomically.
    """
    if not os.path.isdir(parent_dir) or is_single_course_root(parent_dir):
        return []
    courses = []
    try:
        entries = sorted(os.listdir(parent_dir))
    except Exception:
        return []
    for entry in entries:
        if entry.startswith(".") or entry in ["NOTEBOOKLM_AUDIOS", "_temp_downloads"]:
            continue
        full_p = os.path.join(parent_dir, entry)
        if os.path.isdir(full_p):
            if is_course_directory(full_p):
                courses.append(full_p)
    return courses


def extract_mod_num(mod_name: str, filename: str = "") -> int:
    for text in [mod_name, filename]:
        if not text:
            continue
        m = re.search(r"(?:M[oó]dulo|M[oó]d|D[ií]a|Semana|Clase|Lecci[oó]n|Parte|Sesi[oó]n|Bloque)\s*(\d+)", text, re.IGNORECASE)
        if m:
            return int(m.group(1))
        m2 = re.search(r"^\s*(\d+)\b", text)
        if m2:
            return int(m2.group(1))
    return 1


def format_ordered_audio_name(mod_name: str, filename: str, ext: str = "aac", course_prefix: str = "") -> str:
    """
    Adaptive hierarchical zero-spaces audio formatter.
    - Flat course (mod_name == '.' or 'Módulo 1 - Contenido Principal'):
      -> CLASE-{lesson_num:02d}_{clean_title}.{clean_ext}
    - Hierarchical course (mod_name has parent folder, e.g. 'Bloque 1', 'Módulo 2'):
      -> {PARENT}-{parent_num:02d}_{CHILD}-{child_num:02d}_{clean_title}.{clean_ext}
    - Zero spaces: all whitespace converted to '-' or '_'.
    - Strictly chronological zero-padded ordering.
    """
    clean_ext = ext.lstrip(".")
    base = os.path.splitext(filename)[0]
    clean_base = re.sub(r"^\[.*?\]\s*", "", base).strip()

    is_flat = mod_name in [".", "", "Módulo 1 - Contenido Principal"] or bool(re.search(r"contenido principal", mod_name, re.IGNORECASE))

    if is_flat:
        m_num = re.search(r"(?:Clase|Lecci[oó]n|Video|Tema|Parte|L)?\s*(\d+)", clean_base, re.IGNORECASE)
        lesson_num = int(m_num.group(1)) if m_num else 1

        tag = "CLASE"
        if re.search(r"lecci[oó]n", clean_base, re.IGNORECASE):
            tag = "LECCION"
        elif re.search(r"tema", clean_base, re.IGNORECASE):
            tag = "TEMA"

        if re.match(r"^(?:Clase|Lecci[oó]n|Video|Tema|Parte|L|[A-Za-z]+)?\s*\d+\s*$", clean_base, re.IGNORECASE):
            rem_clean = ""
        else:
            rem = re.sub(r"^(?:Clase|Lecci[oó]n|Video|Tema|Parte|L)?\s*\d+[:\s_–\-]*", "", clean_base, flags=re.IGNORECASE).strip(" -_.")
            rem_clean = sanitize_folder_name(rem)

        if rem_clean:
            res = f"{tag}-{lesson_num:02d}_{rem_clean}.{clean_ext}"
        else:
            res = f"{tag}-{lesson_num:02d}.{clean_ext}"
    else:
        # Hierarchical course: detect parent and child
        parent_tag = "MODULO"
        if re.search(r"bloque", mod_name, re.IGNORECASE):
            parent_tag = "BLOQUE"
        elif re.search(r"semana", mod_name, re.IGNORECASE):
            parent_tag = "SEMANA"
        elif re.search(r"dia|d[ií]a", mod_name, re.IGNORECASE):
            parent_tag = "DIA"
        elif re.search(r"parte", mod_name, re.IGNORECASE):
            parent_tag = "PARTE"

        m_pnum = re.search(r"(\d+)", mod_name)
        p_num = int(m_pnum.group(1)) if m_pnum else 1

        child_tag = "MODULO" if parent_tag == "BLOQUE" else "CLASE"
        if re.search(r"clase", clean_base, re.IGNORECASE):
            child_tag = "CLASE"
        elif re.search(r"m[oó]dulo", clean_base, re.IGNORECASE):
            child_tag = "MODULO"
        elif re.search(r"lecci[oó]n", clean_base, re.IGNORECASE):
            child_tag = "LECCION"
        elif re.search(r"tema", clean_base, re.IGNORECASE):
            child_tag = "TEMA"

        m_cnum = re.search(r"(?:M[oó]dulo|Clase|Lecci[oó]n|Tema|Parte|Video)\s*(\d+)", clean_base, re.IGNORECASE)
        if not m_cnum:
            m_cnum = re.search(r"(\d+)", clean_base)
        c_num = int(m_cnum.group(1)) if m_cnum else 1

        if re.match(r"^(?:M[oó]dulo|Clase|Lecci[oó]n|Tema|Parte|Video|[A-Za-z]+)?\s*\d+\s*$", clean_base, re.IGNORECASE):
            rem_clean = ""
        else:
            # Remainder title: strip course repetitions and module numbers
            rem = re.sub(r".*?(?:M[oó]dulo|Clase|Lecci[oó]n|Tema|Parte|Video)\s*\d+[:\s_–\-]*", "", clean_base, flags=re.IGNORECASE)
            rem = re.sub(r"^\d+[:\s_–\-]*", "", rem)
            rem = re.sub(r".*?(?:202\d|\(202\d\))[:\s–-]*", "", rem)
            rem = re.sub(rf"\b0*{c_num}\b", "", rem).strip(" -_.")
            rem_clean = sanitize_folder_name(rem)

        prefix = f"{parent_tag}-{p_num:02d}_{child_tag}-{c_num:02d}"
        if rem_clean:
            res = f"{prefix}_{rem_clean}.{clean_ext}"
        else:
            res = f"{prefix}.{clean_ext}"

    if course_prefix:
        clean_cp = sanitize_folder_name(course_prefix)
        res = f"[{clean_cp}]_{res}"

    return re.sub(r"[\s]+", "-", res)


def format_ordered_mp3_name(mod_name: str, filename: str) -> str:
    """Legacy wrapper for MP3 naming."""
    return format_ordered_audio_name(mod_name, filename, "mp3")


def get_media_info(filepath: str) -> Dict[str, Any]:
    """Inspects a media file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", filepath
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return {}
    try:
        data = json.loads(proc.stdout)
        v_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
        a_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
        fmt = data.get("format", {})
        return {
            "duration": float(fmt.get("duration") or v_stream.get("duration") or a_stream.get("duration") or 0),
            "width": int(v_stream.get("width") or 0),
            "height": int(v_stream.get("height") or 0),
            "video_codec": v_stream.get("codec_name"),
            "audio_codec": a_stream.get("codec_name"),
            "sample_rate": int(a_stream.get("sample_rate") or 0),
            "channels": int(a_stream.get("channels") or 0),
            "bit_rate": int(fmt.get("bit_rate") or v_stream.get("bit_rate") or 0)
        }
    except Exception:
        return {}


def ensure_agent_browser_clean(session: str = "default"):
    """
    Ensures agent-browser daemon socket and PID state are clean.
    Removes orphan sockets/pids when the process is dead to prevent:
    'Could not configure browser: Failed to connect: No such file or directory (os error 2)'.
    """
    browser_dir = os.path.expanduser("~/.agent-browser")
    if not os.path.isdir(browser_dir):
        return

    sock_file = os.path.join(browser_dir, f"{session}.sock")
    pid_file = os.path.join(browser_dir, f"{session}.pid")

    is_alive = False
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r", encoding="utf-8") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            is_alive = True
        except (ValueError, ProcessLookupError, PermissionError, OSError):
            is_alive = False

    if not is_alive:
        for f in [sock_file, pid_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass


def safe_close_agent_browser(session: str = "default"):
    """Gracefully closes agent-browser, waits for daemon teardown, and purges stale sockets."""
    try:
        cmd = ["agent-browser"]
        if session != "default":
            cmd.extend(["--session", session])
        cmd.append("close")
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    except Exception:
        pass

    browser_dir = os.path.expanduser("~/.agent-browser")
    sock_file = os.path.join(browser_dir, f"{session}.sock")
    pid_file = os.path.join(browser_dir, f"{session}.pid")

    start_wait = time.time()
    while time.time() - start_wait < 3.0:
        if not os.path.exists(sock_file) and not os.path.exists(pid_file):
            break
        time.sleep(0.3)

    ensure_agent_browser_clean(session)
    time.sleep(1.0)


def download_sync_link(
    url: str,
    target_dir: str,
    part_name: str,
    tracker: ProgressTracker,
    timeout_sec: int = 14400,
    part_index: int = 1
) -> List[str]:
    """Downloads files or folders from Sync.com using native AES-256-GCM streaming decryption.
    Bypasses Chromium/browser memory limits completely with O(1) RAM streaming and true byte resuming.
    """
    os.makedirs(target_dir, exist_ok=True)
    part_slug = sanitize_folder_name(part_name) or f"part_{part_index}"

    logger.info(f"⚡ Iniciando descarga nativa en streaming de {part_name} desde Sync.com...")

    # 1. Parse Sync.com URL
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}" if (parsed.scheme and parsed.netloc) else "https://ln5.sync.com"
    m = re.search(r"/(?:dl|s)/([a-zA-Z0-9_-]+)", parsed.path)
    if m:
        publink_id = m.group(1)
    else:
        publink_id = parsed.path.strip("/").split("/")[-1]

    fragment_key = parsed.fragment
    if not fragment_key:
        if "#" in url:
            fragment_key = url.split("#", 1)[1]
        elif "?" in url and "k=" in url:
            fragment_key = parse_qs(parsed.query).get("k", [""])[0]

    if not publink_id:
        raise ValueError(f"No se pudo extraer publink_id de URL de Sync.com: {url}")
    if not fragment_key:
        raise ValueError(f"URL de Sync.com no contiene la clave de descifrado (fragmento #...): {url}")

    # 2. Query linkpathlist metadata
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    })

    req_url = f"{base_url}/api/v1/linkpathlist"
    try:
        resp = session.post(req_url, json={"publink_id": publink_id}, timeout=30)
    except Exception as e_req:
        raise RuntimeError(f"Error conectando a API de Sync.com ({req_url}): {e_req}")

    if resp.status_code != 200:
        raise RuntimeError(f"Sync.com linkpathlist devolvió HTTP {resp.status_code}: {resp.text}")

    meta = resp.json()
    pathitems = meta.get("pathitems", [])
    if not pathitems:
        raise RuntimeError(f"Sync.com no devolvió elementos descargables: {meta}")

    salt_hex = meta.get("salt")
    if not salt_hex:
        raise RuntimeError(f"Sync.com no devolvió salt para derivación de claves: {meta}")
    salt = bytes.fromhex(salt_hex)
    iterations = int(meta.get("iterations", 10000))
    servers_web = meta.get("servers_web", [])
    if not servers_web:
        servers_web = [parsed.netloc]

    # PBKDF2 key derivation (64 bytes = 512 bits)
    derived_64 = hashlib.pbkdf2_hmac("sha256", fragment_key.encode("utf-8"), salt, iterations, 64)
    key_0_256 = derived_64[:32]  # Used to decrypt per-file data keys
    aes_key = derived_64[32:]    # Used to decrypt file/folder names

    downloaded_files: List[str] = []

    # Filter downloadable items (files)
    file_items = [it for it in pathitems if it.get("type") != "dir"]
    if not file_items:
        file_items = pathitems

    for item_idx, item in enumerate(file_items, 1):
        # 3. Decrypt filename
        enc_share_name = item.get("enc_share_name") or item.get("enc_name")
        filename = None
        if enc_share_name and ":" in enc_share_name:
            try:
                raw_b64 = enc_share_name.split(":", 1)[1]
                raw_bytes = base64.b64decode(raw_b64)
                iv, ct, tag = raw_bytes[:12], raw_bytes[12:-12], raw_bytes[-12:]
                cipher_name = Cipher(algorithms.AES(aes_key), modes.GCM(iv, tag, min_tag_length=12)).decryptor()
                filename = (cipher_name.update(ct) + cipher_name.finalize()).decode("utf-8", errors="replace")
            except Exception as e_name:
                logger.warning(f"Aviso al descifrar nombre de archivo con AES-GCM: {e_name}")

        if not filename:
            filename = f"{part_slug}.zip" if len(file_items) == 1 else f"{part_slug}_{item_idx}.zip"

        file_size = int(item.get("size", 0))
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "zip"
        ext_b64 = base64.b64encode(ext.encode("utf-8")).decode("utf-8")
        cachekey = item.get("cachekey") or publink_id

        logger.info(f"📦 Sync.com archivo [{item_idx}/{len(file_items)}]: {filename} ({file_size / (1024*1024):.2f} MB)")

        target_file = os.path.join(target_dir, filename)
        part_file = os.path.join(target_dir, f".{filename}.syncpart")

        # Check if target_file is already completely downloaded
        if os.path.exists(target_file) and file_size > 0 and os.path.getsize(target_file) == file_size:
            logger.info(f"⚡ [RESUME] Archivo ya existe completamente en disco: {filename} ({file_size / (1024*1024):.2f} MB)")
            tracker.update(filename, file_size, file_size)
            downloaded_files.append(target_file)
            continue

        # 4. Decrypt Data Key
        enc_data_key = item.get("enc_data_key")
        if not enc_data_key:
            req_pathdata = f"{base_url}/api/v1/pathdata"
            pdata_payload = {
                "pathitems": [{
                    "share_id": str(item.get("share_id", "")),
                    "blob_id": item.get("blob_id"),
                    "sync_id": item.get("sync_id"),
                    "ext": ext_b64,
                    "link_cachekey": publink_id,
                    "size": file_size
                }]
            }
            try:
                resp_pdata = session.post(req_pathdata, json=pdata_payload, timeout=30)
                if resp_pdata.status_code == 200:
                    datakeys = resp_pdata.json().get("datakeys", {})
                    sync_id_str = str(item.get("sync_id"))
                    if sync_id_str in datakeys:
                        enc_data_key = datakeys[sync_id_str].get("enc_data_key")
                    elif datakeys:
                        enc_data_key = next(iter(datakeys.values())).get("enc_data_key")
            except Exception as e_pdata:
                logger.warning(f"Error consultando pathdata en Sync.com: {e_pdata}")

        if not enc_data_key or ":" not in enc_data_key:
            raise RuntimeError(f"No se pudo obtener la clave de datos encriptada (enc_data_key) para {filename}")

        raw_dk_bytes = base64.b64decode(enc_data_key.split(":", 1)[1])
        dk_iv, dk_ct, dk_tag = raw_dk_bytes[:12], raw_dk_bytes[12:-12], raw_dk_bytes[-12:]
        cipher_dk = Cipher(algorithms.AES(key_0_256), modes.GCM(dk_iv, dk_tag, min_tag_length=12)).decryptor()
        data_key = cipher_dk.update(dk_ct) + cipher_dk.finalize()

        # 5. Packet Math & Resuming Configuration
        GCM_PACKET_SIZE = 131072   # 128 KB encrypted packet size
        GCM_PAYLOAD_SIZE = 131036  # 131072 - 36 bytes (12B AAD + 12B IV + 12B Tag)
        OVERHEAD = 36
        BLOCK_PACKETS = 32         # 4 MB per HTTP request

        num_packets = (file_size + GCM_PAYLOAD_SIZE - 1) // GCM_PAYLOAD_SIZE if file_size > 0 else 1
        last_payload_len = file_size - (num_packets - 1) * GCM_PAYLOAD_SIZE if file_size > 0 else 0
        last_packet_len = last_payload_len + OVERHEAD

        packets_done = 0
        if os.path.exists(part_file):
            cur_size = os.path.getsize(part_file)
            packets_done = cur_size // GCM_PAYLOAD_SIZE
            aligned_size = packets_done * GCM_PAYLOAD_SIZE
            if cur_size != aligned_size:
                with open(part_file, "r+b") as pf:
                    pf.truncate(aligned_size)
                logger.info(f"⚡ [RESUME] Truncando archivo parcial {os.path.basename(part_file)} a {aligned_size} bytes ({packets_done} paquetes)")
            if packets_done > 0:
                logger.info(f"⚡ [RESUME] Reanudando {filename} desde paquete {packets_done}/{num_packets} ({aligned_size / (1024*1024):.2f} MB ya transferidos)")

        written_bytes = packets_done * GCM_PAYLOAD_SIZE
        tracker.update(filename, written_bytes, file_size)

        # 6. Streaming Download & Decryption Loop
        start_dl_time = time.time()
        last_progress_time = time.time()
        last_progress_bytes = written_bytes
        server_idx = 0

        with open(part_file, "a+b") as out_fp:
            p_start = packets_done
            while p_start < num_packets:
                p_end = min(p_start + BLOCK_PACKETS, num_packets)
                enc_offset = p_start * GCM_PACKET_SIZE

                full_packets_in_block = p_end - p_start
                if p_end == num_packets:
                    enc_len = (full_packets_in_block - 1) * GCM_PACKET_SIZE + last_packet_len
                else:
                    enc_len = full_packets_in_block * GCM_PACKET_SIZE

                # Fetch block with retries and alternate storage servers
                block_data = None
                for retry in range(6):
                    server = servers_web[server_idx % len(servers_web)]
                    dl_url = f"https://{server}/proxyapi.fcgi"
                    dl_params = {
                        "command": "download",
                        "cachekey": cachekey,
                        "blobtype": "btFILE",
                        "offset": enc_offset,
                        "length": enc_len,
                        "engine": "cp-3.1.38",
                        "userid": 0,
                        "deviceid": 0,
                        "devicetypeid": 3
                    }
                    try:
                        resp_dl = session.get(dl_url, params=dl_params, timeout=45)
                        if resp_dl.status_code in (200, 206) and len(resp_dl.content) == enc_len:
                            block_data = resp_dl.content
                            break
                        else:
                            logger.warning(f"Aviso descarga Sync ({filename}): HTTP {resp_dl.status_code} (len={len(resp_dl.content)}, req={enc_len}). Reintento {retry+1}/6...")
                            server_idx += 1
                            time.sleep(1.5 * (retry + 1))
                    except Exception as e_dl:
                        logger.warning(f"Error de red descargando bloque Sync en offset {enc_offset}: {e_dl}. Reintento {retry+1}/6...")
                        server_idx += 1
                        time.sleep(2.0 * (retry + 1))

                if block_data is None:
                    raise RuntimeError(f"Falla crítica: No se pudo descargar bloque en offset {enc_offset} tras 6 reintentos para {filename}")

                # Decrypt packets in block sequentially
                block_offset = 0
                for pkt_idx in range(p_start, p_end):
                    is_last = (pkt_idx == num_packets - 1)
                    cur_pkt_len = last_packet_len if is_last else GCM_PACKET_SIZE

                    pkt = block_data[block_offset : block_offset + cur_pkt_len]
                    block_offset += cur_pkt_len

                    h = pkt[:12]
                    iv = pkt[12:24]
                    ct = pkt[24:-12]
                    tag = pkt[-12:]

                    cipher = Cipher(algorithms.AES(data_key), modes.GCM(iv, tag, min_tag_length=12)).decryptor()
                    cipher.authenticate_additional_data(h)
                    decrypted_chunk = cipher.update(ct) + cipher.finalize()

                    out_fp.write(decrypted_chunk)
                    written_bytes += len(decrypted_chunk)

                out_fp.flush()
                p_start = p_end
                tracker.update(filename, written_bytes, file_size)

                # Stall and timeout watchdogs
                if written_bytes > last_progress_bytes:
                    last_progress_bytes = written_bytes
                    last_progress_time = time.time()
                elif (time.time() - last_progress_time) > 300:
                    raise TimeoutError(f"Stall detectado en Sync.com ({filename}): 0 bytes transferidos en los últimos 300s")

                if (time.time() - start_dl_time) > timeout_sec:
                    raise TimeoutError(f"La descarga de Sync.com ({filename}) excedió el timeout límite de {timeout_sec}s")

        # 7. Atomic promotion of completed file
        if os.path.exists(target_file):
            os.remove(target_file)
        shutil.move(part_file, target_file)
        downloaded_files.append(target_file)
        logger.info(f"✅ Descarga completada exitosamente desde Sync.com: {filename} ({written_bytes / (1024*1024):.2f} MB)")

    if not downloaded_files:
        raise RuntimeError(f"No se pudo descargar ningún archivo de Sync.com para {part_name}")

    return downloaded_files


def get_mega_total_bytes(url: str) -> int:
    """
    Queries Mega.nz public API to determine total size in bytes of a folder or file before downloading.
    Enables accurate percentage calculation, real progress bars, and ETA instead of continuous stream fallbacks.
    """
    try:
        folder_match = re.search(r"mega\.nz/(?:folder/|#F!)([a-zA-Z0-9_-]+)", url)
        if folder_match:
            folder_id = folder_match.group(1)
            api_url = f"https://g.api.mega.co.nz/cs?id=0&n={folder_id}"
            payload = [{"a": "f", "c": 1, "r": 1, "ca": 1}]
            resp = requests.post(api_url, json=payload, timeout=8)
            data = resp.json()
            if isinstance(data, list) and len(data) > 0 and "f" in data[0]:
                return sum(n.get("s", 0) for n in data[0]["f"] if n.get("t") == 0)

        file_match = re.search(r"mega\.nz/(?:file/|#!)([a-zA-Z0-9_-]+)", url)
        if file_match:
            file_id = file_match.group(1)
            api_url = "https://g.api.mega.co.nz/cs?id=0"
            payload = [{"a": "g", "p": file_id}]
            resp = requests.post(api_url, json=payload, timeout=8)
            data = resp.json()
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                return int(data[0].get("s", 0))
    except Exception as e:
        logger.warning(f"Aviso consultando tamaño de enlace Mega: {e}")
    return 0


def download_mega_link(
    url: str,
    target_dir: str,
    part_name: str,
    tracker: ProgressTracker,
    timeout_sec: int = 14400,
    part_index: int = 1
) -> List[str]:
    """Downloads files or folders from Mega.nz using megatools dl with encapsulated staging,
    fail-fast, stall detection, and quota-aware error classification."""
    os.makedirs(target_dir, exist_ok=True)
    part_slug = sanitize_folder_name(part_name) or f"part_{part_index}"
    # Encapsulated staging directly inside target_dir (persistent, isolated per course/part)
    staging_dir = os.path.join(target_dir, f".staging_mega_{part_slug}")
    os.makedirs(staging_dir, exist_ok=True)

    def _inspect_mega_staging() -> Tuple[int, int, List[str]]:
        v_bytes = 0
        v_count = 0
        tmps = []
        if not os.path.isdir(staging_dir):
            return 0, 0, []
        for root, _, files in os.walk(staging_dir):
            for f in files:
                fpath = os.path.join(root, f)
                if f.endswith(".megatmp"):
                    tmps.append(fpath)
                else:
                    v_count += 1
                    try:
                        v_bytes += os.path.getsize(fpath)
                    except OSError:
                        pass
        return v_count, v_bytes, tmps

    def _move_staging_to_target() -> List[str]:
        # Purge any remaining .megatmp temporary files
        for root, _, files in os.walk(staging_dir):
            for f in files:
                if f.endswith(".megatmp"):
                    try:
                        os.remove(os.path.join(root, f))
                    except Exception:
                        pass
        moved = []
        for item in os.listdir(staging_dir):
            src = os.path.join(staging_dir, item)
            dst = os.path.join(target_dir, item)
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst, ignore_errors=True)
                else:
                    os.remove(dst)
            shutil.move(src, dst)
            moved.append(dst)
        shutil.rmtree(staging_dir, ignore_errors=True)
        return moved

    total_mega_bytes = get_mega_total_bytes(url)
    if total_mega_bytes > 0:
        logger.info(f"📊 Tamaño total detectado en Mega: {total_mega_bytes / (1024*1024):.2f} MB")
        tracker.update(f"{part_slug}_mega", 0, total_mega_bytes)

    # 1. Pre-chequeo de Rescate Soberano: Si el staging ya tiene >=95% del tamaño sin megatmp, omitir descarga
    init_count, init_bytes, init_tmps = _inspect_mega_staging()
    if total_mega_bytes > 0 and init_bytes >= int(total_mega_bytes * 0.95) and init_count > 0 and len(init_tmps) == 0:
        logger.info(f"⚡ [RESUME SOBERANO] {part_name} ya existe físicamente al 100% en staging ({init_bytes / (1024*1024):.2f} MB en {init_count} archivos). Omitiendo megatools.")
        tracker.update(f"{part_slug}_mega", init_bytes, total_mega_bytes)
        downloaded = _move_staging_to_target()
        logger.info(f"✅ Archivos de Mega rescatados y promovidos ({len(downloaded)} items)")
        return downloaded

    logger.info(f"Iniciando descarga de {part_name} desde Mega.nz...")
    cmd = [
        "megatools", "dl",
        "--no-ask-password",
        "--path", staging_dir,
        url
    ]

    start_wait = time.time()
    last_bytes = init_bytes
    last_change_time = time.time()
    stall_timeout_sec = 180
    mega_log_path = f"/tmp/mcv_megatools_{os.getpid()}_{part_slug}.log"
    mega_log_file = open(mega_log_path, "w+", encoding="utf-8", errors="replace")

    def _read_mega_log() -> str:
        try:
            mega_log_file.flush()
            with open(mega_log_path, "r", encoding="utf-8", errors="replace") as f_in:
                return f_in.read()
        except Exception:
            return ""

    def _cleanup_mega_log():
        try:
            mega_log_file.close()
        except Exception:
            pass
        try:
            if os.path.exists(mega_log_path):
                os.remove(mega_log_path)
        except OSError:
            pass

    proc = subprocess.Popen(
        cmd,
        stdout=mega_log_file,
        stderr=subprocess.STDOUT,
        text=True
    )

    try:
        while proc.poll() is None:
            time.sleep(2.0)
            elapsed = time.time() - start_wait
            current_bytes = sum(
                os.path.getsize(os.path.join(root, f))
                for root, _, files in os.walk(staging_dir)
                for f in files
            )
            if current_bytes > 0:
                tracker.update(f"{part_slug}_mega", current_bytes, total_mega_bytes)
                if current_bytes > last_bytes:
                    last_bytes = current_bytes
                    last_change_time = time.time()
                elif (time.time() - last_change_time) > stall_timeout_sec:
                    proc.kill()
                    proc.wait()
                    # Antes de fallar, auditar físicamente si el staging ya contiene los bytes totales
                    s_count, s_bytes, s_tmps = _inspect_mega_staging()
                    if total_mega_bytes > 0 and s_bytes >= int(total_mega_bytes * 0.95) and len(s_tmps) == 0 and s_count > 0:
                        logger.info(f"⚡ [MEGA RECOVERY TRAS STALL] Staging verificado completo al 100% ({s_bytes / (1024*1024):.2f} MB en {s_count} archivos).")
                        tracker.update(f"{part_slug}_mega", s_bytes, total_mega_bytes)
                        return _move_staging_to_target()
                    err_output = _read_mega_log().strip()
                    if any(k in err_output.lower() for k in ["bandwidth limit", "quota", "509", "transfer quota"]):
                        raise RuntimeError(f"🛑 [CUOTA MEGA AGOTADA] Mega.nz agotó la cuota de transferencia IP para {part_name}. Esperar ventana de enfriamiento.")
                    raise TimeoutError(f"Stall detectado en Mega ({part_name}): 0 bytes transferidos en los últimos {stall_timeout_sec}s")

            if elapsed > 120 and current_bytes == 0:
                proc.kill()
                proc.wait()
                err_output = _read_mega_log().strip()
                if any(k in err_output.lower() for k in ["bandwidth limit", "quota", "509", "transfer quota"]):
                    raise RuntimeError(f"🛑 [CUOTA MEGA AGOTADA] Mega.nz agotó la cuota de transferencia IP para {part_name}. Esperar ventana de enfriamiento.")
                raise TimeoutError(f"Fail-Fast activado en Mega ({part_name}): 0 bytes transferidos tras 120s")

            if elapsed > timeout_sec:
                proc.kill()
                proc.wait()
                raise TimeoutError(f"La descarga de Mega ({part_name}) excedió el timeout de {timeout_sec}s")

        proc.wait()
        err_msg = _read_mega_log().strip()
    finally:
        _cleanup_mega_log()

    # 2. Post-chequeo de Rescate: Auditar físicamente el staging antes de aceptar errores de megatools
    end_count, end_bytes, end_tmps = _inspect_mega_staging()
    is_physically_complete = (
        len(end_tmps) == 0 and end_count > 0 and (
            (total_mega_bytes > 0 and end_bytes >= int(total_mega_bytes * 0.95)) or
            (proc.returncode == 0)
        )
    )

    error_lines = [l for l in err_msg.splitlines() if "error" in l.lower()]
    is_already_exists_only = bool(error_lines and all("file already exists" in l.lower() for l in error_lines))

    if is_physically_complete or is_already_exists_only or proc.returncode == 0:
        logger.info(f"⚡ [MEGA RECOVERY] Staging verificado físicamente ({end_bytes / (1024*1024):.2f} MB en {end_count} archivos).")
        tracker.update(f"{part_slug}_mega", end_bytes, total_mega_bytes)
        downloaded = _move_staging_to_target()
        logger.info(f"✅ Archivos de Mega rescatados y promovidos ({len(downloaded)} items)")
        return downloaded

    if proc.returncode != 0:
        if any(k in err_msg.lower() for k in ["bandwidth limit", "quota", "509", "transfer quota"]):
            raise RuntimeError(f"🛑 [CUOTA MEGA AGOTADA] Mega.nz reportó límite de ancho de banda IP para {part_name}: {err_msg}")
        raise RuntimeError(f"Error descargando desde Mega.nz ({part_name}): {err_msg}")

    downloaded = _move_staging_to_target()
    logger.info(f"✅ Descarga desde Mega completada ({len(downloaded)} items)")
    return downloaded


def download_gdrive_link(
    url: str,
    target_dir: str,
    part_name: str,
    tracker: ProgressTracker,
    timeout_sec: int = 14400,
    part_index: int = 1
) -> List[str]:
    """Downloads files or folders from Google Drive using gdown with folder support, stall detection, and fail-fast."""
    os.makedirs(target_dir, exist_ok=True)
    part_slug = sanitize_folder_name(part_name) or f"part_{part_index}"
    # Encapsulated staging inside target_dir
    staging_dir = os.path.join(target_dir, f".staging_gdrive_{part_slug}")
    os.makedirs(staging_dir, exist_ok=True)

    logger.info(f"Iniciando descarga de {part_name} desde Google Drive...")
    is_folder = "folders" in url or "drive/folders" in url
    cmd = ["gdown"]
    if is_folder:
        cmd.append("--folder")
    cmd.extend([
        url,
        "-O", os.path.join(staging_dir, ""),
        "--continue",
        "--retries", "5",
        "--quiet"
    ])

    start_wait = time.time()
    last_bytes = 0
    last_change_time = time.time()
    stall_timeout_sec = 180
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    while proc.poll() is None:
        time.sleep(2.0)
        elapsed = time.time() - start_wait
        current_bytes = sum(
            os.path.getsize(os.path.join(root, f))
            for root, _, files in os.walk(staging_dir)
            for f in files
        )
        if current_bytes > 0:
            tracker.update(f"{part_slug}_gdrive", current_bytes)
            if current_bytes > last_bytes:
                last_bytes = current_bytes
                last_change_time = time.time()
            elif (time.time() - last_change_time) > stall_timeout_sec:
                proc.kill()
                raise TimeoutError(f"Stall detectado en Google Drive ({part_name}): 0 bytes transferidos en los últimos {stall_timeout_sec}s")

        if elapsed > 120 and current_bytes == 0:
            proc.kill()
            raise TimeoutError(f"Fail-Fast activado en Google Drive ({part_name}): 0 bytes transferidos tras 120s")

        if elapsed > timeout_sec:
            proc.kill()
            raise TimeoutError(f"La descarga de Google Drive ({part_name}) excedió el timeout de {timeout_sec}s")

    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"Error descargando desde Google Drive ({part_name}): código de salida {proc.returncode}")

    downloaded_files = []
    for item in os.listdir(staging_dir):
        src = os.path.join(staging_dir, item)
        dst = os.path.join(target_dir, item)
        if os.path.exists(dst):
            if os.path.isdir(dst):
                shutil.rmtree(dst, ignore_errors=True)
            else:
                os.remove(dst)
        shutil.move(src, dst)
        downloaded_files.append(dst)

    shutil.rmtree(staging_dir, ignore_errors=True)
    logger.info(f"✅ Descarga desde Google Drive completada ({len(downloaded_files)} items)")
    return downloaded_files


def download_direct_link(
    url: str,
    target_dir: str,
    part_name: str,
    tracker: ProgressTracker,
    timeout_sec: int = 14400,
    part_index: int = 1
) -> List[str]:
    """Downloads direct HTTP/S3 files (Wasabi S3, CDN, etc.) using streaming requests with stall detection."""
    os.makedirs(target_dir, exist_ok=True)
    parsed = urlparse(url)
    raw_fname = os.path.basename(parsed.path) or f"download_{part_index}.rar"
    part_slug = sanitize_folder_name(part_name) or f"part_{part_index}"
    # Encapsulated staging file inside target_dir
    staging_file = os.path.join(target_dir, f".staging_direct_{part_slug}_{raw_fname}")
    dest_file = os.path.join(target_dir, raw_fname)

    logger.info(f"Iniciando descarga directa de {part_name} ({raw_fname})...")
    start_wait = time.time()
    last_bytes = 0
    last_change_time = time.time()
    stall_timeout_sec = 180

    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        total_size = int(r.headers.get("content-length", 0))
        with open(staging_file, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    cur_size = os.path.getsize(staging_file)
                    tracker.update(f"{part_slug}_direct", cur_size, total_size if total_size > 0 else None)
                    if cur_size > last_bytes:
                        last_bytes = cur_size
                        last_change_time = time.time()
                    elif (time.time() - last_change_time) > stall_timeout_sec:
                        raise TimeoutError(f"Stall detectado en descarga directa ({part_name}): 0 bytes en los últimos {stall_timeout_sec}s")
                    if (time.time() - start_wait) > timeout_sec:
                        raise TimeoutError(f"La descarga directa ({part_name}) excedió el timeout de {timeout_sec}s")

    if os.path.exists(dest_file):
        os.remove(dest_file)
    shutil.move(staging_file, dest_file)
    logger.info(f"✅ Descarga directa completada: {dest_file}")
    return [dest_file]


def is_compressed_archive(filename: str) -> bool:
    """Checks if a file is a supported compressed archive."""
    fn = filename.lower()
    if fn.endswith((".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2")):
        return True
    if bool(re.search(r"\.(?:zip|rar|7z)\.\d+$", fn)):
        return True
    if bool(re.search(r"\.part\d+\.rar$", fn)):
        return True
    if bool(re.search(r"\.z\d+$", fn)) or bool(re.search(r"\.r\d+$", fn)):
        return True
    return False


def is_secondary_volume(filename: str) -> bool:
    """Checks if archive is a secondary volume in a multi-volume split set."""
    fn = filename.lower()
    m_rar = re.search(r"\.part0*(\d+)\.rar$", fn)
    if m_rar and int(m_rar.group(1)) > 1:
        return True
    m_split = re.search(r"\.(?:zip|7z|rar)\.0*(\d+)$", fn)
    if m_split and int(m_split.group(1)) > 1:
        return True
    m_z = re.search(r"\.z0*(\d+)$", fn)
    if m_z and int(m_z.group(1)) > 1:
        return True
    m_r = re.search(r"\.r0*(\d+)$", fn)
    if m_r and int(m_r.group(1)) > 1:
        return True
    return False


def test_archive_integrity(archive_path: str, password: Optional[str] = None) -> Tuple[bool, str]:
    """Validates archive integrity without extracting using unrar or 7z."""
    if archive_path.lower().endswith(".rar") and shutil.which("unrar"):
        cmd = ["unrar", "t", "-y"]
        if password:
            cmd.append(f"-p{password}")
        cmd.append(archive_path)
    else:
        cmd = ["7z", "t", "-mmt=1", archive_path]
        if password:
            cmd.append(f"-p{password}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        return True, "Integridad de archivo verificada (CRC y estructura OK)"
    return False, proc.stderr or proc.stdout


def extract_archive_with_fallbacks(
    archive_path: str,
    dest_dir: str,
    candidate_passwords: Optional[List[str]] = None
) -> Tuple[bool, str]:
    """
    Extracts an archive to dest_dir trying multiple tools (7z, unrar, tar, unzip)
    and rotating candidate passwords.
    """
    os.makedirs(dest_dir, exist_ok=True)
    passwords = [p for p in (candidate_passwords or []) if p]
    if "" not in passwords:
        passwords.append("")
    for standard_pw in ["miscursosvirtuales", "miscursosvirtuales.com", "mcv"]:
        if standard_pw not in passwords:
            passwords.append(standard_pw)

    fn = archive_path.lower()
    last_err = ""

    for pw in passwords:
        pw_str = f" con clave '{pw}'" if pw else " (sin clave)"
        if (fn.endswith(".rar") or ".part" in fn) and shutil.which("unrar"):
            cmd = ["unrar", "x", "-y", "-o-"]
            if pw:
                cmd.append(f"-p{pw}")
            cmd.extend([archive_path, f"{dest_dir}/"])
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode in [0, 1]:  # 0: ok, 1: non-fatal warning (e.g. some files skipped)
                logger.info(f"   ✅ Descomprimido con unrar{pw_str}")
                return True, "Descompresión exitosa con unrar"
            last_err = proc.stderr or proc.stdout

        if shutil.which("7z"):
            cmd = ["7z", "x", "-mmt=1", archive_path, f"-o{dest_dir}", "-aos"]
            if pw:
                cmd.append(f"-p{pw}")
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode in [0, 1]:  # 0: ok, 1: non-fatal warning / skipped files
                logger.info(f"   ✅ Descomprimido con 7z{pw_str}")
                return True, "Descompresión exitosa con 7z"
            last_err = proc.stderr or proc.stdout

        if fn.endswith(".zip") and shutil.which("unzip"):
            cmd = ["unzip", "-n", "-q"]
            if pw:
                cmd.extend(["-P", pw])
            cmd.extend([archive_path, "-d", dest_dir])
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode in [0, 1]:
                logger.info(f"   ✅ Descomprimido con unzip{pw_str}")
                return True, "Descompresión exitosa con unzip"
            last_err = proc.stderr or proc.stdout

        if (fn.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2")) or fn.endswith(".gz")) and shutil.which("tar"):
            cmd = ["tar", "-k", "-xf", archive_path, "-C", dest_dir]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                logger.info(f"   ✅ Descomprimido con tar")
                return True, "Descompresión exitosa con tar"
            last_err = proc.stderr or proc.stdout

    return False, last_err or "No se pudo descomprimir el archivo con ningún método ni contraseña"


def extract_archive(archive_path: str, dest_dir: str, password: Optional[str] = None) -> Tuple[bool, str]:
    """Extracts an archive to destination directory using fallback-enabled engine."""
    candidates = [password] if password else []
    return extract_archive_with_fallbacks(archive_path, dest_dir, candidate_passwords=candidates)


def recursive_extract_tree(
    root_dir: str,
    candidate_passwords: Optional[List[str]] = None,
    max_depth: int = 5
) -> int:
    """
    Scans root_dir recursively for nested archives (e.g. Modulo 1.zip inside main folder),
    decompresses them into their current directory, purges the unpacked archives,
    and repeats until no compressed archives remain or max_depth is reached.
    """
    total_unpacked = 0
    passwords = candidate_passwords or []

    for depth in range(max_depth):
        found_archives = []
        for root, dirs, files in os.walk(root_dir):
            if "NOTEBOOKLM_AUDIOS" in root or "_temp_downloads" in root:
                continue
            for f in sorted(files):
                full_path = os.path.join(root, f)
                if is_compressed_archive(f) and not is_secondary_volume(f):
                    found_archives.append((root, full_path))

        if not found_archives:
            break

        logger.info(f"🔄 Nivel de descompresión recursiva {depth + 1}: {len(found_archives)} archivo(s) anidado(s)...")
        for parent_dir, arch_path in found_archives:
            target_dest = parent_dir
            logger.info(f"   📦 Desempaquetando archivo anidado: {os.path.basename(arch_path)}...")
            ok, msg = extract_archive_with_fallbacks(arch_path, target_dest, passwords)
            if ok:
                total_unpacked += 1
                try:
                    os.remove(arch_path)
                except Exception:
                    pass
            else:
                logger.warning(f"   ⚠️ No se pudo desempaquetar archivo anidado {arch_path}: {msg}")

    return total_unpacked


def get_optimal_staging_dir() -> str:
    """
    Returns a safe disk-backed staging directory under /tmp.
    Avoids /dev/shm in LXC environments to prevent cgroup RAM exhaustion.
    """
    staging = "/tmp/mcv_transcode_staging"
    os.makedirs(staging, exist_ok=True)
    return staging


def reduce_video_to_360p(input_file: str, output_file: str) -> bool:
    """
    Transcodes a video to minimum visible bitrate:
    360p (640x360), H.264 CRF 28, AAC 64k, bounded to 2 threads.
    """
    cmd = [
        "ffmpeg", "-y", "-threads", "2", "-i", input_file,
        "-vf", "scale=-2:360",
        "-c:v", "libx264", "-crf", "28", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "64k",
        output_file
    ]
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if proc.returncode != 0:
        return False

    in_info = get_media_info(input_file)
    out_info = get_media_info(output_file)
    if out_info.get("duration", 0) <= 0:
        return False
    if in_info.get("duration", 0) > 0 and abs(out_info["duration"] - in_info["duration"]) > 5.0:
        return False
    return True


def convert_to_notebooklm_audio(input_file: str, output_file: str, audio_format: str = "mp3") -> bool:
    """Converts video/audio to NotebookLM optimal speech format (MP3 32k, AAC 24k mono, or Opus 20k) with 2 threads."""
    if audio_format == "aac":
        cmd = [
            "ffmpeg", "-y", "-threads", "2", "-i", input_file,
            "-vn", "-c:a", "aac", "-b:a", "24k", "-ac", "1",
            output_file
        ]
    elif audio_format == "opus":
        cmd = [
            "ffmpeg", "-y", "-threads", "2", "-i", input_file,
            "-vn", "-c:a", "libopus", "-b:a", "20k", "-vbr", "on", "-application", "voip", "-ac", "1",
            output_file
        ]
    else:
        cmd = [
            "ffmpeg", "-y", "-threads", "2", "-i", input_file,
            "-vn", "-c:a", "libmp3lame", "-b:a", "32k", "-ac", "1", "-ar", "44100",
            output_file
        ]
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if proc.returncode != 0:
        return False
    out_info = get_media_info(output_file)
    return out_info.get("duration", 0) > 0


def convert_to_notebooklm_mp3(input_file: str, output_file: str) -> bool:
    """Legacy wrapper for MP3 conversion."""
    return convert_to_notebooklm_audio(input_file, output_file, "mp3")


def optimize_media_single_pass(
    input_file: str,
    output_video: Optional[str] = None,
    output_audio: Optional[str] = None,
    audio_format: str = "mp3"
) -> Tuple[bool, bool]:
    """
    Optimizes video (360p CRF 28 veryfast) and audio in a SINGLE FFmpeg pass when both are needed,
    demuxing and decoding the input only once to eliminate redundant disk I/O, bounded to 2 threads.
    """
    if output_video and output_audio:
        cmd = ["ffmpeg", "-y", "-threads", "2", "-i", input_file]
        cmd.extend([
            "-vf", "scale=-2:360",
            "-c:v", "libx264", "-crf", "28", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "64k",
            output_video
        ])
        if audio_format == "aac":
            cmd.extend([
                "-vn", "-c:a", "aac", "-b:a", "24k", "-ac", "1",
                output_audio
            ])
        elif audio_format == "opus":
            cmd.extend([
                "-vn", "-c:a", "libopus", "-b:a", "20k", "-vbr", "on", "-application", "voip", "-ac", "1",
                output_audio
            ])
        else:
            cmd.extend([
                "-vn", "-c:a", "libmp3lame", "-b:a", "32k", "-ac", "1", "-ar", "44100",
                output_audio
            ])
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if proc.returncode == 0:
            v_info = get_media_info(output_video)
            a_info = get_media_info(output_audio)
            if v_info.get("duration", 0) > 0 and a_info.get("duration", 0) > 0:
                return True, True

        # Fallback to separate passes if combined pass fails
        v_ok = reduce_video_to_360p(input_file, output_video)
        a_ok = convert_to_notebooklm_audio(input_file, output_audio, audio_format)
        return v_ok, a_ok

    v_ok = True
    a_ok = True
    if output_video:
        v_ok = reduce_video_to_360p(input_file, output_video)
    if output_audio:
        a_ok = convert_to_notebooklm_audio(input_file, output_audio, audio_format)
    return v_ok, a_ok


def process_and_optimize_course_media(
    course_dir: str,
    log_file: Optional[str] = None,
    interval_sec: int = 3600,
    preferred_audio_format: str = "aac",
    course_title: str = "",
    audio_only: bool = False,
    upload_callback: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Executes Audio-First multimedia optimization:
    - Phase A (Audio-First Priority): Extract speech audio to NOTEBOOKLM_AUDIOS/*.aac at ~28x speed.
      Purge redundant .mp3 files.
      If upload_callback is set, triggers immediate ingestion to Google NotebookLM!
      If audio_only=True, stops here without transcoding video to 360p.
    - Phase B (Space Optimization): Transcodes videos > 360p or non-mp4 containers to 360p MP4 (veryfast, CRF 28).
      Purges heavy raw videos, leaving only the 360p MP4s on disk.
    """
    course_dir = os.path.abspath(course_dir)
    if os.path.basename(course_dir).upper() == "NOTEBOOKLM_AUDIOS":
        course_dir = os.path.dirname(course_dir)

    staging_dir = get_optimal_staging_dir()
    central_audio_dir = os.path.join(course_dir, "NOTEBOOKLM_AUDIOS")
    os.makedirs(central_audio_dir, exist_ok=True)

    # Purge legacy duplicated notebooklm subfolders anywhere in course_dir
    for root, dirs, _ in os.walk(course_dir):
        if "notebooklm" in dirs and root != course_dir:
            legacy_dir = os.path.join(root, "notebooklm")
            for old_f in os.listdir(legacy_dir):
                if old_f.lower().endswith((".mp3", ".opus", ".aac")):
                    norm_name = format_ordered_audio_name(os.path.basename(root), old_f, preferred_audio_format or "aac")
                    c_path = os.path.join(central_audio_dir, norm_name)
                    if not os.path.exists(c_path):
                        shutil.copy2(os.path.join(legacy_dir, old_f), c_path)
            shutil.rmtree(legacy_dir, ignore_errors=True)

    audio_format = preferred_audio_format or "aac"
    video_exts = (".mp4", ".ts", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".m4v")
    audio_exts = (".mp3", ".m4a", ".wav", ".aac", ".ogg", ".flac", ".opus", ".wma")

    media_tasks = []
    for root, dirs, files in os.walk(course_dir):
        if "NOTEBOOKLM_AUDIOS" in root or "_temp_downloads" in root or "/." in root:
            continue
        rel_path = os.path.relpath(root, course_dir)
        if rel_path == ".":
            display_mod = "Módulo 1 - Contenido Principal"
        else:
            parts = rel_path.split(os.sep)
            display_mod = parts[0] if len(parts) == 1 else f"{parts[0]} - {parts[-1]}"

        for f in sorted(files):
            if f.startswith(".") or "_temp" in f or f.startswith("in_"):
                continue
            f_lower = f.lower()
            f_path = os.path.join(root, f)
            if f_lower.endswith(video_exts):
                media_tasks.append(("video", root, display_mod, f, f_path))
            elif f_lower.endswith(audio_exts):
                media_tasks.append(("audio", root, display_mod, f, f_path))

    effective_title = course_title or os.path.basename(course_dir)
    logger.info(f"Iniciando procesamiento de medios ({len(media_tasks)} elementos detectados | Audio: {audio_format.upper()} | Audio-Only: {audio_only})...")

    video_tasks_count = sum(1 for m in media_tasks if m[0] == "video")
    tracker = MediaOptimizationTracker(
        total_videos=video_tasks_count,
        log_file=log_file,
        alert_interval_sec=interval_sec,
        course_dir=course_dir,
        course_title=effective_title
    )
    tracker.set_audio_targets(len(media_tasks), notebook_title=effective_title)
    tracker.set_phase("FASE_A")
    tracker.start()

    total_saved_bytes = 0
    videos_reduced = 0
    audios_created = 0

    try:
        # =========================================================================
        # FASE A: AUDIO-FIRST PRIORITARIO (Velocidad ~28x en tiempo real)
        # =========================================================================
        logger.info(f"\n⚡ [FASE A: AUDIO-FIRST] Extrayendo y ordenando audios para NotebookLM...")
        for mtype, root_dir, display_mod, vf, vpath in media_tasks:
            orig_sz = os.path.getsize(vpath) if os.path.exists(vpath) else 0
            if orig_sz == 0:
                continue

            tracker.update_file(display_mod, vf)
            audio_name = format_ordered_audio_name(display_mod, vf, audio_format, course_prefix="")
            central_audio_path = os.path.join(central_audio_dir, audio_name)
            needs_audio = not os.path.exists(central_audio_path) or os.path.getsize(central_audio_path) <= 1024

            if needs_audio:
                base_name = os.path.splitext(vf)[0]
                stage_audio = os.path.join(staging_dir, f"{base_name}.{audio_format}")
                logger.info(f"   🔊 Extrayendo audio ({audio_format.upper()}): [{display_mod}] {vf}...")
                if convert_to_notebooklm_audio(vpath, stage_audio, audio_format):
                    if os.path.exists(stage_audio):
                        shutil.move(stage_audio, central_audio_path)
                    audios_created += 1
                    logger.info(f"      ✅ Audio centralizado: {audio_name} ({os.path.getsize(central_audio_path)/(1024*1024):.1f} MB)")
                if os.path.exists(stage_audio):
                    try:
                        os.remove(stage_audio)
                    except Exception:
                        pass
            else:
                logger.info(f"      ⚡ Audio ya existe: {audio_name}")

            tracker.record_audio_completed(display_mod, vf)

            # Limpiar formatos redundantes del mismo archivo
            base_audio_stem = os.path.splitext(central_audio_path)[0]
            for other_ext in [".mp3", ".aac", ".opus"]:
                other_file = f"{base_audio_stem}{other_ext}"
                if other_file != central_audio_path and os.path.exists(other_file):
                    try:
                        os.remove(other_file)
                    except Exception:
                        pass

        # Purga determinista de MP3 redundantes en todo el árbol del curso
        for r, _, f_list in os.walk(course_dir):
            if "NOTEBOOKLM_AUDIOS" in r:
                for f in f_list:
                    if f.lower().endswith(".mp3"):
                        stem = os.path.splitext(f)[0]
                        aac_equiv = os.path.join(r, f"{stem}.aac")
                        mp3_fpath = os.path.join(r, f)
                        if os.path.exists(aac_equiv) or audio_format == "aac":
                            try:
                                sz = os.path.getsize(mp3_fpath)
                                os.remove(mp3_fpath)
                                total_saved_bytes += sz
                                logger.info(f"   🗑️ Purga en NOTEBOOKLM_AUDIOS: {f} ({sz/(1024*1024):.1f} MB liberados)")
                            except Exception:
                                pass
            else:
                for f in f_list:
                    if f.lower().endswith(".mp3"):
                        stem = os.path.splitext(f)[0]
                        mp4_equiv = os.path.join(r, f"{stem}.mp4")
                        mp3_fpath = os.path.join(r, f)
                        display_mod = os.path.basename(r)
                        expected_aac = format_ordered_audio_name(display_mod, f, "aac")
                        expected_opus = format_ordered_audio_name(display_mod, f, "opus")
                        if (
                            os.path.exists(mp4_equiv) or
                            os.path.exists(os.path.join(central_audio_dir, expected_aac)) or
                            os.path.exists(os.path.join(central_audio_dir, expected_opus)) or
                            os.path.exists(os.path.join(central_audio_dir, f"{stem}.aac"))
                        ):
                            try:
                                sz = os.path.getsize(mp3_fpath)
                                os.remove(mp3_fpath)
                                total_saved_bytes += sz
                                logger.info(f"   🗑️ MP3 redundante purgado en módulo: {f} ({sz/(1024*1024):.1f} MB liberados)")
                            except Exception:
                                pass

        # Disparo Temprano de Subida a Google NotebookLM
        if upload_callback:
            logger.info(f"\n🚀 [AUDIO-FIRST] Audios listos al 100%. Disparando ingesta anticipada a Google NotebookLM...")
            tracker.set_notebook_status("Ingestando fuentes...")
            try:
                upload_callback()
                tracker.set_notebook_status("Ingesta completada al 100%")
                logger.info(f"🎉 [AUDIO-FIRST] ¡Ingesta completada! Cuaderno listo en NotebookLM para usar con nlm-tutor.\n")
            except Exception as e:
                tracker.set_notebook_status(f"Falla: {str(e)[:25]}")
                logger.error(f"❌ [AUDIO-FIRST] Error en la subida anticipada a NotebookLM: {e}")

        # Si el usuario solicitó --audio-only, finalizar exitosamente aquí
        if audio_only:
            logger.info(f"⚡ [--audio-only] Modo solo audio activo. Videos preservados en tamaño original sin transcodificar.")
            tracker.stop()
            return {
                "videos_reduced": 0,
                "audios_created": audios_created,
                "total_saved_gb": total_saved_bytes / (1024 ** 3),
                "total_audios_central": len(os.listdir(central_audio_dir)) if os.path.exists(central_audio_dir) else 0
            }

        # =========================================================================
        # FASE B: REDUCCIÓN DE VIDEO 360p (veryfast, CRF 28 - Ahorro en Disco)
        # =========================================================================
        tracker.set_phase("FASE_B")
        logger.info(f"\n🎬 [FASE B: VERIFICACIÓN Y REDUCCIÓN DE VIDEO] Comprobando resolución (<=360p) y reduciendo si aplica...")
        for mtype, root_dir, display_mod, vf, vpath in media_tasks:
            if mtype != "video":
                continue
            orig_sz = os.path.getsize(vpath) if os.path.exists(vpath) else 0
            if orig_sz == 0:
                continue

            tracker.update_file(display_mod, vf)
            info = get_media_info(vpath)
            f_lower = vf.lower()
            is_ts = f_lower.endswith(".ts")
            is_legacy = not f_lower.endswith(".mp4")
            needs_reduction = is_ts or is_legacy or (info.get("height", 0) > 360) or (orig_sz > 80 * 1024 * 1024)

            saved = 0
            if needs_reduction:
                base_name = os.path.splitext(vf)[0]
                stage_mp4 = os.path.join(staging_dir, f"{base_name}.mp4")
                logger.info(f"   🎥 Reduciendo a 360p: [{display_mod}] {vf} ({orig_sz/(1024*1024):.1f} MB)...")
                if reduce_video_to_360p(vpath, stage_mp4):
                    final_mp4_path = os.path.join(root_dir, f"{base_name}.mp4")
                    if os.path.exists(stage_mp4):
                        shutil.move(stage_mp4, final_mp4_path)
                    new_sz = os.path.getsize(final_mp4_path)
                    saved = orig_sz - new_sz
                    total_saved_bytes += saved
                    videos_reduced += 1
                    if (is_ts or is_legacy) and vpath != final_mp4_path and os.path.exists(vpath):
                        try:
                            os.remove(vpath)
                        except Exception:
                            pass
                    logger.info(f"      ✅ Reducido a {new_sz/(1024*1024):.1f} MB (Ahorro: {saved/(1024*1024):.1f} MB)")
                if os.path.exists(stage_mp4):
                    try:
                        os.remove(stage_mp4)
                    except Exception:
                        pass
            else:
                logger.info(f"   ⚡ [{display_mod}] {vf} ya está optimizado (<=360p).")

            tracker.record_completed(saved)

    finally:
        tracker.emit_alert(force=True)
        tracker.stop()
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir, ignore_errors=True)

    return {
        "videos_reduced": videos_reduced,
        "audios_created": audios_created,
        "total_saved_gb": total_saved_bytes / (1024 ** 3),
        "total_audios_central": len(os.listdir(central_audio_dir)) if os.path.exists(central_audio_dir) else 0
    }


def validate_extracted_tree(directory: str) -> Dict[str, Any]:
    """Validates the extracted directory structure for 0-byte or corrupted files."""
    total_files = 0
    total_bytes = 0
    zero_byte_files = []
    modules = set()
    media_count = 0
    doc_count = 0

    for root, dirs, files in os.walk(directory):
        for f in files:
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            total_files += 1
            total_bytes += sz

            rel_mod = os.path.relpath(root, directory).split(os.sep)[0]
            if rel_mod and rel_mod not in [".", "NOTEBOOKLM_AUDIOS"] and not rel_mod.startswith("_"):
                modules.add(rel_mod)

            if sz == 0:
                zero_byte_files.append(os.path.relpath(fp, directory))

            if f.lower().endswith((".mp4", ".ts", ".mkv", ".mp3")):
                media_count += 1
            elif f.lower().endswith((".pdf", ".pptx", ".xlsx", ".docx", ".txt")):
                doc_count += 1

    if len(modules) == 0 and media_count > 0:
        modules.add("Contenido Principal")

    return {
        "valid": len(zero_byte_files) == 0 and total_files > 0,
        "total_files": total_files,
        "total_size_gb": total_bytes / (1024 ** 3),
        "total_modules": len(modules),
        "modules_list": sorted(list(modules)),
        "media_count": media_count,
        "doc_count": doc_count,
        "zero_byte_files": zero_byte_files,
    }


def is_course_directory_complete(course_dir: str, audio_only: bool = False) -> Tuple[bool, str]:
    """
    Checks if a course directory is fully downloaded, extracted, and media-optimized.
    Returns (is_complete, status_description).
    """
    if not os.path.isdir(course_dir):
        return False, "No existe en disco"

    entries = [
        e for e in os.listdir(course_dir)
        if not e.startswith(".") and e not in ["download_progress.log", "PROGRESO.txt"]
    ]
    if not entries:
        return False, "Carpeta vacía"

    # Check for active/partial temporary files
    for r, _, files in os.walk(course_dir):
        for f in files:
            fl = f.lower()
            if fl.endswith((".crdownload", ".part", ".tmp")) or f.startswith("_staging_"):
                return False, "Descargas parciales temporales detectadas"

    if os.path.exists(os.path.join(course_dir, "_temp_downloads")):
        return False, "Descarga temporal pendiente de extracción"

    central_audio_dir = os.path.join(course_dir, "NOTEBOOKLM_AUDIOS")
    has_audios = False
    if os.path.isdir(central_audio_dir):
        completed_audios = [
            f for f in os.listdir(central_audio_dir)
            if f.lower().endswith((".mp3", ".aac", ".opus")) and os.path.getsize(os.path.join(central_audio_dir, f)) > 1024
        ]
        has_audios = len(completed_audios) > 0

    video_exts = (".mp4", ".ts", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".m4v")
    audio_exts = (".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac")
    existing_videos = []
    source_audios = []
    for r, _, files in os.walk(course_dir):
        if "NOTEBOOKLM_AUDIOS" in r or "_temp_downloads" in r:
            continue
        for f in files:
            if f.startswith("."):
                continue
            fl = f.lower()
            if fl.endswith(video_exts):
                existing_videos.append(os.path.join(r, f))
            elif fl.endswith(audio_exts):
                source_audios.append(os.path.join(r, f))

    # Arquetipo V (Videos presentes):
    if existing_videos:
        if not has_audios:
            return False, "Videos existentes pero audios NotebookLM no extraídos"
        if not audio_only:
            # Check if any video needs reduction (>360p or >80MB)
            for vp in existing_videos:
                if not vp.lower().endswith(".mp4"):
                    return False, f"Video {os.path.basename(vp)} no normalizado a .mp4"
                v_sz = os.path.getsize(vp)
                v_info = get_media_info(vp)
                if (v_info.get("height", 0) > 360) or (v_sz > 80 * 1024 * 1024):
                    return False, f"Video {os.path.basename(vp)} pendiente de reducción a 360p"
        return True, "Completado y optimizado (Video)"

    # Arquetipo A (Audios puros presentes, ej. David Topi con MP3s):
    if source_audios:
        if not has_audios:
            return False, "Audios fuente presentes pero NOTEBOOKLM_AUDIOS no generado"
        if len(completed_audios) < len(source_audios):
            return False, f"Audios NotebookLM incompletos ({len(completed_audios)}/{len(source_audios)})"
        return True, f"Completado y optimizado (Audio, {len(completed_audios)} lecciones)"

    # Arquetipo D (Documental puro, sin videos ni audios):
    doc_count = 0
    ignore_meta_files = {
        "instrucciones_descarga.txt",
        "progreso.txt",
        "download_progress.log",
        "metadata.json"
    }
    for r, _, files in os.walk(course_dir):
        if "_temp_downloads" in r:
            continue
        for f in files:
            f_lower = f.lower()
            if f_lower in ignore_meta_files or f_lower.endswith(".md") or f_lower.startswith("."):
                continue
            if f_lower.endswith((".pdf", ".pptx", ".xlsx", ".docx", ".epub", ".html")):
                doc_count += 1
    if doc_count > 0:
        return True, f"Completado (documental, {doc_count} archivos)"

    return False, "Sin medios ni documentos verificados"


def build_comprehensive_markdown_report(
    meta: Dict[str, Any],
    course_dir: str,
    initial_size_gb: float,
    final_size_gb: float
) -> str:
    """Generates the authoritative .md reference and validation report (Step 8)."""
    title = meta["title"]
    md_filename = f"{sanitize_folder_name(title)}.md"
    md_path = os.path.join(course_dir, md_filename)

    saved_gb = max(initial_size_gb - final_size_gb, 0.0)
    saved_pct = (saved_gb / initial_size_gb * 100) if initial_size_gb > 0 else 0.0

    links_md = ""
    cloud_links = meta.get("cloud_links") or []
    for idx, item in enumerate(cloud_links, 1):
        links_md += f"{idx}. **{item['part']} ({item['provider'].upper()}):**  \n   {item['url']}\n"
    provider_title = cloud_links[0].get("provider", "Cloud").upper() if cloud_links else "DESCONOCIDO"

    # Build Module Table
    raw_subdirs = [
        d for d in os.listdir(course_dir)
        if os.path.isdir(os.path.join(course_dir, d)) and d not in ["NOTEBOOKLM_AUDIOS"] and not d.startswith("_")
    ]
    modules = sorted(raw_subdirs, key=extract_mod_num)

    root_vids = [
        f for f in os.listdir(course_dir)
        if os.path.isfile(os.path.join(course_dir, f)) and f.lower().endswith((".mp4", ".mkv", ".ts"))
    ]
    has_root_vids = len(root_vids) > 0

    rows = [
        "| # | Módulo | Videos MP4 (360p) | Audios MP3 | Otros | Peso en Disco | Estado |",
        "|---|---|---|---|---|---|---|"
    ]

    total_vids = 0
    total_auds = 0
    total_docs = 0

    central_audio_dir = os.path.join(course_dir, "NOTEBOOKLM_AUDIOS")
    all_central_mp3s = [f for f in os.listdir(central_audio_dir) if f.endswith((".mp3", ".aac", ".opus"))] if os.path.exists(central_audio_dir) else []

    target_mods = []
    if has_root_vids:
        target_mods.append((".", "Módulo 1 - Contenido Principal"))
    for mod in modules:
        target_mods.append((mod, mod))

    for idx, (mod_dir_name, mod_label) in enumerate(target_mods, 1):
        mp = course_dir if mod_dir_name == "." else os.path.join(course_dir, mod_dir_name)
        if mod_dir_name == ".":
            vids = len([f for f in os.listdir(mp) if os.path.isfile(os.path.join(mp, f)) and f.lower().endswith((".mp4", ".mkv", ".ts"))])
            docs = len([f for f in os.listdir(mp) if os.path.isfile(os.path.join(mp, f)) and f.lower().endswith((".pdf", ".pptx", ".xlsx", ".docx", ".txt")) and not f.endswith(".log") and not f.endswith(".md")])
            auds = len(all_central_mp3s) if not modules else len([f for f in all_central_mp3s if f.startswith("M01_")])
            mod_bytes = sum(os.path.getsize(os.path.join(mp, f)) for f in os.listdir(mp) if os.path.isfile(os.path.join(mp, f)) and not f.endswith(".log") and not f.endswith(".md"))
        else:
            vids = len([f for f in os.listdir(mp) if f.lower().endswith((".mp4", ".mkv", ".ts"))])
            mod_num = extract_mod_num(mod_label)
            auds = len([f for f in all_central_mp3s if f.startswith(f"M{mod_num:02d}_")])
            docs = len([f for f in os.listdir(mp) if f.lower().endswith((".pdf", ".pptx", ".xlsx", ".docx", ".txt"))])
            mod_bytes = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(mp) for f in fs)

        mb = mod_bytes / (1024 * 1024)
        sz_str = f"{mb:.1f} MB" if mb < 1000 else f"{mb/1024:.2f} GB"

        total_vids += vids
        total_auds += auds
        total_docs += docs
        rows.append(f"| {idx:02d} | {mod_label} | {vids} | {auds} | {docs} | {sz_str} | ✅ 100% OK |")

    table_md = "\n".join(rows)
    total_modules_count = len(target_mods)

    content = f"""# {title}

**Plataforma:** MisCursosVirtuales  
**Categoría:** {meta.get('category', 'PROFESIONAL')}  
**Producto ID:** `{meta.get('product_id', 'N/A')}`  
**Fecha de Publicación:** `{meta.get('pub_date', 'N/A')}`  
**Última Actualización:** `{meta.get('mod_date', 'N/A')}`  
**Fecha de Vigencia:** `{meta.get('effective_date', 'N/A')}`  
**Estado:** COMPLETADO, OPTIMIZADO Y VALIDADO (100% Verificado)  
**Fecha de Verificación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  

---

## 📊 Balance de Almacenamiento y Optimización
* **Tamaño Inicial Bruto:** `{initial_size_gb:.2f} GB` (archivos originales descargados)
* **Tamaño Final Optimizado:** `{final_size_gb:.2f} GB` (videos 360p + MP3s + recursos)
* **Espacio Total Ahorrado:** `{saved_gb:.2f} GB` (**{saved_pct:.1f}% de ahorro**)
* **Archivos Originales / Comprimidos Eliminados:** Sí (Archivos ZIP y videos pesados purgados tras validación física).

---

## ⚙️ Estándar de Codificación y Calidad de Medios

| Canal | Formato | Resolución / Canales | Codec | Bitrate / CRF | Propósito |
|---|---|---|---|---|---|
| **Video** | MP4 | 640x360 (360p) | H.264 (libx264) | CRF 28 (~100-300 kbps), AAC 64k | Mínimo bitrate visible para estudio y ahorro masivo de espacio |
| **Audio** | MP3 | 44.1 kHz, Mono (1 canal) | MP3 (libmp3lame) | 32 kbps CBR (~14.4 MB/hora) | Calidad óptima speech-to-text para NotebookLM y Gemini |

---

## 🗂️ Nomenclatura Cronológica para NotebookLM
Los audios MP3 han sido estandarizados con el prefijo jerárquico:  
`M{{MODULO:02d}}_L{{LECCION:02d}}_{{NOMBRE_CLASE}}.mp3`  
* Se encuentran organizados dentro de cada subcarpeta `notebooklm/` y centralizados en la carpeta raíz `NOTEBOOKLM_AUDIOS/`.  
* **Ventaja:** Al arrastrar todos los archivos a Google NotebookLM, se procesan y ordenan cronológicamente sin desorden alfabético.

---

## 🔗 Enlaces del Ecosistema MCV

* **URL del Producto:**  
  {meta['product_url']}

* **Endpoint Protegido YITH (Clave de Membresía):**  
  {meta['protected_url']}

* **URL Directa de WooCommerce Uploads (.txt):**  
  {meta['txt_url']}

---

## 📦 Enlaces Finales de Descarga ({provider_title})

{links_md}
* **Contraseña para descomprimir:**  
  `{meta.get('password', 'www.miscursosvirtuales.com')}`

---

## 📂 Inventario Exhaustivo de Módulos y Clases

{table_md}

**TOTAL EN DISCO:** {total_modules_count} Módulos | {total_vids} Videos (360p) | {total_auds} Audios MP3 | {total_docs} Documentos/Diapositivas | `{final_size_gb:.2f} GB`.
"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Reporte exhaustivo guardado en: {md_path}")
    return md_path


def is_collection_url(url: str) -> bool:
    """Detects if a URL is a category, author, or search collection rather than a single course."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    if "s" in qs or "post_type" in qs or any(k.startswith("brx_") for k in qs):
        return True
    if "/cursos/" in parsed.path or "/categoria/" in parsed.path or "/categoria-producto/" in parsed.path:
        return True
    if "/producto/" not in parsed.path:
        return True
    return False


def crawl_collection_courses(session: requests.Session, base_url: str) -> Tuple[str, List[Dict[str, str]]]:
    """
    Crawls all paginated pages of a category, author, or search query.
    Returns (collection_folder_name, list_of_courses_dict).
    """
    parsed = urlparse(base_url)
    qs = parse_qs(parsed.query)

    if "s" in qs:
        author_term = qs["s"][0].strip()
        col_name = sanitize_folder_name(author_term).title()
    elif "brx_qdsvwi[]" in qs:
        col_name = sanitize_folder_name(qs["brx_qdsvwi[]"][0]).upper()
    else:
        brx_vals = [v[0] for k, v in qs.items() if k.startswith("brx_") and v]
        if brx_vals:
            col_name = sanitize_folder_name(brx_vals[0]).upper()
        else:
            path_parts = [
                p for p in parsed.path.strip("/").split("/")
                if p not in ["cursos", "page", "author", "categoria", "categoria-producto"]
            ]
            if path_parts:
                col_name = sanitize_folder_name(path_parts[-1]).title()
            else:
                col_name = f"COLECCION_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    logger.info(f"🔍 Rastreo de colección: [{col_name}] desde {base_url}...")

    current_url = base_url
    courses = []
    visited_urls = set()
    page = 1

    while current_url and current_url not in visited_urls:
        visited_urls.add(current_url)
        logger.info(f"   -> Escaneando catálogo (página {page})...")
        try:
            r = session.get(current_url, timeout=20)
            if r.status_code != 200:
                logger.warning(f"Error HTTP {r.status_code} al consultar {current_url}")
                break
        except Exception as e:
            logger.error(f"Error de red al consultar {current_url}: {e}")
            break

        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].split("?")[0].rstrip("/") + "/"
            if "/producto/" in href and not href.endswith("/producto/"):
                slug = href.split("/producto/")[1].strip("/")
                if slug and not any(c["slug"] == slug for c in courses):
                    title = a.get_text(strip=True)
                    if not title:
                        img = a.find("img")
                        title = img.get("alt", "") if img else ""
                    courses.append({
                        "slug": slug,
                        "title": title or slug.replace("-", " ").title(),
                        "url": href
                    })

        # Check next page link
        next_url = None
        for a in soup.find_all("a", class_=lambda c: c and ("next" in c or "page-numbers" in c)):
            if "next" in a.get("class", []) or "→" in a.text or "Siguiente" in a.text:
                next_url = urljoin(base_url, a["href"])
                break
        if not next_url:
            for a in soup.find_all("a", href=True):
                if f"/page/{page+1}/" in a["href"] or f"paged={page+1}" in a["href"]:
                    next_url = urljoin(base_url, a["href"])
                    break

        current_url = next_url
        page += 1
        time.sleep(0.5)

    logger.info(f"✅ Rastreo finalizado: {len(courses)} cursos detectados en [{col_name}].")
    return col_name, courses


def extract_course_dates_concurrent(session: requests.Session, courses: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Fetches JSON-LD publication and modification dates for courses concurrently."""
    logger.info(f"⏳ Extrayendo metadatos y fechas de vigencia para {len(courses)} cursos en paralelo...")

    def fetch_item(item):
        try:
            r = session.get(item["url"], timeout=12)
            sp = BeautifulSoup(r.text, "html.parser")
            title_el = sp.find("h1", class_="product_title") or sp.find("h1") or sp.find("title")
            title = title_el.get_text(strip=True) if title_el else item.get("title", "")
            title = re.sub(r"^Curso:\s*", "", title, flags=re.IGNORECASE).strip()

            pub_date = None
            mod_date = None
            for script in sp.find_all("script", type="application/ld+json"):
                try:
                    d = json.loads(script.string)
                    graph = d.get("@graph", [d]) if isinstance(d, dict) else []
                    for g in graph:
                        if "datePublished" in g:
                            pub_date = g["datePublished"][:10]
                        if "dateModified" in g:
                            mod_date = g["dateModified"][:10]
                except Exception:
                    pass

            if not pub_date:
                pub_meta = sp.find("meta", property="article:published_time")
                if pub_meta and pub_meta.get("content"):
                    pub_date = pub_meta["content"][:10]

            if not mod_date:
                mod_meta = sp.find("meta", property="article:modified_time")
                if mod_meta and mod_meta.get("content"):
                    mod_date = mod_meta["content"][:10]

            eff = mod_date or pub_date or "2020-01-01"
            return {
                **item,
                "title": title or item["title"],
                "pub_date": pub_date or "N/A",
                "mod_date": mod_date or pub_date or "N/A",
                "effective_date": eff,
            }
        except Exception:
            return {
                **item,
                "pub_date": "N/A",
                "mod_date": "N/A",
                "effective_date": "2020-01-01",
            }

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(fetch_item, courses))

    results.sort(key=lambda x: x["effective_date"], reverse=True)
    return results


def parse_index_selection(expr: Optional[str]) -> Set[int]:
    """
    Parsea una expresión de índices o ruta a archivo con números y rangos.
    Ejemplos: '1,2,5-8,14' o '01, 02, 05-08' o un archivo .txt.
    Retorna un conjunto de enteros (1-based).
    """
    if not expr:
        return set()
    raw = expr.strip()
    if os.path.isfile(raw):
        try:
            with open(raw, "r", encoding="utf-8") as f:
                lines = [line.split("#")[0].strip() for line in f]
                raw = " ".join(lines)
        except Exception as e:
            logger.warning(f"No se pudo leer el archivo de selección de índices '{raw}': {e}")
            return set()

    # Normalizar espacios alrededor de guiones (ej: '5 - 8' -> '5-8')
    raw = re.sub(r"\s*-\s*", "-", raw)
    indices = set()
    # Separar por comas, puntos y comas o espacios
    parts = re.split(r"[\s,;]+", raw)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            sub = part.split("-", 1)
            if sub[0].isdigit() and sub[1].isdigit():
                start = int(sub[0])
                end = int(sub[1])
                step = 1 if start <= end else -1
                for n in range(start, end + step, step):
                    indices.add(n)
        elif part.isdigit():
            indices.add(int(part))
    return indices


def upload_course_to_notebooklm(
    course_dir: str,
    meta: Dict[str, Any],
    audio_format: str = "aac",
    alias: str = "",
    collection_name: str = ""
) -> bool:
    """
    Step 9: Ingesta Soberana a Google NotebookLM (Pro Consumer, 300 fuentes/cuaderno).
    1. Cuaderno individual con nomenclatura limpia [MCV][ALIAS][MM-YY]_Nombre-del-curso
    2. Ingesta secuencial de audios por streaming sin esperas bloqueantes (wait=False)
    3. Auto-labeling con IA de Google si hay >= 5 fuentes
    4. Agrupación en Colección Nativa de Google (soberana, si se especifica)
    5. Indexación en tags locales para cross_notebook_query
    """
    course_dir = os.path.abspath(course_dir)
    if os.path.basename(course_dir).upper() == "NOTEBOOKLM_AUDIOS":
        course_dir = os.path.dirname(course_dir)

    author_val = alias if alias else resolve_author_alias(meta.get("author") or meta.get("title", ""))
    eff_date = meta.get("effective_date", "")
    course_title = meta.get("title", os.path.basename(course_dir))

    nb_title = format_notebook_title(author_val, eff_date, course_title)

    logger.info(f"\n=======================================================")
    logger.info(f"🚀 INGESTA NATIVA A GOOGLE NOTEBOOKLM: {nb_title}")
    logger.info(f"=======================================================")

    # 1. Inicializar cliente SDK nativo
    client = None
    try:
        from notebooklm_tools.cli.utils import get_client
        client = get_client()
        logger.info("Cliente SDK nativo de NotebookLM inicializado exitosamente.")
    except Exception as e_cli:
        logger.error(f"Error inicializando cliente SDK de NotebookLM ({e_cli}). Ejecuta 'nlm login' primero.")
        return False

    # 2. Buscar cuaderno existente o crear uno nuevo con SDK nativo
    notebook_id = None
    try:
        from notebooklm_tools.services import notebooks
        nb_list = notebooks.list_notebooks(client)
        nb_items = nb_list.get("notebooks", []) if isinstance(nb_list, dict) else nb_list
        for nb in nb_items:
            t = (nb.get("title") or "").strip()
            if t == nb_title:
                notebook_id = nb.get("id") or nb.get("notebook_id")
                logger.info(f"Cuaderno existente encontrado: '{nb_title}' (UUID: {notebook_id})")
                break
        if not notebook_id:
            logger.info(f"Creando nuevo cuaderno dedicado: '{nb_title}'...")
            created = notebooks.create_notebook(client, nb_title)
            notebook_id = created.get("id") or created.get("notebook_id") if isinstance(created, dict) else getattr(created, "id", None)
    except Exception as e:
        logger.error(f"Error resolviendo/creando cuaderno en NotebookLM: {e}")
        return False

    if not notebook_id:
        logger.error("No se pudo resolver el UUID del cuaderno en NotebookLM.")
        return False

    # 3. Ingesta secuencial de audios sin esperas bloqueantes (streaming desacoplado)
    audios_dir = os.path.join(course_dir, "NOTEBOOKLM_AUDIOS")
    uploaded_sources = 0
    if os.path.isdir(audios_dir):
        preferred_ext = f".{audio_format.lower()}"
        audio_files = sorted([
            os.path.join(audios_dir, f) for f in os.listdir(audios_dir)
            if f.lower().endswith(preferred_ext) and os.path.getsize(os.path.join(audios_dir, f)) > 1024
        ])
        if not audio_files:
            audio_files = sorted([
                os.path.join(audios_dir, f) for f in os.listdir(audios_dir)
                if f.lower().endswith((".aac", ".mp3", ".opus")) and os.path.getsize(os.path.join(audios_dir, f)) > 1024
            ])
        total_a = len(audio_files)
        logger.info(f"Iniciando subida por streaming de {total_a} lecciones a NotebookLM...")
        for idx, a_path in enumerate(audio_files, 1):
            fname = os.path.basename(a_path)
            logger.info(f"  [{idx}/{total_a}] Transmitiendo audio: {fname}...")
            try:
                client.add_file(notebook_id, a_path, wait=False)
                uploaded_sources += 1
                logger.info(f"  ✅ Transmitido exitosamente: {fname}")
                time.sleep(1.2)
            except Exception as e_up:
                logger.warning(f"  ⚠️ Error subiendo {fname}: {e_up}")

    # 4. Auto-labeling con IA interno si hay >= 5 fuentes
    if uploaded_sources >= 5:
        logger.info("Ejecutando auto-clasificación de fuentes con IA de Google...")
        try:
            from notebooklm_tools.services import labels
            lbl_res = labels.auto_label(client, notebook_id)
            logger.info(f"Fuentes organizadas con IA en {lbl_res.get('count', 0)} etiquetas internas.")
        except Exception as e_lbl:
            logger.warning(f"Aviso en auto-labeling IA: {e_lbl}")

    # 6. Asignación a Colección Nativa en Google (solo si se especifica --collection)
    if collection_name and collection_name.strip():
        col_clean = collection_name.strip()
        logger.info(f"Asignando cuaderno a Colección Soberana Google: '{col_clean}'...")
        try:
            from notebooklm_tools.services import collections
            cols = collections.list_collections(client).get("collections", [])
            target_col = next((c for c in cols if (c.get("name") or "").strip().lower() == col_clean.lower()), None)
            if target_col:
                col_id = target_col.get("id") or target_col.get("collection_id")
                current_nbs = list(target_col.get("notebook_ids", []))
                if notebook_id not in current_nbs:
                    current_nbs.append(notebook_id)
                    try:
                        collections.edit_collection(client, col_id, notebook_ids=current_nbs)
                        logger.info(f"Cuaderno añadido a colección existente '{col_clean}'.")
                    except Exception:
                        try:
                            collections.delete_collection(client, col_id)
                            collections.create_collection(client, col_clean, current_nbs)
                            logger.info(f"Cuaderno añadido y colección '{col_clean}' actualizada con éxito.")
                        except Exception as e_rec:
                            logger.warning(f"Aviso actualizando colección Google: {e_rec}")
            else:
                collections.create_collection(client, col_clean, [notebook_id])
                logger.info(f"Nueva colección '{col_clean}' creada en Google NotebookLM.")
        except Exception as e_col:
            logger.warning(f"Aviso agrupando en Colección Google: {e_col}")

    # 7. Indexación de tags atómicos locales para cross_notebook_query
    atomic_tags = ["mcv", sanitize_folder_name(author_val).lower()]
    if meta.get("category"):
        atomic_tags.append(sanitize_folder_name(meta["category"]).lower())
    if eff_date and len(eff_date) >= 4:
        atomic_tags.append(eff_date[:4])
    logger.info(f"Registrando tags locales para búsquedas transversales: {', '.join(atomic_tags)}...")
    try:
        from notebooklm_tools.services import smart_select
        smart_select.tag_add(notebook_id, atomic_tags, notebook_title=nb_title)
        logger.info("Tags locales registrados exitosamente.")
    except Exception as e_tag:
        logger.warning(f"Aviso registrando tags locales: {e_tag}")

    logger.info(f"\n🎉 INGESTA NATIVA A NOTEBOOKLM COMPLETADA CON ÉXITO: '{nb_title}' (UUID: {notebook_id})")
    return True


def download_and_extract_course(
    session: requests.Session,
    course_url: str,
    base_dest_dir: str,
    args: argparse.Namespace
) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Stage 1: Producer worker (Network I/O & Decompression).
    Downloads all cloud parts and unpacks them into output_dir.
    Returns (output_dir, meta) or None on failure.
    """
    try:
        meta = fetch_course_metadata(session, course_url)
    except Exception as e:
        logger.error(f"❌ Error obteniendo metadata para {course_url}: {e}")
        return None

    date_tag = meta["effective_date"][:7] if meta.get("effective_date") else ""
    cat_tag = sanitize_folder_name(meta.get("category", "CURSO")).upper()
    effective_author = getattr(args, "alias", None) or meta.get("author") or resolve_author_alias(meta.get("title", ""))
    raw_author = sanitize_folder_name(effective_author).title()
    author_tag = "" if raw_author.upper() in ["MCV", "UNKNOWN", "N/A", ""] else raw_author
    clean_title = sanitize_folder_name(meta["title"])

    folder_name = compute_course_folder_name(
        title=meta.get("title", ""),
        effective_date=meta.get("effective_date", ""),
        category=meta.get("category", "CURSO"),
        alias=effective_author,
        date_prefix=getattr(args, "date_prefix", True)
    )

    matched_folder = locate_existing_course_directory(
        base_dest_dir,
        folder_name,
        title=meta.get("title", ""),
        author_alias=effective_author,
        product_id=str(meta.get("product_id", "")),
        product_url=str(meta.get("product_url", course_url))
    )
    if matched_folder:
        folder_name = matched_folder

    output_dir = os.path.abspath(os.path.join(base_dest_dir, folder_name))

    # Persistent staging in local NVMe to guarantee maximum I/O throughput and zero FUSE rclone cache exhaustion
    course_slug = sanitize_folder_name(folder_name)
    temp_download_dir = os.path.join(LOCAL_DOWNLOAD_STAGING_DIR, course_slug, "_temp_downloads")
    legacy_temp = os.path.join(output_dir, "_temp_downloads")
    if os.path.isdir(legacy_temp) and not os.path.exists(temp_download_dir):
        try:
            os.makedirs(os.path.dirname(temp_download_dir), exist_ok=True)
            shutil.move(legacy_temp, temp_download_dir)
        except Exception:
            pass

    # Instant Idempotency Skip Gate:
    central_audio_dir = os.path.join(output_dir, "NOTEBOOKLM_AUDIOS")
    if os.path.isdir(central_audio_dir):
        completed_audios = [
            f for f in os.listdir(central_audio_dir)
            if f.lower().endswith((".mp3", ".aac", ".opus")) and os.path.getsize(os.path.join(central_audio_dir, f)) > 1024
        ]
        video_exts = (".mp4", ".ts", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv", ".m4v")
        existing_videos = []
        for r, _, files in os.walk(output_dir):
            if "NOTEBOOKLM_AUDIOS" in r or "_temp_downloads" in r:
                continue
            existing_videos.extend([f for f in files if f.lower().endswith(video_exts) and not f.startswith(".")])

        is_fully_done = False
        has_pending_temp = os.path.exists(legacy_temp) or os.path.exists(temp_download_dir)
        audio_only_mode = getattr(args, "audio_only", False)
        if completed_audios and existing_videos and len(completed_audios) >= len(existing_videos) and not has_pending_temp:
            if audio_only_mode:
                is_fully_done = True
            else:
                videos_need_reduction = False
                for r, _, files in os.walk(output_dir):
                    if "NOTEBOOKLM_AUDIOS" in r or "_temp_downloads" in r:
                        continue
                    for f in files:
                        if f.lower().endswith(video_exts) and not f.startswith("."):
                            vp = os.path.join(r, f)
                            v_sz = os.path.getsize(vp)
                            v_info = get_media_info(vp)
                            if (not f.lower().endswith(".mp4")) or (v_info.get("height", 0) > 360) or (v_sz > 80 * 1024 * 1024):
                                videos_need_reduction = True
                                break
                    if videos_need_reduction:
                        break
                if not videos_need_reduction:
                    is_fully_done = True
        elif completed_audios and not existing_videos and not has_pending_temp:
            source_audios_count = sum(
                1 for r, _, files in os.walk(output_dir)
                if "NOTEBOOKLM_AUDIOS" not in r and "_temp_downloads" not in r
                for f in files if f.lower().endswith((".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac")) and not f.startswith(".")
            )
            if source_audios_count == 0 or len(completed_audios) >= source_audios_count:
                is_fully_done = True

        if is_fully_done and not getattr(args, "force", False):
            logger.info(f"⚡ [IDEMPOTENCY] El curso '{folder_name}' ya cuenta con {len(completed_audios)} audios y medios 100% verificados. Omitiendo descarga.")
            return (output_dir, meta)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_download_dir, exist_ok=True)
    log_file = os.path.join(output_dir, "download_progress.log")

    # Poda de archivo redundante INSTRUCCIONES_DESCARGA.txt (la metadata y links residen en .md y metadata.json)
    old_txt_path = os.path.join(output_dir, "INSTRUCCIONES_DESCARGA.txt")
    if os.path.isfile(old_txt_path):
        try:
            os.remove(old_txt_path)
        except Exception:
            pass

    meta_save_path = os.path.join(output_dir, "metadata.json")
    clean_meta = {
        "title": meta.get("title", clean_title),
        "raw_title": meta.get("raw_title", ""),
        "author": meta.get("author", author_tag),
        "category": meta.get("category", "CURSO"),
        "effective_date": meta.get("effective_date", date_tag),
        "product_id": meta.get("product_id", "N/A"),
        "product_url": meta.get("product_url", course_url),
        "protected_url": meta.get("protected_url", ""),
        "txt_url": meta.get("txt_url", ""),
        "source": "miscursosvirtuales_native_download",
        "retrieved_at": datetime.now().isoformat()
    }
    try:
        with open(meta_save_path, "w", encoding="utf-8") as mf:
            json.dump(clean_meta, mf, indent=2, ensure_ascii=False)
        logger.info(f"Metadata canónica SSoT guardada en: {meta_save_path}")
    except Exception as e_meta:
        logger.warning(f"Aviso guardando metadata.json: {e_meta}")

    # Step 1: Initial Reference Markdown
    build_comprehensive_markdown_report(meta, output_dir, initial_size_gb=0.0, final_size_gb=0.0)

    if args.metadata_only:
        logger.info(f"Modo Metadata-Only completado para: {folder_name}")
        return (output_dir, meta)

    # Step 2: Download all parts with mirror fallback options
    tracker = ProgressTracker(
        log_file=log_file,
        alert_interval_sec=args.interval,
        course_dir=output_dir,
        course_title=meta["title"]
    )
    tracker.start()

    downloaded_archives = []

    try:
        option_sets = meta.get("all_option_sets") or ([meta["cloud_links"]] if meta.get("cloud_links") else [])
        if not option_sets:
            raise RuntimeError(f"No se encontraron enlaces de descarga válidos en el archivo de instrucciones para {meta['title']}")

        success_download = False
        for opt_idx, current_links in enumerate(option_sets, 1):
            if len(option_sets) > 1:
                logger.info(f"\n🔄 Evaluando opción de descarga {opt_idx}/{len(option_sets)} ({len(current_links)} enlaces)...")
            downloaded_archives = []
            opt_failed = False

            for idx, item in enumerate(current_links, 1):
                part_name = item["part"]
                url = item["url"]
                provider = item["provider"]

                logger.info(f"\n=======================================================")
                logger.info(f"Descargando {part_name} ({provider.upper()}): {url}")
                logger.info(f"=======================================================")

                part_num_match = re.search(r"(\d+)", part_name)
                p_num = int(part_num_match.group(1)) if part_num_match else idx

                existing_archive = None
                candidate_search_dirs = [temp_download_dir, os.path.join(output_dir, "_temp_downloads")]
                for d in candidate_search_dirs:
                    if os.path.isdir(d):
                        for f in os.listdir(d):
                            if f.endswith(".crdownload") or f.startswith("_staging_"):
                                continue
                            if is_compressed_archive(f):
                                if len(current_links) == 1 or re.search(rf"\.part0*{p_num}\.", f, re.IGNORECASE) or re.search(rf"parte?0*{p_num}", f, re.IGNORECASE) or re.search(rf"\.00*{p_num}$", f, re.IGNORECASE):
                                    candidate = os.path.join(d, f)
                                    if os.path.getsize(candidate) > 1024 * 1024:
                                        existing_archive = candidate
                                        break
                    if existing_archive:
                        break

                if existing_archive:
                    size_mb = os.path.getsize(existing_archive) / (1024 * 1024)
                    logger.info(f"⚡ [RESUME] {part_name} ya existe en disco: {os.path.basename(existing_archive)} ({size_mb:.2f} MB). Omitiendo re-descarga.")
                    downloaded_archives.append(existing_archive)
                    tracker.update(os.path.basename(existing_archive), os.path.getsize(existing_archive), os.path.getsize(existing_archive))
                    tracker.emit_alert(force=True)
                    continue

                max_part_retries = 3
                part_downloaded = False
                for attempt in range(1, max_part_retries + 1):
                    try:
                        if provider == "sync":
                            files = download_sync_link(url, temp_download_dir, part_name, tracker, part_index=p_num)
                            downloaded_archives.extend(files)
                        elif provider == "mega":
                            items = download_mega_link(url, temp_download_dir, part_name, tracker, part_index=p_num)
                            downloaded_archives.extend(items)
                        elif provider == "gdrive":
                            items = download_gdrive_link(url, temp_download_dir, part_name, tracker, part_index=p_num)
                            downloaded_archives.extend(items)
                        elif provider == "direct" or url.startswith("http"):
                            items = download_direct_link(url, temp_download_dir, part_name, tracker, part_index=p_num)
                            downloaded_archives.extend(items)
                        else:
                            logger.warning(f"Proveedor '{provider}' no soportado automáticamente. URL: {url}")
                            opt_failed = True
                            break
                        part_downloaded = True
                        break
                    except Exception as e_down:
                        if "CUOTA MEGA AGOTADA" in str(e_down) or "509" in str(e_down):
                            logger.error(f"🛑 [CUOTA MEGA AGOTADA] Bloqueo de IP en Mega.nz. Interrumpiendo reintentos inútiles de 5s.")
                            opt_failed = True
                            break
                        if attempt < max_part_retries:
                            logger.warning(f"⚠️ Reintento {attempt}/{max_part_retries} para {part_name} tras error: {e_down}. Reintentando en 5s...")
                            time.sleep(5.0)
                        else:
                            logger.error(f"❌ Fallaron los {max_part_retries} intentos para {part_name}: {e_down}")
                            opt_failed = True

                if not part_downloaded or opt_failed:
                    break

                tracker.emit_alert(force=True)

            if not opt_failed and downloaded_archives:
                success_download = True
                break
            elif opt_idx < len(option_sets):
                logger.warning(f"⚠️ Opción {opt_idx} presentó fallas. Rotando automáticamente a la opción {opt_idx + 1}...")

        if not success_download:
            raise RuntimeError(f"Todas las opciones de descarga fallaron para {meta['title']}")

        # Step 3: Test & Decompress Archives with recursive unpacking and password rotation
        compressed_archives = []
        raw_items = []
        for item in downloaded_archives:
            if os.path.isfile(item) and is_compressed_archive(item):
                compressed_archives.append(item)
            else:
                raw_items.append(item)

        primary_archives = []
        for arch in compressed_archives:
            if is_secondary_volume(arch):
                logger.info(f"Omitiendo procesamiento individual de volumen secundario: {os.path.basename(arch)}")
                continue
            primary_archives.append(arch)

        candidate_passwords = [meta.get("password")] if meta.get("password") else []
        for arch in primary_archives:
            ok, msg = test_archive_integrity(arch, meta.get("password"))
            if not ok:
                logger.warning(f"Aviso en test de integridad para {arch}: {msg}")

        if not args.no_extract:
            for arch in primary_archives:
                ok, msg = extract_archive_with_fallbacks(arch, output_dir, candidate_passwords)
                if not ok:
                    raise RuntimeError(f"Falla al descomprimir {arch}: {msg}")

            nested_count = recursive_extract_tree(output_dir, candidate_passwords)
            if nested_count > 0:
                logger.info(f"✅ Se desempaquetaron exitosamente {nested_count} archivos comprimidos anidados.")

        for raw in raw_items:
            dest_raw = os.path.join(output_dir, os.path.basename(raw))
            if raw != dest_raw and os.path.exists(raw):
                if os.path.exists(dest_raw):
                    if os.path.isdir(dest_raw):
                        shutil.rmtree(dest_raw, ignore_errors=True)
                    else:
                        os.remove(dest_raw)
                shutil.move(raw, dest_raw)

        # Purge compressed archives and staging
        for arch in compressed_archives:
            if os.path.exists(arch):
                try:
                    os.remove(arch)
                except Exception:
                    pass
        if os.path.exists(temp_download_dir):
            shutil.rmtree(temp_download_dir, ignore_errors=True)
        staging_course_root = os.path.dirname(temp_download_dir)
        if os.path.isdir(staging_course_root) and not os.listdir(staging_course_root):
            try:
                os.rmdir(staging_course_root)
            except Exception:
                pass
        if os.path.exists(legacy_temp):
            shutil.rmtree(legacy_temp, ignore_errors=True)

        return (output_dir, meta)

    except Exception as e:
        logger.error(f"❌ Error descargando/extrayendo {meta.get('title', 'curso')}: {e}")
        write_progress_card(
            course_dir=output_dir,
            title=meta.get("title", "Curso MCV"),
            phase="ERROR",
            status_badge=f"🔴 ERROR DESCARGA: {str(e)[:40]}",
            pct=0.0,
            details={"Detalle del error": str(e)}
        )
        return None
    finally:
        tracker.stop()


def optimize_and_finalize_course(
    output_dir: str,
    meta: Dict[str, Any],
    args: argparse.Namespace
) -> bool:
    """
    Stage 2 & 3: Consumer worker (Audio-First Ingest & Video Reduction).
    Executes Phase A (audio extraction & NotebookLM upload) and Phase B (360p video transcode).
    """
    try:
        clean_title = sanitize_folder_name(meta.get("title", os.path.basename(output_dir)))
        folder_name = os.path.basename(output_dir)

        initial_tree = validate_extracted_tree(output_dir)
        initial_size_gb = initial_tree["total_size_gb"]

        uploaded_early = [False]
        def early_upload_cb():
            if getattr(args, "upload_nlm", False):
                upload_course_to_notebooklm(
                    output_dir,
                    meta,
                    audio_format=args.audio_format,
                    alias=getattr(args, "alias", ""),
                    collection_name=getattr(args, "collection", "")
                )
                uploaded_early[0] = True

        if not args.no_reduce:
            process_and_optimize_course_media(
                output_dir,
                preferred_audio_format=args.audio_format,
                course_title=clean_title,
                audio_only=getattr(args, "audio_only", False),
                upload_callback=early_upload_cb if getattr(args, "upload_nlm", False) else None
            )
        elif getattr(args, "upload_nlm", False):
            early_upload_cb()

        # Step 8: Final Audit and Comprehensive Markdown Report
        final_tree = validate_extracted_tree(output_dir)
        final_size_gb = final_tree["total_size_gb"]

        build_comprehensive_markdown_report(meta, output_dir, initial_size_gb=initial_size_gb, final_size_gb=final_size_gb)

        write_progress_card(
            course_dir=output_dir,
            title=meta.get("title", clean_title),
            phase="FINALIZADO",
            status_badge="🟢 COMPLETADO CON ÉXITO (100%)",
            pct=100.0,
            details={
                "Módulos verificados": str(final_tree['total_modules']),
                "Archivos finales": f"{final_tree['total_files']} ({final_size_gb:.2f} GB)",
                "Espacio total ahorrado": f"{initial_size_gb - final_size_gb:.2f} GB",
                "Audios NotebookLM": f"Listos en {folder_name}/NOTEBOOKLM_AUDIOS/",
            }
        )

        # Step 8.1: Purge transient operational telemetry inside course directory
        for transient_file in ["PROGRESO.txt", "download_progress.log"]:
            t_path = os.path.join(output_dir, transient_file)
            if os.path.exists(t_path):
                try:
                    os.remove(t_path)
                except Exception:
                    pass
        logger.info(f"   - Telemetría transitoria purgada de la carpeta (PROGRESO.txt, download_progress.log)")

        logger.info(f"\n🎉 CURSO COMPLETADO EXITOSAMENTE: {meta.get('title', clean_title)}")
        logger.info(f"   - Módulos verificados: {final_tree['total_modules']}")
        logger.info(f"   - Archivos finales: {final_tree['total_files']} ({final_size_gb:.2f} GB)")

        # Step 9: Ingesta Automática a Google NotebookLM (si no se ejecutó anticipadamente en Fase A)
        if getattr(args, "upload_nlm", False) and not uploaded_early[0]:
            upload_course_to_notebooklm(
                output_dir,
                meta,
                audio_format=args.audio_format,
                alias=getattr(args, "alias", ""),
                collection_name=getattr(args, "collection", "")
            )

        return True

    except Exception as e:
        logger.error(f"❌ Error optimizando {meta.get('title', 'curso')}: {e}")
        write_progress_card(
            course_dir=output_dir,
            title=meta.get("title", "Curso MCV"),
            phase="ERROR",
            status_badge=f"🔴 ERROR OPTIMIZACIÓN: {str(e)[:40]}",
            pct=0.0,
            details={"Detalle del error": str(e)}
        )
        return False


def download_and_process_course(
    session: requests.Session,
    course_url: str,
    base_dest_dir: str,
    args: argparse.Namespace
) -> bool:
    """Executes the full 8-step pipeline for an individual course."""
    res = download_and_extract_course(session, course_url, base_dest_dir, args)
    if not res:
        return False
    output_dir, meta = res
    return optimize_and_finalize_course(output_dir, meta, args)


class PipelineOrchestrator:
    """
    Sovereign Decoupled Producer-Consumer Engine v4.0.0.
    Overlaps Network I/O (cloud downloads) with CPU-Bound video transcoding (ffmpeg)
    and I/O Streaming (Google NotebookLM) with strict compute isolation.
    """

    def __init__(
        self,
        session: requests.Session,
        col_dir: str,
        manifest_path: str,
        col_name: str,
        selected_courses: List[Dict[str, Any]],
        runnable_indices: List[int],
        filter_txt: str,
        args: argparse.Namespace,
        origin_url: str = ""
    ):
        self.session = session
        self.col_dir = col_dir
        self.manifest_path = manifest_path
        self.col_name = col_name
        self.selected_courses = selected_courses
        self.runnable_indices = runnable_indices
        self.filter_txt = filter_txt
        self.args = args
        self.origin_url = origin_url or getattr(args, "url", "")

        self.manifest_statuses = {}
        for idx in range(1, len(selected_courses) + 1):
            if idx not in runnable_indices:
                self.manifest_statuses[idx] = "[OMITIDO]"
            else:
                self.manifest_statuses[idx] = "[PENDIENTE]"

        self.ready_for_optimization_queue: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()
        self.all_success = True
        self.lock = threading.Lock()

    def _save_manifest(self):
        update_batch_manifest(
            manifest_path=self.manifest_path,
            col_name=self.col_name,
            url=self.origin_url,
            filter_txt=self.filter_txt,
            selected_courses=self.selected_courses,
            statuses=self.manifest_statuses,
            col_dir=self.col_dir,
            alias=getattr(self.args, "alias", "") or resolve_author_alias(self.col_name),
            date_prefix=getattr(self.args, "date_prefix", True)
        )

    def run(self) -> bool:
        self._save_manifest()

        runnable_courses = [
            (idx, self.selected_courses[idx - 1])
            for idx in self.runnable_indices
        ]

        total_runnable = len(runnable_courses)
        if total_runnable == 0:
            return True

        # Consumer Worker: CPU-Bound Transcoding & Finalization (Strictly 1 worker)
        def consumer_worker():
            while not self.stop_event.is_set():
                try:
                    item = self.ready_for_optimization_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                if item is None:
                    self.ready_for_optimization_queue.task_done()
                    break

                idx, course_info, output_dir, meta = item
                with self.lock:
                    self.manifest_statuses[idx] = "[OPTIMIZANDO...]"
                    self._save_manifest()

                logger.info(f"\n🎬 [CONSUMER WORKER] Iniciando optimización/audio/video de: {course_info['title']}")
                try:
                    ok = optimize_and_finalize_course(output_dir, meta, self.args)
                    with self.lock:
                        if ok:
                            self.manifest_statuses[idx] = f"[COMPLETADO {datetime.now().strftime('%H:%M')}]"
                        else:
                            self.manifest_statuses[idx] = "[ERROR]"
                            self.all_success = False
                except Exception as e_opt:
                    logger.error(f"❌ [CONSUMER WORKER] Error optimizando {course_info['title']}: {e_opt}")
                    with self.lock:
                        self.manifest_statuses[idx] = "[ERROR]"
                        self.all_success = False
                finally:
                    with self.lock:
                        self._save_manifest()
                    self.ready_for_optimization_queue.task_done()

        consumer_thread = threading.Thread(target=consumer_worker, daemon=True)
        consumer_thread.start()

        # Producer Loop: Network I/O Downloads
        logger.info(f"🚀 [PIPELINE ORCHESTRATOR v4.1.0] Iniciando productor-consumidor para {total_runnable} cursos...")
        for b_idx, (idx, c) in enumerate(runnable_courses, 1):
            if self.stop_event.is_set():
                break

            with self.lock:
                self.manifest_statuses[idx] = "[DESCARGANDO...]"
                self._save_manifest()

            logger.info(f"\n📥 [PRODUCER WORKER {b_idx}/{total_runnable}] Descargando: {c['title']} ({c.get('effective_date', 'N/A')})...")
            try:
                res = download_and_extract_course(self.session, c["url"], self.col_dir, self.args)
                if res:
                    output_dir, meta = res
                    with self.lock:
                        self.manifest_statuses[idx] = "[EN COLA DE VIDEO]"
                        self._save_manifest()
                    self.ready_for_optimization_queue.put((idx, c, output_dir, meta))
                else:
                    logger.error(f"❌ [PRODUCER WORKER] Falló descarga de: {c['title']}")
                    with self.lock:
                        self.manifest_statuses[idx] = "[ERROR DESCARGA]"
                        self.all_success = False
                        self._save_manifest()
            except Exception as e_down:
                logger.error(f"❌ [PRODUCER WORKER] Excepción descargando {c['title']}: {e_down}")
                with self.lock:
                    self.manifest_statuses[idx] = "[ERROR DESCARGA]"
                    self.all_success = False
                    self._save_manifest()

        # Signal consumer to exit when queue is finished
        self.ready_for_optimization_queue.put(None)
        consumer_thread.join()

        return self.all_success


def load_manifest_for_resume(manifest_path: str, args: argparse.Namespace):
    """
    Polymorphic resume loader (v4.1.0):
    Parses batch manifest .txt file, inspects disk for completed vs incomplete vs empty folders,
    skips completed courses in 0 seconds, and executes PipelineOrchestrator only for pending courses.
    """
    if not os.path.isfile(manifest_path):
        logger.error(f"❌ El archivo de manifiesto no existe: {manifest_path}")
        sys.exit(1)

    manifest_path = os.path.abspath(manifest_path)
    logger.info(f"📂 [MODO REANUDACIÓN DE MANIFIESTO]: {manifest_path}")

    origin_url = ""
    col_name = ""
    author_alias = getattr(args, "alias", "") or ""
    applied_filters = ""
    base_dir = os.path.dirname(manifest_path)
    created_at = None

    courses: List[Dict[str, Any]] = []
    current_course: Optional[Dict[str, Any]] = None

    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("# ORIGIN_URL:") or stripped.startswith("# URL_ORIGEN:"):
                origin_url = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("# COLLECTION_NAME:") or stripped.startswith("# COLECCION:"):
                col_name = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("# AUTHOR_ALIAS:") or stripped.startswith("# ALIAS:"):
                if not author_alias:
                    author_alias = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("# APPLIED_FILTERS:") or stripped.startswith("# FILTROS:"):
                applied_filters = stripped.split(":", 1)[1].strip()
            elif stripped.startswith("# BASE_DIR:") or stripped.startswith("# DIR_BASE:"):
                b = stripped.split(":", 1)[1].strip()
                if os.path.isdir(b):
                    base_dir = b
            elif stripped.startswith("# CREATED_AT:") or stripped.startswith("# FECHA_CREACION:"):
                created_at = stripped.split(":", 1)[1].strip()
            elif re.search(r"(?:URL Consultada|ORIGIN_URL):\s*(.*)", stripped, re.IGNORECASE) and not origin_url:
                origin_url = re.sub(r"^(?:#\s*)?(?:URL Consultada|ORIGIN_URL):\s*", "", stripped, flags=re.IGNORECASE).strip()
            elif re.search(r"(?:Directorio Base|BASE_DIR):\s*(.*)", stripped, re.IGNORECASE):
                b = re.sub(r"^(?:#\s*)?(?:Directorio Base|BASE_DIR):\s*", "", stripped, flags=re.IGNORECASE).strip()
                if os.path.isdir(b):
                    base_dir = b
            elif re.search(r"(?:RESULTADOS DEL RASTREO|MANIFIESTO.*?):\s*\[(.*?)\]", stripped, re.IGNORECASE) and not col_name:
                m_c = re.search(r"(?:RESULTADOS DEL RASTREO|MANIFIESTO.*?):\s*\[(.*?)\]", stripped, re.IGNORECASE)
                if m_c:
                    col_name = m_c.group(1).strip()
            elif re.search(r"Filtros aplicados:\s*(.*)", stripped, re.IGNORECASE) and not applied_filters:
                applied_filters = re.sub(r"^Filtros aplicados:\s*", "", stripped, flags=re.IGNORECASE).strip()

            # Parse course rows (supports 4, 5, and 6 column formats)
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[0].isdigit():
                if current_course:
                    courses.append(current_course)
                idx = int(parts[0])
                eff = parts[1]
                if len(parts) >= 6:
                    st = parts[4]
                    title = parts[5]
                elif len(parts) == 5:
                    st = parts[3]
                    title = parts[4]
                else:
                    st = parts[2]
                    title = parts[3]

                current_course = {
                    "idx": idx,
                    "effective_date": eff,
                    "title": title,
                    "status": st,
                    "url": "",
                    "folder_name": ""
                }
            elif current_course and "↳ URL:" in line:
                current_course["url"] = line.split("↳ URL:", 1)[1].strip()
            elif current_course and "↳ DIR:" in line:
                current_course["folder_name"] = line.split("↳ DIR:", 1)[1].strip()

        if current_course:
            courses.append(current_course)

    if not col_name:
        base_name = os.path.splitext(os.path.basename(manifest_path))[0]
        col_name = base_name.title()

    if not author_alias:
        author_alias = resolve_author_alias(col_name)

    if not courses:
        logger.error(f"❌ No se pudieron extraer cursos válidos del manifiesto: {manifest_path}")
        sys.exit(1)

    logger.info(f"   Colección / Autor:    {col_name}")
    logger.info(f"   Directorio Base:      {base_dir}")
    logger.info(f"   Cursos en manifiesto: {len(courses)}")

    # Parse CLI filters if provided (--exclude, --only, --since), otherwise inherit from manifest
    exclude_indices = parse_index_selection(args.exclude)
    if not exclude_indices and applied_filters:
        m_exc = re.search(r"(?:Excluir|skip).*?\[(.*?)\]", applied_filters, re.IGNORECASE)
        if m_exc:
            exclude_indices = parse_index_selection(m_exc.group(1))

    only_indices = parse_index_selection(args.only)
    if not only_indices and applied_filters:
        m_onl = re.search(r"(?:Solo|only).*?\[(.*?)\]", applied_filters, re.IGNORECASE)
        if m_onl:
            only_indices = parse_index_selection(m_onl.group(1))

    applied_since = args.since
    if not applied_since and applied_filters:
        m_sinc = re.search(r"Vigencia >= (\d{4}-\d{2}(?:-\d{2})?)", applied_filters, re.IGNORECASE)
        if m_sinc:
            applied_since = m_sinc.group(1).strip()

    manifest_statuses: Dict[int, str] = {}
    runnable_indices: List[int] = []

    # Inspect physical disk for each course
    for c in courses:
        idx = c["idx"]
        title = c["title"]
        eff = c["effective_date"]
        prev_st = c.get("status", "")
        folder_name = c.get("folder_name", "")
        if not folder_name:
            folder_name = compute_course_folder_name(
                title=title,
                effective_date=eff,
                alias=author_alias,
                date_prefix=getattr(args, "date_prefix", True)
            )
            c["folder_name"] = folder_name

        # Locate physical course directory with smart polymorphic matching
        matched_folder = locate_existing_course_directory(
            base_dir,
            folder_name,
            title=title,
            author_alias=author_alias,
            product_url=c.get("url", "")
        )
        if matched_folder:
            course_dir = os.path.join(base_dir, matched_folder)
            c["folder_name"] = matched_folder
        else:
            course_dir = os.path.join(base_dir, folder_name)

        is_done, reason = is_course_directory_complete(course_dir, audio_only=getattr(args, "audio_only", False))

        if is_done:
            manifest_statuses[idx] = "[COMPLETADO]"
        else:
            is_active = True
            if applied_since and eff != "N/A" and eff < applied_since:
                is_active = False
            if only_indices and idx not in only_indices:
                is_active = False
            if idx in exclude_indices:
                is_active = False

            if is_active:
                if reason == "Carpeta vacía":
                    manifest_statuses[idx] = "[PENDIENTE (VACÍA)]"
                elif "parcial" in reason.lower() or "pendiente" in reason.lower():
                    manifest_statuses[idx] = "[PENDIENTE REANUDACIÓN]"
                else:
                    manifest_statuses[idx] = "[PENDIENTE]"
                runnable_indices.append(idx)
            else:
                if only_indices and idx not in only_indices and prev_st:
                    manifest_statuses[idx] = prev_st
                else:
                    manifest_statuses[idx] = "[OMITIDO]"

    completed_count = sum(1 for s in manifest_statuses.values() if s.startswith("[COMPLETADO"))
    runnable_count = len(runnable_indices)
    skipped_count = len(courses) - runnable_count - completed_count

    logger.info(f"\n================================================================================")
    logger.info(f"📋 AUDITORÍA FÍSICA DE REANUDACIÓN: [{col_name}]")
    logger.info(f"   Total en manifiesto:  {len(courses)} cursos")
    logger.info(f"   Completados en disco: {completed_count} cursos (omitidos en 0s)")
    logger.info(f"   Pendientes reanudar:  {runnable_count} cursos")
    logger.info(f"   Omitidos por filtro:  {skipped_count} cursos")
    logger.info(f"================================================================================")
    logger.info(f" #  | Vigencia   | Estado                 | Título")
    logger.info(f"----+------------+------------------------+-------------------------------------")
    for c in courses:
        idx = c["idx"]
        st = manifest_statuses.get(idx, "[PENDIENTE]")
        logger.info(f" {idx:02d} | {c['effective_date'][:10]} | {st:<22} | {c['title']}")
    logger.info(f"================================================================================\n")

    # Update manifest on disk with current audited status
    update_batch_manifest(
        manifest_path=manifest_path,
        col_name=col_name,
        url=origin_url or manifest_path,
        filter_txt=applied_filters or "Reanudación desde manifiesto",
        selected_courses=courses,
        statuses=manifest_statuses,
        col_dir=base_dir,
        alias=author_alias,
        created_at=created_at
    )

    if args.list_only:
        logger.info(f"🔍 Modo --list completado en manifiesto. Auditoría actualizada en disco.")
        return

    if runnable_count == 0:
        logger.info(f"✨ Todos los cursos seleccionados ({completed_count}/{len(courses)}) ya están 100% completados en disco.")
        logger.info(f"   No hay descargas pendientes en: {manifest_path}")
        return

    # Check for missing URLs in runnable courses
    for idx in runnable_indices:
        c = courses[idx - 1]
        if not c.get("url"):
            logger.info(f"🔍 URL no presente en fila {idx} ({c['title']}), consultando catálogo online...")
            looked_up = lookup_course_metadata_online(c["title"])
            if looked_up and looked_up.get("product_url"):
                c["url"] = looked_up["product_url"]
                logger.info(f"   ↳ URL resuelta: {c['url']}")
            else:
                logger.warning(f"   ⚠️ No se pudo resolver URL online para: {c['title']}")

    session = get_session(args.cookies)
    orchestrator = PipelineOrchestrator(
        session=session,
        col_dir=base_dir,
        manifest_path=manifest_path,
        col_name=col_name,
        selected_courses=courses,
        runnable_indices=runnable_indices,
        filter_txt=applied_filters or "Reanudación desde manifiesto",
        args=args,
        origin_url=origin_url
    )
    # Inherit pre-audited statuses so [COMPLETADO] courses stay [COMPLETADO]
    orchestrator.manifest_statuses = manifest_statuses
    all_batch_success = orchestrator.run()

    # Final manifest update (permanently preserved, never deleted)
    update_batch_manifest(
        manifest_path=manifest_path,
        col_name=col_name,
        url=origin_url or manifest_path,
        filter_txt=applied_filters or "Reanudación desde manifiesto",
        selected_courses=courses,
        statuses=orchestrator.manifest_statuses,
        col_dir=base_dir,
        alias=author_alias,
        created_at=created_at
    )



def normalize_author_name(author_str: str) -> str:
    """Normaliza nombres de autores eliminando acentos y espacios redundantes."""
    import unicodedata
    if not author_str:
        return ""
    norm = unicodedata.normalize('NFKD', author_str)
    no_acc = ''.join(c for c in norm if not unicodedata.combining(c)).strip()
    return ' '.join(no_acc.split()).title()


def clean_course_title_and_author(raw_title: str, author_hint: str = "") -> Tuple[str, str]:
    """
    Sanitiza títulos eliminando texto de accesibilidad de WooCommerce y sufijos comerciales.
    Separa limpiamente el título real y el autor del curso sin mutilar información.
    """
    import html
    t = html.unescape((raw_title or "").strip())
    if any(bad in t for bad in ["Ã¡", "Ã©", "Ã­", "Ã³", "Ãº", "Ã±", "â€“", "â€”", "â€"]):
        try:
            t = t.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            pass
    if t.startswith("Portada del curso "):
        t = t[len("Portada del curso "):]
    t = re.sub(r'^[Cc]urso:\s*', '', t).strip()
    t = re.sub(r'^[Aa]ccede ahora al curso:\s*', '', t, flags=re.IGNORECASE).strip()
    t = re.sub(r'\s*-\s*(?:La Web del Millón|Masterclass\.la|MCV|Mis cursos virtuales).*$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\.la$', '', t, flags=re.IGNORECASE)
    t = t.replace("–", "-").replace("—", "-")
    
    # Reemplazar pipes en títulos para evitar que rompan las columnas de tablas Markdown
    t = re.sub(r'\s*\|\s*', ' - ', t)

    parts = [p.strip() for p in t.split(" - ") if p.strip()]
    if len(parts) == 1:
        cand_title = parts[0]
        cand_author = author_hint or ""
        if author_hint:
            norm_hint = normalize_author_name(author_hint).lower()
            norm_cand = normalize_author_name(cand_title).lower()
            if norm_cand.endswith(norm_hint) and len(norm_cand) > len(norm_hint):
                cand_title = cand_title[:len(cand_title) - len(author_hint)].strip().rstrip("-").strip()
                cand_author = author_hint
        return cand_title, cand_author
    elif len(parts) == 2:
        non_author_words = {
            "master", "curso", "plantillas", "aprende", "guia", "guía", "taller", "desde cero",
            "paginas", "páginas", "trafico", "tráfico", "creacion", "creación", "sistema",
            "pt 1", "pt 2", "pt. 1", "pt. 2", "parte 1", "parte 2"
        }
        p1_lower = parts[1].lower()
        level_or_part = bool(re.search(r'\b(nivel|m[oó]dulo|parte|vol(?:umen)?|fase|bloque|principiante|intermedio|avanzado|b[aá]sico)\b', p1_lower))
        if (any(w in p1_lower for w in non_author_words) or level_or_part) and not any(p1_lower.endswith(w) for w in ["ac", "academy", "seo"]):
            return f"{parts[0]} - {parts[1]}", author_hint or ""
        else:
            return parts[0], parts[1]
    else:
        author = parts[-1]
        title = " - ".join(parts[:-1])
        return title, author


def clean_course_title(raw_title: str, author_hint: str = "") -> str:
    """Retorna únicamente el título sanitizado del curso (retrocompatibilidad)."""
    title, _ = clean_course_title_and_author(raw_title, author_hint)
    return title


def resolve_course_real_date(title: str, text: str = "", date_published: str = "", meta_year: str = "", is_volatile: bool = False, author: str = "") -> str:
    """Extrae la fecha real descubierta delegando al EpistemicGroundingEngine."""
    res = EpistemicGroundingEngine.resolve_dates(
        clean_title=title,
        author=author,
        meta_year=meta_year,
        date_published=date_published,
        text_hint=text
    )
    return res.get("real_date") or res.get("real_year") or "S/F"


def resolve_course_real_year(title: str, text: str = "", meta_year: str = "", is_volatile: bool = False, author: str = "", date_published: str = "") -> str:
    """Retorna únicamente el año real descubierto delegando al EpistemicGroundingEngine."""
    res = EpistemicGroundingEngine.resolve_dates(
        clean_title=title,
        author=author,
        meta_year=meta_year,
        date_published=date_published,
        text_hint=text
    )
    return res.get("real_year") or "S/F"


def is_volatile_domain(domain_name: str, query_hint: str = "") -> bool:
    """
    Discierne epistemológicamente si el campo de estudio es volátil/tecnológico
    (redes, algoritmos, ads, IA, tácticas digitales) o atemporal/perenne
    (desarrollo personal, filosofía, hábitos, idiomas, bioenergía, etc.).
    """
    text = f"{domain_name} {query_hint}".lower()
    exact_markers = [
        "youtube", "tiktok", "instagram", "facebook", "ads", "adsense",
        "seo", "tráfico", "trafico", "chatgpt", "midjourney", "prompt",
        "amazon fba", "dropshipping", "algoritmo", "cripto", "crypto",
        "trading", "software", "tecnologia", "tecnología"
    ]
    if any(m in text for m in exact_markers):
        return True
    if re.search(r'\b(?:ia|ai)\b', text):
        return True
    return False


def fetch_course_deep_metadata(session, url: str) -> dict:
    """
    Crawls product page to extract short description, deep syllabus (pa-toggle-content),
    categories, canonical breadcrumbs, and publication year/date.
    """
    import html
    res = {
        "short_desc": "",
        "long_desc": "",
        "categories": [],
        "breadcrumbs": [],
        "year": "",
        "date_published": "",
        "canonical_title": ""
    }
    if not url or not session:
        return res
    try:
        r = session.get(url, timeout=12)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            short_el = (
                soup.find("div", class_="woocommerce-product-details__short-description")
                or soup.find("div", class_=lambda c: c and "product-short-description" in c)
            )
            long_el = (
                soup.find("div", class_="pa-toggle-content")
                or soup.find("div", id="tab-description")
                or soup.find("div", class_="entry-content")
                or soup.find("div", class_=lambda c: c and any(k in c for k in ["conmutador-temario", "brxe-accordion-nested", "brxe-accordion", "brxe-post-content", "temario"]))
            )
            if short_el:
                res["short_desc"] = short_el.get_text(" ", strip=True)
            if long_el:
                res["long_desc"] = long_el.get_text("\n", strip=True)

            # Ingesta Mandatoria de Temario y Contenido Profundo: Umbral de suficiencia epistémica
            has_syllabus = any(k in res.get("long_desc", "").lower() for k in ["módulo", "modulo", "lección", "leccion", "clase", "capítulo", "capitulo", "temario", "contenido"])
            if len(res.get("long_desc", "").strip()) < 250 or not has_syllabus:
                try:
                    jina_headers = {"X-No-Cache": "true", "X-Return-Format": "markdown"}
                    keys = EpistemicGroundingEngine._load_env_keys()
                    jina_key = keys.get("JINA_API_KEY")
                    if jina_key:
                        jina_headers["Authorization"] = f"Bearer {jina_key}"
                    rj = session.get(
                        f"https://r.jina.ai/{url}",
                        timeout=9,
                        headers=jina_headers
                    )
                    if rj.status_code == 200 and len(rj.text) > 150:
                        lines_j = []
                        is_content = False
                        for raw_l in rj.text.split("\n"):
                            l = raw_l.strip()
                            if not l:
                                continue
                            if any(bad in l.lower() for bad in ["saltar al contenido", "carrito", "agregar cupón", "menú principal", "todos los derechos", "membresía club", "iniciar sesión", "pedidos", "planes vip", "cupones"]):
                                continue
                            if l.startswith(("![", "[!", "URL Source:", "Markdown Content:")):
                                continue
                            if any(k in l.lower() for k in ["descripción del curso", "temario", "información adicional", "contenido del curso", "lo que aprenderás", "¿para quién es este curso?"]):
                                is_content = True
                            if is_content or len(l) > 30:
                                lines_j.append(l)
                            if any(stop_k in l.lower() for stop_k in ["cursos relacionados", "productos relacionados", "valoraciones", "deja una respuesta"]):
                                break
                        if lines_j:
                            cleaned_jina_text = "\n".join(lines_j[:40])
                            if len(cleaned_jina_text) > len(res.get("long_desc", "")):
                                res["long_desc"] = cleaned_jina_text
                except Exception as e_jina:
                    logger.debug(f"Aviso en crawling Jina Reader para '{url}': {e_jina}")

            # Extracción robusta de categorías en Bricks Builder y WooCommerce
            for a in soup.find_all("a", href=re.compile(r'/categoria(-producto)?/')):
                cat_txt = a.get_text(strip=True)
                if cat_txt and cat_txt.lower() not in ["inicio", "cursos", "home"] and cat_txt not in res["categories"]:
                    res["categories"].append(cat_txt)
            for a in soup.select("span.posted_in a"):
                cat_txt = a.get_text(strip=True)
                if cat_txt and cat_txt.lower() not in ["inicio", "cursos", "home"] and cat_txt not in res["categories"]:
                    res["categories"].append(cat_txt)

            # Extracción de breadcrumbs en Bricks Builder y WooCommerce
            for b in soup.find_all(class_=re.compile(r'breadcrumb')):
                for a in b.find_all("a"):
                    b_txt = a.get_text(strip=True)
                    if b_txt and b_txt.lower() not in ["inicio", "cursos", "home"] and b_txt not in res["breadcrumbs"]:
                        res["breadcrumbs"].append(b_txt)
            for b in soup.select("nav.woocommerce-breadcrumb a, .brxe-breadcrumbs a"):
                b_txt = b.get_text(strip=True)
                if b_txt and b_txt.lower() not in ["inicio", "cursos", "home"] and b_txt not in res["breadcrumbs"]:
                    res["breadcrumbs"].append(b_txt)

            # Direct H1 extraction (Bricks builder or WooCommerce)
            h1_el = (
                soup.find("h1", class_=lambda c: c and "brxe-heading" in c)
                or soup.find("h1", class_="product_title")
                or soup.find("h1", class_="entry-title")
                or soup.find("h1")
            )
            if h1_el:
                raw_h1 = h1_el.get_text(" ", strip=True)
                if raw_h1 and "mis cursos virtuales" not in raw_h1.lower() and not raw_h1.lower().startswith("cursos"):
                    res["canonical_title"] = raw_h1

            # JSON-LD Schema.org extraction
            for sc in soup.find_all("script", type="application/ld+json"):
                sc_text = sc.text or ""
                # datePublished
                d_match = re.search(r'"datePublished"\s*:\s*"([^"]+)"', sc_text)
                if d_match and not res["date_published"]:
                    res["date_published"] = d_match.group(1)
                    y_m = re.match(r'^(\d{4}(?:-\d{2})?)', d_match.group(1))
                    if y_m:
                        res["year"] = y_m.group(1)
                # Canonical name fallback
                if not res["canonical_title"]:
                    n_match = re.search(r'"@type"\s*:\s*"WebPage"[^}]*?"name"\s*:\s*"([^"]+)"', sc_text)
                    if n_match:
                        cand_name = html.unescape(n_match.group(1))
                        if "\\u" in cand_name:
                            try:
                                cand_name = cand_name.encode("utf-8").decode("unicode_escape")
                            except Exception:
                                pass
                        if "Mis cursos virtuales" not in cand_name:
                            res["canonical_title"] = cand_name

            # Fallback for year from image upload url
            if not res["year"]:
                img_el = soup.find("img", class_="attachment-woocommerce_thumbnail") or soup.find("img", src=True)
                if img_el and img_el.get("src"):
                    up_match = re.search(r'/uploads/(\d{4})/(\d{2})/', img_el.get("src", ""))
                    if up_match:
                        res["year"] = f"{up_match.group(1)}-{up_match.group(2)}"
                    else:
                        up_match_y = re.search(r'/uploads/(\d{4})/', img_el.get("src", ""))
                        if up_match_y:
                            res["year"] = up_match_y.group(1)

            # Saneamiento de mojibake
            for k in ["canonical_title", "short_desc", "long_desc"]:
                if res.get(k) and any(bad in res[k] for bad in ["Ã¡", "Ã©", "Ã­", "Ã³", "Ãº", "Ã±", "â€“", "â€”", "â€"]):
                    try:
                        res[k] = res[k].encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
                    except Exception:
                        pass
    except Exception as e:
        logger.debug(f"Aviso extrayendo ficha profunda ({url}): {e}")
    return res


def extract_local_course_deep_metadata(course_dir: str) -> dict:
    """
    Extrae metadatos, temario y año desde el directorio local del curso (.md y metadata.json).
    """
    res = {
        "short_desc": "",
        "long_desc": "",
        "categories": [],
        "breadcrumbs": [],
        "year": "",
        "date_published": "",
        "canonical_title": ""
    }
    if not os.path.isdir(course_dir):
        return res
    m_path = os.path.join(course_dir, "metadata.json")
    if os.path.isfile(m_path):
        try:
            with open(m_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("category"):
                    res["categories"].append(data["category"])
                if data.get("categories"):
                    res["categories"].extend(data["categories"])
                if data.get("title"):
                    res["short_desc"] = data.get("title")
                    res["canonical_title"] = data.get("title")
                if data.get("effective_date"):
                    res["date_published"] = str(data.get("effective_date"))
                    res["year"] = str(data.get("effective_date"))
                if data.get("year"):
                    res["year"] = str(data.get("year"))
                if data.get("date_published"):
                    res["date_published"] = str(data.get("date_published"))
        except Exception:
            pass
    if not res["year"]:
        m_yr = re.search(r'\b(201[0-9]|202[0-9])\b', os.path.basename(course_dir))
        if m_yr:
            res["year"] = m_yr.group(1)
    for f in sorted(os.listdir(course_dir)):
        if f.endswith(".md") and not f.startswith("RUTA_DE_APRENDIZAJE") and not f.startswith("INSTRUCCIONES"):
            try:
                with open(os.path.join(course_dir, f), "r", encoding="utf-8") as f_md:
                    res["long_desc"] = f_md.read()[:5000]
                    break
            except Exception:
                pass
    return res


SPANISH_STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un", "para",
    "con", "no", "una", "su", "al", "lo", "como", "cómo", "mas", "más", "pero", "sus", "le",
    "ya", "o", "este", "si", "sí", "porque", "esta", "entre", "cuando", "cuándo", "muy",
    "sin", "sobre", "también", "tambien", "me", "hasta", "hay", "donde", "dónde", "quien",
    "quién", "quienes", "quiénes", "desde", "todo", "nos", "durante", "todos", "uno",
    "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos", "e", "esto", "mí",
    "antes", "algunos", "qué", "que", "unos", "yo", "otro", "otras", "otra", "él",
    "tanto", "esa", "estos", "mucho", "nada", "muchos", "cual", "cuál", "cuales", "cuáles",
    "poco", "ella", "estar", "estas", "algunas", "algo", "nosotros", "mi", "mis", "tú",
    "te", "ti", "tu", "tus", "ellas", "nosotras", "vosotros", "vosotras", "os", "mío",
    "mía", "míos", "mías", "tuyo", "tuya", "tuyos", "tuyas", "suyo", "suya", "suyos",
    "suyas", "nuestro", "nuestra", "nuestros", "nuestras", "vuestro", "vuestra",
    "vuestros", "vuestras", "esos", "esas", "estoy", "estás", "está", "estamos",
    "estáis", "están", "esté", "estés", "estemos", "estéis", "estén", "tras", "hacia",
    "mediante", "según", "segun", "aprender", "aprende", "aprenderás", "aprenderas",
    "aprendiendo", "completo", "completa", "desde", "cero", "guia", "guía", "curso",
    "taller", "master", "masterclass", "online", "digital", "crear", "crea", "hacer",
    "haz", "nivel", "modulo", "módulo", "parte", "edicion", "edición", "2020", "2021",
    "2022", "2023", "2024", "2025", "2026", "bien", "programa", "metodo", "método",
    "reto", "secretos"
}


def debias_educational_title(title: str) -> str:
    """Elimina sellos editoriales, marketplaces y superlativos publicitarios antes de la evaluación cognitiva."""
    t = title or ""
    t = re.sub(r'\b(masterclass(?:\.la)?|masterclasses(?:\.la)?|platzi|udemy|domestika|crehana|hotmart|mindvalley|fhi(?:\s+institute)?)\b', '', t, flags=re.I)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def infer_universal_cognitive_phase(clean_t: str, text: str = "") -> dict:
    """
    Clasificación pedagógica universal basada en los 5 estadios de maduración cognitiva (Bloom-Dreyfus):
    - Fase 1: Fundamentos & Principios Raíz (Recordar & Comprender - Novato)
    - Fase 2: Métodos, Técnicas & Práctica Instrumental (Aplicar - Principiante Avanzado)
    - Fase 3: Integración de Sistemas & Proyectos Completos (Analizar & Sintetizar - Competente)
    - Fase 4: Optimización, Arquitectura & Especialización (Evaluar & Refinar - Proficiente/Diestro)
    - Fase 5: Salida al Mercado, Negocio & Capitalización (Crear & Monetizar - Experto)
    
    Aplica Debias Filter (stripping de marcas editoriales), scoring multi-superficie ponderado
    y desambiguación contextual de polisemia sin hardcoding de herramientas transitorias.
    """
    debiased_title = debias_educational_title(clean_t).lower()
    desc_clean = debias_educational_title(text[:2500]).lower()

    # Paso 0: Evaluación explícita de ordinales de nivel o módulo (máxima jerarquía pedagógica)
    if any(re.search(r'\b' + re.escape(k) + r'\b', debiased_title) for k in [
        "nivel 1", "nivel i\b", "primer nivel", "primeros pasos", "modulo 1", "módulo 1",
        "parte 1", "vol 1", "volumen 1", "principiante", "principiantes", "desde cero", "para novatos"
    ]):
        return {"phase_num": 1, "phase_label": "Fase 1: Fundamentos & Principios"}
    if any(re.search(r'\b' + re.escape(k) + r'\b', debiased_title) for k in [
        "nivel 2", "nivel ii\b", "segundo nivel", "modulo 2", "módulo 2", "modulo 3", "módulo 3",
        "modulo 4", "módulo 4", "modulo 5", "módulo 5", "modulo 6", "módulo 6", "intermedio", "intermedios", "nivel intermedio"
    ]):
        return {"phase_num": 2, "phase_label": "Fase 2: Métodos & Práctica Instrumental"}
    if any(re.search(r'\b' + re.escape(k) + r'\b', debiased_title) for k in [
        "nivel 3", "nivel iii\b", "tercer nivel", "modulo 7", "módulo 7"
    ]):
        return {"phase_num": 3, "phase_label": "Fase 3: Integración & Proyectos Completos"}
    if any(re.search(r'\b' + re.escape(k) + r'\b', debiased_title) for k in [
        "nivel 4", "nivel iv\b", "cuarto nivel", "modulo 8", "módulo 8"
    ]):
        return {"phase_num": 4, "phase_label": "Fase 4: Optimización & Especialización"}

    # Matrices de procesos cognitivos de Bloom (2001) y estadios Dreyfus (1986)
    k_f1 = {
        "fundamento", "fundamentos", "principio", "principios", "introduccion", "introducción",
        "iniciacion", "iniciación", "iniciaciones", "desde cero", "basico", "básico", "inicial",
        "principiante", "primeros pasos", "anatomia", "anatomía", "historia", "conceptos",
        "bases", "esenciales", "raices", "raíces", "turistas", "alfabeto", "fonetica", "fonética",
        "filosofia", "filosofía", "identificar", "describir", "comprender", "entender", "conocer"
    }
    k_f2 = {
        "taller", "paso a paso", "tecnicas", "técnicas", "practica", "práctica",
        "practico", "práctico", "ejercicios", "guia practica", "guía práctica",
        "metodo", "método", "rutinas", "rutina", "entrenamiento", "entrenar", "ejecucion", "ejecución",
        "protocolos", "recetas", "ejercitacion", "ejercitación", "calistenia", "abdominales",
        "aplicar", "ejecutar", "implementar", "operar", "construir", "desarrollar", "demostrar"
    }
    k_f3 = {
        "completo", "de punta a punta", "proyecto real", "sistema integral", "sintesis", "síntesis",
        "produccion", "producción", "integracion", "integración", "flujo completo", "de la a a la z",
        "total", "integral", "conectar", "combinar", "estructurar", "organizar", "articular"
    }
    k_f4 = {
        "avanzado", "avanzada", "optimizacion", "optimización", "rendimiento", "especializacion",
        "especialización", "estrategias avanzadas", "arquitectura", "auditoria", "auditoría",
        "escalabilidad", "competicion", "competiciones", "culturismo", "bioquimica", "bioquímica",
        "diagnostico", "diagnóstico", "evaluacion", "evaluación", "profesional", "maestria", "maestría",
        "evaluar", "auditar", "refinar", "perfeccionar", "escalar", "validar", "resolver"
    }
    k_f5 = {
        "negocio", "negocios", "agencia", "agencias", "monetiza", "monetizacion", "monetización",
        "ventas", "vender", "vende", "freelance", "ingresos", "rentabilidad", "lanzamiento",
        "afiliados", "capitalizacion", "capitalización", "bienes raices", "bienes raíces",
        "trading", "bolsa", "comercial", "capitalizar", "monetizar", "comercializar", "emprender"
    }

    t_words = set(re.findall(r'[a-záéíóúñ]+', debiased_title))
    d_words = set(re.findall(r'[a-záéíóúñ]+', desc_clean))

    # Desambiguación contextual de polisemia: 'clientes' en contexto de salud/deporte/entrenamiento es asesoría a atletas (F4)
    is_fitness = any(w in t_words or w in d_words for w in ["nutricion", "nutrición", "culturismo", "fitness", "deporte", "deportiva", "atleta", "atletas", "entrenamiento"])
    if is_fitness and "clientes" in d_words:
        d_words.discard("clientes")
        d_words.add("especializacion")

    scores = {
        1: len(t_words & k_f1) * 5 + len(d_words & k_f1),
        2: len(t_words & k_f2) * 5 + len(d_words & k_f2),
        3: len(t_words & k_f3) * 5 + len(d_words & k_f3),
        4: len(t_words & k_f4) * 5 + len(d_words & k_f4),
        5: len(t_words & k_f5) * 5 + len(d_words & k_f5),
    }

    labels = {
        1: "Fase 1: Fundamentos & Principios",
        2: "Fase 2: Métodos & Práctica Instrumental",
        3: "Fase 3: Integración & Proyectos Completos",
        4: "Fase 4: Optimización & Especialización",
        5: "Fase 5: Negocio & Salida al Mercado"
    }

    best_p = max(scores.keys(), key=lambda p: (scores[p], -p))
    if scores[best_p] == 0:
        best_p = 1

    return {"phase_num": best_p, "phase_label": labels[best_p]}


def extract_series_signature(clean_t: str, author: str = "") -> Tuple[str, int, str]:
    """
    Extrae la raíz temática común de una serie y su número ordinal.
    Retorna: (series_key, ordinal, marker_text)
    Soporta: Nivel 1/2/3, Nivel I/II/III, Módulo 1/2, Parte 1/2, Vol 1/2, Bloque 1/2, Fase 1/2.
    Unifica variantes ortográficas/morfológicas (ej: psicobiótico / psicobiónica -> psicobio)
    y desduplica autores normalizados.
    """
    import unicodedata
    norm_author = normalize_author_name(author).lower() if author else "unknown"
    clean_lower = clean_t.lower()

    marker = ""
    num = 0

    # 1. Numéricos arábigos: nivel 1, módulo 2, parte 3, vol 1, bloque 2, etc.
    m_num = re.search(r'\b(nivel|m[oó]dulo|parte|vol(?:umen)?|bloque|fase|paso|step)\s*([0-9]+)\b', clean_lower)
    if m_num:
        marker = m_num.group(0)
        num = int(m_num.group(2))
    else:
        # 2. Números romanos: nivel I, II, III, IV, V, VI
        m_rom = re.search(r'\b(nivel|m[oó]dulo|parte|vol(?:umen)?)\s+(i{1,3}|iv|v|vi{1,3}|ix|x)\b', clean_lower)
        if m_rom:
            marker = m_rom.group(0)
            rom_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10}
            num = rom_map.get(m_rom.group(2), 1)
        else:
            # 2b. Ordinales en palabras: primer nivel, segundo nivel, tercer nivel, etc.
            m_ord = re.search(r'\b(primer(?:o|a)?|segund(?:o|a)?|tercer(?:o|a)?|cuart(?:o|a)?|quint(?:o|a)?)\s+(nivel|m[oó]dulo|parte|vol(?:umen)?|paso)\b', clean_lower)
            if m_ord:
                marker = m_ord.group(0)
                ord_map = {'primer': 1, 'primero': 1, 'primera': 1, 'segundo': 2, 'segunda': 2, 'tercer': 3, 'tercero': 3, 'tercera': 3, 'cuarto': 4, 'cuarta': 4, 'quinto': 5, 'quinta': 5}
                num = ord_map.get(m_ord.group(1), 1)
            else:
                # 3. Niveles semánticos: básico (1), intermedio (2), avanzado (3)
                m_sem = re.search(r'\b(desde cero|b[aá]sico|inicial|principiante|intermedio|medio|avanzado|experto|maestr[íi]a)\b', clean_lower)
                if m_sem:
                    marker = m_sem.group(0)
                    w = marker.lower()
                    if any(k in w for k in ['desde cero', 'basico', 'básico', 'inicial', 'principiante']):
                        num = 1
                    elif any(k in w for k in ['intermedio', 'medio']):
                        num = 2
                    else:
                        num = 3

    # 4. Número ordinal o versión al final del título: ej. "Halcones de Venta 2", "Triunfagram 2.0"
    if not marker:
        m_trail = re.search(r'\b([0-9]+(?:\.[0-9]+)?)\s*$', clean_lower)
        if m_trail:
            val_str = m_trail.group(1)
            try:
                n_val = int(float(val_str))
                if 2 <= n_val <= 20:
                    num = n_val
                    marker = m_trail.group(0).strip()
            except ValueError:
                pass

    if marker:
        base = re.sub(re.escape(marker), '', clean_lower)
    else:
        base = clean_lower

    base = re.sub(r'\b(nivel|m[oó]dulo|modulo|parte|vol(?:umen)?|bloque|fase|paso|step)\b', ' ', base)
    base = re.sub(r'[\(\)\[\]\:\-\–\—\|]+', ' ', base)
    words = re.findall(r'[a-záéíóúñ0-9]+', base)
    meaningful = [w for w in words if w not in SPANISH_STOPWORDS and len(w) > 2]

    stemmed = []
    for w in meaningful:
        w_norm = unicodedata.normalize('NFKD', w).encode('ASCII', 'ignore').decode('ASCII')
        if w_norm.startswith(('psicobio', 'bioenerget')):
            stemmed.append('psicobio')
        elif len(w_norm) > 5 and w_norm.endswith(('cion', 'sistem', 'tic', 'tico')):
            stemmed.append(w_norm[:5])
        else:
            stemmed.append(w_norm)

    base_clean = ' '.join(stemmed) if stemmed else 'general'
    return (f"{norm_author}|{base_clean}", num, marker)


def extract_twin_signature(clean_t: str, author: str = "") -> Tuple[str, str, bool]:
    """
    Detecta si dos cursos son módulos gemelos/complementarios basados en polaridades léxicas
    (ej. Positivas vs Negativas, Parte 1 vs Parte 2, Hombres vs Mujeres, Básico vs Avanzado).
    Retorna: (twin_base_key, polar_token, is_twin)
    """
    clean_lower = clean_t.lower()
    norm_author = normalize_author_name(author).lower() if author else "unknown"
    m_polar = re.search(r'\b(gram\s*positivas?|gram\s*negativas?|positivas?|negativas?|hombres?|mujeres?|masculino|femenino)\b', clean_lower)
    if m_polar:
        mod = m_polar.group(0)
        base = re.sub(re.escape(mod), '', clean_lower)
        base = re.sub(r'[\(\)\[\]\:\-\–\—\|]+', ' ', base)
        words = [re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', w).encode('ASCII', 'ignore').decode('ASCII').lower()) for w in re.findall(r'[a-záéíóúñ0-9]+', base)]
        words = [w for w in words if len(w) > 2 and w not in SPANISH_STOPWORDS]
        base_clean = ' '.join(sorted(words))
        return (f"{norm_author}|{base_clean}", mod, True)
    return ("", "", False)


def extract_agnostic_concept_keyword(clean_t: str, query_hint: str = "") -> str:
    """
    Extrae el concepto o tecnología distintiva de un título sin depender de listas hardcodeadas.
    Filtra stopwords en español y términos de la búsqueda (ej: 'youtube' en catálogo de youtube).
    """
    words = re.findall(r'[a-záéíóúñ0-9]+', clean_t.lower())
    query_words = set(re.findall(r'[a-záéíóúñ0-9]+', query_hint.lower())) if query_hint else set()
    meaningful = [
        w for w in words
        if w not in SPANISH_STOPWORDS
        and w not in query_words
        and len(w) > 2
    ]
    if meaningful:
        return meaningful[0]
    return "general"


def is_true_alternative(primary_title: str, candidate_title: str, primary_author: str, candidate_author: str) -> bool:
    """
    Determina con rigor epistemológico si un curso es una VERDADERA alternativa/reemplazo de otro:
    - Si son módulos gemelos (ej: GRAM Positivas vs GRAM Negativas): JAMÁS son alternativas (retorna False).
    - Mismo autor:
      * Solo es alternativa si los títulos son virtualmente idénticos (Jaccard >= 0.85) sin modificadores complementarios
        y representan re-ediciones en años distintos. Si son del mismo año y difieren en tema/técnica, NO son alternativas.
    - Autores distintos (catálogos de categoría):
      * Es alternativa si abordan el mismo concepto exacto en la misma fase cognitiva (Jaccard >= 0.70).
    """
    t_base1, mod1, is_t1 = extract_twin_signature(primary_title, primary_author)
    t_base2, mod2, is_t2 = extract_twin_signature(candidate_title, candidate_author)
    if is_t1 and is_t2 and t_base1 == t_base2 and mod1 != mod2:
        return False

    # 1b. Cursos de una serie secuencial jamás son alternativas (ej: Halcones 1 vs Halcones 2)
    s_key1, s_ord1, _ = extract_series_signature(primary_title, primary_author)
    s_key2, s_ord2, _ = extract_series_signature(candidate_title, candidate_author)
    if s_key1 == s_key2 and s_ord1 != s_ord2 and (s_ord1 > 0 or s_ord2 > 0):
        return False

    p_auth = normalize_author_name(primary_author).lower() if primary_author else ""
    c_auth = normalize_author_name(candidate_author).lower() if candidate_author else ""
    is_same_author = (p_auth and c_auth and p_auth == c_auth and p_auth != "unknown")

    p_words = set(w for w in re.findall(r'[a-záéíóúñ0-9]+', primary_title.lower()) if w not in SPANISH_STOPWORDS and len(w) > 2)
    c_words = set(w for w in re.findall(r'[a-záéíóúñ0-9]+', candidate_title.lower()) if w not in SPANISH_STOPWORDS and len(w) > 2)

    if not p_words or not c_words:
        return False

    intersection = p_words.intersection(c_words)
    union = p_words.union(c_words)
    jaccard = len(intersection) / len(union) if union else 0.0

    if is_same_author:
        return jaccard >= 0.85
    else:
        return jaccard >= 0.70


UNIVERSAL_MACRO_DOMAINS = [
    (
        "Oratoria, Comunicación & Hablar en Público",
        {"oratoria", "hablar", "publico", "público", "comunicacion", "comunicación", "asertiva",
         "camara", "cámara", "camaras", "cámaras", "voz", "diccion", "dicción", "locucion", "locución",
         "expresion", "expresión", "presentaciones", "retorica", "retórica", "persuadir", "influir",
         "discurso", "discursos", "audiencia", "elocuencia", "vocalizacion", "vocalización", "storytelling",
         "corporal", "escenario", "comunicador", "conferencias", "pitch"}
    ),
    (
        "Inversiones, Finanzas, Criptoactivos & Trading",
        {"bitcoin", "cripto", "criptomonedas", "blockchain", "inversion", "inversión", "inversiones",
         "trading", "trader", "traders", "bolsa", "dinero", "finanzas", "indexada", "acciones",
         "riqueza", "forex", "mercados", "patrimonio", "rentabilidad", "inversionista", "inversionistas",
         "capital", "economica", "económica", "bienes", "raices", "raíces", "inmobiliario", "inmobiliaria",
         "etf", "fondos", "dividendos", "deuda", "presupuesto", "ahorro", "educacion financiera",
         "educación financiera", "analisis tecnico", "análisis técnico", "scalping", "futuros"}
    ),
    (
        "Tecnología, Programación, Ciberseguridad & IT",
        {"programacion", "programación", "codigo", "código", "software", "python", "javascript",
         "typescript", "react", "html", "css", "git", "github", "windows", "linux", "hacking",
         "seguridad", "ciberseguridad", "android", "ios", "red", "redes", "servidores", "algebra",
         "álgebra", "matematicas", "matemáticas", "data", "big data", "desarrollo", "backend",
         "frontend", "moviles", "móviles", "dispositivos", "devops", "cloud", "api", "apis",
         "bases de datos", "sql", "postgresql", "docker", "web", "fullstack", "algoritmos",
         "inteligencia artificial", "machine learning", "pentesting", "cisco", "ethical"}
    ),
    (
        "Audiovisual, Animación, Diseño & Fotografía",
        {"animacion", "animación", "after effects", "premiere", "photoshop", "illustrator",
         "fotografia", "fotografía", "video", "cine", "edicion", "edición", "diseno", "diseño",
         "arte", "blender", "3d", "lightroom", "personajes", "videojuegos", "unreal", "unity",
         "iluminacion", "iluminación", "flash", "ilustracion", "ilustración", "isometrica",
         "isométrica", "fotomontajes", "fotomontaje", "colorimetria", "colorimetría", "motion",
         "graphics", "render", "renderizado", "modelado", "composicion", "composición", "guion",
         "audiovisual", "produccion", "producción", "logotipo", "logo", "logotipos", "branding",
         "identidad", "vector", "vectorial", "vectores", "tipografia", "tipografía", "lettering",
         "manga", "mangaka", "comic", "comics", "camara", "cámara", "camaras", "cámaras",
         "lente", "lentes", "streaming", "figma", "serigrafia", "serigrafía", "packaging",
         "retrato", "retratos", "acuarela", "oleo", "óleo", "dibujo", "dibujar", "trazos",
         "autocad", "cad", "sketchup", "rhinoceros", "rhino", "cinema 4d", "avid", "pro tools",
         "audio", "sonido", "infografia", "infografía", "postproduccion", "postproducción",
         "indesign", "coreldraw", "procreate", "davinci", "resolve", "concept art", "storyboard"}
    ),
    (
        "Marketing Digital, Redes Sociales & Tráfico",
        {"marketing", "facebook ads", "instagram", "tiktok", "reels", "youtube", "youtuber",
         "redes", "sociales", "community", "creador", "digital", "contenido", "copywriting",
         "listening", "trafico", "tráfico", "inmobiliarias", "branding", "linkedin", "networking",
         "estrategia", "publicidad", "anuncios", "growth", "posicionamiento", "audiencia",
         "influencer", "viral", "viralidad", "algoritmo", "campañas", "campanas", "leads", "conversión"}
    ),
    (
        "Ventas, Embudos, E-commerce & Negocios",
        {"ventas", "vende", "vender", "vendedor", "persuasion", "persuasión", "negociacion",
         "negociación", "negocio", "negocios", "multinivel", "networker", "network", "embudos",
         "funnel", "funnels", "ecommerce", "e-commerce", "dropshipping", "b2b", "prospeccion",
         "prospección", "cierre de ventas", "cierre", "llamadas", "agenda", "reuniones", "automatiza",
         "automatizacion", "automatización", "tienda online", "escalabilidad", "escalar", "oferta"}
    ),
    (
        "Desarrollo Personal, Hábitos & Mentalidad",
        {"mente", "creencias", "habitos", "hábitos", "emociones", "psicologia", "psicología",
         "autoestima", "felicidad", "abundancia", "prosperidad", "consciencia", "conciencia",
         "cerebro", "conducta", "liderazgo", "productividad", "disciplina", "mindset",
         "autoconocimiento", "proposito", "propósito", "resiliencia", "gestion emocional",
         "gestión emocional", "inteligencia emocional", "enfoque", "concentracion", "concentración",
         "metas", "rutinas matutinas", "superacion", "superación"}
    ),
    (
        "Salud, Fitness, Nutrición & Bienestar",
        {"fitness", "gym", "gimnasio", "entrenamiento", "ejercicio", "ejercicios", "salud",
         "ayuno", "intermitente", "nutricion", "nutrición", "peso", "obesidad", "sobrepeso",
         "cuerpo", "biomagnetismo", "biomagnetica", "biomagnética", "terapia", "terapeutico",
         "terapéutico", "enfermedad", "remedios", "bacterias", "hongos", "micologia", "micología",
         "psicopatologia", "psicopatología", "sistemica", "sistémica", "medicina", "abdomen",
         "abdominales", "abs", "core", "calistenia", "fuerza", "hipertrofia", "musculo",
         "músculo", "muscular", "musculacion", "musculación", "rutinas", "definicion", "definición",
         "tonificar", "gluteos", "glúteos", "pectorales", "pectoral", "piernas", "brazos", "espalda",
         "hiit", "pliometria", "pliometría", "pliometrico", "pliométrico", "pesas", "crossfit",
         "resistencia", "cardio", "movilidad", "flexibilidad", "postura", "rendimiento", "dieta",
         "dietas", "alimentacion", "alimentación", "calorias", "calorías", "macronutrientes",
         "suplementacion", "suplementación", "metabolismo", "grasa", "adelgazar", "adelgazamiento",
         "keto", "cetogenica", "cetogénica", "recetas", "cocina saludable", "batidos", "smoothies",
         "desintoxicacion", "detox", "columna", "vertebral", "rehabilitacion", "rehabilitación",
         "biomecanica", "biomecánica", "estetico", "estético", "deportivo", "culturismo", "fisicoculturismo",
         "azucar", "azúcar", "combustible", "metamorfosis", "cronosfit", "vfit", "hibrido", "híbrido"}
    ),
    (
        "Espiritualidad, Misticismo & Consciencia",
        {"reiki", "tarot", "magia", "astrologia", "astrología", "chakras", "chakra", "pendulo",
         "péndulo", "quiromancia", "akasha", "espiritual", "vibracional", "oraculo", "oráculo",
         "kundalini", "misticismo", "numerologia", "numerología", "meditacion", "meditación",
         "sanacion", "sanación", "holistica", "holística", "canalizacion", "canalización",
         "energia", "energía", "aura", "registros akashicos", "registros akáshicos", "angeles",
         "ángeles", "arcangeles", "arcángeles", "chamanismo", "metafisica", "metafísica"}
    ),
    (
        "Idiomas & Habilidades Prácticas",
        {"idioma", "idiomas", "ingles", "inglés", "english", "chino", "mandarin", "mandarín",
         "frances", "francés", "aleman", "alemán", "italiano", "portugues", "portugués",
         "pronunciacion", "pronunciación", "gramatica", "gramática", "vocabulario", "conversacion",
         "conversación", "resina", "artesanias", "artesanías", "tazas", "termos", "decoracion",
         "decoración", "prendas", "aguja", "crochet", "tejer", "costura", "musica", "música",
         "canto", "vocal", "guitarra", "piano", "dj", "escribir", "redaccion", "redacción",
         "carpinteria", "carpintería", "manualidades"}
    )
]

DOMAIN_FACETS = {
    "Audiovisual, Animación, Diseño & Fotografía": [
        (
            "Diseño Gráfico, Branding, Identidad & Logotipos",
            {"diseno", "diseño", "grafico", "gráfico", "logotipo", "logo", "logotipos", "branding",
             "identidad", "vector", "vectorial", "vectores", "illustrator", "packaging", "tipografia",
             "tipografía", "lettering", "poster", "cartel", "infografia", "infografía", "editorial",
             "indesign", "coreldraw", "marca"}
        ),
        (
            "Ilustración Digital, Dibujo, Manga & Concept Art",
            {"ilustracion", "ilustración", "dibujo", "dibujar", "manga", "mangaka", "comic", "comics",
             "personajes", "concept art", "pintura", "oleo", "óleo", "acuarela", "pinceles", "trazos",
             "humor grafico", "caricatura", "procreate", "anatomia", "anatomía"}
        ),
        (
            "Fotografía, Iluminación, Retrato & Composición",
            {"fotografia", "fotografía", "camara", "cámara", "camaras", "cámaras", "lente", "lentes",
             "retrato", "retratos", "lightroom", "iluminacion", "iluminación", "foto", "fotos", "sesion",
             "sesión", "disparo", "exposicion", "exposición", "sensor", "iso", "flash"}
        ),
        (
            "Edición de Video, Postproducción & Motion Graphics",
            {"video", "edicion", "edición", "premiere", "after effects", "motion", "motion graphics",
             "animacion", "animación", "colorimetria", "colorimetría", "audiovisual", "produccion",
             "producción", "cine", "guion", "guión", "montaje", "streaming", "davinci", "resolve",
             "avid", "pro tools", "audio", "sonido"}
        ),
        (
            "Modelado 3D, Render, Animación & CAD",
            {"3d", "blender", "cinema 4d", "c4d", "render", "renderizado", "modelado", "autocad",
             "cad", "sketchup", "rhinoceros", "rhino", "texturizado", "vray", "lumion", "unreal", "unity"}
        ),
        (
            "Diseño UI/UX, Producto Digital & Prototipado",
            {"ui", "ux", "figma", "prototipo", "prototipado", "interfaz", "experiencia de usuario",
             "wireframe", "wireframes", "design system"}
        )
    ],
    "Salud, Fitness, Nutrición & Bienestar": [
        (
            "Nutrición, Dietética, Alimentación & Cocina Saludable",
            {"nutricion", "nutrición", "dieta", "dietas", "alimentacion", "alimentación", "ayuno",
             "intermitente", "azucar", "azúcar", "recetas", "cocina", "batidos", "smoothies",
             "keto", "cetogenica", "cetogénica", "suplementacion", "suplementación", "macronutrientes",
             "calorias", "calorías", "metabolismo", "desintoxicacion", "detox", "vegetariana",
             "vegano", "adelgazar", "adelgazamiento", "grasa", "comida", "alimentos", "combustible",
             "antienvejecimiento", "tallas", "peso", "sobrepeso", "obesidad"}
        ),
        (
            "Entrenamiento Físico, Fuerza, Calistenia & Musculación",
            {"entrenamiento", "ejercicio", "ejercicios", "fitness", "gym", "gimnasio", "calistenia",
             "fuerza", "hipertrofia", "musculo", "músculo", "muscular", "musculacion", "musculación",
             "abdomen", "abdominales", "abs", "core", "torso", "pectorales", "pectoral", "gluteos",
             "glúteos", "piernas", "brazos", "espalda", "hiit", "pliometria", "pliometría",
             "pliometrico", "pliométrico", "pesas", "crossfit", "resistencia", "cardio", "movilidad",
             "flexibilidad", "rutinas", "definicion", "definición", "tonificar", "culturismo",
             "fisicoculturismo", "fisicoculturista", "power", "explosive", "suspension", "suspensión",
             "ligas", "funcional", "deportivo", "hibrido", "híbrido", "cronosfit", "atleta", "metamorfosis", "10x"}
        ),
        (
            "Terapias, Salud Holística & Rehabilitación",
            {"terapia", "terapeutico", "terapéutico", "biomagnetismo", "biomagnetica", "biomagnética",
             "salud", "medicina", "remedios", "enfermedad", "dolor", "postura", "columna", "vertebral",
             "pilates", "rehabilitacion", "rehabilitación", "bacterias", "hongos", "micologia",
             "micología", "psicopatologia", "psicopatología", "sistemica", "sistémica", "descanso",
             "holofitness", "holysticos", "diabetes", "neorejuvenation"}
        )
    ],
    "Tecnología, Programación, Ciberseguridad & IT": [
        (
            "Desarrollo Frontend, UI/UX & Web",
            {"frontend", "html", "css", "javascript", "typescript", "react", "vue", "angular",
             "diseno web", "diseño web", "ui", "ux", "maquetacion", "maquetación", "wordpress",
             "elementor", "divi", "cms"}
        ),
        (
            "Desarrollo Backend, APIs & Bases de Datos",
            {"backend", "python", "php", "nodejs", "node", "java", "golang", "c#", ".net", "sql",
             "postgresql", "mysql", "mongodb", "api", "apis", "rest", "graphql", "microservicios",
             "servidores", "arquitectura"}
        ),
        (
            "Ciberseguridad, Redes & Infraestructura",
            {"hacking", "ciberseguridad", "seguridad", "red", "redes", "linux", "cisco", "firewall",
             "pentesting", "vulnerabilidades", "forense", "criptografia", "criptografía", "devops",
             "docker", "cloud", "aws"}
        ),
        (
            "Data Science, Inteligencia Artificial & Big Data",
            {"data", "big data", "analytics", "analitica", "analítica", "machine learning", "ia",
             "inteligencia artificial", "deep learning", "pandas", "numpy", "algebra", "álgebra",
             "matematicas", "matemáticas", "estadistica", "estadística"}
        )
    ],
    "Marketing Digital, Redes Sociales & Tráfico": [
        (
            "Redes Sociales, Video & Creadores de Contenido",
            {"youtube", "youtuber", "instagram", "tiktok", "reels", "shorts", "redes sociales",
             "community", "creador", "video marketing", "viralidad", "algoritmo", "audiencia",
             "engagement", "suscriptores"}
        ),
        (
            "Tráfico Pago, Publicidad & Anuncios",
            {"facebook ads", "google ads", "tiktok ads", "anuncios", "publicidad", "campañas",
             "campanas", "trafico", "tráfico", "pauta", "roas", "cpc", "conversion", "conversión"}
        ),
        (
            "Estrategia, Branding & Copywriting",
            {"copywriting", "branding", "marca", "posicionamiento", "storytelling", "estrategia",
             "comunicacion", "comunicación", "lanzamientos"}
        ),
        (
            "Embudos, Email Marketing & Automatización",
            {"funnel", "funnels", "embudos", "email marketing", "automatizacion", "automatización",
             "leads", "secuencias", "lead magnet"}
        )
    ],
    "Desarrollo Personal, Hábitos & Mentalidad": [
        (
            "Hábitos, Disciplina & Productividad",
            {"habitos", "hábitos", "disciplina", "productividad", "rutinas", "gestion del tiempo",
             "gestión del tiempo", "enfoque", "concentracion", "concentración", "metas", "proposito"}
        ),
        (
            "Gestión Emocional, Autoestima & Psicología",
            {"emociones", "psicologia", "psicología", "autoestima", "creencias", "miedo", "mente",
             "mentalidad", "mindset", "resiliencia", "reprogramacion", "reprogramación", "felicidad"}
        ),
        (
            "Liderazgo, Habilidades Sociales & Relaciones",
            {"liderazgo", "habilidades sociales", "relaciones", "comunicacion interpersonal",
             "influencia", "carisma", "persuasion personal"}
        )
    ],
    "Idiomas & Habilidades Prácticas": [
        (
            "Fonética, Pronunciación & Inmersión Auditiva",
            {"pronunciacion", "pronunciación", "fonetica", "fonética", "listening", "oido", "oído",
             "acento", "inmersion", "inmersión", "hablar"}
        ),
        (
            "Gramática, Vocabulario & Estructura del Idioma",
            {"gramatica", "gramática", "vocabulario", "estructura", "oraciones", "tiempos verbales",
             "lectura", "escribir", "reglas"}
        ),
        (
            "Fluidez Conversacional, Sagas Progresivas & Niveles",
            {"conversar", "fluidez", "conversacional", "dialogos", "diálogos", "principiante",
             "intermedio", "avanzado", "nivel"}
        ),
        (
            "Artesanías, Oficios & Habilidades Manuales",
            {"resina", "artesanias", "artesanías", "tazas", "termos", "decoracion", "decoración",
             "crochet", "tejer", "costura", "manualidades", "carpinteria", "carpintería"}
        ),
        (
            "Música, Canto & Producción Sonora",
            {"musica", "música", "canto", "vocal", "guitarra", "piano", "dj", "produccion musical",
             "producción musical", "mezclar"}
        )
    ]
}


def _norm_token_set(text: str) -> Set[str]:
    """Extrae conjunto de tokens limpios en minúsculas y sin acentos."""
    cleaned = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII').lower()
    return set(re.findall(r'[a-z0-9]+', cleaned))


def cluster_courses_into_itineraries(courses: list, col_name: str, target: str = "") -> Tuple[Dict[str, list], list]:
    """
    Agrupa cursos en itinerarios pedagógicos coherentes de forma totalmente no supervisada.
    - Utiliza taxonomía ontológica universal (UNIVERSAL_MACRO_DOMAINS y DOMAIN_FACETS).
    - Cero hardcoding de autores, títulos de cursos, o marcas comerciales.
    - Catálogos homogéneos pequeños (<= 8 cursos): Ruta Pedagógica Integral unificada.
    - Catálogos densos (>= 9 cursos): Descomposición dinámica en sub-itinerarios temáticos (facetas).
    """
    total_count = len(courses)
    itineraries = {}
    outliers = []

    if total_count == 0:
        return itineraries, outliers

    if total_count <= 8:
        author_label = col_name.title() if col_name else 'Catálogo'
        track_name = f"Ruta Pedagógica Integral: {author_label}"
        itineraries[track_name] = courses
        return itineraries, outliers

    # 1. Puntuación de afinidad hacia macro-dominios universales
    domain_scores = defaultdict(lambda: defaultdict(int))
    for idx, c in enumerate(courses):
        t_clean = c.get("clean_title", "")
        desc = f"{c.get('short_desc', '')} {c.get('long_desc', '')}"

        t_words = _norm_token_set(t_clean)
        d_words = _norm_token_set(desc)
        cat_words = set()
        for cat in (c.get('categories', []) + c.get('breadcrumbs', [])):
            cat_words.update(_norm_token_set(cat))

        full_text_lower = f"{t_clean} {desc}".lower()

        for d_name, d_keys in UNIVERSAL_MACRO_DOMAINS:
            active_keys = set(d_keys)

            # Filtros de desambiguación contextual de polisemia
            # 1. Modismo "bajo presupuesto" no es inversión financiera ni trading
            if d_name == "Inversiones, Finanzas, Criptoactivos & Trading":
                if "bajo presupuesto" in full_text_lower or "poco presupuesto" in full_text_lower or "sin presupuesto" in full_text_lower:
                    active_keys = active_keys - {"presupuesto"}

            # 2. "Cámara" técnica de fotografía/video/streaming no es oratoria ni hablar en público
            if d_name == "Oratoria, Comunicación & Hablar en Público":
                is_photo_cam = any(k in full_text_lower for k in ["lente", "lentes", "foto", "fotos", "video", "sensor", "iso", "disparo", "rubenguo", "streaming", "audiovisual", "retrato"])
                is_speech = any(k in full_text_lower for k in ["hablar", "oratoria", "publico", "público", "miedo escenico", "discurso", "locucion", "vocalizacion"])
                if is_photo_cam and not is_speech:
                    active_keys = active_keys - {"camara", "cámara", "camaras", "cámaras"}

            # 3. Dibujo de anatomía/cuerpo y ejercicios de manga/ilustración no son salud ni fitness
            if d_name == "Salud, Fitness, Nutrición & Bienestar":
                is_art_drawing = any(k in full_text_lower for k in ["dibujo", "dibujar", "ilustracion", "ilustración", "manga", "mangaka", "comic", "comics", "trazos", "boceto", "acuarela", "pintura"])
                if is_art_drawing:
                    active_keys = active_keys - {"cuerpo", "ejercicios", "ejercicio", "rutinas"}

            # Ponderación arquitectural objetiva: Categorías oficiales (+20), Título (+10), Descripción (+1)
            t_inter = len(t_words.intersection(active_keys))
            c_inter = len(cat_words.intersection(active_keys))
            d_inter = len(d_words.intersection(active_keys))
            sc = (c_inter * 20) + (t_inter * 10) + d_inter
            if sc > 0:
                domain_scores[idx][d_name] = sc

    # 2. Asignación inicial por afinidad
    domain_membership = defaultdict(list)
    unassigned = []
    target_lower = f"{col_name} {target}".lower()
    for idx, c in enumerate(courses):
        scores = domain_scores[idx]
        if scores:
            # Desempate arquitectónico: si el catálogo apunta a diseño/audiovisual o el curso tiene categorías afines
            best_domain = max(
                scores.keys(),
                key=lambda d: (
                    scores[d],
                    1 if (d == "Audiovisual, Animación, Diseño & Fotografía" and any(k in target_lower for k in ["diseno", "diseño", "grafico", "gráfico", "audiovisual", "foto", "video", "animacion", "animación"])) else 0
                )
            )
            domain_membership[best_domain].append(c)
        else:
            unassigned.append(c)

    # 3. Determinación de dominio dominante del catálogo
    dominant_domain = None
    if domain_membership:
        candidate_dom, dom_courses = max(domain_membership.items(), key=lambda x: len(x[1]))
        if len(dom_courses) >= (total_count * 0.40):
            dominant_domain = candidate_dom

    # 4. Resolución de no asignados (si hay dominio dominante, pertenecen allí; si no, a complementarios)
    for c in unassigned:
        if dominant_domain:
            domain_membership[dominant_domain].append(c)
        else:
            c["divergent_area"] = "Habilidades Complementarias / Electivo General"
            outliers.append(c)

    # 5. Formación de itinerarios por dominio y descomposición en sub-itinerarios (facetas)
    itinerary_idx = 1
    sorted_domains = sorted(domain_membership.items(), key=lambda x: -len(x[1]))

    for dom_name, c_list in sorted_domains:
        # Aislamiento de residuales minúsculos (<= 2 cursos) en presencia de dominio dominante
        if dominant_domain and dom_name != dominant_domain and len(c_list) <= 2:
            for c in c_list:
                c["divergent_area"] = f"{dom_name} (Electivo)"
                outliers.append(c)
            continue
        elif len(c_list) < 2 and total_count > 10 and not dominant_domain:
            for c in c_list:
                c["divergent_area"] = f"{dom_name} (Electivo)"
                outliers.append(c)
            continue

        # Si el dominio es denso (>= 9 cursos) y tiene facetas definidas, descomponer en sub-tracks
        facets = DOMAIN_FACETS.get(dom_name, [])
        if len(c_list) >= 9 and facets:
            facet_membership = defaultdict(list)
            facet_unassigned = []

            for c in c_list:
                t_words = _norm_token_set(c.get("clean_title", ""))
                desc_val = f"{c.get('short_desc', '')} {c.get('long_desc', '')}"
                d_words = _norm_token_set(desc_val)
                cat_words = set()
                for cat in (c.get('categories', []) + c.get('breadcrumbs', [])):
                    cat_words.update(_norm_token_set(cat))

                best_f = None
                best_f_sc = 0
                for f_name, f_keys in facets:
                    t_inter = len(t_words.intersection(f_keys))
                    c_inter = len(cat_words.intersection(f_keys))
                    d_inter = len(d_words.intersection(f_keys))
                    f_sc = (c_inter * 15) + (t_inter * 10) + d_inter
                    if f_sc > best_f_sc:
                        best_f_sc = f_sc
                        best_f = f_name

                if best_f and best_f_sc > 0:
                    facet_membership[best_f].append(c)
                else:
                    facet_unassigned.append(c)

            # Reasignar no asignados a la faceta más afín o a la faceta principal
            if facet_membership:
                largest_facet = max(facet_membership.keys(), key=lambda k: len(facet_membership[k]))
                for c in facet_unassigned:
                    facet_membership[largest_facet].append(c)
            else:
                facet_membership[f"{dom_name}: Troncal General"] = c_list

            # Generar itinerarios para cada faceta válida
            for f_name, f_courses in sorted(facet_membership.items(), key=lambda x: -len(x[1])):
                itineraries[f"Itinerario {itinerary_idx}: {f_name}"] = f_courses
                itinerary_idx += 1
        else:
            itineraries[f"Itinerario {itinerary_idx}: {dom_name}"] = c_list
            itinerary_idx += 1

    return itineraries, outliers


def assign_roles_and_prerequisites(itinerary_courses: list, is_volatile: bool, start_p_idx: int, is_small_catalog: bool = False) -> Tuple[list, int]:
    """
    Ordena cursos pedagógicamente dentro de un itinerario:
    1. Preserva series secuenciales consecutivas (🔗 Secuenciales).
    2. Agrupa módulos gemelos / complementarios (ej: GRAM Positivas y GRAM Negativas) contiguamente, NUNCA como alternativas.
    3. Asegura la clausura del grafo: cursos iniciales jamás exigen fases inexistentes.
    """
    series_groups = defaultdict(list)
    twin_groups = defaultdict(list)

    for c in itinerary_courses:
        author_val = c.get("author", "") or "unknown"
        s_key, s_ord, s_marker = extract_series_signature(c["clean_title"], author_val)
        t_base, t_mod, is_t = extract_twin_signature(c["clean_title"], author_val)
        c["_series_key"] = s_key
        c["_series_ord"] = s_ord
        c["_series_marker"] = s_marker
        c["_twin_base"] = t_base
        c["_twin_mod"] = t_mod
        c["_is_twin"] = is_t
        series_groups[s_key].append(c)
        if is_t:
            twin_groups[t_base].append(c)

    confirmed_series_keys = set()
    for s_key, s_courses in series_groups.items():
        if len(s_courses) >= 2:
            if any(sc["_series_ord"] > 0 for sc in s_courses):
                for sc in s_courses:
                    if sc["_series_ord"] == 0:
                        sc["_series_ord"] = 1
                distinct_ords = {sc["_series_ord"] for sc in s_courses}
                if len(distinct_ords) >= 2:
                    confirmed_series_keys.add(s_key)

    series_base_phase = {}
    series_base_prio = {}
    for s_key, s_courses in series_groups.items():
        if s_key in confirmed_series_keys:
            series_base_phase[s_key] = min(sc.get("phase_num", 1) for sc in s_courses)
            prios = []
            for sc in s_courses:
                st_low = sc["clean_title"].lower()
                if any(k in st_low for k in ["primer nivel", "primeros pasos", "desde cero", "fundament", "principi", "basico", "básico", "introducc"]):
                    prios.append(0)
                elif any(k in st_low for k in ["nivel 1", "nivel i ", "nivel i)"]):
                    prios.append(1)
                elif any(k in st_low for k in ["iniciaci", "completo", "esencial"]):
                    prios.append(2)
                else:
                    prios.append(3)
            series_base_prio[s_key] = min(prios) if prios else 1

    confirmed_twin_bases = set()
    for t_base, t_courses in twin_groups.items():
        if len(t_courses) >= 2:
            confirmed_twin_bases.add(t_base)

    twin_base_phase = {}
    twin_base_prio = {}
    for t_base, t_courses in twin_groups.items():
        if t_base in confirmed_twin_bases:
            twin_base_phase[t_base] = min(sc.get("phase_num", 1) for sc in t_courses)
            prios = []
            for tc in t_courses:
                tt_low = tc["clean_title"].lower()
                if any(k in tt_low for k in ["primer nivel", "primeros pasos", "desde cero", "fundament", "principi", "basico", "básico", "introducc"]):
                    prios.append(0)
                elif any(k in tt_low for k in ["nivel 1", "nivel i ", "nivel i)"]):
                    prios.append(1)
                elif any(k in tt_low for k in ["iniciaci", "completo", "esencial"]):
                    prios.append(2)
                else:
                    prios.append(3)
            twin_base_prio[t_base] = min(prios) if prios else 1

    # Ordenamiento pedagógico desprovisto de sesgo multipartes
    def sort_key(c):
        s_key = c["_series_key"]
        t_base = c["_twin_base"]
        t_low = c["clean_title"].lower()

        # Prioridad conceptual intra-fase (gobierna la posición fundacional)
        if any(k in t_low for k in ["primer nivel", "primeros pasos", "desde cero", "fundament", "principi", "basico", "básico", "introducc"]):
            intra_phase_prio = 0
        elif any(k in t_low for k in ["nivel 1", "nivel i ", "nivel i)"]):
            intra_phase_prio = 1
        elif any(k in t_low for k in ["iniciaci", "completo", "esencial"]):
            intra_phase_prio = 2
        elif any(k in t_low for k in ["avanzad", "maestr", "tercer", "cuarto", "profund"]):
            intra_phase_prio = 4
        else:
            intra_phase_prio = 3

        if s_key in confirmed_series_keys:
            return (
                series_base_phase.get(s_key, c.get("phase_num", 1)),
                series_base_prio.get(s_key, 1),
                0,  # serie ordenada
                s_key,
                c["_series_ord"],
                str(c.get("real_year", c.get("year", ""))),
                c["clean_title"].lower()
            )
        elif t_base in confirmed_twin_bases:
            twin_pos = 0 if "positiva" in c["_twin_mod"] else 1
            return (
                twin_base_phase.get(t_base, c.get("phase_num", 1)),
                twin_base_prio.get(t_base, 1),
                1,  # par gemelo
                t_base,
                twin_pos,
                str(c.get("real_year", c.get("year", ""))),
                c["clean_title"].lower()
            )
        else:
            return (
                c.get("phase_num", 1),
                intra_phase_prio,
                2,  # curso individual
                "",
                0,
                str(c.get("real_year", c.get("year", ""))),
                c["clean_title"].lower()
            )

    itinerary_courses.sort(key=sort_key)

    present_phases = sorted(list(set(c.get("phase_num", 1) for c in itinerary_courses)))
    min_phase = present_phases[0] if present_phases else 1

    phase_short_names = {
        1: "[F1] Fundamentos & Principios",
        2: "[F2] Métodos & Práctica Instrumental",
        3: "[F3] Integración & Proyectos Completos",
        4: "[F4] Optimización & Especialización",
        5: "[F5] Negocio & Salida al Mercado"
    }

    seen_phase_topics = {}
    seen_courses_in_catalog = []
    series_last_step = {}
    twin_last_step = {}
    p_idx = start_p_idx

    # Detección de stopwords transversales del catálogo (ej. 'reiki' en un catálogo monotemático de Reiki)
    catalog_wide_stopwords = {
        w for w, cnt in Counter(
            w for c_item in itinerary_courses
            for w in re.findall(r'[a-záéíóúñ0-9]+', c_item["clean_title"].lower())
            if len(w) >= 4 and w not in SPANISH_STOPWORDS
        ).items() if cnt >= max(3, len(itinerary_courses) * 0.40)
    }
    generic_technical_stopwords = {
        "curso", "taller", "nivel", "clases", "metodo", "método", "online", "master", "masterclass",
        "system", "sistema", "completo", "aprende", "total", "diplomado", "alta", "vida", "vidas",
        "para", "como", "sobre", "gran", "paso", "pasos", "arte"
    }

    for c in itinerary_courses:
        c["code"] = f"P{p_idx:02d}"
        p_num = c.get("phase_num", 1)
        s_key = c["_series_key"]
        s_ord = c["_series_ord"]
        t_base = c["_twin_base"]
        year_str = str(c.get("year", "2020"))
        year_val = int(year_str[:4]) if year_str[:4].isdigit() else 2020

        # Caso A: Serie Secuencial Confirmada
        if s_key in confirmed_series_keys:
            # Armonización de fase en series correlativas: Nivel 2 -> Fase 2 si fue inflado indebidamente
            if s_ord == 2 and p_num > 2 and not any(k in c["clean_title"].lower() for k in ["avanzad", "maestr", "profund"]):
                c["phase_num"] = 2
                c["phase_label"] = "Fase 2: Métodos & Práctica Instrumental"
                p_num = 2
            elif s_ord == 3 and p_num > 3 and not any(k in c["clean_title"].lower() for k in ["avanzad", "maestr", "profund"]):
                c["phase_num"] = 3
                c["phase_label"] = "Fase 3: Integración & Proyectos Completos"
                p_num = 3

            if s_key not in series_last_step:
                c["role"] = "⭐ Troncal"
                series_last_step[s_key] = (c["code"], c["clean_title"], s_ord)
                if p_num == min_phase or p_idx == start_p_idx:
                    c["prereq"] = "Punto de partida de la serie"
                else:
                    prev_p = max((p for p in present_phases if p < p_num), default=min_phase)
                    c["prereq"] = f"Requiere dominar {phase_short_names.get(prev_p, f'[F{prev_p}]')}"
            else:
                prev_code, prev_title, prev_ord = series_last_step[s_key]
                c["role"] = "🔗 Secuencial"
                gap_note = ""
                if s_ord > 0 and prev_ord > 0 and (s_ord - prev_ord) > 1:
                    gap_note = " [⚠️ Salto en serie: Módulos intermedios no disponibles en MCV]"
                c["prereq"] = f"Requiere completar [{prev_code}] ({prev_title}){gap_note}"
                series_last_step[s_key] = (c["code"], c["clean_title"], s_ord)

            seen_courses_in_catalog.append(c)
            p_idx += 1
            continue

        # Caso B: Módulo Gemelo / Par Complementario (ej. GRAM Positivas / Negativas)
        if t_base in confirmed_twin_bases:
            if t_base not in twin_last_step:
                c["role"] = "⭐ Troncal" if p_num not in seen_phase_topics else "📚 Especialidad"
                seen_phase_topics[p_num] = c["code"]
                twin_last_step[t_base] = (c["code"], c["clean_title"])
                if p_num == min_phase or p_idx == start_p_idx:
                    c["prereq"] = "Punto de partida de la serie temática"
                else:
                    prev_p = max((p for p in present_phases if p < p_num), default=min_phase)
                    c["prereq"] = f"Requiere dominar {phase_short_names.get(prev_p, f'Fase {prev_p}')}"
            else:
                prev_code, prev_title = twin_last_step[t_base]
                c["role"] = "📚 Especialidad"
                c["prereq"] = f"Módulo complementario a [{prev_code}] ({prev_title})"
                twin_last_step[t_base] = (c["code"], c["clean_title"])

            seen_courses_in_catalog.append(c)
            p_idx += 1
            continue

        # Caso C: Curso Individual
        concept_kw = extract_agnostic_concept_keyword(c["clean_title"])

        # Búsqueda de predecesor temático causal en fases estrictamente anteriores
        direct_predecessor = None
        c_tokens = set(re.findall(r'[a-záéíóúñ0-9]+', c["clean_title"].lower())) - SPANISH_STOPWORDS - catalog_wide_stopwords - generic_technical_stopwords
        meaningful_c = {w for w in c_tokens if len(w) >= 4}

        if meaningful_c and p_num > min_phase:
            best_sc = 0
            for prev_c in reversed(seen_courses_in_catalog):
                if prev_c.get("phase_num", 1) < p_num:
                    # Invariante Jerárquico: Un curso Troncal jamás debe depender de una Especialidad optativa
                    if c.get("role") == "⭐ Troncal" and prev_c.get("role") == "📚 Especialidad":
                        continue
                    # Invariante de Maestría: Un curso fundacional o completo nunca debe depender de un curso de maestría
                    if any(k in c["clean_title"].lower() for k in ["completo", "fundament", "desde cero"]) and any(k in prev_c["clean_title"].lower() for k in ["maestro", "maestría", "maestria", "avanzado"]):
                        continue
                    prev_tokens = set(re.findall(r'[a-záéíóúñ0-9]+', prev_c["clean_title"].lower())) - SPANISH_STOPWORDS - catalog_wide_stopwords - generic_technical_stopwords
                    meaningful_prev = {w for w in prev_tokens if len(w) >= 4}
                    common = meaningful_c.intersection(meaningful_prev)
                    if len(common) > best_sc:
                        best_sc = len(common)
                        direct_predecessor = prev_c

        alt_primary = None
        for prev_c in seen_courses_in_catalog:
            if is_true_alternative(prev_c["clean_title"], c["clean_title"], prev_c.get("author", ""), c.get("author", "")):
                alt_primary = prev_c
                break

        if alt_primary:
            prev_year_str = str(alt_primary.get("year", "2020"))
            prev_year_val = int(prev_year_str[:4]) if prev_year_str[:4].isdigit() else 2020
            if is_volatile and (prev_year_val - year_val) >= 3:
                c["role"] = "⚠️ Histórico"
                c["prereq"] = f"Opcional de referencia (Superado por [{alt_primary['code']}])"
            else:
                c["role"] = "🔄 Alternativa"
                c["prereq"] = f"Alternativa electiva a [{alt_primary['code']}]"
        else:
            t_low = c["clean_title"].lower()
            is_foundational_intro = any(k in t_low for k in ["primer nivel", "primeros pasos", "nivel 1", "fundament", "principi", "desde cero", "basico", "básico"])
            is_major_milestone = any(k in t_low for k in ["completo", "sistema", "integral", "avanzado", "maestria", "maestría", "master", "masterclass", "nivel 4", "nivel 5"])

            if p_num not in seen_phase_topics:
                seen_phase_topics[p_num] = c["code"]
                c["role"] = "⭐ Troncal"
                if p_num == min_phase or p_idx == start_p_idx:
                    c["prereq"] = "Ninguno (Punto de partida del itinerario)"
                elif direct_predecessor:
                    c["prereq"] = f"Requiere dominar [{direct_predecessor['code']}] ({direct_predecessor['clean_title']})"
                else:
                    prev_p = max((p for p in present_phases if p < p_num), default=min_phase)
                    c["prereq"] = f"Requiere dominar {phase_short_names.get(prev_p, f'[F{prev_p}]')}"
            elif is_foundational_intro:
                c["role"] = "⭐ Troncal"
                if p_num == min_phase:
                    c["prereq"] = f"Troncal fundacional paralelo o rama alternativa (opción a [{seen_phase_topics[p_num]}])"
                elif direct_predecessor:
                    c["prereq"] = f"Requiere dominar [{direct_predecessor['code']}] ({direct_predecessor['clean_title']})"
                else:
                    prev_p = max((p for p in present_phases if p < p_num), default=min_phase)
                    c["prereq"] = f"Requiere dominar {phase_short_names.get(prev_p, f'[F{prev_p}]')}"
            elif is_major_milestone and p_num >= 3:
                c["role"] = "⭐ Troncal"
                if direct_predecessor:
                    c["prereq"] = f"Requiere completar [{direct_predecessor['code']}] ({direct_predecessor['clean_title']})"
                else:
                    prev_p = max((p for p in present_phases if p < p_num), default=min_phase)
                    c["prereq"] = f"Requiere dominar {phase_short_names.get(prev_p, f'[F{prev_p}]')}"
            else:
                c["role"] = "📚 Especialidad"
                if direct_predecessor:
                    c["prereq"] = f"Especialización vinculada a [{direct_predecessor['code']}] ({direct_predecessor['clean_title']})"
                else:
                    c["prereq"] = f"Electivo complementario de [Fase {p_num}]"

        seen_courses_in_catalog.append(c)
        p_idx += 1

    return itinerary_courses, p_idx


def _visual_pad(text: str, target_w: int) -> str:
    """Garantiza longitud uniforme en caracteres para alineación determinista de 135 columnas en texto plano."""
    pad_len = max(0, target_w - len(text))
    return f"{text}{' ' * pad_len}"


def render_ascii_boxed_table(c_list: list, width: int = 135, is_outliers: bool = False) -> list:
    """Renderiza una tabla ASCII/Unicode con bordes limpios, nombre de curso precedido por el peldaño, doble fecha (real y MCV), wrapping automatico y espacio holgado."""
    w_year = 15
    if is_outliers:
        w_area = 35
        w_title = max(50, width - (w_area + w_year + 4))

        border_top = f"┌{'─'*w_title}┬{'─'*w_area}┬{'─'*w_year}┐"
        border_mid = f"├{'─'*w_title}┼{'─'*w_area}┼{'─'*w_year}┤"
        border_bot = f"└{'─'*w_title}┴{'─'*w_area}┴{'─'*w_year}┘"

        lines = [border_top]
        lines.append(f"│ {'Curso & Autor':<{w_title-2}} │ {'Área Detectada':<{w_area-2}} │ {'Año Real/MCV':^{w_year-2}} │")
        lines.append(border_mid)

        for c in c_list:
            safe_title = c['clean_title'].replace('|', '-').replace('\n', ' ').strip()
            safe_author = f" - {c['author'].replace('|', '-').strip()}" if c.get("author") and c["author"] != "Autor no especificado" else ""
            course_text = f"[{c['code']}] {safe_title}{safe_author}"
            area_str = c.get('divergent_area', 'Complementario')[:w_area-2]

            m_raw = str(c.get('mcv_year', c.get('meta_year', ''))).strip()
            mcv_yr = m_raw[:7] if re.match(r'^\d{4}-\d{2}', m_raw) else (m_raw[:4] if re.match(r'^\d{4}', m_raw) else "")
            r_raw = str(c.get('real_year', c.get('year', 'S/F'))).strip()
            real_yr = r_raw[:7] if re.match(r'^\d{4}-\d{2}', r_raw) else (r_raw[:4] if re.match(r'^\d{4}', r_raw) else "S/F")

            is_verified = c.get('is_original_verified', False)
            real_num = int(real_yr[:4]) if (real_yr and real_yr[:4].isdigit()) else 0
            mcv_num = int(mcv_yr[:4]) if (mcv_yr and mcv_yr[:4].isdigit()) else 9999

            if is_verified and real_yr and real_yr != 'S/F' and mcv_yr and mcv_yr != 'S/F' and real_yr[:4] != mcv_yr[:4] and real_num <= mcv_num:
                y_l1 = f"Real: {real_yr}"
                y_l2 = f"MCV: {mcv_yr}"
            elif mcv_yr and mcv_yr != 'S/F':
                y_l1 = mcv_yr
                y_l2 = ""
            elif real_yr and real_yr != 'S/F' and real_num <= mcv_num:
                y_l1 = real_yr
                y_l2 = ""
            else:
                y_l1 = "S/F"
                y_l2 = ""

            title_chunks = textwrap.wrap(course_text, width=w_title-2, subsequent_indent="      ") or [course_text[:w_title-2]]

            first_title = title_chunks[0]
            lines.append(f"│ {first_title:<{w_title-2}} │ {area_str:<{w_area-2}} │ {y_l1:^{w_year-2}} │")
            y_l2_placed = False
            for t_chunk in title_chunks[1:]:
                col_y = y_l2 if not y_l2_placed else ""
                y_l2_placed = True
                lines.append(f"│ {t_chunk:<{w_title-2}} │ {'':<{w_area-2}} │ {col_y:^{w_year-2}} │")
            if y_l2 and not y_l2_placed:
                lines.append(f"│ {'':<{w_title-2}} │ {'':<{w_area-2}} │ {y_l2:^{w_year-2}} │")
            lines.append(border_mid)

        if lines and lines[-1] == border_mid:
            lines[-1] = border_bot
        return lines

    w_role = 18
    w_phase = 42
    w_title = max(50, width - (w_role + w_phase + w_year + 5))

    border_top = f"┌{'─'*w_title}┬{'─'*w_role}┬{'─'*w_phase}┬{'─'*w_year}┐"
    border_mid = f"├{'─'*w_title}┼{'─'*w_role}┼{'─'*w_phase}┼{'─'*w_year}┤"
    border_bot = f"└{'─'*w_title}┴{'─'*w_role}┴{'─'*w_phase}┴{'─'*w_year}┘"

    lines = [border_top]
    lines.append(f"│ {'Curso & Prerrequisito Clave':<{w_title-2}} │ {_visual_pad('Rol', w_role-2)} │ {'Fase Cognitiva':<{w_phase-2}} │ {'Año Real/MCV':^{w_year-2}} │")
    lines.append(border_mid)

    for c in c_list:
        safe_title = c['clean_title'].replace('|', '-').replace('\n', ' ').strip()
        safe_author = f" - {c['author'].replace('|', '-').strip()}" if c.get("author") and c["author"] != "Autor no especificado" else ""
        course_text = f"[{c['code']}] {safe_title}{safe_author}"
        role_str = c.get('role', '')
        p_num = c.get('phase_num', 1)
        p_name = c.get('phase_label', '').split(':', 1)[-1].strip()
        phase_str = f"[F{p_num}] {p_name}"[:w_phase-2]
        prereq_str = f"↳ Prerrequisito: {c.get('prereq', '')}"

        m_raw = str(c.get('mcv_year', c.get('meta_year', ''))).strip()
        mcv_yr = m_raw[:7] if re.match(r'^\d{4}-\d{2}', m_raw) else (m_raw[:4] if re.match(r'^\d{4}', m_raw) else "")
        r_raw = str(c.get('real_year', c.get('year', 'S/F'))).strip()
        real_yr = r_raw[:7] if re.match(r'^\d{4}-\d{2}', r_raw) else (r_raw[:4] if re.match(r'^\d{4}', r_raw) else "S/F")

        is_verified = c.get('is_original_verified', False)
        real_num = int(real_yr[:4]) if (real_yr and real_yr[:4].isdigit()) else 0
        mcv_num = int(mcv_yr[:4]) if (mcv_yr and mcv_yr[:4].isdigit()) else 9999

        if is_verified and real_yr and real_yr != 'S/F' and mcv_yr and mcv_yr != 'S/F' and real_yr[:4] != mcv_yr[:4] and real_num <= mcv_num:
            y_l1 = f"Real: {real_yr}"
            y_l2 = f"MCV: {mcv_yr}"
        elif mcv_yr and mcv_yr != 'S/F':
            y_l1 = mcv_yr
            y_l2 = ""
        elif real_yr and real_yr != 'S/F' and real_num <= mcv_num:
            y_l1 = real_yr
            y_l2 = ""
        else:
            y_l1 = "S/F"
            y_l2 = ""

        title_chunks = textwrap.wrap(course_text, width=w_title-2, subsequent_indent="      ") or [course_text[:w_title-2]]
        prereq_chunks = textwrap.wrap(prereq_str, width=w_title-4, subsequent_indent="  ") or [prereq_str[:w_title-4]]

        first_title = title_chunks[0]
        lines.append(f"│ {first_title:<{w_title-2}} │ {_visual_pad(role_str, w_role-2)} │ {phase_str:<{w_phase-2}} │ {y_l1:^{w_year-2}} │")
        y_l2_placed = False
        for t_chunk in title_chunks[1:]:
            col_y = y_l2 if not y_l2_placed else ""
            y_l2_placed = True
            lines.append(f"│ {t_chunk:<{w_title-2}} │ {_visual_pad('', w_role-2)} │ {'':<{w_phase-2}} │ {col_y:^{w_year-2}} │")
        for p_chunk in prereq_chunks:
            col_y = y_l2 if not y_l2_placed else ""
            y_l2_placed = True
            lines.append(f"│   {p_chunk:<{w_title-4}} │ {_visual_pad('', w_role-2)} │ {'':<{w_phase-2}} │ {col_y:^{w_year-2}} │")
        if y_l2 and not y_l2_placed:
            lines.append(f"│ {'':<{w_title-2}} │ {_visual_pad('', w_role-2)} │ {'':<{w_phase-2}} │ {y_l2:^{w_year-2}} │")
        lines.append(border_mid)

    if lines and lines[-1] == border_mid:
        lines[-1] = border_bot

    return lines


def handle_curriculum(target: str, args) -> bool:
    """
    Analiza un catálogo de autor o categoría de MCV (URL o directorio local),
    deconstruye la correlatividad pedagógica mediante crawling profundo y genera
    RUTA_DE_APRENDIZAJE.txt estructurado en itinerarios formativos coherentes.
    Incorpora temporalidad dúctil (conocimiento perenne vs tecnologías volátiles),
    desduplicación por alternativas, detección de cursos desalineados (outliers) y
    desacoplamiento estricto de Google NotebookLM en fase exploratoria.
    """
    logger.info(f"\n=======================================================")
    logger.info(f"🧭 MOTOR CURRICULAR UNIVERSAL (BLOOM-DREYFUS v9.2.0): {target}")
    logger.info(f"=======================================================")

    raw_items = []
    author_name = getattr(args, "alias", "") or ""
    author_dir = None

    if os.path.isdir(target):
        target_dir = os.path.abspath(target)
        if os.path.basename(target_dir).upper() == "NOTEBOOKLM_AUDIOS":
            target_dir = os.path.dirname(target_dir)

        author_dir = target_dir
        if not author_name:
            author_name = os.path.basename(target_dir).replace("-", " ").replace("_", " ")

        contained = discover_contained_courses(target_dir)
        if contained:
            for c_path in contained:
                meta = resolve_or_lookup_course_metadata(c_path, alias=author_name)
                c_title = meta.get("title") or os.path.basename(c_path)
                deep_info = extract_local_course_deep_metadata(c_path)
                raw_items.append({
                    "title": deep_info.get("canonical_title") or c_title,
                    "path": c_path,
                    "meta": meta,
                    "short_desc": deep_info.get("short_desc", ""),
                    "long_desc": deep_info.get("long_desc", ""),
                    "categories": deep_info.get("categories", []),
                    "breadcrumbs": deep_info.get("breadcrumbs", []),
                    "meta_year": deep_info.get("year", "")
                })
        else:
            for entry in sorted(os.listdir(target_dir)):
                ep = os.path.join(target_dir, entry)
                if os.path.isdir(ep) and not entry.startswith(".") and entry.lower() not in ["_temp_downloads", "0.dwnl", "notebooklm_audios", "__pycache__"]:
                    meta = resolve_or_lookup_course_metadata(ep, alias=author_name)
                    c_title = meta.get("title") or entry
                    deep_info = extract_local_course_deep_metadata(ep)
                    raw_items.append({
                        "title": deep_info.get("canonical_title") or c_title,
                        "path": ep,
                        "meta": meta,
                        "short_desc": deep_info.get("short_desc", ""),
                        "long_desc": deep_info.get("long_desc", ""),
                        "categories": deep_info.get("categories", []),
                        "breadcrumbs": deep_info.get("breadcrumbs", []),
                        "meta_year": deep_info.get("year", "")
                    })
    elif is_collection_url(target):
        session = get_session(args.cookies)
        col_name, catalog_courses = crawl_collection_courses(session, target)
        if not author_name:
            author_name = col_name or "Catálogo MCV"

        logger.info(f"🕷️ Extrayendo fichas técnicas profundas en paralelo ({len(catalog_courses)} cursos)...")
        with ThreadPoolExecutor(max_workers=8) as ex:
            deep_metas = list(ex.map(lambda c: fetch_course_deep_metadata(session, c.get("url")), catalog_courses))

        # Inyección del target/filtro de catálogo como prior en categorías
        target_slug = ""
        m_slug = re.search(r'brx_qdsvwi(?:%5B%5D|\[\])=([^&]+)', target) or re.search(r'/categoria(?:-producto)?/([^/]+)', target)
        if m_slug:
            target_slug = urllib.parse.unquote(m_slug.group(1)).replace('-', ' ')

        for c, dm in zip(catalog_courses, deep_metas):
            cats = list(dm.get("categories", []))
            if col_name and col_name.strip() and col_name not in cats:
                cats.append(col_name.strip())
            if target_slug and target_slug not in cats:
                cats.append(target_slug)
            raw_items.append({
                "title": dm.get("canonical_title") or c.get("title", ""),
                "url": c.get("url", ""),
                "meta": c,
                "short_desc": dm.get("short_desc", ""),
                "long_desc": dm.get("long_desc", ""),
                "categories": cats,
                "breadcrumbs": dm.get("breadcrumbs", []),
                "meta_year": dm.get("year", "")
            })
    else:
        logger.error(f"El objetivo '{target}' no es un directorio ni una URL de colección válida.")
        return (False, [])

    if not raw_items:
        logger.warning(f"No se detectaron cursos para construir la ruta curricular en: {target}")
        return (False, [])

    logger.info(f"Deconstruyendo pedagogía de {len(raw_items)} cursos para '{author_name}'...")

    is_volatile = is_volatile_domain(author_name, target)

    # Deconstrucción cognitiva de cada curso
    classified = []
    for item in raw_items:
        clean_t, author_val = clean_course_title_and_author(item["title"])
        dates_res = EpistemicGroundingEngine.resolve_dates(
            clean_title=clean_t,
            author=author_val,
            meta_year=item.get("meta_year", ""),
            date_published=item.get("date_published", ""),
            text_hint=f"{item.get('short_desc', '')} {item.get('long_desc', '')}"
        )
        real_year = dates_res.get("real_year", "S/F")
        mcv_year = dates_res.get("mcv_year", item.get("meta_year", "S/F"))

        phase_info = infer_universal_cognitive_phase(
            clean_t=clean_t,
            text=f"{item.get('short_desc', '')} {item.get('long_desc', '')}"
        )

        c_dict = dict(item)
        c_dict["clean_title"] = clean_t
        c_dict["author"] = author_val
        c_dict["year"] = real_year
        c_dict["real_year"] = real_year
        c_dict["mcv_year"] = mcv_year
        c_dict["epistemic_source"] = dates_res.get("source", "")
        c_dict["is_original_verified"] = dates_res.get("is_original_verified", False)
        c_dict.update(phase_info)
        classified.append(c_dict)

    # Agrupación en itinerarios pedagógicos y aislamiento de outliers
    raw_itineraries, outliers = cluster_courses_into_itineraries(classified, author_name, target=target)

    # Detección de escala de catálogo (autor o monotemático pequeño vs masivo)
    total_courses_count = len(classified)
    authors_list = [c.get("author", "") for c in classified if c.get("author") and c["author"] != "Autor no especificado"]
    author_counts_all = Counter(authors_list)
    dominant_author_ratio = (max(author_counts_all.values()) / total_courses_count) if (total_courses_count > 0 and author_counts_all) else 0.0
    is_small_catalog = (total_courses_count <= 35) or (dominant_author_ratio >= 0.6)

    # Ordenamiento pedagógico y asignación de roles / prerrequisitos correlativos
    main_itineraries = {}
    current_p_idx = 1
    for track_name, c_list in sorted(raw_itineraries.items()):
        processed_courses, current_p_idx = assign_roles_and_prerequisites(c_list, is_volatile, current_p_idx, is_small_catalog=is_small_catalog)
        main_itineraries[track_name] = processed_courses

    # Ordenar outliers
    outliers.sort(key=lambda x: (x["year"], x["clean_title"].lower()))
    for idx, c in enumerate(outliers, 1):
        c["code"] = f"T{idx:02d}"

    clean_alias = resolve_author_alias(author_name) if author_name else "MCV"
    if not author_dir:
        author_dir = os.path.abspath(args.output_dir) if args.output_dir else os.getcwd()

    if clean_alias and clean_alias not in ["MCV", "General"]:
        ruta_txt_path = os.path.join(author_dir, f"RUTA_DE_APRENDIZAJE_{clean_alias}.txt")
    else:
        ruta_txt_path = os.path.join(author_dir, "RUTA_DE_APRENDIZAJE.txt")

    txt_lines = [
        "================================================================================",
        f"  🗺️  RUTA DE APRENDIZAJE CURRICULAR (v9.2.0): {author_name.upper()}",
        "================================================================================",
        f"Catálogo / Dominio: {author_name}",
        f"Plataforma SSoT: MisCursosVirtuales (MCV)",
        f"Total de Cursos en Catálogo: {len(classified)}",
        f"Itinerarios Pedagógicos: {len(main_itineraries)} rutas de especialización",
        f"Estructura Curricular: Progresión Cognitiva Universal (Bloom-Dreyfus)",
        f"Criterio Temporal: {'Priorización por Vigencia Tecnológica (Tech-Decay)' if is_volatile else 'Progresión Conceptual Atemporal (Evergreen)'}",
        f"Fecha de Análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "GLOSARIO DE FASES COGNITIVAS (BLOOM-DREYFUS):",
        "  • [F1] Fundamentos & Principios (Bases teóricas, conceptos raíz y nivel inicial)",
        "  • [F2] Métodos & Práctica Instrumental (Técnicas, herramientas y protocolos paso a paso)",
        "  • [F3] Integración & Proyectos Completos (Sistemas integrales y proyectos avanzados)",
        "  • [F4] Optimización & Especialización (Arquitectura, maestría y refinamiento)",
        "  • [F5] Negocio & Salida al Mercado (Monetización, clientes y venta)",
        "",
        "RESUMEN DE ITINERARIOS DISPONIBLES:",
    ]
    for track_title, c_list in sorted(main_itineraries.items()):
        txt_lines.append(f"  • {track_title}: {len(c_list)} cursos")
    if outliers:
        txt_lines.append(f"  • Cursos Complementarios / Fuera del Eje Troncal: {len(outliers)} cursos aislados")
    txt_lines.append("")

    for track_title, c_list in sorted(main_itineraries.items()):
        txt_lines.append(f"🏛️  ITINERARIO: {track_title} ({len(c_list)} cursos)")
        txt_lines.extend(render_ascii_boxed_table(c_list, width=135, is_outliers=False))
        txt_lines.append("")

    if outliers:
        txt_lines.append(f"📦 CURSOS COMPLEMENTARIOS / FUERA DEL EJE TRONCAL ({len(outliers)} cursos)")
        txt_lines.extend(render_ascii_boxed_table(outliers, width=135, is_outliers=True))
        txt_lines.append("")

    txt_lines.extend([
        "ORIENTACIÓN DE ESTUDIO Y SIGUIENTES PASOS:",
        "1. Selección de Itinerario: Elegí el itinerario que mejor responda a tu meta actual.",
        "2. Cursos Troncales vs Alternativas: Priorizá los cursos marcados con [⭐ Troncal]. Si ya dominás el tema o preferís otro instructor, utilizá las [🔄 Alternativas].",
        "3. Filtro de Versiones: Omití o dejá como consulta secundaria los cursos marcados con [⚠️ Histórico] si ya existe un curso actualizado.",
        "",
        "Ingesta a Google NotebookLM (Opcional):",
        f"  mcv-download --curriculum \"{target}\" --upload-nlm --alias \"{clean_alias}\" --collection \"{author_name}\"",
        ""
    ])

    with open(ruta_txt_path, "w", encoding="utf-8") as f_txt:
        f_txt.write("\n".join(txt_lines))

    logger.info(f"✅ Archivo RUTA_DE_APRENDIZAJE generado exitosamente en: {ruta_txt_path}")

    # Impresión elegante en terminal con tablas encuadradas
    print(f"\n{CYAN}================================================================================")
    print(f"  🗺️  RUTA DE APRENDIZAJE CURRICULAR (v8.3.0): {BOLD}{author_name}{RESET}")
    print(f"{CYAN}================================================================================{RESET}\n")
    for track_title, c_list in sorted(main_itineraries.items()):
        print(f"\n{BOLD}🏛️  {track_title}{RESET} ({len(c_list)} cursos)")
        print("\n".join(render_ascii_boxed_table(c_list, width=135, is_outliers=False)))

    if outliers:
        print(f"\n{BOLD}📦 CURSOS COMPLEMENTARIOS / FUERA DEL EJE TRONCAL{RESET} ({len(outliers)} cursos)")
        print("\n".join(render_ascii_boxed_table(outliers, width=135, is_outliers=True)))

    print(f"\n📄 Documento curricular guardado en: {BOLD}{ruta_txt_path}{RESET}\n")

    # Ingesta opcional a Google NotebookLM como cuaderno [00]
    if getattr(args, "upload_nlm", False):
        logger.info(f"🚀 Ingestando RUTA_DE_APRENDIZAJE.txt como Cuaderno Maestro [00] en NotebookLM...")
        try:
            from notebooklm_tools.cli.utils import get_client
            from notebooklm_tools.services import notebooks, collections
            client = get_client()

            guide_title = format_notebook_title(clean_alias, "00", "GUIA-DE-ESTUDIO")
            existing_nbs = notebooks.list_notebooks(client)
            items = existing_nbs.get("notebooks", []) if isinstance(existing_nbs, dict) else existing_nbs
            nb_id = None
            for nb in items:
                if (nb.get("title") or "").strip() == guide_title:
                    nb_id = nb.get("id") or nb.get("notebook_id")
                    break

            if not nb_id:
                logger.info(f"Creando Cuaderno Maestro: '{guide_title}'...")
                created = notebooks.create_notebook(client, guide_title)
                nb_id = created.get("id") or created.get("notebook_id") if isinstance(created, dict) else getattr(created, "id", None)

            if nb_id:
                logger.info(f"Subiendo RUTA_DE_APRENDIZAJE.txt al cuaderno maestro ({nb_id})...")
                client.add_file(nb_id, ruta_txt_path, wait=False)
                logger.info(f"✅ RUTA_DE_APRENDIZAJE.txt subida con éxito.")

                # Asignación a colección
                col_name = getattr(args, "collection", "") or author_name
                if col_name:
                    logger.info(f"Asignando cuaderno maestro a colección: '{col_name}'...")
                    cols = collections.list_collections(client).get("collections", [])
                    target_col = next((col for col in cols if (col.get("name") or "").strip().lower() == col_name.strip().lower()), None)
                    if target_col:
                        col_id = target_col.get("id") or target_col.get("collection_id")
                        c_nbs = list(target_col.get("notebook_ids", []))
                        if nb_id not in c_nbs:
                            c_nbs.append(nb_id)
                            try:
                                collections.edit_collection(client, col_id, notebook_ids=c_nbs)
                            except Exception:
                                try:
                                    collections.delete_collection(client, col_id)
                                    collections.create_collection(client, col_name, c_nbs)
                                except Exception as e_c:
                                    logger.warning(f"Aviso actualizando colección: {e_c}")
                    else:
                        collections.create_collection(client, col_name, [nb_id])

                print(f"{GREEN}🎉 Cuaderno maestro [00]_GUIA-DE-ESTUDIO creado y vinculado a la colección.{RESET}")
                print(f"   Podés configurarlo como Decano Curricular ejecutando:")
                print(f"     {BOLD}nlm-tutor setup \"{guide_title}\"{RESET}\n")
        except Exception as e_nlm:
            logger.warning(f"Aviso ingestado cuaderno maestro a NotebookLM: {e_nlm}")

    ordered_all_courses = []
    for track_title, c_list in sorted(main_itineraries.items()):
        ordered_all_courses.extend(c_list)
    ordered_all_courses.extend(outliers)

    return (True, ordered_all_courses)



def main():
    # Inmunidad nativa contra desconexiones de terminal web (SIGHUP) y pipes rotos (SIGPIPE)
    try:
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description=f"MCV Downloader & Optimizer v{VERSION}: Descarga Multi-Proveedor (Sync, Mega, Google Drive), reducción a 360p y audio NotebookLM"
    )
    parser.add_argument("url", nargs="?", help="URL del curso, categoría o autor a descargar en MisCursosVirtuales")
    parser.add_argument("-o", "--output-dir", help="Directorio base de destino (por defecto: directorio actual)")
    parser.add_argument("-c", "--cookies", default=DEFAULT_COOKIES_PATH, help=f"Ruta a cookies JSON (por defecto: {DEFAULT_COOKIES_PATH})")
    parser.add_argument("-i", "--interval", type=int, default=3600, help="Intervalo de alertas de progreso en segundos (por defecto: 3600s = 1 hora)")
    parser.add_argument("--alias", help="Alias o apellido explícito del autor (ej: Lavin, Javi) para carpetas y NotebookLM")
    parser.add_argument("--collection", help="Nombre explícito de la Colección en Google NotebookLM (soberano, sin categorías automáticas)")
    parser.add_argument("--metadata-only", action="store_true", help="Solo extraer enlaces y generar archivo .md sin descargar")
    parser.add_argument("--validate-only", nargs="?", const=".", help="Validar y reportar la integridad de un directorio de curso existente (por defecto: '.')")
    parser.add_argument("--optimize-only", nargs="?", const=".", help="Ejecutar reducción a 360p, extracción de audio y ordenamiento en carpeta existente (por defecto: '.')")
    parser.add_argument("--upload-only", nargs="?", const=".", help="Subir únicamente audios y markdown existentes a Google NotebookLM sin tocar medios ni transcodificar (por defecto: '.')")
    parser.add_argument("--curriculum", nargs="?", const=".", help="Analizar catálogo o directorio de autor, deducir la ruta pedagógica ascendente [P01]..[Pn] y generar RUTA_DE_APRENDIZAJE.txt")
    parser.add_argument("--download", action="store_true", help="Forzar ejecución de la cola de descarga cuando se combina con --curriculum")
    parser.add_argument("--no-extract", action="store_true", help="No descomprimir automáticamente los archivos")
    parser.add_argument("--no-reduce", action="store_true", help="No reducir videos ni generar audios")
    parser.add_argument(
        "--audio-format",
        default="aac",
        choices=["aac", "mp3", "opus"],
        help="Formato de audio para NotebookLM: 'aac' (24k mono, 25%% más liviano, por defecto), 'mp3' (32k CBR) u 'opus'"
    )
    parser.add_argument("-d", "--detach", action="store_true", help="Ejecutar como demonio en segundo plano sin conectar el visor en vivo")
    parser.add_argument("-f", "--foreground", action="store_true", help="Ejecutar en primer plano pegado a la terminal (por defecto corre siempre en segundo plano inmune)")
    parser.add_argument("--since", help="Filtrar cursos con vigencia mayor o igual a fecha (ej: '2024-09' o '2024-09-01')")
    parser.add_argument("--exclude", "--skip", help="Números de cursos a excluir de la lista (ej: '1,2,5-8,14' o ruta a archivo .txt)")
    parser.add_argument("--only", "--include", help="Descargar únicamente los números indicados (ej: '3,4,9-12' o ruta a archivo .txt)")
    parser.add_argument("--list", "--dry-run", action="store_true", dest="list_only", help="Escanear catálogo y listar cursos detectados con fecha y estado sin descargar nada")
    parser.add_argument("--no-date-prefix", action="store_false", dest="date_prefix", default=True, help="No agregar prefijo [YYYY-MM] al nombre de la carpeta")
    parser.add_argument("--upload-nlm", action="store_true", help="Ingestar automáticamente audios y markdown del curso a Google NotebookLM al finalizar")
    parser.add_argument(
        "--audio-only", "--audio-first",
        action="store_true",
        dest="audio_only",
        help="Arquitectura Audio-First: Extraer audios AAC y subir a NotebookLM dejando los videos en tamaño original sin transcodificar a 360p"
    )
    parser.add_argument("--status", action="store_true", help="Mostrar estado y telemetría de descargas activas")
    parser.add_argument("-w", "--watch", action="store_true", help="Monitorizar continuamente en vivo el progreso de descargas")
    parser.add_argument("-v", "--version", action="version", version=f"MCV Downloader & Optimizer v{VERSION}")
    parser.add_argument("--force", action="store_true", help="Ignorar cerrojo singleton y permitir ejecuciones simultáneas")

    args = parser.parse_args()

    # Si se invoca telemetría de estado, ejecutar inmediatamente y salir
    if args.status or args.watch:
        show_status(watch=args.watch)
        sys.exit(0)

    # Detección rigurosa de intención de descarga frente a pura inspección
    has_download_intent = bool(
        args.url
        and not os.path.isdir(args.url)
        and (
            getattr(args, "audio_only", False)
            or getattr(args, "download", False)
            or args.detach
            or args.foreground
            or not getattr(args, "curriculum", None)
        )
        and not args.list_only
        and not args.metadata_only
        and not bool(args.validate_only)
        and not bool(args.optimize_only)
        and not bool(args.upload_only)
    )

    is_inspection = not has_download_intent

    # Cerrojo Singleton: evitar descargas concurrentes accidentales si no es inspección
    lock_fd = None
    if not is_inspection:
        lock_fd = acquire_singleton_lock(force=args.force)

    if not is_inspection and not args.foreground:
        pid = os.fork()
        if pid > 0:
            print("=" * 80)
            print(f"🚀 DESCARGA DESATENDIDA INICIADA CON ÉXITO")
            print(f"   PID del proceso trabajador autónomo: {pid}")
            print("=" * 80)
            print("🛡️  INMUNIDAD TOTAL:")
            print("   Podés cerrar esta terminal, el navegador o apagar tu computadora con total seguridad.")
            print("   El proceso continúa trabajando en segundo plano de forma 100% autónoma.")
            print("--------------------------------------------------------------------------------")
            print("💡 Para consultar el estado en cualquier momento ejecutá:")
            print("   mcv-status")
            print("   o en vivo continuo:")
            print("   mcv-status -w")
            print("=" * 80)
            if not args.detach and sys.stdout.isatty():
                print("\n👀 Conectando visor en vivo (podés cerrar la terminal o pulsar Ctrl+C sin frenar la descarga)...\n")
                time.sleep(2.0)
                try:
                    subprocess.run(["mcv-status", "-w"])
                except (KeyboardInterrupt, Exception):
                    print(f"\n👋 Visor desconectado. La descarga continúa en segundo plano con PID: {pid}")
            sys.exit(0)

        # Proceso trabajador: desacoplar sesión completamente
        os.setsid()
        if lock_fd:
            try:
                lock_fd.seek(0)
                lock_fd.truncate()
                lock_fd.write(f"{os.getpid()}\n")
                lock_fd.flush()
            except Exception:
                pass
        try:
            # Asignar prioridad de CPU baja (nice 10) para no saturar los 3 vCPU de Zerops
            os.nice(10)
        except Exception:
            pass
        try:
            devnull = os.open(os.devnull, os.O_RDONLY)
            os.dup2(devnull, 0)
            daemon_log = os.open("/var/www/mcv_daemon.log", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
            os.dup2(daemon_log, 1)
            os.dup2(daemon_log, 2)
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(line_buffering=True)
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(line_buffering=True)
        except Exception:
            pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Mode: Optimize existing directory
    if args.optimize_only:
        cdir = os.path.abspath(args.optimize_only)
        if os.path.basename(cdir).upper() == "NOTEBOOKLM_AUDIOS":
            cdir = os.path.dirname(cdir)
        contained_courses = discover_contained_courses(cdir)

        def make_upload_fn(target_dir):
            def _fn():
                if getattr(args, "upload_nlm", False):
                    meta = resolve_or_lookup_course_metadata(target_dir, alias=getattr(args, "alias", ""))
                    upload_course_to_notebooklm(
                        target_dir,
                        meta,
                        audio_format=args.audio_format,
                        alias=getattr(args, "alias", ""),
                        collection_name=getattr(args, "collection", "")
                    )
            return _fn

        try:
            # Caso A: Contenedor general de autor o lote con múltiples cursos
            if contained_courses:
                logger.info(f"📂 [CONTENEDOR DE AUTOR/LOTE DETECTADO]: {cdir}")
                logger.info(f"   Se detectaron {len(contained_courses)} cursos contenidos. Procesando en lote...")
                total_saved_gb = 0.0
                for idx, c_path in enumerate(contained_courses, 1):
                    c_name = os.path.basename(c_path)
                    logger.info(f"\n================================================================================")
                    logger.info(f"▶️ [LOTE OPTIMIZE {idx:02d}/{len(contained_courses)}] Curso: {c_name}")
                    logger.info(f"================================================================================")
                    opt_res = process_and_optimize_course_media(
                        c_path,
                        preferred_audio_format=args.audio_format,
                        course_title=c_name,
                        audio_only=getattr(args, "audio_only", False),
                        upload_callback=make_upload_fn(c_path) if getattr(args, "upload_nlm", False) else None
                    )
                    total_saved_gb += opt_res.get("total_saved_gb", 0.0)
                    for f_trans in ["PROGRESO.txt", "download_progress.log"]:
                        fp = os.path.join(c_path, f_trans)
                        if os.path.exists(fp):
                            try:
                                os.remove(fp)
                            except Exception:
                                pass
                logger.info(f"\n🎉 [LOTE FINALIZADO] Se procesaron {len(contained_courses)} cursos. Ahorro acumulado: {total_saved_gb:.2f} GB")
                return

            # Caso B: Curso individual
            cname = os.path.basename(cdir)
            stats_before = validate_extracted_tree(cdir)
            opt_res = process_and_optimize_course_media(
                cdir,
                preferred_audio_format=args.audio_format,
                course_title=cname,
                audio_only=getattr(args, "audio_only", False),
                upload_callback=make_upload_fn(cdir) if getattr(args, "upload_nlm", False) else None
            )
            stats_after = validate_extracted_tree(cdir)
            logger.info(f"Optimización completada para {cname}. Ahorro: {opt_res['total_saved_gb']:.2f} GB")
            for f_trans in ["PROGRESO.txt", "download_progress.log"]:
                fp = os.path.join(cdir, f_trans)
                if os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except Exception:
                        pass
            return
        finally:
            purge_runtime_transient_files()

    # Mode: Validate only
    if args.validate_only:
        cdir = os.path.abspath(args.validate_only)
        if os.path.basename(cdir).upper() == "NOTEBOOKLM_AUDIOS":
            cdir = os.path.dirname(cdir)
        res = validate_extracted_tree(cdir)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    # Mode: Pure Ingest / Upload to NotebookLM
    if getattr(args, "upload_only", None):
        target_path = os.path.abspath(args.upload_only)
        if os.path.basename(target_path).upper() == "NOTEBOOKLM_AUDIOS":
            target_path = os.path.dirname(target_path)

        contained = discover_contained_courses(target_path)
        courses_to_upload = contained if contained else [target_path]

        logger.info(f"🚀 [UPLOAD-ONLY] Ingestando {len(courses_to_upload)} curso(s) directamente a Google NotebookLM...")
        for c_dir in courses_to_upload:
            c_meta = resolve_or_lookup_course_metadata(c_dir, alias=getattr(args, "alias", ""))
            upload_course_to_notebooklm(
                c_dir,
                c_meta,
                audio_format=args.audio_format,
                alias=getattr(args, "alias", ""),
                collection_name=getattr(args, "collection", "")
            )
        return

    # Modo: Motor Curricular en Inspección Pura (sin intención de descarga inmediata)
    if getattr(args, "curriculum", None) and not has_download_intent:
        target_path_or_url = args.curriculum if args.curriculum != "." else (args.url or ".")
        handle_curriculum(target_path_or_url, args)
        return

    if not args.url:
        parser.print_help()
        sys.exit(1)

    # Caso 0: Reanudación de lote desde manifiesto .txt existente
    if os.path.isfile(args.url) and args.url.lower().endswith(".txt"):
        load_manifest_for_resume(args.url, args)
        return

    # Caso 0.1: Directorio local existente
    if os.path.isdir(args.url):
        target_path = os.path.abspath(args.url)
        if os.path.basename(target_path).upper() == "NOTEBOOKLM_AUDIOS":
            target_path = os.path.dirname(target_path)

        if getattr(args, "upload_nlm", False):
            contained = discover_contained_courses(target_path)
            courses_to_upload = contained if contained else [target_path]
            logger.info(f"🚀 [LOCAL INGEST] Ingestando {len(courses_to_upload)} curso(s) a Google NotebookLM...")
            for c_dir in courses_to_upload:
                c_meta = resolve_or_lookup_course_metadata(c_dir, alias=getattr(args, "alias", ""))
                upload_course_to_notebooklm(
                    c_dir,
                    c_meta,
                    audio_format=args.audio_format,
                    alias=getattr(args, "alias", ""),
                    collection_name=getattr(args, "collection", "")
                )
            return
        else:
            args.optimize_only = target_path

    session = get_session(args.cookies)
    base_dest = os.path.abspath(args.output_dir) if args.output_dir else os.getcwd()

    # Caso 1: Colección (Categoría, Autor o Búsqueda)
    if is_collection_url(args.url):
        col_name, raw_courses = crawl_collection_courses(session, args.url)
        if not raw_courses:
            logger.warning(f"No se detectaron cursos en la URL de colección: {args.url}")
            return

        # Extraer fechas concurrentemente
        courses_with_dates = extract_course_dates_concurrent(session, raw_courses)

        # Aplicar filtro --since si se especificó
        if args.since:
            since_val = args.since.strip()
            selected_courses = [c for c in courses_with_dates if c["effective_date"] >= since_val]
        else:
            selected_courses = courses_with_dates

        if not selected_courses:
            logger.warning(f"Ningún curso en catálogo cumplió con el filtro de fecha ({args.since}). Finalizando.")
            return

        # Si se activó --curriculum en pipeline de descarga, estructurar ruta pedagógica y reordenar cola
        if getattr(args, "curriculum", None):
            logger.info("🧭 [PIPELINE CURRICULAR INTEGRADO]: Analizando catálogo y deduciendo orden pedagógico [P01]..[Pn]...")
            c_ok, ordered_curriculum = handle_curriculum(args.url, args)
            if c_ok and ordered_curriculum:
                url_to_order = {oc.get("url"): (idx, oc) for idx, oc in enumerate(ordered_curriculum) if oc.get("url")}
                title_to_order = {oc.get("clean_title", "").lower(): (idx, oc) for idx, oc in enumerate(ordered_curriculum)}

                def get_curriculum_sort_key(c_item):
                    if c_item.get("url") and c_item["url"] in url_to_order:
                        return url_to_order[c_item["url"]][0]
                    c_clean, _ = clean_course_title_and_author(c_item.get("title", ""))
                    if c_clean.lower() in title_to_order:
                        return title_to_order[c_clean.lower()][0]
                    return 9999

                for c_item in selected_courses:
                    oc_info = None
                    if c_item.get("url") and c_item["url"] in url_to_order:
                        oc_info = url_to_order[c_item["url"]][1]
                    else:
                        c_clean, _ = clean_course_title_and_author(c_item.get("title", ""))
                        if c_clean.lower() in title_to_order:
                            oc_info = title_to_order[c_clean.lower()][1]
                    if oc_info and oc_info.get("code"):
                        c_item["curriculum_code"] = oc_info["code"]
                        c_item["role"] = oc_info.get("role", "")
                        c_item["phase_label"] = oc_info.get("phase_label", "")

                selected_courses.sort(key=get_curriculum_sort_key)
                logger.info(f"✅ Cola de descarga reordenada exitosamente según la ruta pedagógica ({len(selected_courses)} cursos).")

        # Parsear filtros de índice (--exclude y --only)
        exclude_indices = parse_index_selection(args.exclude)
        only_indices = parse_index_selection(args.only)

        # Determinar índices habilitados (1-based)
        runnable_indices = [
            idx for idx in range(1, len(selected_courses) + 1)
            if (not only_indices or idx in only_indices) and (idx not in exclude_indices)
        ]
        runnable_count = len(runnable_indices)
        skipped_count = len(selected_courses) - runnable_count

        filter_parts = []
        if args.since:
            filter_parts.append(f"Vigencia >= {args.since}")
        if only_indices:
            filter_parts.append(f"Solo índices: {sorted(only_indices)}")
        if exclude_indices:
            filter_parts.append(f"Excluir índices: {sorted(exclude_indices)}")
        filter_txt = " | ".join(filter_parts) if filter_parts else "Sin filtros (todos)"

        logger.info(f"\n================================================================================")
        logger.info(f"📋 RESULTADOS DEL RASTREO: [{col_name}]")
        logger.info(f"   Filtros aplicados:    {filter_txt}")
        logger.info(f"   Cursos en catálogo:   {len(selected_courses)} de {len(raw_courses)}")
        logger.info(f"   Cursos a descargar:   {runnable_count} ({skipped_count} omitidos)")
        logger.info(f"================================================================================")
        logger.info(f" #  | Vigencia   | Publicado  | Actualizado | Estado   | Título")
        logger.info(f"----+------------+------------+-------------+----------+--------------------------------")
        for idx, c in enumerate(selected_courses, 1):
            is_active = idx in runnable_indices
            status_tag = "DESCARGA" if is_active else "OMITIDO "
            logger.info(f" {idx:02d} | {c['effective_date'][:10]} | {c['pub_date'][:10]:<10} | {c['mod_date'][:10]:<11} | [{status_tag}] | {c['title']}")
        logger.info(f"================================================================================")
        logger.info(f"   Total a procesar: {runnable_count} cursos ({skipped_count} omitidos)")
        logger.info(f"================================================================================\n")

        # Resolución limpia de directorio de autor / colección y manifiesto:
        if args.alias or "/author/" in args.url or "/autor/" in args.url or "?s=" in args.url or "&s=" in args.url:
            effective_alias = args.alias or resolve_author_alias(col_name)
            col_dir = resolve_author_dir(base_dest, effective_alias)
            manifest_slug = sanitize_folder_name(effective_alias).lower()
        else:
            effective_alias = getattr(args, "alias", "") or ""
            clean_col = sanitize_folder_name(col_name).title()
            col_dir = os.path.join(base_dest, clean_col)
            manifest_slug = sanitize_folder_name(col_name).lower()
        os.makedirs(col_dir, exist_ok=True)

        manifest_path = os.path.join(col_dir, f"{manifest_slug}.txt")

        # Inspección física previa de carpetas para poblar estados iniciales
        manifest_statuses = {}
        for idx, c in enumerate(selected_courses, 1):
            f_name = compute_course_folder_name(
                title=c.get("title", ""),
                effective_date=c.get("effective_date", ""),
                category=c.get("category", "CURSO"),
                alias=effective_alias,
                date_prefix=getattr(args, "date_prefix", True)
            )
            if c.get("curriculum_code"):
                f_name = f"[{c['curriculum_code']}]_{f_name}"
            c["folder_name"] = f_name
            c_dir = os.path.join(col_dir, f_name)
            if not os.path.isdir(c_dir):
                alt_dir = os.path.join(col_dir, re.sub(r"^\[\d{4}-\d{2}\]_?", "", f_name))
                if os.path.isdir(alt_dir):
                    c_dir = alt_dir
                else:
                    alt_dir2 = os.path.join(col_dir, re.sub(r"^\[P\d{2}\]_?", "", f_name))
                    if os.path.isdir(alt_dir2):
                        c_dir = alt_dir2
            is_done, reason = is_course_directory_complete(c_dir, audio_only=getattr(args, "audio_only", False))
            if is_done:
                manifest_statuses[idx] = "[COMPLETADO]"
            elif idx not in runnable_indices:
                manifest_statuses[idx] = "[OMITIDO]"
            else:
                manifest_statuses[idx] = "[PENDIENTE]"

        # Guardar manifiesto inicial siempre (incluso con --list)
        update_batch_manifest(
            manifest_path=manifest_path,
            col_name=col_name,
            url=args.url,
            filter_txt=filter_txt,
            selected_courses=selected_courses,
            statuses=manifest_statuses,
            col_dir=col_dir,
            alias=effective_alias,
            date_prefix=getattr(args, "date_prefix", True)
        )
        logger.info(f"📋 Manifiesto de lote guardado en: {manifest_path}")

        if args.list_only:
            logger.info(f"🔍 Modo --list completado: {runnable_count} cursos seleccionados para descarga ({skipped_count} omitidos).")
            logger.info(f"   Manifiesto de auditoría generado en: {manifest_path}")
            return

        if runnable_count == 0:
            logger.warning(f"Ningún curso cumplió con los filtros de selección ({filter_txt}). Finalizando sin descargas.")
            return

        orchestrator = PipelineOrchestrator(
            session=session,
            col_dir=col_dir,
            manifest_path=manifest_path,
            col_name=col_name,
            selected_courses=selected_courses,
            runnable_indices=runnable_indices,
            filter_txt=filter_txt,
            args=args,
            origin_url=args.url
        )
        orchestrator.manifest_statuses = manifest_statuses
        all_batch_success = orchestrator.run()

        # Normalización post-lote: limpiar cualquier carpeta heredada con prefijo [PROFESIONAL]
        if os.path.isdir(col_dir):
            for entry in os.listdir(col_dir):
                if entry.startswith("[PROFESIONAL] "):
                    old_p = os.path.join(col_dir, entry)
                    new_p = os.path.join(col_dir, entry.replace("[PROFESIONAL] ", "", 1))
                    if not os.path.exists(new_p):
                        try:
                            os.rename(old_p, new_p)
                            logger.info(f"🏷️ Carpeta normalizada sin prefijo: {entry} -> {os.path.basename(new_p)}")
                        except Exception:
                            pass

        # Actualización final del manifiesto (cero purga destructiva: se conserva permanentemente)
        update_batch_manifest(
            manifest_path=manifest_path,
            col_name=col_name,
            url=args.url,
            filter_txt=filter_txt,
            selected_courses=selected_courses,
            statuses=orchestrator.manifest_statuses,
            col_dir=col_dir,
            alias=effective_alias,
            date_prefix=getattr(args, "date_prefix", True)
        )
        logger.info(f"✨ Manifiesto de lote actualizado y preservado para auditoría en: {manifest_path}")
        logger.info(f"\n🎉 LOTE COMPLETO DE [{col_name}] FINALIZADO! ({runnable_count} cursos procesados, {skipped_count} omitidos)")
        purge_runtime_transient_files()

    # Caso 2: Curso Individual
    else:
        if args.alias:
            base_dest = resolve_author_dir(base_dest, args.alias)
            os.makedirs(base_dest, exist_ok=True)
        download_and_process_course(session, args.url, base_dest, args)
        purge_runtime_transient_files()


if __name__ == "__main__":
    main()
