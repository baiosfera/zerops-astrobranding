#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga quirúrgica y transcodificación atómica para el Módulo 10
(Neuroventas para Chat Marketing, 44 archivos) de Jürgen Klarić.
Procesa sesión por sesión con purga inmediata del video en NVMe.
Detecta 403 Over Quota para fallback limpio.
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

URL = "https://mega.nz/folder/p81yxTKb#mUYY6gjAlXkhMS2OnMi1jA"
DEST_DIR = "/var/www/baiosfera/CURSOS/CA/3. CUA/1227_Master_Training_Neuro_Ventas_3_0_Jurgen_Klaric"
STAGING_DIR = "/var/www/localstorage/mega_downloads/.staging/jurgen_m10"

# Mapeo exacto de los 44 archivos de Módulo 10: (índice_mega, clase_num, título_limpio, es_doc)
ITEMS = [
    (25, 1, "Intro_JK_2020", False),
    (47, 2, "Recomendaciones_JK", False),
    (69, 3, "Modulo_1", False),
    (82, 4, "Modulo_2", False),
    (84, 5, "Modulo_3", False),
    (86, 6, "Final_Modulo_3", False),
    (88, 7, "Modulo_4", False),
    (90, 8, "Modulo_5", False),
    (92, 9, "Modulo_6", False),
    (27, 10, "Webinar_Funnel_de_Ventas_por_WhatsApp_en_3_pasos_Felipe_Fandino", False),
    (29, 11, "1er_webinar_de_seguimiento_con_Jurgen_Klaric", False),
    (31, 12, "2do_webinar_de_seguimiento_con_Jurgen_Klaric", False),
    (33, 13, "Modulo_7_Mensajeria_Instantanea", False),
    (35, 14, "Estrategia_de_etiquetas_listas_y_contactos", False),
    (37, 15, "1er_Webinar_Estrategias_con_Josue", False),
    (39, 16, "Contenido_extra_Ideas_para_Etiquetas", False),
    (41, 17, "Como_llevar_trafico", False),
    (43, 18, "Que_necesito_para_llevar_mas_trafico_Parte_1", False),
    (45, 19, "Que_necesito_para_llevar_mas_trafico_Parte_2", False),
    (49, 20, "Integrar_instagram_Facebook_y_WhatsApp", False),
    (51, 21, "Estrategias_de_adquisicion", False),
    (53, 22, "Flujo_y_Estrategias_de_Generacion", False),
    (55, 23, "Practica_de_Generacion_de_trafico", False),
    (57, 24, "Avatares", False),
    (59, 25, "Webinar_con_Josue_Teoria_de_la_Estrategia_de_trafico", False),
    (61, 26, "Webinar_con_Josue_Practica_de_la_Estrategia_de_trafico", False),
    (63, 27, "Webinar_con_Josue_Hablemos_de_Trafico", False),
    (65, 28, "Webinar_de_WhatsON", False),
    (67, 29, "Como_adquirir_la_licencia_de_WhatsON", False),
    (71, 30, "Webinar_de_HiWhaBot", False),
    (73, 31, "Aclaremos_todas_tus_dudas_sobre_HiWaBot", False),
    (75, 32, "Webinar_Aclaremos_todas_tus_dudas_sobre_WhatsOn_y_HiWaBot", False),
    (77, 33, "1er_webinar_de_seguimiento_con_Jurgen_Klaric_Sesion_33", False),
    (78, 34, "2do_webinar_de_seguimiento_con_Jurgen_Klaric_Sesion_33", False),
    (79, 35, "Promo_Sesion_33", False),
    (80, None, "Workbook_Chat_Marketing_Sesion_33.pdf", True),
    (16, 36, "Marketing_de_Afiliados_Jurgen_Klaric", False),
    (17, 37, "Marketing_Afiliados_Josue_Moya_de_la_Cruz", False),
    (18, 38, "Cual_debe_ser_mi_vision_en_el_marketing_de_afiliados", False),
    (19, 39, "El_poder_del_Marketing_de_Afiliados", False),
    (20, 40, "Hablemos_de_Manychat", False),
    (21, 41, "2do_Webinar_de_Marketing_de_Afiliado_con_Josue_Moya_de_la_cruz", False),
    (22, 42, "Caso_de_estudio_La_Formula_de_lanzamiento", False),
    (23, None, "Afiliando.pdf", True)
]

