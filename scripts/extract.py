#!/usr/bin/env python3
"""
Autonomous Universal Extractor for VedAstro PRO API (v1.4)
Extracts 6 core macro-endpoints (HoroscopePredictions, AllPlanetData, AllHouseData,
DasaAtRange, JHoraYogaList, KalaSarpaYoga) and supports optional extraction of all
191 granular atomic calculators via --include-atomic for PRO Unlimited accounts.
Validates semantic status ('Pass' vs 'Fail'), enforces numeric timezone offset (+/-HH:MM),
and uses canonical 'inputTime' for atomic calculators with polite pacing (anti-throttling).
"""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx

VEDASTRO_URL = os.getenv("VEDASTRO_URL", "https://api.vedastro.org/api")
DEFAULT_TIMEOUT = 16.0


def format_timezone_offset(tz_offset: float) -> str:
    """Converts a float timezone offset (e.g. -5.0 or 5.5) to canonical string '+/-HH:MM'."""
    sign = "+" if tz_offset >= 0 else "-"
    abs_offset = abs(tz_offset)
    hours = int(abs_offset)
    minutes = int(round((abs_offset - hours) * 60))
    return f"{sign}{hours:02d}:{minutes:02d}"


def build_std_time(year: int, month: int, day: int, hour: int, minute: int, tz_offset_str: str) -> str:
    """Formats StdTime strictly as 'HH:mm DD/MM/YYYY +/-ZZ:ZZ'."""
    return f"{hour:02d}:{minute:02d} {day:02d}/{month:02d}/{year:04d} {tz_offset_str}"


def load_atomic_time_methods() -> List[str]:
    """
    Loads 191 atomic methods from catalog that only require natal Time.
    """
    cat_path = Path(__file__).parent.parent / "assets" / "advanced_calculators_catalog.json"
    if cat_path.exists():
        try:
            data = json.loads(cat_path.read_text(encoding="utf-8"))
            calcs = data.get("calculators", [])
            methods = []
            for c in calcs:
                desc = c.get("description", "")
                sig = ""
                for line in desc.split("\n"):
                    if "Signature:" in line:
                        sig = line
                        break
                if "Timetime" in sig and len(sig.split("(")[1].split(",")) == 1:
                    methods.append(c["name"])
            if methods:
                return methods
        except Exception:
            pass
    return []


