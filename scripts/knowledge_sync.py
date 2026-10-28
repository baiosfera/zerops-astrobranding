#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
       KNOWLEDGE-SYNC: Motor Soberano de Ingesta Dinámica & Curaduría SSoT
                 para Google NotebookLM Pro & Zerops Control Plane
===============================================================================
Gobernanza: Supreme Directive v8.5 & CoHaLo Engineering (BAI-379, BAI-382)
Versión: 1.1.0 (Hardened Octubre 2026)
Invariantes Blindados:
  1. Metadata Fingerprint: Cero lectura de payloads en montaje FUSE rclone.
  2. Normalizador de Subtítulos: .srt/.vtt despojados de timecodes hacia texto limpio.
  3. Extractor de Audio FFmpeg: Conversión quirúrgica de .mp4 huérfanos a AAC 64k.
  4. Manifiesto Append-Only Particionado: Cero colisiones ni locks fallidos multi-ZCP.
  5. Query-Before-Create: Reutilización estricta de UUIDs en Google NotebookLM.
  6. Configuración de System Prompts: Prompts especializados de hasta 10k caracteres.
  7. Exportación de clusters.json: Descubrimiento de estado sin queries live innecesarias.
===============================================================================
"""

import os
import sys
import glob
import json
import time
import re
import socket
import uuid
import hashlib
import random
import argparse
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Set, Any

sys.dont_write_bytecode = True

# Descubrimiento dinámico del entorno UV de notebooklm-mcp-cli
uv_patterns = [
    os.path.expanduser("~/.local/share/uv/tools/notebooklm-mcp-cli/lib/python*/site-packages"),
    "/home/zerops/.local/share/uv/tools/notebooklm-mcp-cli/lib/python*/site-packages",
]
for pat in uv_patterns:
    for pkg_dir in sorted(glob.glob(pat), reverse=True):
        if os.path.isdir(pkg_dir) and pkg_dir not in sys.path:
            sys.path.insert(0, pkg_dir)


# =============================================================================
# 1. Componente: Limpiador y Normalizador de Subtítulos (.srt y .vtt)
# =============================================================================
class SubtitlesCleaner:
    """Normaliza archivos de subtítulos despojando timecodes y numeración técnica."""

    @staticmethod
    def clean(raw_text: str) -> str:
        """Convierte contenido SRT o VTT en párrafos de texto continuo sin metadatos."""
        # Remover cabecera WEBVTT
        text = re.sub(r"^WEBVTT.*?\n\n", "", raw_text, flags=re.DOTALL | re.IGNORECASE)

        # Remover timestamps SRT: 00:00:00,000 --> 00:00:00,000
        text = re.sub(r"\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}.*?\n", "\n", text)

        # Remover timestamps VTT cortos: 00:00.000 --> 00:00.000
        text = re.sub(r"\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}[,\.]\d{3}.*?\n", "\n", text)

        # Remover números de bloque de subtítulo (líneas con solo dígitos)
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)

        # Remover tags HTML simples como <v Voice>, <i>, </i>, <c.color>
        text = re.sub(r"<[^>]+>", "", text)

        # Unificar líneas rotas en párrafos limpios
        lines = [line.strip() for line in text.splitlines()]
        cleaned_paragraphs = []
        current_chunk = []

        for line in lines:
            if not line:
                if current_chunk:
                    cleaned_paragraphs.append(" ".join(current_chunk))
                    current_chunk = []
            else:
                current_chunk.append(line)

        if current_chunk:
            cleaned_paragraphs.append(" ".join(current_chunk))

        result = "\n\n".join(cleaned_paragraphs).strip()
        result = re.sub(r" +", " ", result)
        return result


# =============================================================================
# 2. Componente: Huella Digital Sintética (Metadata Fingerprint)
# =============================================================================
class MetadataFingerprint:
    """Calcula una huella única sin leer el payload del archivo a través de la red FUSE."""

    @staticmethod
    def compute(file_path: str, base_dir: str = "/var/www/baiosfera") -> str:
        """Deriva el hash desde ruta relativa, tamaño exacto en bytes y mtime POSIX."""
        rel_path = os.path.relpath(file_path, base_dir)
        st = os.stat(file_path)
        raw_key = f"{rel_path}:{st.st_size}:{int(st.st_mtime)}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


# =============================================================================
# 3. Componente: Extractor de Audio FFmpeg Quirúrgico
# =============================================================================
class AudioExtractor:
    """Extrae audio ligero en formato AAC a 64 kbps de videos huérfanos sin subtítulos."""

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
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0 or not os.path.exists(output_file):
            raise RuntimeError(f"FFmpeg falló al procesar el audio de: {video_path}")
        return output_file


# =============================================================================
# 4. Componente: Manifiesto Particionado Append-Only & Estado de Clusters
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
            "version": "1.1",
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
        """Exporta mapa canónico de clusters para descubrimiento rápido sin queries."""
        manifest_path = os.path.join(self.manifest_dir, "clusters.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(clusters_data, f, indent=2, ensure_ascii=False)

        # Sincronizar hacia localstorage si existe
        local_alt = "/var/www/localstorage/.knowledge_manifest"
        if os.path.isdir(local_alt):
            try:
                with open(os.path.join(local_alt, "clusters.json"), "w", encoding="utf-8") as f:
                    json.dump(clusters_data, f, indent=2, ensure_ascii=False)
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
# 5. Componente: Clasificador Semántico & Escáner Anatómico de Cursos
# =============================================================================
class CourseScanner:
    """Escanea y clasifica recursos educativos sin agotar memoria ni cuota FUSE."""

    DEFAULT_SEARCH_PATHS = [
        "/var/www/baiosfera/CURSOS/MCV/VIP",
        "/var/www/baiosfera/CURSOS/MCV/BASIC",
        "/var/www/baiosfera/CURSOS/VELOCITYMEDIA",
        "/var/www/baiosfera/DIGITALMARKETER",
        "/var/www/baiosfera/PLATZI/59 CONTENT COPY EMAIL SEO STORYTELLING VENTAS",
        "/var/www/baiosfera/PLATZI/47 GROWTH JOURNEY MKTN PRODUCT",
        "/var/www/baiosfera/PLATZI/30 BRANDING MARCAP INVEST",
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

    THEMATIC_CLUSTERS = {
        "copywriting": [
            "copy", "copywriting", "escritura", "titul", "hook", "storytelling",
            "narrativa", "persuasion", "redaccion", "headline", "swipe", "script",
            "prompt", "context vault", "prompting", "words that sell"
        ],
        "ofertas": [
            "oferta", "precio", "pricing", "hormozi", "grand slam", "value equation",
            "propuesta de valor", "garantia", "offer", "guarantee", "bonus", "stack",
            "site offers", "irresistible"
        ],
        "funnels": [
            "funnel", "embudo", "checkout", "bump", "upsell", "downsell", "cvj",
            "customer value journey", "landing", "conversion", "convert", "optin",
            "squeeze", "lead magnet", "playbook", "campaign fix", "sales-boosting",
            "funnel architecture"
        ],
        "whatsapp": [
            "whatsapp", "chat", "bot", "cierre", "mensajeria", "conversacional",
            "chatbot", "dm"
        ],
        "email": [
            "email", "correo", "newsletter", "nurture", "secuencia", "listmonk",
            "broadcast", "subject line", "autoresponder", "welcome sequence",
            "re-engagement"
        ],
        "ads": [
            "ads", "pauta", "meta", "facebook", "creativo", "trafico", "traffic",
            "anuncio", "velocity", "audiencia", "escalado", "paid", "media buyer",
            "roas", "creative", "campaign", "ad copy"
        ],
        "branding": [
            "brand", "marca", "branding", "identidad", "arquetipo", "posicionamiento",
            "category of one", "tono de voz", "authority", "reputation", "brand guidelines"
        ],
    }

    CLUSTER_NOTEBOOK_TITLES = {
        "copywriting": "[ESPECIALIDAD_COPY_TITULARES_Y_GANCHOS]",
        "ofertas": "[ESPECIALIDAD_OFERTAS_Y_PRICING]",
        "funnels": "[ESPECIALIDAD_FUNNELS_CHECKOUTS_Y_BUMPS]",
        "whatsapp": "[ESPECIALIDAD_WHATSAPP_MARKETING_Y_BOTS]",
        "email": "[ESPECIALIDAD_EMAIL_AUTOMATION_Y_NURTURE]",
        "ads": "[ESPECIALIDAD_META_ADS_CREATIVOS_Y_PAUTA]",
        "branding": "[ESPECIALIDAD_BRANDING_Y_POSICIONAMIENTO]",
    }

    @classmethod
    def classify_cluster(cls, path_str: str) -> str:
        """Determina el cluster temático a partir de palabras clave en la ruta."""
        lower_path = path_str.lower()
        normalized_path = re.sub(r"[_\-\.]+", " ", lower_path)
        for cluster, keywords in cls.THEMATIC_CLUSTERS.items():
            for kw in keywords:
                if kw in lower_path or kw in normalized_path:
                    return cluster
        return "general"

    @classmethod
    def scan_path(
        cls,
        base_dir: str,
        max_depth: int = 4,
    ) -> List[Dict[str, Any]]:
        """Recorre de forma controlada el sistema de archivos buscando recursos de alto valor mediante BFS rápido."""
        resources = []
        if not os.path.exists(base_dir):
            return resources

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

                has_subtitles = any(
                    os.path.splitext(e.name)[1].lower() in (".srt", ".vtt")
                    for e in files
                )
                has_docs = any(
                    os.path.splitext(e.name)[1].lower() in (".docx", ".pdf", ".md", ".txt")
                    for e in files
                )

                for entry in files:
                    ext = os.path.splitext(entry.name)[1].lower()
                    tier = None
                    if ext in (".docx", ".md", ".txt", ".pdf"):
                        tier = "direct_document"
                    elif ext in (".srt", ".vtt"):
                        tier = "subtitle_text"
                    elif ext in (".aac", ".m4a", ".mp3"):
                        tier = "direct_audio"
                    elif ext == ".mp4":
                        if not has_subtitles and not has_docs:
                            tier = "orphan_video"
                        else:
                            tier = "video_residual"

                    if tier:
                        try:
                            st = entry.stat(follow_symlinks=False)
                            cluster = cls.classify_cluster(entry.path)
                            resources.append({
                                "path": entry.path,
                                "filename": entry.name,
                                "ext": ext,
                                "tier": tier,
                                "size_bytes": st.st_size,
                                "mtime": int(st.st_mtime),
                                "cluster": cluster,
                                "target_notebook": cls.CLUSTER_NOTEBOOK_TITLES.get(
                                    cluster, f"[ESPECIALIDAD_{cluster.upper()}]"
                                ),
                            })
                        except Exception:
                            continue
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
    "whatsapp": """Eres el Estratega de Comercio Conversacional y Automatizaciones de Mensajería.