def is_item_done(cls_num, title, is_doc):
    if is_doc:
        doc_path = os.path.join(DEST_DIR, f"DOC_{title}")
        return os.path.exists(doc_path) and os.path.getsize(doc_path) > 1024
    pattern = os.path.join(DEST_DIR, f"MODULO-10_CLASE-{cls_num:02d}_*.m4a")
    matches = glob.glob(pattern)
    return len(matches) > 0 and any(os.path.getsize(m) > 1024 for m in matches)

def download_item(idx):
    shutil.rmtree(STAGING_DIR, ignore_errors=True)
    os.makedirs(STAGING_DIR, exist_ok=True)
    
    cmd = [
        "megatools", "dl",
        "--choose-files",
        "--no-ask-password",
        "--path", STAGING_DIR,
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
            print(f"[M10] Descargando: {os.path.basename(line_clean)}", flush=True)
        elif "of" in line_clean and ("50." in line_clean or "99." in line_clean or "100%" in line_clean):
            print(f"[M10] Progreso: {line_clean}", flush=True)
            
    proc.wait()
    return not quota_exceeded

def process_downloaded_item(cls_num, title, is_doc):
    # Encontrar el archivo descargado en STAGING_DIR
    downloaded_files = []
    for root, _, files in os.walk(STAGING_DIR):
        for f in files:
            downloaded_files.append(os.path.join(root, f))
            
    if not downloaded_files:
        log("No se encontró ningún archivo descargado en staging.", "WARN")
        return False
        
    src_file = downloaded_files[0]
    
    if is_doc:
        out_doc = os.path.join(DEST_DIR, f"DOC_{title}")
        shutil.copy2(src_file, out_doc)
        log(f"📄 Documento preservado en Drive: DOC_{title}", "INFO")
        shutil.rmtree(STAGING_DIR, ignore_errors=True)
        return True
    else:
        out_name = f"MODULO-10_CLASE-{cls_num:02d}_{title}.m4a"
        out_path = os.path.join(DEST_DIR, out_name)
        log(f"🎧 Transcodificando a M4A Speech: {out_name}", "AUDIO")
        success = Transcoder.extract_m4a_speech(src_file, out_path)
        # Purga inmediata del video en NVMe
        shutil.rmtree(STAGING_DIR, ignore_errors=True)
        if success:
            log(f"✅ Audio promovido exitosamente a Drive: {out_name}", "INFO")
            return True
        else:
            log(f"❌ Error al transcodificar audio: {out_name}", "ERROR")
            return False

def run():
    log("============================================================", "INFO")
    log("Iniciando procesamiento secuencial del Módulo 10 de Jürgen Klarić...", "ACTION")
    os.makedirs(DEST_DIR, exist_ok=True)
    
    completed_this_run = 0
    
    for idx, cls_num, title, is_doc in ITEMS:
        if is_item_done(cls_num, title, is_doc):
            label = title if is_doc else f"Clase {cls_num:02d} ({title})"
            print(f"[M10 SKIP] Ya existe en Drive: {label}")
            continue
            
        label = title if is_doc else f"Clase {cls_num:02d} ({title})"
        log(f"Procesando [{idx}] {label}...", "ACTION")
        
        success = download_item(idx)
        if not success:
            log(f"Deteniendo Módulo 10 debido a límite de cuota MEGA en [{idx}].", "WARN")
            shutil.rmtree(STAGING_DIR, ignore_errors=True)
            sys.exit(42) # Código 42: Quota Exceeded
            
        proc_ok = process_downloaded_item(cls_num, title, is_doc)
        if proc_ok:
            completed_this_run += 1
            
    log(f"🏁 Módulo 10 de Jürgen Klarić completado exitosamente: {completed_this_run} nuevos archivos.", "INFO")
    sys.exit(0)

if __name__ == "__main__":
    run()
