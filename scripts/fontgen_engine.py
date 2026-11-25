#!/usr/bin/env python3
"""
fontgen_engine.py — Sovereign Agnostic Typographic Engine & Art Direction Matrix (v4.0).
Multi-Axis Oráculo 15-Shards + Vertical Context + Live Envato Sourcing + Taste/Impeccable Rules.
Zero-Hallucination Design Synthesis | Anti-CLS Calibration | Zero Phantom Directories.

Architectural Invariants:
1. Respects design-taste-frontend (§4.1 Serif Discipline) & impeccable craft floor:
   - Never uses Fraunces, Instrument Serif, or Inter as defaults.
   - B2B / Systems / Consulting / AI verticals default to clean architectural Sans displays
     with at most one high-contrast sharp editorial serif alternative (never wedding scripts).
2. Ingests ALL available inputs jointly: client_dumps_15_shards.json + astrobranding_<brand>.md + verticals/<v>.json.
3. Live Envato search deduplicates UUIDs, filters noisy genres (wedding/horror/graffiti/calligraphy on B2B),
   verifies elements.envato.com/font-preview.svg previewability, and supports --seed exploration.
4. Never creates phantom top-level brand directories unless --create-brand-dirs is explicitly passed.
"""

import argparse
import json
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def _extract_uuid(url: str) -> str:
    m = re.search(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", str(url or ""), re.IGNORECASE)
    return m.group(1).lower() if m else ""


NOISE_BLOCKLIST_ARCHITECTURAL = {
    "wedding", "bridal", "romantic", "love", "heart", "horror", "scary", "gothic", "zombie",
    "halloween", "graffiti", "cartoon", "comic", "kids", "cute", "brush", "calligraphy",
    "script", "signature", "tattoo", "lavish", "swash", "flourish", "cursive", "handwritten",
    "retro", "vintage", "groovy", "psychedelic", "metal", "blood", "spooky",
}


# -----------------------------------------------------------------------------
# Verified Curated Offline Catalog (app.envato.com/fonts/{uuid})
# -----------------------------------------------------------------------------

ENVATO_VERIFIED_CATALOG: Dict[str, Dict[str, Any]] = {
    "swiss_neo_grotesque": {
        "family": "Monolith",
        "item_uuid": "a0b16453-79c9-4c3a-aac9-1a5774943744",
        "url": "https://app.envato.com/fonts/a0b16453-79c9-4c3a-aac9-1a5774943744",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=swiss+neo+grotesque+sans",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Swiss Architectural Neo-Grotesque",
        "description": "Precision multi-weight Swiss neo-grotesque engineered for technical and corporate identities."
    },
    "minimalist_arch_sans": {
        "family": "Casano",
        "item_uuid": "8906544f-ecc5-44cd-985b-2e43558edcb1",
        "url": "https://app.envato.com/fonts/8906544f-ecc5-44cd-985b-2e43558edcb1",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=minimalist+architectural+sans+serif",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Minimalist Architectural Sans",
        "description": "Crisp minimalist geometric sans with balanced proportions for sovereign brand systems."
    },
    "futuristic_arch_sans": {
        "family": "Arteon",
        "item_uuid": "9675e800-0193-40bc-b3fa-edfc5876bfee",
        "url": "https://app.envato.com/fonts/9675e800-0193-40bc-b3fa-edfc5876bfee",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=modern+architectural+sans",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Architectural Geometric Sans",
        "description": "Architectural futuristic display sans crafted for executive and technology authorities."
    },
    "modern_tech_grotesk": {
        "family": "Qobar",
        "item_uuid": "5f52efb4-f726-4925-bb0b-8946fb95f70b",
        "url": "https://app.envato.com/fonts/5f52efb4-f726-4925-bb0b-8946fb95f70b",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=modern+geometric+grotesque+display",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Modern Structural Grotesk",
        "description": "Structured modern sans serif tailored for B2B systems and editorial headlines."
    },
    "sharp_editorial_serif": {
        "family": "Blure",
        "item_uuid": "b193f130-0d7b-452f-945a-d4df3a56bda4",
        "url": "https://app.envato.com/fonts/b193f130-0d7b-452f-945a-d4df3a56bda4",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=editorial+high+contrast+serif",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Sharp High-Contrast Editorial Serif",
        "description": "Razor-clean high-contrast editorial serif without calligraphic ornamentation."
    },
    "modern_grotesk_stencil": {
        "family": "Akmorn Grotesque",
        "item_uuid": "c1ffdc86-c80d-45ec-92ae-6c69615d1086",
        "url": "https://app.envato.com/fonts/c1ffdc86-c80d-45ec-92ae-6c69615d1086",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=modern+grotesque+sans",
        "weights": ["400", "600", "700", "800"],
        "category": "sans",
        "style": "Industrial Neo-Grotesque",
        "description": "Modular precision neo-grotesque with crisp angular apertures."
    },
    "architectural_emblem": {
        "family": "Architecture",
        "item_uuid": "3632bd0b-4f96-42b7-b4ce-39da5c747057",
        "url": "https://app.envato.com/fonts/3632bd0b-4f96-42b7-b4ce-39da5c747057",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=modern+architectural+emblem+logo+font",
        "weights": ["600", "700", "900"],
        "category": "display",
        "style": "Architectural Emblem Display",
        "description": "Structured emblem display font designed for geometric brand seals and wordmarks."
    },
    "monogram_holder": {
        "family": "Monogram Holder",
        "item_uuid": "b072395d-990e-4637-a1ca-2c8b0355aed0",
        "url": "https://app.envato.com/fonts/b072395d-990e-4637-a1ca-2c8b0355aed0",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=monogram+display+font",
        "weights": ["700", "900"],
        "category": "display",
        "style": "Interlocking Geometric Monogram",
        "description": "Monogram typeface engineered for clean two-letter corporate marks."
    },
    "high_contrast_didone": {
        "family": "Taillevere",
        "item_uuid": "9dee7e7e-b2ad-42a9-8092-f674dc4bd330",
        "url": "https://app.envato.com/fonts/9dee7e7e-b2ad-42a9-8092-f674dc4bd330",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=didone+luxury+serif",
        "weights": ["400", "500", "700"],
        "category": "serif",
        "style": "Modern Didone Editorial",
        "description": "High-contrast modern Didone with restrained vertical stress."
    },
    "architectural_serif": {
        "family": "Domani",
        "item_uuid": "1de94cfa-3ac9-4fd1-b5b2-113405506be3",
        "url": "https://app.envato.com/fonts/1de94cfa-3ac9-4fd1-b5b2-113405506be3",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=architectural+serif",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Architectural Inscriptional Serif",
        "description": "Monumental carved serif rooted in architectural proportions."
    },
}

GOOGLE_FONTS_CATALOG: Dict[str, Dict[str, Any]] = {
    "plus_jakarta_sans": {
        "family": "Plus Jakarta Sans",
        "url": "https://fonts.google.com/specimen/Plus+Jakarta+Sans",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap",
        "variable_axes": "ital,wght@0..1,200..800",
        "weights": ["200", "300", "400", "500", "600", "700", "800"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "98.5%", "ascent": "92.0%", "descent": "24.0%", "line_gap": "0%"}
    },
    "dm_sans": {
        "family": "DM Sans",
        "url": "https://fonts.google.com/specimen/DM+Sans",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,200..800;1,9..40,200..800&display=swap",
        "variable_axes": "ital,opsz,wght@0..1,9..40,200..800",
        "weights": ["200", "300", "400", "500", "600", "700", "800"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "99.0%", "ascent": "94.0%", "descent": "23.0%", "line_gap": "0%"}
    },
    "instrument_sans": {
        "family": "Instrument Sans",
        "url": "https://fonts.google.com/specimen/Instrument+Sans",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Instrument+Sans:ital,wdth,wght@0,75..100,400..700;1,75..100,400..700&display=swap",
        "variable_axes": "ital,wdth,wght@0..1,75..100,400..700",
        "weights": ["400", "500", "600", "700"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "99.0%", "ascent": "94.0%", "descent": "23.0%", "line_gap": "0%"}
    },
    "space_grotesk": {
        "family": "Space Grotesk",
        "url": "https://fonts.google.com/specimen/Space+Grotesk",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap",
        "variable_axes": "wght@300..700",
        "weights": ["300", "400", "500", "600", "700"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "98.0%", "ascent": "93.0%", "descent": "24.0%", "line_gap": "0%"}
    },
    "bricolage_grotesque": {
        "family": "Bricolage Grotesque",
        "url": "https://fonts.google.com/specimen/Bricolage+Grotesque",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,200..800&display=swap",
        "variable_axes": "opsz,wdth,wght@12..96,75..100,200..800",
        "weights": ["200", "300", "400", "500", "600", "700", "800"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "97.5%", "ascent": "95.0%", "descent": "24.0%", "line_gap": "0%"}
    },
    "manrope": {
        "family": "Manrope",
        "url": "https://fonts.google.com/specimen/Manrope",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Manrope:wght@200..800&display=swap",
        "variable_axes": "wght@200..800",
        "weights": ["200", "300", "400", "500", "600", "700", "800"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "100.0%", "ascent": "95.0%", "descent": "24.0%", "line_gap": "0%"}
    },
    "urbanist": {
        "family": "Urbanist",
        "url": "https://fonts.google.com/specimen/Urbanist",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Urbanist:ital,wght@0,100..900;1,100..900&display=swap",
        "variable_axes": "ital,wght@0..1,100..900",
        "weights": ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "99.5%", "ascent": "93.0%", "descent": "22.0%", "line_gap": "0%"}
    },
    "newsreader": {
        "family": "Newsreader",
        "url": "https://fonts.google.com/specimen/Newsreader",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&display=swap",
        "variable_axes": "ital,opsz,wght@0..1,6..72,200..800",
        "weights": ["200", "300", "400", "500", "600", "700", "800"],
        "category": "serif",
        "cls": {"fallback": "Times New Roman", "size_adjust": "98.0%", "ascent": "93.0%", "descent": "25.0%", "line_gap": "0%"}
    },
    "spectral": {
        "family": "Spectral",
        "url": "https://fonts.google.com/specimen/Spectral",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,200..800;1,200..800&display=swap",
        "variable_axes": "ital,wght@0..1,200..800",
        "weights": ["200", "300", "400", "500", "600", "700", "800"],
        "category": "serif",
        "cls": {"fallback": "Times New Roman", "size_adjust": "99.5%", "ascent": "94.5%", "descent": "24.0%", "line_gap": "0%"}
    },
}

