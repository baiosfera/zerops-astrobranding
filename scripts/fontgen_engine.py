#!/usr/bin/env python3
"""
fontgen_engine.py — Sovereign Agnostic Vanguard Typographic Engine (v4.1).
Multi-Axis Oráculo 15-Shards + 5-Tier Vertical Archetype + Vanguard Dual-Sort Envato Discovery.

Key Capabilities (v4.1):
1. Dual-Sort Vanguard Envato Scraping:
   - Fetches structured INITIAL_HYDRATION_DATA from elements.envato.com (sort-by-latest & sort-by-popular)
     AND complements with app.envato.com/search?itemType=fonts (latest + popular).
   - Scores foundry craftsmanship (isNew +15, inktrap/grotesk/neo/variable/mono/editorial +12,
     svg ready +8), filters kitsch/noise (retro/western/90s/pixel/horror/wedding/script/graffiti),
     rotates picks via --seed, verifies live SVG previewability, and emits runner-up shortlist_candidates.
2. 5-Tier Multi-Vertical Differentiation:
   - architectural_b2b, cosmic_archetypal, design_system_atelier, editorial_manifesto, editorial_brand
   under ONE shared client Oráculo chart without ever overwriting sibling verticals or brandbook cores.
3. Enforces design-taste-frontend (§4.1 Serif Discipline) & impeccable floor:
   - Never uses Fraunces, Instrument Serif, or Inter defaults.
   - Zero global phantom directories unless --create-brand-dirs is explicitly passed.
"""

import argparse
import base64
import html as html_lib
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


NOISE_BLOCKLIST_BASE = {
    "wedding", "bridal", "romantic", "love", "heart", "horror", "scary", "gothic", "zombie",
    "halloween", "graffiti", "cartoon", "comic", "kids", "cute", "brush", "calligraphy",
    "script", "signature", "tattoo", "lavish", "swash", "flourish", "cursive", "handwritten",
    "retro", "vintage", "groovy", "psychedelic", "metal", "blood", "spooky", "western",
    "disco", "pixel", "pixelated", "bubble", "drippy", "funky", "mecha", "robot", "scifi",
    "death", "wavy", "playful", "farmhouse", "christmas", "valentine", "y2k", "grunge",
    "blackletter", "medieval", "rounded", "90s", "80s", "70s", "terror", "fear", "drawn",
}

VANGUARD_CRAFT_TOKENS = {
    "inktrap", "grotesk", "grotesque", "groteks", "neo", "variable", "family", "pro",
    "condensed", "editorial", "geometric", "modern", "celestial",
    "cinematic", "minimal", "minimalist", "sans", "didone", "brutalist", "technica",
}


# -----------------------------------------------------------------------------
# Verified Curated Vanguard Fallback Catalog (elements.envato.com verified)
# -----------------------------------------------------------------------------

