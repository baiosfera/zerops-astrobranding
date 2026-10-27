#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
       KNOWLEDGE-SYNC: Motor Soberano de Ingesta Dinámica & Curaduría SSoT
                 para Google NotebookLM Pro & Zerops Control Plane
===============================================================================
Gobernanza: Supreme Directive v8.5 & CoHaLo Engineering (BAI-379)
Versión: 1.0.0 (Hardened Octubre 2026)
Invariantes Blindados:
  1. Metadata Fingerprint: Cero lectura de payloads en montaje FUSE rclone.
  2. Normalizador de Subtítulos: .srt/.vtt despojados de timecodes hacia texto limpio.
  3. Manifiesto Append-Only Particionado: Cero colisiones ni locks fallidos multi-ZCP.
  4. Query-Before-Create: Reutilización estricta de UUIDs en Google NotebookLM.
  5. Cadencia Segura: Retrasos de 5.0s (±1.5s jitter) y timeout de 600s en audios.
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
        # Colapsar espacios redundantes
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
# 3. Componente: Manifiesto Particionado Append-Only (Multi-ZCP Concurrency)
# =============================================================================
class PartitionedManifest:
    """Gestiona el registro de ingesta sin bloqueos POSIX sobre FUSE."""

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
            "version": "1.0",
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


# =============================================================================
# 4. Componente: Clasificador Semántico & Escáner Anatómico de Cursos
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
        "__pycache__", "node_modules", "vendor", ".git", ".rclone"
    }

    THEMATIC_CLUSTERS = {
        "copywriting": [
            "copy", "copywriting", "escritura", "titul", "hook", "storytelling",
            "narrativa", "persuasion", "redaccion"
        ],
        "ofertas": [
            "oferta", "precio", "pricing", "hormozi", "grand slam", "value equation",
            "propuesta de valor", "garantia"
        ],
        "funnels": [
            "funnel", "embudo", "checkout", "bump", "upsell", "downsell", "cvj",
            "customer value journey", "landing"
        ],
        "whatsapp": [
            "whatsapp", "chat", "bot", "cierre", "mensajeria", "conversacional"
        ],
        "email": [
            "email", "correo", "newsletter", "nurture", "secuencia", "listmonk", "broadcast"
        ],
        "ads": [
            "ads", "pauta", "meta", "facebook", "creativo", "trafico", "anuncio",
            "velocity", "audiencia", "escalado"
        ],
        "branding": [
            "brand", "marca", "branding", "identidad", "arquetipo", "posicionamiento",
            "category of one", "tono de voz"
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
        for cluster, keywords in cls.THEMATIC_CLUSTERS.items():
            for kw in keywords:
                if kw in lower_path:
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
                with os.scandir(current_dir) as it:
                    for entry in it:
                        if entry.name.startswith("."):
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name not in cls.EXCLUDE_DIRS and depth + 1 < max_depth:
                                queue.append((entry.path, depth + 1))
                        elif entry.is_file(follow_symlinks=False):
                            ext = os.path.splitext(entry.name)[1].lower()
                            tier = None
                            if ext in (".docx", ".md", ".txt", ".pdf"):
                                tier = "direct_document"
                            elif ext in (".srt", ".vtt"):
                                tier = "subtitle_text"
                            elif ext in (".aac", ".m4a", ".mp3"):
                                tier = "direct_audio"
                            elif ext == ".mp4":
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
# 5. Componente: Puente con SDK de NotebookLM (notebooklm_tools)
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

    def resolve_notebook_id(self, target_title: str) -> str:
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
        return str(nb_id)

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
# 6. Comandos CLI & Orquestación
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
            # Ignorar videos mp4 crudos en subidas automáticas
            if item["tier"] == "video_residual":
                continue

            fp = MetadataFingerprint.compute(item["path"])
            if fp not in uploaded:
                item["fingerprint"] = fp
                candidates.append(item)

    if not candidates:
        print("✅ Todo el contenido ya está sincronizado e ingestando en NotebookLM.")
        return

    print(f"• Candidatos listos para ingesta: {len(candidates)}")
    if args.limit and args.limit > 0:
        candidates = candidates[:args.limit]
        print(f"  (Limitado a {args.limit} archivos por esta ejecución)")

    bridge = None if args.dry_run else NotebookLMBridge()
    success_count = 0

    # Cache de cuadernos resueltos
    resolved_notebooks = {}

    for idx, item in enumerate(candidates, 1):
        target_title = item["target_notebook"]
        filename = item["filename"]
        fp = item["fingerprint"]

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
                    resolved_notebooks[target_title] = bridge.resolve_notebook_id(target_title)
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
# 7. Suite de Pruebas Físicas Unitarias Deterministas (Exit 0)
# =============================================================================
def run_tests():
    """Ejecuta pruebas unitarias de los 3 invariantes de software deterministas."""
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

    # Test 3: Manifiesto Particionado Append-Only
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
    print("✓ [Test 3] Manifiesto Particionado Append-Only Multi-ZCP: PASSED")

    # Test 4: Clasificador de Clusters Temáticos
    assert CourseScanner.classify_cluster("PLATZI/59 CONTENT COPY/clase.docx") == "copywriting"
    assert CourseScanner.classify_cluster("DIGITALMARKETER/Funnels/audit.md") == "funnels"
    assert CourseScanner.classify_cluster("CURSOS/MCV/Ofertas/guia.pdf") == "ofertas"
    assert CourseScanner.classify_cluster("VELOCITYMEDIA/ADS/creative.mp4") == "ads"
    print("✓ [Test 4] Clasificador Semántico de Clusters: PASSED")

    print("\n🎉 TODAS LAS PRUEBAS FÍSICAS PASARON CON ÉXITO (EXIT 0).")
    sys.exit(0)


# =============================================================================
# 8. Punto de Entrada Principal
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

    # Comando: push
    push_p = subparsers.add_parser("push", help="Ingesta incremental hacia NotebookLM")
    push_p.add_argument("--target", type=str, help="Directorio objetivo específico")
    push_p.add_argument("--cluster", type=str, help="Filtrar por cluster específico (copywriting, ofertas, etc.)")
    push_p.add_argument("--limit", type=int, default=0, help="Límite máximo de archivos a subir en esta pasada")
    push_p.add_argument("--delay", type=float, default=5.0, help="Delay entre subidas en segundos")
    push_p.add_argument("--max-depth", type=int, default=4, help="Profundidad máxima de escaneo")
    push_p.add_argument("--dry-run", action="store_true", help="Simula sin realizar subidas reales")

    args = parser.parse_args()

    if args.test:
        run_tests()

    if args.command == "scan":
        cmd_scan(args)
    elif args.command == "push":
        cmd_push(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