SIGN_NORMALIZATION: Dict[str, str] = {
    "aries": "Aries",
    "taurus": "Taurus", "tauro": "Taurus",
    "gemini": "Gemini", "geminis": "Gemini", "géminis": "Gemini",
    "cancer": "Cancer", "cáncer": "Cancer",
    "leo": "Leo",
    "virgo": "Virgo",
    "libra": "Libra",
    "scorpio": "Scorpio", "escorpio": "Scorpio",
    "sagittarius": "Sagittarius", "sagitario": "Sagittarius",
    "capricorn": "Capricorn", "capricornio": "Capricorn",
    "aquarius": "Aquarius", "acuario": "Aquarius",
    "pisces": "Pisces", "piscis": "Pisces",
}

ZODIAC_ELEMENTS = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
}

ZODIAC_MODALITIES = {
    "Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricorn": "Cardinal",
    "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed",
    "Gemini": "Mutable", "Virgo": "Mutable", "Sagittarius": "Mutable", "Pisces": "Mutable"
}

MODALITY_SCALE_RATIOS = {
    "Cardinal": 1.618,
    "Fixed": 1.333,
    "Mutable": 1.250
}

BAZI_MODULATIONS = {
    "Jia": {"element": "Wood", "polarity": "Yang", "tracking_em": -0.02},
    "Yi": {"element": "Wood", "polarity": "Yin", "tracking_em": -0.01},
    "Bing": {"element": "Fire", "polarity": "Yang", "tracking_em": -0.01},
    "Ding": {"element": "Fire", "polarity": "Yin", "tracking_em": 0.00},
    "Wu": {"element": "Earth", "polarity": "Yang", "tracking_em": -0.015},
    "Ji": {"element": "Earth", "polarity": "Yin", "tracking_em": 0.00},
    "Geng": {"element": "Metal", "polarity": "Yang", "tracking_em": -0.025},
    "Xin": {"element": "Metal", "polarity": "Yin", "tracking_em": 0.01},
    "Ren": {"element": "Water", "polarity": "Yang", "tracking_em": -0.01},
    "Gui": {"element": "Water", "polarity": "Yin", "tracking_em": 0.01},
}

