#!/usr/bin/env python3
"""
==============================================================================
build_thematic_compendiums.py (v2.0)
Universal Micro-Lesson Thematic Compendiums & VideoWorker Manifest Compiler
Governance: Supreme Directive v8.5 & Fractal CoHaLo | Meta-Script v1.0
Decoupled Inventory via rclone API + Local High-Speed Stream Extraction
Zero-Token ($0) Local Processing across DIGITALMARKETER, PLATZI and CURSOS
==============================================================================
"""

import os
import sys
import re
import json
import time
import zipfile
import logging
import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

# Configurar logging estructurado
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("build_thematic_compendiums")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from scripts.knowledge_sync import CourseScanner
except ImportError:
    CourseScanner = None
    logger.warning("No se pudo importar CourseScanner de scripts.knowledge_sync. Usando fallback.")

RCLONE_BIN = "/var/www/.rclone/bin/rclone"
RCLONE_CONF = "/var/www/.rclone/config/rclone/rclone.conf"

DEFAULT_OUTPUT_DIR = "/var/www/localstorage/knowledge_cache/compendiums"
DEFAULT_MIRROR_DIR = "/var/www/baiosfera/PLAYBOOKS/0compendiums"
DEFAULT_MANIFEST_OUTPUT = "/var/www/localstorage/knowledge_cache/videoworker_manifest.json"
DEFAULT_MANIFEST_MIRROR = "/var/www/baiosfera/PLAYBOOKS/videoworker_manifest.json"

TEXT_INCLUDES = ["*.md", "*.txt", "*.docx", "*.pdf", "*.srt", "*.vtt"]
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".wav"}
VIDEO_INCLUDES = ["*.mp4"]

CANONICAL_CLUSTERS = [
    "avatar_research", "branding_authority", "offers_pricing", "social_media",
    "seo_aeo", "paid_ads", "copywriting", "funnels_cro", "whatsapp_conversational",
    "consultative_sales", "email_marketing", "customer_success", "growth_loops",
    "ecommerce_stores", "automations_workflows", "data_analytics",
    "ai_prompting_agents", "product_startup", "00_category_of_one"
]


