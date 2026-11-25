#!/usr/bin/env python3
"""
fontgen_engine.py — Sovereign Agnostic Typographic Engine & Art Direction Matrix (v3.1).
Zero-Hallucination Design Synthesis | Real-Time Live Envato Sourcing | Anti-CLS Calibration.
Complies with W3C DTCG 2025.10 & font_manifest.schema.json (Draft 2020-12).

Architectural Invariants:
1. Never creates phantom top-level brand directories unless --create-brand-dirs is explicitly passed.
   When --output-dir is supplied, writes strictly to --output-dir.
2. Parses both English and Spanish zodiac signs/day-masters/nakshatras from astrobranding_*.md.
3. Live Envato search extracts itemUuid and optionally verifies font-preview.svg previewability.
4. Emits 3 differentiated hybrid ecosystems + Astro 5 experimental.fonts self-hosted web bridge.
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


# -----------------------------------------------------------------------------
# Curated Fallback Catalog (app.envato.com/fonts/{uuid})
# -----------------------------------------------------------------------------

ENVATO_VERIFIED_CATALOG: Dict[str, Dict[str, Any]] = {
    "luxury_editorial_serif": {
        "family": "Serif Luxury Logo",
        "item_uuid": "5e116044-15bd-48c4-9b0a-014c8b84214f",
        "url": "https://app.envato.com/fonts/5e116044-15bd-48c4-9b0a-014c8b84214f",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=luxury+serif",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Luxury Editorial Serif",
        "description": "High-fashion editorial serif with polished details and refined headline presence."
    },
    "modern_luxury_serif": {
        "family": "Kovase",
        "item_uuid": "d297622e-0d83-43a3-a96c-f3cc510fa84b",
        "url": "https://app.envato.com/fonts/d297622e-0d83-43a3-a96c-f3cc510fa84b",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=luxury+stencil+serif",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Dramatic Modern Editorial Stencil",
        "description": "Modern editorial stencil serif crafted for luxury branding and dramatic contrast."
    },
    "high_contrast_didone": {
        "family": "Taillevere",
        "item_uuid": "9dee7e7e-b2ad-42a9-8092-f674dc4bd330",
        "url": "https://app.envato.com/fonts/9dee7e7e-b2ad-42a9-8092-f674dc4bd330",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=didone+luxury+serif",
        "weights": ["400", "500", "700"],
        "category": "serif",
        "style": "Modern Didone",
        "description": "Sophisticated high-contrast Didone with razor-thin hairlines and dramatic vertical stress."
    },
    "vintage_didone": {
        "family": "Dogmade",
        "item_uuid": "1084a746-7c46-49eb-978b-b7043fd4212a",
        "url": "https://app.envato.com/fonts/1084a746-7c46-49eb-978b-b7043fd4212a",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=vintage+didone",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Vintage Didone Display",
        "description": "Noble vintage didone with expressive letterforms and editorial prestige."
    },
    "architectural_serif": {
        "family": "Domani",
        "item_uuid": "1de94cfa-3ac9-4fd1-b5b2-113405506be3",
        "url": "https://app.envato.com/fonts/1de94cfa-3ac9-4fd1-b5b2-113405506be3",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=architectural+serif",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Architectural Inscriptional Serif",
        "description": "Monumental stone-carved serif inspired by classical architecture."
    },
    "romanesque_display": {
        "family": "Trabuline",
        "item_uuid": "72c6db75-b4a2-482c-9392-9d7ae5559c6a",
        "url": "https://app.envato.com/fonts/72c6db75-b4a2-482c-9392-9d7ae5559c6a",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=roman+titling+serif",
        "weights": ["600", "700"],
        "category": "serif",
        "style": "Romanesque Titling",
        "description": "Modern romanesque display inspired by stone-carved titling with discretionary ligatures."
    },
    "monogram_holder": {
        "family": "Monogram Holder",
        "item_uuid": "b072395d-990e-4637-a1ca-2c8b0355aed0",
        "url": "https://app.envato.com/fonts/b072395d-990e-4637-a1ca-2c8b0355aed0",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=monogram+display+font",
        "weights": ["700", "900"],
        "category": "display",
        "style": "Interlocking Monogram Slab",
        "description": "Specialized monogram font engineered for interlocking two-letter logos and brand seals."
    },
    "clarissa_monogram": {
        "family": "Clarissa Monogram",
        "item_uuid": "75702d55-4518-452d-ad4c-bad5fb47ea70",
        "url": "https://app.envato.com/fonts/75702d55-4518-452d-ad4c-bad5fb47ea70",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=monogram+ligature+logo",
        "weights": ["600", "800"],
        "category": "display",
        "style": "Luxury Monogram Ligature",
        "description": "Refined brand emblem font featuring ornate interlocking ligatures."
    },
    "clean_geometric_sans": {
        "family": "Franie",
        "item_uuid": "40b427aa-a786-4f98-9ebb-ef68413188e1",
        "url": "https://app.envato.com/fonts/40b427aa-a786-4f98-9ebb-ef68413188e1",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=geometric+sans",
        "weights": ["300", "400", "500", "600", "700"],
        "category": "sans",
        "style": "Clean Modern Geometric Sans",
        "description": "Functional workhorse geometric sans with crisp open apertures and modernist warmth."
    },
    "geometric_minimalist_sans": {
        "family": "Geometric Sans",
        "item_uuid": "af397135-1d09-413c-a77e-aa808c600301",
        "url": "https://app.envato.com/fonts/af397135-1d09-413c-a77e-aa808c600301",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=minimalist+sans+font",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Minimalist Bauhaus Sans",
        "description": "Minimalist architectural sans serif with balanced proportions."
    },
    "modern_grotesk_stencil": {
        "family": "Akmorn Grotesque",
        "item_uuid": "c1ffdc86-c80d-45ec-92ae-6c69615d1086",
        "url": "https://app.envato.com/fonts/c1ffdc86-c80d-45ec-92ae-6c69615d1086",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=modern+grotesque+sans",
        "weights": ["400", "600", "700", "800"],
        "category": "sans",
        "style": "Industrial Neo-Grotesque",
        "description": "Clean neo-grotesque with modular precision and sharp angular cuts."
    },
    "industrial_grotesk": {
        "family": "Berghan",
        "item_uuid": "b1456d39-bfa8-4726-8439-e2fb8ca23fc3",
        "url": "https://app.envato.com/fonts/b1456d39-bfa8-4726-8439-e2fb8ca23fc3",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=modern+grotesk",
        "weights": ["500", "700", "800"],
        "category": "sans",
        "style": "Modern Technical Grotesk",
        "description": "Solid architectural grotesk with robust vertical rhythm."
    },
    "modern_brutalist": {
        "family": "Riot Cut",
        "item_uuid": "7628b08f-35c3-4f95-b4db-455fb0486a43",
        "url": "https://app.envato.com/fonts/7628b08f-35c3-4f95-b4db-455fb0486a43",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=brutalist+font",
        "weights": ["700", "800", "900"],
        "category": "display",
        "style": "Brutalist Kinetic Display",
        "description": "Heavy kinetic brutalist display typography with tight tracking."
    },
    "brutalist_display": {
        "family": "Aurora",
        "item_uuid": "c13eba79-5b72-4c20-938f-6b0826a29745",
        "url": "https://app.envato.com/fonts/c13eba79-5b72-4c20-938f-6b0826a29745",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=brutalist+display+typeface",
        "weights": ["700", "800"],
        "category": "display",
        "style": "Avant-Garde Brutalist Display",
        "description": "Disruptive avant-garde display typeface engineered for bold titling."
    },
    "luxury_calligraphy": {
        "family": "Script Calligraphy",
        "item_uuid": "74af1b1d-ec22-4b99-8df0-bfd011bf9dab",
        "url": "https://app.envato.com/fonts/74af1b1d-ec22-4b99-8df0-bfd011bf9dab",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=script+calligraphy",
        "weights": ["400", "600"],
        "category": "script",
        "style": "Luxury Romantic Calligraphy",
        "description": "Aristocratic calligraphy with fluid swashes and delicate flourished ligatures."
    },
    "wedding_script": {
        "family": "Teofandin Levantamy",
        "item_uuid": "e3eb7b1e-8b7f-4aae-9bfe-febec528c6bd",
        "url": "https://app.envato.com/fonts/e3eb7b1e-8b7f-4aae-9bfe-febec528c6bd",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=wedding+calligraphy+script",
        "weights": ["400", "600"],
        "category": "script",
        "style": "Bespoke Flourished Script",
        "description": "Handcrafted copperplate calligraphic script featuring alternate glyphs."
    },
    "elegant_serif_display": {
        "family": "Swarsh Daisy",
        "item_uuid": "354d8330-5a2a-4196-a03c-ab5ebd7f6dab",
        "url": "https://app.envato.com/fonts/354d8330-5a2a-4196-a03c-ab5ebd7f6dab",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=elegant+serif+display",
        "weights": ["400", "600"],
        "category": "serif",
        "style": "Flourished Editorial Serif",
        "description": "Graceful display serif with botanical swashes and gentle curves."
    },
    "monogram_emblem": {
        "family": "Seals Monogram",
        "item_uuid": "36b5532e-f307-4c1f-818f-2ceeaecb9fb3",
        "url": "https://app.envato.com/fonts/36b5532e-f307-4c1f-818f-2ceeaecb9fb3",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=monogram+brand+seal+font",
        "weights": ["700", "900"],
        "category": "display",
        "style": "Heraldic Brand Seal Monogram",
        "description": "Geometric seal monogram font engineered for crests and brand insignias."
    }
}

GOOGLE_FONTS_CATALOG: Dict[str, Dict[str, Any]] = {
    "instrument_sans": {
        "family": "Instrument Sans",
        "url": "https://fonts.google.com/specimen/Instrument+Sans",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Instrument+Sans:ital,wdth,wght@0,75..100,400..700;1,75..100,400..700&display=swap",
        "variable_axes": "ital,wdth,wght@0..1,75..100,400..700",
        "weights": ["400", "500", "600", "700"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "99.0%", "ascent": "94.0%", "descent": "23.0%", "line_gap": "0%"}
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
    "urbanist": {
        "family": "Urbanist",
        "url": "https://fonts.google.com/specimen/Urbanist",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Urbanist:ital,wght@0,100..900;1,100..900&display=swap",
        "variable_axes": "ital,wght@0..1,100..900",
        "weights": ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "99.5%", "ascent": "93.0%", "descent": "22.0%", "line_gap": "0%"}
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
    "fraunces": {
        "family": "Fraunces",
        "url": "https://fonts.google.com/specimen/Fraunces",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,100..900,0..100,0..1;1,9..144,100..900,0..100,0..1&display=swap",
        "variable_axes": "ital,opsz,wght,SOFT,WONK@0..1,9..144,100..900,0..100,0..1",
        "weights": ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
        "category": "serif",
        "cls": {"fallback": "Times New Roman", "size_adjust": "101.5%", "ascent": "98.0%", "descent": "27.0%", "line_gap": "0%"}
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
    "plus_jakarta_sans": {
        "family": "Plus Jakarta Sans",
        "url": "https://fonts.google.com/specimen/Plus+Jakarta+Sans",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap",
        "variable_axes": "ital,wght@0..1,200..800",
        "weights": ["200", "300", "400", "500", "600", "700", "800"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "98.5%", "ascent": "92.0%", "descent": "24.0%", "line_gap": "0%"}
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
    "Jia": {"element": "Wood", "polarity": "Yang", "tracking_em": -0.01},
    "Yi": {"element": "Wood", "polarity": "Yin", "tracking_em": 0.02},
    "Bing": {"element": "Fire", "polarity": "Yang", "tracking_em": 0.03},
    "Ding": {"element": "Fire", "polarity": "Yin", "tracking_em": 0.01},
    "Wu": {"element": "Earth", "polarity": "Yang", "tracking_em": 0.00},
    "Ji": {"element": "Earth", "polarity": "Yin", "tracking_em": 0.015},
    "Geng": {"element": "Metal", "polarity": "Yang", "tracking_em": -0.02},
    "Xin": {"element": "Metal", "polarity": "Yin", "tracking_em": 0.04},
    "Ren": {"element": "Water", "polarity": "Yang", "tracking_em": 0.01},
    "Gui": {"element": "Water", "polarity": "Yin", "tracking_em": 0.025}
}

NAKSHATRA_FEATURES = {
    "Ashwini": {"feature": "dlig 1, ss01 1", "accent_archetype": "monogram_holder"},
    "Bharani": {"feature": "swsh 1", "accent_archetype": "clarissa_monogram"},
    "Krittika": {"feature": "titl 1", "accent_archetype": "romanesque_display"},
    "Rohini": {"feature": "calt 1, liga 1", "accent_archetype": "luxury_calligraphy"},
    "Mrigashira": {"feature": "ss02 1", "accent_archetype": "clarissa_monogram"},
    "Ardra": {"feature": "zero 1", "accent_archetype": "modern_grotesk_stencil"},
    "Punarvasu": {"feature": "liga 1", "accent_archetype": "luxury_calligraphy"},
    "Pushya": {"feature": "titl 1, cscp 1", "accent_archetype": "monogram_holder"},
    "Ashlesha": {"feature": "swsh 1, dlig 1", "accent_archetype": "wedding_script"},
    "Magha": {"feature": "titl 1", "accent_archetype": "architectural_serif"},
    "Purva Phalguni": {"feature": "calt 1", "accent_archetype": "luxury_calligraphy"},
    "Uttara Phalguni": {"feature": "liga 1", "accent_archetype": "monogram_holder"},
    "Hasta": {"feature": "ss01 1", "accent_archetype": "clarissa_monogram"},
    "Chitra": {"feature": "dlig 1, calt 1", "accent_archetype": "monogram_emblem"},
    "Swati": {"feature": "swsh 1", "accent_archetype": "wedding_script"},
    "Vishakha": {"feature": "titl 1", "accent_archetype": "architectural_serif"},
    "Anuradha": {"feature": "calt 1, liga 1", "accent_archetype": "luxury_calligraphy"},
    "Jyeshtha": {"feature": "cscp 1", "accent_archetype": "monogram_holder"},
    "Mula": {"feature": "ss04 1", "accent_archetype": "modern_brutalist"},
    "Purva Ashadha": {"feature": "swsh 1", "accent_archetype": "luxury_calligraphy"},
    "Uttara Ashadha": {"feature": "titl 1", "accent_archetype": "architectural_serif"},
    "Shravana": {"feature": "liga 1, calt 1", "accent_archetype": "clarissa_monogram"},
    "Dhanishta": {"feature": "ss01 1", "accent_archetype": "modern_grotesk_stencil"},
    "Shatabhisha": {"feature": "zero 1", "accent_archetype": "industrial_grotesk"},
    "Purva Bhadrapada": {"feature": "ss05 1", "accent_archetype": "brutalist_display"},
    "Uttara Bhadrapada": {"feature": "liga 1", "accent_archetype": "wedding_script"},
    "Revati": {"feature": "calt 1, swsh 1", "accent_archetype": "luxury_calligraphy"}
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
    Sovereign Agnostic Typographic Engine (v3.1).
    Zero global phantom mkdir side-effects. Strict workspace/output-dir isolation.
    """

    def __init__(
        self,
        brand: str,
        shards_path: Optional[Path] = None,
        brief_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        use_live_search: bool = True,
        allow_default: bool = False,
        override_params: Optional[Dict[str, Any]] = None,
        create_brand_dirs: bool = False,
        verify_svg_preview: bool = True,
    ):
        self.brand_raw = brand.strip()
        self.brand_upper = self.brand_raw.upper()
        self.brand_lower = self.brand_raw.lower()
        self.shards_path = Path(shards_path).resolve() if shards_path else None
        self.brief_path = Path(brief_path).resolve() if brief_path else None
        self.output_dir = Path(output_dir).resolve() if output_dir else None
        self.use_live_search = use_live_search
        self.allow_default = allow_default
        self.override_params = override_params or {}
        self.create_brand_dirs = create_brand_dirs
        self.verify_svg_preview = verify_svg_preview
        self.used_families: Set[str] = set()

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
                            child / "dev" / "_shared",
                            child / "dev" / "workspaces" / self.brand_lower / "brand",
                            child / "dev" / "workspaces" / self.brand_lower,
                            child / "workspaces" / self.brand_lower / "brand",
                            child / "brand",
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
            r"\b(Font|Typeface|Family|Display|Serif|Sans|Grotesk|Grotesque|Script|Calligraphy|Vintage|Modern|Luxury|Bold|Retro)\b",
            "", first_part, flags=re.IGNORECASE,
        ).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned.title() if len(cleaned) >= 2 else first_part.strip().title()

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

    def _search_live_envato_fonts(self, query: str, category: str = "serif", default_weights: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        if not self.use_live_search:
            return None
        search_url = f"https://app.envato.com/search?itemType=fonts&term={urllib.parse.quote_plus(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                html_text = resp.read().decode("utf-8", errors="ignore")

            chunks = re.findall(r'<a[^>]+data-analytics-item_id="[^"]+"[^>]*>', html_text)
            for c in chunks[:15]:
                m_id = re.search(r'data-analytics-item_id="([^"]+)"', c)
                m_title = re.search(r'data-analytics-item_title="([^"]+)"', c)
                m_author = re.search(r'data-analytics-item_author="([^"]+)"', c)
                if not (m_id and m_title):
                    continue
                fid = m_id.group(1).strip()
                title = m_title.group(1).strip()
                author = m_author.group(1).strip() if m_author else "Envato Author"
                family = self._clean_family_name(title)
                if family.lower() in [f.lower() for f in self.used_families]:
                    continue
                if not self._is_previewable_uuid(fid):
                    continue
                self.used_families.add(family)
                return {
                    "family": family,
                    "item_uuid": fid,
                    "url": f"https://app.envato.com/fonts/{fid}",
                    "search_url": search_url,
                    "weights": default_weights or ["400", "600", "700"],
                    "category": category,
                    "style": f"Live Envato Sourcing ({query})",
                    "description": f"{title} by {author} on Envato Elements Pro."
                }
        except Exception:
            pass
        return None

    def _get_fallback_envato_font(self, archetype_key: str) -> Dict[str, Any]:
        candidate = ENVATO_VERIFIED_CATALOG.get(archetype_key)
        if candidate and candidate["family"].lower() not in [f.lower() for f in self.used_families]:
            self.used_families.add(candidate["family"])
            return candidate
        for v in ENVATO_VERIFIED_CATALOG.values():
            if v["family"].lower() not in [f.lower() for f in self.used_families]:
                self.used_families.add(v["family"])
                return v
        return ENVATO_VERIFIED_CATALOG["luxury_editorial_serif"]

    def resolve_inputs(self) -> Dict[str, Any]:
        data = {"sun_sign": "", "mc_sign": "", "day_master": "", "nakshatra": "", "dominant_element": ""}

        if self.override_params:
            for k in data:
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
                return data

        search_dirs = self._discover_search_dirs()

        # 1. Brief first when explicitly passed, else Shards
        candidates: List[Path] = []
        if self.brief_path and self.brief_path.exists():
            candidates.append(self.brief_path)

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

        if not candidates and shards_target and shards_target.exists():
            try:
                content = json.loads(shards_target.read_text(encoding="utf-8"))
                s1 = content.get("shard_01", {}).get("data", {})
                s3 = content.get("shard_03", {}).get("data", {})
                s4 = content.get("shard_04", {}).get("data", {})
                tripod = s1.get("tripod_of_iron", {})
                if tripod.get("sun", {}).get("sign"):
                    data["sun_sign"] = normalize_zodiac_sign(tripod["sun"]["sign"])
                if tripod.get("midheaven_house_10", {}).get("sign"):
                    data["mc_sign"] = normalize_zodiac_sign(tripod["midheaven_house_10"]["sign"])
                if s4.get("day_master", {}).get("name"):
                    data["day_master"] = s4["day_master"]["name"].split()[0]
                if s3.get("nakshatra", {}).get("name"):
                    data["nakshatra"] = s3["nakshatra"]["name"].split()[0]
                if data["sun_sign"] and data["mc_sign"]:
                    data["dominant_element"] = ZODIAC_ELEMENTS.get(data["sun_sign"], "Earth")
                    data["day_master"] = data["day_master"] or "Wu"
                    data["nakshatra"] = data["nakshatra"] or "Ashwini"
                    return data
            except Exception:
                pass

        for sdir in search_dirs:
            if not sdir.exists():
                continue
            for cand in (
                sdir / f"astrobranding_{self.brand_lower}.md",
                sdir / "raw" / "llm" / f"astrobranding_{self.brand_lower}.md",
            ):
                if cand.exists() and cand not in candidates:
                    candidates.append(cand)

        for c in candidates:
            if not c.is_file():
                continue
            try:
                txt = c.read_text(encoding="utf-8", errors="replace")
                m_sun = re.search(r"\|\s*\*\*Sol Natal\*\*\s*\|\s*\*\*([A-Za-zÁÉÍÓÚáéíóú]+)", txt) or re.search(r"(?:Sun Natal|Sol Natal|Sol)[\s:\*|]+(?:en\s+\*\*)?([A-Za-zÁÉÍÓÚáéíóú]+)", txt, re.IGNORECASE)
                m_mc = re.search(r"\|\s*\*\*Medio Cielo[^*]*\*\*\s*\|\s*\*\*([A-Za-zÁÉÍÓÚáéíóú]+)", txt) or re.search(r"(?:Midheaven|Medio Cielo)[\s:\*|]+(?:en\s+\*\*)?([A-Za-zÁÉÍÓÚáéíóú]+)", txt, re.IGNORECASE)
                m_nak = re.search(r"\*\*Nakshatra[^:\n]*:\*\*\s*([A-Za-z]+(?:\s+[A-Za-z]+)?)", txt) or re.search(r"Nakshatra[\s:\*|]+\*{0,2}([A-Za-z]+)", txt, re.IGNORECASE)
                m_dm = re.search(r"\*\*Day Master:\*\*\s*([A-Za-z]+)", txt) or re.search(r"Day Master[\s:\*|]+([A-Za-z]+)", txt, re.IGNORECASE)

                if m_sun:
                    data["sun_sign"] = normalize_zodiac_sign(m_sun.group(1))
                if m_mc:
                    data["mc_sign"] = normalize_zodiac_sign(m_mc.group(1))
                if m_nak:
                    nak_cand = m_nak.group(1).strip().split()[0]
                    if nak_cand in NAKSHATRA_FEATURES or len(m_nak.group(1).split()) == 1:
                        data["nakshatra"] = nak_cand
                    elif m_nak.group(1).strip() in NAKSHATRA_FEATURES:
                        data["nakshatra"] = m_nak.group(1).strip()
                    else:
                        data["nakshatra"] = nak_cand
                if m_dm:
                    data["day_master"] = m_dm.group(1).strip()

                if data["sun_sign"] and data["mc_sign"]:
                    data["dominant_element"] = ZODIAC_ELEMENTS.get(data["sun_sign"], "Earth")
                    data["day_master"] = data["day_master"] or "Wu"
                    data["nakshatra"] = data["nakshatra"] or "Ashwini"
                    return data
            except Exception:
                pass

        if not (data["sun_sign"] and data["mc_sign"]):
            if not self.allow_default:
                raise FileNotFoundError(
                    f"No valid astrobranding brief or 15-shards data found for '{self.brand_raw}'. "
                    f"Checked {[str(c) for c in candidates[:6]]}. Supply --brief or --shards explicitly."
                )
            data = {"sun_sign": "Capricorn", "mc_sign": "Virgo", "day_master": "Wu", "nakshatra": "Ashwini", "dominant_element": "Earth"}
        return data

    def build_ecosystems(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        sun_sign = params.get("sun_sign", "Capricorn")
        mc_sign = params.get("mc_sign", "Virgo")
        day_master = params.get("day_master", "Wu")
        nakshatra = params.get("nakshatra", "Ashwini")

        mc_elem = ZODIAC_ELEMENTS.get(mc_sign, "Earth")
        mc_mod = ZODIAC_MODALITIES.get(mc_sign, "Cardinal")
        scale_ratio = MODALITY_SCALE_RATIOS.get(mc_mod, 1.333)
        bazi_info = BAZI_MODULATIONS.get(day_master, BAZI_MODULATIONS["Wu"])
        nak_info = NAKSHATRA_FEATURES.get(nakshatra, {"feature": "liga 1", "accent_archetype": "monogram_emblem"})

        # Ecosystem 1: MC + Sun Authority
        if mc_elem == "Earth":
            fb_p1, q_p1, eco1_body = "architectural_serif", "luxury architectural editorial serif font", GOOGLE_FONTS_CATALOG["spectral"]
        elif mc_elem == "Water":
            fb_p1, q_p1, eco1_body = "high_contrast_didone", "high contrast didone editorial serif font", GOOGLE_FONTS_CATALOG["newsreader"]
        elif mc_elem == "Fire":
            fb_p1, q_p1, eco1_body = "romanesque_display", "royal inscriptional titling serif font", GOOGLE_FONTS_CATALOG["instrument_sans"]
        else:
            fb_p1, q_p1, eco1_body = "modern_luxury_serif", "modern luxury editorial serif font", GOOGLE_FONTS_CATALOG["manrope"]

        fb_a1, q_a1 = ("monogram_emblem", "modern geometric monogram brand seal font") if mc_elem in ("Air", "Fire") else ("monogram_holder", "interlocking luxury monogram brand seal font")
        eco1_prim = self._search_live_envato_fonts(q_p1, "serif") or self._get_fallback_envato_font(fb_p1)
        eco1_acc = self._search_live_envato_fonts(q_a1, "display") or self._get_fallback_envato_font(fb_a1)

        eco1 = {
            "id": "eco-1",
            "name": f"Autoridad Editorial ({mc_elem} · MC {mc_sign})",
            "archetype": f"Proyección Pública MC {mc_sign} & Sol {sun_sign}",
            "rationale": f"Contraste editorial entre {eco1_prim['family']} en titulares y lectura continua con {eco1_body['family']} (ratio {scale_ratio:.3f}, {mc_mod}), sello en {eco1_acc['family']}.",
            "tokens": self._pack_tokens(eco1_prim, eco1_body, eco1_acc),
            "layers": {
                "logo": f"{eco1_acc['family']} (Weight 900)",
                "slogan": f"{eco1_prim['family']} (Weight 400, Tracking +0.15em, Uppercase)",
                "h1": f"{eco1_prim['family']} (Weight 600, Ratio {scale_ratio:.3f})",
                "h2": f"{eco1_prim['family']} (Weight 500, Scale {scale_ratio:.3f}x down)",
                "body": f"{eco1_body['family']} (Variable Regular 400, Line-height 1.55)",
                "ui": f"{eco1_body['family']} (Variable SemiBold 600, Tracking -0.01em)"
            },
            "cls_metric_overrides": self._cls_dict(eco1_body),
            "workbench_presets": {"font_size_px": 64, "letter_spacing_em": 0.04, "line_height": 1.15, "text_transform": "none", "font_weight": "600", "ligatures_enabled": True}
        }

        # Ecosystem 2: BaZi Precision
        if bazi_info["element"] in ("Metal", "Fire"):
            q_p2, q_a2, fb_p2, fb_a2, eco2_body = "kinetic brutalist display heavy typeface", "geometric display logo font", "modern_brutalist", "brutalist_display", GOOGLE_FONTS_CATALOG["bricolage_grotesque"]
        elif bazi_info["element"] == "Wood":
            q_p2, q_a2, fb_p2, fb_a2, eco2_body = "clean contemporary geometric sans typeface", "modern architectural emblem logo font", "clean_geometric_sans", "clarissa_monogram", GOOGLE_FONTS_CATALOG["urbanist"]
        else:
            q_p2, q_a2, fb_p2, fb_a2, eco2_body = "modular structured geometric grotesk display", "monogram brand seal emblem font", "modern_grotesk_stencil", "monogram_emblem", GOOGLE_FONTS_CATALOG["instrument_sans"]

        eco2_prim = self._search_live_envato_fonts(q_p2, "sans") or self._get_fallback_envato_font(fb_p2)
        eco2_acc = self._search_live_envato_fonts(q_a2, "display") or self._get_fallback_envato_font(fb_a2)

        eco2 = {
            "id": "eco-2",
            "name": f"Precisión Estructural ({bazi_info['element']} · BaZi {day_master})",
            "archetype": f"Rigor Técnico BaZi {day_master} ({bazi_info['polarity']})",
            "rationale": f"Arquitectura contemporánea con {eco2_prim['family']} y UI ultrarrápida con {eco2_body['family']} (tracking {bazi_info['tracking_em']}em).",
            "tokens": self._pack_tokens(eco2_prim, eco2_body, eco2_acc),
            "layers": {
                "logo": f"{eco2_acc['family']} (Weight 800)",
                "slogan": f"{eco2_prim['family']} (Weight 500, Tracking +0.20em, Uppercase)",
                "h1": f"{eco2_prim['family']} (Weight 700, Ratio {scale_ratio:.3f})",
                "h2": f"{eco2_prim['family']} (Weight 600, Ratio {scale_ratio:.3f})",
                "body": f"{eco2_body['family']} (Variable Regular 400, Line-height 1.50)",
                "ui": f"{eco2_body['family']} (Variable Bold 700, Tracking -0.02em)"
            },
            "cls_metric_overrides": self._cls_dict(eco2_body),
            "workbench_presets": {"font_size_px": 56, "letter_spacing_em": bazi_info["tracking_em"], "line_height": 1.10, "text_transform": "uppercase", "font_weight": "700", "ligatures_enabled": False}
        }

        # Ecosystem 3: Nakshatra Signature
        fb_a3 = nak_info.get("accent_archetype", "wedding_script")
        if mc_elem == "Water" or day_master in ("Ren", "Gui"):
            q_p3, fb_p3, eco3_body = "modern high contrast didone luxury serif font", "high_contrast_didone", GOOGLE_FONTS_CATALOG["spectral"]
        else:
            q_p3, fb_p3, eco3_body = f"editorial luxury serif font {nakshatra.lower()}", "elegant_serif_display", GOOGLE_FONTS_CATALOG["fraunces"]
        q_a3 = "bespoke luxury calligraphy script font"

        eco3_prim = self._search_live_envato_fonts(q_p3, "serif") or self._get_fallback_envato_font(fb_p3)
        eco3_acc = self._search_live_envato_fonts(q_a3, "script") or self._get_fallback_envato_font(fb_a3)

        eco3 = {
            "id": "eco-3",
            "name": f"Firma Artesanal (Nakshatra {nakshatra})",
            "archetype": f"Esencia Védica {nakshatra} ({nak_info['feature']})",
            "rationale": f"Síntesis orgánica entre {eco3_prim['family']} y la calidez de {eco3_body['family']}, con acento caligráfico/emblema {eco3_acc['family']}.",
            "tokens": self._pack_tokens(eco3_prim, eco3_body, eco3_acc),
            "layers": {
                "logo": f"{eco3_acc['family']} (Weight 900)",
                "slogan": f"{eco3_prim['family']} (Weight 400, Italic, Tracking +0.10em)",
                "h1": f"{eco3_prim['family']} (Weight 600, Ratio {scale_ratio:.3f})",
                "h2": f"{eco3_prim['family']} (Weight 400, Italic)",
                "body": f"{eco3_body['family']} (Variable Regular 400, Line-height 1.60)",
                "ui": f"{eco3_body['family']} (Variable SemiBold 600, Tracking 0.00em)"
            },
            "cls_metric_overrides": self._cls_dict(eco3_body),
            "workbench_presets": {"font_size_px": 68, "letter_spacing_em": 0.02, "line_height": 1.20, "text_transform": "none", "font_weight": "500", "ligatures_enabled": True}
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

        # Astro 5 self-hosted web bridge using verified Google Fonts Variable from the ecosystems
        disp_google = GOOGLE_FONTS_CATALOG["fraunces"] if ecosystems[2]["tokens"]["ui_secondary"]["$value"] == "Fraunces" else GOOGLE_FONTS_CATALOG["newsreader"]
        body_google = ecosystems[0]["tokens"]["ui_secondary"]

        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "brand": self.brand_upper,
            "selected_ecosystem_id": selected_eco["id"],
            "candidate_ecosystems": ecosystems,
            "selected_ecosystem": selected_eco,
            "web_ready_bridge": {
                "delivery": "astro_5_experimental_fonts_self_hosted",
                "display_fallback_family": disp_google["family"],
                "display_fallback_v2_url": disp_google["google_fonts_v2_url"],
                "body_family": body_google["$value"],
                "body_v2_url": body_google["google_fonts_v2_url"],
                "mono_family": "JetBrains Mono",
                "envato_upgrade_targets": {
                    "display_primary": selected_eco["tokens"]["display_primary"]["$value"],
                    "display_url": selected_eco["tokens"]["display_primary"]["url"],
                    "accent_brand": selected_eco["tokens"]["accent_brand"]["$value"],
                    "accent_url": selected_eco["tokens"]["accent_brand"]["url"],
                },
            },
            "inheritance": {
                "logo": selected_eco["layers"]["logo"],
                "slogan": selected_eco["layers"]["slogan"],
                "h1": selected_eco["layers"]["h1"],
                "h2": selected_eco["layers"]["h2"],
                "body": selected_eco["layers"]["body"],
                "ui": selected_eco["layers"]["ui"],
                "ui_buttons": selected_eco["layers"]["ui"],
            },
            "metadata": {
                "generator": "fontgen_engine.py v3.1 (Live Envato + Zero-Pollution)",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "astrological_grounding": {
                    "sun": f"{params.get('sun_sign')} ({ZODIAC_ELEMENTS.get(params.get('sun_sign'), 'Earth')})",
                    "midheaven": f"{params.get('mc_sign')} ({ZODIAC_ELEMENTS.get(params.get('mc_sign'), 'Earth')})",
                    "day_master": params.get("day_master"),
                    "nakshatra": params.get("nakshatra"),
                },
            },
        }

    def generate_markdown_sheet(self, manifest: Dict[str, Any]) -> str:
        meta = manifest.get("metadata", {}).get("astrological_grounding", {})
        ecos = manifest.get("candidate_ecosystems", [])
        md = [
            f"# Dirección de Arte Tipográfica: {self.brand_upper}",
            f"> **Resumen:** Sol en {meta.get('sun')}, Medio Cielo en {meta.get('midheaven')}, "
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
                f"3. **Token de Acento (Monograma/Firma):** `{t['accent_brand']['$value']}` — [Envato]({t['accent_brand']['url']}) (UUID `{t['accent_brand'].get('item_uuid','')}`)",
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

        # Without explicit --output-dir: write ONLY to already-existing brand dirs, never mkdir phantoms
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
    output_dir: Optional[Path] = None,
    selected_eco_id: str = "eco-1",
    use_live_search: bool = True,
    allow_default: bool = False,
) -> Dict[str, Any]:
    engine = FontgenEngine(
        brand=brand,
        shards_path=shards_path,
        brief_path=brief_path,
        output_dir=output_dir,
        use_live_search=use_live_search,
        allow_default=allow_default,
    )
    manifest, _ = engine.run(selected_eco_id=selected_eco_id, dry_run=False)
    return manifest


def run_unit_tests() -> int:
    print("Running fontgen_engine v3.1 offline unit tests...")
    assert normalize_zodiac_sign("Géminis") == "Gemini"
    assert normalize_zodiac_sign("Tauro") == "Taurus"
    with tempfile.TemporaryDirectory(prefix="fontgen_test_") as tmp:
        tp = Path(tmp)
        brief_p = tp / "astrobranding_aurelius.md"
        out_p = tp / "ws_brand"
        brief_p.write_text(
            "# Brief AURELIUS\n| **Sol Natal** | **Géminis 19.01°** |\n| **Medio Cielo** | **Acuario 12.00°** |\n"
            "**Nakshatra:** Chitra Pada 4\n**Day Master:** Jia (Wood)\n",
            encoding="utf-8",
        )
        engine = FontgenEngine("AURELIUS", brief_path=brief_p, output_dir=out_p, use_live_search=False)
        manifest, _ = engine.run()
        assert manifest["metadata"]["astrological_grounding"]["sun"].startswith("Gemini")
        assert manifest["metadata"]["astrological_grounding"]["midheaven"].startswith("Aquarius")
        assert len(manifest["candidate_ecosystems"]) == 3
        fams = [e["tokens"]["display_primary"]["$value"] for e in manifest["candidate_ecosystems"]]
        assert len(set(fams)) == 3, f"Repeated display fonts: {fams}"
        assert (out_p / "font_manifest.json").exists()
        assert (out_p / "fontgen_aurelius.md").exists()
    assert not Path("/mnt/localstorage/AURELIUS").exists(), "Phantom folder created!"
    assert not Path("/var/www/baiosfera/PROYECTOS/AURELIUS").exists(), "Phantom Drive folder created!"
    print("✅ FONTGEN ENGINE v3.1 UNIT TESTS PASSED (Bilingual ES/EN, 3 unique ecos, 0 phantom dirs)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fontgen Engine v3.1 — Verified Typographic Synthesizer")
    parser.add_argument("--brand", default="BRAND", help="Brand or vertical name")
    parser.add_argument("--shards", type=Path, default=None, help="Path to client_dumps_15_shards.json")
    parser.add_argument("--brief", type=Path, default=None, help="Path to astrobranding_<brand>.md")
    parser.add_argument("--output-dir", type=Path, default=None, help="Explicit target directory for outputs")
    parser.add_argument("--eco", default="eco-1", choices=["eco-1", "eco-2", "eco-3"], help="Selected ecosystem ID")
    parser.add_argument("--dry-run", action="store_true", help="Calculate without writing to disk")
    parser.add_argument("--no-live", action="store_true", help="Disable live search on Envato")
    parser.add_argument("--allow-default", action="store_true", help="Allow neutral fallback if no brief/shards found")
    parser.add_argument("--create-brand-dirs", action="store_true", help="Allow creating top-level brand dirs when --output-dir is omitted")
    parser.add_argument("--sun-sign", default=None)
    parser.add_argument("--mc-sign", default=None)
    parser.add_argument("--day-master", default=None)
    parser.add_argument("--nakshatra", default=None)
    parser.add_argument("--dominant-element", default=None)
    parser.add_argument("--test", action="store_true", help="Run deterministic offline unit tests")
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
        output_dir=args.output_dir,
        use_live_search=not args.no_live,
        allow_default=args.allow_default,
        override_params=override_params or None,
        create_brand_dirs=args.create_brand_dirs,
    )
    manifest, _ = engine.run(selected_eco_id=args.eco, dry_run=args.dry_run)
    sel = manifest["selected_ecosystem"]["tokens"]
    print(f"✅ FONTGEN ENGINE v3.1 COMPLETED FOR: {args.brand.upper()} ({manifest['selected_ecosystem_id']})")
    print(f"  • Display: {sel['display_primary']['$value']} ({sel['display_primary']['url']})")
    print(f"  • Body UI: {sel['ui_secondary']['$value']} ({sel['ui_secondary']['url']})")
    print(f"  • Accent:  {sel['accent_brand']['$value']} ({sel['accent_brand']['url']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
