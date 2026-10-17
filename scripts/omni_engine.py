#!/usr/bin/env python3
"""
Omni Engine SOTA 2026 - Master CLI Facade for Oráculo (v4.0).
Unified Python 3.12 entrypoint coordinating ExtractionEngine and SharderEngine.
Pure Mathematical Engine: Zero Canned Prose, Zero Business Placeholders, Zero 0.0° Mocks.
"""

import argparse
import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True

# Add skill root to sys.path so 'pipeline' is discoverable
SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pipeline.config import config
from pipeline.engine import ExtractionEngine
from pipeline.sharder import SharderEngine, ExtractionFatalError
from pipeline.data_lake import VirtualDataLake


MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12
}

CITY_GEO_LOOKUP = {
    "hortua": {"lat": 4.5882307, "lon": -74.0853965, "tz": "America/Bogota", "city": "Bogota"},
    "materno infantil": {"lat": 4.5882307, "lon": -74.0853965, "tz": "America/Bogota", "city": "Bogota"},
    "bogota": {"lat": 4.7110, "lon": -74.0721, "tz": "America/Bogota", "city": "Bogota"},
    "bogotá": {"lat": 4.7110, "lon": -74.0721, "tz": "America/Bogota", "city": "Bogota"},
    "medellin": {"lat": 6.2442, "lon": -75.5812, "tz": "America/Bogota", "city": "Medellin"},
    "medellín": {"lat": 6.2442, "lon": -75.5812, "tz": "America/Bogota", "city": "Medellin"},
    "cali": {"lat": 3.4516, "lon": -76.5320, "tz": "America/Bogota", "city": "Cali"},
    "barranquilla": {"lat": 10.9685, "lon": -74.7813, "tz": "America/Bogota", "city": "Barranquilla"},
    "cartagena": {"lat": 10.3910, "lon": -75.4794, "tz": "America/Bogota", "city": "Cartagena"},
    "bucaramanga": {"lat": 7.1254, "lon": -73.1198, "tz": "America/Bogota", "city": "Bucaramanga"},
    "buenos aires": {"lat": -34.6037, "lon": -58.3816, "tz": "America/Argentina/Buenos_Aires", "city": "Buenos Aires"},
    "madrid": {"lat": 40.4168, "lon": -3.7038, "tz": "Europe/Madrid", "city": "Madrid"},
    "cdmx": {"lat": 19.4326, "lon": -99.1332, "tz": "America/Mexico_City", "city": "Ciudad de Mexico"},
    "ciudad de mexico": {"lat": 19.4326, "lon": -99.1332, "tz": "America/Mexico_City", "city": "Ciudad de Mexico"},
}


