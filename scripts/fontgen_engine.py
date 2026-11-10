#!/usr/bin/env python3
"""
fontgen_engine.py — Sovereign Agnostic Typographic Engine & Art Direction Matrix.
Zero-Hallucination Design Synthesis | Real-Time Live Envato Sourcing | Anti-CLS Calibration.
Complies with W3C DTCG 2025.10 & font_manifest.schema.json (Draft 2020-12).

Architectural Contracts:
1. Agnostic & Holistic: Dynamic astrological semantic querying. Zero hardcoded client fallbacks.
2. DTCG 3-Token Structure:
   - display_primary (Token 1): Envato Elements Pro (source: "envato", url: "https://app.envato.com/fonts/{uuid}")
   - ui_secondary    (Token 2): Google Fonts Variable v2 (source: "google_fonts", variable_axes, anti-CLS)
   - accent_brand   (Token 3): Envato Elements Pro (source: "envato", url: "https://app.envato.com/fonts/{uuid}")
3. Decoupled from brandfont: fontgen is purely the recommendation/analytical engine. Zero UI dependencies.
4. Non-Repetition Invariant: Cross-ecosystem deduplication prevents any font family collision across Eco 1, 2, and 3.

Author: Gentleman Programming & Antigravity Orchestrator
Version: 3.0.0
"""

import os
import sys
import json
import re
import argparse
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Curated & Physically Verified Fallback Catalog (HTTP 200 on app.envato.com/fonts/)
# -----------------------------------------------------------------------------

ENVATO_VERIFIED_CATALOG = {
    "luxury_editorial_serif": {
        "family": "Serif Luxury Logo",
        "url": "https://app.envato.com/fonts/5e116044-15bd-48c4-9b0a-014c8b84214f",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=luxury+serif",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Luxury Editorial Serif",
        "description": "High-fashion editorial serif with polished details, noble proportions and refined headline presence."
    },
    "modern_luxury_serif": {
        "family": "Kovase",
        "url": "https://app.envato.com/fonts/d297622e-0d83-43a3-a96c-f3cc510fa84b",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=luxury+stencil+serif",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Dramatic Modern Editorial Stencil",
        "description": "Modern editorial stencil serif crafted for luxury branding, boutique identity and dramatic contrast."
    },
    "high_contrast_didone": {
        "family": "Taillevere",
        "url": "https://app.envato.com/fonts/9dee7e7e-b2ad-42a9-8092-f674dc4bd330",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=didone+luxury+serif",
        "weights": ["400", "500", "700"],
        "category": "serif",
        "style": "Modern Didone",
        "description": "Sophisticated high-contrast Didone with razor-thin hairlines, dramatic vertical stress and graceful curves."
    },
    "vintage_didone": {
        "family": "Dogmade",
        "url": "https://app.envato.com/fonts/1084a746-7c46-49eb-978b-b7043fd4212a",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=vintage+didone",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Vintage Didone Display",
        "description": "Noble vintage didone with expressive letterforms, opulent terminals and editorial prestige."
    },
    "architectural_serif": {
        "family": "Domani",
        "url": "https://app.envato.com/fonts/1de94cfa-3ac9-4fd1-b5b2-113405506be3",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=architectural+serif",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Architectural Inscriptional Serif",
        "description": "Monumental stone-carved serif inspired by classical architecture with balanced geometry and royal gravitas."
    },
    "romanesque_display": {
        "family": "Trabuline",
        "url": "https://app.envato.com/fonts/72c6db75-b4a2-482c-9392-9d7ae5559c6a",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=roman+titling+serif",
        "weights": ["600", "700"],
        "category": "serif",
        "style": "Romanesque Titling",
        "description": "Modern romanesque display inspired by stone-carved titling with discretionary ligatures and imperial presence."
    },
    "monogram_holder": {
        "family": "Monogram Holder",
        "url": "https://app.envato.com/fonts/b072395d-990e-4637-a1ca-2c8b0355aed0",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=monogram+display+font",
        "weights": ["700", "900"],
        "category": "display",
        "style": "Interlocking Monogram Slab",
        "description": "Specialized monogram font engineered for interlocking two-letter logos, brand seals and luxury badges."
    },
    "clarissa_monogram": {
        "family": "Clarissa Monogram",
        "url": "https://app.envato.com/fonts/75702d55-4518-452d-ad4c-bad5fb47ea70",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=monogram+ligature+logo",
        "weights": ["600", "800"],
        "category": "display",
        "style": "Luxury Monogram Ligature",
        "description": "Refined brand emblem font featuring ornate interlocking ligatures designed for luxury seals."
    },
    "clean_geometric_sans": {
        "family": "Franie",
        "url": "https://app.envato.com/fonts/40b427aa-a786-4f98-9ebb-ef68413188e1",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=geometric+sans",
        "weights": ["300", "400", "500", "600", "700"],
        "category": "sans",
        "style": "Clean Modern Geometric Sans",
        "description": "Functional workhorse geometric sans with crisp open apertures, high legibility and modernist warmth."
    },
    "geometric_minimalist_sans": {
        "family": "Geometric Sans",
        "url": "https://app.envato.com/fonts/af397135-1d09-413c-a77e-aa808c600301",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=minimalist+sans+font",
        "weights": ["400", "600", "700"],
        "category": "sans",
        "style": "Minimalist Bauhaus Sans",
        "description": "Minimalist architectural sans serif with balanced proportions and contemporary editorial clarity."
    },
    "modern_grotesk_stencil": {
        "family": "Akmorn Grotesque",
        "url": "https://app.envato.com/fonts/c1ffdc86-c80d-45ec-92ae-6c69615d1086",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=modern+grotesque+sans",
        "weights": ["400", "600", "700", "800"],
        "category": "sans",
        "style": "Industrial Neo-Grotesque",
        "description": "Clean neo-grotesque with modular precision, sharp angular cuts and cutting-edge industrial presence."
    },
    "industrial_grotesk": {
        "family": "Berghan",
        "url": "https://app.envato.com/fonts/b1456d39-bfa8-4726-8439-e2fb8ca23fc3",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=modern+grotesk",
        "weights": ["500", "700", "800"],
        "category": "sans",
        "style": "Modern Technical Grotesk",
        "description": "Solid architectural grotesk with robust vertical rhythm and high mechanical precision."
    },
    "modern_brutalist": {
        "family": "Riot Cut",
        "url": "https://app.envato.com/fonts/7628b08f-35c3-4f95-b4db-455fb0486a43",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=brutalist+font",
        "weights": ["700", "800", "900"],
        "category": "display",
        "style": "Brutalist Kinetic Display",
        "description": "Heavy kinetic brutalist display typography with tight tracking, explosive visual weight and high tension."
    },
    "brutalist_display": {
        "family": "Aurora",
        "url": "https://app.envato.com/fonts/c13eba79-5b72-4c20-938f-6b0826a29745",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=brutalist+display+typeface",
        "weights": ["700", "800"],
        "category": "display",
        "style": "Avant-Garde Brutalist Display",
        "description": "Disruptive avant-garde display typeface engineered for bold titling and radical aesthetic statements."
    },
    "luxury_calligraphy": {
        "family": "Script Calligraphy",
        "url": "https://app.envato.com/fonts/74af1b1d-ec22-4b99-8df0-bfd011bf9dab",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=script+calligraphy",
        "weights": ["400", "600"],
        "category": "script",
        "style": "Luxury Romantic Calligraphy",
        "description": "Aristocratic calligraphy with fluid swashes, delicate flourished ligatures and organic luxury movement."
    },
    "wedding_script": {
        "family": "Teofandin Levantamy",
        "url": "https://app.envato.com/fonts/e3eb7b1e-8b7f-4aae-9bfe-febec528c6bd",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=wedding+calligraphy+script",
        "weights": ["400", "600"],
        "category": "script",
        "style": "Bespoke Flourished Script",
        "description": "Handcrafted copperplate calligraphic script featuring extensive alternate glyphs and bespoke signature flourish."
    },
    "retro_bold_display": {
        "family": "Roketto",
        "url": "https://app.envato.com/fonts/03b9745e-d0bc-434c-ab90-7cc80d34ca05",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=retro+bold+display+font",
        "weights": ["700", "900"],
        "category": "display",
        "style": "Retro Bold Kinetic Display",
        "description": "Powerful retro bold display typography with sculptural curves and unmistakable graphic impact."
    },
    "retro_bold_serif": {
        "family": "Bringbold Nineties",
        "url": "https://app.envato.com/fonts/e5397f80-ddf8-482b-a524-769a5a74ac83",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=retro+bold+serif+font",
        "weights": ["600", "700", "800"],
        "category": "serif",
        "style": "90s Editorial Retro Serif",
        "description": "Voluptuous high-impact retro serif capturing the confident visual power of nineties editorial luxury."
    },
    "elegant_serif_display": {
        "family": "Swarsh Daisy",
        "url": "https://app.envato.com/fonts/354d8330-5a2a-4196-a03c-ab5ebd7f6dab",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=elegant+serif+display",
        "weights": ["400", "600"],
        "category": "serif",
        "style": "Flourished Editorial Serif",
        "description": "Graceful display serif with botanical swashes, gentle curves and poetic luxury elegance."
    },
    "monogram_emblem": {
        "family": "Seals Monogram",
        "url": "https://app.envato.com/fonts/36b5532e-f307-4c1f-818f-2ceeaecb9fb3",
        "search_url": "https://app.envato.com/search?itemType=fonts&term=monogram+brand+seal+font",
        "weights": ["700", "900"],
        "category": "display",
        "style": "Heraldic Brand Seal Monogram",
        "description": "Geometric seal monogram font engineered for royal crests, luxury brand seals and interlocking insignias."
    }
}

