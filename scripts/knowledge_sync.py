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
import html
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
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import Counter, defaultdict

# Inyectar site-packages de uv notebooklm-mcp-cli si existe
UV_SITE_PACKAGES = "/home/zerops/.local/share/uv/tools/notebooklm-mcp-cli/lib/python3.12/site-packages"
if os.path.isdir(UV_SITE_PACKAGES) and UV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, UV_SITE_PACKAGES)


# =============================================================================
# 1. Componente: Limpiador y Normalizador de Subtítulos SRT/VTT en Memoria
# =============================================================================
class SubtitlesCleaner:
    """Normaliza y despoja códigos de tiempo, etiquetas de formateo y repeticiones de roll-up en archivos .srt, .vtt y .txt de subtítulos."""

    TIMECODE_LINE = re.compile(
        r"^(?:\d{1,5}\r?\n)?(?:\d{2}:)?\d{2}:\d{2}[,\.]\d{3}\s*-->\s*(?:\d{2}:)?\d{2}:\d{2}[,\.]\d{3}.*$",
        re.MULTILINE,
    )
    HEADER_VTT = re.compile(r"^\ufeff?WEBVTT.*?\n(?:\w+:.*?\n)*\n?", re.DOTALL | re.IGNORECASE)
    TAG_HTML = re.compile(r"<[^>]+>")

    @classmethod
    def clean(cls, raw_content: str) -> str:
        """Remueve numeración secuencial, marcas de tiempo, etiquetas de karaoke y deduplica repeticiones de roll-up."""
        if not raw_content:
            return ""

        content = raw_content.replace("\r\n", "\n").replace("\r", "\n")
        content = html.unescape(content)
        content = cls.HEADER_VTT.sub("", content)
        content = cls.TIMECODE_LINE.sub("", content)
        content = cls.TAG_HTML.sub("", content)

        lines = []
        for line in content.splitlines():
            line_str = line.strip()
            if not line_str or line_str.isdigit():
                continue
            if line_str.upper().startswith(("NOTE", "REGION", "STYLE", "WEBVTT", "KIND:", "LANGUAGE:")):
                continue
            if lines:
                prev = lines[-1]
                if line_str == prev:
                    continue
                if line_str.startswith(prev):
                    lines[-1] = line_str
                    continue
                if prev.startswith(line_str):
                    continue
                # Detección de solapamiento en roll-up (YouTube / auto-captions)
                wp = prev.split()
                wc = line_str.split()
                overlap = False
                for k in range(min(len(wp), len(wc), 8), 1, -1):
                    if wp[-k:] == wc[:k]:
                        lines[-1] = " ".join(wp + wc[k:])
                        overlap = True
                        break
                if overlap:
                    continue

            lines.append(line_str)

        # Agrupar en párrafos continuos y legibles (cada ~5 oraciones o por pausas)
        paragraphs = []
        current_para = []
        for l in lines:
            current_para.append(l)
            if len(current_para) >= 4 and l.endswith((".", "?", "!")):
                paragraphs.append(" ".join(current_para))
                current_para = []
        if current_para:
            paragraphs.append(" ".join(current_para))

        return "\n\n".join(paragraphs) if paragraphs else "\n".join(lines)


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
# 4. Componente: Parsers Polimórficos de Texto (.docx, .pdf, .srt, .md, .txt)
# =============================================================================
class DocxParser:
    """Extrae texto de archivos .docx mediante zipfile nativo y XML ElementTree (0 dependencias)."""

    @staticmethod
    def extract_text(file_path: str) -> str:
        try:
            with zipfile.ZipFile(file_path, "r") as z:
                if "word/document.xml" not in z.namelist():
                    return ""
                xml_content = z.read("word/document.xml")
                root = ET.fromstring(xml_content)
                paragraphs = []
                for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                    texts = [
                        node.text
                        for node in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
                        if node.text
                    ]
                    if texts:
                        paragraphs.append("".join(texts))
                return "\n\n".join(paragraphs).strip()
        except Exception:
            return ""


class PdfParser:
    """Extrae texto de archivos .pdf mediante pdftotext (poppler-utils) con timeout estricto."""

    @staticmethod
    def extract_text(file_path: str, timeout: int = 30) -> str:
        try:
            res = subprocess.run(
                ["pdftotext", "-layout", "-enc", "UTF-8", file_path, "-"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=True,
            )
            raw_text = res.stdout.decode("utf-8", errors="replace")

            # Filtro estructural de baja densidad (descarte de diapositivas o formularios vacíos)
            pages = raw_text.split("\x0c")
            non_empty_pages = [p for p in pages if p.strip()]
            if len(non_empty_pages) >= 3:
                total_words = len(raw_text.split())
                avg_words_per_page = total_words / len(non_empty_pages)
                if avg_words_per_page < 30:
                    return ""

            # Limpiar caracteres de control form-feed (\x0c)
            clean_text = raw_text.replace("\x0c", "\n\n")
            clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)
            return clean_text.strip()
        except Exception:
            return ""


class TextContentExtractor:
    """Orquestador unificado de extracción de texto para fuentes de conocimiento."""

    @classmethod
    def extract(cls, file_path: str) -> str:
        if not os.path.exists(file_path):
            return ""

        lower_path = file_path.lower()
        if (
            lower_path.endswith(".es.srt")
            or lower_path.endswith(".srt")
            or lower_path.endswith(".es.vtt")
            or lower_path.endswith(".vtt")
        ):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    raw = f.read()
                return SubtitlesCleaner.clean(raw)
            except Exception:
                return ""

        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".md", ".txt"):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    raw = f.read().strip()
                if "-->" in raw and re.search(r"\d{1,2}:\d{2}.*?-->", raw):
                    return SubtitlesCleaner.clean(raw)
                return raw
            except Exception:
                return ""
        elif ext == ".docx":
            return DocxParser.extract_text(file_path)
        elif ext == ".pdf":
            return PdfParser.extract_text(file_path)

        return ""


