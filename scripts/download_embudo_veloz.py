#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga quirúrgica y transcodificación atómica para 'Tu Embudo Veloz de Resultados Inmediatos en 7 Días' (1304).
Procesa módulo por módulo en orden lógico con purga inmediata del video crudo en NVMe.
"""
import os
import sys
import subprocess
import shutil
import glob
import re

sys.dont_write_bytecode = True
sys.path.insert(0, "/var/www/zerops-astrobranding/scripts")
from mega_downloader import Transcoder, Normalizer, log

URL = "https://mega.nz/folder/FoNCyC7a#k_8efBA-OCCJmw4z2fGgfA"
DEST_DIR = "/var/www/baiosfera/CURSOS/CA/3. CUA/1304_Tu_Embudo_Veloz_de_Resultados_Inmediatos"
BASE_STAGING = "/var/www/localstorage/mega_downloads/.staging/embudo_veloz"

MODULES = [
    {
        "id": "mod_01",
        "prefix": "MODULO-01",
        "name": "1. Bienvenida e Instrucciones (42 MB)",
        "items": [
            (3, 1, "Recorrido_por_Area_de_Miembros", False)
        ]
    },
    {
        "id": "mod_02_1",
        "prefix": "MODULO-02-1",
        "name": "2.1 Estrategia y Redaccion Publicitaria (197 MB)",
        "items": [
            (6, 1, "Textos_Landing_Page_o_Pagina_de_Captura", False),
            (7, 2, "Textos_Pagina_de_Gracias_o_Exito", False),
            (8, 3, "Textos_Paginas_Legales", False),
            (9, 4, "Textos_Correos_de_Seguimiento", False),
            (11, None, "Plantilla_Pagina_de_Gracias_Exito.pdf", True),
            (12, None, "Plantillas_Emails_Seguimiento.pdf", True),
            (13, None, "Plantillas_Landing_Page_Alta_Conversion.pdf", True),
            (14, None, "Politicas_de_Privacidad_EVRI.pdf", True),
            (15, None, "Terminos_y_Condiciones_EVRI.pdf", True)
        ]
    },
    {
        "id": "mod_02_2",
        "prefix": "MODULO-02-2",
        "name": "2.2 Ensamblaje 1 Landing Page (580 MB)",
        "items": [
            (17, 1, "Como_Crear_una_Pagina_de_Captura_en_BlastFunnels", False),
            (18, 2, "Como_Editar_una_Pagina_de_Captura_en_BlastFunnels", False),
            (19, 3, "Como_Crear_una_Pagina_de_Gracias_en_BlastFunnels", False),
            (20, 4, "Como_integrar_un_Dominio_Propio_al_Embudo", False),
            (21, 5, "Como_Crear_un_Correo_Corporativo_Gratis_Zoho_Parte_1", False),
            (22, 6, "Como_Crear_un_Correo_Corporativo_Gratis_Zoho_Parte_2", False)
        ]
    },
    {
        "id": "mod_02_3",
        "prefix": "MODULO-02-3",
        "name": "2.3 Ensamblaje 2 Email Marketing Automatizado (404 MB)",
        "items": [
            (24, 1, "Como_Crear_una_Automatizacion_de_Correos_en_BlastFunnels", False)
        ]
    },
    {
        "id": "mod_02_4",
        "prefix": "MODULO-02-4",
        "name": "2.4 Trafico con Google Ads (500 MB)",
        "items": [
            (26, 1, "Como_Funciona_Google_Ads", False),
            (28, 2, "Creando_la_Cuenta_de_Google_Ads", False),
            (29, 3, "Encontrando_Palabras_Clave", False),
            (30, 4, "Sobre_la_Concordancia_de_Palabras_Clave", False),
            (31, 5, "Creando_la_Conversion_en_Google_Ads_para_Medir", False),
            (32, 6, "Esquematizando_la_Conversion_de_Google_Ads_para_Medir", False),
            (33, 7, "Creando_una_Campana_de_Busqueda_en_Google_Ads", False),
            (34, 8, "Agregando_la_Conversion_al_Embudo", False),
            (35, 9, "Metricas_Importantes_en_Google_Ads", False),
            (27, 10, "Acceso_a_Plantillas", False),
            (36, None, "Google_Ads.xlsx", True),
            (37, None, "Palabras_Clave_Negativas.xlsx", True)
        ]
    }
]

def is_item_done(prefix, cls_num, title, is_doc):
    if is_doc:
        doc_path = os.path.join(DEST_DIR, f"DOC_{title}")
        return os.path.exists(doc_path) and os.path.getsize(doc_path) > 1024
    pattern = os.path.join(DEST_DIR, f"{prefix}_CLASE-{cls_num:02d}_*.m4a")
    matches = glob.glob(pattern)
    return len(matches) > 0 and any(os.path.getsize(m) > 1024 for m in matches)

def download_item(idx, staging_dir):
    shutil.rmtree(staging_dir, ignore_errors=True)
    os.makedirs(staging_dir, exist_ok=True)
    
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
    
    for line in iter(proc.stdout.readline, ''):
        if "Enter numbers" in line:
            proc.stdin.write(f"{idx}\n")
            proc.stdin.flush()
            break
            
    for line in iter(proc.stdout.readline, ''):
        line_clean = line.strip()
        if "403" in line_clean or "Over Quota" in line_clean:
            log(f"🚨 ALERTA: MEGA Cuota de transferencia agotada (403 Over Quota) en índice {idx}", "WARN")
            quota_exceeded = True
            proc.kill()
            break
        elif line_clean.startswith("F "):
            print(f"[EVRI] Descargando: {os.path.basename(line_clean)}", flush=True)
        elif "of" in line_clean and ("50." in line_clean or "99." in line_clean or "100%" in line_clean):
            print(f"[EVRI] Progreso: {line_clean}", flush=True)
            
    proc.wait()
    return not quota_exceeded

def process_item(staging_dir, prefix, cls_num, title, is_doc):
    downloaded = []
    for root, _, files in os.walk(staging_dir):
        for f in files:
            downloaded.append(os.path.join(root, f))
            
    if not downloaded:
        log("No se encontró ningún archivo descargado en staging.", "WARN")
        return False
        
    src_file = downloaded[0]
    
    if is_doc:
        out_doc = os.path.join(DEST_DIR, f"DOC_{title}")
        shutil.copy2(src_file, out_doc)
        log(f"📄 Documento preservado en Drive: DOC_{title}", "INFO")
        shutil.rmtree(staging_dir, ignore_errors=True)
        return True
    else:
        out_name = f"{prefix}_CLASE-{cls_num:02d}_{title}.m4a"
        out_path = os.path.join(DEST_DIR, out_name)
        log(f"🎧 Transcodificando a M4A Speech: {out_name}", "AUDIO")
        success = Transcoder.extract_m4a_speech(src_file, out_path)
        shutil.rmtree(staging_dir, ignore_errors=True)
        if success:
            log(f"✅ Audio promovido exitosamente a Drive: {out_name}", "INFO")
            return True
        else:
            log(f"❌ Error al transcodificar: {out_name}", "ERROR")
            return False

def run():
    log("============================================================", "INFO")
    log("Iniciando descarga y procesamiento de '1304 Tu Embudo Veloz' (Módulos Core)", "ACTION")
    os.makedirs(DEST_DIR, exist_ok=True)
    
    total_audios = 0
    total_docs = 0
    
    for mod in MODULES:
        mod_name = mod["name"]
        prefix = mod["prefix"]
        staging_dir = os.path.join(BASE_STAGING, mod["id"])
        
        log(f"--- Procesando {mod_name} ---", "ACTION")
        
        for idx, cls_num, title, is_doc in mod["items"]:
            if is_item_done(prefix, cls_num, title, is_doc):
                label = title if is_doc else f"Clase {cls_num:02d} ({title})"
                print(f"[EVRI SKIP] Ya existe en Drive: {label}")
                continue
                
            label = title if is_doc else f"Clase {cls_num:02d} ({title})"
            log(f"Descargando [{idx}] {label}...", "ACTION")
            
            ok = download_item(idx, staging_dir)
            if not ok:
                log(f"Límite de cuota alcanzado en [{idx}]. Deteniendo proceso.", "WARN")
                shutil.rmtree(staging_dir, ignore_errors=True)
                sys.exit(42)
                
            proc_ok = process_item(staging_dir, prefix, cls_num, title, is_doc)
            if proc_ok:
                if is_doc:
                    total_docs += 1
                else:
                    total_audios += 1
                    
    log(f"🏁 Tanda de Embudo Veloz completada: {total_audios} audios, {total_docs} documentos en Drive.", "INFO")
    sys.exit(0)

if __name__ == "__main__":
    run()