NAKSHATRA_FEATURES = {
    "Chitra": {"feature": "dlig 1, calt 1", "lord": "Mars", "accent_archetype": "architectural_emblem"},
    "Ashwini": {"feature": "dlig 1, ss01 1", "lord": "Ketu", "accent_archetype": "monogram_holder"},
    "Rohini": {"feature": "calt 1, liga 1", "lord": "Moon", "accent_archetype": "high_contrast_didone"},
    "Mrigashira": {"feature": "ss02 1", "lord": "Mars", "accent_archetype": "architectural_emblem"},
    "Hasta": {"feature": "ss01 1", "lord": "Moon", "accent_archetype": "minimalist_arch_sans"},
    "Swati": {"feature": "liga 1", "lord": "Rahu", "accent_archetype": "swiss_neo_grotesque"},
    "Shravana": {"feature": "liga 1, calt 1", "lord": "Moon", "accent_archetype": "minimalist_arch_sans"},
    "Revati": {"feature": "calt 1, liga 1", "lord": "Mercury", "accent_archetype": "sharp_editorial_serif"},
}


def normalize_zodiac_sign(raw_sign: str) -> str:
    s = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚ]", "", str(raw_sign or "").strip()).lower()
    return SIGN_NORMALIZATION.get(s, str(raw_sign or "").strip().title())


def find_localstorage_roots() -> List[Path]:
    roots: List[Path] = []
    env_path = os.getenv("LOCAL_STORAGE_PATH")
    if env_path and Path(env_path).exists():
        p = Path(env_path).resolve()
        if p not in roots:
            roots.append(p)
        if p.name in ("hermes", "paperclip", "engram", "pidev") and p.parent.exists() and p.parent.resolve() not in roots:
            roots.append(p.parent.resolve())
    for candidate in (Path("/mnt/localstorage"), Path("/var/www/localstorage")):
        if candidate.exists():
            res = candidate.resolve()
            if res not in roots:
                roots.append(res)
    return roots


