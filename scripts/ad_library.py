#!/usr/bin/env python3
"""
ad-library — Token-Frugal Meta Ad Library Extractor & Normalizer (v1.0)
Governed by meta-script & 00-SUPREME-DIRECTIVE.md.

Extracts active ads from Meta Ad Library via a deterministic provider chain:
  1. Official Meta Ad Library API (when META_AD_LIBRARY_TOKEN / META_ACCESS_TOKEN is set)
  2. Firecrawl scrape API (FIRECRAWL_API_KEY from env, ~/.env, or mcp_config.json)
  3. Jina Reader fallback (r.jina.ai)
  4. Local file/stdin (`parse` subcommand or `--provider file`)

Strips ~65KB+ of country selectors, nav chrome, and boilerplate in pure Python
(0 LLM tokens) and outputs a compact `<3KB` structured brief (`ad_library_brief.json`).
Optional `--synth-via bifrost` extracts hooks, VoC phrases, objections, and market gaps.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


CAPTCHA_MARKERS = (
    "verify you are human",
    "security check",
    "recaptcha",
    "hcaptcha",
    "turnstile",
    "complete the captcha",
    "confirma que eres humano",
    "control de seguridad",
)

MONTH_MAP: Dict[str, int] = {
    "jan": 1, "january": 1, "ene": 1, "enero": 1,
    "feb": 2, "february": 2, "febrero": 2,
    "mar": 3, "march": 3, "marzo": 3,
    "apr": 4, "april": 4, "abr": 4, "abril": 4,
    "may": 5, "mayo": 5,
    "jun": 6, "june": 6, "junio": 6,
    "jul": 7, "july": 7, "julio": 7,
    "aug": 8, "august": 8, "ago": 8, "agosto": 8,
    "sep": 9, "sept": 9, "september": 9, "septiembre": 9, "set": 9,
    "oct": 10, "october": 10, "octubre": 10,
    "nov": 11, "november": 11, "noviembre": 11,
    "dec": 12, "december": 12, "dic": 12, "diciembre": 12,
}

CTA_LABELS = {
    "learn more", "más información", "mas informacion", "shop now", "comprar",
    "sign up", "registrarte", "regístrate", "send message", "enviar mensaje",
    "send whatsapp message", "enviar mensaje de whatsapp", "book now", "reservar",
    "download", "descargar", "watch more", "ver más", "apply now", "postularme",
    "get offer", "obtener oferta", "subscribe", "suscribirme", "contact us", "contáctanos",
    "get quote", "solicitar cotización", "see menu", "ver menú",
}

LIBRARY_ID_RE = re.compile(
    r"(?:Library ID|Identificador de la biblioteca|ID de la biblioteca)\s*:\s*(\d{8,22})",
    re.IGNORECASE,
)
STARTED_DATE_RE = re.compile(
    r"(?:Started running on|En circulación desde el|En circulacion desde el|Publicado el)\s+"
    r"([A-Za-zÁÉÍÓÚáéíóú]+\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+(?:de\s+)?[A-Za-zÁÉÍÓÚáéíóú]+\.?\s+(?:de\s+)?\d{4}|\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)
VARIANTS_RE = re.compile(
    r"(\d+)\s+(?:ads?\s+use\s+this\s+creative|anuncios?\s+usan\s+este\s+contenido)",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^\s\)\]>\"']+")
IGNORED_DOMAINS = (
    "facebook.com", "fb.com", "fbcdn.net", "fbsbx.com", "instagram.com",
    "meta.com", "whatsapp.com", "w3.org", "schema.org", "l.facebook.com",
)


def _read_key_from_local_configs(key_names: Tuple[str, ...]) -> Optional[str]:
    """Resolve provider API keys safely from env, ~/.env, or mcp_config.json without printing them."""
    for name in key_names:
        val = os.environ.get(name, "").strip()
        if val:
            return val

    env_file = Path.home() / ".env"
    if env_file.is_file():
        try:
            for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip().removeprefix("export ").strip()
                if k in key_names:
                    cleaned = v.strip().strip('"').strip("'")
                    if cleaned:
                        return cleaned
        except OSError:
            pass

    mcp_cfg = Path.home() / ".gemini" / "config" / "mcp_config.json"
    if mcp_cfg.is_file():
        try:
            data = json.loads(mcp_cfg.read_text(encoding="utf-8"))
            for srv in (data.get("mcpServers") or {}).values():
                srv_env = srv.get("env") or {}
                for name in key_names:
                    val = str(srv_env.get(name, "")).strip()
                    if val and not val.startswith("${"):
                        return val
        except Exception:
            pass
    return None


def build_ad_library_url(query: str, country: str = "CO", active_status: str = "active") -> str:
    params = urllib.parse.urlencode({
        "active_status": active_status,
        "ad_type": "all",
        "country": country.upper(),
        "q": query,
        "search_type": "keyword_unordered",
        "media_type": "all",
    })
    return f"https://www.facebook.com/ads/library/?{params}"


def parse_started_date(raw_date: str) -> Optional[date]:
    s = re.sub(r"[,.]", " ", raw_date.strip().lower())
    s = re.sub(r"\bde\b", " ", s)
    parts = [p for p in s.split() if p]
    if not parts:
        return None
    if re.match(r"^\d{4}-\d{2}-\d{2}$", parts[0]):
        try:
            return date.fromisoformat(parts[0])
        except ValueError:
            return None
    if len(parts) == 3:
        # Format: "nov 1 2026" or "1 nov 2026"
        if parts[0].isdigit() and parts[1] in MONTH_MAP and parts[2].isdigit():
            day, month, year = int(parts[0]), MONTH_MAP[parts[1]], int(parts[2])
        elif parts[1].isdigit() and parts[0] in MONTH_MAP and parts[2].isdigit():
            month, day, year = MONTH_MAP[parts[0]], int(parts[1]), int(parts[2])
        else:
            return None
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None


def _detect_captcha(raw_text: str) -> bool:
    low = raw_text.lower()
    # Only flag if page has minimal ads AND explicit gate wording
    has_ads = bool(LIBRARY_ID_RE.search(raw_text))
    if has_ads:
        return False
    return any(marker in low for marker in CAPTCHA_MARKERS)


def _clean_destination_url(raw_url: str) -> Optional[str]:
    u = raw_url.strip().rstrip(".,;)")
    if "l.facebook.com/l.php" in u:
        parsed = urllib.parse.urlparse(u)
        qs = urllib.parse.parse_qs(parsed.query)
        if qs.get("u"):
            u = urllib.parse.unquote(qs["u"][0])
    parsed = urllib.parse.urlparse(u)
    host = parsed.netloc.lower()
    if not host or any(host == d or host.endswith("." + d) for d in IGNORED_DOMAINS):
        return None
    # Strip fbclid tracking noise on destination preview
    qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)
    clean_qs = {k: v for k, v in qs.items() if k.lower() != "fbclid"}
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urllib.parse.urlencode(clean_qs, doseq=True), ""))


def _is_noise_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    low = s.lower()
    noise_exact = {
        "active", "activo", "inactive", "inactivo", "sponsored", "publicidad",
        "platforms", "plataformas", "see ad details", "ver detalles del anuncio",
        "open dropdown", "filters", "filtros", "ad library", "biblioteca de anuncios",
        "about ads and data use", "privacy", "terms", "cookies", "log in", "iniciar sesión",
    }
    if low in noise_exact:
        return True
    if low.startswith(("library id:", "identificador de la biblioteca:", "started running on", "en circulación desde", "![")):
        return True
    if re.match(r"^[-=*_|•·]{2,}$", s):
        return True
    if s.startswith("[") and "](" in s and any(d in low for d in ("facebook.com/ads/library", "l.facebook.com", "about/privacy")):
        return True
    return False


def _extract_platforms(block: str) -> List[str]:
    low = block.lower()
    found: List[str] = []
    for label, norm in (
        ("facebook", "facebook"),
        ("instagram", "instagram"),
        ("audience network", "audience_network"),
        ("messenger", "messenger"),
        ("threads", "threads"),
    ):
        if label in low and norm not in found:
            found.append(norm)
    return found


def parse_meta_ad_library_markdown(
    raw_text: str,
    reference_date: Optional[date] = None,
    min_days: int = 14,
    limit: int = 15,
) -> Dict[str, Any]:
    """Pure-Python deterministic parser turning noisy Meta Ad Library text into a compact brief."""
    if _detect_captcha(raw_text):
        raise RuntimeError("CAPTCHA_OR_ANTIBOT_GATE: Meta Ad Library returned an anti-bot verification gate.")

    ref_date = reference_date or datetime.now(timezone.utc).date()
    matches = list(LIBRARY_ID_RE.finditer(raw_text))
    parsed_ads: List[Dict[str, Any]] = []
    seen_keys: set[str] = set()

    for idx, match in enumerate(matches):
        lib_id = match.group(1)
        start_pos = match.start()
        end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_text)
        block = raw_text[start_pos:end_pos]

        # Started date & days_active
        started_iso: Optional[str] = None
        days_active = 0
        dm = STARTED_DATE_RE.search(block)
        if dm:
            dt = parse_started_date(dm.group(1))
            if dt:
                started_iso = dt.isoformat()
                days_active = max(0, (ref_date - dt).days)

        if days_active < min_days:
            continue

        vm = VARIANTS_RE.search(block)
        variants = int(vm.group(1)) if vm else 1

        dest_url: Optional[str] = None
        for um in URL_RE.finditer(block):
            candidate = _clean_destination_url(um.group(0))
            if candidate:
                dest_url = candidate
                break

        lines = [re.sub(r"\s+", " ", ln).strip() for ln in block.splitlines()]
        clean_lines: List[str] = []
        cta: Optional[str] = None
        for ln in lines:
            low = ln.lower().strip("*_`#> ")
            if low in CTA_LABELS and not cta:
                cta = ln.strip("*_`#> ")
                continue
            if _is_noise_line(ln):
                continue
            # Clean markdown link formatting `[Label](url)` -> `Label`
            ln_clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", ln).strip(" *#>")
            if not ln_clean or len(ln_clean) < 3:
                continue
            clean_lines.append(ln_clean)

        advertiser = clean_lines[0][:90] if clean_lines else "Unknown"
        body_lines = clean_lines[1:] if len(clean_lines) > 1 else []
        hook = body_lines[0][:180] if body_lines else advertiser[:180]
        body = " ".join(body_lines)[:600]

        dedup_sig = hashlib.sha1(f"{advertiser.lower()}::{hook.lower()[:80]}".encode("utf-8")).hexdigest()[:12]
        if lib_id in seen_keys or dedup_sig in seen_keys:
            continue
        seen_keys.add(lib_id)
        seen_keys.add(dedup_sig)

        parsed_ads.append({
            "library_id": lib_id,
            "advertiser": advertiser,
            "started_running_on": started_iso,
            "days_active": days_active,
            "variants_count": variants,
            "platforms": _extract_platforms(block),
            "hook": hook,
            "body": body,
            "cta": cta,
            "destination_url": dest_url,
        })

    parsed_ads.sort(key=lambda item: (item["days_active"], item["variants_count"]), reverse=True)
    capped = parsed_ads[:limit]

    return {
        "schema_version": "1.0",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "raw_chars": len(raw_text),
        "total_library_ids_seen": len(matches),
        "filtered_min_days": min_days,
        "ads_count": len(capped),
        "ads": capped,
    }


def parse_meta_api_json(payload: Dict[str, Any], reference_date: Optional[date] = None, min_days: int = 14, limit: int = 15) -> Dict[str, Any]:
    ref_date = reference_date or datetime.now(timezone.utc).date()
    ads_out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    rows = payload.get("data") or []

    for row in rows:
        lib_id = str(row.get("id") or "").strip()
        if not lib_id or lib_id in seen:
            continue
        seen.add(lib_id)
        start_raw = str(row.get("ad_delivery_start_time") or "")[:10]
        days_active = 0
        if start_raw:
            try:
                days_active = max(0, (ref_date - date.fromisoformat(start_raw)).days)
            except ValueError:
                days_active = 0
        if days_active < min_days:
            continue
        bodies = row.get("ad_creative_bodies") or []
        titles = row.get("ad_creative_link_titles") or []
        body = re.sub(r"\s+", " ", str(bodies[0] if bodies else "")).strip()[:600]
        hook = (body.split(".")[0][:180] if body else str(titles[0] if titles else ""))[:180]
        ads_out.append({
            "library_id": lib_id,
            "advertiser": str(row.get("page_name") or "Unknown")[:90],
            "started_running_on": start_raw or None,
            "days_active": days_active,
            "variants_count": 1,
            "platforms": row.get("publisher_platforms") or [],
            "hook": hook,
            "body": body,
            "cta": str(titles[0])[:60] if titles else None,
            "destination_url": str(row.get("ad_snapshot_url") or "") or None,
        })

    ads_out.sort(key=lambda item: item["days_active"], reverse=True)
    capped = ads_out[:limit]
    return {
        "schema_version": "1.0",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "raw_chars": len(json.dumps(payload)),
        "total_library_ids_seen": len(rows),
        "filtered_min_days": min_days,
        "ads_count": len(capped),
        "ads": capped,
    }


def _fetch_via_meta_api(query: str, country: str, limit: int) -> Optional[Dict[str, Any]]:
    token = _read_key_from_local_configs(("META_AD_LIBRARY_TOKEN", "META_ACCESS_TOKEN"))
    if not token:
        return None
    params = urllib.parse.urlencode({
        "access_token": token,
        "ad_active_status": "ACTIVE",
        "ad_reached_countries": json.dumps([country.upper()]),
        "search_terms": query,
        "fields": "id,ad_delivery_start_time,page_name,ad_creative_bodies,ad_creative_link_titles,publisher_platforms,ad_snapshot_url",
        "limit": max(25, limit * 2),
    })
    req = urllib.request.Request(
        f"https://graph.facebook.com/v21.0/ads_archive?{params}",
        headers={"User-Agent": "ad-library-cli/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _fetch_via_firecrawl(url: str) -> Optional[str]:
    api_key = _read_key_from_local_configs(("FIRECRAWL_API_KEY", "core_FIRECRAWL_API_KEY", "pidev_FIRECRAWL_API_KEY"))
    if not api_key:
        return None
    payload = json.dumps({
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True,
        "waitFor": 3500,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/scrape",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ad-library-cli/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        body = json.loads(resp.read().decode("utf-8", errors="replace"))
        data = body.get("data") or {}
        return data.get("markdown") or ""


def _fetch_via_jina(url: str) -> Optional[str]:
    jina_key = _read_key_from_local_configs(("JINA_API_KEY", "listmonk_JINA_API_KEY", "hermes_JINA_API_KEY"))
    headers = {"User-Agent": "ad-library-cli/1.0", "X-Return-Format": "markdown"}
    if jina_key:
        headers["Authorization"] = f"Bearer {jina_key}"
    req = urllib.request.Request(f"https://r.jina.ai/{url}", headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _synthesize_with_bifrost(brief: Dict[str, Any], query: str, country: str) -> Dict[str, Any]:
    """Optional zero-cost/low-cost synthesis via local Bifrost LLM gateway."""
    bifrost_url = os.environ.get("BIFROST_GATEWAY_URL", "http://bifrost:8080/v1").rstrip("/")
    if not bifrost_url.endswith("/chat/completions"):
        bifrost_url += "/chat/completions"
    vk = _read_key_from_local_configs(("BIFROST_VIRTUAL_KEY", "BIFROST_MASTER_VK"))
    compact_ads = [
        {"advertiser": a["advertiser"], "days": a["days_active"], "hook": a["hook"], "cta": a["cta"]}
        for a in brief.get("ads", [])[:10]
    ]
    prompt = (
        f"Analiza estos anuncios activos de Meta Ad Library ({country}, query='{query}'). "
        "Devuelve SOLO JSON válido con claves: winning_hooks (lista max 5), voc_phrases (lista max 6), "
        "objections_implied (lista max 4), market_gaps (lista max 4).\n"
        f"Datos: {json.dumps(compact_ads, ensure_ascii=False)}"
    )
    headers = {"Content-Type": "application/json"}
    if vk:
        headers["Authorization"] = f"Bearer {vk}"
    body = json.dumps({
        "model": os.environ.get("BIFROST_DEFAULT_MODEL", "gpt-4o-mini"),
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    try:
        req = urllib.request.Request(bifrost_url, data=body, method="POST", headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = json.loads(resp.read().decode("utf-8", errors="replace"))
            content = raw["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception as exc:
        return {"fallback_reason": f"bifrost_unavailable: {type(exc).__name__}", "winning_hooks": [a["hook"] for a in brief.get("ads", [])[:5]]}


def compute_brief_diff(prev_brief: Dict[str, Any], curr_brief: Dict[str, Any]) -> Dict[str, Any]:
    prev_ids = {a["library_id"] for a in prev_brief.get("ads", [])}
    curr_ids = {a["library_id"] for a in curr_brief.get("ads", [])}
    new_winners = [a for a in curr_brief.get("ads", []) if a["library_id"] not in prev_ids]
    retired = [a for a in prev_brief.get("ads", []) if a["library_id"] not in curr_ids]
    return {
        "new_winners_count": len(new_winners),
        "retired_count": len(retired),
        "new_winners": new_winners,
        "retired_library_ids": [a["library_id"] for a in retired],
    }


def _emit_output(brief: Dict[str, Any], out_path: Optional[Path]) -> None:
    encoded = json.dumps(brief, indent=2, ensure_ascii=False) + "\n"
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(encoded, encoding="utf-8")
        print(f"✅ ad-library brief saved ({len(encoded)} bytes, {brief.get('ads_count', 0)} ads) -> {out_path}")
    else:
        print(encoded)


def run_tests() -> int:
    print("============================================================")
    print("  🧪 RUNNING AD-LIBRARY CLI UNIT TESTS")
    print("============================================================")
    noise_countries = "\n".join([f"[Country {i}](https://www.facebook.com/ads/library/?country=C{i})" for i in range(180)])
    sample_md = f"""
