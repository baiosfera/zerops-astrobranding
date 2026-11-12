#!/usr/bin/env python3
"""
==============================================================================
build_sovereign_compendiums.py (v3.0 SOTA)
Master Sovereign Micro-Compendiums Engine (27 Micro-Clusters, 6 Collections)
Governance: Supreme Directive v8.5, Fractal CoHaLo & Master Plan v4.1
Zero-Token ($0) Local Processing across PLATZI, DIGITALMARKETER and CURSOS
SSoT Parity: NVMe (/var/www/localstorage) <-> Google Drive (/var/www/baiosfera)
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
import hashlib
import unicodedata
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set, Tuple

# Configurar logging estructurado sin buffering
sys.stdout.reconfigure(line_buffering=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("sovereign_compendiums")

RCLONE_BIN = "/var/www/.rclone/bin/rclone"
RCLONE_CONF = "/var/www/.rclone/config/rclone/rclone.conf"

DEFAULT_OUTPUT_DIR = "/var/www/localstorage/knowledge_cache/compendiums"
DEFAULT_MIRROR_DIR = "/var/www/baiosfera/PLAYBOOKS/0compendiums"
DEFAULT_MANIFEST_OUTPUT = "/var/www/localstorage/knowledge_cache/videoworker_manifest.json"
DEFAULT_MANIFEST_MIRROR = "/var/www/baiosfera/PLAYBOOKS/videoworker_manifest.json"

TEXT_INCLUDES = ["*.md", "*.txt", "*.docx", "*.pdf", "*.srt", "*.vtt"]
VIDEO_INCLUDES = ["*.mp4"]

# =============================================================================
# 1. TAXONOMÍA CANÓNICA DE 27 MICRO-CLUSTERS EN 6 COLECCIONES
# =============================================================================
COLLECTIONS = {
    "00_estrategia": ["00_category_of_one", "01_velocity_sales_doctrine"],
    "01_trafico_paid": ["paid_ads_strategy", "paid_ads_meta", "paid_ads_google", "paid_ads_tiktok"],
    "02_organico_social": ["social_media_strategy", "social_instagram", "social_tiktok", "social_youtube", "social_linkedin"],
    "03_conversion": ["funnels_cro", "copywriting_direct_response", "offers_pricing", "whatsapp_conversational", "email_marketing"],
    "04_ventas": ["consultative_sales", "customer_success_retention"],
    "05_operaciones": [
        "ecommerce_stores", "data_analytics", "automations_workflows",
        "ai_prompting_agents", "seo_aeo", "avatar_research",
        "branding_authority", "growth_loops", "product_startup"
    ]
}

ALL_MICRO_CLUSTERS = [c for clist in COLLECTIONS.values() for c in clist]

# Palabras clave y frases ponderadas por Micro-Cluster
CLUSTER_KEYWORDS: Dict[str, List[str]] = {
    "00_category_of_one": [
        "category of one", "categoria de uno", "categoría de uno", "category design",
        "monopolio personal", "two-rill", "two rill", "epoch moat", "uniqueness",
        "territorio inalienable", "posicionamiento ontologico", "posicionamiento ontológico",
        "incomparable", "incomparabilidad", "monopolio de uno"
    ],
    "01_velocity_sales_doctrine": [
        "venta sutil", "tension constructiva", "tensión constructiva", "52 perlas",
        "velocity sales", "alta velocidad", "venta por diagnostico", "venta por diagnóstico",
        "cerrar sin confrontar", "marcos de tension", "marcos de tensión", "apalancamiento de ventas"
    ],
    "paid_ads_meta": [
        "meta ads", "facebook ads", "fb ads", "instagram ads", "ig ads", "anuncios en facebook",
        "anuncios en instagram", "pixel de meta", "pixel de facebook", "capi", "conversions api",
        "business manager", "ads manager", "cbo", "abo", "creatividades meta", "retargeting meta"
    ],
    "paid_ads_google": [
        "google ads", "adwords", "youtube ads", "anuncios en youtube", "pmax", "performance max",
        "search ads", "anuncios de busqueda", "anuncios de búsqueda", "red de display", "google search ads",
        "intencion de busqueda", "intención de búsqueda", "keyword planner", "quality score"
    ],
    "paid_ads_tiktok": [
        "tiktok ads", "anuncios en tiktok", "spark ads", "tiktok for business", "tiktok pixel",
        "tiktok creative center", "subasta tiktok", "formato vertical pago", "tiktok video ads"
    ],
    "paid_ads_strategy": [
        "paid ads", "media buying", "compra de medios", "trafico pago", "tráfico pago",
        "trafico pagado", "tráfico pagado", "campañas de anuncios", "campanas de anuncios",
        "roas", "cpa", "cpm", "ctr", "mer", "scaling ads", "escalado de campanas", "escalado de campañas",
        "creative testing", "testing de anuncios", "atribucion publicitaria", "atribución publicitaria"
    ],
    "social_instagram": [
        "instagram", "reels", "reel", "feed ig", "historias de instagram", "stories ig",
        "carrusel instagram", "carruseles instagram", "perfil magnetico", "perfil magnético",
        "bio de instagram", "algoritmo de instagram", "crecimiento en instagram", "shadowban"
    ],
    "social_tiktok": [
        "tiktok", "tik tok", "videos cortos", "video corto", "formato corto", "viral en tiktok",
        "algoritmo de tiktok", "tendencias tiktok", "for you page", "fyp", "retencion primeros 3 segundos"
    ],
    "social_youtube": [
        "youtube", "canal de youtube", "largo formato", "guion youtube", "guión youtube",
        "miniaturas", "ctr miniatura", "retencion de video", "retención de video", "monetizacion youtube",
        "seo en youtube", "suscriptores", "comunidad youtube"
    ],
    "social_linkedin": [
        "linkedin", "perfil de linkedin", "social selling", "b2b social", "carruseles linkedin",
        "articulos linkedin", "autoridad linkedin", "red profesional", "prospeccion linkedin", "inmail"
    ],
    "social_media_strategy": [
        "social media", "redes sociales", "community manager", "estrategia de contenidos",
        "plan de contenidos", "calendario editorial", "pilares de contenido", "marketing de contenidos",
        "distribucion omnicanal", "distribución omnicanal", "hook retain reward", "engagement", "alcance organico"
    ],
    "copywriting_direct_response": [
        "copywriting", "copy", "redaccion publicitaria", "redacción publicitaria", "redaccion persuasiva",
        "redacción persuasiva", "carta de ventas", "cartas de venta", "sales letter", "vsl script",
        "titulares", "headlines", "ganchos", "hooks", "fórmulas de persuasión", "formulas de persuasion",
        "pas formula", "aida", "storytelling", "respuesta directa", "direct response"
    ],
    "funnels_cro": [
        "funnel", "funnels", "embudo", "embudos", "cro", "conversion rate", "landing page",
        "paginas de aterrizaje", "páginas de aterrizaje", "squeeze page", "tripwire", "webinar funnel",
        "vsl funnel", "tasa de conversion", "tasa de conversión", "opt-in", "lead magnet", "heatmaps"
    ],
    "offers_pricing": [
        "grand slam offer", "oferta irresistible", "ofertas irresistibles", "hormozi", "alex hormozi",
        "value equation", "ecuacion de valor", "ecuación de valor", "pricing", "fijacion de precios",
        "fijación de precios", "high ticket", "high-ticket", "bonus stack", "stack de bonos",
        "garantia", "garantía", "garantias", "garantías", "precio basado en valor", "estructuracion de ofertas"
    ],
    "whatsapp_conversational": [
        "whatsapp", "whatsapp marketing", "chat marketing", "cierre por chat", "conversational selling",
        "ventas por chat", "manychat", "chatbots", "secuencias whatsapp", "scripts de whatsapp",
        "mensajeria instantanea", "cualificacion por chat"
    ],
    "email_marketing": [
        "email marketing", "correo electronico", "correo electrónico", "newsletter", "newsletters",
        "secuencias de email", "email flows", "lead nurturing", "klaviyo", "activecampaign",
        "mailchimp", "autoresponder", "entregabilidad", "open rate", "click rate", "spam score"
    ],
    "consultative_sales": [
        "ventas consultivas", "venta consultiva", "cierre de ventas", "tecnicas de negociacion",
        "técnicas de negociación", "manejo de objeciones", "llamada de ventas", "sales call",
        "spin selling", "descubrimiento de dolor", "presupuesto b2b", "cierre telefonico", "cierre telefónico"
    ],
    "customer_success_retention": [
        "customer success", "onboarding de clientes", "retencion", "retención", "churn",
        "reduccion de churn", "reducción de churn", "fidelizacion", "fidelización", "ltv",
        "lifetime value", "expansion revenue", "nps", "satisfaccion del cliente"
    ],
    "ecommerce_stores": [
        "ecommerce", "e-commerce", "comercio electronico", "comercio electrónico", "shopify",
        "woocommerce", "tienda online", "tiendas online", "dropshipping", "checkout", "carrito abandonado",
        "aov", "ticket promedio", "logistica ecom", "logística ecom"
    ],
    "data_analytics": [
        "analytics", "ga4", "google analytics", "metricas", "métricas", "kpi", "kpis",
        "dashboards", "business intelligence", "atribucion", "atribución", "cac", "roas",
        "ltv/cac", "looker studio", "modelos de datos"
    ],
    "automations_workflows": [
        "automatizacion", "automatización", "n8n", "make.com", "make", "zapier",
        "webhooks", "webhook", "flujos automaticos", "flujos automáticos", "integraciones api",
        "event driven", "crm sync", "rpa"
    ],
    "ai_prompting_agents": [
        "prompt engineering", "prompting", "chatgpt", "gemini", "claude", "llm", "llms",
        "agentes autonomos", "agentes autónomos", "crewai", "rag", "flujos agenticos",
        "flujos agénticos", "context engineering", "fine-tuning", "vector database"
    ],
    "seo_aeo": [
        "seo", "posicionamiento web", "motores de busqueda", "motores de búsqueda", "keywords",
        "palabras clave", "backlinks", "linkbuilding", "schema markup", "aeo", "answer engine",
        "perplexity", "searchgpt", "sitemap", "rastreo e indexacion"
    ],
    "avatar_research": [
        "avatar", "buyer persona", "cliente ideal", "icp", "ideal customer profile",
        "jobs to be done", "jtbd", "thick data", "investigacion de usuarios", "investigación de usuarios",
        "entrevistas a clientes", "mapa de empatia", "mapa de empatía", "dolores y deseos"
    ],
    "branding_authority": [
        "branding", "identidad visual", "manual de marca", "brandbook", "tono de voz",
        "arquitectura de marca", "naming", "diseno de marca", "diseño de marca",
        "posicionamiento de marca", "reputacion de marca", "reputación de marca", "brand guidelines"
    ],
    "growth_loops": [
        "growth loops", "bucles de crecimiento", "viralidad", "programas de referidos",
        "product led growth", "plg", "mecanicas de retencion", "mecánicas de retención",
        "growth hacking", "k-factor", "coeficiente viral"
    ],
    "product_startup": [
        "product management", "gestion de producto", "gestión de producto", "mvp",
        "producto minimo viable", "producto mínimo viable", "product market fit", "lean startup",
        "validacion de hipotesis", "validación de hipótesis", "descubrimiento de producto"
    ]
}

# =============================================================================
# 2. DENYLIST ESTRICTO (VETO PERMANENTE)
# =============================================================================
STRICT_DENYLIST_TERMS = [
    # Cursos y autores no comerciales
    "luis-inestrosa", "inestrosa", "conferencias que venden", "habla y vendete bien",
    "formación-en-consultoría-astrológica", "consultoría astrológica", "astrologica", "astrología", "astrologia",
    "mesmerismo", "hipnosis", "letras hebreas", "codica", "reprogramate rapido", "reprográmate rápido",
    "metodo yuen", "método yuen", "yuen", "alta magia", "psicobionica", "psicobiónica", "psicobiotico", "psicobiótico",
    "bioenergetica", "bioenergética", "constelaciones", "meditaciones", "sanar trauma", "codigos-sagrados", "códigos sagrados",
    "tantra", "dormir-mejor", "dormir mejor", "arte de la felicidad", "dopamine", "transgeneracional", "harry-potra",
    "seduccion", "seducción", "el dinero, mis finanzas y mis creencias", "heroes-sin-capa", "héroes sin capa",
    "irresistiblemente", "piense y hágase rico – el legado", "reiki", "cuantica", "cuántica",
    "libertad economica", "borrar problemas", "fortaleza en los numeros", "esquema borrar",
    # Archivos administrativos, notas y scrapers
    "enlaces_descarga", "enlaces descarga", "progreso.txt", "informacion importante",
    "manual_tutor", "manual_mcv", "engram.md", "handoff.md", "agy.txt", "nblm.md",
    "download_plan", ".download_plan"
]


def is_denylisted(path_or_text: str) -> bool:
    """Verifica si la ruta o contenido contiene términos del denylist permanente."""
    norm = unicodedata.normalize("NFKD", path_or_text).encode("ascii", "ignore").decode("ascii").lower()
    norm = re.sub(r"[-_\s]+", " ", norm)
    for term in STRICT_DENYLIST_TERMS:
        norm_term = unicodedata.normalize("NFKD", term).encode("ascii", "ignore").decode("ascii").lower()
        norm_term = re.sub(r"[-_\s]+", " ", norm_term)
        if norm_term in norm:
            return True
    return False


# =============================================================================
# 3. NORMALIZADOR Y LIMPIADOR SINTÁCTICO DE SUBTÍTULOS (SubtitlesCleaner)
# =============================================================================
class SubtitlesCleaner:
    """Elimina códigos de tiempo, numeración secuencial, tags HTML y ruidos ambientales."""

    TIMECODE_LINE = re.compile(
        r"^(?:\d{1,5}\r?\n)?(?:\d{2}:)?\d{2}:\d{2}[,\.]\d{3}\s*-->\s*(?:\d{2}:)?\d{2}:\d{2}[,\.]\d{3}.*$",
        re.MULTILINE
    )
    HEADER_VTT = re.compile(r"^\ufeff?WEBVTT.*?\n(?:\w+:.*?\n)*\n?", re.DOTALL | re.IGNORECASE)
    TAG_HTML = re.compile(r"<[^>]+>")
    NOISE_BRACKETS = re.compile(r"\[(Música|Music|Aplausos|Risas|Silencio|Audio|Inaudible|Suspiros|Música de fondo)\]", re.IGNORECASE)
    NOISE_PARENS = re.compile(r"\((Música|Music|Aplausos|Risas|Silencio|Audio|Inaudible|Suspiros)\)", re.IGNORECASE)

    @classmethod
    def clean(cls, raw: str) -> str:
        if not raw:
            return ""

        content = raw.replace("\r\n", "\n").replace("\r", "\n")
        content = cls.HEADER_VTT.sub("", content)
        content = cls.TIMECODE_LINE.sub("", content)
        content = cls.TAG_HTML.sub("", content)
        content = cls.NOISE_BRACKETS.sub("", content)
        content = cls.NOISE_PARENS.sub("", content)

        lines: List[str] = []
        for line in content.splitlines():
            s = line.strip()
            if not s or s.isdigit():
                continue
            if s.upper().startswith(("NOTE", "REGION", "STYLE", "WEBVTT", "KIND:", "LANGUAGE:")):
                continue
            if lines:
                prev = lines[-1]
                if s == prev:
                    continue
                if s.startswith(prev):
                    lines[-1] = s
                    continue
                if prev.startswith(s):
                    continue
            lines.append(s)

        # Reconstruir en prosa continua estructurada (párrafos de ~4-5 oraciones)
        paragraphs: List[str] = []
        current_p: List[str] = []
        sentence_count = 0

        for l in lines:
            current_p.append(l)
            if l.endswith((".", "!", "?")):
                sentence_count += 1
                if sentence_count >= 4:
                    paragraphs.append(" ".join(current_p))
                    current_p = []
                    sentence_count = 0

        if current_p:
            paragraphs.append(" ".join(current_p))

        clean_text = "\n\n".join(paragraphs).strip()
        # Eliminar espacios múltiples redundantes
        clean_text = re.sub(r"[ \t]+", " ", clean_text)
        return clean_text


# =============================================================================
# 4. EXTRACTORES MULTIFORMATO ($0 TOKENS)
# =============================================================================
class LocalDocumentExtractor:
    """Extrae texto limpio de DOCX, PDF, SRT, VTT, MD y TXT."""

    @staticmethod
    def extract_docx(file_path: str) -> str:
        try:
            with zipfile.ZipFile(file_path) as z:
                if "word/document.xml" not in z.namelist():
                    return ""
                xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []
            for p in tree.iterfind(".//w:p", namespaces):
                texts = [t.text for t in p.iterfind(".//w:t", namespaces) if t.text]
                if texts:
                    paragraphs.append("".join(texts))
            return "\n\n".join(paragraphs).strip()
        except Exception:
            return ""

    @staticmethod
    def extract_pdf(file_path: str) -> str:
        try:
            res = subprocess.run(
                ["/usr/bin/pdftotext", "-layout", "-enc", "UTF-8", file_path, "-"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
                check=False
            )
            raw = res.stdout
            pages = raw.split("\x0c")
            valid_pages = [p.strip() for p in pages if p.strip()]
            if len(valid_pages) >= 3:
                words = len(raw.split())
                if (words / len(valid_pages)) < 25:
                    return ""  # Descartar diapositivas vacías o formularios
            clean = raw.replace("\x0c", "\n\n")
            return re.sub(r"\n{3,}", "\n\n", clean).strip()
        except Exception:
            return ""

    @staticmethod
    def extract_subtitles(file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()
            return SubtitlesCleaner.clean(raw)
        except Exception:
            return ""

    @staticmethod
    def extract_plain(file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read().strip()
            if "-->" in raw and re.search(r"\d{1,2}:\d{2}.*?-->", raw):
                return SubtitlesCleaner.clean(raw)
            return raw
        except Exception:
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
            return cls.extract_plain(file_path)
        return ""


# =============================================================================
# 5. MOTOR DE CLASIFICACIÓN Y MICRO-PARTICIONADO DE CURSOS
# =============================================================================
class SovereignCompactor:
    """Compila compendios atómicos por curso y micro-cluster (<350k palabras)."""

    MAX_WORDS_PER_COMPENDIUM = 350000

    @staticmethod
    def sanitize_slug(text: str) -> str:
        norm = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        clean = re.sub(r"[^\w\s-]", "", norm).strip()
        return re.sub(r"[-\s]+", "-", clean)

    @classmethod
    def extract_course_metadata(cls, rel_path: str) -> Dict[str, str]:
        """Extrae tupla limpia (proveedor, curso, directorio_curso) a partir de la ruta relativa."""
        parts = rel_path.split(os.sep)
        prov = parts[0].upper()
        if prov == "CURSOS":
            sub_prov = parts[1] if len(parts) > 1 else "CURSOS"
            if len(parts) >= 4 and parts[2].lower() in (
                "vip", "basic", "profesional", "categorias", "author", "archivos",
                "1. cua", "2. cua", "3. cua", "cursos sprint", "cortos"
            ):
                course_name = parts[3]
                course_dir = os.path.join("CURSOS", parts[1], parts[2], parts[3])
            elif len(parts) >= 3:
                course_name = parts[2]
                course_dir = os.path.join("CURSOS", parts[1], parts[2])
            else:
                course_name = sub_prov
                course_dir = os.path.join("CURSOS", parts[1])
        elif prov in ("PLATZI", "DIGITALMARKETER"):
            if len(parts) >= 3:
                course_name = parts[1]
                course_dir = os.path.join(prov, parts[1])
            else:
                course_name = "General"
                course_dir = prov
        else:
            course_name = parts[1] if len(parts) > 1 else prov
            course_dir = os.path.join(prov, course_name)

        clean_name = re.sub(r"^[0-9]+[_\s-]+", "", course_name).strip()
        clean_name = re.sub(r"\.(docx|pdf|txt|md|srt|vtt)$", "", clean_name, flags=re.I).strip()
        if prov == "DIGITALMARKETER":
            clean_name = re.sub(r"_[a-z0-9\-]+$", "", clean_name).replace("_", " ").strip()

        return {
            "provider": prov,
            "course_name": clean_name or course_name,
            "course_dir": course_dir
        }

    @classmethod
    def classify_resource(cls, file_path: str, content_sample: str = "") -> Optional[str]:
        """
        Clasifica una lección individual en uno de los 27 micro-clusters.
        Aplica coincidencia jerárquica: nombre de lección > ruta de curso > muestra de contenido.
        Retorna None si no pertenece a ningún cluster comercial (evita efecto basurero).
        """
        if "VELOCITYMEDIA/INFLUENCE" in file_path or "VELOCITY/INFLUENCE" in file_path:
            return "00_category_of_one"

        norm_path = unicodedata.normalize("NFKD", file_path).encode("ascii", "ignore").decode("ascii").lower()
        fname = os.path.basename(norm_path)

        # Buscar coincidencia exacta en palabras clave
        scores: Dict[str, int] = defaultdict(int)

        for cluster, kws in CLUSTER_KEYWORDS.items():
            for kw in kws:
                kw_norm = unicodedata.normalize("NFKD", kw).encode("ascii", "ignore").decode("ascii").lower()
                # Coincidencia en nombre de archivo (peso 5)
                if kw_norm in fname:
                    scores[cluster] += 5
                # Coincidencia en ruta de carpeta (peso 3)
                elif kw_norm in norm_path:
                    scores[cluster] += 3

        if scores:
            best_cluster = max(scores.items(), key=lambda x: x[1])[0]
            return best_cluster

        # Si no hubo coincidencia en ruta, analizar muestra de contenido
        if content_sample:
            norm_sample = unicodedata.normalize("NFKD", content_sample[:3000]).encode("ascii", "ignore").decode("ascii").lower()
            for cluster, kws in CLUSTER_KEYWORDS.items():
                for kw in kws:
                    kw_norm = unicodedata.normalize("NFKD", kw).encode("ascii", "ignore").decode("ascii").lower()
                    if kw_norm in norm_sample:
                        scores[cluster] += 1
            if scores:
                best_cluster = max(scores.items(), key=lambda x: x[1])[0]
                return best_cluster

        return None  # No forzar a branding_authority si no matchea


# =============================================================================
# 6. ORQUESTADOR PRINCIPAL DEL PIPELINE
# =============================================================================
class SovereignCompendiumCompiler:
    """Ejecuta el inventario rclone, la extracción, la compactación y la auditoría."""

    def __init__(
        self,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        mirror_dir: str = DEFAULT_MIRROR_DIR,
        manifest_output: str = DEFAULT_MANIFEST_OUTPUT
    ):
        self.output_dir = os.path.abspath(output_dir)
        self.mirror_dir = os.path.abspath(mirror_dir)
        self.manifest_output = os.path.abspath(manifest_output)
        self.manifest_mirror = os.path.abspath(DEFAULT_MANIFEST_MIRROR)

        # Estructura: groups[(provider, micro_cluster, course_dir, course_name)] = [items]
        self.course_groups: Dict[Tuple[str, str, str, str], List[Dict[str, Any]]] = defaultdict(list)
        self.orphan_videos: List[Dict[str, Any]] = []

        self.stats = {
            "total_inventoried": 0,
            "denylisted_purged": 0,
            "processed_documents": 0,
            "total_extracted_words": 0,
            "compendiums_created": 0,
            "orphan_videos": 0
        }

    @staticmethod
    def rclone_list(remote_path: str, includes: List[str]) -> List[str]:
        if not os.path.exists(RCLONE_BIN) or not os.path.exists(RCLONE_CONF):
            return []
        cmd = [RCLONE_BIN, "--config", RCLONE_CONF, "lsf", remote_path, "--recursive", "--files-only"]
        for inc in includes:
            cmd.extend(["--include", inc])
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return [l.strip() for l in res.stdout.splitlines() if l.strip()]
        except Exception as e:
            logger.error(f"Error listando {remote_path}: {e}")
            return []

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        logger.info("==================================================================")
        logger.info("🚀 INICIANDO COMPILACIÓN SOBERANA DE MICRO-COMPENDIOS (27 CLUSTERS)")
        logger.info("==================================================================")
        t_start = time.time()

        # 1. Inventario Desacoplado vía rclone API
        sources = [
            ("DIGITALMARKETER", "baiosfera:DIGITALMARKETER", TEXT_INCLUDES),
            ("PLATZI", "baiosfera:PLATZI", ["*.docx", "*.txt"]),
            ("CURSOS", "baiosfera:CURSOS", TEXT_INCLUDES)
        ]

        all_tasks: List[Tuple[str, str, str]] = []  # (prov, rel_p, full_p)
        dirs_with_text: Set[str] = set()

        for prov, remote, incs in sources:
            logger.info(f"• Inventariando {prov}...")
            files = self.rclone_list(remote, incs)
            logger.info(f"  -> {len(files)} archivos encontrados en {prov}.")
            for rel_p in files:
                full_p = os.path.join("/var/www/baiosfera", prov, rel_p)
                all_tasks.append((prov, rel_p, full_p))
                dirs_with_text.add(os.path.dirname(full_p))

        self.stats["total_inventoried"] = len(all_tasks)
        logger.info(f"Inventario completado: {len(all_tasks)} documentos totales.")

        # 2. Inventario de Videos Huérfanos Filtrados (BAI-405)
        logger.info("• Inventariando videos en CURSOS...")
        video_files = self.rclone_list("baiosfera:CURSOS", VIDEO_INCLUDES)
        for v_rel in video_files:
            v_full = os.path.join("/var/www/baiosfera/CURSOS", v_rel)
            if is_denylisted(v_full):
                continue
            v_dir = os.path.dirname(v_full)
            if v_dir not in dirs_with_text:
                cluster = SovereignCompactor.classify_resource(v_full) or "general_business"
                self.orphan_videos.append({
                    "file_name": os.path.basename(v_full),
                    "file_path": v_full,
                    "rel_path": os.path.join("CURSOS", v_rel),
                    "target_cluster": cluster
                })
        self.stats["orphan_videos"] = len(self.orphan_videos)
        logger.info(f"  -> {len(self.orphan_videos)} videos comerciales huérfanos detectados (BAI-405).")

        # 3. Extracción y Clasificación Temática
        logger.info("==================================================================")
        logger.info("⚙️ FASE 2: Extracción Limpia y Clasificación por Micro-Cluster")
        logger.info("==================================================================")

        total_files = len(all_tasks)
        seen_content_hashes: Set[str] = set()

        for idx, (prov, rel_p, full_p) in enumerate(all_tasks, 1):
            # Filtro 1: Denylist permanente
            if is_denylisted(full_p):
                self.stats["denylisted_purged"] += 1
                continue

            fname = os.path.basename(full_p)
            if fname.endswith(".es.vtt"):
                continue

            # Extracción multiformato
            content = LocalDocumentExtractor.extract(full_p)
            words = len(content.split())
            if words < 25:
                continue

            # Filtro 2: Denylist de contenido interno
            if is_denylisted(content[:1000]):
                self.stats["denylisted_purged"] += 1
                continue

            # Deduplicación por hash SHA-256
            norm_sample = re.sub(r"\s+", " ", content[:3000]).strip().lower()
            content_hash = hashlib.sha256(norm_sample.encode("utf-8")).hexdigest()
            if content_hash in seen_content_hashes:
                continue
            seen_content_hashes.add(content_hash)

            # Clasificación a nivel de lección
            meta = SovereignCompactor.extract_course_metadata(os.path.join(prov, rel_p))
            cluster = SovereignCompactor.classify_resource(full_p, content_sample=content)
            if not cluster:
                # Si el curso tiene un tema claro en el directorio, usarlo; sino descartar
                cluster = SovereignCompactor.classify_resource(meta["course_dir"])
                if not cluster:
                    continue  # Descartar archivos que no pertenezcan al negocio

            group_key = (prov, cluster, meta["course_dir"], meta["course_name"])
            self.course_groups[group_key].append({
                "file_name": fname,
                "file_path": full_p,
                "rel_path": os.path.join(prov, rel_p),
                "word_count": words,
                "content": content
            })

            self.stats["processed_documents"] += 1
            self.stats["total_extracted_words"] += words

            if idx % 50 == 0 or idx == total_files:
                pct = (idx / total_files) * 100
                logger.info(
                    f"[{idx}/{total_files}] ({pct:.1f}%) "
                    f"Docs procesados: {self.stats['processed_documents']} "
                    f"({self.stats['total_extracted_words']:,} palabras) "
                    f"| Grupos activos: {len(self.course_groups)}"
                )

        logger.info(
            f"Extracción finalizada: {self.stats['processed_documents']} documentos limpios "
            f"({self.stats['total_extracted_words']:,} palabras). "
            f"Descartados por Denylist: {self.stats['denylisted_purged']}."
        )

        # 4. Escritura de Compendios Modulares
        if not dry_run:
            self.write_all_compendiums()
            self.write_manifest()
        else:
            logger.info("[DRY-RUN] Simulación completa. No se escribieron compendios.")

        elapsed = time.time() - t_start
        logger.info(f"Pipeline ejecutado con éxito en {elapsed:.2f}s.")
        return self.stats

    def write_all_compendiums(self) -> None:
        """Escribe compendios modulares por curso asegurando que ninguno exceda 350.000 palabras."""
        logger.info("==================================================================")
        logger.info("💾 FASE 3: Generación de Compendios Modulares (<350k palabras)")
        logger.info("==================================================================")

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.mirror_dir, exist_ok=True)

        compendium_paths: List[str] = []

        for (prov, cluster, course_dir, course_name), items in self.course_groups.items():
            cluster_dir = os.path.join(self.output_dir, cluster)
            cluster_mirror = os.path.join(self.mirror_dir, cluster)
            os.makedirs(cluster_dir, exist_ok=True)
            os.makedirs(cluster_mirror, exist_ok=True)

            safe_course = SovereignCompactor.sanitize_slug(course_name)
            total_course_words = sum(i["word_count"] for i in items)

            # Particionado en bloques de <350.000 palabras si el curso es gigantesco
            chunks: List[List[Dict[str, Any]]] = []
            current_chunk: List[Dict[str, Any]] = []
            current_words = 0

            for it in items:
                if current_words + it["word_count"] > SovereignCompactor.MAX_WORDS_PER_COMPENDIUM and current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = [it]
                    current_words = it["word_count"]
                else:
                    current_chunk.append(it)
                    current_words += it["word_count"]

            if current_chunk:
                chunks.append(current_chunk)

            for chunk_idx, chunk_items in enumerate(chunks, 1):
                part_suffix = f"__part{chunk_idx}" if len(chunks) > 1 else ""
                filename = f"[{prov}]__[{cluster.upper()}]__{safe_course}{part_suffix}.md"
                out_path = os.path.join(cluster_dir, filename)
                mirror_path = os.path.join(cluster_mirror, filename)

                toc = []
                sections = []
                for sec_idx, it in enumerate(chunk_items, 1):
                    clean_title = re.sub(r"^[0-9]+[_\s-]+", "", os.path.splitext(it["file_name"])[0])
                    clean_title = clean_title.replace("20", " ").replace("_", " ").replace("-", " ").strip().title()
                    toc.append(f"{sec_idx}. **{clean_title}** ({it['word_count']:,} palabras)")
                    sec_md = (
                        f"### {sec_idx}. {clean_title}\n"
                        f"*Archivo fuente*: `{it['rel_path']}`\n\n"
                        f"{it['content']}\n"
                    )
                    sections.append(sec_md)

                header = (
                    f"# [{prov}] [{cluster.upper()}] — {course_name}{part_suffix}\n\n"
                    f"## 📑 Índice de Lecciones y Documentos\n\n"
                    + "\n".join(toc)
                    + "\n\n---\n\n"
                    f"## 📚 Contenido Estructurado de las Lecciones\n\n"
                )

                full_content = header + "\n---\n\n".join(sections)

                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(full_content)

                try:
                    with open(mirror_path, "w", encoding="utf-8") as f:
                        f.write(full_content)
                except Exception as e:
                    logger.warning(f"No se pudo espejear a Drive {mirror_path}: {e}")

                compendium_paths.append(out_path)
                self.stats["compendiums_created"] += 1

        logger.info(f"Compendios creados exitosamente: {self.stats['compendiums_created']} archivos.")

    def write_manifest(self) -> None:
        """Escribe el manifiesto de videos huérfanos para VideoWorker (BAI-405)."""
        manifest_data = {
            "metadata": {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "total_tasks": len(self.orphan_videos),
                "governance": "Supreme Directive v8.5 | BAI-405 Ephemeral VideoWorker Pipeline",
                "clean_business_only": True
            },
            "tasks": self.orphan_videos
        }
        os.makedirs(os.path.dirname(self.manifest_output), exist_ok=True)
        with open(self.manifest_output, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)

        try:
            os.makedirs(os.path.dirname(self.manifest_mirror), exist_ok=True)
            with open(self.manifest_mirror, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"No se pudo espejear manifiesto a Drive: {e}")

        logger.info(f"Manifiesto VideoWorker escrito: {self.manifest_output} ({len(self.orphan_videos)} tareas).")


# =============================================================================
# 7. SUITE DE AUDITORÍA Y CERTIFICACIÓN FÍSICA
# =============================================================================
def audit_compendiums(base_dir: str = DEFAULT_OUTPUT_DIR) -> Dict[str, Any]:
    """Audita físicamente todos los compendios generados contra los contratos estrictos."""
    logger.info("==================================================================")
    logger.info("🔍 AUDITORÍA FORENSE Y CERTIFICACIÓN DE COMPENDIOS (EXIT 0 GATE)")
    logger.info("==================================================================")

    audit_results = {
        "total_files": 0,
        "total_words": 0,
        "clusters_covered": set(),
        "violations_words_exceeded": [],
        "violations_denylist": [],
        "violations_timestamps": [],
        "passed": False
    }

    p = Path(base_dir)
    files = list(p.glob("*/*.md"))
    audit_results["total_files"] = len(files)

    for f in files:
        cluster = f.parent.name
        audit_results["clusters_covered"].add(cluster)

        words = 0
        has_timecode = False
        has_denylist = False

        with open(f, "r", encoding="utf-8", errors="ignore") as fp:
            for line in fp:
                words += len(line.split())
                if "-->" in line and re.search(r"\d{1,2}:\d{2}.*?-->", line):
                    has_timecode = True
                if is_denylisted(line):
                    has_denylist = True

        audit_results["total_words"] += words

        if words > SovereignCompactor.MAX_WORDS_PER_COMPENDIUM:
            audit_results["violations_words_exceeded"].append((f.name, words))
        if has_timecode:
            audit_results["violations_timestamps"].append(f.name)
        if has_denylist:
            audit_results["violations_denylist"].append(f.name)

    audit_results["clusters_covered"] = sorted(list(audit_results["clusters_covered"]))

    logger.info(f"• Total compendios auditados: {audit_results['total_files']}")
    logger.info(f"• Total palabras en el ecosistema: {audit_results['total_words']:,}")
    logger.info(f"• Micro-clusters cubiertos: {len(audit_results['clusters_covered'])}")
    logger.info(f"• Archivos >350k palabras: {len(audit_results['violations_words_exceeded'])}")
    logger.info(f"• Archivos con timestamps: {len(audit_results['violations_timestamps'])}")
    logger.info(f"• Archivos con términos del denylist: {len(audit_results['violations_denylist'])}")

    passed = (
        audit_results["total_files"] > 0
        and len(audit_results["violations_words_exceeded"]) == 0
        and len(audit_results["violations_timestamps"]) == 0
        and len(audit_results["violations_denylist"]) == 0
    )
    audit_results["passed"] = passed

    if passed:
        logger.info("🎉 CERTIFICACIÓN FÍSICA EXITOSA: 100% CUMPLIMIENTO DE CONTRATOS (EXIT 0).")
    else:
        logger.error("❌ FALLA EN AUDITORÍA: Se detectaron violaciones a los contratos.")

    return audit_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compilador Soberano de Micro-Compendios")
    parser.add_argument("--audit", action="store_true", help="Solo audita compendios existentes")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir en disco")
    args = parser.parse_args()

    if args.audit:
        res = audit_compendiums()
        sys.exit(0 if res["passed"] else 1)

    compiler = SovereignCompendiumCompiler()
    compiler.execute(dry_run=args.dry_run)
    res = audit_compendiums()
    sys.exit(0 if res["passed"] else 1)