class FontgenEngine:
    """
    Sovereign Agnostic Typographic Engine (v4.0).
    Combines Oráculo 15-Shards, Brief Semiótico, Vertical Domain, and Taste/Impeccable discipline.
    """

    def __init__(
        self,
        brand: str,
        shards_path: Optional[Path] = None,
        brief_path: Optional[Path] = None,
        vertical_json_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        use_live_search: bool = True,
        allow_default: bool = False,
        override_params: Optional[Dict[str, Any]] = None,
        create_brand_dirs: bool = False,
        verify_svg_preview: bool = True,
        style_profile: str = "auto",
        seed: int = 0,
    ):
        self.brand_raw = brand.strip()
        self.brand_upper = self.brand_raw.upper()
        self.brand_lower = self.brand_raw.lower()
        self.shards_path = Path(shards_path).resolve() if shards_path else None
        self.brief_path = Path(brief_path).resolve() if brief_path else None
        self.vertical_json_path = Path(vertical_json_path).resolve() if vertical_json_path else None
        self.output_dir = Path(output_dir).resolve() if output_dir else None
        self.use_live_search = use_live_search
        self.allow_default = allow_default
        self.override_params = override_params or {}
        self.create_brand_dirs = create_brand_dirs
        self.verify_svg_preview = verify_svg_preview
        self.style_profile = style_profile
        self.seed = max(0, int(seed))
        self.used_families: Set[str] = set()
        self.used_uuids: Set[str] = set()

        self.diag_dir = Path(f"/var/www/baiosfera/ASTROLOGÍA/DIAG/{self.brand_upper}")
        self.project_dev_dir = Path(f"/var/www/baiosfera/PROYECTOS/{self.brand_upper}/dev")

    def _discover_search_dirs(self) -> List[Path]:
        dirs: List[Path] = []
        curr = Path.cwd().resolve()
        for p in [curr] + list(curr.parents)[:4]:
            if p.exists() and p not in dirs:
                dirs.append(p)
            for sub in (p / "dev", p / "dev" / "_shared", p / "_shared", p / "brand"):
                if sub.exists() and sub not in dirs:
                    dirs.append(sub)
        for ls_root in find_localstorage_roots():
            if ls_root not in dirs:
                dirs.append(ls_root)
            try:
                for child in ls_root.iterdir():
                    if child.is_dir() and not child.name.startswith("."):
                        for sub in (
                            child / "dev",
                            child / "dev" / "workspaces" / self.brand_lower / "brand",
                            child / "workspaces" / self.brand_lower / "brand",
                        ):
                            if sub.exists() and sub not in dirs:
                                dirs.append(sub)
            except Exception:
                pass
        for d in (self.diag_dir, self.project_dev_dir):
            if d.exists() and d not in dirs:
                dirs.append(d)
        return dirs

    def _clean_family_name(self, raw_title: str) -> str:
        if not raw_title:
            return "Untitled Font"
        first_part = re.split(r"\s*[-–—|:]\s*", raw_title)[0].strip()
        first_part = re.split(r",", first_part)[0].strip()
        first_part = re.sub(r"&amp;", "&", first_part)
        cleaned = re.sub(
            r"\b(Font|Typeface|Family|Display|Serif|Sans|Grotesk|Grotesque|Script|Calligraphy|Vintage|Modern|Bold|Minimalist)\b",
            "", first_part, flags=re.IGNORECASE,
        ).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned.title() if len(cleaned) >= 2 else first_part.strip().title()

    def _is_noisy_title(self, raw_title: str, allow_script: bool = False) -> bool:
        words = set(re.findall(r"[a-z]+", raw_title.lower()))
        blocked = set(NOISE_BLOCKLIST_ARCHITECTURAL)
        if allow_script:
            blocked -= {"calligraphy", "script", "signature", "flourish"}
        return bool(words.intersection(blocked))

    def _is_previewable_uuid(self, item_uuid: str) -> bool:
        if not item_uuid:
            return False
        if not self.verify_svg_preview:
            return True
        svg_url = f"https://elements.envato.com/font-preview.svg?itemUuid={urllib.parse.quote(item_uuid)}&text=BRAND&typed=1"
        try:
            req = urllib.request.Request(
                svg_url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "Referer": "https://elements.envato.com/"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read(200).decode("utf-8", errors="ignore")
                return resp.status == 200 and "<svg" in body.lower()
        except Exception:
            return False

    def _search_live_envato_fonts(
        self,
        query: str,
        category: str = "sans",
        default_weights: Optional[List[str]] = None,
        allow_script: bool = False,
    ) -> Optional[Dict[str, Any]]:
        if not self.use_live_search:
            return None
        search_url = f"https://app.envato.com/search?itemType=fonts&term={urllib.parse.quote_plus(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                html_text = resp.read().decode("utf-8", errors="ignore")

            chunks = re.findall(r'<a[^>]+data-analytics-item_id="[^"]+"[^>]*>', html_text)
            seen_in_page: Set[str] = set()
            valid_hits: List[Dict[str, Any]] = []
            for c in chunks[:30]:
                m_id = re.search(r'data-analytics-item_id="([^"]+)"', c)
                m_title = re.search(r'data-analytics-item_title="([^"]+)"', c)
                m_author = re.search(r'data-analytics-item_author="([^"]+)"', c)
                if not (m_id and m_title):
                    continue
                fid = m_id.group(1).strip().lower()
                if fid in seen_in_page or fid in self.used_uuids:
                    continue
                seen_in_page.add(fid)

                title = m_title.group(1).strip()
                if self._is_noisy_title(title, allow_script=allow_script):
                    continue
                family = self._clean_family_name(title)
                if family.lower() in [f.lower() for f in self.used_families]:
                    continue
                if not self._is_previewable_uuid(fid):
                    continue

                author = m_author.group(1).strip() if m_author else "Envato Author"
                valid_hits.append({
                    "family": family,
                    "item_uuid": fid,
                    "url": f"https://app.envato.com/fonts/{fid}",
                    "search_url": search_url,
                    "weights": default_weights or ["400", "600", "700"],
                    "category": category,
                    "style": f"Live Envato Sourcing ({query})",
                    "description": f"{title} by {author} on Envato Elements Pro."
                })
                if len(valid_hits) >= 4:
                    break

            if valid_hits:
                pick = valid_hits[self.seed % len(valid_hits)]
                self.used_families.add(pick["family"])
                self.used_uuids.add(pick["item_uuid"])
                return pick
        except Exception:
            pass
        return None

    def _get_fallback_envato_font(self, archetype_key: str) -> Dict[str, Any]:
        candidate = ENVATO_VERIFIED_CATALOG.get(archetype_key)
        if candidate and candidate["family"].lower() not in [f.lower() for f in self.used_families]:
            self.used_families.add(candidate["family"])
            self.used_uuids.add(candidate["item_uuid"])
            return candidate
        for v in ENVATO_VERIFIED_CATALOG.values():
            if v["family"].lower() not in [f.lower() for f in self.used_families]:
                self.used_families.add(v["family"])
                self.used_uuids.add(v["item_uuid"])
                return v
        return ENVATO_VERIFIED_CATALOG["swiss_neo_grotesque"]

    def resolve_inputs(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "sun_sign": "", "mc_sign": "", "sidereal_sun_sign": "", "sidereal_mc_sign": "",
            "sidereal_asc_sign": "", "day_master": "", "bazi_month_element": "",
            "yong_shen": "", "nakshatra": "", "nakshatra_lord": "", "shadbala_dominant": "",
            "dominant_element": "", "style_profile": self.style_profile, "vertical_domain": "general",
            "sources_used": [],
        }

        if self.override_params:
            for k in ("sun_sign", "mc_sign", "day_master", "nakshatra", "dominant_element"):
                if self.override_params.get(k):
                    data[k] = str(self.override_params[k]).strip()
            if data["sun_sign"]:
                data["sun_sign"] = normalize_zodiac_sign(data["sun_sign"])
            if data["mc_sign"]:
                data["mc_sign"] = normalize_zodiac_sign(data["mc_sign"])
            if data["sun_sign"] and not data["dominant_element"]:
                data["dominant_element"] = ZODIAC_ELEMENTS.get(data["sun_sign"], "Earth")
            if data["sun_sign"] and data["mc_sign"]:
                data["day_master"] = data["day_master"] or "Wu"
                data["nakshatra"] = data["nakshatra"] or "Ashwini"
                data["sources_used"].append("cli_override")

        # 1. Read Oráculo 15-Shards first if present
        shards_target = self.shards_path
        if not shards_target:
            for p in (
                self.diag_dir / "raw" / "json" / "dumps" / "client_dumps_15_shards.json",
                self.diag_dir / "dumps" / "client_dumps_15_shards.json",
                self.project_dev_dir / "client_dumps_15_shards.json",
            ):
                if p.exists():
                    shards_target = p
                    break

        if shards_target and shards_target.exists():
            try:
                content = json.loads(shards_target.read_text(encoding="utf-8"))
                data["sources_used"].append(f"shards:{shards_target.name}")
                s1 = content.get("shard_01", {}).get("data", {})
                s2 = content.get("shard_02", {}).get("data", {})
                s3 = content.get("shard_03", {}).get("data", {})
                s4 = content.get("shard_04", {}).get("data", {})
                tripod = s1.get("tripod_of_iron", {})
                if not data["sun_sign"] and tripod.get("sun", {}).get("sign"):
                    data["sun_sign"] = normalize_zodiac_sign(tripod["sun"]["sign"])
                if not data["mc_sign"] and tripod.get("midheaven_house_10", {}).get("sign"):
                    data["mc_sign"] = normalize_zodiac_sign(tripod["midheaven_house_10"]["sign"])
                if not data["dominant_element"] and s1.get("arroyo_elements", {}).get("dominant_element"):
                    data["dominant_element"] = str(s1["arroyo_elements"]["dominant_element"])

                fb = s2.get("fagan_bradley", {})
                if fb.get("midheaven", {}).get("sign"):
                    data["sidereal_mc_sign"] = normalize_zodiac_sign(fb["midheaven"]["sign"])
                if fb.get("ascendant", {}).get("sign"):
                    data["sidereal_asc_sign"] = normalize_zodiac_sign(fb["ascendant"]["sign"])

                sh = s3.get("shadbala", {})
                if sh.get("dominant_planet"):
                    data["shadbala_dominant"] = str(sh["dominant_planet"])
                nk = s3.get("nakshatra", {})
                if not data["nakshatra"] and nk.get("name"):
                    data["nakshatra"] = nk["name"].split()[0]
                if nk.get("lord") or nk.get("ruler"):
                    data["nakshatra_lord"] = str(nk.get("lord") or nk.get("ruler"))

                dm = s4.get("day_master", {})
                if not data["day_master"] and dm.get("name"):
                    data["day_master"] = dm["name"].split()[0]
                fp = s4.get("four_pillars", {})
                if fp.get("month", {}).get("element"):
                    data["bazi_month_element"] = str(fp["month"]["element"])
                ys = s4.get("yong_shen", {})
                if ys.get("element"):
                    data["yong_shen"] = str(ys["element"]).split()[0]
            except Exception:
                pass

        # 2. Enrich from astrobranding_<brand>.md brief if available
        candidates: List[Path] = []
        if self.brief_path and self.brief_path.exists():
            candidates.append(self.brief_path)
        for sdir in self._discover_search_dirs():
            if sdir.exists():
                for cand in (sdir / f"astrobranding_{self.brand_lower}.md", sdir / "raw" / "llm" / f"astrobranding_{self.brand_lower}.md"):
                    if cand.exists() and cand not in candidates:
                        candidates.append(cand)

        for c in candidates:
            if not c.is_file():
                continue
            try:
                txt = c.read_text(encoding="utf-8", errors="replace")
                m_sun = re.search(r"\|\s*\*\*Sol Natal\*\*\s*\|\s*\*\*([A-Za-zÁÉÍÓÚáéíóú]+)", txt) or re.search(r"(?:Sun Natal|Sol Natal|Sol)[\s:\*|]+(?:en\s+\*\*)?([A-Za-zÁÉÍÓÚáéíóú]+)", txt, re.IGNORECASE)
                m_mc = re.search(r"\|\s*\*\*Medio Cielo[^*]*\*\*\s*\|\s*\*\*([A-Za-zÁÉÍÓÚáéíóú]+)", txt) or re.search(r"(?:Midheaven|Medio Cielo)[\s:\*|]+(?:en\s+\*\*)?([A-Za-zÁÉÍÓÚáéíóú]+)", txt, re.IGNORECASE)
                m_nak = re.search(r"\*\*Nakshatra[^:\n]*:\*\*\s*([A-Za-z]+)", txt)
                m_dm = re.search(r"\*\*Day Master:\*\*\s*([A-Za-z]+)", txt)
                if not data["sun_sign"] and m_sun:
                    data["sun_sign"] = normalize_zodiac_sign(m_sun.group(1))
                if not data["mc_sign"] and m_mc:
                    data["mc_sign"] = normalize_zodiac_sign(m_mc.group(1))
                if not data["nakshatra"] and m_nak:
                    data["nakshatra"] = m_nak.group(1).strip()
                if not data["day_master"] and m_dm:
                    data["day_master"] = m_dm.group(1).strip()
                if f"brief:{c.name}" not in data["sources_used"]:
                    data["sources_used"].append(f"brief:{c.name}")
                break
            except Exception:
                pass

        # 3. Read vertical JSON context to infer real commercial aesthetic profile
        if self.vertical_json_path and self.vertical_json_path.is_file():
            try:
                vraw = self.vertical_json_path.read_text(encoding="utf-8")
                vblob = vraw.lower()
                data["sources_used"].append(f"vertical:{self.vertical_json_path.name}")
                if any(k in vblob for k in ("consultor", "b2b", "financier", "abogado", "médico", "unipersonal", "arquitect", "sistemas", "saas", "ia")):
                    data["vertical_domain"] = "b2b_consulting_systems"
                    if data["style_profile"] == "auto":
                        data["style_profile"] = "architectural_b2b"
            except Exception:
                pass

        if data["style_profile"] == "auto":
            if data["shadbala_dominant"] in ("Sun", "Saturn", "Mercury") or data["bazi_month_element"] == "Metal":
                data["style_profile"] = "architectural_b2b"
            else:
                data["style_profile"] = "editorial_authority"

        if not (data["sun_sign"] and data["mc_sign"]):
            if not self.allow_default:
                raise FileNotFoundError(f"No valid astrobranding brief or 15-shards data found for '{self.brand_raw}'.")
            data.update({"sun_sign": "Capricorn", "mc_sign": "Virgo", "day_master": "Wu", "nakshatra": "Ashwini", "dominant_element": "Earth"})

        data["dominant_element"] = data["dominant_element"] or ZODIAC_ELEMENTS.get(data["sun_sign"], "Earth")
        data["day_master"] = data["day_master"] or "Wu"
        data["nakshatra"] = data["nakshatra"] or "Ashwini"
        return data

    def build_ecosystems(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        sun_sign = params.get("sun_sign", "Capricorn")
        mc_sign = params.get("mc_sign", "Virgo")
        day_master = params.get("day_master", "Wu")
        nakshatra = params.get("nakshatra", "Ashwini")
        style_profile = params.get("style_profile", "architectural_b2b")

        mc_elem = ZODIAC_ELEMENTS.get(mc_sign, "Earth")
        mc_mod = ZODIAC_MODALITIES.get(mc_sign, "Cardinal")
        scale_ratio = MODALITY_SCALE_RATIOS.get(mc_mod, 1.333)
        bazi_info = BAZI_MODULATIONS.get(day_master, BAZI_MODULATIONS["Wu"])
        nak_info = NAKSHATRA_FEATURES.get(nakshatra, {"feature": "liga 1", "lord": "Mars", "accent_archetype": "architectural_emblem"})

        # Ecosystem 1: Swiss Architectural Authority (Sans-first per taste-skill §4.1, zero Fraunces/calligraphy slop)
        if style_profile == "architectural_b2b":
            q_p1, fb_p1, eco1_body = "swiss neo grotesque sans", "swiss_neo_grotesque", GOOGLE_FONTS_CATALOG["plus_jakarta_sans"]
            q_a1, fb_a1 = "minimalist architectural sans serif", "minimalist_arch_sans"
            disp_fallback_1 = GOOGLE_FONTS_CATALOG["space_grotesk"]
        elif mc_elem == "Water":
            q_p1, fb_p1, eco1_body = "sharp editorial high contrast sans serif", "high_contrast_didone", GOOGLE_FONTS_CATALOG["dm_sans"]
            q_a1, fb_a1 = "modern architectural emblem logo font", "architectural_emblem"
            disp_fallback_1 = GOOGLE_FONTS_CATALOG["bricolage_grotesque"]
        else:
            q_p1, fb_p1, eco1_body = "modern architectural geometric sans font", "futuristic_arch_sans", GOOGLE_FONTS_CATALOG["plus_jakarta_sans"]
            q_a1, fb_a1 = "monogram geometric brand font", "monogram_holder"
            disp_fallback_1 = GOOGLE_FONTS_CATALOG["space_grotesk"]

        eco1_prim = self._search_live_envato_fonts(q_p1, "sans") or self._get_fallback_envato_font(fb_p1)
        eco1_acc = self._search_live_envato_fonts(q_a1, "display") or self._get_fallback_envato_font(fb_a1)

        eco1 = {
            "id": "eco-1",
            "name": f"Arquitectura Suiza B2B ({mc_elem} · MC {mc_sign} / Sideral {params.get('sidereal_mc_sign') or mc_sign})",
            "archetype": f"Precisión MC {mc_sign} · Shadbala {params.get('shadbala_dominant') or 'Sun'}",
            "rationale": (
                f"Display arquitectónico sin ornamentos ({eco1_prim['family']}) y lectura humana continua en "
                f"{eco1_body['family']} (ratio {scale_ratio:.3f}, {mc_mod}), sello geométrico {eco1_acc['family']}."
            ),
            "web_fallback_display": disp_fallback_1,
            "tokens": self._pack_tokens(eco1_prim, eco1_body, eco1_acc),
            "layers": {
                "logo": f"{eco1_acc['family']} (Weight 700, Tracking -0.02em)",
                "slogan": f"{eco1_prim['family']} (Weight 500, Tracking +0.08em)",
                "h1": f"{eco1_prim['family']} (Weight 700, Ratio {scale_ratio:.3f}, Tracking -0.025em)",
                "h2": f"{eco1_prim['family']} (Weight 600, Ratio {scale_ratio:.3f})",
                "body": f"{eco1_body['family']} (Variable Regular 400, Line-height 1.60)",
                "ui": f"{eco1_body['family']} (Variable SemiBold 600, Tracking -0.01em)"
            },
            "cls_metric_overrides": self._cls_dict(eco1_body),
            "workbench_presets": {"font_size_px": 60, "letter_spacing_em": -0.025, "line_height": 1.08, "text_transform": "none", "font_weight": "700", "ligatures_enabled": False}
        }

        # Ecosystem 2: Structural Geometric Systems (BaZi Day Master + Month Element)
        q_p2 = "modern geometric grotesque display sans" if bazi_info["element"] in ("Wood", "Metal", "Fire") else "minimalist geometric sans font"
        fb_p2 = "modern_tech_grotesk"
        q_a2 = "industrial neo grotesque display font"
        fb_a2 = "modern_grotesk_stencil"
        eco2_body = GOOGLE_FONTS_CATALOG["dm_sans"]
        eco2_prim = self._search_live_envato_fonts(q_p2, "sans") or self._get_fallback_envato_font(fb_p2)
        eco2_acc = self._search_live_envato_fonts(q_a2, "display") or self._get_fallback_envato_font(fb_a2)

        eco2 = {
            "id": "eco-2",
            "name": f"Rigor Geométrico Estructural (BaZi {day_master} {bazi_info['element']} · Mes {params.get('bazi_month_element') or 'Metal'})",
            "archetype": f"Estructura BaZi {day_master} ({bazi_info['polarity']})",
            "rationale": f"Titular técnico {eco2_prim['family']} emparejado con {eco2_body['family']} (tracking {bazi_info['tracking_em']}em) y marca {eco2_acc['family']}.",
            "web_fallback_display": GOOGLE_FONTS_CATALOG["bricolage_grotesque"],
            "tokens": self._pack_tokens(eco2_prim, eco2_body, eco2_acc),
            "layers": {
                "logo": f"{eco2_acc['family']} (Weight 800, Tracking -0.02em)",
                "slogan": f"{eco2_prim['family']} (Weight 500, Tracking +0.10em)",
                "h1": f"{eco2_prim['family']} (Weight 700, Tracking {bazi_info['tracking_em']}em)",
                "h2": f"{eco2_prim['family']} (Weight 600, Ratio {scale_ratio:.3f})",
                "body": f"{eco2_body['family']} (Variable Regular 400, Line-height 1.55)",
                "ui": f"{eco2_body['family']} (Variable Bold 700, Tracking -0.015em)"
            },
            "cls_metric_overrides": self._cls_dict(eco2_body),
            "workbench_presets": {"font_size_px": 56, "letter_spacing_em": bazi_info["tracking_em"], "line_height": 1.10, "text_transform": "none", "font_weight": "700", "ligatures_enabled": False}
        }

        # Ecosystem 3: Sharp Editorial Contrast (Nakshatra Craft — High-contrast editorial serif without calligraphy/Fraunces)
        q_p3 = "editorial high contrast serif"
        fb_p3 = "sharp_editorial_serif"
        q_a3 = "modern architectural emblem logo font"
        fb_a3 = nak_info.get("accent_archetype", "architectural_emblem")
        eco3_body = GOOGLE_FONTS_CATALOG["instrument_sans"]
        eco3_prim = self._search_live_envato_fonts(q_p3, "serif") or self._get_fallback_envato_font(fb_p3)
        eco3_acc = self._search_live_envato_fonts(q_a3, "display") or self._get_fallback_envato_font(fb_a3)

        eco3 = {
            "id": "eco-3",
            "name": f"Autoridad Editorial Cortante (Nakshatra {nakshatra} · Regente {nak_info.get('lord', 'Mars')})",
            "archetype": f"Artesanía Védica {nakshatra} ({nak_info['feature']})",
            "rationale": f"Alternativa editorial sobria en {eco3_prim['family']} con UI limpia en {eco3_body['family']} y emblema {eco3_acc['family']} (cero caligrafía nupcial).",
            "web_fallback_display": GOOGLE_FONTS_CATALOG["newsreader"],
            "tokens": self._pack_tokens(eco3_prim, eco3_body, eco3_acc),
            "layers": {
                "logo": f"{eco3_acc['family']} (Weight 800)",
                "slogan": f"{eco3_prim['family']} (Weight 400, Tracking +0.06em)",
                "h1": f"{eco3_prim['family']} (Weight 600, Ratio {scale_ratio:.3f})",
                "h2": f"{eco3_prim['family']} (Weight 500)",
                "body": f"{eco3_body['family']} (Variable Regular 400, Line-height 1.58)",
                "ui": f"{eco3_body['family']} (Variable SemiBold 600, Tracking -0.01em)"
            },
            "cls_metric_overrides": self._cls_dict(eco3_body),
            "workbench_presets": {"font_size_px": 62, "letter_spacing_em": -0.015, "line_height": 1.12, "text_transform": "none", "font_weight": "600", "ligatures_enabled": True}
        }

        return [eco1, eco2, eco3]

    def _cls_dict(self, body: Dict[str, Any]) -> Dict[str, str]:
        return {
            "fallback_font": body["cls"]["fallback"],
            "size_adjust": body["cls"]["size_adjust"],
            "ascent_override": body["cls"]["ascent"],
            "descent_override": body["cls"]["descent"],
            "line_gap_override": body["cls"]["line_gap"],
        }

    def _pack_tokens(self, prim: Dict[str, Any], body: Dict[str, Any], acc: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "display_primary": {
                "$value": prim["family"],
                "$type": "fontFamily",
                "$description": f"Envato Elements Pro — {prim['description']}",
                "source": "envato",
                "item_uuid": prim.get("item_uuid") or _extract_uuid(prim["url"]),
                "url": prim["url"],
                "search_url": prim.get("search_url", ""),
                "weights": prim["weights"],
            },
            "ui_secondary": {
                "$value": body["family"],
                "$type": "fontFamily",
                "$description": "Google Fonts v2 Variable — Workhorse tipográfico",
                "source": "google_fonts",
                "url": body["url"],
                "google_fonts_v2_url": body["google_fonts_v2_url"],
                "variable_axes": body["variable_axes"],
                "weights": body["weights"],
            },
            "accent_brand": {
                "$value": acc["family"],
                "$type": "fontFamily",
                "$description": f"Envato Elements Pro — {acc['description']}",
                "source": "envato",
                "item_uuid": acc.get("item_uuid") or _extract_uuid(acc["url"]),
                "url": acc["url"],
                "search_url": acc.get("search_url", ""),
                "weights": acc["weights"],
            },
        }

    def generate_manifest(self, selected_eco_id: str = "eco-1") -> Dict[str, Any]:
        params = self.resolve_inputs()
        ecosystems = self.build_ecosystems(params)
        selected_eco = next((e for e in ecosystems if e["id"] == selected_eco_id), ecosystems[0])

        disp_bridge = selected_eco.get("web_fallback_display", GOOGLE_FONTS_CATALOG["space_grotesk"])
        body_google = selected_eco["tokens"]["ui_secondary"]

        # Remove temporary internal helper key from serialized JSON ecosystems
        clean_ecosystems = []
        for e in ecosystems:
            e_copy = {k: v for k, v in e.items() if k != "web_fallback_display"}
            clean_ecosystems.append(e_copy)
        selected_clean = next((e for e in clean_ecosystems if e["id"] == selected_eco["id"]), clean_ecosystems[0])

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "brand": self.brand_upper,
            "selected_ecosystem_id": selected_clean["id"],
            "style_profile": params.get("style_profile"),
            "candidate_ecosystems": clean_ecosystems,
            "selected_ecosystem": selected_clean,
            "web_ready_bridge": {
                "delivery": "astro_5_experimental_fonts_self_hosted",
                "display_fallback_family": disp_bridge["family"],
                "display_fallback_v2_url": disp_bridge["google_fonts_v2_url"],
                "body_family": body_google["$value"],
                "body_v2_url": body_google["google_fonts_v2_url"],
                "mono_family": "JetBrains Mono",
                "anti_slop_bans_enforced": ["Fraunces", "Instrument Serif", "Inter", "wedding calligraphy"],
                "envato_upgrade_targets": {
                    "display_primary": selected_clean["tokens"]["display_primary"]["$value"],
                    "display_url": selected_clean["tokens"]["display_primary"]["url"],
                    "accent_brand": selected_clean["tokens"]["accent_brand"]["$value"],
                    "accent_url": selected_clean["tokens"]["accent_brand"]["url"],
                },
            },
            "inheritance": {
                "logo": selected_clean["layers"]["logo"],
                "slogan": selected_clean["layers"]["slogan"],
                "h1": selected_clean["layers"]["h1"],
                "h2": selected_clean["layers"]["h2"],
                "body": selected_clean["layers"]["body"],
                "ui": selected_clean["layers"]["ui"],
                "ui_buttons": selected_clean["layers"]["ui"],
            },
            "metadata": {
                "generator": "fontgen_engine.py v4.0 (Oráculo 15-Shards + Vertical + Live Envato)",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "inputs_used": params,
                "astrological_grounding": {
                    "sun": f"{params.get('sun_sign')} ({ZODIAC_ELEMENTS.get(params.get('sun_sign'), 'Earth')})",
                    "midheaven": f"{params.get('mc_sign')} ({ZODIAC_ELEMENTS.get(params.get('mc_sign'), 'Earth')})",
                    "sidereal_midheaven": params.get("sidereal_mc_sign") or params.get("mc_sign"),
                    "shadbala_dominant": params.get("shadbala_dominant") or "Sun",
                    "day_master": params.get("day_master"),
                    "bazi_month_element": params.get("bazi_month_element") or "",
                    "nakshatra": params.get("nakshatra"),
                },
            },
        }

    def generate_markdown_sheet(self, manifest: Dict[str, Any]) -> str:
        meta = manifest.get("metadata", {}).get("astrological_grounding", {})
        ecos = manifest.get("candidate_ecosystems", [])
        md = [
            f"# Dirección de Arte Tipográfica: {self.brand_upper}",
            f"> **Perfil:** `{manifest.get('style_profile')}` · Sol en {meta.get('sun')}, MC {meta.get('midheaven')} "
            f"(Sideral {meta.get('sidereal_midheaven')}), Shadbala {meta.get('shadbala_dominant')}, "
            f"Day Master {meta.get('day_master')}, Nakshatra {meta.get('nakshatra')}.",
            "",
            "---",
            "",
        ]
        for idx, eco in enumerate(ecos, 1):
            t = eco["tokens"]
            p = eco.get("cls_metric_overrides", {})
            md.extend([
                f"### Ecosistema {idx}: {eco['name']} ({eco['id']})",
                f"- **Arquetipo Rector:** {eco['archetype']}",
                f"- **Justificación Gestalt:** {eco['rationale']}",
                "",
                "#### Matriz de 3 Design Tokens (W3C DTCG)",
                f"1. **Token Primario (Display):** `{t['display_primary']['$value']}` — [Envato]({t['display_primary']['url']}) (UUID `{t['display_primary'].get('item_uuid','')}`)",
                f"2. **Token Secundario (UI & Lectura):** `{t['ui_secondary']['$value']}` — [Google Fonts]({t['ui_secondary']['url']})",
                f"3. **Token de Acento (Monograma/Emblema):** `{t['accent_brand']['$value']}` — [Envato]({t['accent_brand']['url']}) (UUID `{t['accent_brand'].get('item_uuid','')}`)",
                "",
                "#### Herencia de 6 Capas",
                *[f"- **{k}:** {v}" for k, v in eco["layers"].items()],
                "",
                "#### Anti-CLS",
                f"- `fallback_font`: `{p.get('fallback_font')}`, `size_adjust`: `{p.get('size_adjust')}`, `ascent_override`: `{p.get('ascent_override')}`",
                "",
                "---",
                "",
            ])
        return "\n".join(md)

    def run(self, selected_eco_id: str = "eco-1", dry_run: bool = False) -> Tuple[Dict[str, Any], str]:
        manifest = self.generate_manifest(selected_eco_id=selected_eco_id)
        markdown = self.generate_markdown_sheet(manifest)
        if dry_run:
            return manifest, markdown

        manifest_str = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
            (self.output_dir / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")
            return manifest, markdown

        written = False
        for d in (self.project_dev_dir, self.diag_dir):
            if d.exists():
                (d / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
                (d / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")
                written = True
        if not written:
            if self.create_brand_dirs:
                self.project_dev_dir.mkdir(parents=True, exist_ok=True)
                (self.project_dev_dir / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
                (self.project_dev_dir / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")
            else:
                cwd_out = Path.cwd()
                (cwd_out / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
                (cwd_out / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")
        return manifest, markdown


def derive_agnostic_typography(
    brand: str,
    shards: Optional[Dict[str, Any]] = None,
    shards_path: Optional[Path] = None,
    brief_path: Optional[Path] = None,
    vertical_json_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    selected_eco_id: str = "eco-1",
    use_live_search: bool = True,
    allow_default: bool = False,
) -> Dict[str, Any]:
    engine = FontgenEngine(
        brand=brand,
        shards_path=shards_path,
        brief_path=brief_path,
        vertical_json_path=vertical_json_path,
        output_dir=output_dir,
        use_live_search=use_live_search,
        allow_default=allow_default,
    )
    manifest, _ = engine.run(selected_eco_id=selected_eco_id, dry_run=False)
    return manifest


def run_unit_tests() -> int:
    print("Running fontgen_engine v4.0 offline unit tests...")
    assert normalize_zodiac_sign("Géminis") == "Gemini"
    assert normalize_zodiac_sign("Tauro") == "Taurus"
    e_filter = FontgenEngine("TEST", use_live_search=False)
    assert e_filter._is_noisy_title("Wedding Luxury Calligraphy Script") is True
    assert e_filter._is_noisy_title("Thornvoid Horror Gothic") is True
    assert e_filter._is_noisy_title("Monolith - Swiss Neo Grotesque Sans") is False

    with tempfile.TemporaryDirectory(prefix="fontgen_v4_test_") as tmp:
        tp = Path(tmp)
        shards_p = tp / "client_dumps_15_shards.json"
        vert_p = tp / "vert.json"
        out_p = tp / "ws_brand"
        shards_p.write_text(json.dumps({
            "shard_01": {"data": {"tripod_of_iron": {"sun": {"sign": "Gemini"}, "midheaven_house_10": {"sign": "Gemini"}}}},
            "shard_02": {"data": {"fagan_bradley": {"midheaven": {"sign": "Taurus"}}}},
            "shard_03": {"data": {"shadbala": {"dominant_planet": "Sun"}, "nakshatra": {"name": "Chitra Pada 4", "lord": "Mars"}}},
            "shard_04": {"data": {"day_master": {"name": "Jia", "element": "Wood"}, "four_pillars": {"month": {"element": "Metal"}}}},
        }), encoding="utf-8")
        vert_p.write_text(json.dumps({"category": "Consultoría unipersonal B2B e IA"}), encoding="utf-8")

        engine = FontgenEngine("TESTCORP", shards_path=shards_p, vertical_json_path=vert_p, output_dir=out_p, use_live_search=False)
        manifest, _ = engine.run()
        assert manifest["style_profile"] == "architectural_b2b"
        assert manifest["web_ready_bridge"]["display_fallback_family"] not in ("Fraunces", "Instrument Serif")
        fams = [e["tokens"]["display_primary"]["$value"] for e in manifest["candidate_ecosystems"]]
        assert len(set(fams)) == 3
        assert (out_p / "font_manifest.json").exists()
    assert not Path("/mnt/localstorage/TESTCORP").exists()
    print("✅ FONTGEN ENGINE v4.0 UNIT TESTS PASSED (Oráculo+Vertical, 0 Fraunces/wedding slop, 3 unique ecos, 0 phantom dirs)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fontgen Engine v4.0 — Verified Typographic Synthesizer")
    parser.add_argument("--brand", default="BRAND")
    parser.add_argument("--shards", type=Path, default=None)
    parser.add_argument("--brief", type=Path, default=None)
    parser.add_argument("--vertical-json", type=Path, default=None)
    parser.add_argument("--style-profile", default="auto", choices=["auto", "architectural_b2b", "editorial_authority"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--eco", default="eco-1", choices=["eco-1", "eco-2", "eco-3"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-live", action="store_true")
    parser.add_argument("--allow-default", action="store_true")
    parser.add_argument("--create-brand-dirs", action="store_true")
    parser.add_argument("--sun-sign", default=None)
    parser.add_argument("--mc-sign", default=None)
    parser.add_argument("--day-master", default=None)
    parser.add_argument("--nakshatra", default=None)
    parser.add_argument("--dominant-element", default=None)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        return run_unit_tests()

    override_params = {k: v for k, v in {
        "sun_sign": args.sun_sign, "mc_sign": args.mc_sign, "day_master": args.day_master,
        "nakshatra": args.nakshatra, "dominant_element": args.dominant_element,
    }.items() if v}

    engine = FontgenEngine(
        brand=args.brand,
        shards_path=args.shards,
        brief_path=args.brief,
        vertical_json_path=args.vertical_json,
        output_dir=args.output_dir,
        use_live_search=not args.no_live,
        allow_default=args.allow_default,
        override_params=override_params or None,
        create_brand_dirs=args.create_brand_dirs,
        style_profile=args.style_profile,
        seed=args.seed,
    )
    manifest, _ = engine.run(selected_eco_id=args.eco, dry_run=args.dry_run)
    sel = manifest["selected_ecosystem"]["tokens"]
    print(f"✅ FONTGEN ENGINE v4.0 COMPLETED FOR: {args.brand.upper()} ({manifest['selected_ecosystem_id']}, profile={manifest['style_profile']})")
    print(f"  • Display: {sel['display_primary']['$value']} ({sel['display_primary']['url']})")
    print(f"  • Body UI: {sel['ui_secondary']['$value']} ({sel['ui_secondary']['url']})")
    print(f"  • Accent:  {sel['accent_brand']['$value']} ({sel['accent_brand']['url']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