ENVATO_VERIFIED_CATALOG: Dict[str, Dict[str, Any]] = {
    "xenon_nue": {
        "family": "Xenon Nue",
        "item_uuid": "12d5699d-d4a8-4231-abcc-4a1aec744a4a",
        "url": "https://app.envato.com/fonts/12d5699d-d4a8-4231-abcc-4a1aec744a4a",
        "search_url": "https://elements.envato.com/fonts/sans-serif/sort-by-popular",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Vanguard Neo-Grotesque Family",
        "description": "Xenon Nue - Premium Architectural Sans-Serif Family on Envato Elements."
    },
    "nority_inktrap": {
        "family": "Nority",
        "item_uuid": "2e9b3477-adbb-44cb-93eb-d7b94b2cc9c9",
        "url": "https://app.envato.com/fonts/2e9b3477-adbb-44cb-93eb-d7b94b2cc9c9",
        "search_url": "https://elements.envato.com/fonts/inktrap/sort-by-popular",
        "weights": ["500", "700"],
        "category": "sans",
        "style": "Contemporary Inktrap Display",
        "description": "Nority - Inktrap Bold Display Font by limitype on Envato Elements."
    },
    "helvena_grotesk": {
        "family": "Helvena Grotesk",
        "item_uuid": "28f120ab-2460-43f2-8f72-7b982cb8c27b",
        "url": "https://app.envato.com/fonts/28f120ab-2460-43f2-8f72-7b982cb8c27b",
        "search_url": "https://elements.envato.com/fonts/inktrap/sort-by-popular",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Modern Brand Identity Grotesk",
        "description": "Helvena Grotesk - Modern Bold Brand Identity Font on Envato Elements."
    },
    "lenia_mono": {
        "family": "Lenia Mono",
        "item_uuid": "f23df0ad-bbed-4d5b-927d-3e57d35ef0c0",
        "url": "https://app.envato.com/fonts/f23df0ad-bbed-4d5b-927d-3e57d35ef0c0",
        "search_url": "https://elements.envato.com/fonts/monospace/sort-by-popular",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Geometric Monospace Family",
        "description": "Lenia Mono - Geometric Monospace Sans-Serif Family on Envato Elements."
    },
    "gatger_corporate": {
        "family": "Gatger",
        "item_uuid": "66202144-4780-4b72-94e5-aea49c57f49d",
        "url": "https://app.envato.com/fonts/66202144-4780-4b72-94e5-aea49c57f49d",
        "search_url": "https://elements.envato.com/fonts/sans-serif/sort-by-popular",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Corporate Display Branding Family",
        "description": "Gatger - Display Branding Corporate Family Font by darecostudio."
    },
    "commune_inktrap_serif": {
        "family": "Commune",
        "item_uuid": "276b2711-b524-41a2-91b0-a8f117dae846",
        "url": "https://app.envato.com/fonts/276b2711-b524-41a2-91b0-a8f117dae846",
        "search_url": "https://elements.envato.com/fonts/inktrap/sort-by-popular",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Modern Inktrap Editorial Serif",
        "description": "Commune - Modern Inktrap Serif on Envato Elements."
    },
    "maire_editorial": {
        "family": "Maire",
        "item_uuid": "07c929a4-98d1-4746-bedc-f60e0d96bf62",
        "url": "https://app.envato.com/fonts/07c929a4-98d1-4746-bedc-f60e0d96bf62",
        "search_url": "https://elements.envato.com/fonts/editorial+modern/sort-by-latest",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Refined Contemporary Editorial Serif",
        "description": "Maire - Refined Editorial Serif Font on Envato Elements."
    },
    "pierre_robe_cinematic": {
        "family": "Pierre Robe",
        "item_uuid": "d8fc5546-87ef-45c1-a642-6929c72d9da4",
        "url": "https://app.envato.com/fonts/d8fc5546-87ef-45c1-a642-6929c72d9da4",
        "search_url": "https://elements.envato.com/fonts/serif/sort-by-popular",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Cinematic Sculptural Serif",
        "description": "Pierre Robe - Cinematic Editorial Serif Branding on Envato Elements."
    },
    "mtry_experimental": {
        "family": "Mtry",
        "item_uuid": "324ffc3d-42c7-4584-a479-f3b638a7d96f",
        "url": "https://app.envato.com/fonts/324ffc3d-42c7-4584-a479-f3b638a7d96f",
        "search_url": "https://app.envato.com/fonts",
        "weights": ["400", "600", "700"],
        "category": "display",
        "style": "Geometric Experimental Display",
        "description": "Mtry - Geometric Experimental Typeface by marvadesign."
    },
    "korolis_serif": {
        "family": "Korolis",
        "item_uuid": "25a6b739-a2ba-4eae-aced-4281dbf4b74b",
        "url": "https://app.envato.com/fonts/25a6b739-a2ba-4eae-aced-4281dbf4b74b",
        "search_url": "https://elements.envato.com/fonts/serif/sort-by-latest",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Modern Sharp Serif",
        "description": "Korolis - Modern Crisp Editorial Serif on Envato Elements."
    },
    "arteon_arch": {
        "family": "Arteon",
        "item_uuid": "9675e800-0193-40bc-b3fa-edfc5876bfee",
        "url": "https://app.envato.com/fonts/9675e800-0193-40bc-b3fa-edfc5876bfee",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=arteon",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Architectural Geometric Sans",
        "description": "Arteon - Architectural Futuristic Sans Serif on Envato Elements."
    },
    "qobar_grotesk": {
        "family": "Qobar",
        "item_uuid": "5f52efb4-f726-4925-bb0b-8946fb95f70b",
        "url": "https://app.envato.com/fonts/5f52efb4-f726-4925-bb0b-8946fb95f70b",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=qobar",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Modern Structural Grotesk",
        "description": "Qobar - Modern Structural Sans Serif on Envato Elements."
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
    "Chitra": {"feature": "dlig 1, calt 1", "lord": "Mars"},
    "Ashwini": {"feature": "dlig 1, ss01 1", "lord": "Ketu"},
    "Rohini": {"feature": "calt 1, liga 1", "lord": "Moon"},
    "Mrigashira": {"feature": "ss02 1", "lord": "Mars"},
    "Hasta": {"feature": "ss01 1", "lord": "Moon"},
    "Swati": {"feature": "liga 1", "lord": "Rahu"},
    "Shravana": {"feature": "liga 1, calt 1", "lord": "Moon"},
    "Revati": {"feature": "calt 1, liga 1", "lord": "Mercury"},
}


def normalize_zodiac_sign(raw_sign: str) -> str:
    s = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚ]", "", str(raw_sign or "").strip()).lower()
    return SIGN_NORMALIZATION.get(s, str(raw_sign or "").strip().title())


def _extract_vertical_identity_blob(vdata: Dict[str, Any]) -> str:
    cap = vdata.get("category_and_positioning") or {}
    parts: List[Any] = [
        vdata.get("vertical_slug", ""),
        vdata.get("display_name", ""),
        vdata.get("name", ""),
        vdata.get("title", ""),
        vdata.get("funnel_type", ""),
        vdata.get("category", ""),
        vdata.get("tagline", ""),
        vdata.get("aesthetic_direction", ""),
        vdata.get("design_archetype", ""),
        cap.get("category_name", ""),
        cap.get("primary_positioning_terms", []),
        vdata.get("ontological_foundation", {}),
        vdata.get("unique_mechanism", {}),
        vdata.get("subthemes", []),
        vdata.get("target_avatar", {}),
    ]
    return json.dumps(parts, ensure_ascii=False)


