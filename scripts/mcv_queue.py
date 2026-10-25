#!/usr/bin/env python3
"""
MCV Unattended Zero-Credit Queue Orchestrator (v1.0.0)
Processes queued MCV courses without human intervention and with 0 CREDITS consumed.
Architecture:
  - Scans target course directory (default: AUTHOR/Lavin).
  - Skips already verified courses in 0s.
  - Automatically prioritizes OPTIMIZE_ONLY courses (videos in disk, missing NotebookLM audios/360p).
  - Resolves cloud links (Sync.com, Mega.nz, Google Drive) strictly from local instructions/metadata.
  - Downloads, decompresses (password: www.miscursosvirtuales.com), transcodes to 360p CRF 28 (nice 19),
    extracts AAC/MP3 audios for Google NotebookLM, and compiles final .md reports.
  - Emits real-time telemetry to /var/www/localstorage/mcv_staging/mcv_queue_status.json and mcv_queue.log.
"""

import os
import sys
import time
import json
import signal
import shutil
import argparse
import logging
from typing import List, Dict, Any, Optional

# Enforce America/Bogota timezone
os.environ["TZ"] = "America/Bogota"
if hasattr(time, "tzset"):
    time.tzset()

sys.dont_write_bytecode = True
MCV_DIR = "/var/www/baiosfera/CURSOS/MCV"
if MCV_DIR not in sys.path:
    sys.path.insert(0, MCV_DIR)

import mcv_downloader as mcv

STAGING_BASE = "/var/www/localstorage/mcv_staging"
QUEUE_LOG = os.path.join(STAGING_BASE, "mcv_queue.log")
QUEUE_STATUS_FILE = os.path.join(STAGING_BASE, "mcv_queue_status.json")
QUEUE_PID_FILE = os.path.join(STAGING_BASE, "mcv_queue.pid")

