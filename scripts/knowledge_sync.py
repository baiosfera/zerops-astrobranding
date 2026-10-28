#!/usr/bin/env python3
"""
=============================================================================
🏛️ MOTOR SOBERANO DE INGESTA DINÁMICA & MICRO-CLASIFICACIÓN SSoT (v2.0 - HARDENED)
=============================================================================
Gobernanza: 00-SUPREME-DIRECTIVE.md (v8.5) · CoHaLo Engineering & Positive Guidance
Ubicación Canónica: /var/www/zerops-astrobranding/scripts/knowledge_sync.py
Symlink Global: /usr/local/bin/knowledge-sync

Características Principales:
1. Micro-Clasificación Jerárquica Bottom-Up (Clase -> Módulo -> Curso -> Sigla).
2. Correlación de Documentos Hermanos (Peer-Docs) con Normalización Unicode NFC:
   Elimina falsos huérfanos convirtiendo videos con documento homónimo en 'video_residual'.
3. 11 Especialidades Temáticas Soberanas alineadas a Google NotebookLM (Gemini Notebook).
4. Dashboard CLI Enriquecido con métricas de frugalidad, traza de asignación y next steps.
5. Frugalidad SHARED: Prevención de OOM, timeout en subprocesses, limpieza de /tmp y
   escritura atómica de manifiestos sobre FUSE rclone.
=============================================================================
"""

import os
import sys
import re
import json
import time
import uuid
import glob
import random
import socket
import hashlib
import argparse
import tempfile
import unicodedata
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict

# Inyectar site-packages de uv notebooklm-mcp-cli si existe
UV_SITE_PACKAGES = "/home/zerops/.local/share/uv/tools/notebooklm-mcp-cli/lib/python3.12/site-packages"
if os.path.isdir(UV_SITE_PACKAGES) and UV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, UV_SITE_PACKAGES)


# =============================================================================
# 1. Componente: Limpiador y Normalizador de Subtítulos SRT/VTT en Memoria
# =============================================================================
class SubtitlesCleaner:
    """Normaliza y despoja códigos de tiempo de archivos .srt y .vtt."""

    TIMECODE_SRT = re.compile(
        r"^\d{1,5}\r?\n\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}.*$",
        re.MULTILINE,
    )
    TIMECODE_VTT = re.compile(
        r"^\d{2}:\d{2}(?::\d{2})?[,\.]\d{3}\s*-->\s*\d{2}:\d{2}(?::\d{2})?[,\.]\d{3}.*$",
        re.MULTILINE,
    )
    TAG_HTML = re.compile(r"<[^>]+>")
    HEADER_VTT = re.compile(r"^WEBVTT.*?\n\n", re.DOTALL | re.IGNORECASE)

    @classmethod
    def clean(cls, raw_content: str) -> str:
        """Remueve numeración secuencial, marcas de tiempo y etiquetas de formateo."""
        if not raw_content:
            return ""

        content = cls.HEADER_VTT.sub("", raw_content)
        content = cls.TIMECODE_SRT.sub("", content)
        content = cls.TIMECODE_VTT.sub("", content)
        content = cls.TAG_HTML.sub("", content)

        lines = []
        last_line = ""
        for line in content.splitlines():
            line_str = line.strip()
            if not line_str or line_str.isdigit():
                continue
            if line_str != last_line:
                lines.append(line_str)
                last_line = line_str

        return "\n".join(lines)


# =============================================================================
# 2. Componente: Huella Digital Sintética (Metadata Fingerprint)
# =============================================================================
class MetadataFingerprint:
    """Genera hash determinista sin lectura de payload para proteger cuota de I/O."""

    @staticmethod
    def compute(file_path: str, base_dir: str = "/var/www/baiosfera") -> str:
        """Deriva el hash desde ruta relativa, tamaño exacto en bytes y mtime POSIX."""
        try:
            rel_path = os.path.relpath(file_path, base_dir)
            st = os.stat(file_path)
            raw_key = f"{rel_path}:{st.st_size}:{int(st.st_mtime)}"
            return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        except Exception:
            raw_key = f"{file_path}:{time.time()}"
            return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_from_stat(rel_path: str, size_bytes: int, mtime_int: int) -> str:
        """Genera hash sin re-invocar os.stat si los metadatos ya fueron leídos."""
        raw_key = f"{rel_path}:{size_bytes}:{mtime_int}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


# =============================================================================
# 3. Componente: Extractor de Audio FFmpeg con Timeout y Limpieza de /tmp
# =============================================================================
class AudioExtractor:
    """Extrae audio ligero en formato AAC a 64 kbps de videos huérfanos reales."""

    @staticmethod
    def extract_aac(video_path: str, output_dir: str = "/tmp/knowledge_audio_cache") -> str:
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", base_name)
        path_hash = hashlib.md5(video_path.encode("utf-8")).hexdigest()[:8]
        output_file = os.path.join(output_dir, f"{clean_name}_{path_hash}.aac")

        if os.path.exists(output_file) and os.path.getsize(output_file) > 1024:
            return output_file

        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-c:a", "aac", "-b:a", "64k", "-ar", "24000",
            output_file
        ]
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=300,  # 5 minutos máximo para demuxing
            )
            if res.returncode != 0 or not os.path.exists(output_file):
                raise RuntimeError(f"FFmpeg falló (código {res.returncode}) al procesar: {video_path}")
            return output_file
        except subprocess.TimeoutExpired:
            if os.path.exists(output_file):
                try:
                    os.unlink(output_file)
                except Exception:
                    pass
            raise RuntimeError(f"FFmpeg excedió el tiempo límite (300s) procesando: {video_path}")

    @staticmethod
    def cleanup(file_path: str):
        """Elimina archivo de audio temporal para evitar fugas de disco en /tmp."""
        if file_path and file_path.startswith("/tmp/") and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except Exception:
                pass