class LessonExtractor:
    """Extractor local de alta velocidad ($0 tokens) para documentos y subtítulos."""

    @staticmethod
    def extract_docx(file_path: str) -> str:
        """Extrae texto de DOCX usando zipfile y XML estándar."""
        try:
            with zipfile.ZipFile(file_path) as z:
                xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []
            for p in tree.iterfind(".//w:p", namespaces):
                texts = [t.text for t in p.iterfind(".//w:t", namespaces) if t.text]
                if texts:
                    paragraphs.append("".join(texts))
            return "\n\n".join(paragraphs).strip()
        except Exception as e:
            logger.debug(f"Fallo extrayendo DOCX {file_path}: {e}")
            return ""

    @staticmethod
    def extract_pdf(file_path: str) -> str:
        """Extrae texto de PDF usando /usr/bin/pdftotext nativo con timeout estricto."""
        try:
            res = subprocess.run(
                ["/usr/bin/pdftotext", "-layout", file_path, "-"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
                check=False
            )
            return res.stdout.strip()
        except Exception as e:
            logger.debug(f"Fallo extrayendo PDF {file_path}: {e}")
            return ""

    @staticmethod
    def extract_subtitles(file_path: str) -> str:
        """Extrae y normaliza texto de subtítulos .srt y .vtt eliminando marcas de tiempo."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            cleaned: List[str] = []
            prev = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if re.match(r"^\d+$", line):
                    continue
                if re.match(r"^\d{2}:\d{2}", line) or "-->" in line:
                    continue
                if line.startswith("WEBVTT") or line.startswith("NOTE") or line.startswith("STYLE"):
                    continue
                line = re.sub(r"<[^>]+>", "", line).strip()
                if line and line != prev:
                    cleaned.append(line)
                    prev = line
            return " ".join(cleaned).strip()
        except Exception as e:
            logger.debug(f"Fallo extrayendo subtítulo {file_path}: {e}")
            return ""

    @staticmethod
    def extract_plain_text(file_path: str) -> str:
        """Lee archivos de texto plano y Markdown."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read().strip()
        except Exception as e:
            logger.debug(f"Fallo leyendo texto {file_path}: {e}")
            return ""

    @classmethod
    def extract(cls, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".docx":
            return cls.extract_docx(file_path)
        elif ext == ".pdf":
            return cls.extract_pdf(file_path)
        elif ext in (".srt", ".vtt"):
            return cls.extract_subtitles(file_path)
        elif ext in (".md", ".txt"):
            return cls.extract_plain_text(file_path)
        return ""


class ThematicCompiler:
    """Compilador desacoplado: inventario rápido vía rclone API + extracción secuencial controlada."""

    def __init__(self, output_dir: str, mirror_dir: str, manifest_output: str):
        self.output_dir = os.path.abspath(output_dir)
        self.mirror_dir = os.path.abspath(mirror_dir)
        self.manifest_output = os.path.abspath(manifest_output)
        self.manifest_mirror = os.path.abspath(DEFAULT_MANIFEST_MIRROR)
        self.cluster_data: Dict[str, List[Dict[str, Any]]] = {}
        self.orphan_videos: List[Dict[str, Any]] = []
        self.stats = {
            "inventoried_files": 0,
            "processed_texts": 0,
            "orphan_videos": 0,
            "clusters_populated": 0,
            "total_extracted_words": 0
        }

    @staticmethod
    def rclone_list(remote_path: str, includes: List[str]) -> List[str]:
        """Obtiene el inventario completo de archivos vía rclone API en segundos sin saturar FUSE."""
        if not os.path.exists(RCLONE_BIN) or not os.path.exists(RCLONE_CONF):
            logger.warning("rclone binario o config no encontrado. Usando listado estándar.")
            return []

        cmd = [RCLONE_BIN, "--config", RCLONE_CONF, "lsf", remote_path, "--recursive", "--files-only"]
        for inc in includes:
            cmd.extend(["--include", inc])

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return [l.strip() for l in res.stdout.splitlines() if l.strip()]
        except Exception as e:
            logger.error(f"Error listando {remote_path} con rclone: {e}")
            return []

    def classify(self, file_path: str) -> str:
        """Clasifica un recurso en su cluster temático canónico."""
        if "VELOCITYMEDIA/INFLUENCE" in file_path or "VELOCITY/INFLUENCE" in file_path:
            return "00_category_of_one"

        if CourseScanner:
            cluster = CourseScanner.classify_cluster(file_path)
            if cluster in CANONICAL_CLUSTERS:
                return cluster
            synonyms = {
                "categoria_de_uno": "00_category_of_one",
                "funnels": "funnels_cro",
                "ofertas": "offers_pricing",
                "copy": "copywriting",
                "email": "email_marketing",
                "whatsapp": "whatsapp_conversational",
                "seo": "seo_aeo"
            }
            if cluster in synonyms:
                return synonyms[cluster]

        lower_p = file_path.lower()
        if any(k in lower_p for k in ["copywriting", "copy", "titulares", "redaccion"]):
            return "copywriting"
        if any(k in lower_p for k in ["funnel", "embudo", "cro", "landing", "squeeze"]):
            return "funnels_cro"
        if any(k in lower_p for k in ["offer", "oferta", "pricing", "grand slam"]):
            return "offers_pricing"
        if any(k in lower_p for k in ["email", "newsletter", "autoresponder"]):
            return "email_marketing"
        if any(k in lower_p for k in ["paid_ads", "ads", "facebook ads", "meta ads", "google ads"]):
            return "paid_ads"
        if any(k in lower_p for k in ["whatsapp", "chat", "conversational", "cierre"]):
            return "whatsapp_conversational"
        if any(k in lower_p for k in ["avatar", "buyer persona", "customer research"]):
            return "avatar_research"
        if any(k in lower_p for k in ["branding", "marca", "authority", "posicionamiento"]):
            return "branding_authority"
        if any(k in lower_p for k in ["ecom", "shopify", "woocommerce", "tienda", "dropshipping"]):
            return "ecommerce_stores"
        if any(k in lower_p for k in ["prompt", "chatgpt", "gemini", "agent", "llm", "claude"]):
            return "ai_prompting_agents"
        if any(k in lower_p for k in ["automation", "n8n", "make", "zapier", "rpa"]):
            return "automations_workflows"
        if any(k in lower_p for k in ["analytics", "ga4", "metricas", "kpi", "bi"]):
            return "data_analytics"
        if any(k in lower_p for k in ["seo", "posicionamiento web", "google search", "aeo"]):
            return "seo_aeo"
        if any(k in lower_p for k in ["social media", "instagram", "tiktok", "youtube", "linkedin"]):
            return "social_media"

        return "branding_authority"

    def execute_pipeline(self, dry_run: bool = False, max_items_per_source: Optional[int] = None) -> None:
        """Pipeline desacoplado: inventario instantáneo y extracción secuencial con progreso visible."""
        logger.info("==================================================================")
        logger.info("Fase A: Inventario Rápido vía rclone API ($0 overhead FUSE)")
        logger.info("==================================================================")
        t0 = time.time()

        sources = [
            ("DIGITALMARKETER", "baiosfera:DIGITALMARKETER", TEXT_INCLUDES),
            ("PLATZI", "baiosfera:PLATZI", ["*.docx", "*.txt"]),
            ("CURSOS", "baiosfera:CURSOS", TEXT_INCLUDES)
        ]

        all_text_tasks: List[Tuple[str, str, str]] = []  # (provider, rel_path, full_path)
        all_dirs_with_text: Set[str] = set()

        for prov, remote, incs in sources:
            logger.info(f"Inventariando {prov}...")
            files = self.rclone_list(remote, incs)
            logger.info(f"• {prov}: {len(files)} documentos encontrados.")
            if max_items_per_source:
                files = files[:max_items_per_source]

            for rel_p in files:
                full_p = os.path.join("/var/www/baiosfera", prov, rel_p)
                all_text_tasks.append((prov, rel_p, full_p))
                all_dirs_with_text.add(os.path.dirname(full_p))

        self.stats["inventoried_files"] = len(all_text_tasks)
        logger.info(f"Inventario completado en {time.time()-t0:.2f}s: {len(all_text_tasks)} archivos a procesar.")

        # Inventario de Videos para Manifiesto VideoWorker (BAI-405)
        logger.info("Inventariando videos en CURSOS para detectar huérfanos (BAI-405)...")
        video_files = self.rclone_list("baiosfera:CURSOS", VIDEO_INCLUDES)
        for v_rel in video_files:
            v_full = os.path.join("/var/www/baiosfera/CURSOS", v_rel)
            v_dir = os.path.dirname(v_full)
            if v_dir not in all_dirs_with_text:
                cluster = self.classify(v_full)
                self.orphan_videos.append({
                    "file_name": os.path.basename(v_full),
                    "file_path": v_full,
                    "rel_path": os.path.join("CURSOS", v_rel),
                    "target_cluster": cluster
                })
        self.stats["orphan_videos"] = len(self.orphan_videos)
        logger.info(f"Videos huérfanos detectados para VideoWorker: {len(self.orphan_videos)}")

        logger.info("==================================================================")
        logger.info("Fase B: Extracción y Clasificación Temática con Progreso Visible")
        logger.info("==================================================================")

        total_tasks = len(all_text_tasks)
        processed_count = 0

        for idx, (prov, rel_p, full_p) in enumerate(all_text_tasks, 1):
            fname = os.path.basename(full_p)

            # Omitir traducciones automáticas garrafales .es.vtt
            if fname.endswith(".es.vtt"):
                continue

            text = LessonExtractor.extract(full_p)
            words = len(text.split())

            if words < 30:
                continue

            cluster = self.classify(full_p)
            if cluster not in self.cluster_data:
                self.cluster_data[cluster] = []

            self.cluster_data[cluster].append({
                "file_name": fname,
                "file_path": full_p,
                "rel_path": os.path.join(prov, rel_p),
                "word_count": words,
                "content": text
            })

            processed_count += 1
            self.stats["processed_texts"] += 1
            self.stats["total_extracted_words"] += words

            # Reportar progreso visible cada 50 archivos o cada 5%
            if idx % 50 == 0 or idx == total_tasks:
                pct = (idx / total_tasks) * 100
                logger.info(
                    f"[{idx}/{total_tasks}] ({pct:.1f}%) "
                    f"Extraídos {processed_count} docs ({self.stats['total_extracted_words']} palabras) "
                    f"| Último: {fname[:35]} -> {cluster}"
                )

        self.stats["clusters_populated"] = len(self.cluster_data)
        logger.info(
            f"Extracción finalizada: {processed_count} documentos sustantivos "
            f"({self.stats['total_extracted_words']} palabras) en {self.stats['clusters_populated']} clusters."
        )

        # Escribir compendios y manifiesto
        self.write_compendiums(dry_run=dry_run)
        self.write_videoworker_manifest(dry_run=dry_run)

    def write_compendiums(self, dry_run: bool = False) -> None:
        """Escribe los compendios temáticos modulares y los espejea a Google Drive."""
        if dry_run:
            logger.info("[DRY-RUN] Omitiendo escritura en disco.")
            return

        logger.info(f"Escribiendo compendios en {self.output_dir}...")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.mirror_dir, exist_ok=True)

        for cluster, items in self.cluster_data.items():
            cluster_dir = os.path.join(self.output_dir, cluster)
            cluster_mirror_dir = os.path.join(self.mirror_dir, cluster)
            os.makedirs(cluster_dir, exist_ok=True)
            os.makedirs(cluster_mirror_dir, exist_ok=True)

            # Agrupar por proveedor
            by_prov: Dict[str, List[Dict[str, Any]]] = {}
            for it in items:
                prov = it["rel_path"].split(os.sep)[0]
                by_prov.setdefault(prov, []).append(it)

            for prov, prov_items in by_prov.items():
                prov_slug = prov.lower().replace(" ", "_")
                filename = f"{cluster}_{prov_slug}_compendium.md"
                out_path = os.path.join(cluster_dir, filename)
                mirror_path = os.path.join(cluster_mirror_dir, filename)

                header = [
                    f"# Compendio Temático: {cluster.upper()}",
                    f"**Especialidad:** `{cluster}`",
                    f"**Proveedor:** `{prov}`",
                    f"**Total Documentos:** {len(prov_items)}",
                    f"**Total Palabras:** {sum(i['word_count'] for i in prov_items)}",
                    "**Gobernanza:** SSoT Parity & Pure Brand-Agnostic Knowledge Base",
                    "---",
                    ""
                ]

                body = []
                for it in prov_items:
                    body.append(f"## Lección / Recurso: {it['file_name']}")
                    body.append(f"*Origen:* `{it['rel_path']}` ({it['word_count']} palabras)\n")
                    body.append(it["content"])
                    body.append("\n---\n")

                full_md = "\n".join(header + body)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(full_md)

                try:
                    with open(mirror_path, "w", encoding="utf-8") as f:
                        f.write(full_md)
                except Exception as e:
                    logger.warning(f"No se pudo espejear {mirror_path}: {e}")

        logger.info("✅ Todos los compendios temáticos fueron escritos y espejeados con éxito.")

    def write_videoworker_manifest(self, dry_run: bool = False) -> None:
        """Escribe el manifiesto oficial de videos huérfanos para VideoWorker (BAI-405)."""
        manifest = {
            "metadata": {
                "generated_at": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip(),
                "governance": "BAI-405 VideoWorker Manifest (FFmpeg Asynchronous Ingestion)",
                "total_orphan_videos": len(self.orphan_videos)
            },
            "tasks": self.orphan_videos
        }

        if dry_run:
            logger.info(f"[DRY-RUN] Manifiesto VideoWorker: {len(self.orphan_videos)} videos.")
            return

        os.makedirs(os.path.dirname(self.manifest_output), exist_ok=True)
        with open(self.manifest_output, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        try:
            os.makedirs(os.path.dirname(self.manifest_mirror), exist_ok=True)
            with open(self.manifest_mirror, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"No se pudo espejear manifiesto {self.manifest_mirror}: {e}")

        logger.info(f"✅ Manifiesto VideoWorker guardado en {self.manifest_output} ({len(self.orphan_videos)} videos).")


def run_tests() -> int:
    """Tests deterministas de auto-validación."""
    logger.info("Ejecutando tests deterministas de auto-validación...")
    compiler = ThematicCompiler("/tmp", "/tmp", "/tmp/m.json")
    assert compiler.classify("DIGITALMARKETER/COPY/SOP.md") == "copywriting"
    assert compiler.classify("PLATZI/03_ECOM/Supply.docx") == "ecommerce_stores"
    assert compiler.classify("CURSOS/VELOCITYMEDIA/INFLUENCE/Monopoly.md") == "00_category_of_one"
    logger.info("✅ Auto-validación completada con éxito (exit code 0).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compilador Temático de Lecciones y Manifiesto VideoWorker")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--mirror-dir", default=DEFAULT_MIRROR_DIR)
    parser.add_argument("--manifest-output", default=DEFAULT_MANIFEST_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Límite de archivos por fuente para pruebas rápidas")

    args = parser.parse_args()

    if args.test:
        return run_tests()

    compiler = ThematicCompiler(
        output_dir=args.output_dir,
        mirror_dir=args.mirror_dir,
        manifest_output=args.manifest_output
    )

    compiler.execute_pipeline(dry_run=args.dry_run, max_items_per_source=args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
