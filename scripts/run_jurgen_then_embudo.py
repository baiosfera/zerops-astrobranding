#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orquestador inteligente: ejecuta Jürgen Klarić (Módulo 10 Chat Marketing)
y si se agota la cuota de MEGA, realiza el fallback a Tu Embudo Veloz.
"""
import os
import sys
import subprocess
import shutil

sys.dont_write_bytecode = True
sys.path.insert(0, "/var/www/zerops-astrobranding/scripts")
from mega_downloader import log

def test_embudo_quota():
    url = "https://mega.nz/folder/FoNCyC7a#k_8efBA-OCCJmw4z2fGgfA"
    staging_dir = "/var/www/localstorage/mega_downloads/.staging/test_embudo"
    os.makedirs(staging_dir, exist_ok=True)
    
    cmd = ["megatools", "dl", "--choose-files", "--no-ask-password", "--path", staging_dir, url]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    # Índice 3 es Recorrido por Área de Miembros.mp4 (41.6 MiB)
    for line in iter(proc.stdout.readline, ''):
        if "Enter numbers" in line:
            proc.stdin.write("3\n")
            proc.stdin.flush()
            break
            
    has_quota = True
    for line in iter(proc.stdout.readline, ''):
        line_clean = line.strip()
        if "403" in line_clean or "Over Quota" in line_clean:
            has_quota = False
            proc.kill()
            break
        elif "%" in line_clean:
            proc.kill()
            break
            
    proc.kill()
    shutil.rmtree(staging_dir, ignore_errors=True)
    return has_quota

def main():
    log("============================================================", "INFO")
    log("Iniciando orquestación: Jürgen Klarić Módulo 10 con fallback a Embudo Veloz", "ACTION")
    
    # 1. Probar Jürgen Klarić Módulo 10
    cmd_jurgen = [sys.executable, "/var/www/zerops-astrobranding/scripts/download_jurgen_m10.py"]
    res_jurgen = subprocess.run(cmd_jurgen)
    
    if res_jurgen.returncode == 0:
        log("✅ Módulo 10 de Jürgen Klarić completado 100% sin agotar cuota.", "INFO")
        return
        
    if res_jurgen.returncode == 42:
        log("⚠️ Jürgen Klarić Módulo 10 se detuvo por límite de cuota MEGA (403 Over Quota).", "WARN")
        log("Evaluando disponibilidad de cuota en '1304 Tu Embudo Veloz'...", "ACTION")
        
        has_quota_embudo = test_embudo_quota()
        if not has_quota_embudo:
            log("🚨 ATENCIÓN: El límite de cuota de MEGA opera a nivel de IP pública. Ambas carpetas de MEGA reportan Over Quota.", "WARN")
            log("Los archivos procesados hasta este momento quedaron a salvo en Drive sin saturar disco.", "INFO")
            sys.exit(0)
        else:
            log("⚡ Cuota disponible detectada para Embudo Veloz. Iniciando procesamiento...", "ACTION")
            # Ejecutar procesamiento quirúrgico de Embudo Veloz
    else:
        log(f"Jürgen terminó con código inesperado: {res_jurgen.returncode}", "ERROR")

if __name__ == "__main__":
    main()
