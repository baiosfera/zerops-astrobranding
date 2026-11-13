#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga selectiva y transcodificación atómica para completar el Módulo 3
(Taller Código Simbólico) de Jürgen Klarić sin desperdiciar cuota de MEGA.
"""
import os
import sys
import subprocess
import shutil

sys.dont_write_bytecode = True
sys.path.insert(0, "/var/www/zerops-astrobranding/scripts")
from mega_downloader import CourseProcessor, log

def run():
    staging_dir = "/var/www/localstorage/mega_downloads/.staging/jurgen_m3_rest"
    dest_dir = "/var/www/baiosfera/CURSOS/CA/3. CUA/1227_Master_Training_Neuro_Ventas_3_0_Jurgen_Klaric"
    url = "https://mega.nz/folder/p81yxTKb#mUYY6gjAlXkhMS2OnMi1jA"
    
    # 6 archivos pendientes del Módulo 3:
    # 122: 10.Webinar en Vivo (319 MiB)
    # 126: 5. Las Improntas (1.3 GiB)
    # 127: 6.Implementación del Código Simbólico (830 MiB)
    # 128: 7. Ejercición de la implementación (638 MiB)
    # 129: 8.Discurso de ventas táctico (937 MiB)
    # 130: 9.La ética del Código Simbólico (388 MiB)
    indices_str = "122 126 127 128 129 130\n"
    
    os.makedirs(staging_dir, exist_ok=True)
    os.makedirs(dest_dir, exist_ok=True)
    
    cmd = [
        "megatools", "dl",
        "--choose-files",
        "--no-ask-password",
        "--path", staging_dir,
        url
    ]
    
    log("Iniciando megatools dl con selección específica (Módulo 3 restante)...", "ACTION")
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Esperar al prompt de selección
    for line in iter(proc.stdout.readline, ''):
        if "Enter numbers" in line:
            log("Enviando selección de índices: 122 126 127 128 129 130", "INFO")
            proc.stdin.write(indices_str)
            proc.stdin.flush()
            break
            
    # Mostrar progreso de descarga
    for line in iter(proc.stdout.readline, ''):
        line_clean = line.strip()
        if "of" in line_clean and "%" in line_clean:
            # Imprimir solo progresos significativos
            if "0.00%" in line_clean or "50." in line_clean or "99." in line_clean or "100%" in line_clean:
                print(f"[MEGA] {line_clean}", flush=True)
        elif line_clean.startswith("F "):
            print(f"[MEGA] Descargando: {os.path.basename(line_clean)}", flush=True)
        elif "WARNING" in line_clean or "ERROR" in line_clean:
            print(f"[MEGA ALERT] {line_clean}", flush=True)
            
    proc.wait()
    log(f"megatools completado con código de salida: {proc.returncode}", "INFO")
    
    if proc.returncode != 0:
        log("Fallo o advertencia durante la descarga en megatools", "WARN")
        
    # Verificar archivos descargados en staging y procesarlos
    log("Iniciando CourseProcessor para transcodificación y preservación...", "ACTION")
    processor = CourseProcessor(
        course_title="1227 Master Training Neuro Ventas 3.0 - Jurgen Klaric (Modulo 3)",
        staging_dir=staging_dir,
        gdrive_dest=dest_dir,
        flat=True
    )
    result = processor.process()
    log(f"✅ Procesamiento completado: {result}", "INFO")

if __name__ == "__main__":
    run()