def classify_vertical_style_profile(vblob: str, vertical_slug: str = "") -> str:
    t = f"{vertical_slug} {vblob}".lower()
    if any(k in t for k in ("sabidurías cósmicas", "arquetipo vocacional", "astrolog", "kabbalah", "human design", "numerolog", "tarot", "autoconocimiento", "carta natal", "cósmic")):
        return "cosmic_archetypal"
    if any(k in t for k in ("design system", "tokens de diseño", "brandbook", "monogramas vectoriales", "tipografía curada", "tokens dtcg", "astrobranding", "sistema de diseño", "identidad visual")):
        return "design_system_atelier"
    if any(k in t for k in ("causalidad inversa", "arqueología del futuro", "saga editorial", "manifiesto", "book_waitlist", "libro", "ensayo filosófico")):
        return "editorial_manifesto"
    if any(k in t for k in ("consultor", "b2b", "financier", "abogado", "médico", "unipersonal", "agencia", "automatiz", "saas", "seo local", "google maps", "infraestructura", "captación", "independientes")):
        return "architectural_b2b"
    return "editorial_brand"


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
    Sovereign Agnostic Vanguard Typographic Engine (v4.1).
    Dual-sort Envato Elements hydration + app.envato.com + Multi-vertical differentiation.
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
        sort_mode: str = "hybrid",
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
        self.sort_mode = sort_mode
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
        first_part = html_lib.unescape(first_part)
        first_part = re.sub(r"[®™©]+", "", first_part).strip()
        first_part = re.sub(r"\s+A\s+(?:Geometric|Modern|Minimal|Experimental|Corporate|Editorial|Clean)\b.*$", "", first_part, flags=re.IGNORECASE).strip()
        cleaned = re.sub(
            r"\b(?:Clean\s+Minimal\s+Geometric|Geometric\s+Monospace|Font|Typeface|Family|Display|Serif|Sans|Bold|Minimalist|Minimal|Clean|Branding|Logo|Modern)\b",
            "", first_part, flags=re.IGNORECASE,
        ).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned.title() if len(cleaned) >= 2 else first_part.strip().title()

    def _is_noisy_title(self, raw_title: str) -> bool:
        words = set(re.findall(r"[a-z0-9]+", raw_title.lower()))
        return bool(words.intersection(NOISE_BLOCKLIST_BASE))

    def _score_candidate(self, title: str, is_new: bool, has_svg: bool, sort_label: str, query_term: str = "") -> int:
        words = set(re.findall(r"[a-z0-9]+", title.lower()))
        score = 10
        if is_new or sort_label == "latest":
            score += 15
        if has_svg:
            score += 8
        craft_hits = len(words.intersection(VANGUARD_CRAFT_TOKENS))
        score += craft_hits * 10
        wants_mono = "mono" in query_term.lower()
        has_mono = bool(words.intersection({"mono", "monospace"}))
        if has_mono:
            score += 12 if wants_mono else -15
        if "logo" in words and craft_hits == 0:
            score -= 18
        if len(title) > 52:
            score -= 5
        return score

    def _is_previewable_uuid(self, item_uuid: str) -> bool:
        if not item_uuid:
            return False
        if not self.verify_svg_preview:
            return True
        txt = urllib.parse.quote_plus("DISEÑO Ñ")
        svg_url = f"https://elements.envato.com/font-preview.svg?itemUuid={urllib.parse.quote(item_uuid)}&text={txt}&typed=1"
        try:
            req = urllib.request.Request(
                svg_url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "Referer": "https://elements.envato.com/"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read(220).decode("utf-8", errors="ignore")
                return resp.status == 200 and "<svg" in body.lower()
        except Exception:
            return False

    def _fetch_elements_hydration(self, term_slug: str, cat_slug: Optional[str], sort_opt: str) -> List[Dict[str, Any]]:
        sort_part = "sort-by-latest" if sort_opt == "latest" else "sort-by-popular"
        parts = ["https://elements.envato.com/fonts"]
        if term_slug:
            parts.append(term_slug)
        if cat_slug:
            parts.append(cat_slug)
        parts.append(sort_part)
        url = "/".join(parts)
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}
        out: List[Dict[str, Any]] = []
        try:
            body = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=8).read().decode("utf-8", errors="ignore")
            m = re.search(r'window\.INITIAL_HYDRATION_DATA="([^"]+)"', body)
            if not m:
                return []
            pdata = json.loads(base64.b64decode(m.group(1)).decode("utf-8"))["page"]["data"]["data"]
            for it in pdata.get("items", []):
                fid = str(it.get("itemUuid") or "").lower()
                title = str(it.get("title") or "").strip()
                if not fid or not title:
                    continue
                item_url = str(it.get("itemUrl") or "")
                full_url = f"https://elements.envato.com{item_url}" if item_url.startswith("/") else f"https://app.envato.com/fonts/{fid}"
                out.append({
                    "uuid": fid,
                    "title": title,
                    "author": str(it.get("author") or "Envato Foundry"),
                    "is_new": bool(it.get("isNew")),
                    "has_svg": bool(it.get("fontPreviewSvg") or it.get("fontPreviewSvgs")),
                    "sort_label": sort_opt,
                    "source_url": url,
                    "item_url": full_url,
                })
        except Exception:
            pass
        return out

    def _fetch_app_envato(self, query: str, sort_opt: str) -> List[Dict[str, Any]]:
        url = f"https://app.envato.com/search?itemType=fonts&term={urllib.parse.quote_plus(query)}&sort={sort_opt}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        out: List[Dict[str, Any]] = []
        try:
            ht = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=8).read().decode("utf-8", errors="ignore")
            chunks = re.findall(r'<a[^>]+data-analytics-item_id="[^"]+"[^>]*>', ht)
            for c in chunks[:40]:
                mid = re.search(r'data-analytics-item_id="([^"]+)"', c)
                mt = re.search(r'data-analytics-item_title="([^"]+)"', c)
                ma = re.search(r'data-analytics-item_author="([^"]+)"', c)
                if not (mid and mt):
                    continue
                fid = mid.group(1).strip().lower()
                title = html_lib.unescape(mt.group(1).strip())
                out.append({
                    "uuid": fid,
                    "title": title,
                    "author": html_lib.unescape(ma.group(1).strip()) if ma else "Envato Author",
                    "is_new": sort_opt == "latest",
                    "has_svg": True,
                    "sort_label": sort_opt,
                    "source_url": url,
                    "item_url": f"https://app.envato.com/fonts/{fid}",
                })
        except Exception:
            pass
        return out

    def _search_live_envato_fonts(
        self,
        elements_term: str,
        app_query: str,
        category_slug: str = "sans-serif",
        category_label: str = "sans",
        default_weights: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self.use_live_search:
            return None

        sorts = ["latest", "popular"] if self.sort_mode == "hybrid" else [self.sort_mode]
        raw_pool: List[Dict[str, Any]] = []
        term_slug = elements_term.strip().replace(" ", "+")

        for s in sorts:
            hits = self._fetch_elements_hydration(term_slug, category_slug, s)
            if not hits:
                hits = self._fetch_elements_hydration(term_slug, None, s)
            raw_pool.extend(hits)
        if len(raw_pool) < 8:
            for s in sorts:
                raw_pool.extend(self._fetch_app_envato(app_query, s))

        # Deduplicate, filter noise, and rank by vanguard craftsmanship
        scored: List[Tuple[int, Dict[str, Any]]] = []
        seen_uuids: Set[str] = set()
        seen_fams: Set[str] = set()

        for cand in raw_pool:
            fid = cand["uuid"]
            if fid in seen_uuids or fid in self.used_uuids:
                continue
            seen_uuids.add(fid)
            title = cand["title"]
            if self._is_noisy_title(title):
                continue
            family = self._clean_family_name(title)
            if family.lower() in [f.lower() for f in self.used_families] or family.lower() in seen_fams:
                continue
            seen_fams.add(family.lower())
            sc = self._score_candidate(title, cand["is_new"], cand["has_svg"], cand["sort_label"], elements_term)
            cand_copy = dict(cand)
            cand_copy["family"] = family
            cand_copy["score"] = sc
            scored.append((sc, cand_copy))

        scored.sort(key=lambda x: (-x[0], x[1]["family"]))
        verified: List[Dict[str, Any]] = []
        for sc, c in scored[:12]:
            if not self._is_previewable_uuid(c["uuid"]):
                continue
            verified.append({
                "family": c["family"],
                "item_uuid": c["uuid"],
                "url": f"https://app.envato.com/fonts/{c['uuid']}",
                "elements_url": c["item_url"],
                "search_url": c["source_url"],
                "weights": default_weights or ["400", "600", "700"],
                "category": category_label,
                "is_new": c["is_new"],
                "score": sc,
                "sort_source": c["sort_label"],
                "style": f"Vanguard Envato ({c['sort_label']}: {elements_term})",
                "description": f"{c['title']} by {c['author']} (Envato Elements, score={sc}, sort={c['sort_label']}).",
            })
            if len(verified) >= 4:
                break

        if not verified:
            return None

        idx = self.seed % len(verified)
        pick = dict(verified[idx])
        shortlist = [
            {
                "family": v["family"],
                "item_uuid": v["item_uuid"],
                "url": v["url"],
                "elements_url": v["elements_url"],
                "score": v["score"],
                "is_new": v["is_new"],
                "sort_source": v["sort_source"],
                "description": v["description"],
            }
            for i, v in enumerate(verified) if i != idx
        ][:3]
        pick["shortlist"] = shortlist
        self.used_families.add(pick["family"])
        self.used_uuids.add(pick["item_uuid"])
        return pick

    def _get_fallback_envato_font(self, catalog_key: str, backup_keys: Tuple[str, ...] = ()) -> Dict[str, Any]:
        shortlist_pool: List[Dict[str, Any]] = []
        pick: Optional[Dict[str, Any]] = None
        for key in (catalog_key,) + backup_keys + tuple(ENVATO_VERIFIED_CATALOG.keys()):
            c = ENVATO_VERIFIED_CATALOG.get(key)
            if not c:
                continue
            if c["family"].lower() in [f.lower() for f in self.used_families]:
                continue
            if pick is None:
                pick = dict(c)
                pick["shortlist"] = []
                self.used_families.add(pick["family"])
                self.used_uuids.add(pick["item_uuid"])
            else:
                shortlist_pool.append({
                    "family": c["family"],
                    "item_uuid": c["item_uuid"],
                    "url": c["url"],
                    "elements_url": c["url"],
                    "score": 25,
                    "is_new": False,
                    "sort_source": "curated_catalog",
                    "description": c["description"],
                })
            if len(shortlist_pool) >= 2 and pick is not None:
                break
        if pick is None:
            pick = dict(ENVATO_VERIFIED_CATALOG["xenon_nue"])
            pick["shortlist"] = []
        else:
            pick["shortlist"] = shortlist_pool
        return pick

    def resolve_inputs(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "sun_sign": "", "mc_sign": "", "sidereal_sun_sign": "", "sidereal_mc_sign": "",
            "sidereal_asc_sign": "", "day_master": "", "bazi_month_element": "",
            "yong_shen": "", "nakshatra": "", "nakshatra_lord": "", "shadbala_dominant": "",
            "dominant_element": "", "style_profile": self.style_profile, "vertical_slug": "",
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

        if self.vertical_json_path and self.vertical_json_path.is_file():
            try:
                vdata = json.loads(self.vertical_json_path.read_text(encoding="utf-8"))
                vblob = _extract_vertical_identity_blob(vdata)
                data["vertical_slug"] = str(vdata.get("vertical_slug") or self.vertical_json_path.stem)
                data["sources_used"].append(f"vertical:{self.vertical_json_path.name}")
                if data["style_profile"] == "auto":
                    data["style_profile"] = str(vdata.get("style_profile") or "") or classify_vertical_style_profile(vblob, data["vertical_slug"])
            except Exception:
                pass

        if data["style_profile"] == "auto":
            if data["shadbala_dominant"] in ("Sun", "Saturn", "Mercury") or data["bazi_month_element"] == "Metal":
                data["style_profile"] = "architectural_b2b"
            else:
                data["style_profile"] = "editorial_brand"

        if not (data["sun_sign"] and data["mc_sign"]):
            if not self.allow_default:
                raise FileNotFoundError(f"No valid astrobranding brief or 15-shards data found for '{self.brand_raw}'.")
            data.update({"sun_sign": "Capricorn", "mc_sign": "Virgo", "day_master": "Wu", "nakshatra": "Ashwini", "dominant_element": "Earth"})

        data["dominant_element"] = data["dominant_element"] or ZODIAC_ELEMENTS.get(data["sun_sign"], "Earth")
        data["day_master"] = data["day_master"] or "Wu"
        data["nakshatra"] = data["nakshatra"] or "Ashwini"
        return data

    def build_ecosystems(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        mc_sign = params.get("mc_sign", "Virgo")
        day_master = params.get("day_master", "Wu")
        nakshatra = params.get("nakshatra", "Ashwini")
        style_profile = params.get("style_profile", "architectural_b2b")

        mc_elem = ZODIAC_ELEMENTS.get(mc_sign, "Earth")
        mc_mod = ZODIAC_MODALITIES.get(mc_sign, "Cardinal")
        scale_ratio = MODALITY_SCALE_RATIOS.get(mc_mod, 1.333)
        bazi_info = BAZI_MODULATIONS.get(day_master, BAZI_MODULATIONS["Wu"])
        nak_info = NAKSHATRA_FEATURES.get(nakshatra, {"feature": "liga 1", "lord": "Mars"})

        if style_profile == "cosmic_archetypal":
            specs = [
                ("eco-1", f"Observatorio Celestial Editorial ({mc_elem} · MC {mc_sign})",
                 "editorial modern", "modern high contrast editorial serif", "serif", "serif", "commune_inktrap_serif",
                 "modern", "minimalist serif monogram", "serif", "display", "maire_editorial",
                 GOOGLE_FONTS_CATALOG["plus_jakarta_sans"], GOOGLE_FONTS_CATALOG["newsreader"]),
                ("eco-2", f"Geometría Experimental & Monospace ({day_master} · Sideral {params.get('sidereal_mc_sign') or mc_sign})",
                 "geometric", "geometric experimental sans typeface", "sans-serif", "sans", "mtry_experimental",
                 "monospace", "geometric monospace sans", "sans-serif", "display", "lenia_mono",
                 GOOGLE_FONTS_CATALOG["dm_sans"], GOOGLE_FONTS_CATALOG["space_grotesk"]),
                ("eco-3", f"Alta Tipografía Simbólica (Nakshatra {nakshatra} · {nak_info['lord']})",
                 "serif", "cinematic sculptural serif font", "serif", "serif", "pierre_robe_cinematic",
                 "editorial", "contemporary classic serif display", "serif", "display", "korolis_serif",
                 GOOGLE_FONTS_CATALOG["manrope"], GOOGLE_FONTS_CATALOG["spectral"]),
            ]
        elif style_profile in ("design_system_atelier", "editorial_manifesto"):
            specs = [
                ("eco-1", f"Atelier Tipográfico Vanguardia ({mc_elem} · MC {mc_sign})",
                 "editorial", "inktrap editorial serif font", "serif", "serif", "commune_inktrap_serif",
                 "grotesk", "neo grotesque monogram font", "sans-serif", "display", "xenon_nue",
                 GOOGLE_FONTS_CATALOG["plus_jakarta_sans"], GOOGLE_FONTS_CATALOG["newsreader"]),
                ("eco-2", f"Sistema Suizo Mono/Grotesk ({day_master} · Mes {params.get('bazi_month_element') or 'Metal'})",
                 "grotesk", "swiss neo grotesque sans family", "sans-serif", "sans", "helvena_grotesk",
                 "monospace", "geometric monospace sans font", "sans-serif", "display", "lenia_mono",
                 GOOGLE_FONTS_CATALOG["dm_sans"], GOOGLE_FONTS_CATALOG["space_grotesk"]),
                ("eco-3", f"Edición Clásica Cortante (Nakshatra {nakshatra})",
                 "editorial modern", "refined editorial serif", "serif", "serif", "maire_editorial",
                 "minimal", "minimalist architectural logo sans", "sans-serif", "display", "arteon_arch",
                 GOOGLE_FONTS_CATALOG["instrument_sans"], GOOGLE_FONTS_CATALOG["spectral"]),
            ]
        else:
            # architectural_b2b & general: Swiss/Inktrap Neo-Grotesk display first (taste-skill §4.1), 1 sharp editorial alternative
            specs = [
                ("eco-1", f"Neo-Grotesca Vanguardia B2B ({mc_elem} · MC {mc_sign} / Inktrap)",
                 "inktrap", "inktrap modern grotesque sans font", "sans-serif", "sans", "nority_inktrap",
                 "grotesk", "swiss neo grotesque family sans", "sans-serif", "display", "xenon_nue",
                 GOOGLE_FONTS_CATALOG["plus_jakarta_sans"], GOOGLE_FONTS_CATALOG["space_grotesk"]),
                ("eco-2", f"Precisión Corporativa & Mono (BaZi {day_master} {bazi_info['element']} · Mes {params.get('bazi_month_element') or 'Metal'})",
                 "grotesk", "corporate geometric grotesk sans family", "sans-serif", "sans", "helvena_grotesk",
                 "monospace", "geometric monospace sans font", "sans-serif", "display", "lenia_mono",
                 GOOGLE_FONTS_CATALOG["dm_sans"], GOOGLE_FONTS_CATALOG["bricolage_grotesque"]),
                ("eco-3", f"Editorial Inktrap Ejecutivo (Nakshatra {nakshatra} · {nak_info['lord']})",
                 "inktrap", "modern inktrap editorial serif", "serif", "serif", "commune_inktrap_serif",
                 "minimal", "corporate display branding family sans", "sans-serif", "display", "gatger_corporate",
                 GOOGLE_FONTS_CATALOG["instrument_sans"], GOOGLE_FONTS_CATALOG["newsreader"]),
            ]

        ecosystems: List[Dict[str, Any]] = []
        for eid, ename, el_t1, app_q1, cat_slug1, cat_lbl1, fb1, el_t2, app_q2, cat_slug2, cat_lbl2, fb2, body_gf, bridge_gf in specs:
            prim = self._search_live_envato_fonts(el_t1, app_q1, cat_slug1, cat_lbl1) or self._get_fallback_envato_font(fb1)
            acc = self._search_live_envato_fonts(el_t2, app_q2, cat_slug2, cat_lbl2) or self._get_fallback_envato_font(fb2)
            ecosystems.append({
                "id": eid,
                "name": ename,
                "archetype": f"Perfil {style_profile} · MC {mc_sign} · Shadbala {params.get('shadbala_dominant') or 'Sun'}",
                "rationale": (
                    f"Vanguardia Envato ({prim['family']}, {prim.get('style')}) en titulares, lectura fluida en "
                    f"{body_gf['family']} (ratio {scale_ratio:.3f}, {mc_mod}) y sello en {acc['family']}."
                ),
                "web_fallback_display": bridge_gf,
                "tokens": self._pack_tokens(prim, body_gf, acc),
                "shortlist_candidates": {
                    "display_alternatives": prim.get("shortlist", []),
                    "accent_alternatives": acc.get("shortlist", []),
                },
                "layers": {
                    "logo": f"{acc['family']} (Weight 700, Tracking -0.02em)",
                    "slogan": f"{prim['family']} (Weight 500, Tracking +0.06em)",
                    "h1": f"{prim['family']} (Weight 700, Ratio {scale_ratio:.3f}, Tracking -0.025em)",
                    "h2": f"{prim['family']} (Weight 600, Ratio {scale_ratio:.3f})",
                    "body": f"{body_gf['family']} (Variable Regular 400, Line-height 1.60)",
                    "ui": f"{body_gf['family']} (Variable SemiBold 600, Tracking -0.01em)",
                },
                "cls_metric_overrides": self._cls_dict(body_gf),
                "workbench_presets": {"font_size_px": 60, "letter_spacing_em": bazi_info["tracking_em"], "line_height": 1.10, "text_transform": "none", "font_weight": "700", "ligatures_enabled": False},
            })

        return ecosystems

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
                "$description": f"Envato Elements — {prim['description']}",
                "source": "envato",
                "category": prim.get("category", "sans"),
                "item_uuid": prim.get("item_uuid") or _extract_uuid(prim["url"]),
                "url": prim["url"],
                "elements_url": prim.get("elements_url", prim["url"]),
                "search_url": prim.get("search_url", ""),
                "weights": prim["weights"],
            },
            "ui_secondary": {
                "$value": body["family"],
                "$type": "fontFamily",
                "$description": "Google Fonts v2 Variable — Workhorse tipográfico",
                "source": "google_fonts",
                "category": body.get("category", "sans"),
                "url": body["url"],
                "google_fonts_v2_url": body["google_fonts_v2_url"],
                "variable_axes": body["variable_axes"],
                "weights": body["weights"],
            },
            "accent_brand": {
                "$value": acc["family"],
                "$type": "fontFamily",
                "$description": f"Envato Elements — {acc['description']}",
                "source": "envato",
                "category": acc.get("category", "display"),
                "item_uuid": acc.get("item_uuid") or _extract_uuid(acc["url"]),
                "url": acc["url"],
                "elements_url": acc.get("elements_url", acc["url"]),
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

        clean_ecosystems = [{k: v for k, v in e.items() if k != "web_fallback_display"} for e in ecosystems]
        selected_clean = next((e for e in clean_ecosystems if e["id"] == selected_eco["id"]), clean_ecosystems[0])

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "brand": self.brand_upper,
            "vertical_slug": params.get("vertical_slug") or self.brand_lower,
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
                "anti_slop_bans_enforced": ["Fraunces", "Instrument Serif", "Inter", "wedding calligraphy", "retro 90s novelty"],
                "envato_upgrade_targets": {
                    "display_primary": selected_clean["tokens"]["display_primary"]["$value"],
                    "display_url": selected_clean["tokens"]["display_primary"]["url"],
                    "display_elements_url": selected_clean["tokens"]["display_primary"].get("elements_url", ""),
                    "accent_brand": selected_clean["tokens"]["accent_brand"]["$value"],
                    "accent_url": selected_clean["tokens"]["accent_brand"]["url"],
                    "accent_elements_url": selected_clean["tokens"]["accent_brand"].get("elements_url", ""),
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
                "generator": "fontgen_engine.py v4.1 (Vanguard Dual-Sort + Multi-Vertical)",
                "sort_mode": self.sort_mode,
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
        target_label = f"{self.brand_upper} / {manifest.get('vertical_slug', '')}"
        md = [
            f"# Dirección de Arte Tipográfica: {target_label}",
            f"> **Perfil:** `{manifest.get('style_profile')}` (`sort={self.sort_mode}`) · Sol en {meta.get('sun')}, MC {meta.get('midheaven')} "
            f"(Sideral {meta.get('sidereal_midheaven')}), Shadbala {meta.get('shadbala_dominant')}, "
            f"Day Master {meta.get('day_master')}, Nakshatra {meta.get('nakshatra')}.",
            "",
            "---",
            "",
        ]
        for idx, eco in enumerate(ecos, 1):
            t = eco["tokens"]
            p = eco.get("cls_metric_overrides", {})
            sc = eco.get("shortlist_candidates", {})
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
                "#### Alternativas Vanguardia en Envato (`shortlist_candidates`)",
                *[f"- **Alt Display:** `{a['family']}` (`{a['sort_source']}`, score `{a['score']}`) — {a['url']}" for a in sc.get("display_alternatives", [])],
                *[f"- **Alt Acento:** `{a['family']}` (`{a['sort_source']}`, score `{a['score']}`) — {a['url']}" for a in sc.get("accent_alternatives", [])],
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
        out_name = f"fontgen_{(manifest.get('vertical_slug') or self.brand_lower).lower()}.md"
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
            (self.output_dir / out_name).write_text(markdown, encoding="utf-8")
            if self.brand_lower != (manifest.get("vertical_slug") or "").lower():
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
    print("Running fontgen_engine v4.1 offline unit tests...")
    assert normalize_zodiac_sign("Géminis") == "Gemini"
    assert normalize_zodiac_sign("Tauro") == "Taurus"
    ef = FontgenEngine("TEST", use_live_search=False)
    for bad in ("Bringbold Nineties Retro Font", "Locatro Western Display", "Byte Craft Pixel Display", "Wedding Calligraphy Script", "Kliwon Terror Horror"):
        assert ef._is_noisy_title(bad) is True, f"Should reject noisy title: {bad}"
    assert ef._is_noisy_title("Nority - Inktrap Bold Font") is False
    assert ef._score_candidate("Nority - Inktrap Bold Font", True, True, "latest") > ef._score_candidate("Generic Logo", False, False, "popular")

    with tempfile.TemporaryDirectory(prefix="fontgen_v41_test_") as tmp:
        tp = Path(tmp)
        shards_p = tp / "client_dumps_15_shards.json"
        vert_b2b = tp / "acme-b2b.json"
        vert_cos = tp / "orion-cosmic.json"
        out_b2b = tp / "b2b"
        out_cos = tp / "cos"
        shards_p.write_text(json.dumps({
            "shard_01": {"data": {"tripod_of_iron": {"sun": {"sign": "Gemini"}, "midheaven_house_10": {"sign": "Gemini"}}}},
            "shard_02": {"data": {"fagan_bradley": {"midheaven": {"sign": "Taurus"}}}},
            "shard_03": {"data": {"shadbala": {"dominant_planet": "Sun"}, "nakshatra": {"name": "Chitra Pada 4", "lord": "Mars"}}},
            "shard_04": {"data": {"day_master": {"name": "Jia", "element": "Wood"}, "four_pillars": {"month": {"element": "Metal"}}}},
        }), encoding="utf-8")
        vert_b2b.write_text(json.dumps({
            "vertical_slug": "acme-b2b",
            "display_name": "Consultoría B2B e IA",
            "role_in_ecosystem": "Otra vertical derivada de Orion y Sabidurías Cósmicas.",
        }), encoding="utf-8")
        vert_cos.write_text(json.dumps({"vertical_slug": "orion-cosmic", "display_name": "Orion — Sabidurías Cósmicas & Arquetipos Vocacionales"}), encoding="utf-8")

        m_b2b, _ = FontgenEngine("TESTCORP", shards_path=shards_p, vertical_json_path=vert_b2b, output_dir=out_b2b, use_live_search=False).run()
        m_cos, _ = FontgenEngine("TESTCORP", shards_path=shards_p, vertical_json_path=vert_cos, output_dir=out_cos, use_live_search=False).run()

        assert m_b2b["style_profile"] == "architectural_b2b"
        assert m_cos["style_profile"] == "cosmic_archetypal"
        assert m_b2b["selected_ecosystem"]["tokens"]["display_primary"]["$value"] != m_cos["selected_ecosystem"]["tokens"]["display_primary"]["$value"]
        assert m_b2b["web_ready_bridge"]["display_fallback_family"] not in ("Fraunces", "Instrument Serif")
        assert m_cos["web_ready_bridge"]["display_fallback_family"] not in ("Fraunces", "Instrument Serif")
        assert len(m_b2b["candidate_ecosystems"][0]["shortlist_candidates"]["display_alternatives"]) >= 1
    assert not Path("/mnt/localstorage/TESTCORP").exists()
    print("✅ FONTGEN ENGINE v4.1 UNIT TESTS PASSED (Dual-Sort scorer, multi-vertical differentiation, 0 noise/Fraunces, 0 phantom dirs)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fontgen Engine v4.1 — Verified Vanguard Typographic Synthesizer")
    parser.add_argument("--brand", default="BRAND")
    parser.add_argument("--shards", type=Path, default=None)
    parser.add_argument("--brief", type=Path, default=None)
    parser.add_argument("--vertical-json", type=Path, default=None)
    parser.add_argument("--style-profile", default="auto", choices=["auto", "architectural_b2b", "cosmic_archetypal", "design_system_atelier", "editorial_manifesto", "editorial_brand"])
    parser.add_argument("--sort", default="hybrid", choices=["hybrid", "latest", "popular"])
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
        sort_mode=args.sort,
        seed=args.seed,
    )
    manifest, _ = engine.run(selected_eco_id=args.eco, dry_run=args.dry_run)
    sel = manifest["selected_ecosystem"]["tokens"]
    print(f"✅ FONTGEN ENGINE v4.1 COMPLETED FOR: {manifest['brand']}/{manifest['vertical_slug']} ({manifest['selected_ecosystem_id']}, profile={manifest['style_profile']}, sort={args.sort})")
    print(f"  • Display: {sel['display_primary']['$value']} ({sel['display_primary']['url']})")
    print(f"  • Body UI: {sel['ui_secondary']['$value']} ({sel['ui_secondary']['url']})")
    print(f"  • Accent:  {sel['accent_brand']['$value']} ({sel['accent_brand']['url']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
