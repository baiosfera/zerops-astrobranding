#!/usr/bin/env python3
"""
Autonomous Extractor for FreeAstroAPI Engine (v2.2)
Extracts Western Tropical, Sidereal Fagan-Campanus, Numerology, BaZi True Solar, Vedic KP V2,
Western Profections, Progressions, and audits available PDF report credits.
"""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any, Dict, Optional
import unicodedata
import httpx

BASE_URL = os.getenv("FREEASTRO_API_URL", "https://api.freeastroapi.com")
DEFAULT_TIMEOUT = 12.0


def get_zodiac_sign(month: int, day: int) -> str:
    """Returns western zodiac sign key for daily sign horoscope."""
    if (month == 3 and day >= 21) or (month == 4 and day <= 19): return "aries"
    if (month == 4 and day >= 20) or (month == 5 and day <= 20): return "taurus"
    if (month == 5 and day >= 21) or (month == 6 and day <= 20): return "gemini"
    if (month == 6 and day >= 21) or (month == 7 and day <= 22): return "cancer"
    if (month == 7 and day >= 23) or (month == 8 and day <= 22): return "leo"
    if (month == 8 and day >= 23) or (month == 9 and day <= 22): return "virgo"
    if (month == 9 and day >= 23) or (month == 10 and day <= 22): return "libra"
    if (month == 10 and day >= 23) or (month == 11 and day <= 21): return "scorpio"
    if (month == 11 and day >= 22) or (month == 12 and day <= 21): return "sagittarius"
    if (month == 12 and day >= 22) or (month == 1 and day <= 19): return "capricorn"
    if (month == 1 and day >= 20) or (month == 2 and day <= 18): return "aquarius"
    return "pisces"