Tu foco es extraer los flujos de mensajería (WhatsApp, Telegram, DM) que maximizan respuesta, engagement y transacciones.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Diseña árboles de decisión y flujos conversacionales de calificación rápida.
- Establece el protocolo de transición entre automatización y asesor humano (Human Takeover).
- Formula guiones de recuperación de carritos abandonados con lenguaje natural, cercano y respetuoso.
- Extrae secuencias de seguimiento post-registro para webinars, lanzamientos y reservas en vivo.
- Codifica las respuestas ante las 5 objeciones más frecuentes de precios y tiempos de entrega.
""",
    "email": """Eres el Director de Email Marketing y Entregabilidad de Mensajería Directa.
Tu foco es extraer los flujos de email marketing que maximizan apertura, clics y retención de suscriptores.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Extrae la estructura de la Soap Opera Sequence (5 emails de bienvenida con ganchos narrativos y tensión continua).
- Extrae el modelo Seinfeld (historias cotidianas conectadas fluidamente con la oferta comercial).
- Formula líneas de asunto de alta apertura basadas en curiosidad, beneficio directo y contraste de expectativas.
- Especifica las reglas de higiene técnica de entregabilidad (DMARC, DKIM, SPF, ratios de clics, términos que garantizan inbox primario).
""",
    "ads": """Eres el Media Buyer Maestro y Especialista en Creativos Publicitarios de Meta Ads y Tráfico Pago.
