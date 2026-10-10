#!/usr/bin/env python3
"""
Pipeline de Depuración, Higiene de Datos y Validación DNS MX para Leads de Bogotá
Proyecto: El Placer de Compartir / The Corset Society
Entrada: /var/www/baiosfera/PROYECTOS/ELPLACERDC/leads/DBMails/Todas_Bases_Bogota_limpieza1.xlsx
Salidas:
  - /var/www/baiosfera/PROYECTOS/ELPLACERDC/leads/DBMails/leads_bogota_limpios_listmonk.csv
  - /var/www/webprod/localstorage/ELPLACERDC/leads/leads_bogota_limpios_listmonk.csv
  - Lotes preparados: batch1_sonda_350.csv, batch2_decision_750.csv, batch3_caliente.csv
"""

import os
import re
import csv
import json
import io
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
import dns.resolver

# 1. Reglas y Mapeos de Corrección Tipográfica
DOMAIN_TYPOS = {
    'gmai.com': 'gmail.com', 'gamil.com': 'gmail.com', 'gmial.com': 'gmail.com',
    'gmaill.com': 'gmail.com', 'gmail.con': 'gmail.com', 'gmail.co': 'gmail.com',
    'gmeil.com': 'gmail.com', 'gemail.com': 'gmail.com', 'gmail.cpm': 'gmail.com',
    'hotmial.com': 'hotmail.com', 'hotmai.com': 'hotmail.com', 'hotmaill.com': 'hotmail.com',
    'homail.com': 'hotmail.com', 'jotmail.com': 'hotmail.com', 'hotmail.con': 'hotmail.com',
    'hotmail.cpm': 'hotmail.com', 'hotmial.es': 'hotmail.es', 'hotmai.es': 'hotmail.es',
    'outlok.com': 'outlook.com', 'outloo.com': 'outlook.com', 'outllok.com': 'outlook.com',
    'outloock.com': 'outlook.com', 'outlok.es': 'outlook.es',
    'yaho.com': 'yahoo.com', 'yahooo.com': 'yahoo.com', 'yaho.es': 'yahoo.es',
    'yahoo.con': 'yahoo.com', 'iclud.com': 'icloud.com'
}

DISPOSABLE_DOMAINS = {
    'mailinator.com', 'yopmail.com', 'tempmail.com', '10minutemail.com',
    'guerrillamail.com', 'trashmail.com', 'throwawaymail.com', 'sharklasers.com',
    'getairmail.com', 'dispostable.com'
}

DEAD_DOMAINS = {
    'misena.edu.co', 'colombianenergyservices.com', 'hotmail.comisr', 'excite.com',
    'somosswinger.xyz', 'ingenieros.com', 'yahho.com.ar', 'sexcoaching.co',
    'em2.com.co', 'latinmail.com'
}

# Correos dados de baja en campañas previas (Supresión Permanente)
SUPPRESSED_EMAILS = {
    'federico951123@gmail.com',
    'bettobassdc@gmail.com',
    'juanm.narvaezv@gmail.com',
    'jbeltranpinto@gmail.com',
    'fnietoelgazi@gmail.com',
    'pachosva@gmail.com',
    'adrianalorena88@gmail.com',
    'geramonc@gmail.com',
    'alejandro26iker@gmail.com'
}

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

# 2. Funciones de Normalización de Texto y Nombres
def title_case_es(text: str) -> str:
    if not text:
        return ""
    words = text.strip().split()
    lowers = {'de', 'del', 'la', 'las', 'los', 'y', 'e', 'en', 'el', 'san', 'santa'}
    formatted = []
    for i, w in enumerate(words):
        w_low = w.lower()
        if i > 0 and w_low in lowers:
            formatted.append(w_low)
        else:
            formatted.append(w_low.capitalize())
    return " ".join(formatted)