def parse_client_file(file_path: Path) -> dict:
    """Parse client birth data from text, markdown, or JSON files."""
    if not file_path.exists():
        if file_path.suffix.lower() == ".txt" and file_path.with_suffix(".md").exists():
            file_path = file_path.with_suffix(".md")
        elif file_path.suffix.lower() == ".md" and file_path.with_suffix(".txt").exists():
            file_path = file_path.with_suffix(".txt")
        else:
            # Resiliencia Diacrítica y Normalización Unicode (NFC/NFD/acento-insensible)
            import unicodedata
            def _strip_accents(s: str) -> str:
                return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()

            target_stem = _strip_accents(file_path.stem)
            parent_dir = file_path.parent
            resolved = None
            if parent_dir.is_dir():
                for candidate in parent_dir.iterdir():
                    if candidate.is_file() and candidate.suffix.lower() in [".md", ".txt", ".json"]:
                        if _strip_accents(candidate.stem) == target_stem:
                            resolved = candidate
                            break
            if resolved and resolved.exists():
                print(f"ℹ️ Archivo resuelto automáticamente por coincidencia diacrítica: {resolved}")
                file_path = resolved
            else:
                raise FileNotFoundError(f"Archivo de consultante no encontrado: {file_path}")
    
    content = file_path.read_text(encoding="utf-8").strip()
    data = {}
    brand_items = []
    in_brands_list = False
    
    # 1. Intentar JSON primero
    if file_path.suffix.lower() == ".json" or (content.startswith("{") and content.endswith("}")):
        try:
            raw_data = json.loads(content)
            if isinstance(raw_data, dict):
                for k, v in raw_data.items():
                    data[str(k).lower().strip()] = v
        except Exception:
            pass
            
    # 2. Si no es JSON o falló, procesar línea por línea
    if not data:
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue

            # Detectar URLs de Google Maps
            m_pin = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", line)
            if m_pin:
                data["lat"] = float(m_pin.group(1))
                data["lon"] = float(m_pin.group(2))
                continue

            m_view = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", line)
            if m_view and "lat" not in data:
                data["lat"] = float(m_view.group(1))
                data["lon"] = float(m_view.group(2))
                continue

            # Detectar líneas con coordenadas explícitas
            m_coords = re.search(r"(?:coordenadas|coords|gps|lat_lon)\s*[:=]\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)", line, re.IGNORECASE)
            if m_coords:
                data["lat"] = float(m_coords.group(1))
                data["lon"] = float(m_coords.group(2))
                continue

            # Detectar listas de marcas
            m_list = re.match(r"^(?:\d+[\.\)\-]|[•\-\*])\s*(.*)$", line)
            if in_brands_list and m_list:
                item = m_list.group(1).strip()
                if item:
                    brand_items.append(item)
                continue
            elif in_brands_list and not (":" in line or "=" in line):
                brand_items.append(line)
                continue
            else:
                in_brands_list = False

            # Limpiar viñetas markdown
            line = re.sub(r"^[\-\*\+•]\s*", "", line)
            line = re.sub(r"^\*\*([^\*]+)\*\*:\s*", r"\1: ", line)
            line = re.sub(r"^__([^_]+)__:\s*", r"\1: ", line)
            
            k, v = "", ""
            if ":" in line:
                if re.match(r"^\d{1,2}:\d{2}", line):
                    k, v = "tob", line
                else:
                    k, v = line.split(":", 1)
            elif "=" in line:
                k, v = line.split("=", 1)
            else:
                v = line
                
            k = k.strip().lower()
            v = v.strip().strip("'\"")

            if k in ["marca", "marcas", "marcas comerciales", "brands", "brand_names"]:
                in_brands_list = True
                if v:
                    brand_items.extend([b.strip() for b in v.split(",") if b.strip()])
                continue

            if k:
                # Normalizar si el valor tiene fecha en español o formato numérico común
                m_date = re.search(r"\b(\d{1,2})\s+(?:de\s+)?([a-zA-ZáéíóúÁÉÍÓÚñÑ]+)(?:\s+de)?\s+(\d{4})\b", v, re.IGNORECASE)
                if m_date and m_date.group(2).lower() in MONTHS_ES:
                    m_num = MONTHS_ES[m_date.group(2).lower()]
                    v = f"{int(m_date.group(3)):04d}-{m_num:02d}-{int(m_date.group(1)):02d}"
                else:
                    m_dmy = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b", v)
                    if m_dmy:
                        v = f"{int(m_dmy.group(3)):04d}-{int(m_dmy.group(2)):02d}-{int(m_dmy.group(1)):02d}"
                # Normalizar si el valor tiene hora con am/pm
                m_time = re.search(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(am|pm)?\b", v, re.IGNORECASE)
                if m_time and ("hora" in k or "tob" in k):
                    h = int(m_time.group(1))
                    mn = m_time.group(2)
                    ampm = m_time.group(4)
                    if ampm:
                        ampm = ampm.lower()
                        if ampm == "pm" and h < 12:
                            h += 12
                        elif ampm == "am" and h == 12:
                            h = 0
                    v = f"{h:02d}:{mn}"
                data[k] = v
            else:
                # Fecha en español (ej: 18 de enero de 1986 o 18 enero 1986) o numérica (19.10.1998, 19/10/1998, 19-10-1998)
                m_date = re.search(r"\b(\d{1,2})\s+(?:de\s+)?([a-zA-ZáéíóúÁÉÍÓÚñÑ]+)(?:\s+de)?\s+(\d{4})\b", line, re.IGNORECASE)
                if m_date:
                    m_name = m_date.group(2).lower()
                    if m_name in MONTHS_ES:
                        m_num = MONTHS_ES[m_name]
                        d_num = int(m_date.group(1))
                        y_num = int(m_date.group(3))
                        data["dob"] = f"{y_num:04d}-{m_num:02d}-{d_num:02d}"
                        continue
                else:
                    m_dmy = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b", line)
                    if m_dmy:
                        data["dob"] = f"{int(m_dmy.group(3)):04d}-{int(m_dmy.group(2)):02d}-{int(m_dmy.group(1)):02d}"
                        continue
                    m_iso = re.search(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b", line)
                    if m_iso:
                        data["dob"] = f"{int(m_iso.group(1)):04d}-{int(m_iso.group(2)):02d}-{int(m_iso.group(3)):02d}"
                        continue

                # Hora (ej: 03:00)
                m_time = re.search(r"\b(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(am|pm)?\b", line, re.IGNORECASE)
                if m_time:
                    h = int(m_time.group(1))
                    mn = m_time.group(2)
                    ampm = m_time.group(4)
                    if ampm:
                        ampm = ampm.lower()
                        if ampm == "pm" and h < 12:
                            h += 12
                        elif ampm == "am" and h == 12:
                            h = 0
                    data["tob"] = f"{h:02d}:{mn}"
                    continue

    if brand_items and "brand_names" not in data:
        data["brand_names"] = brand_items

    return data


def resolve_geo(city_name: str, raw_lat=None, raw_lon=None):
    if raw_lat is not None and raw_lon is not None:
        tz = "UTC"
        c_low = city_name.lower().strip() if city_name else ""
        resolved_city = city_name or "Desconocido"
        for k, v in CITY_GEO_LOOKUP.items():
            if k in c_low:
                tz = v["tz"]
                resolved_city = v["city"]
                break
        if tz == "UTC":
            approx_offset = round(float(raw_lon) / 15.0)
            tz = f"Etc/GMT{'+' if approx_offset <= 0 else '-'}{abs(approx_offset)}"
        return float(raw_lat), float(raw_lon), tz, resolved_city

    c_norm = city_name.lower().strip() if city_name else ""
    for k, v in CITY_GEO_LOOKUP.items():
        if k in c_norm or c_norm in k:
            return v["lat"], v["lon"], v["tz"], v["city"]

    raise ValueError(f"No se pudieron resolver las coordenadas para la ciudad '{city_name}'. Especifique latitud y longitud explícitamente.")


def main():
    parser = argparse.ArgumentParser(description="Omni Engine SOTA 2026 - Master CLI Facade for Oráculo v4.0")
    parser.add_argument("file_pos", nargs="?", default=None, help="Ruta al archivo del consultante (.txt, .json, .md)")
    parser.add_argument("-f", "--file", dest="file_flag", help="Ruta al archivo del consultante")
    parser.add_argument("-n", "--name", help="Nombre completo del consultante")
    parser.add_argument("--dob", help="Fecha de nacimiento (YYYY-MM-DD)")
    parser.add_argument("--tob", help="Hora de nacimiento (HH:MM)")
    parser.add_argument("--city", help="Ciudad de nacimiento")
    parser.add_argument("--lat", type=float, help="Latitud decimal")
    parser.add_argument("--lon", type=float, help="Longitud decimal")
    parser.add_argument("--tz", help="Zona horaria IANA (ej: America/Bogota)")
    parser.add_argument("--client-dir", help="Directorio destino del consultante")
    parser.add_argument("--apis", help="Lista de APIs a ejecutar separadas por coma (ej: astrologyapi,astroway,freeastro,vedastro). Por defecto: todas.")
    parser.add_argument("--exclude", help="Lista de APIs a excluir separadas por coma.")
    parser.add_argument("-x", "--extract", action="store_true", help="Solo ejecutar extracción y persistencia en caché (no compilar feeds).")
    parser.add_argument("-c", "--compile", action="store_true", help="Compilar shards y feeds (Capa Oro) desde caché verificado.")
    parser.add_argument("--allow-partial", action="store_true", help="Permitir compilación parcial ignorando la compuerta estricta de cobertura completa.")
    parser.add_argument("--refresh-pro", action="store_true", help="Bypass cache for paid Pro APIs")
    parser.add_argument("--include-atomic", action="store_true", help="Incluir los 191 calculadores atómicos de VedAstro (197 endpoints totales)")
    parser.add_argument("--astrology-key", help="Clave de Astrology-API.io para sobrescribir dinámicamente la del entorno")
    parser.add_argument("--dry-run", action="store_true", help="Dry run offline")

    args = parser.parse_args()

    if getattr(args, "astrology_key", None):
        os.environ["ASTROLOGY_API_IO"] = args.astrology_key.strip()
        config.reload()

    input_file = args.file_flag or args.file_pos
    file_data = {}
    file_path = None

    if input_file:
        file_path = Path(input_file).resolve()
        file_data = parse_client_file(file_path)

    def _clean_str(val: Any) -> str:
        if not val:
            return ""
        s = str(val).strip()
        if re.match(r"^[-—_.\s]+$", s) or s.lower() in ("n/a", "none", "null", "---", "--", "-"):
            return ""
        return s

    # Consolidar parámetros con sanitización estricta anti-placeholders
    raw_bname = _clean_str(file_data.get("birth_name") or file_data.get("nombre_nacimiento") or file_data.get("nombre de nacimiento") or args.name or file_data.get("name") or file_data.get("nombre"))
    birth_name = raw_bname or "Consultant"

    raw_cname = _clean_str(file_data.get("current_name") or file_data.get("nombre_actual") or file_data.get("nombre actual") or file_data.get("nombre actual (cambio)"))
    current_name = raw_cname or birth_name
    names = _clean_str(args.name) or current_name

    # Marcas: filtrar estrictamente para evitar marcas '---' o vacías
    brand_names_raw = file_data.get("brand_names") or file_data.get("marcas") or file_data.get("marca") or []
    if isinstance(brand_names_raw, str):
        brand_list = [_clean_str(b) for b in brand_names_raw.split(",") if _clean_str(b)]
    elif isinstance(brand_names_raw, list):
        brand_list = [_clean_str(b) for b in brand_names_raw if _clean_str(b)]
    else:
        brand_list = []

    raw_spoken = _clean_str(file_data.get("spoken_name") or file_data.get("trato"))
    if not raw_spoken:
        matched_token = None
        context_str = f"{file_path.stem if file_path else ''} {' '.join(brand_list)}".lower()
        for token in (current_name + " " + birth_name).split():
            if len(token) > 2 and token.lower() in context_str:
                matched_token = token.capitalize()
                break
        spoken_name = matched_token or (birth_name.split()[0] if birth_name != "Consultant" else "Consultant")
    else:
        spoken_name = raw_spoken

    # Fecha (dob)
    dob = args.dob or file_data.get("dob") or file_data.get("fecha") or file_data.get("fecha_nacimiento") or file_data.get("fecha de nacimiento")
    if dob:
        m_date = re.search(r"\b(\d{1,2})\s+(?:de\s+)?([a-zA-ZáéíóúÁÉÍÓÚñÑ]+)(?:\s+de)?\s+(\d{4})\b", str(dob), re.IGNORECASE)
        if m_date and m_date.group(2).lower() in MONTHS_ES:
            m_num = MONTHS_ES[m_date.group(2).lower()]
            dob = f"{int(m_date.group(3)):04d}-{m_num:02d}-{int(m_date.group(1)):02d}"
        else:
            m_iso = re.search(r"(\d{4})[-/. ](\d{1,2})[-/. ](\d{1,2})", str(dob))
            if m_iso:
                dob = f"{int(m_iso.group(1)):04d}-{int(m_iso.group(2)):02d}-{int(m_iso.group(3)):02d}"
            else:
                m_dmy = re.search(r"(\d{1,2})[-/. ](\d{1,2})[-/. ](\d{4})", str(dob))
                if m_dmy:
                    dob = f"{int(m_dmy.group(3)):04d}-{int(m_dmy.group(2)):02d}-{int(m_dmy.group(1)):02d}"

    # Hora (tob)
    tob = args.tob or file_data.get("tob") or file_data.get("hora") or file_data.get("hora_nacimiento") or file_data.get("hora de nacimiento")
    if tob:
        m_t = re.search(r"(\d{1,2}):(\d{2})", str(tob))
        if m_t:
            tob = f"{int(m_t.group(1)):02d}:{int(m_t.group(2)):02d}"

    city_raw = args.city or file_data.get("city") or file_data.get("ciudad") or file_data.get("lugar")
    lat_raw = args.lat or file_data.get("lat") or file_data.get("latitud")
    lon_raw = args.lon or file_data.get("lon") or file_data.get("longitud")

    lat, lon, tz, city = resolve_geo(city_raw, lat_raw, lon_raw)
    if args.tz:
        tz = args.tz

    # Directorio de salida
    client_dir = args.client_dir or file_data.get("client_dir")
    base_diag = Path(os.getenv("OUTPUT_ROOT", "/var/www/baiosfera/ASTROLOGÍA/DIAG"))
    if not base_diag.exists():
        base_diag = Path("/var/www/output")

    if not client_dir:
        if file_path:
            # Soberanía de ruta: respetar directamente la carpeta del archivo de entrada suministrado
            client_dir = str(file_path.parent)
        else:
            folder_slug = re.sub(r'[^a-zA-Z0-9]+', '_', (current_name or names).upper()).strip('_')
            client_dir = str(base_diag / folder_slug)
    elif not client_dir.startswith("/"):
        client_dir = str(base_diag / client_dir)

    # Validar campos obligatorios
    missing = []
    if not dob:
        missing.append("dob (fecha de nacimiento YYYY-MM-DD)")
    if not tob:
        missing.append("tob (hora de nacimiento HH:MM)")
    if lat is None:
        missing.append("lat (latitud)")
    if lon is None:
        missing.append("lon (longitud)")

    if missing:
        print(f"❌ Error: Faltan parámetros obligatorios de nacimiento: {', '.join(missing)}", file=sys.stderr)
        return 1

    print("=" * 70)
    print("🏛️  ORÁCULO MAESTRO SOTA 2026 — OMNI ENGINE PIPELINE (v4.0)")
    print("=" * 70)
    print(f"📍 Destino: {client_dir}")
    print(f"👤 Consultante: {birth_name} (Actual: {current_name} | Trato: {spoken_name})")
    if brand_list:
        print(f"🏢 Marcas ({len(brand_list)}): {', '.join(brand_list)}")
    print(f"📅 Nacimiento: {dob} a las {tob} ({tz}) [{city} | Lat: {lat}, Lon: {lon}]")
    print(f"🛡️  Modo: {'DRY-RUN' if args.dry_run else 'LIVE EXTRACTION (Async Multi-Engine)'}")
    print(f"🔄 Refresh Pro: {args.refresh_pro}")
    print("-" * 70)

    # Calcular offset horario canónico
    m_norm = re.search(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", str(dob))
    if m_norm:
        y, m, d = int(m_norm.group(1)), int(m_norm.group(2)), int(m_norm.group(3))
    else:
        parts = [p for p in re.split(r"[-/. ]", str(dob)) if p.strip()]
        if len(parts) == 3:
            if len(parts[0]) == 4:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            else:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
        else:
            raise ValueError(f"Formato de fecha inválido o no reconocido: '{dob}'")
    dob = f"{y:04d}-{m:02d}-{d:02d}"
    h, mn = [int(x) for x in tob.split(":")[:2]]

    try:
        dt = datetime(y, m, d, h, mn, tzinfo=ZoneInfo(tz))
        tz_offset = dt.utcoffset().total_seconds() / 3600.0
    except Exception:
        tz_offset = round(lon / 15.0)

    client_payload = {
        "year": y, "month": m, "day": d,
        "hour": h, "minute": mn,
        "lat": lat, "lng": lon,
        "tz_str": tz, "tz_offset": tz_offset,
        "name": birth_name,
        "preferred_name": spoken_name,
        "city": city,
        "brand_names": brand_list
    }

    apis_list = [a.strip() for a in args.apis.split(",")] if args.apis else None
    exclude_list = [e.strip() for e in args.exclude.split(",")] if args.exclude else None

    try:
        cache_dir = Path(client_dir) / "raw" / "json" / "cache"
        engine = ExtractionEngine(
            cache_dir=str(cache_dir),
            refresh_pro=args.refresh_pro,
            include_atomic=getattr(args, "include_atomic", False)
        )

        is_extraction_only = args.extract or (bool(args.apis) and not args.compile)

        if is_extraction_only:
            print("=" * 70)
            print("🚀 MODO EXTRACCIÓN PURA (-x / --apis) — CERO SHARDING PREMATURO")
            print("=" * 70)
            extraction_output = asyncio.run(engine.execute_extraction(client_payload, apis=apis_list, exclude=exclude_list))
            cov = engine.get_coverage_status(client_payload)
            print("=" * 70)
            print("✅ Extracción y persistencia en caché finalizadas con éxito:")
            print(f"  • Directorio base: {client_dir}")
            print(f"  • Caché JSON persistida en: {cache_dir}")
            print(f"  • Hash del consultante: {cov['client_hash']}")
            print(f"  • Cobertura acumulada en lago de datos: {cov['pct']}% ({len(cov['coverage']) - len(cov['missing'])}/{len(cov['coverage'])} proveedores)")
            for prov_k, prov_ok in cov['coverage'].items():
                status_icon = "🟢" if prov_ok else "⚪"
                status_txt = "EN CACHÉ" if prov_ok else "PENDIENTE"
                print(f"    {status_icon} {prov_k.ljust(15)} : {status_txt}")
            if cov['missing']:
                print(f"\n⚠️  Aún faltan proveedores por extraer antes de compilar (-c): {', '.join(cov['missing'])}")
            else:
                print("\n🎉 ¡Universo astrológico 100% completo en caché! Listo para compilar con: -c")
            print("=" * 70)
            return 0

        # MODO COMPILACIÓN (-c o ejecución completa por defecto)
        cov = engine.get_coverage_status(client_payload)

        # Revisar si existe manifiesto de exclusión justificada
        exclusion_file = Path(client_dir) / "raw" / "json" / "audit" / "exclusion_manifest.json"
        excluded_providers = []
        if exclusion_file.exists():
            try:
                with open(exclusion_file, "r", encoding="utf-8") as f:
                    exc_manifest = json.load(f)
                    excluded_providers = [p.lower().strip() for p in exc_manifest.get("excluded_providers", [])]
            except Exception:
                pass

        if exclude_list:
            for item in exclude_list:
                item_lower = item.lower().strip()
                if item_lower == "mcp":
                    excluded_providers.extend(["bazi_mcp", "kundali_mcp", "zmanim_mcp"])
                else:
                    excluded_providers.append(item_lower)

        unjustified_missing = [m for m in cov['missing'] if m not in excluded_providers]

        if unjustified_missing and not args.allow_partial:
            # Si es corrida automática por defecto (sin -c explícito), intentar auto-extraer faltantes
            if not args.compile:
                print(f"ℹ️ Auto-extrayendo proveedores pendientes en lago de datos: {unjustified_missing}...")
                asyncio.run(engine.execute_extraction(client_payload, apis=unjustified_missing, exclude=exclude_list))
                cov = engine.get_coverage_status(client_payload)
                unjustified_missing = [m for m in cov['missing'] if m not in excluded_providers]

            if unjustified_missing and not args.allow_partial:
                print("=" * 70, file=sys.stderr)
                print("❌ COMPILACIÓN BLOQUEADA (Strict Multi-Tradition Gate):", file=sys.stderr)
                print(f"El universo astrológico está incompleto para este consultante ({cov['pct']}% en caché).", file=sys.stderr)
                print(f"Proveedores ausentes sin justificación: {', '.join(unjustified_missing)}", file=sys.stderr)
                print("\nPor contrato de calidad, la compilación de shards y Fase 0 no procede con datos faltantes", file=sys.stderr)
                print("para evitar corromper la matriz downstream de branding (orchesbrand).", file=sys.stderr)
                print("\nAcciones disponibles:", file=sys.stderr)
                print(f"  1. Justificar exclusión por cuota/caída en: {exclusion_file}", file=sys.stderr)
                print(f"  2. Forzar compilación parcial deliberada pasando: --allow-partial", file=sys.stderr)
                print("=" * 70, file=sys.stderr)
                return 2

        print(f"📦 Compilando feeds y shards desde lago de datos (Cobertura: {cov['pct']}%)...")
        extraction_output = {"client_payload": client_payload}

        # Ejecutar verificación de salud, sharding de 12 shards y 9 feeds (Capa Oro)
        sharder = SharderEngine(output_root=client_dir)
        shard_summary = sharder.verify_and_shard(extraction_output)

        # Silver Tier: Cargar Virtual Data Lake y compilar master dump omni_dump_mega.json
        lake = VirtualDataLake(Path(client_dir) / "raw")
        master_dump_path = lake.export_master_dump()

        print("=" * 70)
        print("✅ Compilación matemática y sharding finalizados con éxito (Canon 12-15-9):")
        print(f"  • Directorio base: {client_dir}")
        print(f"  • 12 Shards Físicos JSON (Bronze): {client_dir}/raw/json/dumps/ ({shard_summary['shards_count']} shards)")
        print(f"  • 15 Shards Relacionales (Silver): {client_dir}/raw/json/dumps/client_dumps_15_shards.json")
        print(f"  • 9 Feeds Enciclopédicos (Gold): {client_dir}/raw/feeds/ ({shard_summary['feeds_count']} feeds)")
        print(f"  • Silver Manifest: {client_dir}/raw/json/dumps/manifest.json")
        print(f"  • Master Dump: {master_dump_path}")
        print(f"  • Micro-Auditorías Atómicas: {client_dir}/raw/json/audit/")
        print(f"  • Auditoría Forense Macro: {client_dir}/raw/json/extraction_health_audit.md")
        print(f"  • Health Ledger Consolidado: {client_dir}/raw/json/audit/health_ledger.json")
        print("=" * 70)
        return 0

    except ExtractionFatalError as e:
        print(f"❌ Error Fatal de Extracción: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"❌ Error crítico en ejecución de pipeline: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