# =============================================================================
# 4. Componente: Manifiesto Particionado Append-Only & Estado Atómico
# =============================================================================
class PartitionedManifest:
    """Gestiona el registro de ingesta sin bloqueos POSIX sobre FUSE y consolida clusters."""

    def __init__(self, manifest_dir: Optional[str] = None):
        if manifest_dir:
            self.manifest_dir = manifest_dir
        else:
            primary = "/var/www/baiosfera/.knowledge_manifest"
            fallback = "/var/www/localstorage/.knowledge_manifest"
            self.manifest_dir = primary if os.path.isdir(os.path.dirname(primary)) else fallback

        os.makedirs(self.manifest_dir, exist_ok=True)
        self.hostname = socket.gethostname() or "zcp-local"
        self.session_id = uuid.uuid4().hex[:8]
        self.event_file = os.path.join(
            self.manifest_dir, f"events_{self.hostname}_{self.session_id}.jsonl"
        )

    def record_upload(
        self,
        fingerprint: str,
        relative_path: str,
        notebook_id: str,
        notebook_title: str,
        source_id: str,
        source_type: str,
    ):
        """Registra un evento de subida exitosa de forma append-only."""
        event = {
            "version": "1.2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hostname": self.hostname,
            "fingerprint": fingerprint,
            "relative_path": relative_path,
            "notebook_id": notebook_id,
            "notebook_title": notebook_title,
            "source_id": source_id,
            "source_type": source_type,
        }
        with open(self.event_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def get_uploaded_fingerprints(self) -> Dict[str, Dict[str, Any]]:
        """Lee todos los archivos de eventos y consolida los fingerprints ya procesados."""
        manifest: Dict[str, Dict[str, Any]] = {}
        for event_path in glob.glob(os.path.join(self.manifest_dir, "events_*.jsonl")):
            try:
                with open(event_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            data = json.loads(line)
                            fp = data.get("fingerprint")
                            if fp:
                                manifest[fp] = data
            except Exception:
                continue
        return manifest

    def export_clusters_manifest(self, clusters_data: Dict[str, Any]) -> str:
        """Exporta mapa canónico de clusters de forma atómica para prevenir archivos truncados."""
        manifest_path = os.path.join(self.manifest_dir, "clusters.json")
        dir_name = os.path.dirname(manifest_path)

        # Escritura atómica mediante archivo temporal y reemplazo POSIX
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            json.dump(clusters_data, tf, indent=2, ensure_ascii=False)
            temp_name = tf.name

        os.replace(temp_name, manifest_path)

        # Replicar hacia localstorage si existe
        local_alt = "/var/www/localstorage/.knowledge_manifest"
        if os.path.isdir(local_alt):
            try:
                alt_path = os.path.join(local_alt, "clusters.json")
                with tempfile.NamedTemporaryFile("w", dir=local_alt, delete=False, encoding="utf-8") as tf:
                    json.dump(clusters_data, tf, indent=2, ensure_ascii=False)
                    alt_temp = tf.name
                os.replace(alt_temp, alt_path)
            except Exception:
                pass

        return manifest_path

    def load_clusters_manifest(self) -> Dict[str, Any]:
        """Carga el manifiesto de clusters existente."""
        for path in [
            os.path.join(self.manifest_dir, "clusters.json"),
            "/var/www/localstorage/.knowledge_manifest/clusters.json",
        ]:
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    continue
        return {}


# =============================================================================
# 5. Componente: Clasificador Bottom-Up & Correlación de Documentos Hermanos
# =============================================================================
class CourseScanner:
    """Escanea y micro-clasifica recursos educativos sin agotar memoria ni cuota FUSE."""

    DEFAULT_SEARCH_PATHS = [
        "/var/www/baiosfera/CURSOS/MCV/VIP",
        "/var/www/baiosfera/CURSOS/MCV/BASIC",
        "/var/www/baiosfera/CURSOS/VELOCITYMEDIA",
        "/var/www/baiosfera/DIGITALMARKETER",
        "/var/www/baiosfera/PLATZI/59 CONTENT COPY EMAIL SEO STORYTELLING VENTAS",
        "/var/www/baiosfera/PLATZI/47 GROWTH JOURNEY MKTN PRODUCT",
        "/var/www/baiosfera/PLATZI/33 GRAPHIC THINKING UXUI",
        "/var/www/baiosfera/PLATZI/30 BRANDING MARCAP INVEST",
        "/var/www/baiosfera/PLATZI/14 AI PROMPT",
        "/var/www/baiosfera/PLATZI/04 AUTOM",
        "/var/www/baiosfera/PLATZI/03 ECOM",
    ]

    EXCLUDE_DIRS = {
        "CATEGORIAS", "AUTHOR", "Archivos", "AGY", "0.DWNL",
        "00_START_HERE", "00_START", "00_BIENVENIDA", "Announcements",
        "Live_Calls", "Start_Here_5-Min_Plan", "changelogs", "bienvenidas",
        "onboarding", "community", "comunidad", "avisos", "foro", "foros",
        "recursos_adicionales", "__pycache__", "node_modules", "vendor",
        ".git", ".rclone"
    }

    # 11 Especialidades Soberanas
    THEMATIC_CLUSTERS = {
        "copywriting": [
            "copy", "copywriting", "escritura persuasiva", "titular", "titulares",
            "titulo", "titulos", "gancho", "ganchos", "hook", "hooks", "storytelling",
            "narrativa", "persuasion", "redaccion", "redacción", "headline", "headlines",
            "swipe file", "swipe", "script", "words that sell", "carta de venta", "cartas de venta", "texto persuasivo"
        ],
        "ofertas": [
            "oferta", "ofertas", "precio", "pricing", "hormozi", "grand slam", "value equation",
            "propuesta de valor", "garantia", "garantía", "offer", "offers", "guarantee",
            "bonus", "stack", "bonus stack", "offer stack", "site offers", "irresistible",
            "modelos de negocio", "monetiz", "icp", "ideal customer", "ideal client", "cliente ideal", "avatar"
        ],
        "funnels": [
            "funnel", "funnels", "embudo", "embudos", "checkout", "checkouts",
            "bump", "order bump", "upsell", "downsell", "cvj", "customer value journey",
            "landing", "landing page", "landings", "conversion", "conversiones",
            "optin", "squeeze", "squeeze page", "lead magnet", "vsl", "video sales letter",
            "funnel architecture", "cro", "ab testing", "tripwire", "home page", "homepage"
        ],
        "whatsapp": [
            "whatsapp", "chatbot", "chatbots", "cierre por chat", "mensajeria",
            "mensajería", "conversacional", "conversational commerce", "atencion al cliente",
            "atención al cliente"
        ],
        "email": [
            "email", "correo", "newsletter", "nurture", "secuencia", "secuencias", "listmonk",
            "broadcast", "subject line", "autoresponder", "welcome sequence",
            "re engagement", "entregabilidad", "email marketing", "dmarc", "dkim"
        ],
        "paid_ads": [
            "ads", "pauta", "meta ads", "facebook ads", "fb ads", "instagram ads", "tiktok ads",
            "creativo", "creativos", "trafico", "tráfico", "traffic", "anuncio", "anuncios",
            "velocity", "audiencia", "audiencias", "escalado", "paid media", "media buyer",
            "roas", "ad copy", "google ads", "performance max", "campaign fixer", "campaign", "campaigns"
        ],
        "branding": [
            "brand", "marca", "branding", "identidad", "arquetipo", "arquetipos",
            "posicionamiento", "category of one", "tono de voz", "authority", "reputation",
            "brand guidelines", "marca personal"
        ],
        "ecommerce": [
            "ecom", "ecommerce", "supply chain", "logistica", "logística", "tienda",
            "tiendas online", "dropshipping", "shopify", "woocommerce", "amazon",
            "inventario", "retail", "vender por internet", "catalogo", "catálogo",
            "product page", "product pages", "ficha de producto", "red de valor"
        ],
        "automatizaciones": [
            "autom", "automatizacion", "automatización", "automatizaciones", "automation",
            "automations", "workflow", "workflows", "n8n", "make", "zapier", "rpa",
            "crm", "webhook", "webhooks", "hiperautomatizacion", "no code", "nocode",
            "procesos de marketing"
        ],
        "ia_prompting": [
            "ai prompt", "prompt", "prompts", "prompting", "chatgpt", "midjourney",
            "claude", "agentes ai", "agentes de ia", "ai assistant", "ai assistants",
            "ai engines", "ai engine", "ai systems", "ai system", "ai tools", "gpts",
            "gpt", "gemini", "copilot", "context vault", "llm", "inteligencia artificial",
            "ia para", "ingenieria de prompt", "ingeniería de prompt", "prompt toolkit",
            "ai search", "artificial intelligence"
        ],
        "ux_ui": [
            "uxui", "ux/ui", "ui/ux", "design thinking", "designthinking", "tipografia",
            "tipografía", "manejo del color", "teoria del color", "teoría del color",
            "direccion de arte", "dirección de arte", "composicion visual", "composición visual",
            "accesibilidad", "diseno centrado", "diseño centrado", "arquitectura de informacion",
            "arquitectura de información", "wireframe", "wireframing", "interfaz",
            "interfaces", "ui", "ux"
        ],
    }

    CLUSTER_NOTEBOOK_TITLES = {
        "copywriting": "[ESPECIALIDAD_COPY_TITULARES_Y_GANCHOS]",
        "ofertas": "[ESPECIALIDAD_OFERTAS_Y_PRICING]",
        "funnels": "[ESPECIALIDAD_FUNNELS_CHECKOUTS_Y_BUMPS]",
        "whatsapp": "[ESPECIALIDAD_WHATSAPP_MARKETING_Y_BOTS]",
        "email": "[ESPECIALIDAD_EMAIL_AUTOMATION_Y_NURTURE]",
        "paid_ads": "[ESPECIALIDAD_META_ADS_CREATIVOS_Y_PAUTA]",
        "branding": "[ESPECIALIDAD_BRANDING_Y_POSICIONAMIENTO]",
        "ecommerce": "[ESPECIALIDAD_ECOMMERCE_Y_TIENDAS]",
        "automatizaciones": "[ESPECIALIDAD_AUTOMATIZACIONES_Y_WORKFLOWS]",
        "ia_prompting": "[ESPECIALIDAD_IA_PROMPTING_Y_AGENTES]",
        "ux_ui": "[ESPECIALIDAD_UX_UI_Y_PRODUCTO]",
    }

    # Mapeo prioritario de Siglas de Tracks (Nivel 4 - Prioridad Máxima)
    TRACK_TAGS_MAP = {
        "[ecom]": "ecommerce",
        "03 ecom": "ecommerce",
        "[autom]": "automatizaciones",
        "04 autom": "automatizaciones",
        "[ai]": "ia_prompting",
        "14 ai prompt": "ia_prompting",
        "[prompt]": "ia_prompting",
        "[uxui]": "ux_ui",
        "[designthinking]": "ux_ui",
        "[graphic]": "ux_ui",
        "33 graphic thinking uxui": "ux_ui",
        "[growth]": "funnels",
        "[journey]": "funnels",
        "47 growth journey mktn product": "funnels",
        "[branding]": "branding",
        "30 branding marcap invest": "branding",
        "[ads]": "paid_ads",
        "[pauta]": "paid_ads",
        "[copy]": "copywriting",
        "[email]": "email",
        "[whatsapp]": "whatsapp",
    }

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Normaliza Unicode a NFC, remueve puntuación periférica y dobles espacios."""
        if not text:
            return ""
        norm = unicodedata.normalize("NFC", text).lower()
        norm = re.sub(r"^[\*\-_#\.\s]+", "", norm)
        norm = re.sub(r"[\*\-_#\.\s]+$", "", norm)
        norm = re.sub(r"[_\-\.]+", " ", norm)
        return re.sub(r"\s+", " ", norm).strip()

    @classmethod
    def match_cluster_keywords(cls, text: str) -> Optional[str]:
        """Busca coincidencias exactas por límite de palabra en la matriz de clusters."""
        norm_text = cls.normalize_text(text)
        if not norm_text:
            return None

        # Prioridad de desempate: evaluar clusters más especializados primero
        priority_order = [
            "ia_prompting", "ux_ui", "whatsapp", "email",
            "ecommerce", "automatizaciones", "paid_ads",
            "ofertas", "funnels", "branding", "copywriting"
        ]

        for cluster in priority_order:
            keywords = cls.THEMATIC_CLUSTERS.get(cluster, [])
            for kw in keywords:
                # Blindaje estricto: exige límites de palabra exactos para evitar colisiones de sub-cadenas
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, norm_text, flags=re.IGNORECASE):
                    return cluster

        return None

    @classmethod
    def classify_cluster_bottom_up(cls, file_path: str) -> Tuple[str, str]:
        """
        Clasifica una ruta de archivo evaluando en 4 capas concéntricas:
        Retorna (cluster_key, match_reason)
        """
        norm_path = unicodedata.normalize("NFC", file_path)
        parts = [p for p in norm_path.split(os.sep) if p]

        if not parts:
            return ("general", "Ruta vacía")

        filename = parts[-1]
        parent_dir = parts[-2] if len(parts) >= 2 else ""
        grandparent_dir = parts[-3] if len(parts) >= 3 else ""

        # Nivel 4 (Prioridad Máxima): ¿Existe una sigla de Track explícita en alguna parte?
        lower_full_path = norm_path.lower()
        for tag, cluster in cls.TRACK_TAGS_MAP.items():
            if tag in lower_full_path:
                return (cluster, f"Sigla de Track '{tag}' en ruta")

        # Nivel 1: Evaluar nombre del archivo/lección (ej: 04_embudo_ventas.mp4)
        c_file = cls.match_cluster_keywords(filename)
        if c_file:
            return (c_file, f"Lección individual: '{filename}'")

        # Nivel 2: Evaluar subcarpeta inmediata / Módulo (ej: Modulo 3 - Email Marketing)
        if parent_dir:
            c_parent = cls.match_cluster_keywords(parent_dir)
            if c_parent:
                return (c_parent, f"Módulo temático: '{parent_dir}'")

        # Nivel 3: Evaluar carpeta contenedora del curso
        if grandparent_dir:
            c_grand = cls.match_cluster_keywords(grandparent_dir)
            if c_grand:
                return (c_grand, f"Curso contenedor: '{grandparent_dir}'")

        # Nivel Fallback: Evaluar carpetas intermedias hacia arriba evitando las raíces comunes
        if len(parts) > 3:
            for p_part in reversed(parts[3:-2]):
                c_part = cls.match_cluster_keywords(p_part)
                if c_part:
                    return (c_part, f"Directorio intermedio: '{p_part}'")

        return ("general", "Sin coincidencia temática")

    @classmethod
    def classify_cluster(cls, path_str: str) -> str:
        """Interfaz retrocompatible que retorna únicamente la clave de cluster."""
        cluster, _ = cls.classify_cluster_bottom_up(path_str)
        return cluster

    @classmethod
    def find_peer_document_in_parent(
        cls,
        parent_dir: str,
        current_dir_name: str,
        parent_entries_cache: Dict[str, Set[str]],
    ) -> bool:
        """
        Verifica de forma atómica y en memoria si la carpeta padre contiene un documento
        hermano homónimo (.docx, .pdf, .md, .txt) correspondiente al curso actual.
        """
        norm_parent = unicodedata.normalize("NFC", parent_dir)
        if norm_parent not in parent_entries_cache:
            try:
                entries = set()
                with os.scandir(parent_dir) as it:
                    for e in it:
                        if e.is_file(follow_symlinks=False):
                            entries.add(cls.normalize_text(e.name))
                parent_entries_cache[norm_parent] = entries
            except Exception:
                parent_entries_cache[norm_parent] = set()

        cached_names = parent_entries_cache[norm_parent]
        target_stem = cls.normalize_text(current_dir_name)

        # Verificar si existe [Curso].docx, [Curso].pdf, etc.
        for ext in ("docx", "pdf", "md", "txt"):
            candidate = f"{target_stem} {ext}"
            if candidate in cached_names:
                return True

            # Comparación flexible sin extensión concatenada
            for name in cached_names:
                if name.startswith(target_stem) and name.endswith(ext):
                    return True

        return False

    @classmethod
    def extract_lesson_stem(cls, filename: str) -> str:
        """
        Extrae la raíz temática de una lección eliminando extensiones y sufijos de idioma.
        Ej:
          'Start_Here.es.srt' -> 'start here'
          'Start_Here.es.vtt' -> 'start here'
          'Start_Here.md'     -> 'start here'
          'Start_Here.mp3'    -> 'start here'
          'Start_Here.mp4'    -> 'start here'
        """
        stem = filename
        stem = re.sub(r"\.(?:es|en|pt|fr|de)?\.(?:srt|vtt)$", "", stem, flags=re.IGNORECASE)
        stem = re.sub(r"\.(?:srt|vtt|mp4|mp3|m4a|aac|wav|md|docx|pdf|txt)$", "", stem, flags=re.IGNORECASE)
        norm = cls.normalize_text(stem)
        return norm if norm else stem.lower().strip()

    @classmethod
    def _register_resource(
        cls,
        resources_list: List[Dict[str, Any]],
        entry: os.DirEntry,
        ext: str,
        tier: str,
        canonical_upload: bool,
        reason_detail: Optional[str] = None,
        has_peer_doc: bool = False,
    ):
        try:
            st = entry.stat(follow_symlinks=False)
            cluster, match_reason = cls.classify_cluster_bottom_up(entry.path)
            target_title = cls.CLUSTER_NOTEBOOK_TITLES.get(
                cluster, f"[ESPECIALIDAD_{cluster.upper()}]"
            )
            resources_list.append({
                "path": entry.path,
                "filename": entry.name,
                "ext": ext,
                "tier": tier,
                "canonical_upload": canonical_upload,
                "size_bytes": st.st_size,
                "mtime": int(st.st_mtime),
                "cluster": cluster,
                "match_reason": match_reason,
                "status_detail": reason_detail if reason_detail else match_reason,
                "has_peer_doc": has_peer_doc,
                "target_notebook": target_title,
            })
        except Exception:
            pass

    @classmethod
    def scan_path(
        cls,
        base_dir: str,
        max_depth: int = 4,
    ) -> List[Dict[str, Any]]:
        """Recorre de forma controlada el sistema de archivos clasificando con Bottom-Up, Peer-Docs y Deduplicación por Stem."""
        resources = []
        if not os.path.exists(base_dir):
            return resources

        parent_cache: Dict[str, Set[str]] = {}
        queue = [(base_dir, 0)]

        while queue:
            current_dir, depth = queue.pop(0)
            try:
                subdirs = []
                files = []
                with os.scandir(current_dir) as it:
                    for entry in it:
                        if entry.name.startswith("."):
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name not in cls.EXCLUDE_DIRS and depth + 1 < max_depth:
                                subdirs.append((entry.path, depth + 1))
                        elif entry.is_file(follow_symlinks=False):
                            files.append(entry)

                queue.extend(subdirs)

                if not files:
                    continue

                # Filtrar solo archivos de interés
                relevant_files = []
                for entry in files:
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext in (".docx", ".md", ".txt", ".pdf", ".srt", ".vtt", ".aac", ".m4a", ".mp3", ".mp4"):
                        relevant_files.append((entry, ext))

                if not relevant_files:
                    continue

                # 1. Correlación de Documentos Hermanos (Peer-Docs en carpeta padre)
                parent_dir = os.path.dirname(current_dir)
                current_dir_name = os.path.basename(current_dir)
                has_peer_doc = cls.find_peer_document_in_parent(
                    parent_dir, current_dir_name, parent_cache
                )

                # 2. Agrupación por Stem de Lección en la carpeta actual
                stem_groups: Dict[str, List[Tuple[os.DirEntry, str]]] = defaultdict(list)
                for entry, ext in relevant_files:
                    stem = cls.extract_lesson_stem(entry.name)
                    stem_groups[stem].append((entry, ext))

                # 3. Jerarquía de Formatos por Stem (Anti-Redundancia)
                for stem, group in stem_groups.items():
                    docs = [it for it in group if it[1] in (".docx", ".md", ".txt", ".pdf")]
                    subs = [it for it in group if it[1] in (".srt", ".vtt")]
                    audios = [it for it in group if it[1] in (".aac", ".m4a", ".mp3")]
                    videos = [it for it in group if it[1] == ".mp4"]

                    # CASO 1: Existe Documento Maestro (.md, .docx, .pdf, .txt)
                    if docs:
                        for entry, ext in docs:
                            cls._register_resource(
                                resources, entry, ext,
                                tier="direct_document",
                                canonical_upload=True,
                                reason_detail=None,
                                has_peer_doc=has_peer_doc
                            )
                        for entry, ext in subs:
                            cls._register_resource(
                                resources, entry, ext,
                                tier="format_redundant",
                                canonical_upload=False,
                                reason_detail="Omitido: Ya existe documento maestro (.md/.docx/.pdf) para esta lección",
                                has_peer_doc=has_peer_doc
                            )
                        for entry, ext in audios:
                            cls._register_resource(
                                resources, entry, ext,
                                tier="format_redundant",
                                canonical_upload=False,
                                reason_detail="Omitido: Ya existe documento maestro (.md/.docx/.pdf) para esta lección",
                                has_peer_doc=has_peer_doc
                            )
                        for entry, ext in videos:
                            cls._register_resource(
                                resources, entry, ext,
                                tier="video_residual",
                                canonical_upload=False,
                                reason_detail="Omitido: Lección cubierta por documento maestro",
                                has_peer_doc=has_peer_doc
                            )

                    # CASO 2: No hay Documento Maestro, pero hay Subtítulo (.srt, .vtt)
                    elif subs:
                        # Prioridad: .es.srt > .srt > .es.vtt > .vtt
                        def sub_prio(item):
                            n = item[0].name.lower()
                            if n.endswith(".es.srt"): return 0
                            if n.endswith(".srt"): return 1
                            if n.endswith(".es.vtt"): return 2
                            return 3

                        sorted_subs = sorted(subs, key=sub_prio)
                        primary_sub = sorted_subs[0]
                        redundant_subs = sorted_subs[1:]

                        cls._register_resource(
                            resources, primary_sub[0], primary_sub[1],
                            tier="subtitle_text",
                            canonical_upload=True,
                            reason_detail=None,
                            has_peer_doc=has_peer_doc
                        )
                        for entry, ext in redundant_subs:
                            cls._register_resource(
                                resources, entry, ext,
                                tier="format_redundant",
                                canonical_upload=False,
                                reason_detail="Omitido: Subtítulo redundante (.vtt/.srt duplicado)",
                                has_peer_doc=has_peer_doc
                            )
                        for entry, ext in audios:
                            cls._register_resource(
                                resources, entry, ext,
                                tier="format_redundant",
                                canonical_upload=False,
                                reason_detail="Omitido: Audio cubierto por subtítulo limpio",
                                has_peer_doc=has_peer_doc
                            )
                        for entry, ext in videos:
                            cls._register_resource(
                                resources, entry, ext,
                                tier="video_residual",
                                canonical_upload=False,
                                reason_detail="Omitido: Lección cubierta por subtítulo limpio",
                                has_peer_doc=has_peer_doc
                            )

                    # CASO 3: No hay Documento ni Subtítulo, pero hay Audio (.mp3, .m4a, .aac)
                    elif audios:
                        for idx, (entry, ext) in enumerate(audios):
                            if idx == 0:
                                cls._register_resource(
                                    resources, entry, ext,
                                    tier="direct_audio",
                                    canonical_upload=True,
                                    reason_detail=None,
                                    has_peer_doc=has_peer_doc
                                )
                            else:
                                cls._register_resource(
                                    resources, entry, ext,
                                    tier="format_redundant",
                                    canonical_upload=False,
                                    reason_detail="Omitido: Audio duplicado para la misma lección",
                                    has_peer_doc=has_peer_doc
                                )
                        for entry, ext in videos:
                            cls._register_resource(
                                resources, entry, ext,
                                tier="video_residual",
                                canonical_upload=False,
                                reason_detail="Omitido: Audio nativo disponible",
                                has_peer_doc=has_peer_doc
                            )

                    # CASO 4: Solo hay Video (.mp4)
                    else:
                        for entry, ext in videos:
                            if has_peer_doc:
                                cls._register_resource(
                                    resources, entry, ext,
                                    tier="video_residual",
                                    canonical_upload=False,
                                    reason_detail="Omitido: Cubierto por documento hermano en carpeta padre",
                                    has_peer_doc=has_peer_doc
                                )
                            else:
                                cls._register_resource(
                                    resources, entry, ext,
                                    tier="orphan_video",
                                    canonical_upload=False,
                                    reason_detail="Video huérfano sin documento ni audio",
                                    has_peer_doc=has_peer_doc
                                )
            except Exception:
                continue

        return resources


# =============================================================================
# 6. Prompts Especializados de Extracción para NotebookLM (10k Chars)
# =============================================================================
MASTER_UNIVERSAL_PROMPT = """Eres el Motor Soberano de Extracción Estratégica y Curaduría de Conocimiento de Baiosfera.
Tu misión exclusiva es actuar como un sintetizador de máxima densidad intelectual, extrayendo modelos mentales, heurísticas, algoritmos paso a paso, fórmulas de redacción, arquitecturas de conversión y marcos conceptuales de las fuentes indexadas en este cuaderno.

DIRECTIVAS OPERATIVAS AFIRMATIVAS:
1. RIGOR EPISTÉMICO Y EXCLUSIVIDAD FUENTE: Responde exclusivamente a partir de la información explícita o demostrable en los documentos, audios, transcripciones y materiales adjuntos a este cuaderno. Ante la ausencia de un dato o métrica específica, declara con exactitud: "Dato no presente en las fuentes indexadas".
2. CITACIÓN EXTRACTIVA Y TRAZABILIDAD: Toda afirmación, fórmula o recomendación debe citar el autor, curso o documento fuente del cual proviene. Siempre que sea posible, cita textualmente la frase clave o principio rector.
3. CONCISIÓN Y DENSIDAD COMERCIAL: Emplea una redacción directa, técnica y libre de preámbulos, cortesías o adjetivos vacíos. Enfócate de inmediato en el núcleo conceptual, los mecanismos psicológicos y la implementación táctica.
4. FORMATO ESTRUCTURAL DE ALTA DENSIDAD:
   - Presenta las respuestas en Playbooks estructurados con Markdown limpio.
   - Utiliza listas ordenadas para secuencias temporales o algoritmos de ejecución.
   - Utiliza tablas comparativas para matrices de decisión, arquetipos o pros/contras.
   - Define fórmulas matemáticas o algebraicas de valor con parámetros claros.
   - Separa siempre el PRINCIPIO (por qué funciona psicológicamente) del ALGORITMO (cómo se implementa paso a paso).
5. DESACOPLE ESTRUCTURAL: Extrae la mecánica del método (la fórmula lógica) separada del caso de estudio específico, permitiendo que dicha fórmula sea posteriormente transmutada hacia cualquier marca o proyecto downstream sin arrastrar la voz del autor original.
"""

CLUSTER_SYSTEM_PROMPTS = {
    "copywriting": """Eres el Analista Maestro de Copywriting de Respuesta Directa y Psicología de la Persuasión.
Tu función es extraer y codificar las técnicas de redacción comercial más sofisticadas de las fuentes de este cuaderno.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Descompón cada técnica en su estructura sintáctica fundamental: Hook (Gancho) -> Story (Narrativa/Tensión) -> Offer/CTA (Resolución).
- Extrae fórmulas exactas de Titulares (Headlines) indicando variables reemplazables: [Resultado Deseado] sin [Objeción/Fricción Principal] en [Tiempo Específico].
- Identifica los Gatillos Emocionales primarios invocados en las clases: Estatus, Certeza, Pertenencia, Autonomía, Seguridad.
- Para cada objeción del comprador analizada en los cursos, extrae el Mecanismo Único de Desmantelamiento enseñado por los autores.
- Provee micro-copys de alta conversión para botones, llamadas a la acción, micro-interacciones de formulario y mensajes de checkout.
- Cada análisis culmina en una plantilla operativa de aplicación inmediata.
""",
    "ofertas": """Eres el Arquitecto de Ingeniería de Ofertas Grand Slam y Economía de Valor.
Tu objetivo es diseccionar la anatomía de las ofertas comerciales presentes en las fuentes y convertirlas en matrices matemáticas y estratégicas de valor.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Aplica rigurosamente la Ecuación de Valor: Maximizar Dream Outcome y Perceived Likelihood of Achievement, mientras se reduce al mínimo el Time Delay y el Effort & Sacrifice.
- Identifica la lista exhaustiva de problemas del avatar y mapea cada problema a una solución empaquetada como bono de alto valor percibido.
- Extrae las estructuras de Garantía: Incondicionales (reembolso total), Condicionales (basadas en métricas de esfuerzo del cliente), o Anti-Garantías (exclusividad sin retorno).
- Modela la jerarquía de Precios: Anclas de valor (Price Anchoring), contraste de costo de inacción vs inversión, y opciones de pago único vs financiamiento.
- Descompón los nombres de oferta según la fórmula M.A.G.I.C. (Magnetic reason, Avatar, Goal, Interval, Container) o equivalente en las fuentes.
""",
    "funnels": """Eres el Director de Arquitectura de Conversión (CRO) y Funnels Digitales.
Tu misión es traducir las estrategias de embudos de venta y diseño de páginas de aterrizaje en planos arquitectónicos y secuencias de conversión.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Modela la anatomía sección por sección de las páginas de aterrizaje de alto rendimiento:
  1. Hero Section (Titular, subtitular, VSL/Media, CTA principal, micro-prueba social).
  2. Problematización y Espejo Empático (descripción vívida de la frustración actual).
  3. Revelación del Mecanismo Único (por qué las soluciones anteriores fallaron).
  4. Presentación de la Oferta y Stack de Valor.
  5. Prueba Social Masiva (estudios de caso, testimonios específicos, números).
  6. Inversión y Garantía de Riesgo Cero.
  7. FAQ con desmantelamiento activo de objeciones.
- Extrae la lógica de Order Bumps (micro-ofertas pre-checkout) y 1-Click Upsells/Downsells post-pago, detallando el ratio de precio y relevancia.
- Documenta las heurísticas de fricción móvil y experiencia de usuario que incrementan la tasa de conversión.
""",
    "whatsapp": """Eres el Especialista en Conversational Commerce y Embudos de Mensajería Directa.
Tu función es extraer secuencias de venta conversacional, scripts de chat y arquitectura de bots.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Codifica las fases del diálogo de ventas: Saludo de Apertura -> Calificación de Intención -> Presentación Concisa -> Manejo de Fricción -> Cierre con Link Directo.
- Extrae los tiempos de respuesta y cadencia de mensajes recomendados para no saturar al usuario ni provocar bloqueos por spam.
- Mapea las reglas de derivación inteligente hacia humanos cuando el prospecto presenta objeciones complejas o tickets altos.
""",
    "email": """Eres el Estratega de Email Marketing, Secuencias Automatizadas y Entregabilidad.
Tu objetivo es destilar las secuencias de nutrición, ventas y retención por correo electrónico.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Descompón las estructuras clásicas de secuencias: Soap Opera Sequence (5 emails), secuencias de carrito abandonado (3 emails con urgencia progresiva) y boletines de valor diario.
- Extrae fórmulas de Asunto (Subject Lines) con ratios de apertura comprobados.
- Formula las pautas técnicas de higiene de listas y palabras tabú para evitar la bandeja de spam.
""",
    "paid_ads": """Eres el Director de Medios y Tráfico Pagado (Meta Ads, TikTok Ads, Google).
Tu función es extraer estrategias de compra de medios, matrices creativas y algoritmos de escalado.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Extrae matrices de testeo de Creativos: Gancho visual de 3 segundos -> Tensión/Problema -> Presentación de Oferta -> Llamado a la Acción.
- Mapea las reglas de escalado horizontal (duplicación de audiencias y ángulos) y vertical (incremento de presupuesto).
- Codifica las métricas de corte temprano para pausar anuncios con ROAS insuficiente.
""",
    "branding": """Eres el Custodio de Estrategia de Marca, Arquetipos y Posicionamiento.
Tu misión es extraer las metodologías para construir una Categoría de Uno y autoridad de mercado.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Extrae los marcos para definir la Propuesta Única de Valor y el Manifiesto de Marca.
- Identifica la matriz de los 12 Arquetipos de Personalidad y su aplicación al tono y lenguaje.
- Codifica las estrategias para transformar transacciones aisladas en lealtad y comunidad a largo plazo.
""",
    "ecommerce": """Eres el Director de Operaciones de E-Commerce, Supply Chain y Gestión de Tiendas.
Tu función es extraer las mejores prácticas operativas para tiendas online, catálogos y logística.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Extrae las metodologías de gestión de cadena de suministro (Supply Chain), niveles óptimos de inventario y políticas de reposición.
- Documenta las mejores prácticas para estructurar fichas de producto de alta conversión, arquitectura de colecciones y políticas de envío.
- Modela las estrategias de logística omnicanal para reducir costos de última milla y tiempos de entrega.
- Codifica las tácticas de rentabilidad en plataformas de comercio electrónico (Shopify, WooCommerce, Amazon FBA).
""",
    "automatizaciones": """Eres el Arquitecto de Automatización de Negocios, Flujos No-Code y Conexión de Sistemas.
Tu misión es extraer las arquitecturas de integración mediante n8n, Make, Zapier, CRMs y webhooks.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Modela los diagramas de flujo de automatización: Evento Disparador (Trigger) -> Filtros de Calificación -> Transformación de Datos -> Acciones Consecuentes.
- Extrae los patrones de integración entre plataformas de marketing, pasarelas de pago y sistemas de gestión de clientes (CRM).
- Documenta el manejo de errores, reintentos idempotentes y dead-letter queues en flujos de automatización crítica.
- Provee especificaciones técnicas para webhooks y APIs REST aplicadas a procesos de ventas.
""",
    "ia_prompting": """Eres el Ingeniero Maestro de Prompts, Modelos de Lenguaje y Agentes Autónomos.
Tu función es extraer las técnicas avanzadas de prompting, diseño de context vaults y arquitecturas agénticas.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Extrae las estructuras de System Prompts de alta densidad: Rol -> Directivas Operativas -> Restricciones Negativas/Positivas -> Formato de Salida -> Ejemplos Few-Shot.
- Documenta las metodologías de Chain-of-Thought (CoT), Tree-of-Thought y generación aumentada por recuperación (RAG).
- Codifica los patrones para construir Context Vaults y bibliotecas de contexto de marca que alimentan a los agentes.
- Modela los bucles de interacción y herramientas para agentes autónomos que resuelven flujos de negocio complejos.
""",
    "ux_ui": """Eres el Diseñador Principal de Experiencia de Usuario (UX), Interfaces (UI) y Sistemas de Diseño.
Tu objetivo es destilar las leyes de usabilidad, dirección de arte, tipografía y diseño centrado en el usuario.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Extrae los fundamentos de jerarquía visual, espaciado, uso del color y matrices tipográficas para interfaces digitales.
- Documenta las leyes de UX (Fitts, Hick, Miller, Jakob) y su aplicación táctica para reducir la carga cognitiva del usuario.
- Codifica los estándares de accesibilidad web (WCAG AAA/APCA) y diseño inclusivo.
- Modela la arquitectura de información, flujos de navegación y wireframing que maximizan la claridad y la conversión.
""",
}


# =============================================================================
# 7. Componente: Puente con el SDK de NotebookLM (Gemini Notebook)
# =============================================================================
class NotebookLMBridge:
    """Encapsula llamadas al cliente de NotebookLM con gestión de errores y jitter."""

    def __init__(self, client=None):
        if client:
            self.client = client
        else:
            try:
                from notebooklm_tools.cli.utils import get_client
                self.client = get_client(None)
            except Exception as e:
                raise RuntimeError(
                    f"No se pudo inicializar el cliente de NotebookLM: {e}. "
                    "Asegurate de haber ejecutado nlm login o nlm auth refresh."
                )

    def resolve_notebook_id(
        self,
        target_title: str,
        cluster_key: Optional[str] = None,
        auto_configure_prompt: bool = True,
    ) -> str:
        """Query-Before-Create: Reutiliza el UUID existente o crea un nuevo cuaderno."""
        all_notebooks = self.client.list_notebooks()
        for nb in all_notebooks:
            if getattr(nb, "is_owned", True) and nb.title.strip().lower() == target_title.strip().lower():
                return nb.id

        # Crear nuevo si no existe
        from notebooklm_tools.services import notebooks as nb_service
        res = nb_service.create_notebook(self.client, target_title)
        nb_id = res.get("id") or getattr(res, "id", None)
        if not nb_id and isinstance(res, dict):
            nb_id = res.get("notebook_id")

        nb_id = str(nb_id)

        if auto_configure_prompt and cluster_key:
            self.configure_system_prompt(nb_id, cluster_key)

        return nb_id

    def configure_system_prompt(self, notebook_id: str, cluster_key: str) -> bool:
        """Inyecta el system prompt especializado de 10k caracteres en el cuaderno."""
        prompt = CLUSTER_SYSTEM_PROMPTS.get(cluster_key, MASTER_UNIVERSAL_PROMPT)
        try:
            from notebooklm_tools.services import chat
            chat.configure_chat(
                self.client,
                notebook_id,
                goal="custom",
                custom_prompt=prompt,
                response_length="default",
            )
            return True
        except Exception as e:
            print(f"    ⚠️ No se pudo configurar el system prompt en {notebook_id}: {e}")
            return False

    def upload_source(
        self,
        notebook_id: str,
        resource: Dict[str, Any],
        dry_run: bool = False,
        upload_delay: float = 5.0,
    ) -> Optional[str]:
        """Sube una fuente aplicando la transformación adecuada según su tipo."""
        path = resource["path"]
        tier = resource["tier"]
        filename = resource["filename"]

        if dry_run:
            print(f"  [DRY-RUN] Subiría: {filename} -> Cuaderno {notebook_id} (Tier: {tier})")
            return "dry-run-source-id"

        # Aplicar delay de seguridad con jitter (evita HTTP 429)
        jitter = random.uniform(-1.0, 1.5)
        actual_delay = max(2.0, upload_delay + jitter)
        time.sleep(actual_delay)

        if tier == "subtitle_text":
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                raw_text = f.read()
            clean_text = SubtitlesCleaner.clean(raw_text)
            if not clean_text or len(clean_text) < 20:
                return None

            title = f"[Subtítulo] {os.path.splitext(filename)[0]}"
            res = self.client.add_text_source(notebook_id, clean_text, title=title)
            if isinstance(res, dict) and res.get("status") == "timeout":
                return None
            return getattr(res, "id", None) or (res.get("id") if isinstance(res, dict) else None)

        elif tier == "orphan_video":
            print(f"    🎙️ Extrayendo audio AAC (64k) de video huérfano...")
            aac_path = AudioExtractor.extract_aac(path)
            try:
                res = self.client.add_file(
                    notebook_id,
                    aac_path,
                    wait=True,
                    wait_timeout=600.0,
                )
                source_id = getattr(res, "id", None) or (res.get("id") if isinstance(res, dict) else None)
                return source_id
            finally:
                AudioExtractor.cleanup(aac_path)

        elif tier in ("direct_document", "direct_audio"):
            is_audio = tier == "direct_audio"
            timeout = 600.0 if is_audio else 120.0
            res = self.client.add_file(
                notebook_id,
                path,
                wait=True,
                wait_timeout=timeout,
            )
            return getattr(res, "id", None) or (res.get("id") if isinstance(res, dict) else None)

        return None


# =============================================================================
# 8. Comandos CLI & Dashboard Enriquecido
# =============================================================================
def cmd_scan(args):
    """Escanea el catálogo de cursos y despliega el Dashboard Operativo Enriquecido."""
    manifest_mgr = PartitionedManifest()
    uploaded = manifest_mgr.get_uploaded_fingerprints()

    paths = [args.target] if args.target else CourseScanner.DEFAULT_SEARCH_PATHS
    total_found = 0
    total_canonical = 0
    pending_canonical = 0
    total_docs = 0
    total_subs = 0
    total_audios = 0
    total_residuals = 0
    total_redundant = 0
    total_orphans = 0

    by_cluster: Dict[str, List[Dict[str, Any]]] = {}

    print("==================================================================")
    print("🔍 INICIANDO ESCANEO ANATÓMICO SSoT (knowledge-sync v2.1)")
    print("==================================================================")
    print(f"• Manifiesto SSoT activo: {len(uploaded)} fuentes ya registradas.")

    for p in paths:
        if not os.path.exists(p):
            continue
        print(f"• Escaneando: {p}...")
        found = CourseScanner.scan_path(p, max_depth=args.max_depth)
        total_found += len(found)

        for item in found:
            fp = MetadataFingerprint.compute_from_stat(
                os.path.relpath(item["path"], "/var/www/baiosfera"),
                item["size_bytes"],
                item["mtime"]
            )
            item["fingerprint"] = fp
            item["already_uploaded"] = fp in uploaded

            t = item["tier"]
            is_canon = item.get("canonical_upload", False)

            if is_canon:
                total_canonical += 1
                if not item["already_uploaded"]:
                    pending_canonical += 1

                if t == "direct_document":
                    total_docs += 1
                elif t == "subtitle_text":
                    total_subs += 1
                elif t == "direct_audio":
                    total_audios += 1
            elif t == "format_redundant":
                total_redundant += 1
            elif t == "video_residual":
                total_residuals += 1
            elif t == "orphan_video":
                total_orphans += 1

            c = item["cluster"]
            if c not in by_cluster:
                by_cluster[c] = []
            by_cluster[c].append(item)

    print("\n==================================================================")
    print("📊 DASHBOARD OPERATIVO DE FRUGALIDAD & AUDITORÍA SSoT (v2.1)")
    print("==================================================================")
    print(f"  • Total recursos analizados en disco: {total_found}")
    print(f"  • 🛡️ Formatos redundantes omitidos (Mismo stem de lección): {total_redundant}")
    print(f"     (Subtítulos e/o audios duplicados cuando ya existe documento maestro o subtítulo primario)")
    print(f"  • 🛡️ Videos residuales omitidos (Ahorro de CPU y FUSE): {total_residuals}")
    print(f"     (Cubiertos al 100% por documentos maestros, subtítulos o doc hermano en carpeta padre)")
    print(f"  • ⚠️ Videos huérfanos reales (Worker Efímero): {total_orphans}")
    print(f"  • ⚡ FUENTES CANÓNICAS ÚNICAS LISTAS PARA SUBIR: {total_canonical}")
    print(f"     - Documentos maestros (.docx/.pdf/.md): {total_docs} (⚡ Ingesta directa < 2s)")
    print(f"     - Subtítulos primarios (.srt/.vtt): {total_subs} (⚡ Ingesta directa sin timecodes)")
    print(f"     - Audios primarios (.mp3/.aac): {total_audios} (🎙️ Speech-to-Text en Google Cloud)")
    print(f"  • Fuentes canónicas ya registradas en SSoT: {total_canonical - pending_canonical}")
    print(f"  • Fuentes canónicas pendientes de ingesta: {pending_canonical}")

    print("\n==================================================================")
    print("📂 DESGLOSE POR ESPECIALIDAD Y TRAZA DE MICRO-CLASIFICACIÓN:")
    print("==================================================================")

    for cluster, items in sorted(by_cluster.items()):
        canon_items = [i for i in items if i.get("canonical_upload", False)]
        pending_in_c = sum(1 for i in canon_items if not i["already_uploaded"])
        target_nb = CourseScanner.CLUSTER_NOTEBOOK_TITLES.get(cluster, f"[ESPECIALIDAD_{cluster.upper()}]")
        print(f"\n📁 [{cluster.upper()}] -> Cuaderno: {target_nb}")
        print(f"   Recursos en disco: {len(items)} | Fuentes canónicas únicas: {len(canon_items)} | Pendientes: {pending_in_c}")

        docs_c = sum(1 for i in canon_items if i["tier"] == "direct_document")
        subs_c = sum(1 for i in canon_items if i["tier"] == "subtitle_text")
        aud_c = sum(1 for i in canon_items if i["tier"] == "direct_audio")
        print(f"   Composición Canónica: direct_document: {docs_c}, subtitle_text: {subs_c}, direct_audio: {aud_c}")

        red_c = sum(1 for i in items if i["tier"] == "format_redundant")
        vid_c = sum(1 for i in items if i["tier"] in ("video_residual", "orphan_video"))
        print(f"   Omitidos por optimización: format_redundant: {red_c}, video_residual/orphan: {vid_c}")

        # Muestra representativa de traza de clasificación (priorizando fuentes canónicas)
        sample_reasons = {}
        source_sample = canon_items if canon_items else items
        for it in source_sample:
            reason = it.get("match_reason", "coincidencia")
            if reason not in sample_reasons:
                sample_reasons[reason] = os.path.basename(it["path"])
            if len(sample_reasons) >= 3:
                break

        print("   Muestra Canónica de Micro-Clasificación:")
        for r, fname in sample_reasons.items():
            print(f"     - [{r}] -> {fname}")

        # Siguiente paso accionable
        if pending_in_c > 0 and cluster != "general":
            limit_sug = min(pending_in_c, 20)
            print(f"   👉 Comando sugerido: knowledge-sync push --cluster {cluster} --limit {limit_sug}")

    print("\n==================================================================")
    print(f"✅ ESCANEO FINALIZADO EXITOSAMENTE. Total fuentes canónicas pendientes: {pending_canonical}")
    print("==================================================================")


def cmd_init_clusters(args):
    """Pre-aprovisiona los 11 cuadernos de cluster, inyecta prompts y exporta clusters.json."""
    print("==================================================================")
    print("🏗️ INICIALIZACIÓN DE 11 CLUSTERS Y SYSTEM PROMPTS EN NOTEBOOKLM")
    print("==================================================================")

    bridge = NotebookLMBridge()
    manifest_mgr = PartitionedManifest()
    clusters_manifest = {}

    print("• Sincronizando catálogo con Google NotebookLM...")
    all_notebooks = bridge.client.list_notebooks()
    existing_by_title = {
        nb.title.strip().lower(): nb
        for nb in all_notebooks
        if getattr(nb, "is_owned", True)
    }

    for cluster_key, target_title in CourseScanner.CLUSTER_NOTEBOOK_TITLES.items():
        print(f"\n📁 Procesando cluster: {cluster_key.upper()} -> {target_title}")
        norm_title = target_title.strip().lower()

        if norm_title in existing_by_title:
            nb = existing_by_title[norm_title]
            nb_id = nb.id
            sources_count = len(getattr(nb, "sources", []))
            print(f"  ✓ Cuaderno existente encontrado: UUID {nb_id} ({sources_count} fuentes)")
        else:
            print(f"  • Creando cuaderno nuevo en Google NotebookLM...")
            nb_id = bridge.resolve_notebook_id(
                target_title,
                cluster_key=cluster_key,
                auto_configure_prompt=False,
            )
            sources_count = 0
            print(f"  ✓ Creado exitosamente: UUID {nb_id}")

        print(f"  • Configurando system prompt especializado...")
        configured = bridge.configure_system_prompt(nb_id, cluster_key)
        if configured:
            print(f"  ✓ System prompt configurado exitosamente.")

        clusters_manifest[cluster_key] = {
            "notebook_id": nb_id,
            "title": target_title,
            "sources_count": sources_count,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    out_path = manifest_mgr.export_clusters_manifest(clusters_manifest)
    print(f"\n✅ Manifiesto canónico de clusters exportado en: {out_path}")
    print("\n📋 MAPA CANÓNICO DE LOS 11 CLUSTERS:")
    for c_key, data in clusters_manifest.items():
        print(f"  • {c_key.upper():<16} -> ID: {data['notebook_id']} ({data['title']})")


def cmd_push(args):
    """Ejecuta la ingesta idempotente hacia los cuadernos de NotebookLM."""
    print("==================================================================")
    print("🚀 INGESTA DINÁMICA IDEMPOTENTE A NOTEBOOKLM (v2.0)")
    print("==================================================================")

    manifest_mgr = PartitionedManifest()
    uploaded = manifest_mgr.get_uploaded_fingerprints()

    # Normalizar alias de cluster (ej: ads -> paid_ads)
    target_cluster = args.cluster
    if target_cluster == "ads":
        target_cluster = "paid_ads"

    paths = [args.target] if args.target else CourseScanner.DEFAULT_SEARCH_PATHS
    candidates = []

    for p in paths:
        if not os.path.exists(p):
            continue
        found = CourseScanner.scan_path(p, max_depth=args.max_depth)
        for item in found:
            if target_cluster and item["cluster"] != target_cluster:
                continue

            # Videos residuales (con doc hermano) se omiten
            if item["tier"] == "video_residual":
                continue

            # Formatos redundantes (ya cubiertos por formato superior) se omiten
            if item["tier"] == "format_redundant" or not item.get("canonical_upload", False):
                if item["tier"] == "orphan_video" and getattr(args, "convert_orphan_videos", False):
                    pass
                else:
                    continue

            # Videos huérfanos se procesan solo con flag explícito
            if item["tier"] == "orphan_video" and not getattr(args, "convert_orphan_videos", False):
                continue

            fp = MetadataFingerprint.compute_from_stat(
                os.path.relpath(item["path"], "/var/www/baiosfera"),
                item["size_bytes"],
                item["mtime"]
            )
            if fp not in uploaded:
                item["fingerprint"] = fp
                candidates.append(item)

    if not candidates:
        print("✅ Todo el contenido candidato ya está sincronizado e ingestando en NotebookLM.")
        return

    print(f"• Candidatos listos para ingesta: {len(candidates)}")
    if args.limit and args.limit > 0:
        candidates = candidates[:args.limit]
        print(f"  (Limitado a {args.limit} archivos por esta ejecución)")

    bridge = None if args.dry_run else NotebookLMBridge()
    success_count = 0

    clusters_map = manifest_mgr.load_clusters_manifest()
    resolved_notebooks = {
        data["title"]: data["notebook_id"]
        for data in clusters_map.values()
        if "title" in data and "notebook_id" in data
    }

    for idx, item in enumerate(candidates, 1):
        target_title = item["target_notebook"]
        filename = item["filename"]
        fp = item["fingerprint"]
        cluster_key = item["cluster"]

        print(f"[{idx}/{len(candidates)}] Ingestando: {filename}")
        print(f"    Destino: {target_title} (Tier: {item['tier']})")

        try:
            if args.dry_run:
                nb_id = "dry-run-nb-id"
                source_id = f"dry-run-src-{idx}"
                print(f"    [DRY-RUN] Simulación: Subiría {filename} -> {target_title} (Tier: {item['tier']})")
            else:
                if target_title not in resolved_notebooks:
                    print(f"    • Verificando cuaderno en Google NotebookLM...")
                    resolved_notebooks[target_title] = bridge.resolve_notebook_id(
                        target_title,
                        cluster_key=cluster_key,
                        auto_configure_prompt=True,
                    )
                nb_id = resolved_notebooks[target_title]

                source_id = bridge.upload_source(
                    nb_id,
                    item,
                    dry_run=args.dry_run,
                    upload_delay=args.delay,
                )

            if source_id:
                if not args.dry_run:
                    manifest_mgr.record_upload(
                        fingerprint=fp,
                        relative_path=os.path.relpath(item["path"], "/var/www/baiosfera"),
                        notebook_id=nb_id,
                        notebook_title=target_title,
                        source_id=str(source_id),
                        source_type=item["tier"],
                    )
                success_count += 1
                print(f"    ✅ Ingesta exitosa (Source ID: {source_id})")
            else:
                print(f"    ⚠️ Ingesta omitida o timeout sin confirmación de ID: {filename}")
        except Exception as e:
            print(f"    ❌ Error subiendo {filename}: {e}")

    print(f"\n🏁 Ingesta completada. Procesados con éxito: {success_count}/{len(candidates)}")


# =============================================================================
# 9. Suite de Pruebas Físicas Unitarias Deterministas (Exit 0)
# =============================================================================
def run_tests():
    """Ejecuta pruebas unitarias de los componentes de software deterministas."""
    print("==================================================================")
    print("🧪 EJECUTANDO SUITE DE PRUEBAS UNITARIAS DETERMINISTAS (knowledge-sync v2)")
    print("==================================================================")

    # Test 1: Limpiador de Subtítulos SRT
    sample_srt = """1
00:00:01,000 --> 00:00:04,500
Hola a todos, bienvenidos al curso.

2
00:00:04,600 --> 00:00:07,800
Hoy hablaremos de ofertas irresistibles.
"""
    cleaned_srt = SubtitlesCleaner.clean(sample_srt)
    assert "00:00" not in cleaned_srt, "Falla Test 1: Quedaron timestamps en el SRT"
    assert "-->" not in cleaned_srt, "Falla Test 1: Quedó flecha de timecode en el SRT"
    assert "ofertas irresistibles" in cleaned_srt, "Falla Test 1: Se perdió el texto del subtítulo"
    print("✓ [Test 1] Normalizador de Subtítulos SRT: PASSED")

    # Test 2: Huella Sintética sin Lectura de Payload
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"Prueba de contenido efimero")
        tmp_path = tmp.name

    fp1 = MetadataFingerprint.compute(tmp_path, base_dir=os.path.dirname(tmp_path))
    time.sleep(0.01)
    fp2 = MetadataFingerprint.compute(tmp_path, base_dir=os.path.dirname(tmp_path))
    assert fp1 == fp2, "Falla Test 2: La huella sintética debe ser determinista e idempotente"
    os.remove(tmp_path)
    print("✓ [Test 2] Huella Digital Sintética (Metadata Fingerprint): PASSED")

    # Test 3: Manifiesto Particionado Append-Only y Exportación Atómica de clusters.json
    with tempfile.TemporaryDirectory() as tmp_dir:
        man = PartitionedManifest(manifest_dir=tmp_dir)
        man.record_upload(
            fingerprint="fp123456",
            relative_path="CURSOS/TEST/clase1.md",
            notebook_id="nb-uuid-test",
            notebook_title="[TEST_NOTEBOOK]",
            source_id="src-999",
            source_type="direct_document",
        )
        loaded = man.get_uploaded_fingerprints()
        assert "fp123456" in loaded, "Falla Test 3: El registro append-only no se consolidó"

        # Prueba de exportación atómica
        c_path = man.export_clusters_manifest({"copywriting": {"notebook_id": "test-uuid"}})
        assert os.path.exists(c_path), "Falla Test 3: clusters.json no fue creado"
        c_manifest = man.load_clusters_manifest()
        assert c_manifest.get("copywriting", {}).get("notebook_id") == "test-uuid"
    print("✓ [Test 3] Manifiesto Particionado & Exportación Atómica: PASSED")

    # Test 4: Clasificador Bottom-Up, Mapeo de Siglas y Aislamiento de IA vs Copy
    assert CourseScanner.classify_cluster("PLATZI/03 ECOM/Curso de Supply Chain/01.mp4") == "ecommerce"
    assert CourseScanner.classify_cluster("PLATZI/04 AUTOM/RPA/clase.mp4") == "automatizaciones"
    assert CourseScanner.classify_cluster("PLATZI/14 AI PROMPT/Agentes/clase.mp4") == "ia_prompting"
    assert CourseScanner.classify_cluster("PLATZI/33 GRAPHIC THINKING UXUI/Tipografia/clase.mp4") == "ux_ui"

    # Micro-clasificación: lección de email dentro de carpeta madre compuestas
    c_micro, reason = CourseScanner.classify_cluster_bottom_up(
        "PLATZI/59 CONTENT COPY EMAIL SEO STORYTELLING VENTAS/Curso/Modulo 2/01_secuencias_de_email.mp4"
    )
    assert c_micro == "email", f"Falla Test 4: Esperaba 'email' por micro-lección, obtuvo '{c_micro}'"

    # Desempate IA vs Copywriting vs Email vs Ofertas
    assert CourseScanner.classify_cluster("Marketing_Context_Vault.md") == "ia_prompting"
    assert CourseScanner.classify_cluster("Cartas_de_Venta_PAS.docx") == "copywriting"
    assert CourseScanner.classify_cluster("Email_Promo_Campaign_Builder.md") == "email"
    assert CourseScanner.classify_cluster("AI_Gone_Wild_Create_a_Team_of_Ai_Assistants_with_Stackable_GPTs.es.srt") == "ia_prompting"
    assert CourseScanner.classify_cluster("DigitalMarketer_Offer_Architect_2.0.md") == "ofertas"
    assert CourseScanner.classify_cluster("Build_Your_Winning_eCommerce_Product_Page.md") == "ecommerce"
    assert CourseScanner.classify_cluster("Home_Page_Optimizer.md") == "funnels"
    assert CourseScanner.classify_cluster("How_to_Attract_Your_First_5_Brand_Ambassadors.es.srt") == "branding"
    print("✓ [Test 4] Clasificador Bottom-Up, Mapeo de Siglas & Aislamiento IA/Copy: PASSED")

    # Test 5: Correlación de Documentos Hermanos (Peer-Docs) con Normalización Unicode NFC
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Simular estructura de Platzi: [ECOM] Curso Logística.docx junto a [ECOM] Curso Logística/
        doc_name = unicodedata.normalize("NFC", "[ECOM] Curso Logística.docx")
        dir_name = unicodedata.normalize("NFC", "[ECOM] Curso Logística")
        course_dir = os.path.join(tmp_dir, dir_name)
        os.makedirs(course_dir, exist_ok=True)

        with open(os.path.join(tmp_dir, doc_name), "w") as f:
            f.write("Temario completo")

        with open(os.path.join(course_dir, "01_clase.mp4"), "w") as f:
            f.write("video dummy")

        scanned = CourseScanner.scan_path(tmp_dir)
        video_item = next((i for i in scanned if i["ext"] == ".mp4"), None)
        assert video_item is not None, "Falla Test 5: No se detectó el video"
        assert video_item["tier"] == "video_residual", (
            f"Falla Test 5: El video debió ser 'video_residual' al tener doc hermano, pero fue '{video_item['tier']}'"
        )
    print("✓ [Test 5] Correlación de Documentos Hermanos (Unicode NFC): PASSED")

    # Test 6: Extractor de Audio FFmpeg Quirúrgico y Limpieza
    with tempfile.TemporaryDirectory() as tmp_dir:
        dummy_wav = os.path.join(tmp_dir, "test_audio.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "1", dummy_wav],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        extracted_aac = AudioExtractor.extract_aac(dummy_wav, output_dir=tmp_dir)
        assert os.path.isfile(extracted_aac), "Falla Test 6: No se generó el archivo AAC"
        AudioExtractor.cleanup(extracted_aac)
        assert not os.path.exists(extracted_aac), "Falla Test 6: No se limpió el archivo temporal"
    print("✓ [Test 6] Extractor FFmpeg con Timeout y Limpieza de /tmp: PASSED")

    # Test 7: Deduplicación por Stem de Lección y Jerarquía de Calidad
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = "01_welcome_lesson"
        for ext in (".md", ".es.srt", ".es.vtt", ".srt", ".vtt", ".mp3", ".mp4"):
            with open(os.path.join(tmp_dir, f"{base}{ext}"), "w") as f:
                f.write("dummy content")

        scanned = CourseScanner.scan_path(tmp_dir)
        canon = [i for i in scanned if i.get("canonical_upload", False)]
        redundant = [i for i in scanned if i["tier"] == "format_redundant"]
        residual = [i for i in scanned if i["tier"] == "video_residual"]

        assert len(canon) == 1, f"Falla Test 7: Debió haber exactamente 1 fuente canónica, pero hay {len(canon)}"
        assert canon[0]["ext"] == ".md", f"Falla Test 7: La fuente canónica debió ser .md, fue {canon[0]['ext']}"
        assert len(redundant) == 5, f"Falla Test 7: Debieron omitirse 5 formatos redundantes, pero hay {len(redundant)}"
        assert len(residual) == 1, f"Falla Test 7: El video debió ser residual, pero hay {len(residual)}"
    print("✓ [Test 7] Deduplicación por Stem de Lección & Jerarquía de Calidad: PASSED")

    print("\n🎉 TODAS LAS PRUEBAS FÍSICAS PASARON CON ÉXITO (EXIT 0).")
    sys.exit(0)


# =============================================================================
# 10. Punto de Entrada Principal
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Motor Soberano de Ingesta Dinámica & Curaduría SSoT para NotebookLM (v2.0)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Ejecuta suite de pruebas unitarias físicas",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Subcomando: scan
    scan_parser = subparsers.add_parser("scan", help="Escanea cursos sin gastar tokens ni cuota FUSE")
    scan_parser.add_argument("--target", type=str, default=None, help="Directorio objetivo específico")
    scan_parser.add_argument("--max-depth", type=int, default=4, help="Profundidad máxima de escaneo")

    # Subcomando: init-clusters
    init_parser = subparsers.add_parser(
        "init-clusters",
        help="Pre-aprovisiona los 11 cuadernos de cluster, inyecta system prompts y exporta clusters.json",
    )

    # Subcomando: push
    push_parser = subparsers.add_parser("push", help="Ingesta incremental hacia NotebookLM")
    push_parser.add_argument("--target", type=str, default=None, help="Directorio objetivo específico")
    push_parser.add_argument("--cluster", type=str, default=None, help="Filtrar por cluster específico (ecommerce, funnels, etc.)")
    push_parser.add_argument("--limit", type=int, default=None, help="Límite máximo de archivos a subir en esta pasada")
    push_parser.add_argument("--delay", type=float, default=5.0, help="Delay entre subidas en segundos")
    push_parser.add_argument("--max-depth", type=int, default=4, help="Profundidad máxima de escaneo")
    push_parser.add_argument(
        "--convert-orphan-videos",
        action="store_true",
        help="Convierte videos huérfanos a audio AAC antes de subir (requiere precaución de CPU)",
    )
    push_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula sin realizar subidas reales",
    )

    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    if not args.command:
        parser.print_help()
        return

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "init-clusters":
        cmd_init_clusters(args)
    elif args.command == "push":
        cmd_push(args)


if __name__ == "__main__":
    main()