os.makedirs(STAGING_BASE, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(QUEUE_LOG, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("mcv_queue")


class MCVQueueOrchestrator:
    def __init__(self, target_dir: str, audio_format: str = "aac"):
        self.target_dir = os.path.abspath(target_dir)
        self.audio_format = audio_format
        self.running = True
        self.queue_items: List[Dict[str, Any]] = []
        self.current_idx = 0
        self.state: Dict[str, Any] = {
            "status": "INITIALIZING",
            "pid": os.getpid(),
            "target_dir": self.target_dir,
            "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_courses": 0,
            "completed_count": 0,
            "failed_count": 0,
            "current_index": 0,
            "current_course": "",
            "current_action": "",
            "current_progress": 0.0,
            "current_detail": "",
            "completed_courses": [],
            "failed_courses": [],
            "pending_courses": []
        }

    def _update_state(self, **kwargs):
        self.state.update(kwargs)
        self.state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            tmp_path = QUEUE_STATUS_FILE + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, QUEUE_STATUS_FILE)
        except Exception as e:
            logger.warning(f"Error escribiendo estado de cola: {e}")

    def scan_and_build_queue(self):
        logger.info(f"🔍 Escaneando directorio objetivo: {self.target_dir}...")
        if not os.path.isdir(self.target_dir):
            raise FileNotFoundError(f"Directorio no encontrado: {self.target_dir}")

        entries = sorted(os.listdir(self.target_dir))
        optimize_tasks = []
        sync_tasks = []
        gdrive_tasks = []
        mega_tasks = []
        other_tasks = []

        video_exts = (".mp4", ".ts", ".mkv", ".mov", ".avi", ".webm")

        for entry in entries:
            p = os.path.join(self.target_dir, entry)
            if not os.path.isdir(p):
                continue

            existing_videos = []
            for r, _, files in os.walk(p):
                if "NOTEBOOKLM_AUDIOS" in r or "_temp_downloads" in r:
                    continue
                for f in files:
                    if f.lower().endswith(video_exts) and not f.startswith("."):
                        existing_videos.append(os.path.join(r, f))

            audios_dir = os.path.join(p, "NOTEBOOKLM_AUDIOS")
            completed_audios = []
            if os.path.isdir(audios_dir):
                completed_audios = [
                    f for f in os.listdir(audios_dir)
                    if f.lower().endswith((".aac", ".mp3", ".opus")) and os.path.getsize(os.path.join(audios_dir, f)) > 1024
                ]

            # Si ya tiene videos y audios correspondientes, curso 100% completo
            if existing_videos and completed_audios and len(completed_audios) >= len(existing_videos):
                continue

            # Caso 1: Tiene videos pero le faltan audios/optimización (ej: Módulo 2)
            if existing_videos and not completed_audios:
                optimize_tasks.append({
                    "folder": entry,
                    "dir_path": p,
                    "action": "OPTIMIZE_ONLY",
                    "provider": "local",
                    "videos_count": len(existing_videos),
                    "links": [],
                    "password": "www.miscursosvirtuales.com"
                })
                continue

            # Caso 2: 0 videos descargados -> Buscar enlaces en archivos locales
            if not existing_videos:
                content = ""
                local_txt = os.path.join(p, "INSTRUCCIONES_DESCARGA.txt")
                if os.path.isfile(local_txt):
                    try:
                        with open(local_txt, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                    except Exception:
                        pass

                if not content:
                    for mf in os.listdir(p):
                        if mf.endswith(".md") and not mf.startswith("RUTA_DE_APRENDIZAJE") and not mf.startswith("MANUAL"):
                            try:
                                with open(os.path.join(p, mf), "r", encoding="utf-8", errors="replace") as f:
                                    content = f.read()
                                break
                            except Exception:
                                pass

                links = mcv.parse_txt_links(content) if content else []
                pw = mcv.parse_txt_password(content) if content else "www.miscursosvirtuales.com"

                if links:
                    prov = links[0].get("provider", "unknown").lower()
                    item = {
                        "folder": entry,
                        "dir_path": p,
                        "action": "DOWNLOAD_AND_OPTIMIZE",
                        "provider": prov,
                        "parts_count": len(links),
                        "links": links,
                        "password": pw or "www.miscursosvirtuales.com"
                    }
                    if prov == "sync":
                        sync_tasks.append(item)
                    elif prov == "gdrive":
                        gdrive_tasks.append(item)
                    elif prov == "mega":
                        mega_tasks.append(item)
                    else:
                        other_tasks.append(item)
                else:
                    logger.warning(f"⚠️ Omitiendo '{entry}': 0 videos y sin enlaces válidos en txt/md.")

        # Orden de ejecución estratégico:
        # 1. OPTIMIZE_ONLY primero (inmediato, libera espacio de videos pesados)
        # 2. Sync.com (sin cuotas de tráfico diarias)
        # 3. Google Drive (alta velocidad)
        # 4. Mega.nz (sujeto a límite diario de 5GB)
        # 5. Otros
        self.queue_items = optimize_tasks + sync_tasks + gdrive_tasks + mega_tasks + other_tasks

        logger.info(f"📋 Cola construida con {len(self.queue_items)} cursos pendientes:")
        for idx, item in enumerate(self.queue_items, 1):
            logger.info(f"   [{idx:02d}] {item['folder']} | {item['action']} ({item['provider'].upper()})")

        self._update_state(
            total_courses=len(self.queue_items),
            pending_courses=[it["folder"] for it in self.queue_items]
        )

    def process_item(self, item: Dict[str, Any]) -> bool:
        folder = item["folder"]
        dir_path = item["dir_path"]
        action = item["action"]
        links = item.get("links", [])
        pw = item.get("password", "www.miscursosvirtuales.com")

        logger.info("\n" + "=" * 70)
        logger.info(f"🚀 [COLA {self.current_idx}/{len(self.queue_items)}] Iniciando: {folder}")
        logger.info(f"   Acción: {action} | Proveedor: {item.get('provider', '').upper()}")
        logger.info("=" * 70)

        args = argparse.Namespace(
            no_reduce=False,
            audio_format=self.audio_format,
            audio_only=False,
            upload_nlm=False,
            alias="Lavin",
            interval=3600,
            force=False
        )

        meta = mcv.resolve_or_lookup_course_metadata(dir_path, alias="Lavin")
        meta["password"] = pw
        if links:
            meta["cloud_links"] = links
            meta["all_option_sets"] = [links]

        if action == "OPTIMIZE_ONLY":
            self._update_state(
                current_action="OPTIMIZING",
                current_detail=f"Reduciendo {item.get('videos_count', 0)} videos a 360p y extrayendo audios"
            )
            ok = mcv.optimize_and_finalize_course(dir_path, meta, args)
            return ok

        # DOWNLOAD_AND_OPTIMIZE
        self._update_state(
            current_action="DOWNLOADING",
            current_detail=f"Descargando {len(links)} partes desde {item.get('provider', '').upper()}"
        )

        course_slug = mcv.sanitize_folder_name(folder)
        temp_download_dir = os.path.join(STAGING_BASE, course_slug, "_temp_downloads")
        os.makedirs(temp_download_dir, exist_ok=True)
        log_file = os.path.join(dir_path, "download_progress.log")

        tracker = mcv.ProgressTracker(
            log_file=log_file,
            alert_interval_sec=args.interval,
            course_dir=dir_path,
            course_title=meta.get("title", folder)
        )
        tracker.start()

        downloaded_archives = []
        try:
            for p_idx, lk in enumerate(links, 1):
                part_name = lk.get("part", f"Parte {p_idx}")
                url = lk.get("url")
                provider = lk.get("provider", "unknown").lower()

                logger.info(f"📦 Descargando {part_name} de {len(links)} ({provider.upper()}): {url}")
                self._update_state(
                    current_detail=f"Descargando {part_name}/{len(links)} ({provider.upper()})"
                )

                if provider == "sync":
                    files = mcv.download_sync_link(url, temp_download_dir, part_name, tracker, part_index=p_idx)
                    downloaded_archives.extend(files)
                elif provider == "mega":
                    files = mcv.download_mega_link(url, temp_download_dir, part_name, tracker, part_index=p_idx)
                    downloaded_archives.extend(files)
                elif provider == "gdrive":
                    files = mcv.download_gdrive_link(url, temp_download_dir, part_name, tracker, part_index=p_idx)
                    downloaded_archives.extend(files)
                else:
                    files = mcv.download_direct_link(url, temp_download_dir, part_name, tracker, part_index=p_idx)
                    downloaded_archives.extend(files)

            tracker.stop()

            # Descompresión y Desempaquetado
            self._update_state(
                current_action="EXTRACTING",
                current_detail="Descomprimiendo archivos y desempaquetando árbol de medios"
            )

            compressed_archives = []
            raw_items = []
            for item_p in downloaded_archives:
                if os.path.isfile(item_p) and mcv.is_compressed_archive(item_p):
                    compressed_archives.append(item_p)
                else:
                    raw_items.append(item_p)

            primary_archives = [
                arch for arch in compressed_archives
                if not mcv.is_secondary_volume(arch)
            ]

            candidate_passwords = [pw, "www.miscursosvirtuales.com"]
            for arch in primary_archives:
                logger.info(f"🔓 Descomprimiendo: {os.path.basename(arch)}...")
                ok_ext, msg = mcv.extract_archive_with_fallbacks(arch, dir_path, candidate_passwords)
                if not ok_ext:
                    raise RuntimeError(f"Falla al descomprimir {arch}: {msg}")

            nested_count = mcv.recursive_extract_tree(dir_path, candidate_passwords)
            if nested_count > 0:
                logger.info(f"✅ Se desempaquetaron {nested_count} archivos comprimidos anidados.")

            # Mover elementos sueltos
            for raw in raw_items:
                dest_raw = os.path.join(dir_path, os.path.basename(raw))
                if raw != dest_raw and os.path.exists(raw):
                    if os.path.exists(dest_raw):
                        if os.path.isdir(dest_raw):
                            shutil.rmtree(dest_raw, ignore_errors=True)
                        else:
                            os.remove(dest_raw)
                    shutil.move(raw, dest_raw)

            # Purgar archivos comprimidos y staging
            for arch in compressed_archives:
                if os.path.exists(arch):
                    try:
                        os.remove(arch)
                    except Exception:
                        pass
            if os.path.exists(temp_download_dir):
                shutil.rmtree(temp_download_dir, ignore_errors=True)

            # Optimización de videos a 360p y audios NotebookLM
            self._update_state(
                current_action="TRANSCODING",
                current_detail="Reduciendo videos a 360p (nice 19) y extrayendo audios NotebookLM"
            )
            ok_opt = mcv.optimize_and_finalize_course(dir_path, meta, args)
            return ok_opt

        except Exception as e_proc:
            tracker.stop()
            logger.error(f"❌ Error procesando {folder}: {e_proc}", exc_info=True)
            return False

    def run(self):
        self.scan_and_build_queue()
        if not self.queue_items:
            logger.info("✨ No hay cursos pendientes en la cola. Todo completado.")
            self._update_state(status="COMPLETED", current_detail="Cola vacía o completada")
            return

        self._update_state(status="RUNNING")

        for idx, item in enumerate(self.queue_items, 1):
            if not self.running:
                logger.info("🛑 Detención de la cola solicitada.")
                break

            self.current_idx = idx
            folder = item["folder"]
            self._update_state(
                current_index=idx,
                current_course=folder,
                current_progress=round((idx - 1) / len(self.queue_items) * 100, 1)
            )

            success = self.process_item(item)

            if success:
                logger.info(f"✅ [ÉXITO] Curso {folder} finalizado al 100%.")
                self.state["completed_count"] += 1
                self.state["completed_courses"].append(folder)
                if folder in self.state["pending_courses"]:
                    self.state["pending_courses"].remove(folder)
            else:
                logger.error(f"❌ [FALLO] Curso {folder} no pudo completarse.")
                self.state["failed_count"] += 1
                self.state["failed_courses"].append({"folder": folder, "time": time.strftime("%H:%M:%S")})
                if folder in self.state["pending_courses"]:
                    self.state["pending_courses"].remove(folder)

            self._update_state()

        self._update_state(
            status="FINISHED",
            current_action="IDLE",
            current_detail=f"Completados: {self.state['completed_count']} | Fallidos: {self.state['failed_count']}",
            current_progress=100.0
        )
        logger.info("\n" + "=" * 70)
        logger.info(f"🏁 COLA DESATENDIDA FINALIZADA")
        logger.info(f"   Completados: {self.state['completed_count']}/{len(self.queue_items)}")
        logger.info(f"   Fallidos:    {self.state['failed_count']}/{len(self.queue_items)}")
        logger.info("=" * 70)


def signal_handler(signum, frame):
    logger.info("⚠️ Señal de terminación recibida. Cerrando proceso ordenadamente...")
    if os.path.exists(QUEUE_PID_FILE):
        try:
            os.remove(QUEUE_PID_FILE)
        except Exception:
            pass
    sys.exit(0)


def show_queue_status(watch: bool = False):
    while True:
        if watch:
            sys.stdout.write("\033[3J\033[H\033[2J")
            sys.stdout.flush()

        if not os.path.exists(QUEUE_STATUS_FILE):
            print("\nℹ️  No hay cola de MCV activa ni registro previo.")
            print("   Iniciá la cola con: mcv-queue start\n")
            return

        try:
            with open(QUEUE_STATUS_FILE, "r", encoding="utf-8") as f:
                st = json.load(f)
        except Exception as e:
            print(f"Error leyendo estado: {e}")
            return

        pid = st.get("pid")
        is_alive = False
        if pid:
            try:
                os.kill(pid, 0)
                is_alive = True
            except OSError:
                is_alive = False

        status_str = st.get("status", "UNKNOWN")
        badge = "🟢 ACTIVA" if (is_alive and status_str == "RUNNING") else ("🟡 DETENIDA" if not is_alive else status_str)

        print("=" * 80)
        print("📋 TABLERO DE COLA DESATENDIDA MCV — CERO CRÉDITOS")
        print("=" * 80)
        print(f" Estado:           {badge} (PID Cola: {pid if is_alive else 'Inactivo'})")
        print(f" Directorio Base:  {st.get('target_dir')}")
        print(f" Inicio:           {st.get('started_at')} | Última actualización: {st.get('updated_at')}")
        print(f" Progreso Cola:    {st.get('completed_count', 0)}/{st.get('total_courses', 0)} cursos completados ({st.get('current_progress', 0.0)}%)")
        print(f" Curso Activo:     {st.get('current_course') or 'Ninguno'}")
        print("-" * 80)

        # Inyectar la telemetría viva de PROGRESO.txt si existe
        progress_card_file = "/var/www/PROGRESO.txt"
        has_card = False
        if os.path.exists(progress_card_file):
            try:
                with open(progress_card_file, "r", encoding="utf-8") as pf:
                    p_content = pf.read().strip()
                if p_content:
                    print(p_content)
                    has_card = True
            except Exception:
                pass

        if not has_card:
            print(f" Fase:             {st.get('current_action') or 'Inactivo'}")
            print(f" Detalle:          {st.get('current_detail') or 'En espera'}")

        print("-" * 80)
        pending = st.get("pending_courses", [])
        if pending:
            print(f" ⏳ Próximos en cola ({len(pending)}):")
            for p in pending[:5]:
                print(f"    • {p}")
            if len(pending) > 5:
                print(f"    ... y {len(pending) - 5} más.")

        completed = st.get("completed_courses", [])
        if completed:
            print(f"\n ✅ Cursos Completados en esta sesión ({len(completed)}):")
            for c in completed:
                print(f"    ✓ {c}")

        print("=" * 80)
        if watch:
            print("📺 Monitoreo en vivo continuo cada 2s. Presioná Ctrl+C para salir.")
        else:
            print("💡 Ejecutá 'mcv-queue status -w' o 'mcv-status -w' para monitoreo continuo en vivo.")
            print("   Logs detallados: tail -f /var/www/localstorage/mcv_staging/mcv_queue.log")
        print("=" * 80 + "\n")

        if not watch:
            break
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n👋 Monitoreo en vivo detenido.")
            break


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = argparse.ArgumentParser(description="MCV Unattended Zero-Credit Queue Orchestrator")
    parser.add_argument("--dir", default="/var/www/baiosfera/CURSOS/MCV/AUTHOR/Lavin", help="Directorio objetivo a procesar")
    parser.add_argument("--start", action="store_true", help="Iniciar la cola en primer plano")
    parser.add_argument("--daemon", action="store_true", help="Iniciar en segundo plano (demonio desatendido)")
    parser.add_argument("--status", action="store_true", help="Mostrar estado de la cola")
    parser.add_argument("--stop", action="store_true", help="Detener cola activa")
    parser.add_argument("-w", "--watch", action="store_true", help="Monitorear continuamente en vivo")
    parser.add_argument("--audio-format", default="aac", choices=["aac", "mp3", "opus"])

    args = parser.parse_args()

    if args.status or args.watch:
        show_queue_status(watch=args.watch)
        sys.exit(0)

    if args.stop:
        if os.path.exists(QUEUE_PID_FILE):
            try:
                with open(QUEUE_PID_FILE, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                print(f"🛑 Señal de parada enviada al PID {pid}.")
                try:
                    os.remove(QUEUE_PID_FILE)
                except Exception:
                    pass
            except Exception as e:
                print(f"Error deteniendo proceso: {e}")
        else:
            print("ℹ️ No hay PID de cola activo registrado.")
        sys.exit(0)

    # Iniciar cola
    if os.path.exists(QUEUE_PID_FILE):
        try:
            with open(QUEUE_PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            if old_pid != os.getpid():
                os.kill(old_pid, 0)
                print(f"⚠️ Ya existe una cola ejecutándose activamente bajo PID {old_pid}.")
                print("   Para ver estado ejecutá: mcv-queue status")
                print("   Para detenerla ejecutá:  mcv-queue stop")
                sys.exit(1)
        except OSError:
            try:
                os.remove(QUEUE_PID_FILE)
            except Exception:
                pass

    if args.daemon:
        # Launch detached
        cmd = [
            sys.executable,
            os.path.abspath(__file__),
            "--start",
            "--dir", args.dir,
            "--audio-format", args.audio_format
        ]
        import subprocess
        log_out = open(QUEUE_LOG, "a", encoding="utf-8")
        proc = subprocess.Popen(
            cmd,
            stdout=log_out,
            stderr=log_out,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )
        print(f"\n🚀 Cola desatendida iniciada exitosamente en segundo plano (PID: {proc.pid}).")
        print(f"   Log de ejecución:  {QUEUE_LOG}")
        print("   Monitoreo en vivo: mcv-queue status -w\n")
        sys.exit(0)

    # Write current PID
    with open(QUEUE_PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    try:
        orchestrator = MCVQueueOrchestrator(args.dir, audio_format=args.audio_format)
        orchestrator.run()
    finally:
        if os.path.exists(QUEUE_PID_FILE):
            try:
                os.remove(QUEUE_PID_FILE)
            except Exception:
                pass


if __name__ == "__main__":
    main()