def parse_and_clean_name(raw_name: str, sexo: str = "", yo_soy: str = ""):
    if not raw_name or raw_name.strip() in ['-', '.', 'N/A', 'n/a', 'Sin Nombre', 'sin nombre']:
        return "Invitado(a)", "Invitado(a)", False

    clean = raw_name.strip()
    separators = [',', ' y ', ' Y ', ' - ', ' / ', '/', ' & ', ' + ']
    p1, p2 = None, None

    for sep in separators:
        if sep in clean:
            parts = [p.strip() for p in clean.split(sep) if p.strip()]
            if len(parts) >= 2 and len(parts[0]) >= 2 and len(parts[1]) >= 2:
                p1 = parts[0]
                p2 = parts[1]
                break

    if p1 and p2:
        p1_clean = title_case_es(p1)
        p2_clean = title_case_es(p2)
        full_name = f"{p1_clean} y {p2_clean}"
        salutation = f"{p1_clean.split()[0]} y {p2_clean.split()[0]}"
        return full_name, salutation, True

    # Single name
    full_name = title_case_es(clean)
    salutation = full_name.split()[0] if full_name else "Invitado(a)"
    is_couple = "pareja" in sexo.lower() or "pareja" in yo_soy.lower()
    return full_name, salutation, is_couple

# 3. Validación DNS MX
KNOWN_VALID_DOMAINS = {
    'gmail.com', 'hotmail.com', 'hotmail.es', 'outlook.com', 'outlook.es',
    'yahoo.com', 'yahoo.es', 'yahoo.com.co', 'live.com', 'icloud.com',
    'yahoo.com.mx', 'yahoo.com.ar', 'yahoo.it', 'yahoo.de', 'yahoo.co.uk',
    'hotmail.com.ar', 'outlook.com.ar', 'me.com', 'mac.com'
}

mx_cache = {}

def check_domain_mx(domain: str) -> bool:
    if domain in KNOWN_VALID_DOMAINS:
        return True
    if domain in mx_cache:
        return mx_cache[domain]

    resolver = dns.resolver.Resolver()
    resolver.timeout = 2.5
    resolver.lifetime = 2.5
    try:
        answers = resolver.resolve(domain, 'MX')
        if len(answers) > 0:
            mx_cache[domain] = True
            return True
    except Exception:
        pass

    # Fallback to A record
    try:
        answers_a = resolver.resolve(domain, 'A')
        if len(answers_a) > 0:
            mx_cache[domain] = True
            return True
    except Exception:
        pass

    mx_cache[domain] = False
    return False

