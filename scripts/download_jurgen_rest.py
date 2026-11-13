#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga quirúrgica y transcodificación atómica para los módulos restantes de Jürgen Klarić:
Módulos secundarios y en vivo: 8, 11, 13, 12, 6, 5, 14, 9, 7 (~4.3 GB total bruto).
Orden Shortest-Job-First con purga inmediata en caliente de cada video mp4.
"""
import os
import sys
import subprocess
import shutil
import time

sys.dont_write_bytecode = True
sys.path.insert(0, "/var/www/zerops-astrobranding/scripts")
from mega_downloader import CourseProcessor, log

URL = "https://mega.nz/folder/p81yxTKb#mUYY6gjAlXkhMS2OnMi1jA"
DEST_DIR = "/var/www/baiosfera/CURSOS/CA/3. CUA/1227_Master_Training_Neuro_Ventas_3_0_Jurgen_Klaric"
BASE_STAGING = "/var/www/localstorage/mega_downloads/.staging"

MODULES = [
    {
        "id": "m08",
        "num": 8,
        "name": "Módulo 8 - Los Mejores Descubrimientos (56 MB)",
        "indices": [197],
        "expected_audios": 1
    },
    {
        "id": "m11",
        "num": 11,
        "name": "Módulo 11 - Fuentes Claves de Energía Vital (70 MB)",
        "indices": [94],
        "expected_audios": 1
    },
    {
        "id": "m13",
        "num": 13,
        "name": "Módulo 13 - Real State (119 MB)",
        "indices": [99],
        "expected_audios": 1
    },
    {
        "id": "m12",
        "num": 12,
        "name": "Módulo 12 - Aplicaciones de las Neuroventas (195 MB)",
        "indices": [96, 97],
        "expected_audios": 2
    },
    {
        "id": "m06",
        "num": 6,
        "name": "Módulo 6 - Bono Prospección (538 MB)",
        "indices": [178],
        "expected_audios": 1
    },
    {
        "id": "m05",
        "num": 5,
        "name": "Módulo 5 - Masterclass Presupuesto (718 MB)",
        "indices": [173, 174, 175, 176],
        "expected_audios": 2
    },
    {
        "id": "m14",
        "num": 14,
        "name": "Módulo 14 - Aprende a estructurar tu negocio Marco Lezama (718 MB)",
        "indices": [101, 102],
        "expected_audios": 2
    },
    {
        "id": "m09",
        "num": 9,
        "name": "Módulo 9 - Herramientas Tecnológicas Neuroventas (886 MB)",
        "indices": [199, 200],
        "expected_audios": 2
    },
    {
        "id": "m07",
        "num": 7,
        "name": "Módulo 7 - Los Modelos de Neuroventas (1.1 GB)",
        "indices": [180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195],
        "expected_audios": 16
    }
]

def check_module_already_done(mod):
    if not os.path.exists(DEST_DIR):
        return False
    prefix = f"MODULO-{mod['num']:02d}_"
    existing = [f for f in os.listdir(DEST_DIR) if f.startswith(prefix) and f.endswith(".m4a")]
    return len(existing) >= mod["expected_audios"]

def download_and_process_module(mod):
    mod_id = mod["id"]
    mod_name = mod["name"]
    indices = mod["indices"]
    indices_str = " ".join(str(idx) for idx in indices) + "\n"
    staging_dir = os.path.join(BASE_STAGING, f"jurgen_{mod_id}")
    
    if check_module_already_done(mod):
        log(f"⚡ Módulo ya completo en Drive: {mod_name}. Omitiendo descarga.", "INFO")
        return True
        
    log(f"============================================================", "INFO")
    log(f"Iniciando {mod_name} (Índices: {indices})", "ACTION")
    log(f"Staging: {staging_dir}", "INFO")
    
    os.makedirs(staging_dir, exist_ok=True)
    os.makedirs(DEST_DIR, exist_ok=True)
    
    cmd = [
        "megatools", "dl",
        "--choose-files",
        "--no-ask-password",
        "--path", staging_dir,
        URL
    ]
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    quota_exceeded = False
    
    # Manejar prompt interactivo
    for line in iter(proc.stdout.readline, ''):
        if "Enter numbers" in line:
            log(f"Enviando selección a megatools: {indices_str.strip()}", "INFO")
            proc.stdin.write(indices_str)
            proc.stdin.flush()
            break
            
    # Leer progreso
    for line in iter(proc.stdout.readline, ''):
        line_clean = line.strip()
        if "403" in line_clean or "Over Quota" in line_clean:
            log(f"🚨 ALERTA: MEGA Cuota de transferencia agotada (403 Over Quota) en {mod_name}", "WARN")
            quota_exceeded = True
            proc.kill()
            break
        elif "of" in line_clean and "%" in line_clean:
            if "0.00%" in line_clean or "50." in line_clean or "99." in line_clean or "100%" in line_clean:
                print(f"[{mod_id.upper()}] {line_clean}", flush=True)
        elif line_clean.startswith("F "):
            print(f"[{mod_id.upper()}] Descargando: {os.path.basename(line_clean)}", flush=True)
        elif "WARNING" in line_clean or "ERROR" in line_clean:
            print(f"[{mod_id.upper()} ALERT] {line_clean}", flush=True)
            
    proc.wait()
    
    if quota_exceeded:
        log(f"Interrumpido por cuota en {mod_name}. Procesando lo que haya alcanzado a bajar...", "WARN")
        
    # Procesar archivos descargados (si los hay)
    processor = CourseProcessor(
        course_title=f"1227 Master Training Neuro Ventas 3.0 - Jurgen Klaric ({mod_name})",
        staging_dir=staging_dir,
        gdrive_dest=DEST_DIR,
        flat=True
    )
    result = processor.process()
    log(f"Resultado {mod_name}: {result}", "INFO")
    
    # Asegurar que el staging quede limpio
    shutil.rmtree(staging_dir, ignore_errors=True)
    return not quota_exceeded

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    for mod in MODULES:
        if target != "all" and mod["id"] != target:
            continue
            
        success = download_and_process_module(mod)
        if not success:
            log("Deteniendo la ejecución de módulos siguientes debido a cuota MEGA.", "WARN")
            sys.exit(2)
            
    log("🏁 Procesamiento de módulos secundarios finalizado.", "INFO")

if __name__ == "__main__":
    main()