# =============================================================================
# 5. Componente: Compactador y Fusionador de Cursos Multi-Tema (CourseCompactor)
# =============================================================================
class CourseCompactor:
    """
    Fusiona y compacta lecciones de cada curso en compendios Markdown unificados
    organizados por la tupla canónica (Curso, Cluster).
    Aprovecha la capacidad de 500.000 palabras por fuente de NotebookLM para reducir
    el consumo de fuentes en >85% y evitar la saturación de 300 fuentes por cuaderno.
    """

    DEFAULT_OUTPUT_DIR = "/var/www/localstorage/knowledge_cache/compendiums"

    INTERMEDIATE_TIERS = {
        "vip", "basic", "profesional", "categorias", "author", "archivos",
        "1. cua", "2. cua", "3. cua", "cursos sprint", "cortos", "00. incompletos",
        "01. desarrollo personal", "02. seducción", "03. inversiones finanzas",
        "04. instagram", "05. ventas", "06. meta ads", "07. marketing",
        "03 training playbooks and workshops",
        "00_start_here", "01_ai_systems", "02_programs_and_accelerators",
        "03_training_playbooks_and_workshops", "04_bonuses_and_masterclasses", "05_choose_your_focus"
    }

    @classmethod
    def extract_course_metadata(cls, file_path: str) -> Dict[str, str]:
        """Extrae (provider, course_name, course_dir) preservando la jerarquía institucional y detectando niveles intermedios."""
        rel = os.path.relpath(file_path, "/var/www/baiosfera")
        parts = rel.split(os.sep)
        if not parts:
            return {
                "provider": "GENERAL",
                "course_name": "General",
                "course_dir": os.path.dirname(file_path),
            }

        top = parts[0]
        if top == "CURSOS":
            provider = parts[1] if len(parts) > 1 else "CURSOS"
            if provider == "LUIS-INESTROSA" and len(parts) >= 3 and parts[2].startswith("Taller CONFERENCIAS QUE VENDEN"):
                course_name = "Taller CONFERENCIAS QUE VENDEN"
                course_dir = os.path.join("/var/www/baiosfera", parts[0], parts[1], "Taller CONFERENCIAS QUE VENDEN")
            elif len(parts) >= 4 and parts[2].lower() in cls.INTERMEDIATE_TIERS:
                course_name = parts[3]
                course_dir = os.path.join("/var/www/baiosfera", parts[0], parts[1], parts[2], parts[3])
            elif len(parts) >= 4:
                course_name = parts[2]
                course_dir = os.path.join("/var/www/baiosfera", parts[0], parts[1], parts[2])
            elif len(parts) == 3:
                stem = os.path.splitext(parts[2])[0]
                clean_name = re.sub(r"[\s_-]+(clase|sesi[oó]n|modulo|lecci[oó]n)[\s_-]*\d+.*$", "", stem, flags=re.I).strip()
                course_name = clean_name or parts[1]
                course_dir = os.path.join("/var/www/baiosfera", parts[0], parts[1])
            else:
                course_name = provider
                course_dir = os.path.dirname(file_path)
        elif top in ("PLATZI", "DIGITALMARKETER"):
            provider = top
            if len(parts) >= 4 and parts[1].lower() in cls.INTERMEDIATE_TIERS:
                course_name = parts[2]
                course_dir = os.path.join("/var/www/baiosfera", parts[0], parts[1], parts[2])
            elif len(parts) >= 3:
                course_name = parts[2]
                course_dir = os.path.join("/var/www/baiosfera", parts[0], parts[1], parts[2])
            elif len(parts) == 2:
                stem = os.path.splitext(parts[1])[0]
                course_name = stem
                course_dir = os.path.join("/var/www/baiosfera", parts[0], parts[1])
            else:
                course_name = "General"
                course_dir = os.path.dirname(file_path)
        elif top == "IA INTELIGENCIA ARTIFICIAL":
            provider = "IA"
            if len(parts) >= 3:
                course_name = parts[1]
                course_dir = os.path.join("/var/www/baiosfera", parts[0], parts[1])
            elif len(parts) == 2:
                stem = os.path.splitext(parts[1])[0]
                course_name = stem
                course_dir = os.path.join("/var/www/baiosfera", parts[0])
            else:
                course_name = "General"
                course_dir = os.path.dirname(file_path)
        else:
            provider = top
            course_name = parts[1] if len(parts) > 1 else top
            course_dir = (
                os.path.join("/var/www/baiosfera", parts[0], parts[1])
                if len(parts) > 1
                else os.path.dirname(file_path)
            )

        clean_course_name = re.sub(r"^[0-9]+[_\s-]+", "", course_name).strip()
        if provider == "DIGITALMARKETER":
            clean_course_name = re.sub(r"_[a-z0-9\-]+$", "", clean_course_name)
            clean_course_name = clean_course_name.replace("_", " ").strip()

        if not clean_course_name:
            clean_course_name = course_name

        return {
            "provider": provider.upper(),
            "course_name": clean_course_name,
            "course_dir": course_dir,
        }

    @classmethod
    def sanitize_slug(cls, text: str) -> str:
        """Genera un slug seguro para nombres de archivo."""
        norm = unicodedata.normalize("NFKD", text)
        clean = "".join(c for c in norm if not unicodedata.combining(c))
        clean = re.sub(r"[^\w\s-]", "", clean).strip()
        return re.sub(r"[-\s]+", "-", clean)

    @classmethod
    def compact_group(
        cls,
        provider: str,
        cluster: str,
        course_name: str,
        items: List[Dict[str, Any]],
        output_base_dir: str = DEFAULT_OUTPUT_DIR,
        dry_run: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Genera un compendio Markdown unificado a partir de una lista de lecciones del mismo curso y cluster."""
        if not items:
            return None

        sorted_items = sorted(
            items,
            key=lambda x: os.path.basename(x["path"]).lower()
        )

        extracted_sections = []
        toc_entries = []
        total_words = 0
        seen_content_hashes: Set[str] = set()

        for it in sorted_items:
            fpath = it["path"]
            fname = os.path.basename(fpath)
            stem = CourseScanner.extract_lesson_stem(fname)
            clean_lesson_title = re.sub(r"^[0-9]+[_\s-]+", "", stem).replace("20", " ").replace("_", " ").replace("-", " ").strip().title()
            clean_lesson_title = re.sub(r"\s+", " ", clean_lesson_title).strip()
            if not clean_lesson_title:
                clean_lesson_title = stem

            if dry_run:
                # Simulación rápida: solo estima palabras en documentos de texto (.docx, .pdf, .srt, .md)
                ext = it.get("ext", "").lower()
                if ext in (".docx", ".pdf", ".srt", ".vtt", ".md", ".txt"):
                    words = max(50, min(80_000, it.get("size_bytes", 1000) // 7))
                else:
                    words = 0
                total_words += words
                section_idx = len(extracted_sections) + 1
                toc_entries.append(f"{section_idx}. **{clean_lesson_title}** (~{words} palabras est.)")
                extracted_sections.append(f"### {section_idx}. {clean_lesson_title}\n*(Simulación)*")
                continue

            if CourseScanner.is_scaffold_stub(fpath) or CourseScanner.is_non_llm_auxiliary(fpath) or CourseScanner.is_placeholder_or_duplicate(fpath):
                continue

            content = TextContentExtractor.extract(fpath)
            if not content:
                continue

            if CourseScanner.is_placeholder_or_duplicate(fpath, content):
                continue

            # Descartar stubs residuales o secciones de solo enlaces a medios
            if len(content.split()) < 30 and ("- **Video" in content or "Subtítulo" in content):
                continue

            # Deduplicación intra-curso por huella de contenido para evitar secciones duplicadas (ej: 06_Resources repitiendo 01_Overview)
            norm_content_sample = re.sub(r"\s+", " ", content[:4000]).strip().lower()
            content_hash = hashlib.sha256(norm_content_sample.encode("utf-8")).hexdigest()
            if content_hash in seen_content_hashes:
                continue
            seen_content_hashes.add(content_hash)

            words = len(content.split())
            total_words += words

            section_idx = len(extracted_sections) + 1
            toc_entries.append(f"{section_idx}. **{clean_lesson_title}** ({words} palabras)")
            rel_source = os.path.relpath(fpath, "/var/www/baiosfera")

            section_md = (
                f"### {section_idx}. {clean_lesson_title}\n"
                f"*Archivo fuente*: `{rel_source}` | *Formato*: `{it.get('ext', '')}`\n\n"
                f"{content}\n"
            )
            extracted_sections.append(section_md)

        min_words_threshold = 20 if os.environ.get("KNOWLEDGE_SYNC_TEST") else 200
        if not extracted_sections or total_words < min_words_threshold:
            return None

        header = (
            f"# [{provider}] [{cluster.upper()}] — {course_name}\n\n"
            f"## 📑 Índice de Lecciones y Documentos\n\n"
            + "\n".join(toc_entries)
            + "\n\n---\n\n"
            f"## 📚 Contenido Estructurado de las Lecciones\n\n"
        )

        body = "\n---\n\n".join(extracted_sections)
        full_content = header + body

        cluster_dir = os.path.join(output_base_dir, cluster.lower())
        safe_course = cls.sanitize_slug(course_name)
        compendium_filename = f"[{provider}]__[{cluster.upper()}]__{safe_course}.md"
        compendium_path = os.path.join(cluster_dir, compendium_filename)

        if not dry_run:
            os.makedirs(cluster_dir, exist_ok=True)
            with open(compendium_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            compendium_stat = os.stat(compendium_path)
            size_bytes = compendium_stat.st_size
            mtime = int(compendium_stat.st_mtime)
        else:
            size_bytes = len(full_content.encode("utf-8"))
            mtime = int(time.time())

        fp = hashlib.sha256(full_content.encode("utf-8")).hexdigest()

        return {
            "compendium_path": compendium_path,
            "filename": compendium_filename,
            "provider": provider,
            "cluster": cluster,
            "course_name": course_name,
            "lessons_count": len(extracted_sections),
            "total_items_in_course": len(items),
            "words_count": total_words,
            "size_bytes": size_bytes,
            "fingerprint": fp,
            "mtime": mtime,
            "target_notebook": f"[ESPECIALIDAD_{cluster.upper()}]",
        }

    @classmethod
    def determine_course_cluster(
        cls,
        provider: str,
        course_name: str,
        course_dir: str,
        items: List[Dict[str, Any]],
    ) -> Optional[str]:
        """
        Determina la especialidad canónica del curso bajo el principio Macro-First Blindado.
        Jerarquía:
        1. Descarte estricto de contenido no relacionado (Filtro de Dominio Negativo).
        2. Detección de tags [TAG] y resolución contextual de tags gruesos vs específicos.
        3. Clasificación semántica por título macro del curso (priorizando frases compuestas).
        4. Resolución por directorio contenedor temático.
        5. Fallback por consenso de lecciones individuales solo si el nivel macro es genérico.
        """
        clean_name = re.sub(r"(docx|pdf|txt|md|srt)$", "", course_name, flags=re.I).strip("._- ")
        context_str = f"{clean_name} {course_dir} {' '.join(it.get('filename', '') for it in items[:4])}".lower()
        norm_context = unicodedata.normalize("NFKD", context_str)
        norm_context = "".join(c for c in norm_context if not unicodedata.combining(c))
        norm_context = re.sub(r"[-_]+", " ", norm_context)

        # 1. Filtro de Dominio Negativo
        if any(bad in norm_context for bad in CourseScanner.NON_MARKETING_KEYWORDS):
            return None

        # 2. Extracción de tags de corchetes [TAG]
        tags = re.findall(r"\[([A-Z0-9_\-\+]+)\]", course_name + " " + course_dir)
        m_tag = tags[0].upper() if tags else None
        if not m_tag and provider == "PLATZI":
            m_pref = re.match(r"^([A-Z0-9]+)[-_\s]", os.path.basename(course_name))
            if m_pref:
                m_tag = m_pref.group(1).upper()

        c_title = CourseScanner.match_cluster_keywords(clean_name)
        c_phrase = CourseScanner.match_cluster_phrases(clean_name)

        raw_cluster: Optional[str] = None

        # 3. Proveedor PLATZI
        if provider == "PLATZI" and m_tag and m_tag in CourseScanner.PLATZI_TAGS_MAP:
            tag_cluster = CourseScanner.PLATZI_TAGS_MAP[m_tag]
            coarse_tags = {"DEV", "GROWTH", "INVEST", "MKTN", "WORKING", "VENTAS"}
            if m_tag in coarse_tags:
                raw_cluster = c_title if c_title else tag_cluster
            else:
                if c_phrase and c_phrase in ("whatsapp_conversational", "paid_ads", "ai_prompting_agents", "automations_workflows"):
                    raw_cluster = c_phrase
                else:
                    raw_cluster = tag_cluster

        # 4. Proveedor DIGITALMARKETER
        elif provider == "DIGITALMARKETER":
            if c_title:
                raw_cluster = c_title
            else:
                c_dir = CourseScanner.match_cluster_keywords(os.path.basename(course_dir))
                if c_dir:
                    raw_cluster = c_dir

        # 5. Proveedores CA, SCVIP, MCV, LUIS-INESTROSA, VELOCITYMEDIA
        elif m_tag and m_tag in CourseScanner.PLATZI_TAGS_MAP:
            raw_cluster = CourseScanner.PLATZI_TAGS_MAP[m_tag]
        else:
            lower_name = clean_name.lower()
            if "ca-marcap" in lower_name or "cua-marcap" in lower_name:
                raw_cluster = "branding_authority"
            elif "ca-vsl" in lower_name:
                raw_cluster = "copywriting"
            elif "ca-oferta" in lower_name or "ca-price" in lower_name or "mlm_58-18" in lower_name:
                raw_cluster = "offers_pricing"
            elif "ca-funnels" in lower_name or "cua-funnels" in lower_name:
                raw_cluster = "funnels_cro"
            elif "cua-ads" in lower_name:
                raw_cluster = "paid_ads"
            elif "cua-ai" in lower_name:
                raw_cluster = "ai_prompting_agents"
            elif "ca-seo" in lower_name:
                raw_cluster = "seo_aeo"
            elif c_title:
                raw_cluster = c_title
            elif course_dir:
                c_dir = CourseScanner.match_cluster_keywords(os.path.basename(course_dir))
                if c_dir:
                    raw_cluster = c_dir

        # 6. Fallback final por micro-lecciones
        if not raw_cluster or raw_cluster == "general":
            cluster_votes = [it["cluster"] for it in items if it.get("cluster") not in ("general", None)]
            if cluster_votes:
                raw_cluster = Counter(cluster_votes).most_common(1)[0][0]

        if not raw_cluster:
            return None

        return CourseScanner.CANONICAL_CLUSTER_MAP.get(raw_cluster, raw_cluster)

    @classmethod
    def compact_all(
        cls,
        scanned_items: List[Dict[str, Any]],
        target_cluster: Optional[str] = None,
        target_provider: Optional[str] = None,
        output_base_dir: str = DEFAULT_OUTPUT_DIR,
        dry_run: bool = False,
    ) -> List[Dict[str, Any]]:
        """Agrupa los items canónicos por tupla (provider, cluster, course_dir) y genera compendios."""
        eligible_items = []
        for it in scanned_items:
            if not it.get("canonical_upload", False):
                continue
            if it.get("tier") not in ("direct_document", "subtitle_text"):
                continue
            if target_cluster and it.get("cluster") != target_cluster:
                continue

            meta = cls.extract_course_metadata(it["path"])
            provider = meta["provider"]
            if target_provider and provider != target_provider.upper():
                continue

            # Filtro de Dominio: descartar contenido esotérico / salud / bienestar ajeno al marketing
            norm_p = re.sub(r"[-_]+", " ", it["path"].lower())
            if any(bad in norm_p for bad in CourseScanner.NON_MARKETING_KEYWORDS):
                continue

            it["_provider"] = provider
            it["_course_name"] = meta["course_name"]
            it["_course_dir"] = meta["course_dir"]

            eligible_items.append(it)

        # 1. Agrupar lecciones por curso físico (provider, course_dir, course_name)
        course_items = defaultdict(list)
        for it in eligible_items:
            key = (it["_provider"], it["_course_dir"], it["_course_name"])
            course_items[key].append(it)

        # 2. Partición Multi-Compendio y Clasificación Semántica por Lección
        groups = defaultdict(list)
        for (provider, course_dir, course_name), items in course_items.items():
            macro_cluster = cls.determine_course_cluster(
                provider=provider,
                course_name=course_name,
                course_dir=course_dir,
                items=items,
            )
            macro_canon = CourseScanner.CANONICAL_CLUSTER_MAP.get(macro_cluster, macro_cluster) if macro_cluster else None

            for it in items:
                fname = os.path.basename(it["path"])
                item_cluster = it.get("cluster")

                # Prioridad 1: Frase clave específica en el archivo de la lección
                c_phrase = CourseScanner.match_cluster_phrases(fname)
                if c_phrase:
                    target_c = CourseScanner.CANONICAL_CLUSTER_MAP.get(c_phrase, c_phrase)
                # Prioridad 2: Cluster pre-clasificado a nivel de lección si es canónico y no genérico
                elif item_cluster and item_cluster not in ("general", None):
                    target_c = CourseScanner.CANONICAL_CLUSTER_MAP.get(item_cluster, item_cluster)
                # Prioridad 3: Fallback al cluster macro del curso contenedor
                elif macro_canon and macro_canon != "general":
                    target_c = macro_canon
                else:
                    target_c = None

                if not target_c or target_c == "general":
                    continue

                if target_cluster and target_c != target_cluster:
                    continue

                it["cluster"] = target_c
                groups[(provider, target_c, course_dir, course_name)].append(it)

        total_groups = len(groups)
        print(f"• Compendios únicos a consolidar (partición multi-compendio): {total_groups:,}", flush=True)

        compendiums = []
        for idx, ((provider, cluster, course_dir, course_name), items) in enumerate(groups.items(), 1):
            if idx % 10 == 0 or idx == 1 or idx == total_groups:
                print(f"  [{idx}/{total_groups}] Analizando: [{provider}] [{cluster.upper()}] {course_name} ({len(items)} items)...", flush=True)
            comp = cls.compact_group(
                provider=provider,
                cluster=cluster,
                course_name=course_name,
                items=items,
                output_base_dir=output_base_dir,
                dry_run=dry_run,
            )
            if comp:
                compendiums.append(comp)

        return compendiums


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
        "/var/www/baiosfera/CURSOS",
        "/var/www/baiosfera/DIGITALMARKETER",
        "/var/www/baiosfera/PLATZI",
    ]

    EXCLUDE_DIRS = {
        "CATEGORIAS", "AUTHOR", "Archivos", "AGY", "0.DWNL",
        "00_START_HERE", "00_START", "00_BIENVENIDA", "Announcements",
        "Live_Calls", "Start_Here_5-Min_Plan", "changelogs", "bienvenidas",
        "onboarding", "community", "comunidad", "avisos", "foro", "foros",
        "recursos_adicionales", "__pycache__", "node_modules", "vendor",
        ".git", ".rclone"
    }

    # Palabras clave y patrones de exclusión para temas ajenos al negocio/marketing
    NON_MARKETING_KEYWORDS = {
        # Mindset, Desarrollo Personal, Esoterismo y No-Negocio
        "01. desarrollo personal", "02. seducción", "seduccion", "seducción", "sanar trauma",
        "desarrollo personal", "desarrolo personal", "reprogramate", "reprogramación",
        "millonarios conscientes", "heroes sin capa", "héroes sin capa", "master en coaching",
        "coaching ontologico", "coaching ontológico", "amor propio", "autoestima",
        # Trading, Cripto, Inversiones bursátiles ajenas al marketing digital
        "bolsa de valores", "inversiones", "inversion en bolsa", "inversión en bolsa",
        "cripto", "criptomonedas", "trading", "forex", "opciones binarias",
        # Salud, pseudociencia y esoterismo
        "biodecodificacion", "biodecodificación", "constelaciones", "hipnosis", "hipnotica", "hipnótica",
        "codigos sagrados", "códigos sagrados", "cirugias cuanticas", "cirugías cuánticas", "metodo yuen",
        "método yuen", "micologia", "micología", "letras hebreas", "vision aural", "visión aural",
        "astrologica", "astrológica", "dopamine mastery", "dormir mejor",
        "desafiando imposibles", "tantra", "terapeuta", "terapeutas", "transgeracional", "transgeneracional",
        "meditaciones", "meditacion", "meditación", "mesmerismo", "paralelo de embrio",
        "chakras", "reiki", "sanacion", "sanación", "magia", "esoterico", "esotérico"
    }

    # Patrones para descartar materiales auxiliares no-LLM (slides, cuadernos de trabajo, checklists impresos)
    NON_LLM_PATTERNS = [
        r"slide[-_ 20]*deck", r"slidedeck", r"\bslides\b", r"diapositiva", r"presentaci[oó]n",
        r"worksheet", r"workbook", r"work[-_ 20]*sheet", r"cuaderno[-_ 20]*de[-_ 20]*trabajo",
        r"libro[-_ 20]*de[-_ 20]*trabajo", r"hoja[-_ 20]*de[-_ 20]*trabajo", r"hojas[-_ 20]*de[-_ 20]*trabajo",
        r"checklist", r"cheatsheet", r"cheat[-_ 20]*sheet", r"\bquiz\b",
        r"ejercicio", r"imprimible", r"audit[-_ 20]*print", r"fillable"
    ]

    # 18 Especialidades Soberanas Canónicas (Customer Value Journey & Business Life Cycle)
    THEMATIC_CLUSTERS = {
        "avatar_research": [
            "icp", "ideal customer profile", "buyer persona", "avatar", "cliente ideal", "publico objetivo",
            "público objetivo", "dolores del cliente", "mapa de empatia", "mapa de empatía", "customer research",
            "investigacion de usuarios", "investigación de usuarios", "investigacion de mercado", "investigación de mercado",
            "jobs to be done", "jtbd", "thick data", "customer interviews", "entrevistas a clientes", "focus group",
            "etnografia digital", "etnografía digital", "segmentacion psicografica", "segmentación psicográfica",
            "segmentacion de mercado", "arquetipos de cliente", "dolores y deseos", "customer empathy", "user research"
        ],
        "branding_authority": [
            "branding", "brand", "marca", "marcap", "marca personal", "personal brand", "marca de poder", "identidad de marca",
            "brand identity", "tono de voz", "manual de marca", "brandbook", "brand guidelines", "posicionamiento",
            "positioning", "authority", "autoridad", "categoria de uno", "categoría de uno", "category of one",
            "become the go to expert", "celebrity marketer", "brief creativo", "arquitectura de marca", "brand equity",
            "brand ambassadors", "propuesta de valor de marca", "brand story", "brand positioning", "reputacion", "reputación"
        ],
        "offers_pricing": [
            "oferta", "ofertas", "offer", "offers", "precio", "precios", "ofertas irresistibles", "irresistible offer",
            "grand slam", "grand slam offer", "propuesta de valor", "pricing", "fijacion de precios", "fijación de precios",
            "value based pricing", "pricing por valor", "precio de valor", "hormozi", "value equation", "ecuacion de valor",
            "ecuación de valor", "garantia", "garantía", "guarantee", "bonus stack", "stack de bonos", "offer stack",
            "price elasticity", "elasticidad de precio", "high ticket", "high-ticket", "premium pricing", "inversion vs retorno",
            "estructuracion de ofertas", "site offers", "offer architect"
        ],
        "social_media": [
            "social media", "redes sociales", "instagram", "reels", "tiktok", "youtube", "linkedin", "community manager",
            "community management", "contenido organico", "contenido orgánico", "carrusel", "carruseles", "posts",
            "historias", "stories", "tiktok creativo", "creadores de video", "produccion para youtube", "producción para youtube",
            "podcast", "podcasting", "listening en redes", "crecimiento en redes", "viral content", "social strategy",
            "youtube subscribers", "scroll stopping", "estrategias de contenido para linkedin"
        ],
        "seo_aeo": [
            "seo", "search engine optimization", "posicionamiento web", "posicionamiento organico", "posicionamiento orgánico",
            "google search console", "gsc", "semrush", "ahrefs", "seo tecnico", "seo técnico", "aeo",
            "answer engine optimization", "geo", "generative engine optimization", "searchgpt", "perplexity seo",
            "backlinks", "link building", "linkbuilding", "keyword research", "palabras clave", "intencion de busqueda",
            "intención de búsqueda", "seo para ecommerce", "search strategy", "consultorias seo", "consultorías seo"
        ],
        "paid_ads": [
            "ads", "paid ads", "pauta", "pauta publicitaria", "meta ads", "meta ad", "facebook ads", "facebook ad",
            "fb ads", "fb ad", "instagram ads", "instagram ad", "campañas publicitarias", "campanas publicitarias",
            "campaña publicitaria", "campana publicitaria", "anuncios en meta", "anuncios en instagram", "google ads",
            "google ad", "google search ads", "google search ad", "performance max", "pmax", "tiktok ads", "tiktok ad",
            "linkedin ads", "linkedin ad", "roas", "cpa", "cpm", "media buying", "media buyer", "creativos para anuncios",
            "ad creatives", "business manager", "administrador de anuncios", "pixel de meta", "capi", "retargeting",
            "remarketing", "audiencias personalizadas", "lookalike", "scaling academy", "ad playbook", "ads playbook"
        ],
        "copywriting": [
            "copy", "copywriting", "redaccion persuasiva", "redacción persuasiva", "titular", "titulares", "headline",
            "headlines", "gancho", "ganchos", "hook", "hooks", "storytelling", "narrativa", "cartas de venta",
            "carta de venta", "sales letter", "vsl", "video sales letter", "textos que venden", "persuasion", "persuasión",
            "direct response copywriter", "swipe file", "formulas de copy", "bullet points", "balas persuasivas",
            "copywriting de respuesta directa", "words that sell", "pillar blog post", "titulares que venden"
        ],
        "funnels_cro": [
            "funnel", "funnels", "embudo", "embudos", "embudos de venta", "landing", "landing page", "landings",
            "home page", "homepage", "optimizer", "page optimizer", "paginas de captura", "páginas de captura",
            "checkout", "checkouts", "order bump", "bump", "upsell", "downsell", "cro",
            "conversion rate optimization", "optimizacion de conversion", "optimización de conversión",
            "ab testing", "split testing", "lead magnet", "squeeze page", "optin", "microembudos", "embudo de ventas",
            "embudos automatizados", "customer value journey", "cvj", "quiz funnel"
        ],
        "whatsapp_conversational": [
            "whatsapp", "whatsapp marketing", "whatsapp business", "ventas por whatsapp", "chatbot", "chatbots",
            "bot de whatsapp", "comercio conversacional", "conversational commerce", "cierre por chat", "secuencias de whatsapp",
            "mensajes masivos de whatsapp", "mensajes por chat", "difusion whatsapp", "difusiones whatsapp",
            "rapport por chat", "atencion conversacional", "atencion al cliente", "atención al cliente"
        ],
        "consultative_sales": [
            "ventas consultivas", "ventas b2b", "prospeccion", "prospección", "llamadas de venta", "sales calls",
            "closing calls", "cierre de ventas", "cerrar ventas", "1 call close", "1-call close", "one call close",
            "the 1 call close", "manejo de objeciones", "objection handling", "pitch de ventas", "sales pitch",
            "conferencias que venden", "habla y vendete bien", "ventas de alto valor", "high ticket sales",
            "negociacion", "negociación", "pipeline de ventas", "sales qualification", "meddpicc", "bant",
            "inmersion de ventas", "venta logica emocional"
        ],
        "email_marketing": [
            "email", "email marketing", "correo electronico", "correo electrónico", "newsletters", "newsletter",
            "autoresponder", "welcome sequence", "secuencias de email", "nurture", "secuencia de bienvenida",
            "entregabilidad", "dmarc", "dkim", "cold email", "email copywriting", "difusiones por correo",
            "listmonk", "broadcast de email", "secuencias automatizadas de correo", "email follow up", "customer centric emails"
        ],
        "customer_success": [
            "customer success", "retencion de clientes", "retención de clientes", "reduccion de churn", "reducción de churn",
            "churn rate", "fidelizacion de clientes", "fidelización de clientes", "onboarding de clientes", "soporte al cliente",
            "net promoter score", "nps", "satisfaccion del cliente", "satisfacción del cliente", "exito del cliente",
            "éxito del cliente", "servicio al cliente", "experiencia del cliente", "customer experience", "cx"
        ],
        "growth_loops": [
            "growth loops", "growth hacking", "marketing viral", "viral marketing", "viralidad", "bucles de crecimiento",
            "programas de referidos", "referidos", "referral program", "boca a boca", "word of mouth", "flywheel",
            "k factor", "product led growth", "plg", "aceleracion de crecimiento", "crecimiento exponencial", "habit loops"
        ],
        "ecommerce_stores": [
            "ecommerce", "e-commerce", "tiendas online", "tienda online", "tienda", "tiendas", "vender por internet",
            "shopify", "woocommerce", "dropshipping", "catalogo de productos", "catálogo de productos", "inventario",
            "logistica", "logística", "supply chain", "envios", "pasarelas de pago", "pago contra entrega", "cod",
            "cash on delivery", "ficha de producto", "product page", "devoluciones", "retail", "amazon"
        ],
        "automations_workflows": [
            "automatizacion", "automatizaciones", "automatización", "automation", "automations", "make", "zapier",
            "n8n", "webhook", "webhooks", "workflow", "workflows", "no code", "nocode", "rpa", "procesos automatizados",
            "crm workflows", "integracion de apis", "integración de apis", "integraciones no code", "api integrations",
            "hiperautomatizacion", "client on boarding"
        ],
        "data_analytics": [
            "data analytics", "analytics", "analitica digital", "analítica digital", "analitica web", "analítica web",
            "google analytics", "ga4", "looker studio", "business intelligence", "dashboards", "paneles de datos",
            "metricas de marketing", "métricas de marketing", "tracking", "seguimiento de eventos", "cpa", "ltv",
            "lifetime value", "cac", "costo de adquisicion", "atribucion multi touch", "atribución multi-touch",
            "kpis de negocio", "google tag manager", "gtm"
        ],
        "ai_prompting_agents": [
            "ia", "ai", "inteligencia artificial", "artificial intelligence", "prompt engineering", "ingenieria de prompt",
            "ingeniería de prompt", "prompts", "prompt", "prompting", "chatgpt", "gpt", "gpts", "claude", "gemini",
            "llm", "llms", "agentes de ia", "agentes ai", "agentes autonomos", "agentes autónomos", "crewai",
            "pydantic ai", "context engineering", "observabilidad de agentes", "langsmith", "flujos agenticos",
            "flujos agénticos", "context vault", "ai assistants", "ai tools"
        ],
        "product_startup": [
            "product management", "product manager", "gestion de producto", "gestión de producto", "startup", "startups",
            "lean startup", "business model canvas", "canvas de negocio", "mvp", "producto minimo viable",
            "producto mínimo viable", "validacion de producto", "validación de producto", "product market fit", "pmf",
            "product discovery", "roadmap de producto", "agile delivery", "scrum", "scrum master", "agile",
            "pmbok", "evaluacion financiera de proyectos", "pensamiento estrategico", "pensamiento estratégico",
            "ux", "ui", "ux/ui", "ui/ux", "uxui", "figma", "design systems", "sistemas de diseno", "sistemas de diseño",
            "design thinking", "tipografia", "tipografía", "graphic thinking", "interfaz", "interfaces", "wireframe", "accesibilidad"
        ],
    }

    # Mapa de Normalización Canónica (18 Especialidades SSoT)
    CANONICAL_CLUSTER_MAP = {
        # Canónicos directos
        "avatar_research": "avatar_research",
        "branding_authority": "branding_authority",
        "offers_pricing": "offers_pricing",
        "social_media": "social_media",
        "seo_aeo": "seo_aeo",
        "paid_ads": "paid_ads",
        "copywriting": "copywriting",
        "funnels_cro": "funnels_cro",
        "whatsapp_conversational": "whatsapp_conversational",
        "consultative_sales": "consultative_sales",
        "email_marketing": "email_marketing",
        "customer_success": "customer_success",
        "growth_loops": "growth_loops",
        "ecommerce_stores": "ecommerce_stores",
        "automations_workflows": "automations_workflows",
        "data_analytics": "data_analytics",
        "ai_prompting_agents": "ai_prompting_agents",
        "product_startup": "product_startup",
        # Aliases retrocompatibles
        "seo": "seo_aeo",
        "branding": "branding_authority",
        "ofertas": "offers_pricing",
        "funnels": "funnels_cro",
        "whatsapp": "whatsapp_conversational",
        "email": "email_marketing",
        "ecommerce": "ecommerce_stores",
        "automatizaciones": "automations_workflows",
        "ia_prompting": "ai_prompting_agents",
        "product_management": "product_startup",
        "ux_ui": "product_startup",
    }

    CLUSTER_NOTEBOOK_TITLES = {
        "avatar_research": "[ESPECIALIDAD_AVATAR_ICP_Y_RESEARCH]",
        "branding_authority": "[ESPECIALIDAD_BRANDING_Y_AUTORIDAD]",
        "offers_pricing": "[ESPECIALIDAD_OFERTAS_Y_PRICING]",
        "social_media": "[ESPECIALIDAD_REDES_SOCIALES_Y_COMUNIDAD]",
        "seo_aeo": "[ESPECIALIDAD_SEO_AEO_SEARCH]",
        "paid_ads": "[ESPECIALIDAD_META_ADS_CREATIVOS_Y_PAUTA]",
        "copywriting": "[ESPECIALIDAD_COPY_TITULARES_Y_GANCHOS]",
        "funnels_cro": "[ESPECIALIDAD_FUNNELS_CHECKOUTS_Y_CRO]",
        "whatsapp_conversational": "[ESPECIALIDAD_WHATSAPP_Y_CONVERSACIONAL]",
        "consultative_sales": "[ESPECIALIDAD_VENTAS_CONSULTIVAS_B2B]",
        "email_marketing": "[ESPECIALIDAD_EMAIL_AUTOMATION_Y_NURTURE]",
        "customer_success": "[ESPECIALIDAD_CUSTOMER_SUCCESS_Y_CHURN]",
        "growth_loops": "[ESPECIALIDAD_GROWTH_LOOPS_Y_REFERIDOS]",
        "ecommerce_stores": "[ESPECIALIDAD_ECOMMERCE_Y_TIENDAS]",
        "automations_workflows": "[ESPECIALIDAD_AUTOMATIZACIONES_Y_WORKFLOWS]",
        "data_analytics": "[ESPECIALIDAD_DATA_METRICAS_Y_ANALYTICS]",
        "ai_prompting_agents": "[ESPECIALIDAD_IA_PROMPTING_Y_AGENTES]",
        "product_startup": "[ESPECIALIDAD_PRODUCT_MANAGEMENT_Y_STARTUP]",
    }
    # Mapeo determinista de Siglas y Tokens de Corchetes ([TAG])
    PLATZI_TAGS_MAP = {
        # SEO & Búsqueda
        "SEO": "seo_aeo",
        # Redes Sociales Orgánicas & Comunidad
        "SOCIAL": "social_media",
        "INSTAGRAM": "social_media",
        "TIKTOK": "social_media",
        "YOUTUBE": "social_media",
        "VIDEO": "social_media",
        "LINKEDIN": "social_media",
        # Data & Analítica
        "DATA": "data_analytics",
        # Product Management & Metodologías
        "PRODUCT": "product_startup",
        "AGILE": "product_startup",
        "PROJECT": "product_startup",
        "STRATEGY": "product_startup",
        "STARTUP": "product_startup",
        "WORKING": "product_startup",
        "SKILL": "product_startup",
        "SKILLS": "product_startup",
        # UX/UI & Diseño
        "UXUI": "product_startup",
        "DESIGNTHINKING": "product_startup",
        "GRAPHIC": "product_startup",
        "DEV": "product_startup",
        "WEB": "product_startup",
        # Copywriting & Contenidos
        "COPY": "copywriting",
        "COPYWRITING": "copywriting",
        "CONTENT": "copywriting",
        "STORYTELLING": "copywriting",
        # Email Marketing
        "EMAILM": "email_marketing",
        "EMAIL": "email_marketing",
        # Ventas / Ofertas
        "VENTAS": "consultative_sales",
        "OFERTAS": "offers_pricing",
        # Funnels & Growth
        "FUNNELS": "funnels_cro",
        "GROWTH": "growth_loops",
        "JOURNEY": "customer_success",
        "MKTN": "funnels_cro",
        # Branding & Investigación
        "BRANDING": "branding_authority",
        "MARCAP": "branding_authority",
        "INVEST": "avatar_research",
        "AVATAR": "avatar_research",
        # Pauta Publicitaria
        "ADS": "paid_ads",
        "PAUTA": "paid_ads",
        # E-commerce
        "ECOM": "ecommerce_stores",
        "ECOMMERCE": "ecommerce_stores",
        # Automatizaciones
        "AUTOM": "automations_workflows",
        # IA & Prompting
        "AI": "ai_prompting_agents",
        "PROMPT": "ai_prompting_agents",
        # WhatsApp
        "WHATSAPP": "whatsapp_conversational",
    }

    # Mapeo retrocompatible
    TRACK_TAGS_MAP = PLATZI_TAGS_MAP

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
        """
        Busca coincidencias semánticas priorizando la máxima especificidad por longitud
        de frase compuesta (Longest Match). Resuelve ambigüedades favoreciendo frases
        compuestas específicas (ej: 'tiktok ad' -> paid_ads, 'google search ads' -> paid_ads)
        frente a palabras aisladas (ej: 'tiktok' -> social_media, 'search' -> seo_aeo).
        """
        norm_text = cls.normalize_text(text)
        if not norm_text:
            return None

        # Eliminar sufijos de extensión comunes adheridos a palabras (ej: 'Webdocx' -> 'Web')
        norm_text = re.sub(r"\b(docx|pdf|txt|md|srt)\b", "", norm_text).strip()

        best_score = (0, 0)
        best_cluster = None

        tie_order = [
            "paid_ads", "ai_prompting_agents", "whatsapp_conversational", "email_marketing",
            "funnels_cro", "offers_pricing", "copywriting", "seo_aeo", "data_analytics",
            "social_media", "ecommerce_stores", "automations_workflows", "branding_authority",
            "product_startup", "avatar_research", "consultative_sales", "customer_success", "growth_loops"
        ]

        for cluster in tie_order:
            kws = cls.THEMATIC_CLUSTERS.get(cluster, [])
            for kw in kws:
                norm_kw = cls.normalize_text(kw)
                pattern = r"\b" + re.escape(norm_kw) + r"\b"
                if re.search(pattern, norm_text, flags=re.IGNORECASE):
                    score = (len(norm_kw.split()), len(norm_kw))
                    if score > best_score:
                        best_score = score
                        best_cluster = cluster

        return best_cluster

    @classmethod
    def match_cluster_phrases(cls, text: str) -> Optional[str]:
        """Busca coincidencias exclusivamente en frases compuestas (>= 2 palabras)."""
        norm_text = cls.normalize_text(text)
        if not norm_text:
            return None
        norm_text = re.sub(r"\b(docx|pdf|txt|md|srt)\b", "", norm_text).strip()

        best_score = (0, 0)
        best_cluster = None

        tie_order = [
            "paid_ads", "ai_prompting_agents", "whatsapp_conversational", "email_marketing",
            "funnels_cro", "offers_pricing", "copywriting", "seo_aeo", "data_analytics",
            "social_media", "ecommerce_stores", "automations_workflows", "branding_authority",
            "product_startup", "avatar_research", "consultative_sales", "customer_success", "growth_loops"
        ]

        for cluster in tie_order:
            phrases = [kw for kw in cls.THEMATIC_CLUSTERS.get(cluster, []) if " " in kw]
            for kw in phrases:
                norm_kw = cls.normalize_text(kw)
                pattern = r"\b" + re.escape(norm_kw) + r"\b"
                if re.search(pattern, norm_text, flags=re.IGNORECASE):
                    score = (len(norm_kw.split()), len(norm_kw))
                    if score > best_score:
                        best_score = score
                        best_cluster = cluster

        return best_cluster

    @classmethod
    def profile_content_density(cls, text: str) -> Tuple[Optional[str], float, Dict[str, int]]:
        """
        Analiza la densidad léxica y semántica del texto real extraído de una lección
        contra las 18 especialidades canónicas.
        Pondera fuertemente frases compuestas (>= 2 palabras, 5 pts) sobre palabras aisladas (1.5 pts).
        Retorna (top_cluster, confidence_score, hit_counts) o (None, 0.0, {}) si no hay señal suficiente.
        """
        if not text or len(text.strip()) < 50:
            return (None, 0.0, {})

        sample = text[:50000].lower()
        norm_sample = unicodedata.normalize("NFC", sample)

        scores: Dict[str, float] = defaultdict(float)
        hits: Dict[str, int] = defaultdict(int)

        for cluster_key, terms in cls.THEMATIC_CLUSTERS.items():
            canon_key = cls.CANONICAL_CLUSTER_MAP.get(cluster_key, cluster_key)
            for term in terms:
                norm_term = unicodedata.normalize("NFC", term.lower().strip())
                if not norm_term:
                    continue
                pattern = r"\b" + re.escape(norm_term) + r"\b"
                count = len(re.findall(pattern, norm_sample))
                if count > 0:
                    hits[canon_key] += count
                    is_phrase = " " in norm_term
                    weight = 5.0 if is_phrase else 1.5
                    scores[canon_key] += count * weight

        if not scores:
            return (None, 0.0, {})

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_cluster, top_score = sorted_scores[0]
        second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0

        if top_score >= 8.0:
            return (top_cluster, top_score, dict(hits))

        return (None, 0.0, dict(hits))

    @classmethod
    def classify_cluster_bottom_up(cls, file_path: str, content: str = "") -> Tuple[str, str]:
        """
        Clasifica una ruta de archivo aplicando una estrategia polimórfica según proveedor:
        1. CONTENT-FIRST: Inspección semántica de texto real (>= 50 caracteres) si está disponible.
        2. FRASES CLAVE EN ARCHIVO: Máxima especificidad por frases compuestas (Longest Match).
        3. PLATZI: Detección estricta de tokens [TAG] en nombre de archivo o carpeta del curso.
        4. DIGITALMARKETER: Limpieza de slug sufijo y clasificación semántica por título de curso en inglés.
        5. SCVIP: Mapeo directo por carpeta temática numerada.
        6. CA: Detección de prefijo ca [TAG] o multinivel.
        7. LUIS-INESTROSA / MCV / VELOCITYMEDIA: Detección semántica por keywords del curso.
        """
        # 0. Inspección de Contenido (Content-First Semantic Profiling)
        if content and len(content.strip()) >= 50:
            c_dens, score_dens, _ = cls.profile_content_density(content)
            if c_dens and score_dens >= 12.0:
                canon_dens = cls.CANONICAL_CLUSTER_MAP.get(c_dens, c_dens)
                return (canon_dens, f"Content-first semantic profiling (score={score_dens:.1f})")

        norm_path = unicodedata.normalize("NFC", file_path)
        parts = [p for p in norm_path.split(os.sep) if p]

        if not parts:
            return ("general", "Ruta vacía")

        filename = parts[-1]
        parent_dir = parts[-2] if len(parts) >= 2 else ""
        grandparent_dir = parts[-3] if len(parts) >= 3 else ""

        # 1. Frases compuestas a nivel de archivo (máxima prioridad léxica)
        c_phrase_file = cls.match_cluster_phrases(filename)
        if c_phrase_file:
            canon = cls.CANONICAL_CLUSTER_MAP.get(c_phrase_file, c_phrase_file)
            return (canon, f"Frase clave en archivo: '{filename}'")

        # 2. Capa 0: Token universal de corchetes [TAG] en archivo o carpeta inmediata
        file_tags = re.findall(r"\[([A-Z0-9_\-\+]+)\]", filename)
        for raw_tag in file_tags:
            tag_up = raw_tag.upper()
            if tag_up in cls.PLATZI_TAGS_MAP:
                canon = cls.CANONICAL_CLUSTER_MAP.get(cls.PLATZI_TAGS_MAP[tag_up], cls.PLATZI_TAGS_MAP[tag_up])
                return (canon, f"Token [{tag_up}] en archivo")

        if len(parts) >= 2 and parts[-2] not in ("01_PLAN", "02_BUILD", "03_LAUNCH", "01_Content", "MP3"):
            parent_tags = re.findall(r"\[([A-Z0-9_\-\+]+)\]", parts[-2])
            for raw_tag in parent_tags:
                tag_up = raw_tag.upper()
                if tag_up in cls.PLATZI_TAGS_MAP:
                    canon = cls.CANONICAL_CLUSTER_MAP.get(cls.PLATZI_TAGS_MAP[tag_up], cls.PLATZI_TAGS_MAP[tag_up])
                    return (canon, f"Token [{tag_up}] en carpeta de curso")

        # Casos especiales de rutas conocidas
        if "PLATZI" in parts and "monetiza tu talento" in norm_path.lower():
            canon = cls.CANONICAL_CLUSTER_MAP.get("ai_prompting_agents", "ai_prompting_agents")
            return (canon, "Platzi track Monetiza tu Talento con IA")

        # 3. ESTRATEGIA CA: Detección de prefijos ca [TAG] o multinivel
        if "CA" in parts:
            if "MLM_58-18" in parts or "multinivel" in norm_path.lower():
                canon = cls.CANONICAL_CLUSTER_MAP.get("consultative_sales", "consultative_sales")
                return (canon, "CA prospección multinivel y ventas")

        # 4. ESTRATEGIA SCVIP: Carpetas temáticas numeradas
        if "SCVIP" in parts:
            lower_path = norm_path.lower()
            if "04. instagram" in lower_path or "04.instagram" in lower_path:
                return (cls.CANONICAL_CLUSTER_MAP.get("social_media", "social_media"), "SCVIP 04. INSTAGRAM")
            if "05. ventas" in lower_path or "05.ventas" in lower_path:
                return (cls.CANONICAL_CLUSTER_MAP.get("offers_pricing", "offers_pricing"), "SCVIP 05. VENTAS")
            if "06. meta ads" in lower_path or "06.meta ads" in lower_path:
                return (cls.CANONICAL_CLUSTER_MAP.get("paid_ads", "paid_ads"), "SCVIP 06. META ADS")
            if "07. marketing" in lower_path or "07.marketing" in lower_path:
                course_tag = cls.match_cluster_keywords(filename) or (cls.match_cluster_keywords(parts[-2]) if len(parts) >= 2 else None)
                if course_tag:
                    canon = cls.CANONICAL_CLUSTER_MAP.get(course_tag, course_tag)
                    return (canon, f"SCVIP 07. MARKETING ({canon})")
                if len(parts) >= 3:
                    c_deep = cls.match_cluster_keywords(parts[-3])
                    if c_deep:
                        canon = cls.CANONICAL_CLUSTER_MAP.get(c_deep, c_deep)
                        return (canon, f"SCVIP 07. MARKETING ({canon})")
                return ("general", "SCVIP 07. MARKETING sin coincidencia")

        # 5. ESTRATEGIA DIGITALMARKETER: Clasificación por título de curso en inglés (sin sufijo de slug)
        if "DIGITALMARKETER" in parts:
            dm_idx = parts.index("DIGITALMARKETER")
            course_part = ""
            if len(parts) > dm_idx + 2:
                course_part = parts[dm_idx + 2]
            elif len(parts) > dm_idx + 1:
                course_part = parts[dm_idx + 1]

            clean_dm_title = re.sub(r"_[a-z0-9\-]+$", "", course_part)
            clean_dm_title = clean_dm_title.replace("_", " ").strip()

            c_dm = cls.match_cluster_keywords(clean_dm_title)
            if c_dm:
                canon = cls.CANONICAL_CLUSTER_MAP.get(c_dm, c_dm)
                return (canon, f"DigitalMarketer curso: '{clean_dm_title}'")

        # 6. ESTRATEGIA LUIS-INESTROSA
        if "LUIS-INESTROSA" in parts:
            if "conferencias que venden" in norm_path.lower():
                canon = cls.CANONICAL_CLUSTER_MAP.get("consultative_sales", "consultative_sales")
                return (canon, "Luis Inestrosa conferencias que venden")
            if "habla y vendete bien" in norm_path.lower():
                canon = cls.CANONICAL_CLUSTER_MAP.get("consultative_sales", "consultative_sales")
                return (canon, "Luis Inestrosa habla y vendete bien")

        # 7. ESTRATEGIA GENERAL (Fallback semántico por capas concéntricas)
        # Nivel 1: Archivo
        c_file = cls.match_cluster_keywords(filename)
        if c_file:
            canon = cls.CANONICAL_CLUSTER_MAP.get(c_file, c_file)
            return (canon, f"Lección individual: '{filename}'")

        # Nivel 2: Módulo / Subcarpeta inmediata (evitando fases genéricas)
        if parent_dir and parent_dir not in ("01_PLAN", "02_BUILD", "03_LAUNCH", "01_Content", "MP3", "BASIC", "VIP", "PROFESIONAL"):
            c_parent = cls.match_cluster_keywords(parent_dir)
            if c_parent:
                canon = cls.CANONICAL_CLUSTER_MAP.get(c_parent, c_parent)
                return (canon, f"Módulo temático: '{parent_dir}'")

        # Nivel 3: Curso contenedor
        if grandparent_dir and grandparent_dir not in ("03_TRAINING_PLAYBOOKS_AND_WORKSHOPS", "01_AI_SYSTEMS", "02_PROGRAMS_AND_ACCELERATORS", "CURSOS", "PLATZI", "DIGITALMARKETER"):
            c_grand = cls.match_cluster_keywords(grandparent_dir)
            if c_grand:
                canon = cls.CANONICAL_CLUSTER_MAP.get(c_grand, c_grand)
                return (canon, f"Curso contenedor: '{grandparent_dir}'")

        # Nivel Fallback: Carpetas intermedias
        if len(parts) > 3:
            for p_part in reversed(parts[2:-2]):
                if p_part in ("03_TRAINING_PLAYBOOKS_AND_WORKSHOPS", "01_AI_SYSTEMS", "02_PROGRAMS_AND_ACCELERATORS", "CURSOS", "PLATZI", "DIGITALMARKETER", "baiosfera", "var", "www"):
                    continue
                c_part = cls.match_cluster_keywords(p_part)
                if c_part:
                    canon = cls.CANONICAL_CLUSTER_MAP.get(c_part, c_part)
                    return (canon, f"Directorio intermedio: '{p_part}'")

        return ("general", "Sin coincidencia temática")

    @classmethod
    def classify_cluster(cls, path_str: str, content: str = "") -> str:
        """Interfaz retrocompatible que retorna únicamente la clave de cluster."""
        cluster, _ = cls.classify_cluster_bottom_up(path_str, content=content)
        return cls.CANONICAL_CLUSTER_MAP.get(cluster, cluster)

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
    def is_scaffold_stub(cls, file_path: str) -> bool:
        """
        Detecta si un archivo .md o .txt es un cascarón vacío de scaffold (puntero a medios)
        que no contiene contenido educativo sustancial y nunca debe eclipsar subtítulos reales.
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in (".md", ".txt"):
            return False
        try:
            if not os.path.exists(file_path):
                return False
            size = os.path.getsize(file_path)
            if size > 15000:  # Archivos de más de 15KB tienen contenido real
                return False
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return False

        # 1. Marcadores inequívocos de listas de medios scaffold
        stub_patterns = [
            r"-\s+\*\*Video(?:\s+MP4)?:\*\*",
            r"-\s+\*\*Audio(?:\s+MP3)?:\*\*",
            r"-\s+\*\*Subt[ií]tulos(?:\s+[A-Z]{2})?:\*\*",
            r"-\s+Video(?:\s+MP4)?:\s*[`\w\-\.]+\.mp4",
        ]
        for p in stub_patterns:
            if re.search(p, content, re.I):
                return True

        # 2. Archivos ultracortos con múltiples punteros a extensiones de video/audio
        words = content.split()
        if len(words) < 60:
            media_hits = len(re.findall(r"\.(mp4|mp3|m4a|aac|srt|vtt)\b", content, re.I))
            if media_hits >= 2:
                return True

        return False

    @classmethod
    def is_non_llm_auxiliary(cls, file_path: str) -> bool:
        """
        Detecta si un archivo (típicamente PDF o docx) es material auxiliar
        imprimible o no apto para LLM: diapositivas/slides repetitivas,
        cuadernos/hojas de trabajo para rellenar, checklists impresos o quizzes.
        """
        fname = os.path.basename(file_path)
        clean_name = fname.replace("20", " ").lower()
        clean_name = re.sub(r"[-_]+", " ", clean_name)
        for pat in cls.NON_LLM_PATTERNS:
            if re.search(pat, clean_name, re.I):
                return True
        return False

    @classmethod
    def is_placeholder_or_duplicate(cls, file_path: str, content: str = "") -> bool:
        """
        Detecta si un archivo es un placeholder vacío, borrador sin contenido sustancial,
        o una copia duplicada sintáctica (ej: 'archivo (1).pdf', 'copia de...').
        """
        fname = os.path.basename(file_path).lower()
        clean_name = fname.replace("20", " ").replace("_", " ").replace("-", " ")
        clean_name = re.sub(r"\s+", " ", clean_name).strip()

        # 1. Copias duplicadas sintácticas en el nombre
        if re.search(r"(\(\d+\)|\bcopy\b|\bcopia\b|_copy)", fname, re.I):
            return True

        # 2. Placeholders en nombre de archivo
        placeholder_file_patterns = [
            r"\b(placeholder|contenido pendiente|en desarrollo|pr[oó]ximamente|borrador|draft|sample)\b",
            r"^(pendiente|draft|borrador)\b",
        ]
        for pat in placeholder_file_patterns:
            if re.search(pat, clean_name, re.I):
                return True

        # 3. Contenido de texto si fue suministrado
        if content:
            words = content.split()
            if len(words) < 50:
                short_text = content.lower()
                placeholder_content_patterns = [
                    r"\b(contenido pendiente|pr[oó]ximamente|coming soon|en construcci[oó]n|por definir|to be defined)\b",
                    r"\b(lorem ipsum|asdf)\b",
                ]
                for pat in placeholder_content_patterns:
                    if re.search(pat, short_text, re.I):
                        return True

        return False

    @classmethod
    def detect_course_language(cls, path_or_context: str) -> str:
        """
        Detecta si el curso es predominantemente en inglés o español para
        garantizar consistencia idiomática en la selección de subtítulos.
        """
        lower = path_or_context.lower()
        if "digitalmarketer" in lower:
            return "en"
        if "platzi" in lower:
            return "es"

        # Heurística léxica para CURSOS u otros proveedores
        norm = re.sub(r"[^a-z\s]", " ", lower)
        tokens = set(norm.split())

        en_indicators = {
            "the", "to", "and", "how", "for", "with", "marketing", "your",
            "of", "in", "from", "accelerator", "workshop", "masterclass",
            "playbook", "system", "systems", "scale", "traffic", "leads"
        }
        es_indicators = {
            "de", "la", "el", "en", "para", "con", "del", "los", "las",
            "curso", "taller", "ventas", "como", "crear", "estrategia",
            "negocio", "negocios", "marca", "embudo", "embudos"
        }

        en_score = len(tokens.intersection(en_indicators))
        es_score = len(tokens.intersection(es_indicators))

        if en_score > es_score and es_score == 0:
            return "en"
        return "es"

    @classmethod
    def scan_path(
        cls,
        base_dir: str,
        max_depth: int = 6,
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

                # 1. Correlación de Documentos Hermanos (Peer-Docs en carpeta padre) y Detección de Idioma
                parent_dir = os.path.dirname(current_dir)
                current_dir_name = os.path.basename(current_dir)
                has_peer_doc = cls.find_peer_document_in_parent(
                    parent_dir, current_dir_name, parent_cache
                )
                course_lang = cls.detect_course_language(current_dir)

                # 2. Agrupación por Stem de Lección en la carpeta actual
                stem_groups: Dict[str, List[Tuple[os.DirEntry, str]]] = defaultdict(list)
                for entry, ext in relevant_files:
                    stem = cls.extract_lesson_stem(entry.name)
                    stem_groups[stem].append((entry, ext))

                # 3. Jerarquía de Formatos por Stem (Anti-Redundancia)
                for stem, group in stem_groups.items():
                    raw_docs = [it for it in group if it[1] in (".docx", ".md", ".txt", ".pdf")]
                    subs = [it for it in group if it[1] in (".srt", ".vtt")]
                    audios = [it for it in group if it[1] in (".aac", ".m4a", ".mp3")]
                    videos = [it for it in group if it[1] == ".mp4"]

                    # Separar documentos maestros reales de cascarones de enlaces (scaffold stubs), placeholders/duplicados y material auxiliar no-LLM
                    docs = []
                    for entry, ext in raw_docs:
                        if cls.is_placeholder_or_duplicate(entry.path):
                            cls._register_resource(
                                resources, entry, ext,
                                tier="placeholder_duplicate",
                                canonical_upload=False,
                                reason_detail="Omitido: Archivo placeholder o copia duplicada",
                                has_peer_doc=has_peer_doc
                            )
                        elif cls.is_scaffold_stub(entry.path):
                            cls._register_resource(
                                resources, entry, ext,
                                tier="scaffold_stub",
                                canonical_upload=False,
                                reason_detail="Omitido: Archivo esqueleto de enlaces a medios",
                                has_peer_doc=has_peer_doc
                            )
                        elif cls.is_non_llm_auxiliary(entry.path):
                            cls._register_resource(
                                resources, entry, ext,
                                tier="auxiliary_non_llm",
                                canonical_upload=False,
                                reason_detail="Omitido: Material auxiliar no apto para LLM (slide deck, cuaderno de trabajo, checklist)",
                                has_peer_doc=has_peer_doc
                            )
                        else:
                            docs.append((entry, ext))

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
                        # Prioridad según idioma del curso para evitar mezclas Frankenstinianas
                        if course_lang == "en":
                            def sub_prio(item):
                                n = item[0].name.lower()
                                if n.endswith(".en.vtt"): return 0
                                if n.endswith(".en.srt"): return 1
                                if n.endswith(".vtt"): return 2
                                if n.endswith(".srt"): return 3
                                if n.endswith(".es.srt"): return 4
                                if n.endswith(".es.vtt"): return 5
                                return 6
                        else:
                            def sub_prio(item):
                                n = item[0].name.lower()
                                if n.endswith(".es.srt"): return 0
                                if n.endswith(".srt"): return 1
                                if n.endswith(".es.vtt"): return 2
                                if n.endswith(".vtt"): return 3
                                if n.endswith(".en.vtt"): return 4
                                if n.endswith(".en.srt"): return 5
                                return 6

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
    "seo": """Eres el Ingeniero Maestro de SEO Técnico, AEO (Answer Engine Optimization) y GEO (Generative Engine Optimization).
Tu objetivo es extraer las estrategias de optimización para motores de búsqueda tradicionales y modelos generativos de IA.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Extrae las arquitecturas de rastreo, indexación, Core Web Vitals y jerarquías canónicas de URL.
- Modela las metodologías de investigación de palabras clave, intención de búsqueda y mapas de tópicos semánticos.
- Documenta las estrategias de SEO para motores de respuesta de IA (ChatGPT Search, Perplexity, Google SGE/AI Overviews).
- Codifica los patrones de marcado estructurado Schema.org, auditorías técnicas con Google Search Console y análisis de Semrush.
""",
    "social_media": """Eres el Director de Estrategia de Redes Sociales Orgánicas, Formatos Cortos y Creación de Contenido.
Tu misión es destilar las heurísticas de viralidad, retención y construcción de comunidad en plataformas sociales.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Descompón los primeros 3 segundos de ganchos visuales y auditivos en Reels, TikTok y YouTube Shorts.
- Codifica las estrategias de contenido en LinkedIn para fundadores, marcas personales y venta B2B.
- Extrae las directivas de Community Management para convertir comentarios y mensajes directos en relaciones comerciales.
- Modela calendarios editoriales, reciclaje inteligente de formatos largos a piezas cortas y producción de podcasts.
""",
    "data_analytics": """Eres el Analista Principal de Métricas de Negocio, Analítica Digital y Tracking de Conversiones.
Tu función es extraer los modelos de medición, eventos de seguimiento e interpretación de datos comerciales.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Codifica la configuración de arquitecturas de medición con Google Analytics 4 (GA4) y Google Tag Manager (GTM).
- Extrae las definiciones matemáticas de métricas clave: CAC, LTV, ROAS, AOV, Churn Rate y tasa de conversión por etapa.
- Modela los cuadros de mando (dashboards) e informes de desempeño para identificar cuellos de botella en el embudo.
- Documenta las mejores prácticas para seguimiento con API de conversiones (CAPI) y mitigación de pérdidas por cookies de terceros.
""",
    "product_management": """Eres el Líder de Producto, Metodologías Ágiles y Validación de Startups.
Tu misión es extraer los marcos de Product Discovery, entrega ágil (Scrum/Agile) y desarrollo de modelos de negocio.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Modela los procesos de Product Discovery: validación de problemas, entrevistas con usuarios y definición de MVP.
- Codifica los rituales y artefactos de Scrum y Agile Delivery (sprints, backlogs, user stories, criterios de aceptación).
- Extrae las matrices estratégicas de toma de decisiones: Business Model Canvas, Value Proposition Canvas y análisis de riesgos.
- Documenta las tácticas de consecución de primeros clientes y tracción temprana para startups y nuevos productos.
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

        elif tier in ("direct_document", "direct_audio", "compendium_markdown"):
            is_audio = tier == "direct_audio"
            timeout = 600.0 if is_audio else 180.0
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

    target = getattr(args, "target_pos", None) or args.target
    paths = [target] if target else CourseScanner.DEFAULT_SEARCH_PATHS
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


def cmd_compact(args):
    """Ejecuta la compactación y fusión de lecciones en compendios Markdown unificados por (Curso, Cluster)."""
    print("==================================================================")
    print("📦 COMPACTACIÓN Y FUSIÓN DE CURSOS EN COMPENDIOS CANÓNICOS (v1.0)")
    print("==================================================================")

    target_cluster = args.cluster
    if target_cluster == "ads":
        target_cluster = "paid_ads"

    target_provider = args.provider.upper() if getattr(args, "provider", None) else None

    target = getattr(args, "target_pos", None) or args.target
    paths = [target] if target else CourseScanner.DEFAULT_SEARCH_PATHS
    all_scanned = []

    for p in paths:
        if not os.path.exists(p):
            continue
        found = CourseScanner.scan_path(p, max_depth=args.max_depth)
        all_scanned.extend(found)

    print(f"• Total archivos analizados: {len(all_scanned):,}")

    output_base_dir = getattr(args, "output_dir", None) or CourseCompactor.DEFAULT_OUTPUT_DIR
    is_dry_run = getattr(args, "dry_run", False)
    if is_dry_run:
        print("🔍 MODO SIMULACIÓN (--dry-run ACTIVO): No se escribirán archivos en disco.")

    compendiums = CourseCompactor.compact_all(
        scanned_items=all_scanned,
        target_cluster=target_cluster,
        target_provider=target_provider,
        output_base_dir=output_base_dir,
        dry_run=is_dry_run,
    )

    if not compendiums:
        print("⚠️ No se encontraron lecciones canónicas elegibles para compactar con los filtros provistos.")
        return

    total_lessons_absorbed = sum(c["lessons_count"] for c in compendiums)
    total_words = sum(c["words_count"] for c in compendiums)
    total_size = sum(c["size_bytes"] for c in compendiums)

    print(f"\n✅ COMPACTACIÓN FINALIZADA CON ÉXITO:")
    print(f"   • Compendios generados: {len(compendiums)} archivos maestros")
    print(f"   • Lecciones absorbidas: {total_lessons_absorbed:,} archivos individuales")
    reduction = ((total_lessons_absorbed - len(compendiums)) / total_lessons_absorbed * 100) if total_lessons_absorbed > 0 else 0
    print(f"   • Reducción de fuentes en NotebookLM: {reduction:.1f}%")
    print(f"   • Palabras consolidadas: {total_words:,}")
    print(f"   • Tamaño total en disco: {total_size / (1024*1024):.2f} MB")
    print(f"   • Directorio destino: {output_base_dir}")

    print("\n📋 LISTADO DE COMPENDIOS GENERADOS:")
    for c in compendiums:
        print(f"   - [{c['cluster'].upper()}] {c['filename']} ({c['lessons_count']} lecciones, {c['words_count']:,} palabras)")


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

    target = getattr(args, "target_pos", None) or args.target
    paths = [target] if target else CourseScanner.DEFAULT_SEARCH_PATHS
    candidates = []

    if getattr(args, "compendiums", False):
        compendiums_dir = getattr(args, "output_dir", None) or CourseCompactor.DEFAULT_OUTPUT_DIR
        print(f"• Modo Compendios Activo: Leyendo archivos consolidados desde {compendiums_dir}")
        cluster_dirs = (
            [os.path.join(compendiums_dir, target_cluster.lower())]
            if target_cluster
            else glob.glob(os.path.join(compendiums_dir, "*"))
        )
        for cdir in cluster_dirs:
            if not os.path.isdir(cdir):
                continue
            c_name = os.path.basename(cdir).lower()
            for fname in sorted(os.listdir(cdir)):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(cdir, fname)
                st = os.stat(fpath)
                fp = hashlib.sha256(f"{fname}:{st.st_size}:{int(st.st_mtime)}".encode("utf-8")).hexdigest()
                if fp not in uploaded:
                    candidates.append({
                        "path": fpath,
                        "filename": fname,
                        "name": fname,
                        "cluster": c_name,
                        "tier": "compendium_markdown",
                        "size_bytes": st.st_size,
                        "mtime": int(st.st_mtime),
                        "canonical_upload": True,
                        "target_notebook": CourseScanner.CLUSTER_NOTEBOOK_TITLES.get(
                            c_name, f"[ESPECIALIDAD_{c_name.upper()}]"
                        ),
                        "fingerprint": fp,
                    })
    else:
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
                    rel_p = (
                        os.path.relpath(item["path"], "/var/www/baiosfera")
                        if item["path"].startswith("/var/www/baiosfera")
                        else os.path.relpath(item["path"], "/var/www")
                    )
                    manifest_mgr.record_upload(
                        fingerprint=fp,
                        relative_path=rel_p,
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
    os.environ["KNOWLEDGE_SYNC_TEST"] = "1"
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
    assert CourseScanner.classify_cluster("PLATZI/03 ECOM/Curso de Supply Chain/01.mp4") == "ecommerce_stores"
    assert CourseScanner.classify_cluster("PLATZI/04 AUTOM/RPA/clase.mp4") == "automations_workflows"
    assert CourseScanner.classify_cluster("PLATZI/14 AI PROMPT/Agentes/clase.mp4") == "ai_prompting_agents"
    assert CourseScanner.classify_cluster("PLATZI/33 GRAPHIC THINKING UXUI/Tipografia/clase.mp4") == "product_startup"

    # Micro-clasificación: lección de email dentro de carpeta madre compuestas
    c_micro, reason = CourseScanner.classify_cluster_bottom_up(
        "PLATZI/59 CONTENT COPY EMAIL SEO STORYTELLING VENTAS/Curso/Modulo 2/01_secuencias_de_email.mp4"
    )
    assert c_micro == "email_marketing", f"Falla Test 4: Esperaba 'email_marketing' por micro-lección, obtuvo '{c_micro}'"

    # Desempate IA vs Copywriting vs Email vs Ofertas
    assert CourseScanner.classify_cluster("Marketing_Context_Vault.md") == "ai_prompting_agents"
    assert CourseScanner.classify_cluster("Cartas_de_Venta_PAS.docx") == "copywriting"
    assert CourseScanner.classify_cluster("Email_Promo_Campaign_Builder.md") == "email_marketing"
    assert CourseScanner.classify_cluster("AI_Gone_Wild_Create_a_Team_of_Ai_Assistants_with_Stackable_GPTs.es.srt") == "ai_prompting_agents"
    assert CourseScanner.classify_cluster("DigitalMarketer_Offer_Architect_2.0.md") == "offers_pricing"
    assert CourseScanner.classify_cluster("Build_Your_Winning_eCommerce_Product_Page.md") == "ecommerce_stores"
    assert CourseScanner.classify_cluster("Home_Page_Optimizer.md") == "funnels_cro"
    assert CourseScanner.classify_cluster("How_to_Attract_Your_First_5_Brand_Ambassadors.es.srt") == "branding_authority"
    # Longest Match & Blindaje Macro-First
    assert CourseScanner.match_cluster_keywords("Google Search Ads Playbook") == "paid_ads"
    assert CourseScanner.match_cluster_keywords("The 1-Call Close Masterclass") == "consultative_sales"
    assert CourseScanner.match_cluster_keywords("How to Launch Your First TikTok Ad: Profitability Within 30 Days") == "paid_ads"
    assert CourseScanner.match_cluster_keywords("VENTAS Curso de Whatsapp Business") == "whatsapp_conversational"
    assert CourseScanner.match_cluster_keywords("DEV Observabilidad de Agentes AI con LangSmith") == "ai_prompting_agents"
    assert CourseScanner.match_cluster_keywords("INVEST User Research Tecnicas para Investigacion Efectiva") == "avatar_research"
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

    # Test 8: Compactación Multi-Curso y Parsers Polimórficos (.docx, .srt, .md)
    with tempfile.TemporaryDirectory() as tmp_dir:
        course_dir = os.path.join(tmp_dir, "PLATZI", "59 CONTENT", "Curso de Email Marketing")
        os.makedirs(course_dir, exist_ok=True)

        docx_path = os.path.join(course_dir, "01_temario.docx")
        xml_content = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p><w:r><w:t>Temario completo de email marketing automatizado.</w:t></w:r></w:p>
            </w:body>
        </w:document>"""
        with zipfile.ZipFile(docx_path, "w") as z:
            z.writestr("word/document.xml", xml_content)

        srt_path = os.path.join(course_dir, "02_bienvenida.es.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("1\n00:00:01,000 --> 00:00:04,000\nBienvenidos a la clase de automatizacion de correos.\n")

        md_path = os.path.join(course_dir, "03_estrategia.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Estrategia de Email\nSegmentacion avanzada y lead nurturing.\n")

        # Escanear
        scanned = CourseScanner.scan_path(course_dir)
        canon_items = [i for i in scanned if i.get("canonical_upload", False)]
        assert len(canon_items) == 3, f"Falla Test 8: Esperaba 3 items canonicos, obtuve {len(canon_items)}"

        # Compactar
        comp_output_dir = os.path.join(tmp_dir, "compendiums")
        compendiums = CourseCompactor.compact_all(
            scanned_items=canon_items,
            output_base_dir=comp_output_dir,
        )

        assert len(compendiums) == 1, f"Falla Test 8: Debio generarse exactamente 1 compendio, pero hay {len(compendiums)}"
        c = compendiums[0]
        assert c["lessons_count"] == 3, f"Falla Test 8: Debio consolidar 3 lecciones, consolido {c['lessons_count']}"
        assert c["words_count"] > 10, f"Falla Test 8: Palabras insuficientes: {c['words_count']}"
        assert os.path.isfile(c["compendium_path"]), f"Falla Test 8: No se creo el archivo {c['compendium_path']}"

        with open(c["compendium_path"], "r", encoding="utf-8") as f:
            body = f.read()
            assert "Temario completo de email marketing" in body, "Falla Test 8: No extrajo .docx"
            assert "Bienvenidos a la clase de automatizacion" in body, "Falla Test 8: No extrajo .srt limpio"
            assert "Segmentacion avanzada" in body, "Falla Test 8: No extrajo .md"
    print("✓ [Test 8] Compactación Multi-Curso y Parsers Polimórficos (.docx, .srt, .md): PASSED")

    # Test 9: Detección de Cascarones (Scaffold Stubs) y Promoción de Subtítulos Reales
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = "02_real_lesson"
        stub_content = """# 02 Real Lesson
- **Video MP4:** 02_real_lesson.mp4
- **Audio MP3:** 02_real_lesson.mp3
- **Subtítulos ES:** 02_real_lesson.es.srt
"""
        with open(os.path.join(tmp_dir, f"{base}.md"), "w") as f:
            f.write(stub_content)

        sample_srt = """1
00:00:01,000 --> 00:00:04,500
En esta clase aprenderemos a construir ofertas de alta conversión y valor irresistible.
"""
        with open(os.path.join(tmp_dir, f"{base}.es.srt"), "w") as f:
            f.write(sample_srt)

        with open(os.path.join(tmp_dir, f"{base}.mp4"), "w") as f:
            f.write("dummy video")

        scanned = CourseScanner.scan_path(tmp_dir)
        stub_item = next((i for i in scanned if i["path"].endswith(".md")), None)
        assert stub_item is not None, "Falla Test 9: No se encontró el .md"
        assert stub_item["tier"] == "scaffold_stub", f"Falla Test 9: El stub debió ser 'scaffold_stub', fue '{stub_item['tier']}'"
        assert not stub_item["canonical_upload"], "Falla Test 9: El stub no debe ser canonical_upload"

        sub_item = next((i for i in scanned if i["path"].endswith(".es.srt")), None)
        assert sub_item is not None, "Falla Test 9: No se encontró el .es.srt"
        assert sub_item["canonical_upload"], "Falla Test 9: El subtítulo real debió ser promovido a canonical_upload"
        assert sub_item["tier"] == "subtitle_text", f"Falla Test 9: El subtítulo debió ser 'subtitle_text', fue '{sub_item['tier']}'"
    print("✓ [Test 9] Detección de Scaffold Stubs & Promoción de Subtítulo Real: PASSED")

    # Test 10: Detección y Exclusión de Material Auxiliar no-LLM (Slide Decks, Worksheets, Cuadernos de Trabajo)
    assert CourseScanner.is_non_llm_auxiliary("slides-curso-para-crear-un-brief-creativo.pdf")
    assert CourseScanner.is_non_llm_auxiliary("innovacion-y-creacion-de-productos_CUADERNO-DE-TRABAJO.pdf")
    assert CourseScanner.is_non_llm_auxiliary("How20To20Get20The20Most20-20Slide20Deck.pdf")
    assert CourseScanner.is_non_llm_auxiliary("Automate-Your-Client-On-boarding-Worksheet.pdf")
    assert CourseScanner.is_non_llm_auxiliary("01a. Libro de Trabajo.pdf")
    assert CourseScanner.is_non_llm_auxiliary("Marketing-Audit-Printable-Checklist.pdf")
    assert not CourseScanner.is_non_llm_auxiliary("Guia-Estrategica-Email-Marketing.pdf")
    assert not CourseScanner.is_non_llm_auxiliary("The-Ultimate-Prompting-Manual.pdf")

    with tempfile.TemporaryDirectory() as tmp_dir:
        slide_pdf = os.path.join(tmp_dir, "Course_Slide_Deck.pdf")
        with open(slide_pdf, "w") as f:
            f.write("dummy pdf")
        guide_pdf = os.path.join(tmp_dir, "Course_Strategy_Guide.pdf")
        with open(guide_pdf, "w") as f:
            f.write("dummy pdf guide")

        scanned = CourseScanner.scan_path(tmp_dir)
        slide_item = next((i for i in scanned if i["path"] == slide_pdf), None)
        guide_item = next((i for i in scanned if i["path"] == guide_pdf), None)

        assert slide_item is not None, "Falla Test 10: No se escaneó el slide deck"
        assert slide_item["tier"] == "auxiliary_non_llm", f"Falla Test 10: El slide debió ser 'auxiliary_non_llm', fue '{slide_item['tier']}'"
        assert not slide_item["canonical_upload"], "Falla Test 10: El slide deck no debe ser canonical_upload"

        assert guide_item is not None, "Falla Test 10: No se escaneó la guía"
        assert guide_item["canonical_upload"], "Falla Test 10: La guía real debió ser canonical_upload"
    print("✓ [Test 10] Detección & Exclusión de Material Auxiliar no-LLM (Slides/Worksheets/Checklists): PASSED")

    # Test 11: Detección de Idioma de Curso y Consistencia de Subtítulos (.en vs .es)
    assert CourseScanner.detect_course_language("/var/www/baiosfera/DIGITALMARKETER/03_TRAINING/How_To_Scale") == "en"
    assert CourseScanner.detect_course_language("/var/www/baiosfera/PLATZI/01_CONTENT/Curso_De_Ventas") == "es"

    with tempfile.TemporaryDirectory() as tmp_dir:
        en_course = os.path.join(tmp_dir, "DIGITALMARKETER", "Client_Onboarding")
        os.makedirs(en_course, exist_ok=True)
        # Crear subtítulos inglés y español para la misma lección
        with open(os.path.join(en_course, "lesson1.en.vtt"), "w") as f:
            f.write("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nWelcome to onboarding automation.")
        with open(os.path.join(en_course, "lesson1.es.srt"), "w") as f:
            f.write("1\n00:00:01,000 --> 00:00:04,000\nBienvenido a la automatizacion.")

        scanned_en = CourseScanner.scan_path(en_course)
        canon_en = [i for i in scanned_en if i.get("canonical_upload", False)]
        assert len(canon_en) == 1, f"Falla Test 11: Debió seleccionarse 1 subtítulo primario, hubo {len(canon_en)}"
        assert canon_en[0]["filename"] == "lesson1.en.vtt", (
            f"Falla Test 11: Curso en inglés debió priorizar .en.vtt sobre .es.srt, pero seleccionó '{canon_en[0]['filename']}'"
        )

        es_course = os.path.join(tmp_dir, "PLATZI", "Curso_De_Ventas")
        os.makedirs(es_course, exist_ok=True)
        with open(os.path.join(es_course, "leccion1.en.vtt"), "w") as f:
            f.write("WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nWelcome to sales.")
        with open(os.path.join(es_course, "leccion1.es.srt"), "w") as f:
            f.write("1\n00:00:01,000 --> 00:00:04,000\nBienvenidos a ventas.")

        scanned_es = CourseScanner.scan_path(es_course)
        canon_es = [i for i in scanned_es if i.get("canonical_upload", False)]
        assert len(canon_es) == 1, f"Falla Test 11: Debió seleccionarse 1 subtítulo primario, hubo {len(canon_es)}"
        assert canon_es[0]["filename"] == "leccion1.es.srt", (
            f"Falla Test 11: Curso en español debió priorizar .es.srt sobre .en.vtt, pero seleccionó '{canon_es[0]['filename']}'"
        )
    print("✓ [Test 11] Detección de Idioma & Consistencia de Subtítulos (.en vs .es): PASSED")

    # Test 12: Deduplicación Intra-Curso de Secciones Idénticas y Sanitización de Títulos
    with tempfile.TemporaryDirectory() as tmp_dir:
        comp_dir = os.path.join(tmp_dir, "output")
        identical_content = "# Welcome Overview\nHere is the detailed overview of our strategy."
        items = [
            {
                "path": os.path.join(tmp_dir, "01_Overview.md"),
                "filename": "01_Overview.md",
                "ext": ".md",
                "size_bytes": len(identical_content),
                "canonical_upload": True,
            },
            {
                "path": os.path.join(tmp_dir, "06_Resources20Duplicate.md"),
                "filename": "06_Resources20Duplicate.md",
                "ext": ".md",
                "size_bytes": len(identical_content),
                "canonical_upload": True,
            },
            {
                "path": os.path.join(tmp_dir, "02_Deep_Dive.md"),
                "filename": "02_Deep_Dive.md",
                "ext": ".md",
                "size_bytes": len(identical_content) + 50,
                "canonical_upload": True,
            },
        ]
        with open(items[0]["path"], "w") as f:
            f.write(identical_content)
        with open(items[1]["path"], "w") as f:
            f.write(identical_content)  # Duplicado
        with open(items[2]["path"], "w") as f:
            f.write("# Deep Dive\nUnique and rich tactical implementation material.")

        comp = CourseCompactor.compact_group(
            provider="DIGITALMARKETER",
            cluster="automatizaciones",
            course_name="Client Onboarding",
            items=items,
            output_base_dir=comp_dir,
        )
        assert comp is not None, "Falla Test 12: No se generó el compendio"
        assert comp["lessons_count"] == 2, f"Falla Test 12: Se esperaba dedup a 2 lecciones, hubo {comp['lessons_count']}"

        with open(comp["compendium_path"], "r") as f:
            body = f.read()
            # Verificar renumeración continua 1. y 2. sin huecos
            assert "1. **Overview**" in body
            assert "2. **Deep Dive**" in body
            assert "3. **" not in body
    print("✓ [Test 12] Deduplicación Intra-Curso y Sanitización Continua: PASSED")

    # Test 13: Content-First Semantic Profiler en Lecciones Genéricas
    generic_text = (
        "En esta clase aprenderemos cómo escalar las campañas publicitarias en Meta Ads. "
        "Configuraremos el Business Manager, optimizaremos los anuncios en Instagram y Facebook, "
        "y analizaremos métricas clave como el ROAS, CPA y CPM mediante el pixel de Meta y el API CAPI. "
        "Estructuraremos creativos para anuncios de alto impacto y retargeting a audiencias personalizadas."
    )
    c_dens, r_dens = CourseScanner.classify_cluster_bottom_up(
        "/var/www/baiosfera/CURSOS/Generico/05_clase_generica.txt",
        content=generic_text
    )
    assert c_dens == "paid_ads", f"Falla Test 13: Esperaba 'paid_ads', obtuvo '{c_dens}'"
    assert "Content-first semantic profiling" in r_dens, f"Falla Test 13: Esperaba profiling por contenido, razón: {r_dens}"
    print("✓ [Test 13] Content-First Semantic Profiler en Lecciones Genéricas: PASSED")

    # Test 14: Partición Multi-Compendio en Cursos Híbridos (p. ej. Social Media + Paid Ads)
    with tempfile.TemporaryDirectory() as tmp_dir:
        course_dir = os.path.join(tmp_dir, "PLATZI", "04. INSTAGRAM", "Curso de Instagram para Negocios")
        os.makedirs(course_dir, exist_ok=True)

        items_hybrid = [
            {
                "path": os.path.join(course_dir, "01_Estrategia_de_Reels_y_Comunidad.md"),
                "filename": "01_Estrategia_de_Reels_y_Comunidad.md",
                "ext": ".md",
                "size_bytes": 500,
                "tier": "direct_document",
                "canonical_upload": True,
                "cluster": "social_media",
            },
            {
                "path": os.path.join(course_dir, "02_Crecimiento_Organico_y_Carruseles.md"),
                "filename": "02_Crecimiento_Organico_y_Carruseles.md",
                "ext": ".md",
                "size_bytes": 600,
                "tier": "direct_document",
                "canonical_upload": True,
                "cluster": "social_media",
            },
            {
                "path": os.path.join(course_dir, "03_Campañas_en_Meta_Ads_y_Pauta.md"),
                "filename": "03_Campañas_en_Meta_Ads_y_Pauta.md",
                "ext": ".md",
                "size_bytes": 700,
                "tier": "direct_document",
                "canonical_upload": True,
                "cluster": "paid_ads",
            },
        ]
        with open(items_hybrid[0]["path"], "w") as f:
            f.write("# Reels y Comunidad\nEstrategia completa de contenido orgánico para crear comunidad sólida y engagement en Instagram para negocios.")
        with open(items_hybrid[1]["path"], "w") as f:
            f.write("# Carruseles y Algoritmo\nPublicación regular y engagement orgánico optimizado para distribución masiva y alcance de nuevos seguidores.")
        with open(items_hybrid[2]["path"], "w") as f:
            f.write("# Meta Ads y Pauta\nPauta publicitaria profesional y campañas de conversión pagadas optimizando creativos, presupuestos, pixel de Meta y retargeting avanzado en Business Manager.")

        comp_output = os.path.join(tmp_dir, "compendiums")
        comps = CourseCompactor.compact_all(
            scanned_items=items_hybrid,
            output_base_dir=comp_output,
        )
        assert len(comps) == 2, f"Falla Test 14: Debieron generarse 2 compendios particionados, hubo {len(comps)}"
        clusters_found = {c["cluster"] for c in comps}
        assert clusters_found == {"social_media", "paid_ads"}, f"Falla Test 14: Clusters inesperados {clusters_found}"
    print("✓ [Test 14] Partición Multi-Compendio por Especialidad en Cursos Híbridos: PASSED")

    # Test 15: Encabezados Limpios Anti-Slop (Cero debug blockquotes, TOC directo)
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = os.path.join(tmp_dir, "01_Clase.md")
        with open(test_file, "w") as f:
            f.write(
                "# Introducción y Fundamentos\n"
                "Contenido formativo de alto valor sobre marketing, tráfico pagado y optimización de conversión "
                "para estructurar embudos rentables con ROAS positivo y escalabilidad continua."
            )
        single_item = [{
            "path": test_file,
            "filename": "01_Clase.md",
            "ext": ".md",
            "size_bytes": 100,
            "tier": "direct_document",
            "canonical_upload": True,
        }]
        comp_clean = CourseCompactor.compact_group(
            provider="PLATZI",
            cluster="paid_ads",
            course_name="Master en Meta Ads",
            items=single_item,
            output_base_dir=tmp_dir,
        )
        assert comp_clean is not None, "Falla Test 15: No se generó el compendio limpio"
        with open(comp_clean["compendium_path"], "r") as f:
            clean_body = f.read()
            assert clean_body.startswith("# [PLATZI] [PAID_ADS] — Master en Meta Ads\n\n## 📑 Índice de Lecciones y Documentos"), (
                f"Falla Test 15: El encabezado no sigue la estructura limpia: {clean_body[:100]}"
            )
            assert "> **Especialidad" not in clean_body, "Falla Test 15: Persiste bloque de debug de especialidad"
            assert "> **Fecha de Generación" not in clean_body, "Falla Test 15: Persiste bloque de debug de fecha"
            assert "> **Volumen Estimado" not in clean_body, "Falla Test 15: Persiste bloque de debug de volumen"
    print("✓ [Test 15] Encabezados Limpios Anti-Slop y TOC Directo: PASSED")

    # Test 16: Detección y Exclusión de Placeholders y Copias Duplicadas
    assert CourseScanner.is_placeholder_or_duplicate("01_clase (1).pdf"), "Falla Test 16: No detectó (1)"
    assert CourseScanner.is_placeholder_or_duplicate("02_Contenido Pendiente.txt"), "Falla Test 16: No detectó Contenido Pendiente"
    assert CourseScanner.is_placeholder_or_duplicate("03_draft_intro.docx"), "Falla Test 16: No detectó draft"
    assert CourseScanner.is_placeholder_or_duplicate("04_clase_copy.md"), "Falla Test 16: No detectó copy"
    assert CourseScanner.is_placeholder_or_duplicate("05_normal.txt", content="Contenido pendiente por definir."), "Falla Test 16: No detectó contenido placeholder"
    assert not CourseScanner.is_placeholder_or_duplicate("01_clase_estrategica.md", content="Contenido educativo profundo de marketing estratégico."), "Falla Test 16: Falso positivo en lección legítima"

    with tempfile.TemporaryDirectory() as tmp_dir:
        with open(os.path.join(tmp_dir, "01_clase (1).pdf"), "w") as f:
            f.write("dummy")
        with open(os.path.join(tmp_dir, "02_Contenido Pendiente.txt"), "w") as f:
            f.write("dummy")
        with open(os.path.join(tmp_dir, "03_leccion_valida.md"), "w") as f:
            f.write("Leccion valida y completa")

        scanned_ph = CourseScanner.scan_path(tmp_dir)
        ph_items = [i for i in scanned_ph if i["tier"] == "placeholder_duplicate"]
        canon_ph = [i for i in scanned_ph if i.get("canonical_upload", False)]
        assert len(ph_items) == 2, f"Falla Test 16: Debieron detectarse 2 placeholders, hubo {len(ph_items)}"
        assert len(canon_ph) == 1, f"Falla Test 16: Solo 1 lección debió ser canónica, hubo {len(canon_ph)}"
        assert canon_ph[0]["filename"] == "03_leccion_valida.md"
    print("✓ [Test 16] Detección de Placeholders y Copias Duplicadas: PASSED")

    # Test 17: Integridad de Taxonomía Canónica de 18 Especialidades
    assert len(CourseScanner.THEMATIC_CLUSTERS) == 18, f"Falla Test 17: Se esperaban 18 especialidades, hay {len(CourseScanner.THEMATIC_CLUSTERS)}"
    assert len(CourseScanner.CLUSTER_NOTEBOOK_TITLES) == 18, f"Falla Test 17: Se esperaban 18 títulos de cuadernos, hay {len(CourseScanner.CLUSTER_NOTEBOOK_TITLES)}"
    for cluster_k in CourseScanner.THEMATIC_CLUSTERS:
        assert cluster_k in CourseScanner.CLUSTER_NOTEBOOK_TITLES, f"Falla Test 17: Falta título para cluster {cluster_k}"
        assert CourseScanner.CANONICAL_CLUSTER_MAP.get(cluster_k) == cluster_k, f"Falla Test 17: {cluster_k} no es auto-canónico"
    print("✓ [Test 17] Integridad Absoluta de Taxonomía Canónica de 18 Especialidades: PASSED")

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
    scan_parser.add_argument("target_pos", nargs="?", default=None, help="Directorio objetivo opcional (posicional)")
    scan_parser.add_argument("--target", type=str, default=None, help="Directorio objetivo específico")
    scan_parser.add_argument("--max-depth", type=int, default=6, help="Profundidad máxima de escaneo")
    scan_parser.add_argument("--dry-run", action="store_true", help="Tolerado por conveniencia (scan ya es solo lectura por defecto)")

    # Subcomando: compact
    compact_parser = subparsers.add_parser(
        "compact",
        help="Compacta y fusiona cursos en compendios Markdown unificados por (Curso, Cluster)",
    )
    compact_parser.add_argument("target_pos", nargs="?", default=None, help="Directorio objetivo opcional (posicional)")
    compact_parser.add_argument("--target", type=str, default=None, help="Directorio objetivo específico")
    compact_parser.add_argument("--cluster", type=str, default=None, help="Filtrar por cluster específico (ecommerce, funnels, etc.)")
    compact_parser.add_argument("--provider", type=str, default=None, help="Filtrar por proveedor específico (PLATZI, DIGITALMARKETER, etc.)")
    compact_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directorio destino para compendios (default: /var/www/localstorage/knowledge_cache/compendiums)",
    )
    compact_parser.add_argument("--max-depth", type=int, default=6, help="Profundidad máxima de escaneo")
    compact_parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir compendios en disco")

    # Subcomando: init-clusters
    init_parser = subparsers.add_parser(
        "init-clusters",
        help="Pre-aprovisiona los 15 cuadernos de cluster, inyecta system prompts y exporta clusters.json",
    )

    # Subcomando: push
    push_parser = subparsers.add_parser("push", help="Ingesta incremental hacia NotebookLM")
    push_parser.add_argument("target_pos", nargs="?", default=None, help="Directorio objetivo opcional (posicional)")
    push_parser.add_argument("--target", type=str, default=None, help="Directorio objetivo específico")
    push_parser.add_argument("--cluster", type=str, default=None, help="Filtrar por cluster específico (ecommerce, funnels, etc.)")
    push_parser.add_argument("--limit", type=int, default=None, help="Límite máximo de archivos a subir en esta pasada")
    push_parser.add_argument("--delay", type=float, default=5.0, help="Delay entre subidas en segundos")
    push_parser.add_argument("--max-depth", type=int, default=6, help="Profundidad máxima de escaneo")
    push_parser.add_argument(
        "--compendiums",
        action="store_true",
        help="Sube los compendios consolidados en vez de archivos individuales",
    )
    push_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directorio de origen de compendios (default: /var/www/localstorage/knowledge_cache/compendiums)",
    )
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
    elif args.command == "compact":
        cmd_compact(args)
    elif args.command == "init-clusters":
        cmd_init_clusters(args)
    elif args.command == "push":
        cmd_push(args)


if __name__ == "__main__":
    main()