# 4. Procesamiento Principal
def process_excel(input_path: str):
    print(f"📖 Leyendo base original desde: {input_path}")
    with open(input_path, 'rb') as f:
        buf = io.BytesIO(f.read())

    z = zipfile.ZipFile(buf)
    shared_strings = []
    if 'xl/sharedStrings.xml' in z.namelist():
        tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in tree.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
            text = ''.join(t.text for t in si.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t') if t.text)
            shared_strings.append(text)

    sheet_tree = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    rows = sheet_tree.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheetData/{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')

    print(f"Total filas encontradas: {len(rows)}")

    stats = {
        'total_rows': len(rows) - 1,
        'syntax_errors': 0,
        'typos_corrected': 0,
        'disposable_dropped': 0,
        'dead_domains_dropped': 0,
        'no_mx_dropped': 0,
        'duplicates_merged': 0,
        'couples_detected': 0,
        'singles_detected': 0,
        'final_clean': 0
    }

    records_by_email = {}

    for r in rows[1:]:
        vals = {}
        for c in r.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
            ref = c.get('r')
            col = ''.join([ch for ch in ref if ch.isalpha()])
            v = c.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
            val = v.text if v is not None else ''
            t = c.get('t')
            if t == 's' and val.isdigit() and int(val) < len(shared_strings):
                val = shared_strings[int(val)]
            vals[col] = val

        raw_email = vals.get('A', '').strip()
        raw_name = vals.get('B', '').strip()
        ciudad = vals.get('C', 'Bogotá').strip() or 'Bogotá'
        sexo = vals.get('D', '').strip()
        yo_soy = vals.get('E', '').strip()

        if not raw_email or '@' not in raw_email:
            stats['syntax_errors'] += 1
            continue

        local_p, domain_p = raw_email.split('@', 1)
        domain_p = domain_p.lower().strip()
        local_p = local_p.strip()

        # Corrección de typos
        if domain_p in DOMAIN_TYPOS:
            domain_p = DOMAIN_TYPOS[domain_p]
            stats['typos_corrected'] += 1

        email_clean = f"{local_p}@{domain_p}".lower()

        # Descarte de desuscripciones previas (Supresión Permanente)
        if email_clean in SUPPRESSED_EMAILS:
            continue

        # Validación regex RFC 5322
        if not EMAIL_REGEX.match(email_clean):
            stats['syntax_errors'] += 1
            continue

        # Descarte de desechables
        if domain_p in DISPOSABLE_DOMAINS:
            stats['disposable_dropped'] += 1
            continue

        # Descarte de dominios muertos conocidos
        if domain_p in DEAD_DOMAINS:
            stats['dead_domains_dropped'] += 1
            continue

        # Validación DNS MX
        if not check_domain_mx(domain_p):
            stats['no_mx_dropped'] += 1
            continue

        # Normalización de nombre
        full_name, salutation, is_couple = parse_and_clean_name(raw_name, sexo, yo_soy)

        if is_couple:
            stats['couples_detected'] += 1
        else:
            stats['singles_detected'] += 1

        attribs = {
            "ciudad": ciudad,
            "sexo": sexo,
            "yo_soy": yo_soy,
            "saludo": salutation,
            "es_pareja": is_couple
        }

        if email_clean in records_by_email:
            stats['duplicates_merged'] += 1
            # Preservar el más completo
            existing = records_by_email[email_clean]
            if existing['name'] in ['Invitado(a)', ''] and full_name != 'Invitado(a)':
                existing['name'] = full_name
                existing['attribs'] = attribs
            continue

        records_by_email[email_clean] = {
            'email': email_clean,
            'name': full_name,
            'attribs': attribs
        }

    clean_list = list(records_by_email.values())
    stats['final_clean'] = len(clean_list)

    return clean_list, stats

def export_clean_data(clean_list, stats):
    # Destinos principales
    out_drive = '/var/www/baiosfera/PROYECTOS/ELPLACERDC/leads/DBMails/leads_bogota_limpios_listmonk.csv'
    out_local_dir = '/var/www/webprod/localstorage/ELPLACERDC/leads'
    os.makedirs(out_local_dir, exist_ok=True)
    out_local = os.path.join(out_local_dir, 'leads_bogota_limpios_listmonk.csv')

    for target_path in [out_drive, out_local]:
        try:
            with open(target_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['email', 'name', 'attributes'])
                for rec in clean_list:
                    writer.writerow([rec['email'], rec['name'], json.dumps(rec['attribs'], ensure_ascii=False)])
            print(f"✓ Archivo consolidado guardado en: {target_path}")
        except Exception as e:
            print(f"⚠️ Error escribiendo en {target_path}: {e}")

    # Exportar también los 3 lotes preparados (para cuando se decida disparar)
    b1 = clean_list[:350]
    b2 = clean_list[350:1100]
    b3 = clean_list[1100:]

    batches = [
        ('batch1_sonda_350.csv', b1),
        ('batch2_decision_750.csv', b2),
        ('batch3_caliente_remate.csv', b3)
    ]

    for fname, data_batch in batches:
        b_path = os.path.join(out_local_dir, fname)
        with open(b_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['email', 'name', 'attributes'])
            for rec in data_batch:
                writer.writerow([rec['email'], rec['name'], json.dumps(rec['attribs'], ensure_ascii=False)])
        print(f"✓ Lote preparado ({len(data_batch)} contactos): {b_path}")

    # Guardar reporte JSON
    report_path = os.path.join(out_local_dir, 'reporte_limpieza_bogota.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"✓ Reporte de auditoría guardado en: {report_path}")

if __name__ == '__main__':
    input_xlsx = '/var/www/baiosfera/PROYECTOS/ELPLACERDC/leads/DBMails/Todas_Bases_Bogota_limpieza1.xlsx'
    clean_records, stats = process_excel(input_xlsx)
    export_clean_data(clean_records, stats)

    print("\n" + "="*50)
    print("📊 REPORTE FINAL DE HIGIENE Y DEPURACIÓN")
    print("="*50)
    for k, v in stats.items():
        print(f"  • {k}: {v}")
    print("="*50)