Meta Ad Library
{noise_countries}

Library ID: 9988776655443322
Started running on Oct 10, 2026
Platforms
Facebook
Instagram
Active
Studio Norte
Deja de competir por tarifa por hora cuando tu criterio vale diez veces más.
Instala tu sistema comercial propio en menos de 15 días sin inflar nómina fija.
12 ads use this creative and text
Learn More
https://l.facebook.com/l.php?u=https%3A%2F%2Fstudionorte.example.com%2Fdiagnostico%3Ffbclid%3Dabc123

Library ID: 1122334455667788
En circulación desde el 24 nov 2026
Platforms
Instagram
Activo
Anunciante Reciente
Anuncio nuevo de hace solo 3 días que debe ser filtrado por min_days=14.
Más información
https://reciente.example.com/landing

Library ID: 4455667788990011
Started running on Nov 1, 2026
Platforms
Facebook
Active
Marca Clara CO
Construye una oferta única imposible de comparar con propuestas genéricas.
Más información
https://marcaclara.example.com/reto
"""
    ref = date(2026, 11, 27)
    brief = parse_meta_ad_library_markdown(sample_md, reference_date=ref, min_days=14, limit=10)
    assert brief["ads_count"] == 2, f"Expected 2 ads >=14d, got {brief['ads_count']}"
    assert brief["ads"][0]["library_id"] == "9988776655443322", "Expected longest running ad first"
    assert brief["ads"][0]["days_active"] == 48, f"Expected 48 days, got {brief['ads'][0]['days_active']}"
    assert brief["ads"][0]["variants_count"] == 12
    assert brief["ads"][0]["destination_url"] == "https://studionorte.example.com/diagnostico"
    assert brief["ads"][1]["days_active"] == 26
    compact_size = len(json.dumps(brief, ensure_ascii=False))
    assert compact_size < 3072, f"Expected <3KB compact brief, got {compact_size} bytes"

    # Test diff
    prev = {"ads": [brief["ads"][1]]}
    diff = compute_brief_diff(prev, brief)
    assert diff["new_winners_count"] == 1
    assert diff["new_winners"][0]["library_id"] == "9988776655443322"

    # Test Meta API JSON parser
    api_brief = parse_meta_api_json({
        "data": [{
            "id": "777888999",
            "ad_delivery_start_time": "2026-11-01T10:00:00+0000",
            "page_name": "Consultora Demo",
            "ad_creative_bodies": ["Cobra por resultados y sistema, no por horas sueltas."],
            "ad_creative_link_titles": ["Agenda diagnóstico"],
            "publisher_platforms": ["facebook", "instagram"],
        }]
    }, reference_date=ref, min_days=14, limit=10)
    assert api_brief["ads_count"] == 1
    assert api_brief["ads"][0]["days_active"] == 26

    # Test captcha detection
    try:
        parse_meta_ad_library_markdown("Please verify you are human to continue with Security Check.")
        assert False, "Expected CAPTCHA_OR_ANTIBOT_GATE error"
    except RuntimeError as exc:
        assert "CAPTCHA_OR_ANTIBOT_GATE" in str(exc)

    print(f"✓ Parsed 2 winning ads cleanly, stripped {len(sample_md)} chars -> {compact_size} bytes JSON.")
    print("✓ Verified days_active, min-days filter, URL fbclid cleanup, diff, Meta API JSON, and CAPTCHA guard.")
    print("🎉 ALL AD-LIBRARY UNIT TESTS PASSED (Exit 0)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="ad-library: Token-Frugal Meta Ad Library Extractor & Normalizer")
    parser.add_argument("--test", action="store_true", help="Run offline unit tests")
    sub = parser.add_subparsers(dest="subcommand")

    p_fetch = sub.add_parser("fetch", help="Fetch & clean Meta Ad Library ads for a query")
    p_fetch.add_argument("--query", "-q", required=True)
    p_fetch.add_argument("--country", "-c", default="CO")
    p_fetch.add_argument("--min-days", type=int, default=14)
    p_fetch.add_argument("--limit", type=int, default=15)
    p_fetch.add_argument("--provider", choices=["auto", "meta-api", "firecrawl", "jina", "file"], default="auto")
    p_fetch.add_argument("--input-file", type=Path, help="Raw dump when --provider file")
    p_fetch.add_argument("--synth-via", choices=["none", "bifrost"], default="none")
    p_fetch.add_argument("--out", "-o", type=Path)

    p_parse = sub.add_parser("parse", help="Parse raw Meta Ad Library markdown/HTML from file or stdin (0 LLM tokens)")
    p_parse.add_argument("--input-file", "-i", type=Path)
    p_parse.add_argument("--query", "-q", default="")
    p_parse.add_argument("--country", "-c", default="CO")
    p_parse.add_argument("--min-days", type=int, default=14)
    p_parse.add_argument("--limit", type=int, default=15)
    p_parse.add_argument("--synth-via", choices=["none", "bifrost"], default="none")
    p_parse.add_argument("--out", "-o", type=Path)

    p_diff = sub.add_parser("diff", help="Compare two ad-library briefs to find newly winning ads")
    p_diff.add_argument("--prev", required=True, type=Path)
    p_diff.add_argument("--curr", required=True, type=Path)
    p_diff.add_argument("--out", "-o", type=Path)

    args = parser.parse_args()
    if args.test:
        return run_tests()

    if args.subcommand == "parse":
        raw = args.input_file.read_text(encoding="utf-8", errors="replace") if args.input_file else sys.stdin.read()
        brief = parse_meta_ad_library_markdown(raw, min_days=args.min_days, limit=args.limit)
        brief["query"] = args.query
        brief["country"] = args.country.upper()
        brief["provider"] = "file_or_stdin"
        if args.synth_via == "bifrost":
            brief["synthesis"] = _synthesize_with_bifrost(brief, args.query, args.country)
        _emit_output(brief, args.out)
        return 0

    if args.subcommand == "fetch":
        url = build_ad_library_url(args.query, country=args.country)
        brief: Optional[Dict[str, Any]] = None
        used_provider = ""
        errors: List[str] = []

        if args.provider == "file":
            if not args.input_file or not args.input_file.is_file():
                print("❌ --provider file requires existing --input-file", file=sys.stderr)
                return 1
            brief = parse_meta_ad_library_markdown(
                args.input_file.read_text(encoding="utf-8", errors="replace"),
                min_days=args.min_days,
                limit=args.limit,
            )
            used_provider = "file"
        else:
            providers = [args.provider] if args.provider != "auto" else ["meta-api", "firecrawl", "jina"]
            for prov in providers:
                try:
                    if prov == "meta-api":
                        api_json = _fetch_via_meta_api(args.query, args.country, args.limit)
                        if api_json is not None:
                            brief = parse_meta_api_json(api_json, min_days=args.min_days, limit=args.limit)
                            used_provider = "meta-api"
                            break
                    elif prov == "firecrawl":
                        md = _fetch_via_firecrawl(url)
                        if md:
                            brief = parse_meta_ad_library_markdown(md, min_days=args.min_days, limit=args.limit)
                            used_provider = "firecrawl"
                            break
                    elif prov == "jina":
                        md = _fetch_via_jina(url)
                        if md:
                            brief = parse_meta_ad_library_markdown(md, min_days=args.min_days, limit=args.limit)
                            used_provider = "jina"
                            break
                except RuntimeError as exc:
                    if "CAPTCHA_OR_ANTIBOT_GATE" in str(exc):
                        print(f"❌ Blocked by Meta Ad Library verification gate ({prov}): {exc}", file=sys.stderr)
                        return 2
                    errors.append(f"{prov}: {exc}")
                except Exception as exc:
                    errors.append(f"{prov}: {type(exc).__name__}: {exc}")

        if brief is None:
            print(f"❌ Unable to fetch Meta Ad Library via providers ({', '.join(errors) or 'no keys configured'}). Pass --input-file with `ad-library parse`.", file=sys.stderr)
            return 1

        brief["query"] = args.query
        brief["country"] = args.country.upper()
        brief["library_url"] = url
        brief["provider"] = used_provider
        if args.synth_via == "bifrost":
            brief["synthesis"] = _synthesize_with_bifrost(brief, args.query, args.country)
        _emit_output(brief, args.out)
        return 0

    if args.subcommand == "diff":
        prev = json.loads(args.prev.read_text(encoding="utf-8"))
        curr = json.loads(args.curr.read_text(encoding="utf-8"))
        diff = compute_brief_diff(prev, curr)
        _emit_output(diff, args.out)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