async def extract_vedastro(
    client_data: Dict[str, Any],
    api_key: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
    include_atomic: bool = False,
    cache_manager: Optional[Any] = None,
    client_hash: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extracts complete VedAstro PRO calculations for the given client data.
    Supports atomic delta-cache skipping and recording.
    """
    key = api_key or os.getenv("VEDASTRO_API_KEY") or os.getenv("vedastro_apiKey")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if key:
        headers["x-api-key"] = key

    year = int(client_data.get("year", 1990))
    month = int(client_data.get("month", 1))
    day = int(client_data.get("day", 1))
    hour = int(client_data.get("hour", 12))
    minute = int(client_data.get("minute", 0))
    lat = float(client_data.get("lat", 0.0))
    lng = float(client_data.get("lng", 0.0))
    city = client_data.get("city", client_data.get("preferred_name", "Birth City"))

    tz_offset_val = client_data.get("tz_offset", -5.0)
    if isinstance(tz_offset_val, (int, float)):
        tz_offset_str = format_timezone_offset(float(tz_offset_val))
    else:
        tz_offset_str = str(tz_offset_val)
        if not (tz_offset_str.startswith("+") or tz_offset_str.startswith("-")):
            tz_offset_str = "-05:00"

    std_time = build_std_time(year, month, day, hour, minute, tz_offset_str)

    # Target range for dashas (from birth to 90 years ahead)
    end_year = year + 90
    end_std_time = build_std_time(end_year, month, day, hour, minute, tz_offset_str)

    loc_obj = {
        "Latitude": lat,
        "Longitude": lng,
        "Name": city
    }

    payload_predictions = {
        "birthTime": {
            "StdTime": std_time,
            "Location": loc_obj
        },
        "Ayanamsa": "LAHIRI",
        "sortByWeight": True
    }

    payload_planet = {
        "PlanetName": "All",
        "Time": {
            "StdTime": std_time,
            "Location": loc_obj
        },
        "Ayanamsa": "LAHIRI"
    }

    payload_house = {
        "HouseName": "All",
        "Time": {
            "StdTime": std_time,
            "Location": loc_obj
        },
        "Ayanamsa": "LAHIRI"
    }

    payload_dasa = {
        "birthTime": {
            "StdTime": std_time,
            "Location": loc_obj
        },
        "TimebirthTime": {
            "StdTime": std_time,
            "Location": loc_obj
        },
        "startTime": {
            "StdTime": std_time,
            "Location": loc_obj
        },
        "endTime": {
            "StdTime": end_std_time,
            "Location": loc_obj
        },
        "levels": 5,
        "precision_hours": 100,
        "ayanamsa": "LAHIRI"
    }

    # Atomic calculators strictly require 'inputTime'
    payload_atomic_base = {
        "inputTime": {
            "StdTime": std_time,
            "Location": loc_obj
        },
        "Ayanamsa": "LAHIRI"
    }

    payload_jhora = {
        "time": {
            "StdTime": std_time,
            "Location": loc_obj
        },
        "Ayanamsa": "LAHIRI"
    }

    endpoints: List[Tuple[str, str, Dict[str, Any]]] = [
        ("predictions", f"{VEDASTRO_URL}/Calculate/HoroscopePredictions", payload_predictions),
        ("planet_data", f"{VEDASTRO_URL}/Calculate/AllPlanetData", payload_planet),
        ("house_data", f"{VEDASTRO_URL}/Calculate/AllHouseData", payload_house),
        ("ashtakvarga", f"{VEDASTRO_URL}/Calculate/Ashtakvarga", payload_house),
        ("dasa_range", f"{VEDASTRO_URL}/Calculate/DasaAtRange", payload_dasa),
        ("jhora_yogas", f"{VEDASTRO_URL}/Calculate/JHoraYogaList", payload_jhora),
        ("kalasarpa_yoga", f"{VEDASTRO_URL}/Calculate/KalaSarpaYoga", payload_atomic_base),
    ]

    # Append 191 atomic calculators if requested
    if include_atomic:
        atomic_names = load_atomic_time_methods()
        for name in atomic_names:
            endpoints.append((f"atomic_{name}", f"{VEDASTRO_URL}/Calculate/{name}", payload_atomic_base))

    results: Dict[str, Any] = {
        "provider": "vedastro",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS",
        "is_unlimited": True,
        "include_atomic": include_atomic,
        "calls_made": 0,
        "data": {},
        "raw_responses": {},
        "endpoint_audits": [],
        "failures": []
    }

    close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True)
        close_client = True

    try:
        total_eps = len(endpoints)
        for idx, (key_name, url, body) in enumerate(endpoints, 1):
            # 1. Delta cache check
            if cache_manager and client_hash:
                cached_data = cache_manager.get_endpoint("vedastro", key_name, client_hash)
                if cached_data is not None:
                    print(f"⚡ [VedAstro ({idx}/{total_eps})] {key_name} -> [CACHED / SKIP]", flush=True)
                    results["data"][key_name] = cached_data
                    results["raw_responses"][key_name] = cached_data
                    results["endpoint_audits"].append({
                        "endpoint": key_name,
                        "status": "CACHED",
                        "http_status": 200,
                        "latency_ms": 0.0,
                        "error": None
                    })
                    continue

            if results["calls_made"] > 0:
                # Polite pacing to avoid API throttling
                await asyncio.sleep(0.35)

            t0 = time.perf_counter()
            try:
                resp = await client.post(url, headers=headers, json=body)
                results["calls_made"] += 1
                lat = (time.perf_counter() - t0) * 1000.0
                if resp.status_code == 200:
                    data = resp.json()
                    results["raw_responses"][key_name] = data

                    if isinstance(data, dict):
                        status_field = str(data.get("Status", "")).lower()
                        if status_field == "pass":
                            payload_val = data.get("Payload", data)
                            results["data"][key_name] = payload_val
                            if cache_manager and client_hash:
                                cache_manager.set_endpoint("vedastro", key_name, client_hash, payload_val)
                            print(f"✨ [VedAstro ({idx}/{total_eps})] {key_name} -> [200 OK Pass] ({lat:.1f}ms)", flush=True)
                            results["endpoint_audits"].append({
                                "endpoint": key_name,
                                "status": "SUCCESS",
                                "http_status": 200,
                                "latency_ms": lat,
                                "error": None
                            })
                        elif status_field == "fail":
                            err_msg = str(data.get("Payload", "VedAstro calculation returned Status: Fail"))
                            print(f"❌ [VedAstro ({idx}/{total_eps})] {key_name} -> [FAIL]: {err_msg}", flush=True)
                            results["failures"].append({"endpoint": key_name, "error": err_msg})
                            results["data"][key_name] = {"error": err_msg, "status": "FAIL"}
                            results["endpoint_audits"].append({
                                "endpoint": key_name,
                                "status": "FAILED",
                                "http_status": 200,
                                "latency_ms": lat,
                                "error": err_msg
                            })
                        else:
                            results["data"][key_name] = data
                            if cache_manager and client_hash:
                                cache_manager.set_endpoint("vedastro", key_name, client_hash, data)
                            print(f"✨ [VedAstro ({idx}/{total_eps})] {key_name} -> [200 OK] ({lat:.1f}ms)", flush=True)
                            results["endpoint_audits"].append({
                                "endpoint": key_name,
                                "status": "SUCCESS",
                                "http_status": 200,
                                "latency_ms": lat,
                                "error": None
                            })
                    else:
                        results["data"][key_name] = data
                        if cache_manager and client_hash:
                            cache_manager.set_endpoint("vedastro", key_name, client_hash, data)
                        print(f"✨ [VedAstro ({idx}/{total_eps})] {key_name} -> [200 OK] ({lat:.1f}ms)", flush=True)
                        results["endpoint_audits"].append({
                            "endpoint": key_name,
                            "status": "SUCCESS",
                            "http_status": 200,
                            "latency_ms": lat,
                            "error": None
                        })
                else:
                    lat = (time.perf_counter() - t0) * 1000.0
                    err_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    print(f"❌ [VedAstro ({idx}/{total_eps})] {key_name} -> [HTTP {resp.status_code}]: {err_msg}", flush=True)
                    results["failures"].append({"endpoint": key_name, "error": err_msg})
                    results["data"][key_name] = {"error": err_msg}
                    results["endpoint_audits"].append({
                        "endpoint": key_name,
                        "status": "FAILED",
                        "http_status": resp.status_code,
                        "latency_ms": lat,
                        "error": err_msg
                    })
            except Exception as exc:
                lat = (time.perf_counter() - t0) * 1000.0
                err_msg = f"Exception: {type(exc).__name__} - {str(exc)}"
                print(f"❌ [VedAstro ({idx}/{total_eps})] {key_name} -> [EXC]: {err_msg}", flush=True)
                results["failures"].append({"endpoint": key_name, "error": err_msg})
                results["data"][key_name] = {"error": err_msg}
                results["endpoint_audits"].append({
                    "endpoint": key_name,
                    "status": "FAILED",
                    "http_status": 500,
                    "latency_ms": lat,
                    "error": err_msg
                })

        if results["failures"]:
            results["status"] = "FAILED" if len(results["failures"]) == len(endpoints) else "PARTIAL"
        else:
            results["status"] = "SUCCESS"

    finally:
        if close_client:
            await client.aclose()

    return results


def main():
    parser = argparse.ArgumentParser(description="VedAstro PRO Extractor v1.4")
    parser.add_argument("--client-file", type=str, help="Path to client JSON file")
    parser.add_argument("--output", type=str, help="Path to write output JSON")
    parser.add_argument("--include-atomic", action="store_true", help="Include all 191 atomic calculators")
    args = parser.parse_args()

    client_data = {
        "year": 1986, "month": 1, "day": 18,
        "hour": 3, "minute": 0,
        "lat": 6.2340437, "lng": -75.5731248,
        "tz_offset": -5.0,
        "city": "Medellin"
    }

    if args.client_file and Path(args.client_file).exists():
        p = Path(args.client_file)
        if p.suffix.lower() == ".json":
            client_data = json.loads(p.read_text(encoding="utf-8"))

    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(extract_vedastro(client_data, include_atomic=args.include_atomic))

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Extraction saved to {args.output}")
    else:
        print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