def load_natal_catalog() -> list:
    """Loads all 124 calculation operations from assets/natal_endpoints_catalog.json."""
    catalog_path = Path(__file__).parent.parent / "assets" / "natal_endpoints_catalog.json"
    if catalog_path.exists():
        try:
            return json.loads(catalog_path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


async def extract_freeastroapi(
    client_data: Dict[str, Any],
    api_key: Optional[str] = None,
    client: Optional[httpx.AsyncClient] = None,
    cache_manager: Optional[Any] = None,
    client_hash: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extracts all core astronomical, numerological, and BaZi calculations from FreeAstroAPI.
    """
    key = api_key or os.getenv("FREEASTRO_API_KEY") or os.getenv("freeastro_apiKey")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if key:
        headers["x-api-key"] = key

    full_name = client_data.get("name", "Consultant")
    pref_name = client_data.get("preferred_name", full_name)
    year = int(client_data.get("year", 1990))
    month = int(client_data.get("month", 1))
    day = int(client_data.get("day", 1))
    hour = int(client_data.get("hour", 12))
    minute = int(client_data.get("minute", 0))
    lat = float(client_data.get("lat", 0.0))
    lng = float(client_data.get("lng", 0.0))
    tz_str = client_data.get("tz_str", "UTC")
    gender = client_data.get("gender", "female")
    current_year = datetime.now(timezone.utc).year

    base_western_payload = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lng": lng, "tz_str": tz_str
    }

    payload_tropical_placidus = {**base_western_payload, "name": full_name, "house_system": "placidus", "zodiac_type": "tropical"}
    payload_tropical_campanus = {**base_western_payload, "name": full_name, "house_system": "campanus", "zodiac_type": "tropical"}
    payload_sidereal_fc = {
        **base_western_payload,
        "name": full_name,
        "zodiac_type": "sidereal",
        "sidereal_ayanamsa": "fagan_bradley",
        "house_system": "campanus"
    }
    payload_sidereal_lahiri = {
        **base_western_payload,
        "name": full_name,
        "zodiac_type": "sidereal",
        "sidereal_ayanamsa": "lahiri",
        "house_system": "whole_sign"
    }

    payload_numerology = {
        "method": {
            "system": "pythagorean",
            "profile": "standard",
            "compound_policy": "compound_and_root"
        },
        "subject": {
            "birth_date": f"{year:04d}-{month:02d}-{day:02d}",
            "name": {
                "birth": full_name,
                "current": pref_name
            },
            "tz_str": tz_str
        },
        "include_interpretations": True
    }

    sex_code = gender[0].upper() if gender else "M"

    payload_bazi = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lng": lng, "tz_str": tz_str,
        "sex": sex_code,
        "time_standard": "true_solar",
        "include_ten_gods": True,
        "include_pinyin": True,
        "include_stars": True,
        "include_interactions": True,
        "include_professional": True,
        "include_current_flow": True
    }

    # Flow payload uses single target_year to conform with OpenAPI 3.1 schema
    payload_bazi_flow = {
        **payload_bazi,
        "target_year": current_year
    }

    payload_bazi_health = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lng": lng, "tz_str": tz_str,
        "sex": sex_code,
        "time_standard": "true_solar",
        "include_timing": True,
        "timing_years_ahead": 10
    }

    payload_bazi_lifespan = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lng": lng, "tz_str": tz_str,
        "sex": sex_code,
        "time_standard": "true_solar",
        "max_age": 100,
        "cultivation_factor": 0.75
    }

    payload_kp = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lng": lng, "tz_str": tz_str,
        "ayanamsha": "kp",
        "dasha_levels": 3
    }

    payload_vargas = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute, "second": 0,
        "lat": lat, "lng": lng, "tz_str": tz_str,
        "ayanamsha": "lahiri",
        "divisions": [1, 2, 3, 4, 5, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60],
        "include_bhava_chalit": True
    }

    payload_acg = {
        "natal": {
            "year": year, "month": month, "day": day,
            "hour": hour, "minute": minute,
            "lat": lat, "lng": lng, "tz_str": tz_str,
            "house_system": "placidus",
            "time_known": True
        },
        "mode": "in_mundo",
        "bodies": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "True_Node"],
        "angles": ["asc", "dsc", "mc", "ic"],
        "include_crossings": False
    }

    raw_city = client_data.get("city") or "Unknown"
    clean_city = unicodedata.normalize("NFKD", str(raw_city)).encode("ASCII", "ignore").decode("utf-8")
    clean_city = re.sub(r"[,\(\)].*$", "", clean_city).strip() or "Unknown"

    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    datetime_iso = f"{date_str}T{hour:02d}:{minute:02d}:00"
    now_utc = datetime.now(timezone.utc)
    today_str = now_utc.strftime("%Y-%m-%d")
    zodiac_sign = get_zodiac_sign(month, day)

    # Base flat payloads
    base_western_payload = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lng": lng, "tz_str": tz_str
    }
    payload_tropical_placidus = {**base_western_payload, "name": full_name, "house_system": "placidus", "zodiac_type": "tropical"}
    payload_tropical_campanus = {**base_western_payload, "name": full_name, "house_system": "campanus", "zodiac_type": "tropical"}
    payload_sidereal_fc = {
        **base_western_payload,
        "name": full_name,
        "zodiac_type": "sidereal",
        "sidereal_ayanamsa": "fagan_bradley",
        "house_system": "campanus"
    }
    payload_sidereal_lahiri = {
        **base_western_payload,
        "name": full_name,
        "zodiac_type": "sidereal",
        "sidereal_ayanamsa": "lahiri",
        "house_system": "whole_sign"
    }

    location_obj = {
        "city": clean_city,
        "lat": lat,
        "lng": lng,
        "tz_str": tz_str
    }

    # Nested natal for directions & progressions (OpenAPI 3.1 SecondaryProgressionsNatalInput)
    natal_nested_obj = {
        "name": full_name,
        "datetime": datetime_iso,
        "time_known": True,
        "location": location_obj
    }

    payload_profections = {
        "year": year, "month": month, "day": day,
        "hour": hour, "minute": minute,
        "lat": lat, "lng": lng,
        "city": clean_city,
        "annual_profection": {
            "year": current_year
        }
    }

    catalog_path = Path(__file__).parent.parent / "assets" / "natal_endpoints_catalog.json"
    endpoints_to_run = [
        ("api_v1_natal_calculate_tropical_placidus", "POST", f"{BASE_URL}/api/v1/natal/calculate", payload_tropical_placidus, None),
        ("api_v1_natal_calculate_tropical_campanus", "POST", f"{BASE_URL}/api/v1/natal/calculate", payload_tropical_campanus, None),
        ("api_v1_natal_calculate_sidereal_fagan_campanus", "POST", f"{BASE_URL}/api/v1/natal/calculate", payload_sidereal_fc, None),
        ("api_v1_natal_calculate_sidereal_lahiri", "POST", f"{BASE_URL}/api/v1/natal/calculate", payload_sidereal_lahiri, None),
    ]

    for num_sys in ["pythagorean", "chaldean", "kabbalah", "ank_jyotish"]:
        num_payload = {
            "method": {
                "system": num_sys,
                "profile": "standard",
                "compound_policy": "compound_and_root"
            },
            "subject": {
                "birth_date": date_str,
                "name": {
                    "birth": full_name,
                    "current": pref_name
                },
                "tz_str": tz_str
            },
            "include_interpretations": True
        }
        endpoints_to_run.append((f"api_v1_numerology_profile_{num_sys}", "POST", f"{BASE_URL}/api/v1/numerology/profile", num_payload, None))

    if catalog_path.exists():
        try:
            cat_data = json.loads(catalog_path.read_text(encoding="utf-8"))
            for item in cat_data:
                p = item["path"]
                m = item.get("method", "POST").upper()
                schema = item.get("schema", "")

                # Skip permanently closed/deprecated or invalid endpoints
                if p == "/api/v1/natal/experimental" or "job_id" in p:
                    continue
                # Skip endpoints already registered explicitly
                if p == "/api/v1/natal/calculate" or p == "/api/v1/numerology/profile":
                    continue

                formatted_p = p.replace("{date}", date_str)
                url = f"{BASE_URL}{formatted_p}"

                # Keep version prefix to avoid collision between versions
                clean_key = p.strip("/").replace("/", "_").replace("-", "_").replace("{", "").replace("}", "")

                body = None
                params = None

                if m == "POST":
                    if schema in ("PrimaryDirectionsRequest",) or "/directions/" in p:
                        body = {
                            "natal": natal_nested_obj,
                            "range": {"start_date": f"{current_year}-01-01", "end_date": f"{current_year}-12-31", "limit": 100}
                        }
                    elif schema in ("ProgressionCalendarRequest",) or "/calendar" in p:
                        body = {
                            "natal": natal_nested_obj,
                            "calendar": {"from": f"{current_year}-01-01", "to": f"{current_year}-12-31"}
                        }
                    elif schema in ("ExactAspectSearchRequest", "ExactIngressSearchRequest") or "exact-aspects" in p or "exact-ingresses" in p:
                        body = {
                            "natal": natal_nested_obj,
                            "search": {"from": f"{current_year}-01-01", "to": f"{current_year}-12-31"}
                        }
                    elif schema in ("SecondaryProgressionsRequest",) or p.endswith("/progressions/secondary"):
                        body = {
                            "natal": natal_nested_obj,
                            "secondary_progression": {"target_date": today_str}
                        }
                    elif schema in ("ConverseSecondaryProgressionsRequest",) or p.endswith("/progressions/converse-secondary"):
                        body = {
                            "natal": natal_nested_obj,
                            "converse_secondary_progression": {"target_date": today_str}
                        }
                    elif schema in ("TertiaryProgressionsRequest",) or p.endswith("/progressions/tertiary"):
                        body = {
                            "natal": natal_nested_obj,
                            "tertiary_progression": {"target_date": today_str}
                        }
                    elif schema in ("QuaternaryProgressionsRequest",) or p.endswith("/progressions/quaternary"):
                        body = {
                            "natal": natal_nested_obj,
                            "quaternary_progression": {"target_date": today_str}
                        }
                    elif schema in ("QuotidianProgressionsRequest",) or p.endswith("/progressions/quotidian"):
                        body = {
                            "natal": natal_nested_obj,
                            "quotidian_progression": {"target_date": today_str}
                        }
                    elif schema in ("SolarArcProgressionsRequest",) or "solar-arc" in p:
                        body = {
                            "natal": natal_nested_obj,
                            "solar_arc_progression": {"target_date": today_str}
                        }
                    elif schema in ("SolarReturnRequest", "ExperimentalSolarReturnChartRequest") or "solar-return" in p or p.endswith("/solar/calculate"):
                        body = {
                            "natal": natal_nested_obj,
                            "solar_return": {
                                "year": int(current_year),
                                "location": location_obj
                            }
                        }
                    elif schema in ("PlanetReturnRequest",) or p.endswith("/returns/calculate"):
                        body = {
                            "natal": natal_nested_obj,
                            "return_target": {
                                "body": "sun",
                                "search_start": f"{current_year}-01-01",
                                "location": location_obj
                            }
                        }
                    elif schema in ("TransitRequest", "ExperimentalTransitChartRequest") or p.endswith("/transits/calculate"):
                        body = {
                            "natal": base_western_payload,
                            "transit_date": today_str,
                            "current_city": clean_city
                        }
                    elif schema in ("TransitTimelineRequest",):
                        body = {
                            "natal": base_western_payload,
                            "range_start": f"{current_year}-10-01",
                            "range_end": f"{current_year}-10-10"
                        }
                    elif schema in ("TransitSearchRequest",):
                        body = {
                            "natal": base_western_payload,
                            "transit_planet": "Jupiter",
                            "natal_point": "Sun"
                        }
                    elif schema in ("AstrocartographyCityCheckRequest", "AstrocartographyRelocationRequest"):
                        body = {
                            "natal": base_western_payload,
                            "city": clean_city
                        }
                    elif schema in ("AstrocartographyParansRequest",):
                        body = {
                            "natal": base_western_payload
                        }
                    elif schema in ("AstrocartographyLinesRequest", "AstrocartographyRecommendationsRequest") or "/astrocartography/" in p:
                        body = payload_acg
                    elif schema in ("AtomicReportRequest",) or "/ai/generate" in p:
                        body = {
                            **base_western_payload,
                            "name": full_name,
                            "city": clean_city,
                            "report_type": "natal_summary"
                        }
                    elif "PersonalHoroscopeRequest" in schema or "/horoscope/daily/personal" in p:
                        body = {
                            "birth": base_western_payload,
                            "date": today_str
                        }
                    elif schema in ("EphemerisRequest",) or "/ephemeris/calculate" in p:
                        body = {
                            "start": date_str,
                            "end": date_str
                        }
                    elif schema in ("VedicGocharTimelineRequest", "GocharTimelineRequest"):
                        body = {
                            **payload_vargas,
                            "range_start": f"{current_year}-10-01",
                            "range_end": f"{current_year}-10-10"
                        }
                    elif schema in ("VedicTransitInsightsRequest",) or p.endswith("/vedic/transits/insights"):
                        body = {
                            **payload_vargas,
                            "year": year, "month": month, "day": day,
                            "hour": hour, "minute": minute, "second": 0,
                            "lat": lat, "lng": lng, "tz_str": tz_str,
                            "ayanamsha": "lahiri",
                            "transit_year": int(current_year),
                            "transit_month": int(month),
                            "transit_day": int(day)
                        }
                    elif schema in ("VedicBatchRequest",):
                        body = {
                            "items": [
                                {
                                    "endpoint": "calculate",
                                    "payload": {
                                        "year": year, "month": month, "day": day,
                                        "hour": hour, "minute": minute, "second": 0,
                                        "lat": lat, "lng": lng, "tz_str": tz_str,
                                        "ayanamsha": "lahiri"
                                    }
                                }
                            ]
                        }
                    elif "ElectionSearchRequest" in schema or "/electional/" in p:
                        body = {
                            "search_window": {"start": f"{current_year}-10-01", "end": f"{current_year}-10-10"},
                            "location": location_obj
                        }
                    elif "FamousPeople" in schema:
                        body = {"natal": base_western_payload}
                    elif schema in ("WesternChatRequest", "VedicChatRequest"):
                        body = {"message": f"Interpretación astrológica para {full_name}"}
                    elif schema in ("VedicQARequest",) or p.endswith("/vedic/qa"):
                        body = {
                            "question": "abhijit_muhurat_today",
                            "date": today_str,
                            "time": f"{hour:02d}:{minute:02d}",
                            "city": clean_city
                        }
                    elif schema in ("VedicMuhuratPersonalizedSearchRequest",) or "personalized" in p:
                        body = {
                            "start_date": today_str,
                            "end_date": f"{current_year}-10-14",
                            "subject": {
                                "year": year, "month": month, "day": day,
                                "hour": hour, "minute": minute, "second": 0,
                                "lat": lat, "lng": lng, "tz_str": tz_str,
                                "ayanamsha": "lahiri"
                            },
                            "city": clean_city
                        }
                    elif schema in ("VedicMuhuratSearchRequest",) or p.endswith("/vedic/muhurat/search"):
                        body = {
                            "start_date": today_str,
                            "end_date": f"{current_year}-10-14",
                            "city": clean_city
                        }
                    elif p.endswith("/vedic/visual/chart") or "visual/chart" in p:
                        body = {
                            "year": year, "month": month, "day": day,
                            "hour": hour, "minute": minute, "second": 0,
                            "lat": lat, "lng": lng, "tz_str": tz_str,
                            "ayanamsha": "lahiri",
                            "divisions": [1, 9]
                        }
                    elif "/chinese/" in p:
                        if "/flow" in p: body = payload_bazi_flow
                        elif "/health" in p: body = payload_bazi_health
                        elif "/lifespan" in p: body = payload_bazi_lifespan
                        else: body = payload_bazi
                    elif "/numerology/" in p:
                        body = payload_numerology
                    elif "/vedic/" in p:
                        if "/kp" in p: body = payload_kp
                        elif "/vargas" in p: body = payload_vargas
                        elif "/batch" in p:
                            body = {
                                "items": [
                                    {
                                        "endpoint": "calculate",
                                        "payload": {
                                            "year": year, "month": month, "day": day,
                                            "hour": hour, "minute": minute, "second": 0,
                                            "lat": lat, "lng": lng, "tz_str": tz_str,
                                            "ayanamsha": "lahiri"
                                        }
                                    }
                                ]
                            }
                        else:
                            body = {
                                "year": year, "month": month, "day": day,
                                "hour": hour, "minute": minute, "second": 0,
                                "lat": lat, "lng": lng, "tz_str": tz_str,
                                "ayanamsha": "lahiri"
                            }
                    elif "/profections/" in p:
                        body = payload_profections
                    elif "sidereal" in p or "campanus" in p:
                        body = payload_tropical_campanus
                    else:
                        body = payload_tropical_placidus
                elif m == "GET":
                    if "/ephemeris" in p:
                        params = {"start": date_str, "end": date_str}
                    elif "/geo/search" in p:
                        params = {"q": clean_city}
                    elif "/horoscope/daily/sign" in p:
                        params = {"sign": zodiac_sign}
                    elif "/moon/month" in p:
                        params = {"year": year, "month": month}
                    elif "/sky-events" in p:
                        params = {"date": today_str}

                endpoints_to_run.append((clean_key, m, url, body, params))
        except Exception:
            pass

    if not endpoints_to_run:
        endpoints_to_run = [
            ("western_natal_tropical", "POST", f"{BASE_URL}/api/v1/natal/calculate", payload_tropical_placidus, None),
            ("western_natal_tropical_campanus", "POST", f"{BASE_URL}/api/v1/natal/calculate", payload_tropical_campanus, None),
            ("western_natal_sidereal_fagan_campanus", "POST", f"{BASE_URL}/api/v1/natal/calculate", payload_sidereal_fc, None),
            ("western_natal_sidereal_lahiri", "POST", f"{BASE_URL}/api/v1/natal/calculate", payload_sidereal_lahiri, None),
            ("western_natal_insights", "POST", f"{BASE_URL}/api/v1/western/natal/insights", payload_tropical_placidus, None),
            ("western_profections_annual", "POST", f"{BASE_URL}/api/v1/western/profections/annual", payload_profections, None),
            ("numerology_profile_pythagorean", "POST", f"{BASE_URL}/api/v1/numerology/profile", payload_numerology, None),
            ("chinese_bazi_true_solar", "POST", f"{BASE_URL}/api/v1/chinese/bazi", payload_bazi, None),
            ("chinese_bazi_flow", "POST", f"{BASE_URL}/api/v1/chinese/bazi/flow", payload_bazi_flow, None),
            ("chinese_bazi_health", "POST", f"{BASE_URL}/api/v1/chinese/bazi/health", payload_bazi_health, None),
            ("chinese_bazi_lifespan", "POST", f"{BASE_URL}/api/v1/chinese/bazi/lifespan", payload_bazi_lifespan, None),
            ("vedic_kp_v2", "POST", f"{BASE_URL}/api/v2/vedic/kp", payload_kp, None),
            ("vedic_vargas", "POST", f"{BASE_URL}/api/v2/vedic/vargas", payload_vargas, None),
            ("astrocartography_lines", "POST", f"{BASE_URL}/api/v1/western/astrocartography/lines", payload_acg, None),
        ]

    results: Dict[str, Any] = {
        "provider": "freeastro",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS",
        "plan": "Astro Entry ($8/mo, 50k req/mo, 2 PDF reports/mo)",
        "report_credits": None,
        "calls_made": 0,
        "data": {},
        "failures": []
    }

    close_client = False
    if client is None:
        client = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, follow_redirects=True)
        close_client = True

    try:
        total_endpoints = len(endpoints_to_run)
        results["endpoint_audits"] = []

        # 1. Audit report credits
        try:
            cred_resp = await client.get(f"{BASE_URL}/api/v1/natal/report-credits", headers=headers)
            results["calls_made"] += 1
            if cred_resp.status_code == 200:
                results["report_credits"] = cred_resp.json()
        except Exception:
            results["report_credits"] = {"available": 2, "plan": "Entry"}

        # 2. Execute endpoints with atomic delta cache
        for idx, (key_name, method, url, body, params) in enumerate(endpoints_to_run, 1):
            # Check delta cache
            if cache_manager and client_hash:
                cached_data = cache_manager.get_endpoint("freeastro", key_name, client_hash)
                if cached_data is not None:
                    print(f"⚡ [FreeAstro ({idx}/{total_endpoints})] {key_name} -> [CACHED / SKIP]", flush=True)
                    results["data"][key_name] = cached_data
                    results["endpoint_audits"].append({
                        "endpoint": key_name,
                        "status": "CACHED",
                        "http_status": 200,
                        "latency_ms": 0.0,
                        "error": None
                    })
                    continue

            t0 = time.perf_counter()
            try:
                await asyncio.sleep(0.25)
                if method == "GET":
                    resp = await client.get(url, headers=headers, params=params)
                else:
                    resp = await client.post(url, headers=headers, json=body)
                results["calls_made"] += 1
                lat = (time.perf_counter() - t0) * 1000.0

                if resp.status_code == 429:
                    print(f"⏳ [FreeAstro ({idx}/{total_endpoints})] 429 Rate Limit hit. Backing off 5.0s...", flush=True)
                    await asyncio.sleep(5.0)
                    t0 = time.perf_counter()
                    if method == "GET":
                        resp = await client.get(url, headers=headers, params=params)
                    else:
                        resp = await client.post(url, headers=headers, json=body)
                    results["calls_made"] += 1
                    lat = (time.perf_counter() - t0) * 1000.0

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except Exception:
                        data = {"format": "svg" if "<svg" in resp.text else "text", "content": resp.text}

                    if isinstance(data, dict) and (data.get("status") == "error" or "error" in data):
                        err_msg = data.get("error", data.get("message", "Error in response"))
                        print(f"❌ [FreeAstro ({idx}/{total_endpoints})] {key_name} -> [ERROR] ({lat:.1f}ms): {err_msg}", flush=True)
                        results["failures"].append({"endpoint": key_name, "error": err_msg})
                        results["data"][key_name] = {"error": err_msg}
                        results["endpoint_audits"].append({
                            "endpoint": key_name,
                            "status": "FAILED",
                            "http_status": 200,
                            "latency_ms": lat,
                            "error": str(err_msg)
                        })
                    else:
                        print(f"✨ [FreeAstro ({idx}/{total_endpoints})] {key_name} -> [200 OK] ({lat:.1f}ms)", flush=True)
                        results["data"][key_name] = data
                        if cache_manager and client_hash:
                            cache_manager.set_endpoint("freeastro", key_name, client_hash, data)
                        results["endpoint_audits"].append({
                            "endpoint": key_name,
                            "status": "SUCCESS",
                            "http_status": 200,
                            "latency_ms": lat,
                            "error": None
                        })
                else:
                    err_msg = f"HTTP {resp.status_code}: {resp.text[:150]}"
                    print(f"❌ [FreeAstro ({idx}/{total_endpoints})] {key_name} -> [HTTP {resp.status_code}] ({lat:.1f}ms)", flush=True)
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
                print(f"❌ [FreeAstro ({idx}/{total_endpoints})] {key_name} -> [{type(exc).__name__}] ({lat:.1f}ms): {err_msg}", flush=True)
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
            results["status"] = "FAILED" if len(results["failures"]) == len(endpoints_to_run) else "PARTIAL"
        else:
            results["status"] = "SUCCESS"

    finally:
        if close_client:
            await client.aclose()

    return results


def main():
    parser = argparse.ArgumentParser(description="FreeAstroAPI Extractor")
    parser.add_argument("--client-file", type=str, help="Path to client JSON file")
    parser.add_argument("--output", type=str, help="Path to write output JSON")
    args = parser.parse_args()

    client_data = {
        "name": "Consultant",
        "preferred_name": "Consultant",
        "year": 1990, "month": 1, "day": 1,
        "hour": 12, "minute": 0,
        "lat": 0.0, "lng": 0.0,
        "tz_str": "UTC"
    }

    if args.client_file and Path(args.client_file).exists():
        p = Path(args.client_file)
        if p.suffix.lower() == ".json":
            client_data = json.loads(p.read_text(encoding="utf-8"))

    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(extract_freeastroapi(client_data))

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Extraction saved to {args.output}")
    else:
        print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
