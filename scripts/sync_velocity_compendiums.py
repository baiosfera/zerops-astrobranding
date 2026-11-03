#!/usr/bin/env python3
"""
sync_velocity_compendiums.py — Compactador y Sincronizador Soberano de Audio para VelocityMedia.
Concatena 300 audios de 36 cursos en 39 compendios maestros sin recodificar (ffmpeg -c copy)
y los ingesta de forma idempotente en el cuaderno satélite [VELOCITY_MEDIA_SPRINT_SALES].
"""

import sys
sys.dont_write_bytecode = True

import os
import re
import time
import argparse
import tempfile
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Inyectar rutas soberanas
ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from knowledge_sync import NotebookLMBridge, PartitionedManifest, MetadataFingerprint

SOURCE_ROOT = "/var/www/baiosfera/CURSOS/VELOCITYMEDIA"
OUTPUT_DIR = "/var/www/localstorage/knowledge_cache/velocity_compendiums"
NOTEBOOK_ID = "68dfe298-4e0c-460b-a893-2137dd131359"
NOTEBOOK_TITLE = "[VELOCITY_MEDIA_SPRINT_SALES]"
MAX_MB_PER_CHUNK = 180.0


def plan_master_compendiums(root_dir: str) -> List[Tuple[str, List[str], float, str]]:
    """Escanea y agrupa los 300 audios de VELOCITY en 39 compendios maestros particionados."""
    course_groups = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if "INFLUENCE" in dirpath.split(os.sep):
            continue
        m4as = sorted([f for f in filenames if f.endswith(".m4a")])
        if not m4as:
            continue
        rel = os.path.relpath(dirpath, root_dir)
        full_paths = [os.path.join(dirpath, f) for f in m4as]
        total_sz_mb = sum(os.path.getsize(p) for p in full_paths) / (1024 * 1024)

        clean_name = rel.replace("/", "_").replace(" ", "_")
        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "", clean_name)

        if total_sz_mb > 300.0:
            # 3 partes para podcasts gigantes
            n = len(full_paths)
            c1 = full_paths[: n // 3]
            c2 = full_paths[n // 3 : 2 * n // 3]
            c3 = full_paths[2 * n // 3 :]
            course_groups.append((f"{clean_name}_Parte_1_Master.m4a", c1, sum(os.path.getsize(p) for p in c1) / (1024 * 1024), rel))
            course_groups.append((f"{clean_name}_Parte_2_Master.m4a", c2, sum(os.path.getsize(p) for p in c2) / (1024 * 1024), rel))
            course_groups.append((f"{clean_name}_Parte_3_Master.m4a", c3, sum(os.path.getsize(p) for p in c3) / (1024 * 1024), rel))
        elif total_sz_mb > MAX_MB_PER_CHUNK:
            # 2 partes
            mid = len(full_paths) // 2
            p1 = full_paths[:mid]
            p2 = full_paths[mid:]
            course_groups.append((f"{clean_name}_Parte_1_Master.m4a", p1, sum(os.path.getsize(p) for p in p1) / (1024 * 1024), rel))
            course_groups.append((f"{clean_name}_Parte_2_Master.m4a", p2, sum(os.path.getsize(p) for p in p2) / (1024 * 1024), rel))
        else:
            course_groups.append((f"{clean_name}_Master.m4a", full_paths, total_sz_mb, rel))

    return sorted(course_groups, key=lambda x: x[0])


def concatenate_audio_group(output_path: str, input_files: List[str]) -> bool:
    """Concatena los archivos de audio en un solo contenedor m4a usando ffmpeg -c copy."""
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
        return True

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for audio in input_files:
            f.write(f"file '{audio}'\n")
        list_file = f.name

    try:
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            "-movflags", "+faststart",
            output_path,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
    finally:
        if os.path.exists(list_file):
            os.remove(list_file)


def run_sync(dry_run: bool = False, limit: int = None, delay: float = 3.0):
    print("==================================================================")
    print("🚀 SINCRONIZACIÓN DE COMPENDIOS DE AUDIO: VELOCITYMEDIA")
    print(f"🎯 Cuaderno Destino: {NOTEBOOK_TITLE} ({NOTEBOOK_ID})")
    print("==================================================================")

    groups = plan_master_compendiums(SOURCE_ROOT)
    print(f"• Compendios maestros planificados: {len(groups)}")
    if limit and limit > 0:
        groups = groups[:limit]
        print(f"• Ejecución limitada a: {limit} compendios")

    bridge = None if dry_run else NotebookLMBridge()
    manifest_mgr = PartitionedManifest()
    uploaded_fps = manifest_mgr.get_uploaded_fingerprints()

    existing_titles = {}
    if not dry_run:
        try:
            raw_sources = bridge.client.get_notebook_sources_with_types(NOTEBOOK_ID)
            existing_titles = {
                s.get("title", "").strip().lower(): s.get("id")
                for s in raw_sources if s.get("title")
            }
            print(f"• Fuentes activas pre-existentes en cuaderno: {len(existing_titles)}")
        except Exception as e:
            print(f"⚠️ No se pudo consultar fuentes pre-existentes: {e}")

    success_count = 0
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for idx, (master_name, tracks, est_mb, rel_path) in enumerate(groups, 1):
        print(f"\n[{idx}/{len(groups)}] Procesando: {master_name}")
        print(f"    Ruta: {rel_path} ({len(tracks)} lecciones, ~{est_mb:.1f} MB)")
        master_path = os.path.join(OUTPUT_DIR, master_name)

        # 1. Concatenación física con ffmpeg -c copy
        if not dry_run:
            if not os.path.exists(master_path) or os.path.getsize(master_path) == 0:
                print(f"    🔄 Concatenando {len(tracks)} audios en {master_name}...")
                ok = concatenate_audio_group(master_path, tracks)
                if not ok:
                    print(f"    ❌ Error concatenando {master_name}")
                    continue
            actual_sz_mb = os.path.getsize(master_path) / (1024 * 1024)
            print(f"    ✓ Archivo maestro listo: {actual_sz_mb:.1f} MB")
        else:
            print(f"    [DRY-RUN] Generaría: {master_path} (~{est_mb:.1f} MB)")

        # 2. Comprobación de idempotencia
        clean_title = master_name.strip().lower()
        if not dry_run and clean_title in existing_titles:
            src_id = existing_titles[clean_title]
            print(f"    ⏭️ Ya presente en NotebookLM (Source ID: {src_id}), omitiendo...")
            success_count += 1
            continue

        # 3. Subida hacia NotebookLM
        if dry_run:
            print(f"    [DRY-RUN] Subiría {master_name} -> {NOTEBOOK_TITLE}")
            success_count += 1
        else:
            item = {
                "path": master_path,
                "filename": master_name,
                "tier": "direct_audio",
            }
            print(f"    🚀 Ingestando audio maestro en NotebookLM (con transcripción)...")
            try:
                source_id = bridge.upload_source(
                    NOTEBOOK_ID,
                    item,
                    dry_run=False,
                    upload_delay=delay,
                )
                if source_id:
                    st = os.stat(master_path)
                    fp = MetadataFingerprint.compute_from_stat(
                        os.path.relpath(master_path, "/var/www"),
                        st.st_size,
                        int(st.st_mtime)
                    )
                    manifest_mgr.record_upload(
                        fingerprint=fp,
                        relative_path=f"localstorage/knowledge_cache/velocity_compendiums/{master_name}",
                        notebook_id=NOTEBOOK_ID,
                        notebook_title=NOTEBOOK_TITLE,
                        source_id=str(source_id),
                        source_type="direct_audio",
                    )
                    existing_titles[clean_title] = str(source_id)
                    success_count += 1
                    print(f"    ✅ Ingesta exitosa (Source ID: {source_id})")
                else:
                    print(f"    ⚠️ Timeout o sin confirmación de ID para: {master_name}")
            except Exception as e:
                print(f"    ❌ Error en subida de {master_name}: {e}")

    print("\n==================================================================")
    print(f"🏁 SINCRONIZACIÓN FINALIZADA: {success_count}/{len(groups)} compendios procesados.")
    print("==================================================================")


def main():
    parser = argparse.ArgumentParser(description="Compactador y Sincronizador de Audio de VelocityMedia a NotebookLM")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin realizar concatenaciones ni subidas reales")
    parser.add_argument("--limit", type=int, default=None, help="Límite máximo de compendios a procesar")
    parser.add_argument("--delay", type=float, default=3.0, help="Delay entre subidas en segundos")
    args = parser.parse_args()

    run_sync(dry_run=args.dry_run, limit=args.limit, delay=args.delay)


if __name__ == "__main__":
    main()
