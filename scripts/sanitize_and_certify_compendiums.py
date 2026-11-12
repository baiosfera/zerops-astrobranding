#!/usr/bin/env python3
"""
==============================================================================
sanitize_and_certify_compendiums.py
Surgical Sanitizer, Re-Chunker and SOTA Certification Sensor (EXIT 0 GATE)
Governance: Supreme Directive v8.5 | BAI-456 Verification
==============================================================================
"""

import os
import sys
import re
from pathlib import Path

BASE_DIR = "/var/www/localstorage/knowledge_cache/compendiums"
MIRROR_DIR = "/var/www/baiosfera/PLAYBOOKS/0compendiums"

EXCLUDED_PATTERNS = [
    "00-incompletos", "01-desarrollo-personal", "biodecodificacion",
    "coaching-inteligencia-emocional", "fenix-reinvencion",
    "formula-aceleradora", "dain-heer", "paralelo-de-embrio",
    "vision-aural", "lain-garcia-calvo", "lavin", "agy", "start-here"
]

def purge_excluded_courses():
    """Elimina compendios correspondientes a cursos no comerciales/esotéricos."""
    files = list(Path(BASE_DIR).glob("*/*.md"))
    deleted = 0
    for f in files:
        low = f.name.lower()
        if any(pat in low for pat in EXCLUDED_PATTERNS):
            f.unlink()
            deleted += 1
            # Mirror
            m_file = Path(MIRROR_DIR) / f.parent.name / f.name
            if m_file.exists():
                try:
                    m_file.unlink()
                except Exception:
                    pass
    print(f"🗑️ Compendios fuera de dominio eliminados: {deleted}")

def rechunk_oversized_files(max_words: int = 280000):
    """Particiona cualquier archivo que supere el umbral seguro en partes balanceadas."""
    files = list(Path(BASE_DIR).glob("*/*.md"))
    rechunked = 0
    for f in files:
        with open(f, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()
        words = len(content.split())
        if words > 350000:
            print(f"✂️ Re-particionando archivo sobredimensionado: {f.name} ({words:,} palabras)")
            sections = content.split("\n### ")
            header = sections[0]
            sec_items = sections[1:]

            part1_secs = []
            part2_secs = []
            cur_words = 0
            half_words = words // 2

            for s in sec_items:
                s_words = len(s.split())
                if cur_words + s_words <= half_words or not part1_secs:
                    part1_secs.append(s)
                    cur_words += s_words
                else:
                    part2_secs.append(s)

            # Escribir part1 y part2
            parent = f.parent
            base_name = f.stem
            if "__part1" in base_name:
                stem_root = base_name.replace("__part1", "")
            else:
                stem_root = base_name

            file_part1 = parent / f"{stem_root}__subpart1.md"
            file_part2 = parent / f"{stem_root}__subpart2.md"

            content_p1 = header + "\n### " + "\n### ".join(part1_secs)
            content_p2 = header + "\n### " + "\n### ".join(part2_secs)

            with open(file_part1, "w", encoding="utf-8") as fp1:
                fp1.write(content_p1)
            with open(file_part2, "w", encoding="utf-8") as fp2:
                fp2.write(content_p2)

            f.unlink()
            rechunked += 1

    print(f"✂️ Archivos re-particionados: {rechunked}")

def sync_to_mirror():
    """Sincroniza todos los compendios verificados hacia Google Drive SSoT."""
    print("🔄 Sincronizando compendios saneados hacia Google Drive SSoT...")
    import subprocess
    cmd = [
        "rsync", "-av", "--delete",
        f"{BASE_DIR}/", f"{MIRROR_DIR}/"
    ]
    subprocess.run(cmd, check=True)
    print("✅ Sincronización SSoT completada exitosamente.")

def audit_and_certify():
    """Ejecuta la auditoría exhaustiva 100% de cumplimiento físico (Exit Code 0)."""
    print("\n" + "="*70)
    print("🔍 AUDITORÍA FORENSE SOBERANA DE COMPENDIOS (EXIT 0 CERTIFICATION)")
    print("="*70)

    files = list(Path(BASE_DIR).glob("*/*.md"))
    total_files = len(files)
    total_words = 0
    clusters = set()
    over_350k = []
    has_timestamps = []
    has_denylist = []
    has_admin_junk = []

    for f in files:
        clusters.add(f.parent.name)
        with open(f, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()

        words = len(content.split())
        total_words += words

        if words > 350000:
            over_350k.append((f.name, words))
        if "-->" in content and re.search(r"\d{1,2}:\d{2}.*?-->", content):
            has_timestamps.append(f.name)
        if any(pat in f.name.lower() for pat in EXCLUDED_PATTERNS):
            has_denylist.append(f.name)
        if any(j in content for j in ["ENLACES_DESCARGA_RECUPERADOS", "PROGRESO.txt", "MANUAL_TUTOR.md"]):
            has_admin_junk.append(f.name)

    print(f"• Total compendios limpios: {total_files}")
    print(f"• Total palabras en el ecosistema: {total_words:,}")
    print(f"• Micro-clusters cubiertos: {len(clusters)}/27")
    print(f"• Archivos >350.000 palabras: {len(over_350k)}")
    print(f"• Archivos con códigos de tiempo (timestamps): {len(has_timestamps)}")
    print(f"• Archivos de cursos vetados (denylist): {len(has_denylist)}")
    print(f"• Archivos con residuos de scraping administrativo: {len(has_admin_junk)}")

    passed = (
        total_files > 0
        and len(clusters) == 27
        and len(over_350k) == 0
        and len(has_timestamps) == 0
        and len(has_denylist) == 0
        and len(has_admin_junk) == 0
    )

    if passed:
        print("\n🎉 CERTIFICACIÓN EXITOSA: 100% CUMPLIMIENTO FÍSICO Y SOBERANO (EXIT 0).")
        return 0
    else:
        print("\n❌ FALLA EN AUDITORÍA: Revisa las violaciones detectadas.")
        return 1

if __name__ == "__main__":
    purge_excluded_courses()
    rechunk_oversized_files()
    sync_to_mirror()
    code = audit_and_certify()
    sys.exit(code)