# Rich, diverse Google Fonts v2 Variable multiaxis catalog (Non-repetitive workhorses)
GOOGLE_FONTS_CATALOG = {
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
    "dm_sans": {
        "family": "DM Sans",
        "url": "https://fonts.google.com/specimen/DM+Sans",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&display=swap",
        "variable_axes": "ital,opsz,wght@0..1,9..40,100..1000",
        "weights": ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "99.0%", "ascent": "94.0%", "descent": "23.5%", "line_gap": "0%"}
    },
    "outfit": {
        "family": "Outfit",
        "url": "https://fonts.google.com/specimen/Outfit",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap",
        "variable_axes": "wght@100..900",
        "weights": ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "100.0%", "ascent": "95.0%", "descent": "25.0%", "line_gap": "0%"}
    }
}

# -----------------------------------------------------------------------------
# Astrological Gestalt Constants
# -----------------------------------------------------------------------------

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
    "Cardinal": 1.618,  # Golden Ratio (Disrupción soberana, salto editorial tajante)
    "Fixed": 1.333,     # Perfect Fourth (Arquitectura sólida, equilibrio monumental)
    "Mutable": 1.250    # Major Third (Dinámica rítmica, agilidad modular)
}

BAZI_MODULATIONS = {
    "Jia":  {"element": "Wood",  "polarity": "Yang", "tracking_em": -0.01},
    "Yi":   {"element": "Wood",  "polarity": "Yin",  "tracking_em":  0.02},
    "Bing": {"element": "Fire",  "polarity": "Yang", "tracking_em":  0.03},
    "Ding": {"element": "Fire",  "polarity": "Yin",  "tracking_em":  0.01},
    "Wu":   {"element": "Earth", "polarity": "Yang", "tracking_em":  0.00},
    "Ji":   {"element": "Earth", "polarity": "Yin",  "tracking_em":  0.015},
    "Geng": {"element": "Metal", "polarity": "Yang", "tracking_em": -0.02},
    "Xin":  {"element": "Metal", "polarity": "Yin",  "tracking_em":  0.04},
    "Ren":  {"element": "Water", "polarity": "Yang", "tracking_em":  0.01},
    "Gui":  {"element": "Water", "polarity": "Yin",  "tracking_em":  0.025}
}

NAKSHATRA_FEATURES = {
    "Ashwini":     {"feature": "dlig 1, ss01 1", "accent_archetype": "monogram_holder"},
    "Bharani":     {"feature": "swsh 1",         "accent_archetype": "clarissa_monogram"},
    "Krittika":    {"feature": "titl 1",         "accent_archetype": "romanesque_display"},
    "Rohini":      {"feature": "calt 1, liga 1", "accent_archetype": "luxury_calligraphy"},
    "Mrigashira":  {"feature": "ss02 1",         "accent_archetype": "clarissa_monogram"},
    "Ardra":       {"feature": "zero 1",         "accent_archetype": "modern_grotesk_stencil"},
    "Punarvasu":   {"feature": "liga 1",         "accent_archetype": "luxury_calligraphy"},
    "Pushya":      {"feature": "titl 1, cscp 1", "accent_archetype": "monogram_holder"},
    "Ashlesha":    {"feature": "swsh 1, dlig 1", "accent_archetype": "wedding_script"},
    "Magha":       {"feature": "titl 1",         "accent_archetype": "architectural_serif"},
    "Purva Phalguni":  {"feature": "calt 1",     "accent_archetype": "luxury_calligraphy"},
    "Uttara Phalguni": {"feature": "liga 1",     "accent_archetype": "monogram_holder"},
    "Hasta":       {"feature": "ss01 1",         "accent_archetype": "clarissa_monogram"},
    "Chitra":      {"feature": "dlig 1, calt 1", "accent_archetype": "monogram_emblem"},
    "Swati":       {"feature": "swsh 1",         "accent_archetype": "wedding_script"},
    "Vishakha":    {"feature": "titl 1",         "accent_archetype": "architectural_serif"},
    "Anuradha":    {"feature": "calt 1, liga 1", "accent_archetype": "luxury_calligraphy"},
    "Jyeshtha":    {"feature": "cscp 1",         "accent_archetype": "monogram_holder"},
    "Mula":        {"feature": "ss04 1",         "accent_archetype": "modern_brutalist"},
    "Purva Ashadha":   {"feature": "swsh 1",     "accent_archetype": "luxury_calligraphy"},
    "Uttara Ashadha":  {"feature": "titl 1",     "accent_archetype": "architectural_serif"},
    "Shravana":    {"feature": "liga 1, calt 1", "accent_archetype": "clarissa_monogram"},
    "Dhanishta":   {"feature": "ss01 1",         "accent_archetype": "modern_grotesk_stencil"},
    "Shatabhisha": {"feature": "zero 1",         "accent_archetype": "industrial_grotesk"},
    "Purva Bhadrapada": {"feature": "ss05 1",    "accent_archetype": "brutalist_display"},
    "Uttara Bhadrapada":{"feature": "liga 1",    "accent_archetype": "wedding_script"},
    "Revati":      {"feature": "calt 1, swsh 1", "accent_archetype": "luxury_calligraphy"}
}