Tu objetivo es extraer los frameworks de creación de anuncios, ángulos de comunicación y tácticas de escalado.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Descompón la anatomía del anuncio: Hook Visual/Auditivo (primeros 3 segundos) -> Problema/Ángulo -> Solución/Prueba -> Llamado a la Acción.
- Extrae matrices de variación de ángulos publicitarios para testear múltiples dolores de avatar con un mismo producto.
- Formula scripts de UGC (User Generated Content) y VSL (Video Sales Letters) con indicaciones escénicas y de ritmo.
- Documenta las metodologías de prueba de creativos y lectura de métricas tempranas (Thumbstop Ratio, Hold Rate, CTR saliente).
""",
    "branding": """Eres el Consultor Senior de Estrategia de Marca, Posicionamiento y Categoría Única.
Tu misión es extraer los marcos de construcción de marcas memorables y posicionamiento defensible.

REGLAS DE RESPUESTA AFIRMATIVAS:
- Modela la definición de la 'Categoría de Uno' (Category of One) enseñada en los cursos para erradicar la competencia directa.
- Estructura las matrices de personalidad y tono de voz con ejemplos afirmativos y distinciones claras de estilo.
- Documenta las etapas del viaje de identidad: Propósito -> Arquetipo -> Pilares de Contenido -> Simbología Visual y Lingüística.
- Codifica los mecanismos de autoridad y reputación para profesionales y empresas en sectores de alta competencia.
""",
}


# =============================================================================
# 7. Componente: Puente con SDK de NotebookLM (notebooklm_tools)
# =============================================================================
class NotebookLMBridge:
    """Encapsula llamadas seguras con reintentos y respeto de cuotas."""

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

        # Configurar de inmediato el system prompt especializado si corresponde
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
            # Normalizar subtítulo en memoria y subir como texto puro
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                raw_text = f.read()
            clean_text = SubtitlesCleaner.clean(raw_text)
            if not clean_text or len(clean_text) < 20:
                return None

            title = f"[Subtítulo] {os.path.splitext(filename)[0]}"
            res = self.client.add_text_source(notebook_id, clean_text, title=title)
            return getattr(res, "id", None) or res.get("id") or "uploaded_text"

        elif tier == "orphan_video":
            # Extraer audio AAC a 64k y subirlo como archivo de audio directo
            print(f"    🎙️ Extrayendo audio AAC (64k) de video huérfano...")
            aac_path = AudioExtractor.extract_aac(path)
            res = self.client.add_file(
                notebook_id,
                aac_path,
                wait=True,
                wait_timeout=600.0,
            )
            return getattr(res, "id", None) or (res.get("id") if isinstance(res, dict) else "uploaded_audio")

        elif tier in ("direct_document", "direct_audio"):
            # Subida directa mediante add_file del SDK
            is_audio = tier == "direct_audio"
            timeout = 600.0 if is_audio else 120.0
            res = self.client.add_file(
                notebook_id,
                path,
                wait=True,
                wait_timeout=timeout,
            )
            return getattr(res, "id", None) or (res.get("id") if isinstance(res, dict) else "uploaded_file")

        return None


# =============================================================================
# 8. Comandos CLI & Orquestación
# =============================================================================
def cmd_scan(args):
    """Escanea el catálogo de cursos y muestra la distribución por cluster y tier."""
    print("==================================================================")
    print("🔍 ESCANEO ANATÓMICO DE CURSOS (Costo de tokens: 0)")
    print("==================================================================")

    manifest_mgr = PartitionedManifest()
    uploaded = manifest_mgr.get_uploaded_fingerprints()
    print(f"• Manifiesto SSoT activo: {len(uploaded)} fuentes ya registradas.")

    paths = [args.target] if args.target else CourseScanner.DEFAULT_SEARCH_PATHS
    total_found = 0
    pending_found = 0
    by_cluster: Dict[str, List[Dict[str, Any]]] = {}

    for p in paths:
        if not os.path.exists(p):
            continue
        print(f"• Escaneando: {p}...")
        found = CourseScanner.scan_path(p, max_depth=args.max_depth)
        total_found += len(found)

        for item in found:
            fp = MetadataFingerprint.compute(item["path"])
            item["fingerprint"] = fp
            item["already_uploaded"] = fp in uploaded
            if not item["already_uploaded"]:
                pending_found += 1

            c = item["cluster"]
            if c not in by_cluster:
                by_cluster[c] = []
            by_cluster[c].append(item)

    print("\n📊 RESUMEN DE CLUSTERS TEMÁTICOS:")
    for cluster, items in sorted(by_cluster.items()):
        pending_in_c = sum(1 for i in items if not i["already_uploaded"])
        target_nb = CourseScanner.CLUSTER_NOTEBOOK_TITLES.get(cluster, f"[ESPECIALIDAD_{cluster.upper()}]")
        print(f"  📁 {cluster.upper()} ({target_nb}):")
        print(f"     Total recursos: {len(items)} | Pendientes por subir: {pending_in_c}")

        # Desglose por tier
        tiers = {}
        for it in items:
            tiers[it["tier"]] = tiers.get(it["tier"], 0) + 1
        for t, count in tiers.items():
            print(f"       - {t}: {count}")

    print(f"\n✅ Total recursos detectados: {total_found} | Pendientes de ingesta: {pending_found}")


def cmd_init_clusters(args):
    """Pre-aprovisiona los 7 cuadernos de cluster, inyecta prompts y exporta clusters.json."""
    print("==================================================================")
    print("🏗️ INICIALIZACIÓN DE CLUSTERS Y SYSTEM PROMPTS EN NOTEBOOKLM")
    print("==================================================================")

    bridge = NotebookLMBridge()
    manifest_mgr = PartitionedManifest()
    clusters_manifest = {}

    # Obtener cuadernos existentes
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

        # Configurar system prompt especializado
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

    # Exportar archivo clusters.json
    out_path = manifest_mgr.export_clusters_manifest(clusters_manifest)
    print(f"\n✅ Manifiesto canónico de clusters exportado en: {out_path}")
    print("\n📋 MAPA CANÓNICO DE CLUSTERS:")
    for c_key, data in clusters_manifest.items():
        print(f"  • {c_key.upper():<12} -> ID: {data['notebook_id']} ({data['title']})")


def cmd_push(args):
    """Ejecuta la ingesta idempotente hacia los cuadernos de NotebookLM."""
    print("==================================================================")
    print("🚀 INGESTA DINÁMICA IDEMPOTENTE A NOTEBOOKLM")
    print("==================================================================")

    manifest_mgr = PartitionedManifest()
    uploaded = manifest_mgr.get_uploaded_fingerprints()

    paths = [args.target] if args.target else CourseScanner.DEFAULT_SEARCH_PATHS
    candidates = []

    for p in paths:
        if not os.path.exists(p):
            continue
        found = CourseScanner.scan_path(p, max_depth=args.max_depth)
        for item in found:
            if args.cluster and item["cluster"] != args.cluster:
                continue

            # Videos residuales (que ya tienen subtítulos o docs) se ignoran
            if item["tier"] == "video_residual":
                continue

            # Videos huérfanos se procesan solo si se solicita --convert-orphan-videos
            if item["tier"] == "orphan_video" and not getattr(args, "convert_orphan_videos", False):
                continue

            fp = MetadataFingerprint.compute(item["path"])
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

    # Cargar mapa de clusters conocido
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
        except Exception as e:
            print(f"    ❌ Error subiendo {filename}: {e}")

    print(f"\n🏁 Ingesta completada. Procesados con éxito: {success_count}/{len(candidates)}")


# =============================================================================
# 9. Suite de Pruebas Físicas Unitarias Deterministas (Exit 0)
# =============================================================================
def run_tests():
    """Ejecuta pruebas unitarias de los componentes de software deterministas."""
    print("==================================================================")
    print("🧪 EJECUTANDO SUITE DE PRUEBAS UNITARIAS DETERMINISTAS (knowledge-sync)")
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
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"Prueba de contenido efimero")
        tmp_path = tmp.name

    fp1 = MetadataFingerprint.compute(tmp_path, base_dir=os.path.dirname(tmp_path))
    time.sleep(0.01)
    fp2 = MetadataFingerprint.compute(tmp_path, base_dir=os.path.dirname(tmp_path))
    assert fp1 == fp2, "Falla Test 2: La huella sintética debe ser determinista e idempotente"
    os.remove(tmp_path)
    print("✓ [Test 2] Huella Digital Sintética (Metadata Fingerprint): PASSED")

    # Test 3: Manifiesto Particionado Append-Only y clusters.json
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
        assert loaded["fp123456"]["source_id"] == "src-999", "Falla Test 3: Datos de evento corruptos"

        # Prueba export clusters.json
        man.export_clusters_manifest({"copywriting": {"notebook_id": "test-uuid"}})
        c_manifest = man.load_clusters_manifest()
        assert c_manifest.get("copywriting", {}).get("notebook_id") == "test-uuid"
    print("✓ [Test 3] Manifiesto Particionado & Exportación de clusters.json: PASSED")

    # Test 4: Clasificador de Clusters Temáticos con Términos en Inglés y Español
    assert CourseScanner.classify_cluster("PLATZI/59 CONTENT COPY/clase.docx") == "copywriting"
    assert CourseScanner.classify_cluster("DIGITALMARKETER/Funnels/audit.md") == "funnels"
    assert CourseScanner.classify_cluster("DIGITALMARKETER/01_AI_SYSTEMS/Marketing_Context_Vault.md") == "copywriting"
    assert CourseScanner.classify_cluster("DIGITALMARKETER/03_TRAINING_PLAYBOOKS/15_Minute_Campaign_Fix.pdf") == "funnels"
    assert CourseScanner.classify_cluster("DIGITALMARKETER/Offers/3_Sales_Boosting_Site_Offers.pdf") == "ofertas"
    assert CourseScanner.classify_cluster("CURSOS/MCV/Ofertas/guia.pdf") == "ofertas"
    assert CourseScanner.classify_cluster("VELOCITYMEDIA/ADS/creative.mp4") == "ads"
    print("✓ [Test 4] Clasificador Semántico de Clusters (ES + EN): PASSED")

    # Test 5: Extractor de Audio FFmpeg Quirúrgico
    with tempfile.TemporaryDirectory() as tmp_dir:
        dummy_wav = os.path.join(tmp_dir, "test_audio.wav")
        # Generar 1 segundo de audio mudo con ffmpeg
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "1", dummy_wav],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        extracted_aac = AudioExtractor.extract_aac(dummy_wav, output_dir=tmp_dir)
        assert os.path.isfile(extracted_aac), "Falla Test 5: No se generó el archivo AAC"
        assert os.path.getsize(extracted_aac) > 100, "Falla Test 5: Archivo AAC demasiado pequeño"
    print("✓ [Test 5] Extractor de Audio FFmpeg Quirúrgico: PASSED")

    print("\n🎉 TODAS LAS PRUEBAS FÍSICAS PASARON CON ÉXITO (EXIT 0).")
    sys.exit(0)


# =============================================================================
# 10. Punto de Entrada Principal
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Motor Soberano de Ingesta Dinámica & Curaduría SSoT para NotebookLM"
    )
    parser.add_argument("--test", action="store_true", help="Ejecuta suite de pruebas unitarias físicas")

    subparsers = parser.add_subparsers(dest="command")

    # Comando: scan
    scan_p = subparsers.add_parser("scan", help="Escanea cursos sin gastar tokens ni cuota FUSE")
    scan_p.add_argument("--target", type=str, help="Directorio objetivo específico a escanear")
    scan_p.add_argument("--max-depth", type=int, default=4, help="Profundidad máxima de escaneo")

    # Comando: init-clusters
    subparsers.add_parser(
        "init-clusters",
        help="Pre-aprovisiona los 7 cuadernos de cluster, inyecta system prompts y exporta clusters.json"
    )

    # Comando: push
    push_p = subparsers.add_parser("push", help="Ingesta incremental hacia NotebookLM")
    push_p.add_argument("--target", type=str, help="Directorio objetivo específico")
    push_p.add_argument("--cluster", type=str, help="Filtrar por cluster específico (copywriting, ofertas, etc.)")
    push_p.add_argument("--limit", type=int, default=0, help="Límite máximo de archivos a subir en esta pasada")
    push_p.add_argument("--delay", type=float, default=5.0, help="Delay entre subidas en segundos")
    push_p.add_argument("--max-depth", type=int, default=4, help="Profundidad máxima de escaneo")
    push_p.add_argument("--convert-orphan-videos", action="store_true", help="Convierte videos huérfanos a audio AAC antes de subir")
    push_p.add_argument("--dry-run", action="store_true", help="Simula sin realizar subidas reales")

    args = parser.parse_args()

    if args.test:
        run_tests()

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "init-clusters":
        cmd_init_clusters(args)
    elif args.command == "push":
        cmd_push(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