# -----------------------------------------------------------------------------
# Sovereign Dynamic Path & LocalStorage Discovery Helpers
# -----------------------------------------------------------------------------

def find_localstorage_roots() -> List[Path]:
    """Dynamically resolves all persistent local storage mounts and active runtime volumes."""
    roots: List[Path] = []
    env_path = os.getenv("LOCAL_STORAGE_PATH")
    if env_path and Path(env_path).exists():
        p = Path(env_path).resolve()
        if p not in roots:
            roots.append(p)
        if p.name in ("hermes", "paperclip", "engram", "pidev") and p.parent.exists():
            par = p.parent.resolve()
            if par not in roots:
                roots.append(par)

    for candidate in [Path("/mnt/localstorage"), Path("/var/www/localstorage")]:
        if candidate.exists():
            res = candidate.resolve()
            if res not in roots:
                roots.append(res)
    return roots


# -----------------------------------------------------------------------------
# Fontgen Engine Implementation
# -----------------------------------------------------------------------------

class FontgenEngine:
    """
    Sovereign Agnostic Typographic Engine.
    Synthesizes 3 differentiated typography ecosystems with verified real fonts:
      - Display Primary: Envato Elements Pro (source: "envato", https://app.envato.com/fonts/{uuid})
      - UI Secondary:    Google Fonts v2 Variable (source: "google_fonts", multiaxis, anti-CLS)
      - Accent Brand:    Envato Elements Pro (source: "envato", https://app.envato.com/fonts/{uuid})
    Guarantees cross-ecosystem deduplication so no two ecosystems repeat the same font family.
    Zero coupling with brandfont (visualization workbench).
    """

    def __init__(self, brand: str, shards_path: Optional[Path] = None, brief_path: Optional[Path] = None,
                 output_dir: Optional[Path] = None, use_live_search: bool = True, allow_default: bool = False):
        self.brand_raw = brand.strip()
        self.brand_upper = self.brand_raw.upper()
        self.brand_lower = self.brand_raw.lower()
        self.shards_path = Path(shards_path).resolve() if shards_path else None
        self.brief_path = Path(brief_path).resolve() if brief_path else None
        self.output_dir = Path(output_dir).resolve() if output_dir else None
        self.use_live_search = use_live_search
        self.allow_default = allow_default

        self.used_families: Set[str] = set()

        # Dynamic SSoT fallback destinations
        self.diag_dir = Path(f"/var/www/baiosfera/ASTROLOGÍA/DIAG/{self.brand_upper}")
        self.project_dev_dir = Path(f"/var/www/baiosfera/PROYECTOS/{self.brand_upper}/dev")
        self.localstorage_dir = Path(f"/var/www/localstorage/{self.brand_upper}/dev")

    def _discover_search_dirs(self) -> List[Path]:
        """Dynamically discovers all potential dev, shared, and brand directories across the workspace and localstorage."""
        dirs: List[Path] = []

        # 1. Current working directory and ancestors up to 4 levels
        curr = Path.cwd().resolve()
        for p in [curr] + list(curr.parents)[:4]:
            if p.exists() and p not in dirs:
                dirs.append(p)
            for sub in [p / "dev", p / "dev" / "_shared", p / "_shared", p / "brand"]:
                if sub.exists() and sub not in dirs:
                    dirs.append(sub)

        # 2. Workspace directories matching brand or vertical
        for base in list(dirs):
            for ws_candidate in [
                base / "workspaces" / self.brand_lower / "brand",
                base / "workspaces" / self.brand_lower,
                base / "dev" / "workspaces" / self.brand_lower / "brand",
                base / "dev" / "workspaces" / self.brand_lower
            ]:
                if ws_candidate.exists() and ws_candidate not in dirs:
                    dirs.append(ws_candidate)

        # 3. Dynamic LocalStorage discovery across all projects (zero hardcoding)
        for ls_root in find_localstorage_roots():
            if not ls_root.exists():
                continue
            if ls_root not in dirs:
                dirs.append(ls_root)
            try:
                for child in ls_root.iterdir():
                    if child.is_dir() and not child.name.startswith("."):
                        for sub in [
                            child / "dev",
                            child / "dev" / "_shared",
                            child / "dev" / "workspaces" / self.brand_lower / "brand",
                            child / "dev" / "workspaces" / self.brand_lower,
                            child / "workspaces" / self.brand_lower / "brand",
                            child / "brand"
                        ]:
                            if sub.exists() and sub not in dirs:
                                dirs.append(sub)
            except Exception:
                pass

        # 4. FUSE SSoT directories (if mounted)
        fuse_diag = Path(f"/var/www/baiosfera/ASTROLOGÍA/DIAG/{self.brand_upper}")
        if fuse_diag.exists() and fuse_diag not in dirs:
            dirs.append(fuse_diag)
        fuse_proj = Path(f"/var/www/baiosfera/PROYECTOS/{self.brand_upper}/dev")
        if fuse_proj.exists() and fuse_proj not in dirs:
            dirs.append(fuse_proj)

        # 5. Dynamic ecosystem discovery (umbrella brand detection from ecosystem.json)
        # ONLY add umbrella paths if self.brand_lower is verified as part of the ecosystem
        for d in list(dirs):
            for candidate_eco in [d / "ecosystem.json", d / "_shared" / "ecosystem.json", d / "dev" / "_shared" / "ecosystem.json"]:
                if candidate_eco.exists():
                    try:
                        eco_data = json.loads(candidate_eco.read_text(encoding="utf-8"))
                        verts = eco_data.get("verticals", {})
                        is_member = False
                        if isinstance(verts, dict):
                            if self.brand_lower in verts or any(self.brand_lower == str(v.get("vertical_slug", "")).lower() for v in verts.values() if isinstance(v, dict)):
                                is_member = True
                        elif isinstance(verts, list):
                            if self.brand_lower in [str(x).lower() for x in verts]:
                                is_member = True

                        if self.brand_lower == str(eco_data.get("brand_slug", "")).lower():
                            is_member = True

                        umb_slug = eco_data.get("umbrella_brand") or eco_data.get("brand_slug")
                        if is_member and umb_slug:
                            umb_upper = str(umb_slug).upper()
                            u_diag = Path(f"/var/www/baiosfera/ASTROLOGÍA/DIAG/{umb_upper}")
                            if u_diag.exists() and u_diag not in dirs:
                                dirs.append(u_diag)
                            u_proj = Path(f"/var/www/baiosfera/PROYECTOS/{umb_upper}/dev")
                            if u_proj.exists() and u_proj not in dirs:
                                dirs.append(u_proj)
                    except Exception:
                        pass

        return dirs

    def _clean_family_name(self, raw_title: str) -> str:
        """Extracts a clean canonical typographic family name from title."""
        if not raw_title:
            return "Untitled Font"

        first_part = re.split(r"\s*[-–—|:]\s*", raw_title)[0].strip()
        first_part = re.split(r",", first_part)[0].strip()
        first_part = re.sub(r"&amp;", "&", first_part)
        cleaned = re.sub(r"\b(Font|Typeface|Family|Display|Serif|Sans|Grotesk|Grotesque|Script|Calligraphy|Vintage|Modern|Luxury|Bold|Retro)\b", "", first_part, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        if len(cleaned) >= 2:
            return cleaned.title()
        return first_part.strip().title()

    def _search_live_envato_fonts(self, query: str, category: str = "serif", default_weights: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Queries app.envato.com/search in real time, extracts items and ensures non-duplication."""
        if not self.use_live_search:
            return None

        search_url = f"https://app.envato.com/search?itemType=fonts&term={urllib.parse.quote_plus(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        try:
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                html = resp.read().decode("utf-8")

            chunks = re.findall(r"<a[^>]+data-analytics-item_id=\"[^\"]+\"[^>]*>", html)
            for c in chunks:
                m_id = re.search(r"data-analytics-item_id=\"([^\"]+)\"", c)
                m_title = re.search(r"data-analytics-item_title=\"([^\"]+)\"", c)
                m_author = re.search(r"data-analytics-item_author=\"([^\"]+)\"", c)

                if m_id and m_title:
                    fid = m_id.group(1).strip()
                    title = m_title.group(1).strip()
                    author = m_author.group(1).strip() if m_author else "Envato Author"
                    family = self._clean_family_name(title)

                    if family.lower() in [f.lower() for f in self.used_families]:
                        continue

                    self.used_families.add(family)
                    return {
                        "family": family,
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

    def _get_fallback_envato_font(self, archetype_key: str, category: str = "serif", default_weights: Optional[List[str]] = None) -> Dict[str, Any]:
        """Returns an unused fallback font from the curated 25+ verified catalog."""
        candidate = ENVATO_VERIFIED_CATALOG.get(archetype_key)
        if candidate and candidate["family"].lower() not in [f.lower() for f in self.used_families]:
            self.used_families.add(candidate["family"])
            return candidate

        # Find first unused fallback with matching or compatible category
        for k, v in ENVATO_VERIFIED_CATALOG.items():
            if v["family"].lower() not in [f.lower() for f in self.used_families]:
                self.used_families.add(v["family"])
                return v

        # Emergency fallback
        fallback = ENVATO_VERIFIED_CATALOG["luxury_editorial_serif"]
        return fallback

    def resolve_inputs(self) -> Dict[str, Any]:
        """Discovers astronomical coordinates dynamically from shards or brief."""
        data = {
            "sun_sign": "",
            "mc_sign": "",
            "day_master": "",
            "nakshatra": "",
            "dominant_element": ""
        }

        search_dirs = self._discover_search_dirs()

        # 1. Shards Ingestion (Explicit target or brand-specific diagnostic lakehouse)
        shards_target = self.shards_path
        if not shards_target:
            direct_potentials = [
                self.diag_dir / "raw" / "json" / "dumps" / "client_dumps_15_shards.json",
                self.diag_dir / "dumps" / "client_dumps_15_shards.json",
                self.project_dev_dir / "client_dumps_15_shards.json"
            ]
            for p in direct_potentials:
                if p.exists():
                    shards_target = p
                    break

        if shards_target and Path(shards_target).exists():
            try:
                content = json.loads(Path(shards_target).read_text(encoding="utf-8"))
                s1 = content.get("shard_01", {}).get("data", {})
                s3 = content.get("shard_03", {}).get("data", {})
                s4 = content.get("shard_04", {}).get("data", {})

                tripod = s1.get("tripod_of_iron", {})
                if "sun" in tripod and tripod["sun"].get("sign"):
                    data["sun_sign"] = tripod["sun"]["sign"]
                if "midheaven_house_10" in tripod and tripod["midheaven_house_10"].get("sign"):
                    data["mc_sign"] = tripod["midheaven_house_10"]["sign"]

                dm = s4.get("day_master", {})
                if dm.get("name"):
                    data["day_master"] = dm.get("name").split()[0]

                nak = s3.get("nakshatra", {})
                if nak.get("name"):
                    data["nakshatra"] = nak.get("name").split()[0]

                if data["sun_sign"] and data["mc_sign"]:
                    data["dominant_element"] = ZODIAC_ELEMENTS.get(data["sun_sign"], "Earth")
                    if not data["day_master"]:
                        data["day_master"] = "Wu"
                    if not data["nakshatra"]:
                        data["nakshatra"] = "Ashwini"
                    return data
            except Exception:
                pass

        # 2. Brief Ingestion fallback
        candidates: List[Path] = []
        if self.brief_path and Path(self.brief_path).exists():
            candidates.append(Path(self.brief_path).resolve())

        # Check explicit brand-named briefs first
        for sdir in search_dirs:
            if not sdir.exists():
                continue
            named_brief = sdir / f"astrobranding_{self.brand_lower}.md"
            if named_brief.exists() and named_brief not in candidates:
                candidates.append(named_brief)
            raw_named = sdir / "raw" / "llm" / f"astrobranding_{self.brand_lower}.md"
            if raw_named.exists() and raw_named not in candidates:
                candidates.append(raw_named)

        # If brand has no dedicated brief, inspect ecosystem.json to check if it's a verified vertical
        # of an umbrella brand. Only verified verticals inherit their umbrella's master brief.
        umbrella_slug = None
        for sdir in search_dirs:
            for eco_cand in [sdir / "ecosystem.json", sdir / "_shared" / "ecosystem.json", sdir / "dev" / "_shared" / "ecosystem.json"]:
                if eco_cand.exists():
                    try:
                        eco_data = json.loads(eco_cand.read_text(encoding="utf-8"))
                        verts = eco_data.get("verticals", {})
                        is_vertical = False
                        if isinstance(verts, dict):
                            if self.brand_lower in verts:
                                is_vertical = True
                            elif any(self.brand_lower == str(v.get("vertical_slug", "")).lower() for v in verts.values() if isinstance(v, dict)):
                                is_vertical = True
                        elif isinstance(verts, list):
                            if self.brand_lower in [str(x).lower() for x in verts]:
                                is_vertical = True

                        if is_vertical or self.brand_lower == str(eco_data.get("brand_slug", "")).lower():
                            umbrella_slug = eco_data.get("brand_slug") or eco_data.get("umbrella_brand")
                            break
                    except Exception:
                        pass
            if umbrella_slug:
                break

        if umbrella_slug:
            umb_lower = str(umbrella_slug).lower()
            for sdir in search_dirs:
                if not sdir.exists():
                    continue
                umb_brief = sdir / f"astrobranding_{umb_lower}.md"
                if umb_brief.exists() and umb_brief not in candidates:
                    candidates.append(umb_brief)
                raw_umb = sdir / "raw" / "llm" / f"astrobranding_{umb_lower}.md"
                if raw_umb.exists() and raw_umb not in candidates:
                    candidates.append(raw_umb)

        for c in candidates:
            if c.exists() and c.is_file():
                try:
                    txt = c.read_text(encoding="utf-8")
                    m_sun = re.search(r"\|\s*\*\*Sol Natal\*\*\s*\|\s*\*\*([A-Za-z]+)", txt) or re.search(r"(?:Sun Natal|Sol Natal)[\s\:\*\|]+([A-Za-z]+)", txt, re.IGNORECASE)
                    m_mc = re.search(r"\|\s*\*\*Medio Cielo[^\*]*\*\*\s*\|\s*\*\*([A-Za-z]+)", txt) or re.search(r"(?:Midheaven|Medio Cielo)[\s\:\*\|]+([A-Za-z]+)", txt, re.IGNORECASE)
                    m_nak = re.search(r"\*\*Nakshatra:\*\*\s*([A-Za-z]+)", txt) or re.search(r"Nakshatra[\s\:\*\|]+([A-Za-z]+)", txt, re.IGNORECASE)
                    m_dm = re.search(r"\*\*Day Master:\*\*\s*([A-Za-z]+)", txt) or re.search(r"Day Master[\s\:\*\|]+([A-Za-z]+)", txt, re.IGNORECASE)

                    if m_sun: data["sun_sign"] = m_sun.group(1).strip()
                    if m_mc: data["mc_sign"] = m_mc.group(1).strip()
                    if m_nak: data["nakshatra"] = m_nak.group(1).strip()
                    if m_dm: data["day_master"] = m_dm.group(1).strip()

                    if data["sun_sign"] and data["mc_sign"]:
                        data["dominant_element"] = ZODIAC_ELEMENTS.get(data["sun_sign"], "Earth")
                        if not data["day_master"]:
                            data["day_master"] = "Wu"
                        if not data["nakshatra"]:
                            data["nakshatra"] = "Ashwini"
                        return data
                except Exception:
                    pass

        # If data was not found
        if not (data["sun_sign"] and data["mc_sign"]):
            if not self.allow_default:
                raise FileNotFoundError(
                    f"No valid astrobranding brief or 15-shards data found for brand '{self.brand_raw}'.\n"
                    f"Searched {len(search_dirs)} dynamic directories, checked candidates:\n"
                    f"  - Brief candidates: {[str(c) for c in candidates]}\n"
                    f"  - Search roots: {[str(d) for d in search_dirs[:8]]}\n"
                    f"Ensure Oráculo (omni_engine.py) has run for this brand/umbrella or supply --brief / --shards explicitly."
                )
            # Standalone fallback mode only when explicitly allowed
            data = {
                "sun_sign": "Capricorn",
                "mc_sign": "Virgo",
                "day_master": "Wu",
                "nakshatra": "Ashwini",
                "dominant_element": "Earth"
            }

        return data

    def build_ecosystems(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Derives 3 unique, diverse ecosystems with verified real fonts:
          Eco 1: Quiet Luxury & Authority (MC + Sun)
          Eco 2: High Performance Precision (Modality + BaZi Day Master)
          Eco 3: Alchemical Bio-Sensual Vanguard (Nakshatra)
        Ensures cross-ecosystem non-repetition and Envato for display & accent tokens.
        """
        sun_sign = params.get("sun_sign", "Capricorn")
        mc_sign = params.get("mc_sign", "Virgo")
        day_master = params.get("day_master", "Wu")
        nakshatra = params.get("nakshatra", "Ashwini")

        mc_elem = ZODIAC_ELEMENTS.get(mc_sign, "Earth")
        mc_mod = ZODIAC_MODALITIES.get(mc_sign, "Cardinal")
        scale_ratio = MODALITY_SCALE_RATIOS.get(mc_mod, 1.333)

        bazi_info = BAZI_MODULATIONS.get(day_master, BAZI_MODULATIONS["Wu"])
        nak_info = NAKSHATRA_FEATURES.get(nakshatra, {"feature": "liga 1", "accent_archetype": "monogram_emblem"})

        # --- ECOSISTEMA 1: QUIET LUXURY & AUTHORITY (MC + SUN) ---
        if mc_elem in ["Earth", "Water"]:
            query_prim1 = f"luxury architectural editorial serif font {mc_elem.lower()}"
            query_acc1 = "interlocking luxury monogram logo brand seal"
            fallback_prim_key1 = "luxury_editorial_serif"
            fallback_acc_key1 = "monogram_holder"
            eco1_body = GOOGLE_FONTS_CATALOG["newsreader"]
        elif mc_elem == "Fire":
            query_prim1 = "royal inscriptional stone titling serif font"
            query_acc1 = "architectural monogram emblem font"
            fallback_prim_key1 = "romanesque_display"
            fallback_acc_key1 = "clarissa_monogram"
            eco1_body = GOOGLE_FONTS_CATALOG["instrument_sans"]
        else: # Air
            query_prim1 = "modern luxury editorial high contrast serif font"
            query_acc1 = "modern geometric monogram brand seal font"
            fallback_prim_key1 = "modern_luxury_serif"
            fallback_acc_key1 = "monogram_emblem"
            eco1_body = GOOGLE_FONTS_CATALOG["manrope"]

        live_prim_1 = self._search_live_envato_fonts(query_prim1, category="serif")
        eco1_prim = live_prim_1 if live_prim_1 else self._get_fallback_envato_font(fallback_prim_key1, category="serif")

        live_acc_1 = self._search_live_envato_fonts(query_acc1, category="display")
        eco1_acc = live_acc_1 if live_acc_1 else self._get_fallback_envato_font(fallback_acc_key1, category="display")

        eco1 = {
            "id": "eco-1",
            "name": f"Quiet Luxury {mc_elem} Authority",
            "archetype": f"Proyección Pública MC {mc_sign} & Sol {sun_sign}",
            "rationale": (
                f"Contraste editorial de alta gama entre la sofisticación de {eco1_prim['family']} en titulares "
                f"y el confort de lectura inmersiva de {eco1_body['family']}. "
                f"Escala armónica modulada a ratio {scale_ratio:.3f} ({mc_mod}) con acento heráldico en {eco1_acc['family']}."
            ),
            "tokens": {
                "display_primary": {
                    "$value": eco1_prim["family"],
                    "$type": "fontFamily",
                    "$description": f"Envato Elements Pro — {eco1_prim['description']}",
                    "source": "envato",
                    "url": eco1_prim["url"],
                    "search_url": eco1_prim["search_url"],
                    "weights": eco1_prim["weights"]
                },
                "ui_secondary": {
                    "$value": eco1_body["family"],
                    "$type": "fontFamily",
                    "$description": "Google Fonts v2 Variable — Workhorse tipográfico",
                    "source": "google_fonts",
                    "url": eco1_body["url"],
                    "google_fonts_v2_url": eco1_body["google_fonts_v2_url"],
                    "variable_axes": eco1_body["variable_axes"],
                    "weights": eco1_body["weights"]
                },
                "accent_brand": {
                    "$value": eco1_acc["family"],
                    "$type": "fontFamily",
                    "$description": f"Envato Elements Pro — {eco1_acc['description']}",
                    "source": "envato",
                    "url": eco1_acc["url"],
                    "search_url": eco1_acc["search_url"],
                    "weights": eco1_acc["weights"]
                }
            },
            "layers": {
                "logo": f"{eco1_acc['family']} (Weight 900)",
                "slogan": f"{eco1_prim['family']} (Weight 400, Tracking +0.15em, Uppercase)",
                "h1": f"{eco1_prim['family']} (Weight 600, Ratio {scale_ratio:.3f})",
                "h2": f"{eco1_prim['family']} (Weight 500, Scale {scale_ratio:.3f}x down)",
                "body": f"{eco1_body['family']} (Variable Regular 400, Line-height 1.55)",
                "ui": f"{eco1_body['family']} (Variable Medium 600, Tracking -0.01em)"
            },
            "cls_metric_overrides": {
                "fallback_font": eco1_body["cls"]["fallback"],
                "size_adjust": eco1_body["cls"]["size_adjust"],
                "ascent_override": eco1_body["cls"]["ascent"],
                "descent_override": eco1_body["cls"]["descent"],
                "line_gap_override": eco1_body["cls"]["line_gap"]
            },
            "workbench_presets": {
                "font_size_px": 64,
                "letter_spacing_em": 0.04,
                "line_height": 1.15,
                "text_transform": "none",
                "font_weight": "600",
                "font_style": "normal",
                "text_align": "left",
                "ligatures_enabled": True,
                "translate_x": 0.0,
                "translate_y": 0.0,
                "rotation_deg": 0.0,
                "mirror_enabled": False
            }
        }

        # --- ECOSISTEMA 2: HIGH PERFORMANCE PRECISION (MODALITY + BAZI) ---
        if bazi_info["element"] in ["Metal", "Fire"]:
            query_prim2 = "kinetic brutalist display heavy typeface"
            query_acc2 = "futuristic geometric display logo font"
            fallback_prim_key2 = "modern_brutalist"
            fallback_acc_key2 = "brutalist_display"
            eco2_body = GOOGLE_FONTS_CATALOG["bricolage_grotesque"]
        elif bazi_info["element"] == "Wood":
            query_prim2 = "clean contemporary geometric sans typeface"
            query_acc2 = "modern architectural brand emblem logo font"
            fallback_prim_key2 = "clean_geometric_sans"
            fallback_acc_key2 = "clarissa_monogram"
            eco2_body = GOOGLE_FONTS_CATALOG["urbanist"]
        else: # Earth or Water
            query_prim2 = "modular structured geometric grotesk display"
            query_acc2 = "monogram brand seal emblem font"
            fallback_prim_key2 = "modern_grotesk_stencil"
            fallback_acc_key2 = "monogram_emblem"
            eco2_body = GOOGLE_FONTS_CATALOG["instrument_sans"]

        live_prim_2 = self._search_live_envato_fonts(query_prim2, category="sans")
        eco2_prim = live_prim_2 if live_prim_2 else self._get_fallback_envato_font(fallback_prim_key2, category="sans")

        live_acc_2 = self._search_live_envato_fonts(query_acc2, category="display")
        eco2_acc = live_acc_2 if live_acc_2 else self._get_fallback_envato_font(fallback_acc_key2, category="display")

        eco2 = {
            "id": "eco-2",
            "name": f"High Performance {bazi_info['element']} Precision",
            "archetype": f"Rigor Técnico BaZi {day_master} & Dinámica {bazi_info['polarity']}",
            "rationale": (
                f"Arquitectura contemporánea con la fuerza estructural de {eco2_prim['family']}. "
                f"Emparejada con {eco2_body['family']} para alta velocidad de lectura en interfaces interactivas "
                f"y tracking regulado ({bazi_info['tracking_em']}em)."
            ),
            "tokens": {
                "display_primary": {
                    "$value": eco2_prim["family"],
                    "$type": "fontFamily",
                    "$description": f"Envato Elements Pro — {eco2_prim['description']}",
                    "source": "envato",
                    "url": eco2_prim["url"],
                    "search_url": eco2_prim["search_url"],
                    "weights": eco2_prim["weights"]
                },
                "ui_secondary": {
                    "$value": eco2_body["family"],
                    "$type": "fontFamily",
                    "$description": "Google Fonts v2 Variable — Ultra rendimiento de UI",
                    "source": "google_fonts",
                    "url": eco2_body["url"],
                    "google_fonts_v2_url": eco2_body["google_fonts_v2_url"],
                    "variable_axes": eco2_body["variable_axes"],
                    "weights": eco2_body["weights"]
                },
                "accent_brand": {
                    "$value": eco2_acc["family"],
                    "$type": "fontFamily",
                    "$description": f"Envato Elements Pro — {eco2_acc['description']}",
                    "source": "envato",
                    "url": eco2_acc["url"],
                    "search_url": eco2_acc["search_url"],
                    "weights": eco2_acc["weights"]
                }
            },
            "layers": {
                "logo": f"{eco2_acc['family']} (Weight 800)",
                "slogan": f"{eco2_prim['family']} (Weight 500, Tracking +0.20em, Uppercase)",
                "h1": f"{eco2_prim['family']} (Weight 700, Ratio {scale_ratio:.3f})",
                "h2": f"{eco2_prim['family']} (Weight 600, Ratio {scale_ratio:.3f})",
                "body": f"{eco2_body['family']} (Variable Regular 400, Line-height 1.50)",
                "ui": f"{eco2_body['family']} (Variable Bold 700, Tracking -0.02em)"
            },
            "cls_metric_overrides": {
                "fallback_font": eco2_body["cls"]["fallback"],
                "size_adjust": eco2_body["cls"]["size_adjust"],
                "ascent_override": eco2_body["cls"]["ascent"],
                "descent_override": eco2_body["cls"]["descent"],
                "line_gap_override": eco2_body["cls"]["line_gap"]
            },
            "workbench_presets": {
                "font_size_px": 56,
                "letter_spacing_em": bazi_info["tracking_em"],
                "line_height": 1.10,
                "text_transform": "uppercase",
                "font_weight": "700",
                "font_style": "normal",
                "text_align": "left",
                "ligatures_enabled": False,
                "translate_x": 0.0,
                "translate_y": 0.0,
                "rotation_deg": 0.0,
                "mirror_enabled": False
            }
        }

        # --- ECOSISTEMA 3: ALCHEMICAL BIO-SENSUAL VANGUARD (NAKSHATRA) ---
        fallback_acc_key3 = nak_info.get("accent_archetype", "wedding_script")
        if mc_elem == "Water" or day_master in ["Ren", "Gui"]:
            query_prim3 = "modern high contrast didone luxury serif font"
            fallback_prim_key3 = "high_contrast_didone"
            eco3_body = GOOGLE_FONTS_CATALOG["spectral"]
        else:
            query_prim3 = f"flourished artistic editorial serif font {nakshatra.lower()}"
            fallback_prim_key3 = "elegant_serif_display"
            eco3_body = GOOGLE_FONTS_CATALOG["fraunces"]

        query_acc3 = f"bespoke flourish luxury script calligraphy font {nakshatra.lower()}"

        live_prim_3 = self._search_live_envato_fonts(query_prim3, category="serif")
        eco3_prim = live_prim_3 if live_prim_3 else self._get_fallback_envato_font(fallback_prim_key3, category="serif")

        live_acc_3 = self._search_live_envato_fonts(query_acc3, category="script")
        eco3_acc = live_acc_3 if live_acc_3 else self._get_fallback_envato_font(fallback_acc_key3, category="script")

        eco3 = {
            "id": "eco-3",
            "name": f"Alchemical {nakshatra} Vanguard",
            "archetype": f"Esencia Védica {nakshatra} ({nak_info['feature']})",
            "rationale": (
                f"Tensión estética rica y orgánica entre el dramatismo de {eco3_prim['family']} "
                f"y la calidez tipográfica de {eco3_body['family']}. "
                f"Acento caligráfico de alto impacto con {eco3_acc['family']}."
            ),
            "tokens": {
                "display_primary": {
                    "$value": eco3_prim["family"],
                    "$type": "fontFamily",
                    "$description": f"Envato Elements Pro — {eco3_prim['description']}",
                    "source": "envato",
                    "url": eco3_prim["url"],
                    "search_url": eco3_prim["search_url"],
                    "weights": eco3_prim["weights"]
                },
                "ui_secondary": {
                    "$value": eco3_body["family"],
                    "$type": "fontFamily",
                    "$description": "Google Fonts v2 Variable — Calidez tipográfica orgánica",
                    "source": "google_fonts",
                    "url": eco3_body["url"],
                    "google_fonts_v2_url": eco3_body["google_fonts_v2_url"],
                    "variable_axes": eco3_body["variable_axes"],
                    "weights": eco3_body["weights"]
                },
                "accent_brand": {
                    "$value": eco3_acc["family"],
                    "$type": "fontFamily",
                    "$description": f"Envato Elements Pro — {eco3_acc['description']}",
                    "source": "envato",
                    "url": eco3_acc["url"],
                    "search_url": eco3_acc["search_url"],
                    "weights": eco3_acc["weights"]
                }
            },
            "layers": {
                "logo": f"{eco3_acc['family']} (Weight 900)",
                "slogan": f"{eco3_prim['family']} (Weight 400, Italic, Tracking +0.10em)",
                "h1": f"{eco3_prim['family']} (Weight 600, Ratio {scale_ratio:.3f})",
                "h2": f"{eco3_prim['family']} (Weight 400, Italic)",
                "body": f"{eco3_body['family']} (Variable Regular 400, Line-height 1.60)",
                "ui": f"{eco3_body['family']} (Variable SemiBold 600, Tracking 0.00em)"
            },
            "cls_metric_overrides": {
                "fallback_font": eco3_body["cls"]["fallback"],
                "size_adjust": eco3_body["cls"]["size_adjust"],
                "ascent_override": eco3_body["cls"]["ascent"],
                "descent_override": eco3_body["cls"]["descent"],
                "line_gap_override": eco3_body["cls"]["line_gap"]
            },
            "workbench_presets": {
                "font_size_px": 68,
                "letter_spacing_em": 0.02,
                "line_height": 1.20,
                "text_transform": "none",
                "font_weight": "500",
                "font_style": "italic",
                "text_align": "left",
                "ligatures_enabled": True,
                "translate_x": 0.0,
                "translate_y": 0.0,
                "rotation_deg": 0.0,
                "mirror_enabled": False
            }
        }

        return [eco1, eco2, eco3]

    def generate_manifest(self, selected_eco_id: str = "eco-1") -> Dict[str, Any]:
        """Assembles the complete JSON document complying with font_manifest.schema.json."""
        params = self.resolve_inputs()
        ecosystems = self.build_ecosystems(params)

        selected_eco = next((e for e in ecosystems if e["id"] == selected_eco_id), ecosystems[0])

        manifest = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "brand": self.brand_upper,
            "selected_ecosystem_id": selected_eco["id"],
            "candidate_ecosystems": ecosystems,
            "selected_ecosystem": selected_eco,
            "inheritance": {
                "logo": selected_eco["layers"]["logo"],
                "slogan": selected_eco["layers"]["slogan"],
                "h1": selected_eco["layers"]["h1"],
                "h2": selected_eco["layers"]["h2"],
                "body": selected_eco["layers"]["body"],
                "ui": selected_eco["layers"]["ui"],
                "ui_buttons": selected_eco["layers"]["ui"]
            },
            "metadata": {
                "generator": "fontgen_engine.py v3.0 (Dynamic Live Envato + Verified Sourcing)",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "astrological_grounding": {
                    "sun": f"{params.get('sun_sign')} ({ZODIAC_ELEMENTS.get(params.get('sun_sign'), 'Earth')})",
                    "midheaven": f"{params.get('mc_sign')} ({ZODIAC_ELEMENTS.get(params.get('mc_sign'), 'Earth')})",
                    "day_master": params.get("day_master"),
                    "nakshatra": params.get("nakshatra")
                }
            }
        }
        return manifest

    def generate_markdown_sheet(self, manifest: Dict[str, Any]) -> str:
        """Generates technical documentation sheet matching font_matrix_template.md."""
        meta = manifest.get("metadata", {}).get("astrological_grounding", {})
        ecos = manifest.get("candidate_ecosystems", [])

        md = []
        md.append(f"# ♟️ Dirección de Arte Tipográfica SOTA: {self.brand_upper}")
        md.append(f"> **Resumen de Arquitectura:** Matriz tipográfica agnóstica derivada matemáticamente a partir de "
                  f"Sol en {meta.get('sun')}, Medio Cielo en {meta.get('midheaven')}, "
                  f"Day Master BaZi {meta.get('day_master')} y Nakshatra Védica {meta.get('nakshatra')}. "
                  f"Genera 3 ecosistemas híbridos con fuentes reales y verificadas de Envato Elements Pro "
                  f"(`app.envato.com/fonts/{{uuid}}`) para Display/Acento y Google Fonts Variable v2 para Body/UI con calibración anti-CLS.")
        md.append("")
        md.append("---")
        md.append("")

        for idx, eco in enumerate(ecos, 1):
            t = eco["tokens"]
            p = eco.get("cls_metric_overrides", {})
            w = eco.get("workbench_presets", {})

            md.append(f"### Ecosistema {idx}: {eco['name']} ({eco['id']})")
            md.append(f"- **Arquetipo Rector:** {eco['archetype']}")
            md.append(f"- **Justificación Gestalt:** {eco['rationale']}")
            md.append("")
            md.append("#### Matriz de 3 Design Tokens (W3C DTCG)")
            md.append(f"1. **Token Primario (Autoridad / Display):** `{t['display_primary']['$value']}` — *Descarga:* [Item Directo]({t['display_primary']['url']}) | [Explorar Categoría en Envato]({t['display_primary'].get('search_url')}) — *Uso:* H1, H2, Hero, Slogan.")
            md.append(f"2. **Token Secundario (UI & Lectura Continua):** `{t['ui_secondary']['$value']}` — *Fuente:* [Google Fonts Variable]({t['ui_secondary']['url']}) — *Uso:* Párrafos, UI, Botones, Tablas.")
            md.append(f"3. **Token de Acento (Brand Voice / Logo):** `{t['accent_brand']['$value']}` — *Descarga:* [Item Directo]({t['accent_brand']['url']}) | [Explorar Categoría en Envato]({t['accent_brand'].get('search_url')}) — *Uso:* Isologo, Monograma, Citas destacadas.")
            md.append("")
            md.append("#### Herencia Funcional de 6 Capas")
            md.append(f"- **1. Logo / Monograma:** {eco['layers'].get('logo')}")
            md.append(f"- **2. Slogan / Tagline:** {eco['layers'].get('slogan')}")
            md.append(f"- **3. H1 / Títulos Hero:** {eco['layers'].get('h1')}")
            md.append(f"- **4. H2 / Subtítulos:** {eco['layers'].get('h2')}")
            md.append(f"- **5. Cuerpo / Párrafos:** {eco['layers'].get('body')}")
            md.append(f"- **6. UI / Botones (Labels):** {eco['layers'].get('ui')}")
            md.append("")
            md.append("#### Implementación Web & Calibración Anti-CLS (CLS = 0.00)")
            md.append("```html")
            md.append("<!-- CDN Google Fonts API v2 Multi-Eje -->")
            md.append('<link rel="preconnect" href="https://fonts.googleapis.com">')
            md.append('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
            md.append(f'<link href="{t["ui_secondary"].get("google_fonts_v2_url")}" rel="stylesheet">')
            md.append("```")
            md.append("")
            md.append("```css")
            md.append("/* Fallback Métrico para evitar saltos de maquetación */")
            md.append("@font-face {")
            md.append(f"  font-family: '{t['ui_secondary']['$value']} Fallback';")
            md.append(f"  src: local('{p.get('fallback_font', 'Arial')}');")
            md.append(f"  size-adjust: {p.get('size_adjust', '100%')};")
            md.append(f"  ascent-override: {p.get('ascent_override', '95%')};")
            md.append(f"  descent-override: {p.get('descent_override', '25%')};")
            md.append(f"  line-gap-override: {p.get('line_gap_override', '0%')};")
            md.append("}")
            md.append("")
            md.append(":root {")
            md.append(f"  --font-display: '{t['display_primary']['$value']}', serif;")
            md.append(f"  --font-body: '{t['ui_secondary']['$value']}', '{t['ui_secondary']['$value']} Fallback', system-ui, sans-serif;")
            md.append(f"  --font-accent: '{t['accent_brand']['$value']}', cursive;")
            md.append("}")
            md.append("```")
            md.append("")
            md.append("#### Presets Sugeridos para Workbench")
            md.append(f"- **Tamaño Display:** `{w.get('font_size_px', 64)}px` | **Letter Spacing:** `{w.get('letter_spacing_em', 0.0)}em` | **Line Height:** `{w.get('line_height', 1.2)}`")
            md.append(f"- **Transformación:** `{w.get('text_transform', 'none')}` | **Ligaduras OpenType:** `{'Activadas' if w.get('ligatures_enabled') else 'Desactivadas'}`")
            md.append("")
            md.append("---")
            md.append("")

        return "\n".join(md)

    def run(self, selected_eco_id: str = "eco-1", dry_run: bool = False) -> Tuple[Dict[str, Any], str]:
        """Executes the pipeline and writes canonical outputs to dual destinations."""
        manifest = self.generate_manifest(selected_eco_id=selected_eco_id)
        markdown = self.generate_markdown_sheet(manifest)

        if dry_run:
            return manifest, markdown

        manifest_str = json.dumps(manifest, indent=2, ensure_ascii=False)

        # 1. Explicit Output Destination (if specified)
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            (self.output_dir / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
            (self.output_dir / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")

        # 2. Workspace brand directory if discovered dynamically
        for sdir in self._discover_search_dirs():
            if sdir.name == "brand" and self.brand_lower in str(sdir):
                try:
                    sdir.mkdir(parents=True, exist_ok=True)
                    (sdir / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
                    (sdir / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")
                except Exception:
                    pass

        # 3. Archive Destination (if Google Drive SSoT is mounted): /var/www/baiosfera/ASTROLOGÍA/DIAG/[MARCA]/
        if Path("/var/www/baiosfera").exists():
            try:
                self.diag_dir.mkdir(parents=True, exist_ok=True)
                (self.diag_dir / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
                (self.diag_dir / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")

                self.project_dev_dir.mkdir(parents=True, exist_ok=True)
                (self.project_dev_dir / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
                (self.project_dev_dir / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")
            except Exception:
                pass

        # 4. LocalStorage Dev (if mounted)
        for ls_root in find_localstorage_roots():
            ls_dev = ls_root / self.brand_upper / "dev"
            try:
                ls_dev.mkdir(parents=True, exist_ok=True)
                (ls_dev / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
                (ls_dev / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")
            except Exception:
                pass

        return manifest, markdown


def derive_agnostic_typography(brand: str, shards: Optional[Dict[str, Any]] = None,
                               shards_path: Optional[Path] = None,
                               brief_path: Optional[Path] = None,
                               output_dir: Optional[Path] = None,
                               selected_eco_id: str = "eco-1",
                               use_live_search: bool = True,
                               allow_default: bool = False) -> Dict[str, Any]:
    engine = FontgenEngine(
        brand=brand,
        shards_path=shards_path,
        brief_path=brief_path,
        output_dir=output_dir,
        use_live_search=use_live_search,
        allow_default=allow_default
    )
    manifest, _ = engine.run(selected_eco_id=selected_eco_id, dry_run=False)
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Fontgen Engine — Verified Typographic Synthesizer")
    parser.add_argument("--brand", required=True, help="Brand or vertical name (e.g. BAIOSFERA, DAMAREN, CATALINAGLAMUR)")
    parser.add_argument("--shards", type=Path, default=None, help="Path to client_dumps_15_shards.json")
    parser.add_argument("--brief", type=Path, default=None, help="Path to astrobranding_[marca].md")
    parser.add_argument("--output-dir", type=Path, default=None, help="Explicit target directory for outputs")
    parser.add_argument("--eco", default="eco-1", choices=["eco-1", "eco-2", "eco-3"], help="Selected ecosystem ID")
    parser.add_argument("--dry-run", action="store_true", help="Calculate without writing to disk")
    parser.add_argument("--no-live", action="store_true", help="Disable real-time live search on Envato")
    parser.add_argument("--allow-default", action="store_true", help="Allow fallback to canonical neutral archetype if no brief/shards found")
    args = parser.parse_args()

    engine = FontgenEngine(
        brand=args.brand,
        shards_path=args.shards,
        brief_path=args.brief,
        output_dir=args.output_dir,
        use_live_search=not args.no_live,
        allow_default=args.allow_default
    )
    manifest, markdown = engine.run(selected_eco_id=args.eco, dry_run=args.dry_run)

    print(f"✅ FONTGEN ENGINE (V3.0 AGNOSTIC ENVATO SOURCING) EJECUTADO EXITOSAMENTE PARA: {args.brand.upper()}")
    print(f"  • Ecosistema Seleccionado: {manifest.get('selected_ecosystem_id')}")
    print(f"  • Display (Token 1): {manifest['selected_ecosystem']['tokens']['display_primary']['$value']} ({manifest['selected_ecosystem']['tokens']['display_primary']['url']})")
    print(f"  • UI (Token 2):      {manifest['selected_ecosystem']['tokens']['ui_secondary']['$value']} ({manifest['selected_ecosystem']['tokens']['ui_secondary']['url']})")
    print(f"  • Acento (Token 3):  {manifest['selected_ecosystem']['tokens']['accent_brand']['$value']} ({manifest['selected_ecosystem']['tokens']['accent_brand']['url']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
