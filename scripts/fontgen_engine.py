#!/usr/bin/env python3
"""
fontgen_engine.py — Sovereign Art-Direction-First Typographic Compiler (v7.0).
Clean-slate Nov 2026 + Playbook 19 + Context7-Verified Astro Native Fonts API:
- Zero hidden Oráculo filesystem crawling: shards/brief are read ONLY when explicitly passed via --shards/--brief.
- Separates creative Art Direction (--spec font_spec.json) from deterministic WOFF2 + CLS=0 + Envato verification.
- Strict anti-slop font ban & anti-amateur/sci-fi Envato noise filtering.
- <= 2 core active families (Display + Body) + conditional Mono, with Astro fontProviders.fontsource() / local().
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html as html_lib
import json
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
    "disco", "pixel", "pixelated", "bubble", "drippy", "funky", "mecha", "robot", "scifi", "sci-fi",
    "futuristic", "cyber", "cyberpunk", "techno", "gaming", "arcade", "neon", "glitch", "space", "alien", "esport", "stencil",
    "death", "wavy", "playful", "farmhouse", "christmas", "valentine", "y2k", "grunge",
    "blackletter", "medieval", "rounded", "90s", "80s", "70s", "terror", "fear", "drawn",
}

VANGUARD_CRAFT_TOKENS = {
    "inktrap", "grotesk", "grotesque", "groteks", "neo", "variable", "family", "pro",
    "condensed", "editorial", "geometric", "modern", "cinematic", "minimal", "minimalist",
    "sans", "didone", "brutalist", "serif", "swiss",
}

BANNED_OVERUSED_FAMILIES = {
    "inter", "fraunces", "instrument serif", "plus jakarta sans", "space grotesk",
    "dm sans", "instrument sans", "outfit", "syne", "playfair display",
    "newsreader", "ibm plex sans", "lora", "cormorant", "crimson text", "space mono",
}


# -----------------------------------------------------------------------------
# Verified Curated Envato Fallback Catalog (used only offline / --no-live)
# -----------------------------------------------------------------------------

ENVATO_VERIFIED_CATALOG: Dict[str, Dict[str, Any]] = {
    "bagina_editorial": {"family": "Bagina", "item_uuid": "3bd954cf-9759-4238-b79a-42bc88e5c832", "url": "https://app.envato.com/fonts/3bd954cf-9759-4238-b79a-42bc88e5c832", "category": "serif", "weights": ["400", "600", "700"]},
    "heronium_display": {"family": "Heronium", "item_uuid": "202ae3c2-f217-43dd-a5aa-767ade79c626", "url": "https://app.envato.com/fonts/202ae3c2-f217-43dd-a5aa-767ade79c626", "category": "sans", "weights": ["400", "600", "700"]},
    "centure_grotesk": {"family": "Centure", "item_uuid": "8d4c77c6-31f5-4c0c-a58c-28f4d9e8a9c1", "url": "https://app.envato.com/fonts/8d4c77c6-31f5-4c0c-a58c-28f4d9e8a9c1", "category": "sans", "weights": ["400", "600", "700"]},
    "nority_inktrap": {"family": "Nority", "item_uuid": "2e9b3477-adbb-44cb-93eb-d7b94b2cc9c9", "url": "https://app.envato.com/fonts/2e9b3477-adbb-44cb-93eb-d7b94b2cc9c9", "category": "sans", "weights": ["400", "600", "700"]},
    "xenon_nue": {"family": "Xenon Nue", "item_uuid": "12d5699d-d4a8-4231-abcc-4a1aec744a4a", "url": "https://app.envato.com/fonts/12d5699d-d4a8-4231-abcc-4a1aec744a4a", "category": "sans", "weights": ["400", "600", "700"]},
    "helvena_grotesk": {"family": "Helvena Grotesk", "item_uuid": "28f120ab-2460-43f2-8f72-7b982cb8c27b", "url": "https://app.envato.com/fonts/28f120ab-2460-43f2-8f72-7b982cb8c27b", "category": "sans", "weights": ["400", "600", "700"]},
    "commune_inktrap_serif": {"family": "Commune", "item_uuid": "276b2711-b524-41a2-91b0-a8f117dae846", "url": "https://app.envato.com/fonts/276b2711-b524-41a2-91b0-a8f117dae846", "category": "serif", "weights": ["400", "600", "700"]},
    "maire_editorial": {"family": "Maire", "item_uuid": "07c929a4-98d1-4746-bedc-f60e0d96bf62", "url": "https://app.envato.com/fonts/07c929a4-98d1-4746-bedc-f60e0d96bf62", "category": "serif", "weights": ["400", "600", "700"]},
    "korolis_serif": {"family": "Korolis", "item_uuid": "25a6b739-a2ba-4eae-aced-4281dbf4b74b", "url": "https://app.envato.com/fonts/25a6b739-a2ba-4eae-aced-4281dbf4b74b", "category": "serif", "weights": ["400", "600", "700"]},
    "arteon_arch": {"family": "Arteon", "item_uuid": "9675e800-0193-40bc-b3fa-edfc5876bfee", "url": "https://app.envato.com/fonts/9675e800-0193-40bc-b3fa-edfc5876bfee", "category": "sans", "weights": ["400", "600", "700"]},
    "lenia_mono": {"family": "Lenia", "item_uuid": "f23df0ad-bbed-4d5b-927d-3e57d35ef0c0", "url": "https://app.envato.com/fonts/f23df0ad-bbed-4d5b-927d-3e57d35ef0c0", "category": "display", "weights": ["400", "600", "700"]},
    "grift_sans": {"family": "Grift", "item_uuid": "72c6db75-b4a2-482c-9392-9d7ae5559c6a", "url": "https://app.envato.com/fonts/72c6db75-b4a2-482c-9392-9d7ae5559c6a", "category": "sans", "weights": ["400", "600", "700"]},
    "monstral_display": {"family": "Monstral", "item_uuid": "2e1b9f00-43d2-4586-a06d-2a8f3591ddaa", "url": "https://app.envato.com/fonts/2e1b9f00-43d2-4586-a06d-2a8f3591ddaa", "category": "sans", "weights": ["400", "600", "700"]},
    "elvon_grotesk": {"family": "Elvon Grotesk", "item_uuid": "7d794fa7-9c19-4bf1-acf1-68ab664f664f", "url": "https://app.envato.com/fonts/7d794fa7-9c19-4bf1-acf1-68ab664f664f", "category": "sans", "weights": ["400", "600", "700"]},
    "fegon_serif": {"family": "Fegon", "item_uuid": "0e11a841-97ac-4c64-b94b-fee128d53ace", "url": "https://app.envato.com/fonts/0e11a841-97ac-4c64-b94b-fee128d53ace", "category": "serif", "weights": ["400", "600", "700"]},
    "beglack_serif": {"family": "Beglack", "item_uuid": "f297098d-0bf3-4611-beae-bbacb6a2e3b2", "url": "https://app.envato.com/fonts/f297098d-0bf3-4611-beae-bbacb6a2e3b2", "category": "serif", "weights": ["400", "600", "700"]},
    "colazun_serif": {"family": "Colazun", "item_uuid": "faf222a2-c8d8-4ada-81ae-a846d387f764", "url": "https://app.envato.com/fonts/faf222a2-c8d8-4ada-81ae-a846d387f764", "category": "serif", "weights": ["400", "600", "700"]},
    "gelga_serif": {"family": "Gelga", "item_uuid": "465e96f4-f98b-4e6b-b78e-c9484da0bc64", "url": "https://app.envato.com/fonts/465e96f4-f98b-4e6b-b78e-c9484da0bc64", "category": "serif", "weights": ["400", "600", "700"]},
    "bagind_serif": {"family": "Bagind", "item_uuid": "53269ad6-2b73-49a7-9c58-49c2393c9032", "url": "https://app.envato.com/fonts/53269ad6-2b73-49a7-9c58-49c2393c9032", "category": "serif", "weights": ["400", "600", "700"]},
    "taillevere_didone": {"family": "Taillevere", "item_uuid": "9dee7e7e-b2ad-42a9-8092-f674dc4bd330", "url": "https://app.envato.com/fonts/9dee7e7e-b2ad-42a9-8092-f674dc4bd330", "category": "serif", "weights": ["400", "600", "700"]},
    "vitrenuit_didone": {"family": "Vitrenuit", "item_uuid": "01936819-5715-488e-bd22-38d2d5a3c057", "url": "https://app.envato.com/fonts/01936819-5715-488e-bd22-38d2d5a3c057", "category": "serif", "weights": ["400", "600", "700"]},
    "konfus_organic": {"family": "Konfus", "item_uuid": "6cb2b36a-ef46-4297-9f0c-c67ffab37261", "url": "https://app.envato.com/fonts/6cb2b36a-ef46-4297-9f0c-c67ffab37261", "category": "serif", "weights": ["400", "600", "700"]},
}


# -----------------------------------------------------------------------------
# Verified Curated 2026 Fontsource Variable WOFF2 Registry (Zero AI Slop)
# -----------------------------------------------------------------------------

GOOGLE_FONTS_CATALOG: Dict[str, Dict[str, Any]] = {
    # Editorial & Contrast Serifs
    "source_serif_4": {"family": "Source Serif 4", "fontsource_pkg": "@fontsource-variable/source-serif-4", "url": "https://fonts.google.com/specimen/Source+Serif+4", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,200..900;1,8..60,200..900&display=swap", "variable_axes": "ital,opsz,wght@0..1,8..60,200..900", "weights": ["300", "400", "500", "600", "700", "800"], "category": "serif", "cls": {"fallback": "Times New Roman", "size_adjust": "99.0%", "ascent": "94.0%", "descent": "24.0%", "line_gap": "0%"}},
    "literata": {"family": "Literata", "fontsource_pkg": "@fontsource-variable/literata", "url": "https://fonts.google.com/specimen/Literata", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,200..800;1,7..72,200..800&display=swap", "variable_axes": "ital,opsz,wght@0..1,7..72,200..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "serif", "cls": {"fallback": "Times New Roman", "size_adjust": "99.2%", "ascent": "93.5%", "descent": "24.0%", "line_gap": "0%"}},
    "spectral": {"family": "Spectral", "fontsource_pkg": "@fontsource/spectral", "url": "https://fonts.google.com/specimen/Spectral", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&display=swap", "variable_axes": "ital,wght@0..1,400..700", "weights": ["400", "500", "600", "700"], "category": "serif", "cls": {"fallback": "Times New Roman", "size_adjust": "98.0%", "ascent": "93.0%", "descent": "24.0%", "line_gap": "0%"}},
    "eb_garamond": {"family": "EB Garamond", "fontsource_pkg": "@fontsource-variable/eb-garamond", "url": "https://fonts.google.com/specimen/EB+Garamond", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400..800;1,400..800&display=swap", "variable_axes": "ital,wght@0..1,400..800", "weights": ["400", "500", "600", "700", "800"], "category": "serif", "cls": {"fallback": "Times New Roman", "size_adjust": "97.5%", "ascent": "93.0%", "descent": "24.5%", "line_gap": "0%"}},
    "bodoni_moda": {"family": "Bodoni Moda", "fontsource_pkg": "@fontsource-variable/bodoni-moda", "url": "https://fonts.google.com/specimen/Bodoni+Moda", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..900;1,6..96,400..900&display=swap", "variable_axes": "ital,opsz,wght@0..1,6..96,400..900", "weights": ["400", "500", "600", "700", "800"], "category": "serif", "cls": {"fallback": "Times New Roman", "size_adjust": "98.0%", "ascent": "93.5%", "descent": "24.5%", "line_gap": "0%"}},
    "bitter": {"family": "Bitter", "fontsource_pkg": "@fontsource-variable/bitter", "url": "https://fonts.google.com/specimen/Bitter", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Bitter:ital,wght@0,200..800;1,200..800&display=swap", "variable_axes": "ital,wght@0..1,200..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "serif", "cls": {"fallback": "Times New Roman", "size_adjust": "98.8%", "ascent": "94.0%", "descent": "24.0%", "line_gap": "0%"}},
    "piazzolla": {"family": "Piazzolla", "fontsource_pkg": "@fontsource-variable/piazzolla", "url": "https://fonts.google.com/specimen/Piazzolla", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Piazzolla:ital,opsz,wght@0,8..30,300..800;1,8..30,300..800&display=swap", "variable_axes": "ital,opsz,wght@0..1,8..30,300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "serif", "cls": {"fallback": "Times New Roman", "size_adjust": "98.5%", "ascent": "93.0%", "descent": "24.0%", "line_gap": "0%"}},
    "brygada_1918": {"family": "Brygada 1918", "fontsource_pkg": "@fontsource-variable/brygada-1918", "url": "https://fonts.google.com/specimen/Brygada+1918", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Brygada+1918:ital,wght@0,400..700;1,400..700&display=swap", "variable_axes": "ital,wght@0..1,400..700", "weights": ["400", "500", "600", "700"], "category": "serif", "cls": {"fallback": "Times New Roman", "size_adjust": "98.4%", "ascent": "93.2%", "descent": "24.0%", "line_gap": "0%"}},
    # Humanist, Editorial & Swiss Grotesque Sans (Body / UI)
    "hanken_grotesk": {"family": "Hanken Grotesk", "fontsource_pkg": "@fontsource-variable/hanken-grotesk", "url": "https://fonts.google.com/specimen/Hanken+Grotesk", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Hanken+Grotesk:ital,wght@0,300..800;1,300..800&display=swap", "variable_axes": "ital,wght@0..1,300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "98.5%", "ascent": "94.0%", "descent": "23.5%", "line_gap": "0%"}},
    "albert_sans": {"family": "Albert Sans", "fontsource_pkg": "@fontsource-variable/albert-sans", "url": "https://fonts.google.com/specimen/Albert+Sans", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Albert+Sans:ital,wght@0,200..800;1,200..800&display=swap", "variable_axes": "ital,wght@0..1,200..800", "weights": ["200", "300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "99.0%", "ascent": "94.0%", "descent": "23.5%", "line_gap": "0%"}},
    "familjen_grotesk": {"family": "Familjen Grotesk", "fontsource_pkg": "@fontsource-variable/familjen-grotesk", "url": "https://fonts.google.com/specimen/Familjen+Grotesk", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Familjen+Grotesk:ital,wght@0,400..700;1,400..700&display=swap", "variable_axes": "ital,wght@0..1,400..700", "weights": ["400", "500", "600", "700"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "98.2%", "ascent": "93.8%", "descent": "23.8%", "line_gap": "0%"}},
    "schibsted_grotesk": {"family": "Schibsted Grotesk", "fontsource_pkg": "@fontsource-variable/schibsted-grotesk", "url": "https://fonts.google.com/specimen/Schibsted+Grotesk", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Schibsted+Grotesk:ital,wght@0,400..800;1,400..800&display=swap", "variable_axes": "ital,wght@0..1,400..800", "weights": ["400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "98.8%", "ascent": "94.2%", "descent": "23.6%", "line_gap": "0%"}},
    "work_sans": {"family": "Work Sans", "fontsource_pkg": "@fontsource-variable/work-sans", "url": "https://fonts.google.com/specimen/Work+Sans", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Work+Sans:ital,wght@0,300..800;1,300..800&display=swap", "variable_axes": "ital,wght@0..1,300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "99.1%", "ascent": "94.5%", "descent": "23.5%", "line_gap": "0%"}},
    "manrope": {"family": "Manrope", "fontsource_pkg": "@fontsource-variable/manrope", "url": "https://fonts.google.com/specimen/Manrope", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Manrope:wght@200..800&display=swap", "variable_axes": "wght@200..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "99.5%", "ascent": "94.0%", "descent": "23.5%", "line_gap": "0%"}},
    "figtree": {"family": "Figtree", "fontsource_pkg": "@fontsource-variable/figtree", "url": "https://fonts.google.com/specimen/Figtree", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Figtree:ital,wght@0,300..800;1,300..800&display=swap", "variable_axes": "ital,wght@0..1,300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "98.0%", "ascent": "94.0%", "descent": "24.0%", "line_gap": "0%"}},
    "onest": {"family": "Onest", "fontsource_pkg": "@fontsource-variable/onest", "url": "https://fonts.google.com/specimen/Onest", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Onest:wght@200..800&display=swap", "variable_axes": "wght@200..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "99.2%", "ascent": "94.2%", "descent": "23.5%", "line_gap": "0%"}},
    "public_sans": {"family": "Public Sans", "fontsource_pkg": "@fontsource-variable/public-sans", "url": "https://fonts.google.com/specimen/Public+Sans", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Public+Sans:ital,wght@0,300..800;1,300..800&display=swap", "variable_axes": "ital,wght@0..1,300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "98.8%", "ascent": "94.0%", "descent": "23.5%", "line_gap": "0%"}},
    "golos_text": {"family": "Golos Text", "fontsource_pkg": "@fontsource-variable/golos-text", "url": "https://fonts.google.com/specimen/Golos+Text", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Golos+Text:wght@400..800&display=swap", "variable_axes": "wght@400..800", "weights": ["400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "99.0%", "ascent": "94.0%", "descent": "23.5%", "line_gap": "0%"}},
    # Expressive / Architectural Display Sans
    "bricolage_grotesque": {"family": "Bricolage Grotesque", "fontsource_pkg": "@fontsource-variable/bricolage-grotesque", "url": "https://fonts.google.com/specimen/Bricolage+Grotesque", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,300..800&display=swap", "variable_axes": "opsz,wdth,wght@12..96,75..100,300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "98.0%", "ascent": "94.0%", "descent": "24.0%", "line_gap": "0%"}},
    "archivo": {"family": "Archivo", "fontsource_pkg": "@fontsource-variable/archivo", "url": "https://fonts.google.com/specimen/Archivo", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Archivo:ital,wdth,wght@0,75..100,200..800;1,75..100,200..800&display=swap", "variable_axes": "ital,wdth,wght@0..1,75..100,200..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "98.5%", "ascent": "94.0%", "descent": "24.0%", "line_gap": "0%"}},
    "red_hat_display": {"family": "Red Hat Display", "fontsource_pkg": "@fontsource-variable/red-hat-display", "url": "https://fonts.google.com/specimen/Red+Hat+Display", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Red+Hat+Display:ital,wght@0,400..800;1,400..800&display=swap", "variable_axes": "ital,wght@0..1,400..800", "weights": ["400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "98.4%", "ascent": "93.5%", "descent": "24.0%", "line_gap": "0%"}},
    "sora": {"family": "Sora", "fontsource_pkg": "@fontsource-variable/sora", "url": "https://fonts.google.com/specimen/Sora", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Sora:wght@300..800&display=swap", "variable_axes": "wght@300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "99.4%", "ascent": "94.0%", "descent": "23.5%", "line_gap": "0%"}},
    "unbounded": {"family": "Unbounded", "fontsource_pkg": "@fontsource-variable/unbounded", "url": "https://fonts.google.com/specimen/Unbounded", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Unbounded:wght@300..800&display=swap", "variable_axes": "wght@300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "104.0%", "ascent": "95.0%", "descent": "24.0%", "line_gap": "0%"}},
    "host_grotesk": {"family": "Host Grotesk", "fontsource_pkg": "@fontsource-variable/host-grotesk", "url": "https://fonts.google.com/specimen/Host+Grotesk", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Host+Grotesk:ital,wght@0,300..800;1,300..800&display=swap", "variable_axes": "ital,wght@0..1,300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "sans", "cls": {"fallback": "Arial", "size_adjust": "98.6%", "ascent": "94.0%", "descent": "23.5%", "line_gap": "0%"}},
    # Conditional Technical Monospace (only numbers/data tables/tech specs)
    "jetbrains_mono": {"family": "JetBrains Mono", "fontsource_pkg": "@fontsource-variable/jetbrains-mono", "url": "https://fonts.google.com/specimen/JetBrains+Mono", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,300..800;1,300..800&display=swap", "variable_axes": "ital,wght@0..1,300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "mono", "cls": {"fallback": "Courier New", "size_adjust": "96.0%", "ascent": "93.0%", "descent": "24.0%", "line_gap": "0%"}},
    "martian_mono": {"family": "Martian Mono", "fontsource_pkg": "@fontsource-variable/martian-mono", "url": "https://fonts.google.com/specimen/Martian+Mono", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Martian+Mono:wdth,wght@75..112.5,300..800&display=swap", "variable_axes": "wdth,wght@75..112.5,300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "mono", "cls": {"fallback": "Courier New", "size_adjust": "94.5%", "ascent": "92.0%", "descent": "24.0%", "line_gap": "0%"}},
    "azeret_mono": {"family": "Azeret Mono", "fontsource_pkg": "@fontsource-variable/azeret-mono", "url": "https://fonts.google.com/specimen/Azeret+Mono", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Azeret+Mono:ital,wght@0,300..800;1,300..800&display=swap", "variable_axes": "ital,wght@0..1,300..800", "weights": ["300", "400", "500", "600", "700", "800"], "category": "mono", "cls": {"fallback": "Courier New", "size_adjust": "95.5%", "ascent": "92.5%", "descent": "24.0%", "line_gap": "0%"}},
}


SIGN_NORMALIZATION: Dict[str, str] = {
    "aries": "Aries", "taurus": "Taurus", "tauro": "Taurus",
    "gemini": "Gemini", "geminis": "Gemini", "géminis": "Gemini",
    "cancer": "Cancer", "cáncer": "Cancer", "leo": "Leo", "virgo": "Virgo",
    "libra": "Libra", "scorpio": "Scorpio", "escorpio": "Scorpio",
    "sagittarius": "Sagittarius", "sagitario": "Sagittarius",
    "capricorn": "Capricorn", "capricornio": "Capricorn",
    "aquarius": "Aquarius", "acuario": "Aquarius",
    "pisces": "Pisces", "piscis": "Pisces",
}
ZODIAC_ELEMENTS = {"Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire", "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth", "Gemini": "Air", "Libra": "Air", "Aquarius": "Air", "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"}
ZODIAC_MODALITIES = {"Aries": "Cardinal", "Cancer": "Cardinal", "Libra": "Cardinal", "Capricorn": "Cardinal", "Taurus": "Fixed", "Leo": "Fixed", "Scorpio": "Fixed", "Aquarius": "Fixed", "Gemini": "Mutable", "Virgo": "Mutable", "Sagittarius": "Mutable", "Pisces": "Mutable"}
MODALITY_SCALE_RATIOS = {"Cardinal": 1.500, "Fixed": 1.333, "Mutable": 1.250}

STYLE_SCALE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "architectural_b2b": {"scale_ratio": 1.250, "needs_mono": True, "tracking_em": -0.025, "display_weight": 700, "mono_key": "jetbrains_mono"},
    "luxury_editorial": {"scale_ratio": 1.500, "needs_mono": False, "tracking_em": -0.020, "display_weight": 600, "mono_key": "jetbrains_mono"},
    "organic_wellness": {"scale_ratio": 1.333, "needs_mono": False, "tracking_em": -0.015, "display_weight": 600, "mono_key": "jetbrains_mono"},
    "bold_brutalist": {"scale_ratio": 1.500, "needs_mono": True, "tracking_em": -0.035, "display_weight": 800, "mono_key": "martian_mono"},
    "fintech_clinical": {"scale_ratio": 1.250, "needs_mono": True, "tracking_em": -0.020, "display_weight": 700, "mono_key": "jetbrains_mono"},
    "warm_hospitality": {"scale_ratio": 1.333, "needs_mono": False, "tracking_em": -0.018, "display_weight": 700, "mono_key": "jetbrains_mono"},
    "creative_playful": {"scale_ratio": 1.333, "needs_mono": False, "tracking_em": -0.022, "display_weight": 700, "mono_key": "martian_mono"},
    "cosmic_archetypal": {"scale_ratio": 1.333, "needs_mono": True, "tracking_em": -0.020, "display_weight": 700, "mono_key": "jetbrains_mono"},
    "design_system_atelier": {"scale_ratio": 1.250, "needs_mono": True, "tracking_em": -0.025, "display_weight": 700, "mono_key": "martian_mono"},
    "editorial_manifesto": {"scale_ratio": 1.500, "needs_mono": False, "tracking_em": -0.025, "display_weight": 700, "mono_key": "jetbrains_mono"},
    "editorial_brand": {"scale_ratio": 1.333, "needs_mono": False, "tracking_em": -0.020, "display_weight": 700, "mono_key": "jetbrains_mono"},
}


_ORACULO_ELEMENTS = {"water": "Water", "agua": "Water", "fire": "Fire", "fuego": "Fire", "wood": "Wood", "madera": "Wood", "earth": "Earth", "tierra": "Earth", "metal": "Metal", "air": "Air", "aire": "Air"}
_ORACULO_NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
)
_BAZI_YANG_STEMS = {"Jia", "Bing", "Wu", "Geng", "Ren"}
_BAZI_ALL_STEMS = ("Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui")
_PLANET_MAP = {"sun": "Sun", "sol": "Sun", "moon": "Moon", "luna": "Moon", "mars": "Mars", "marte": "Mars", "mercury": "Mercury", "mercurio": "Mercury", "jupiter": "Jupiter", "júpiter": "Jupiter", "venus": "Venus", "saturn": "Saturn", "saturno": "Saturn"}
_NAKSHATRA_CRAFT = {
    "Chitra": "sculptural_precision", "Hasta": "sculptural_precision", "Rohini": "sculptural_precision", "Mrigashira": "sculptural_precision",
    "Ashwini": "incisive_authority", "Krittika": "incisive_authority", "Magha": "incisive_authority", "Jyeshtha": "incisive_authority",
    "Swati": "architectural_modern", "Shatabhisha": "architectural_modern", "Dhanishta": "architectural_modern", "Uttara Phalguni": "architectural_modern",
}


def normalize_zodiac_sign(raw_sign: str) -> str:
    s = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚ]", "", str(raw_sign or "").strip()).lower()
    return SIGN_NORMALIZATION.get(s, "")


def parse_oraculo_brief_signals(txt: str) -> Dict[str, str]:
    """Strict Oráculo markdown extractor returning only validated signs/nakshatras/stems (never stop-words like 'Como')."""
    out: Dict[str, str] = {}
    sign_alts = "|".join(sorted(SIGN_NORMALIZATION.keys(), key=len, reverse=True))
    m_sol = re.search(rf"(?:Sol\s*Natal|Tropical\s+Placidus)[^\n]{{0,120}}\b({sign_alts})\b", txt, re.IGNORECASE)
    if m_sol and normalize_zodiac_sign(m_sol.group(1)):
        out["sun_sign"] = normalize_zodiac_sign(m_sol.group(1))
    m_mc_row = re.search(rf"^\|\s*\*\*Medio\s*Cielo[^|]*\|\s*\*\*({sign_alts})[^|]*\|\s*\*\*({sign_alts})", txt, re.IGNORECASE | re.MULTILINE)
    if m_mc_row:
        if normalize_zodiac_sign(m_mc_row.group(1)):
            out["mc_sign"] = normalize_zodiac_sign(m_mc_row.group(1))
        if normalize_zodiac_sign(m_mc_row.group(2)):
            out["sidereal_mc_sign"] = normalize_zodiac_sign(m_mc_row.group(2))
    else:
        m_mc = re.search(rf"(?:Medio\s*Cielo[^\n|]{{0,60}}\||MC\s+en\s+\**)\s*\**({sign_alts})\b", txt, re.IGNORECASE)
        if m_mc and normalize_zodiac_sign(m_mc.group(1)):
            out["mc_sign"] = normalize_zodiac_sign(m_mc.group(1))
    nak_alts = "|".join(_ORACULO_NAKSHATRAS)
    m_nak = re.search(rf"Nakshatra[^\n]{{0,80}}\b({nak_alts})\b", txt, re.IGNORECASE)
    if m_nak:
        out["nakshatra"] = next((n for n in _ORACULO_NAKSHATRAS if n.lower() == m_nak.group(1).lower()), "")
    dm_alts = "|".join(_BAZI_ALL_STEMS)
    m_dm = re.search(rf"Day\s*Master[^\n]{{0,40}}\b({dm_alts})\b", txt, re.IGNORECASE)
    if m_dm:
        out["day_master"] = m_dm.group(1).title()
    m_dom = re.search(r"Elemento\s+dominante\**\s*:?\**\s*([A-Za-záéíóúÁÉÍÓÚ]+)", txt, re.IGNORECASE)
    if m_dom and m_dom.group(1).lower() in _ORACULO_ELEMENTS:
        out["dominant_element"] = _ORACULO_ELEMENTS[m_dom.group(1).lower()]
    m_ys = re.search(r"Yong\s*Shen\**\s*:?\**\s*([A-Za-záéíóúÁÉÍÓÚ]+)", txt, re.IGNORECASE)
    if m_ys and m_ys.group(1).lower() in _ORACULO_ELEMENTS:
        out["yong_shen"] = _ORACULO_ELEMENTS[m_ys.group(1).lower()]
    pl_alts = "|".join(sorted(_PLANET_MAP.keys(), key=len, reverse=True))
    m_sh = re.search(rf"Dominante\s+Shadbala\s*:\s*\**({pl_alts})\b", txt, re.IGNORECASE)
    if m_sh:
        out["shadbala_dominant"] = _PLANET_MAP.get(m_sh.group(1).lower(), "Sun")
    return {k: v for k, v in out.items() if v}


def classify_vertical_style_profile(vblob: str, vertical_slug: str = "") -> str:
    t = f"{vertical_slug} {vblob}".lower()
    if any(k in t for k in ("multi_branch_hub", "hub_root", "hub oficial")):
        return "editorial_brand"
    if any(k in t for k in ("sabidurías cósmicas", "arquetipo vocacional", "astrolog", "kabbalah", "human design", "numerolog", "tarot", "carta natal")):
        return "cosmic_archetypal"
    if any(k in t for k in ("design system", "tokens de diseño", "brandbook", "monogramas vectoriales", "tipografía curada", "tokens dtcg")):
        return "design_system_atelier"
    if any(k in t for k in ("manifiesto", "book_waitlist", "libro", "ensayo filosófico")):
        return "editorial_manifesto"
    if any(k in t for k in ("lujo", "luxury", "alta costura", "atelier", "joyería", "boutique", "bespoke")):
        return "luxury_editorial"
    if any(k in t for k in ("bienestar", "wellness", "orgánic", "organic", "botánic", "spa", "skincare")):
        return "organic_wellness"
    if any(k in t for k in ("brutalis", "industrial", "arquitectura", "streetwear")):
        return "bold_brutalist"
    if any(k in t for k in ("fintech", "clínic", "clinic", "hospital", "biotech", "banca", "auditoría", "ciberseguridad")):
        return "fintech_clinical"
    if any(k in t for k in ("café", "coffee", "restaurante", "gastronom", "hotel", "hospitalidad")):
        return "warm_hospitality"
    if any(k in t for k in ("educación", "edtech", "creativ", "comunidad", "podcast", "playful")):
        return "creative_playful"
    if any(k in t for k in ("consultor", "b2b", "unipersonal", "agencia", "automatiz", "saas", "seo local")):
        return "architectural_b2b"
    return "editorial_brand"


def _resolve_web_font(name_or_key: str, default_key: str = "hanken_grotesk") -> Dict[str, Any]:
    raw = str(name_or_key or "").strip()
    if not raw:
        return GOOGLE_FONTS_CATALOG[default_key]
    slug = re.sub(r"[^a-z0-9]+", "_", raw.lower()).strip("_")
    if slug in GOOGLE_FONTS_CATALOG:
        return GOOGLE_FONTS_CATALOG[slug]
    for v in GOOGLE_FONTS_CATALOG.values():
        if v["family"].lower() == raw.lower():
            return v
    if raw.lower() in BANNED_OVERUSED_FAMILIES:
        return GOOGLE_FONTS_CATALOG[default_key]
    return GOOGLE_FONTS_CATALOG[default_key]


class FontgenEngine:
    """Art-Direction-First Typographic Compiler (v7.0) — zero hidden Oráculo disk leaks."""

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
        sibling_workspaces_dir: Optional[Path] = None,
        exclude_fonts: Optional[List[str]] = None,
        brand_brief_path: Optional[Path] = None,
        include_mono: Optional[bool] = None,
        spec_path: Optional[Path] = None,
    ):
        self.brand_raw = brand.strip()
        self.brand_upper = self.brand_raw.upper()
        self.brand_lower = self.brand_raw.lower()
        self.shards_path = Path(shards_path).resolve() if shards_path else None
        self.brief_path = Path(brief_path).resolve() if brief_path else None
        self.brand_brief_path = Path(brand_brief_path).resolve() if brand_brief_path else None
        self.vertical_json_path = Path(vertical_json_path).resolve() if vertical_json_path else None
        self.spec_path = Path(spec_path).resolve() if spec_path else None
        self.include_mono = include_mono
        self.output_dir = Path(output_dir).resolve() if output_dir else None
        self.use_live_search = use_live_search
        self.allow_default = allow_default
        self.override_params = override_params or {}
        self.create_brand_dirs = create_brand_dirs
        self.verify_svg_preview = verify_svg_preview
        self.style_profile = style_profile
        self.sort_mode = sort_mode
        self.seed = max(0, int(seed))
        self.sibling_workspaces_dir = Path(sibling_workspaces_dir).resolve() if sibling_workspaces_dir else None
        if not self.sibling_workspaces_dir and self.output_dir:
            if self.output_dir.name == "brand" and self.output_dir.parent.parent.name == "workspaces":
                self.sibling_workspaces_dir = self.output_dir.parent.parent

        self.explicit_exclude_fonts: Set[str] = {f.strip().lower() for f in (exclude_fonts or []) if f and f.strip()}
        self.used_families: Set[str] = set()
        self.used_uuids: Set[str] = set()
        self.excluded_envato_families: Set[str] = set()
        self.excluded_envato_uuids: Set[str] = set()
        self.excluded_google_families: Set[str] = set()
        self.hard_excluded_google_families: Set[str] = set()
        self._load_sibling_exclusions()

    def _load_sibling_exclusions(self) -> None:
        for f in self.explicit_exclude_fonts:
            self.excluded_envato_families.add(f)
            self.excluded_google_families.add(f)
            self.hard_excluded_google_families.add(f)
            self.used_families.add(f)

        ws_root = self.sibling_workspaces_dir
        if not ws_root or not ws_root.is_dir():
            return
        own_brand_dir = self.output_dir.resolve() if self.output_dir else None
        for child in sorted(ws_root.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            sib_brand = (child / "brand").resolve()
            if own_brand_dir and sib_brand == own_brand_dir:
                continue
            fm_path = sib_brand / "font_manifest.json"
            if not fm_path.is_file():
                continue
            try:
                fm = json.loads(fm_path.read_text(encoding="utf-8"))
                sel = (fm.get("selected_ecosystem") or {}).get("tokens", {})
                for rk in ("display_primary", "accent_brand"):
                    tok = sel.get(rk, {})
                    fam = str(tok.get("$value") or "").strip().lower()
                    uid = str(tok.get("item_uuid") or _extract_uuid(str(tok.get("url") or ""))).lower()
                    if fam:
                        self.excluded_envato_families.add(fam)
                        self.used_families.add(fam)
                    if uid:
                        self.excluded_envato_uuids.add(uid)
                        self.used_uuids.add(uid)
                bridge = fm.get("web_ready_bridge", {})
                for bk in ("display_fallback_family", "body_family", "editorial_italic_family"):
                    bf = str(bridge.get(bk) or "").strip().lower()
                    if bf:
                        self.excluded_google_families.add(bf)
                        self.hard_excluded_google_families.add(bf)
                gf_sel = str(sel.get("ui_secondary", {}).get("$value") or "").strip().lower()
                if gf_sel:
                    self.excluded_google_families.add(gf_sel)
                    self.hard_excluded_google_families.add(gf_sel)
                for eco in fm.get("candidate_ecosystems", []):
                    toks = eco.get("tokens", {})
                    for rk in ("display_primary", "accent_brand"):
                        tok = toks.get(rk, {})
                        fam = str(tok.get("$value") or "").strip().lower()
                        uid = str(tok.get("item_uuid") or _extract_uuid(str(tok.get("url") or ""))).lower()
                        if fam:
                            self.excluded_envato_families.add(fam)
                            self.used_families.add(fam)
                        if uid:
                            self.excluded_envato_uuids.add(uid)
                            self.used_uuids.add(uid)
                    gfc = str(toks.get("ui_secondary", {}).get("$value") or "").strip().lower()
                    if gfc:
                        self.excluded_google_families.add(gfc)
            except Exception:
                pass

    def _clean_family_name(self, raw_title: str) -> str:
        if not raw_title:
            return "Untitled Font"
        first_part = html_lib.unescape(re.split(r"[,|\-–—:]", raw_title)[0].strip())
        first_part = re.sub(r"[®™©]+", "", first_part).strip()
        first_part = re.sub(r"\s+(?:For|With|A)\s+.*$", "", first_part, flags=re.IGNORECASE).strip()
        cleaned = re.sub(
            r"\b(?:Font|Typeface|Family|Display|Serif|Sans|Bold|Minimalist|Minimal|Clean|Modern|Branding|Logo)\b",
            "", first_part, flags=re.IGNORECASE,
        ).strip()
        words_dedup = list(dict.fromkeys(w.title() for w in re.sub(r"\s+", " ", cleaned).split() if w))
        res = " ".join(words_dedup).strip()
        return res if len(res) >= 2 else first_part.strip().title()

    def _is_noisy_title(self, raw_title: str) -> bool:
        words = set(re.findall(r"[a-z0-9-]+", raw_title.lower()))
        if words.intersection(NOISE_BLOCKLIST_BASE):
            return True
        if any(phrase in raw_title.lower() for phrase in ("for elegant", "for branding", "for logo", "for wedding", "for poster")):
            return True
        return False

    def _score_candidate(self, title: str, is_new: bool, has_svg: bool, sort_label: str, query_term: str = "") -> int:
        words = re.findall(r"[a-z0-9]+", title.lower())
        wset = set(words)
        score = 20
        if sort_label == "popular":
            score += 14
        elif is_new or sort_label == "latest":
            score += 8
        if has_svg:
            score += 8
        craft_hits = len(wset.intersection(VANGUARD_CRAFT_TOKENS))
        score += craft_hits * 9
        # Clean concise foundry names beat SEO keyword-stuffed titles
        fam_clean = self._clean_family_name(title)
        if len(fam_clean.split()) <= 2:
            score += 14
        elif len(fam_clean.split()) >= 4:
            score -= 18
        if "mono" in wset or "monospace" in wset:
            score += 12 if "mono" in query_term.lower() else -16
        if "logo" in wset:
            score -= 22
        if len(title) > 48:
            score -= 10
        return score

    def _is_previewable_uuid(self, item_uuid: str) -> bool:
        if not item_uuid:
            return False
        if not self.verify_svg_preview:
            return True
        txt = urllib.parse.quote_plus("DISEÑO Ñ")
        svg_url = f"https://elements.envato.com/font-preview.svg?itemUuid={urllib.parse.quote(item_uuid)}&text={txt}&typed=1"
        try:
            req = urllib.request.Request(svg_url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", "Referer": "https://elements.envato.com/"})
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
                out.append({
                    "uuid": fid,
                    "title": title,
                    "author": str(it.get("author") or "Envato Foundry"),
                    "is_new": bool(it.get("isNew")),
                    "has_svg": bool(it.get("fontPreviewSvg") or it.get("fontPreviewSvgs")),
                    "sort_label": sort_opt,
                    "source_url": url,
                    "item_url": f"https://elements.envato.com{item_url}" if item_url.startswith("/") else f"https://app.envato.com/fonts/{fid}",
                })
        except Exception:
            pass
        return out

    def _search_live_envato_fonts(
        self,
        elements_term: str,
        category_slug: str = "sans-serif",
        category_label: str = "sans",
        seed_offset: int = 0,
    ) -> Optional[Dict[str, Any]]:
        if not self.use_live_search:
            return None
        sorts = ["popular", "latest"] if self.sort_mode == "hybrid" else [self.sort_mode]
        raw_pool: List[Dict[str, Any]] = []
        term_slug = elements_term.strip().replace(" ", "+")
        for s in sorts:
            hits = self._fetch_elements_hydration(term_slug, category_slug, s)
            if not hits:
                hits = self._fetch_elements_hydration(term_slug, None, s)
            raw_pool.extend(hits)

        scored: List[Tuple[int, Dict[str, Any]]] = []
        seen_u: Set[str] = set()
        seen_f: Set[str] = set()
        for c in raw_pool:
            fid = c["uuid"]
            if fid in seen_u or fid in self.used_uuids:
                continue
            seen_u.add(fid)
            if self._is_noisy_title(c["title"]):
                continue
            fam = self._clean_family_name(c["title"])
            fl = fam.lower()
            if fl in seen_f or fl in self.used_families or fl in BANNED_OVERUSED_FAMILIES or len(fam) < 2:
                continue
            seen_f.add(fl)
            sc = self._score_candidate(c["title"], c["is_new"], c["has_svg"], c["sort_label"], elements_term)
            scored.append((sc, {**c, "family": fam}))

        scored.sort(key=lambda x: (-x[0], x[1]["family"]))
        verified: List[Dict[str, Any]] = []
        start_idx = (self.seed + seed_offset) % max(1, min(len(scored), 5))
        rotated = scored[start_idx:] + scored[:start_idx]
        for sc, item in rotated[:14]:
            if not self._is_previewable_uuid(item["uuid"]):
                continue
            verified.append({"score": sc, **item})
            if len(verified) >= 5:
                break
        if not verified:
            return None

        best = verified[0]
        self.used_families.add(best["family"].lower())
        self.used_uuids.add(best["uuid"])
        shortlist = [
            {"family": v["family"], "item_uuid": v["uuid"], "url": f"https://app.envato.com/fonts/{v['uuid']}", "elements_url": v["item_url"], "sort_source": v["sort_label"], "score": v["score"]}
            for v in verified[1:4]
        ]
        return {
            "family": best["family"],
            "source": "envato",
            "item_uuid": best["uuid"],
            "url": f"https://app.envato.com/fonts/{best['uuid']}",
            "elements_url": best["item_url"],
            "search_url": best["source_url"],
            "category": category_label,
            "weights": ["400", "600", "700"],
            "description": f"{best['title']} by {best['author']} (Envato Elements, score={best['score']}, sort={best['sort_label']}).",
            "shortlist": shortlist,
        }

    def _get_fallback_envato_font(self, preferred_key: str) -> Dict[str, Any]:
        keys = [preferred_key] + [k for k in ENVATO_VERIFIED_CATALOG if k != preferred_key]
        for k in keys:
            item = ENVATO_VERIFIED_CATALOG[k]
            if item["family"].lower() not in self.used_families and item["item_uuid"] not in self.used_uuids:
                self.used_families.add(item["family"].lower())
                self.used_uuids.add(item["item_uuid"])
                return {**item, "source": "envato", "elements_url": item["url"], "search_url": "https://app.envato.com/fonts", "description": f"{item['family']} — Verified Curated Catalog.", "shortlist": []}
        item = ENVATO_VERIFIED_CATALOG[preferred_key]
        return {**item, "source": "envato", "elements_url": item["url"], "search_url": "https://app.envato.com/fonts", "description": f"{item['family']} — Verified Curated Catalog.", "shortlist": []}

    def _pick_google_font(self, preferred_keys: List[str], used_in_run: Set[str], offset: int = 0, category_filter: Optional[str] = None) -> Dict[str, Any]:
        clean = [k for k in preferred_keys if k in GOOGLE_FONTS_CATALOG and (not category_filter or GOOGLE_FONTS_CATALOG[k]["category"] == category_filter)]
        if not clean:
            clean = [k for k, v in GOOGLE_FONTS_CATALOG.items() if (not category_filter or v["category"] == category_filter)]
        shift = offset % len(clean)
        ordered = clean[shift:] + clean[:shift]
        for pass_excl in (self.excluded_google_families, self.hard_excluded_google_families, set()):
            for k in ordered:
                it = GOOGLE_FONTS_CATALOG[k]
                fl = it["family"].lower()
                if fl not in used_in_run and fl not in pass_excl and fl not in BANNED_OVERUSED_FAMILIES:
                    used_in_run.add(fl)
                    return it
        it = GOOGLE_FONTS_CATALOG[ordered[0]]
        used_in_run.add(it["family"].lower())
        return it

    def resolve_inputs(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "sun_sign": "",
            "mc_sign": "",
            "sidereal_mc_sign": "",
            "day_master": "",
            "nakshatra": "",
            "dominant_element": "",
            "style_profile": self.style_profile if self.style_profile != "auto" else "editorial_brand",
            "vertical_slug": self.brand_lower,
            "vertical_display_name": self.brand_upper,
            "sources_used": [],
            "has_oraculo": False,
        }
        # Strictly opt-in: ONLY read shards/brief if explicitly passed via --shards or --brief
        if self.shards_path and self.shards_path.is_file():
            sd = json.loads(self.shards_path.read_text(encoding="utf-8"))
            s1 = sd.get("shard_01", {}).get("data", {})
            s2 = sd.get("shard_02", {}).get("data", {})
            s3 = sd.get("shard_03", {}).get("data", {})
            s4 = sd.get("shard_04", {}).get("data", {})
            params["sun_sign"] = normalize_zodiac_sign(s1.get("tripod_of_iron", {}).get("sun", {}).get("sign") or "")
            params["mc_sign"] = normalize_zodiac_sign(s1.get("tripod_of_iron", {}).get("midheaven_house_10", {}).get("sign") or "")
            params["sidereal_mc_sign"] = normalize_zodiac_sign(s2.get("fagan_bradley", {}).get("midheaven", {}).get("sign") or "")
            params["dominant_element"] = str(s1.get("arroyo_elements", {}).get("dominant_element") or "")
            params["nakshatra"] = str(s3.get("nakshatra", {}).get("name") or "").split()[0]
            params["day_master"] = str(s4.get("day_master", {}).get("name") or "").split()[0]
            params["shadbala_dominant"] = str(s3.get("shadbala", {}).get("dominant_planet") or "Sun")
            params["sources_used"].append(f"shards:{self.shards_path.name}")
            params["has_oraculo"] = True

        if self.brief_path and self.brief_path.is_file():
            params["sources_used"].append(f"brief:{self.brief_path.name}")
            txt = self.brief_path.read_text(encoding="utf-8", errors="replace")
            parsed = parse_oraculo_brief_signals(txt)
            for k, v in parsed.items():
                if not params.get(k):
                    params[k] = v
            if parsed:
                params["has_oraculo"] = True

        vfile = self.vertical_json_path if (self.vertical_json_path and self.vertical_json_path.is_file()) else (self.brand_brief_path if (self.brand_brief_path and self.brand_brief_path.is_file()) else None)
        if vfile:
            params["sources_used"].append(f"{'vertical' if vfile == self.vertical_json_path else 'brand_brief'}:{vfile.name}")
            raw_txt = vfile.read_text(encoding="utf-8", errors="replace")
            if vfile.suffix.lower() == ".json":
                vdata = json.loads(raw_txt)
                params["vertical_slug"] = str(vdata.get("vertical_slug") or vfile.stem).lower()
                params["vertical_display_name"] = str(vdata.get("display_name") or vdata.get("name") or self.brand_upper)
                if self.style_profile == "auto":
                    params["style_profile"] = str(vdata.get("style_profile") or "") or classify_vertical_style_profile(raw_txt, params["vertical_slug"])
            else:
                if self.style_profile == "auto":
                    params["style_profile"] = classify_vertical_style_profile(raw_txt, params["vertical_slug"])

        for k, v in self.override_params.items():
            if v:
                params[k] = v
                if k in ("sun_sign", "mc_sign", "day_master", "nakshatra"):
                    params["has_oraculo"] = True
        return params

    def _compute_effective_seed(self, params: Dict[str, Any]) -> int:
        orac_sig = f"::{params.get('sun_sign','')}::{params.get('mc_sign','')}::{params.get('sidereal_mc_sign','')}::{params.get('nakshatra','')}::{params.get('day_master','')}" if params.get("has_oraculo") else ""
        raw = f"{self.brand_lower}::{params.get('vertical_slug', '')}::{params.get('style_profile', '')}{orac_sig}"
        return self.seed + (hashlib.sha256(raw.encode("utf-8")).digest()[0] % 64)

    def _pack_ecosystem(
        self,
        eid: str,
        ename: str,
        arch_label: str,
        rationale: str,
        disp_gf: Dict[str, Any],
        body_gf: Dict[str, Any],
        italic_gf: Dict[str, Any],
        prim_envato: Dict[str, Any],
        acc_envato: Dict[str, Any],
        scale_ratio: float,
        tracking_em: float,
        display_weight: int,
    ) -> Dict[str, Any]:
        tokens = {
            "display_primary": {"$value": prim_envato["family"], "$type": "fontFamily", "$description": f"Envato Elements — {prim_envato['description']}", "source": "envato", "category": prim_envato.get("category", "sans"), "item_uuid": prim_envato["item_uuid"], "url": prim_envato["url"], "elements_url": prim_envato.get("elements_url", prim_envato["url"]), "search_url": prim_envato.get("search_url", "https://app.envato.com/fonts"), "weights": prim_envato.get("weights", ["400", "600", "700"])},
            "ui_secondary": {"$value": body_gf["family"], "$type": "fontFamily", "$description": "Astro Native Fonts WOFF2 / Workhorse UI", "source": "google_fonts", "category": body_gf["category"], "url": body_gf["url"], "google_fonts_v2_url": body_gf["google_fonts_v2_url"], "variable_axes": body_gf["variable_axes"], "weights": body_gf["weights"]},
            "accent_brand": {"$value": acc_envato["family"], "$type": "fontFamily", "$description": f"Envato Elements — {acc_envato['description']}", "source": "envato", "category": acc_envato.get("category", "display"), "item_uuid": acc_envato["item_uuid"], "url": acc_envato["url"], "elements_url": acc_envato.get("elements_url", acc_envato["url"]), "search_url": acc_envato.get("search_url", "https://app.envato.com/fonts"), "weights": acc_envato.get("weights", ["400", "600", "700"])},
        }
        return {
            "id": eid,
            "name": ename,
            "archetype": arch_label,
            "scale_ratio": scale_ratio,
            "rationale": rationale,
            "web_fallback_display": disp_gf,
            "web_editorial_italic": italic_gf,
            "web_pair": {"display_family": disp_gf["family"], "display_v2_url": disp_gf["google_fonts_v2_url"], "body_family": body_gf["family"], "body_v2_url": body_gf["google_fonts_v2_url"], "italic_family": italic_gf["family"]},
            "tokens": tokens,
            "shortlist_candidates": {"display_alternatives": prim_envato.get("shortlist", []), "accent_alternatives": acc_envato.get("shortlist", [])},
            "layers": {
                "logo": f"{acc_envato['family']} (Weight 700, Tracking -0.02em)",
                "slogan": f"{disp_gf['family']} (Weight 500, Tracking +0.04em)",
                "h1": f"{disp_gf['family']} (clamp(2.5rem, 1.85rem + 3.2vw, 4.5rem), Ratio {scale_ratio:.3f}, Tracking {tracking_em:+.3f}em)",
                "h2": f"{disp_gf['family']} (Weight {display_weight}, Ratio {scale_ratio:.3f})",
                "body": f"{body_gf['family']} (Variable Regular 400, Line-height 1.60, Medida 60-72ch)",
                "ui": f"{body_gf['family']} (Variable SemiBold 600, Tracking -0.01em, tabular-nums)",
            },
            "cls_metric_overrides": {
                "fallback_font": body_gf["cls"]["fallback"],
                "size_adjust": body_gf["cls"]["size_adjust"],
                "ascent_override": body_gf["cls"]["ascent"],
                "descent_override": body_gf["cls"]["descent"],
                "line_gap_override": body_gf["cls"]["line_gap"],
                "display": {"fallback_font": disp_gf["cls"]["fallback"], "size_adjust": disp_gf["cls"]["size_adjust"], "ascent_override": disp_gf["cls"]["ascent"], "descent_override": disp_gf["cls"]["descent"], "line_gap_override": disp_gf["cls"]["line_gap"]},
                "body": {"fallback_font": body_gf["cls"]["fallback"], "size_adjust": body_gf["cls"]["size_adjust"], "ascent_override": body_gf["cls"]["ascent"], "descent_override": body_gf["cls"]["descent"], "line_gap_override": body_gf["cls"]["line_gap"]},
            },
            "workbench_presets": {"font_size_px": 60, "letter_spacing_em": tracking_em, "line_height": 1.10, "text_transform": "none", "font_weight": str(display_weight), "ligatures_enabled": False},
        }

    def build_ecosystems(self, params: Dict[str, Any], resolved_spec: Optional[Path] = None) -> List[Dict[str, Any]]:
        style_profile = params.get("style_profile", "editorial_brand")
        arch_prof = STYLE_SCALE_DEFAULTS.get(style_profile, STYLE_SCALE_DEFAULTS["editorial_brand"])
        eff_seed = self._compute_effective_seed(params)
        used_web_run: Set[str] = set()

        if resolved_spec and resolved_spec.is_file():
            spec_data = json.loads(resolved_spec.read_text(encoding="utf-8"))
            items = spec_data if isinstance(spec_data, list) else spec_data.get("ecosystems", [])
            ecosystems: List[Dict[str, Any]] = []
            for idx_s, it in enumerate(items[:4]):
                eid = str(it.get("id") or f"eco-{idx_s + 1}")
                ename = str(it.get("name") or f"Sistema Tipográfico {idx_s + 1}")
                disp_gf = _resolve_web_font(it.get("display_web") or "source_serif_4", "source_serif_4")
                body_gf = _resolve_web_font(it.get("body_web") or "hanken_grotesk", "hanken_grotesk")
                italic_gf = _resolve_web_font(it.get("italic_web") or disp_gf["family"], disp_gf["family"] if disp_gf["category"] == "serif" else "source_serif_4")
                scale_r = float(it.get("scale_ratio") or arch_prof["scale_ratio"])
                track_em = float(it.get("tracking_em") if it.get("tracking_em") is not None else arch_prof["tracking_em"])
                d_wt = int(it.get("display_weight") or arch_prof["display_weight"])

                dq = str(it.get("envato_display_query") or ("editorial serif" if disp_gf["category"] == "serif" else "swiss grotesk"))
                dcat = "serif" if disp_gf["category"] == "serif" else "sans-serif"
                aq = str(it.get("envato_accent_query") or "minimalist architectural sans")
                prim = self._search_live_envato_fonts(dq, dcat, disp_gf["category"], seed_offset=idx_s) or self._get_fallback_envato_font("bagina_editorial" if disp_gf["category"] == "serif" else "arteon_arch")
                acc = self._search_live_envato_fonts(aq, "sans-serif", "display", seed_offset=idx_s + 3) or self._get_fallback_envato_font("xenon_nue")
                rationale = str(it.get("rationale") or f"Contraste anatómico {disp_gf['family']} + {body_gf['family']} (escala {scale_r:.3f}, medida 60-72ch).")
                ecosystems.append(self._pack_ecosystem(eid, ename, f"Art Direction Spec · {style_profile}", rationale, disp_gf, body_gf, italic_gf, prim, acc, scale_r, track_em, d_wt))
            return ecosystems

        # Chart-Aware Oráculo OR Clean Structural Fallback Mode
        has_orac = bool(params.get("has_oraculo"))
        mc_mod = ZODIAC_MODALITIES.get(params.get("mc_sign") or "", "Fixed")
        sid_mod = ZODIAC_MODALITIES.get(params.get("sidereal_mc_sign") or "", mc_mod)
        dm = str(params.get("day_master") or "")
        shadbala = str(params.get("shadbala_dominant") or "Sun")
        nak = str(params.get("nakshatra") or "")
        dom_el = str(params.get("dominant_element") or ZODIAC_ELEMENTS.get(params.get("sun_sign") or "", "") or "")

        if has_orac:
            r_mc = MODALITY_SCALE_RATIOS.get(mc_mod, 1.333)
            r_sid = MODALITY_SCALE_RATIOS.get(sid_mod, 1.333)
            scale_r = round((r_mc + r_sid) * 0.5, 3) if r_mc != r_sid else r_mc
            if abs(scale_r - 1.292) < 0.02:
                scale_r = 1.333
            is_yang_axis = (dm in _BAZI_YANG_STEMS) or (shadbala in ("Sun", "Mars", "Saturn"))
            track_em = -0.024 if is_yang_axis else -0.016
            d_wt = 700 if is_yang_axis else 600
            nak_craft = _NAKSHATRA_CRAFT.get(nak, "humanist_editorial")
            orac_label = " · ".join([x for x in (
                f"MC {params.get('mc_sign')}/{params.get('sidereal_mc_sign')}" if params.get("mc_sign") else "",
                f"Nakshatra {nak}" if nak else "",
                f"DM {dm}" if dm else "",
                f"Shadbala {shadbala}" if shadbala else "",
            ) if x]) or "Síntesis Oráculo"
        else:
            scale_r = arch_prof["scale_ratio"]
            track_em = arch_prof["tracking_em"]
            d_wt = arch_prof["display_weight"]
            nak_craft = "humanist_editorial"
            orac_label = ""

        if has_orac and nak_craft == "sculptural_precision":
            specs = [
                ("eco-1", "Joyería Editorial & Precisión Arquitectónica", "architectural serif", "serif", "serif", "commune_inktrap_serif", "swiss grotesk", "sans-serif", "display", "xenon_nue",
                 ["source_serif_4", "bodoni_moda", "literata", "eb_garamond"], ["hanken_grotesk", "schibsted_grotesk", "albert_sans", "onest"]),
                ("eco-2", "Geometría Inktrap & Sistemas", "inktrap sans", "sans-serif", "sans", "elvon_grotesk", "modern sans", "sans-serif", "display", "grift_sans",
                 ["bricolage_grotesque", "host_grotesk", "archivo", "sora"], ["schibsted_grotesk", "familjen_grotesk", "albert_sans", "manrope"]),
                ("eco-3", "Monolito Didone Contemporáneo", "didone display", "serif", "serif", "taillevere_didone", "minimalist sans", "sans-serif", "display", "centure_grotesk",
                 ["bodoni_moda", "brygada_1918", "spectral", "piazzolla"], ["albert_sans", "public_sans", "work_sans", "golos_text"]),
            ]
        elif has_orac and (nak_craft == "incisive_authority" or dom_el in ("Fire", "Metal")):
            specs = [
                ("eco-1", "Autoridad Incisiva & Contraste Alto", "bold editorial sans", "sans-serif", "sans", "monstral_display", "swiss grotesk", "sans-serif", "display", "arteon_arch",
                 ["archivo", "bricolage_grotesque", "unbounded", "red_hat_display"], ["schibsted_grotesk", "public_sans", "hanken_grotesk", "work_sans"]),
                ("eco-2", "Tinta Editorial de Imprenta", "high contrast serif", "serif", "serif", "vitrenuit_didone", "grotesk sans", "sans-serif", "display", "nority_inktrap",
                 ["bodoni_moda", "bitter", "source_serif_4", "spectral"], ["onest", "albert_sans", "figtree", "golos_text"]),
                ("eco-3", "Humanismo Estructural Contenido", "editorial serif", "serif", "serif", "fegon_serif", "minimal sans", "sans-serif", "display", "helvena_grotesk",
                 ["literata", "brygada_1918", "eb_garamond", "piazzolla"], ["familjen_grotesk", "manrope", "work_sans", "hanken_grotesk"]),
            ]
        else:
            specs = [
                ("eco-1", "Contraste Editorial Serif + Humanista", "editorial serif", "serif", "serif", "korolis_serif", "swiss grotesk", "sans-serif", "display", "xenon_nue",
                 ["source_serif_4", "literata", "brygada_1918", "eb_garamond"], ["hanken_grotesk", "albert_sans", "work_sans", "onest"]),
                ("eco-2", "Arquitectura Grotesca Suiza", "swiss grotesk", "sans-serif", "sans", "arteon_arch", "minimal sans", "sans-serif", "display", "nority_inktrap",
                 ["bricolage_grotesque", "archivo", "red_hat_display", "host_grotesk"], ["schibsted_grotesk", "familjen_grotesk", "figtree", "manrope"]),
                ("eco-3", "Alta Autoridad Didone / Escultural", "didone", "serif", "serif", "maire_editorial", "editorial sans", "sans-serif", "display", "helvena_grotesk",
                 ["bodoni_moda", "spectral", "piazzolla", "bitter"], ["public_sans", "golos_text", "albert_sans", "hanken_grotesk"]),
            ]
            if style_profile in ("architectural_b2b", "fintech_clinical", "design_system_atelier"):
                specs = [specs[1], specs[0], specs[2]]

        if has_orac and (sid_mod == "Fixed" or dom_el in ("Earth", "Water")) and nak_craft == "humanist_editorial":
            specs = [specs[0], specs[2], specs[1]]

        ecosystems = []
        for idx_s, (eid, ename, eq1, c1, l1, fb1, eq2, c2, l2, fb2, disp_pool, body_pool) in enumerate(specs):
            prim = self._search_live_envato_fonts(eq1, c1, l1, seed_offset=eff_seed + idx_s) or self._get_fallback_envato_font(fb1)
            acc = self._search_live_envato_fonts(eq2, c2, l2, seed_offset=eff_seed + idx_s + 2) or self._get_fallback_envato_font(fb2)
            disp_gf = self._pick_google_font(disp_pool, used_web_run, offset=eff_seed + idx_s)
            body_gf = self._pick_google_font(body_pool, used_web_run, offset=eff_seed + idx_s, category_filter="sans")
            italic_gf = disp_gf if disp_gf["category"] == "serif" else self._pick_google_font(["source_serif_4", "eb_garamond", "literata"], set(), offset=idx_s)
            if has_orac:
                arch_desc = f"Oráculo ({orac_label})"
                rat = f"Derivado de {orac_label} (polaridad {mc_mod}/{sid_mod}, escala {scale_r:.3f}, peso {d_wt}, tracking {track_em:+.3f}em). Display web {disp_gf['family']} + cuerpo {body_gf['family']}; Envato ({prim['family']}) como mejora opcional."
            else:
                arch_desc = f"Perfil {style_profile}"
                rat = f"Display web auto-hospedado {disp_gf['family']} + cuerpo {body_gf['family']} (escala {scale_r:.3f}, medida 60-72ch). Envato ({prim['family']}) reservada como mejora opcional si existe .woff2 local."
            ecosystems.append(self._pack_ecosystem(eid, ename, arch_desc, rat, disp_gf, body_gf, italic_gf, prim, acc, scale_r, track_em, d_wt))
        return ecosystems

    def _build_astro_web_ready(self, disp_gf: Dict[str, Any], body_gf: Dict[str, Any], mono_gf: Optional[Dict[str, Any]], selected_eco: Dict[str, Any], arch: str) -> Dict[str, Any]:
        entries = []
        for role_var, gf in (("--font-display", disp_gf), ("--font-body", body_gf)):
            entries.append({"provider": "fontProviders.fontsource()", "name": gf["family"], "cssVariable": role_var, "weights": [f"{gf['weights'][0]} {gf['weights'][-1]}"], "styles": ["normal", "italic"], "optimizedFallbacks": True})
        if mono_gf:
            entries.append({"provider": "fontProviders.fontsource()", "name": mono_gf["family"], "cssVariable": "--font-mono", "weights": [f"{mono_gf['weights'][0]} {mono_gf['weights'][-1]}"], "styles": ["normal"], "optimizedFallbacks": True})

        entry_lines = [f'    {{ provider: fontProviders.fontsource(), name: "{e["name"]}", cssVariable: "{e["cssVariable"]}", weights: {json.dumps(e["weights"])}, styles: {json.dumps(e["styles"])}, optimizedFallbacks: true }},' for e in entries]
        astro_cfg = (
            "// astro.config.mjs (Astro 2026 Native Fonts API — self-hosted WOFF2 at build time, zero Google CDN)\n"
            "import { defineConfig, fontProviders } from \"astro/config\";\n"
            "export default defineConfig({\n"
            "  fonts: [\n"
            + "\n".join(entry_lines) + "\n"
            "    // Optional .woff2 local upgrade (Context7 verified schema):\n"
            "    // { provider: fontProviders.local(), name: \"CustomDisplay\", cssVariable: \"--font-display\", options: { variants: [{ weight: \"400 800\", style: \"normal\", src: [\"./src/assets/fonts/display.woff2\"] }] } }\n"
            "  ],\n});"
        )
        d_cls, b_cls = disp_gf["cls"], body_gf["cls"]
        d_gen = "serif" if disp_gf["category"] == "serif" else "sans-serif"
        mono_css = f'\n  --font-mono: "{mono_gf["family"]}", ui-monospace, monospace;' if mono_gf else ""
        css_sys = (
            f"/* PB19 Typography System — Profile: {arch} | Scale: {selected_eco.get('scale_ratio', 1.333):.3f} | CLS=0 Dual Fallbacks */\n"
            f"@font-face {{\n  font-family: \"{disp_gf['family']} Fallback\";\n  src: local(\"{d_cls['fallback']}\");\n  size-adjust: {d_cls['size_adjust']};\n  ascent-override: {d_cls['ascent']};\n  descent-override: {d_cls['descent']};\n  line-gap-override: {d_cls['line_gap']};\n}}\n"
            f"@font-face {{\n  font-family: \"{body_gf['family']} Fallback\";\n  src: local(\"{b_cls['fallback']}\");\n  size-adjust: {b_cls['size_adjust']};\n  ascent-override: {b_cls['ascent']};\n  descent-override: {b_cls['descent']};\n  line-gap-override: {b_cls['line_gap']};\n}}\n"
            f":root {{\n  --font-display: \"{disp_gf['family']}\", \"{disp_gf['family']} Fallback\", {d_gen};\n  --font-body: \"{body_gf['family']}\", \"{body_gf['family']} Fallback\", system-ui, sans-serif;{mono_css}\n  --type-scale-ratio: {selected_eco.get('scale_ratio', 1.333):.3f};\n  --measure-prose: 66ch;\n}}\n"
            "body { font-family: var(--font-body); font-size: 1rem; line-height: 1.60; font-optical-sizing: auto; font-size-adjust: from-font; }\n"
            f"h1, .display-xl {{ font-family: var(--font-display); font-size: clamp(2.5rem, 1.85rem + 3.2vw, 4.5rem); line-height: 1.08; letter-spacing: {selected_eco['workbench_presets']['letter_spacing_em']:+.3f}em; text-wrap: balance; font-optical-sizing: auto; }}\n"
            "h2, h3 { font-family: var(--font-display); text-wrap: balance; line-height: 1.18; }\n"
            ".prose, article p { max-inline-size: var(--measure-prose); }\n"
            ".metric, .tabular-nums, td[data-numeric] { font-variant-numeric: tabular-nums; }\n"
            "@supports not (font-size-adjust: from-font) { body { line-height: 1.62; } }"
        )
        return {"astro_fonts_entries": entries, "astro_fonts_config": astro_cfg, "css_typography_system": css_sys}

    def generate_manifest(self, selected_eco_id: str = "eco-1") -> Dict[str, Any]:
        params = self.resolve_inputs()
        resolved_spec = self.spec_path if (self.spec_path and self.spec_path.is_file()) else (self.output_dir / "font_spec.json" if (self.output_dir and (self.output_dir / "font_spec.json").is_file()) else None)
        ecosystems = self.build_ecosystems(params, resolved_spec=resolved_spec)
        selected = next((e for e in ecosystems if e["id"] == selected_eco_id), ecosystems[0])
        arch = params.get("style_profile") or "editorial_brand"
        arch_prof = STYLE_SCALE_DEFAULTS.get(arch, STYLE_SCALE_DEFAULTS["editorial_brand"])
        needs_mono = self.include_mono if self.include_mono is not None else arch_prof["needs_mono"]

        disp_gf = selected["web_fallback_display"]
        italic_gf = selected["web_editorial_italic"]
        body_tok = selected["tokens"]["ui_secondary"]
        body_gf = _resolve_web_font(body_tok["$value"], "hanken_grotesk")
        mono_gf = GOOGLE_FONTS_CATALOG[arch_prof.get("mono_key", "jetbrains_mono")] if needs_mono else None
        fontsource_pkgs = list(dict.fromkeys([p for p in (disp_gf["fontsource_pkg"], body_gf["fontsource_pkg"], mono_gf["fontsource_pkg"] if mono_gf else "") if p]))
        vslug = params.get("vertical_slug") or self.brand_lower

        astro_web_ready = self._build_astro_web_ready(disp_gf, body_gf, mono_gf, selected, arch)
        dtcg_tokens = {
            "$schema": "https://www.designtokens.org/tr/2025.10/format/",
            "typography": {
                "h1": {"$type": "typography", "$value": {"fontFamily": [disp_gf["family"], "serif" if disp_gf["category"] == "serif" else "sans-serif"], "fontSize": "clamp(2.5rem, 1.85rem + 3.2vw, 4.5rem)", "fontWeight": 700, "lineHeight": 1.08}},
                "body": {"$type": "typography", "$value": {"fontFamily": [body_gf["family"], "system-ui", "sans-serif"], "fontSize": "1rem", "fontWeight": 400, "lineHeight": 1.60}},
                "scale_ratio": {"$type": "number", "$value": selected.get("scale_ratio", 1.333)},
            },
        }
        bf_entries = []
        for eco in ecosystems:
            wp = eco["cls_metric_overrides"]
            for rk in ("display_primary", "ui_secondary", "accent_brand"):
                tok = eco["tokens"][rk]
                bf_entries.append({
                    "ecosystem_id": eco["id"], "role": rk, "family": tok["$value"], "source": tok["source"],
                    "item_uuid": tok.get("item_uuid", ""), "url": tok["url"], "category": tok["category"],
                    "weights": tok["weights"], "variable_axes": tok.get("variable_axes", ""),
                    "cls_overrides": wp["display"] if rk == "display_primary" else wp["body"],
                    "workbench_presets": eco["workbench_presets"],
                })

        clean_ecos = [{k: v for k, v in e.items() if k not in ("web_fallback_display", "web_editorial_italic")} for e in ecosystems]
        sel_clean = next((e for e in clean_ecos if e["id"] == selected["id"]), clean_ecos[0])
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "brand": self.brand_upper,
            "vertical_slug": vslug,
            "selected_ecosystem_id": sel_clean["id"],
            "style_profile": arch,
            "has_oraculo": bool(params.get("has_oraculo", False)),
            "candidate_ecosystems": clean_ecos,
            "selected_ecosystem": sel_clean,
            "web_ready_bridge": {
                "delivery": "astro_fonts_api_or_fontsource_woff2_local",
                "display_fallback_family": disp_gf["family"],
                "display_fallback_pkg": disp_gf["fontsource_pkg"],
                "display_fallback_v2_url": disp_gf["google_fonts_v2_url"],
                "body_family": body_gf["family"],
                "body_pkg": body_gf["fontsource_pkg"],
                "body_v2_url": body_gf["google_fonts_v2_url"],
                "editorial_italic_family": italic_gf["family"],
                "editorial_italic_pkg": italic_gf["fontsource_pkg"],
                "mono_family": mono_gf["family"] if mono_gf else "",
                "mono_pkg": mono_gf["fontsource_pkg"] if mono_gf else "",
                "fontsource_packages": fontsource_pkgs,
                "envato_asset_policy": "optional_upgrade_only_when_woff2_present",
                "anti_slop_bans_enforced": sorted(BANNED_OVERUSED_FAMILIES),
                "envato_upgrade_targets": {
                    "display_primary": sel_clean["tokens"]["display_primary"]["$value"],
                    "display_url": sel_clean["tokens"]["display_primary"]["url"],
                    "accent_brand": sel_clean["tokens"]["accent_brand"]["$value"],
                    "accent_url": sel_clean["tokens"]["accent_brand"]["url"],
                },
            },
            "astro_web_ready": astro_web_ready,
            "dtcg_tokens": dtcg_tokens,
            "brandfont_export": {"brand": self.brand_upper, "vertical_slug": vslug, "catalog_entries": bf_entries},
            "inheritance": {"logo": sel_clean["layers"]["logo"], "slogan": sel_clean["layers"]["slogan"], "h1": sel_clean["layers"]["h1"], "h2": sel_clean["layers"]["h2"], "body": sel_clean["layers"]["body"], "ui": sel_clean["layers"]["ui"], "ui_buttons": sel_clean["layers"]["ui"]},
            "metadata": {
                "generator": "fontgen_engine.py v7.0 (Art-Direction-First + Zero Oráculo Leak + Astro 2026 Fonts API)",
                "spec_used": str(resolved_spec.name) if resolved_spec else "",
                "sort_mode": self.sort_mode,
                "effective_seed": self._compute_effective_seed(params),
                "excluded_sibling_fonts": sorted(self.excluded_envato_families | self.excluded_google_families),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "inputs_used": params,
            },
        }

    def generate_markdown_sheet(self, manifest: Dict[str, Any]) -> str:
        target = f"{self.brand_upper} / {manifest.get('vertical_slug', '')}"
        md = [f"# Dirección de Arte Tipográfica: {target}", f"> **Perfil:** `{manifest.get('style_profile')}` · **Has Oráculo:** `{manifest.get('has_oraculo')}` · Astro Native Fonts API WOFF2 + CLS=0", "", "---", ""]
        for i, eco in enumerate(manifest.get("candidate_ecosystems", []), 1):
            t, p, wp = eco["tokens"], eco["cls_metric_overrides"], eco.get("web_pair", {})
            md.extend([
                f"### Ecosistema {i}: {eco['name']} ({eco['id']})",
                f"- **Justificación Gestalt:** {eco['rationale']}",
                f"1. **Display Web (`astro-web` WOFF2):** `{wp.get('display_family')}` (Escala `{eco.get('scale_ratio', 1.333):.3f}`)",
                f"2. **Cuerpo & UI (`astro-web` WOFF2):** `{t['ui_secondary']['$value']}` (Medida `60–72ch`)",
                f"3. **Mejora Opcional Envato (`.woff2` local):** `{t['display_primary']['$value']}` / `{t['accent_brand']['$value']}` — [Envato]({t['display_primary']['url']})",
                f"- **Anti-CLS:** `fallback`: `{p.get('fallback_font')}`, `size_adjust`: `{p.get('size_adjust')}`",
                "", "---", "",
            ])
        return "\n".join(md)

    def run(self, selected_eco_id: str = "eco-1", dry_run: bool = False) -> Tuple[Dict[str, Any], str]:
        manifest = self.generate_manifest(selected_eco_id=selected_eco_id)
        md = self.generate_markdown_sheet(manifest)
        if dry_run:
            return manifest, md
        out_dir = (self.output_dir or Path.cwd()).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "font_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (out_dir / f"fontgen_{(manifest.get('vertical_slug') or self.brand_lower).lower()}.md").write_text(md, encoding="utf-8")
        return manifest, md


def run_unit_tests() -> int:
    print("Running fontgen_engine v7.0 clean-slate unit tests...")
    assert normalize_zodiac_sign("Géminis") == "Gemini"
    ef = FontgenEngine("TEST", use_live_search=False)
    for bad in ("Astra Neo Futuristic Font", "Cyberpunk Techno Display", "Logo For Elegant Branding", "Wedding Calligraphy Script"):
        assert ef._is_noisy_title(bad) is True, f"Expected noisy reject for: {bad}"
    assert ef._score_candidate("Nority - Editorial Sans", False, True, "popular", "sans") > ef._score_candidate("Some Weird Long Name For Branding Design", True, True, "latest", "sans")

    with tempfile.TemporaryDirectory(prefix="fontgen_v70_test_") as tmp:
        tp = Path(tmp)
        bb_client = tp / "brandnoor_vertical.json"
        bb_client.write_text(json.dumps({"vertical_slug": "brand-noor", "display_name": "Consultoría Estratégica de Marca"}), encoding="utf-8")
        # CRITICAL: Running without --shards/--brief MUST keep has_oraculo=False (zero silent DIAG crawl!)
        m_noor, _ = FontgenEngine("BRANDNOOR", brand_brief_path=bb_client, output_dir=tp / "noor", use_live_search=False).run()
        assert m_noor["has_oraculo"] is False, "Silent Oráculo filesystem leak!"

        spec_p = tp / "font_spec.json"
        spec_p.write_text(json.dumps({
            "ecosystems": [
                {"id": "eco-1", "name": "Editorial Serif + Humanista", "display_web": "Source Serif 4", "body_web": "Hanken Grotesk", "scale_ratio": 1.333},
                {"id": "eco-2", "name": "Expresiva Grotesca", "display_web": "Bricolage Grotesque", "body_web": "Schibsted Grotesk", "scale_ratio": 1.250},
                {"id": "eco-3", "name": "Autoridad Didone", "display_web": "Bodoni Moda", "body_web": "Albert Sans", "scale_ratio": 1.500},
            ]
        }), encoding="utf-8")
        m_spec, _ = FontgenEngine("CLIENTX", brand_brief_path=bb_client, spec_path=spec_p, output_dir=tp / "spec_out", use_live_search=False).run()
        assert m_spec["has_oraculo"] is False
        assert m_spec["web_ready_bridge"]["display_fallback_family"] == "Source Serif 4"
        assert m_spec["web_ready_bridge"]["body_family"] == "Hanken Grotesk"
        assert "options: { variants:" in m_spec["astro_web_ready"]["astro_fonts_config"]
        assert m_spec["candidate_ecosystems"][0]["web_pair"]["display_family"] == "Source Serif 4"

        # Sibling isolation test
        ws = tp / "workspaces"
        v_a, v_b = tp / "a.json", tp / "b.json"
        v_a.write_text(json.dumps({"vertical_slug": "alpha-b2b", "display_name": "Alpha B2B Consultoría"}), encoding="utf-8")
        v_b.write_text(json.dumps({"vertical_slug": "beta-b2b", "display_name": "Beta B2B Consultoría"}), encoding="utf-8")
        m_a, _ = FontgenEngine("CO", vertical_json_path=v_a, output_dir=ws / "alpha-b2b" / "brand", use_live_search=False).run()
        m_b, _ = FontgenEngine("CO", vertical_json_path=v_b, output_dir=ws / "beta-b2b" / "brand", use_live_search=False).run()
        a_env = {t["$value"].lower() for e in m_a["candidate_ecosystems"] for rk, t in e["tokens"].items() if rk in ("display_primary", "accent_brand")}
        b_env = {t["$value"].lower() for e in m_b["candidate_ecosystems"] for rk, t in e["tokens"].items() if rk in ("display_primary", "accent_brand")}
        assert a_env.isdisjoint(b_env), f"Sibling Envato overlap: {a_env & b_env}"
        for m in (m_noor, m_spec, m_a, m_b):
            assert m["web_ready_bridge"]["display_fallback_family"].lower() not in BANNED_OVERUSED_FAMILIES
            assert m["web_ready_bridge"]["body_family"].lower() not in BANNED_OVERUSED_FAMILIES
            assert len(m["web_ready_bridge"]["fontsource_packages"]) >= 2

        # Strict Oráculo brief parser (must NOT capture prose words like 'Como') & chart differentiation
        brief_md = tp / "astro_test.md"
        brief_md.write_text(
            "| **Sol Natal** | **Gemini 19.01°** | **Taurus 24.45°** |\n"
            "| **Medio Cielo** | **Gemini 16.57°** | **Taurus 22.01°** |\n"
            "El Medio Cielo actúa como faro público.\n"
            "**Nakshatra:** Chitra Pada 4\n"
            "**Day Master:** Jia\n"
            "- **Elemento dominante:** Aire\n"
            "### 5.1 Dominante Shadbala: Sol\n",
            encoding="utf-8",
        )
        m_br, _ = FontgenEngine("TESTBR", brief_path=brief_md, output_dir=tp / "br", use_live_search=False).run()
        br_inp = m_br["metadata"]["inputs_used"]
        assert br_inp["mc_sign"] == "Gemini", f"Unexpected mc_sign: {br_inp['mc_sign']}"
        assert br_inp["sidereal_mc_sign"] == "Taurus"
        assert br_inp["nakshatra"] == "Chitra" and br_inp["day_master"] == "Jia" and br_inp["shadbala_dominant"] == "Sun"
        m_fire, _ = FontgenEngine("TESTFR", override_params={"sun_sign": "Leo", "mc_sign": "Aries", "sidereal_mc_sign": "Pisces", "nakshatra": "Ashwini", "day_master": "Geng", "dominant_element": "Fire", "shadbala_dominant": "Mars"}, output_dir=tp / "fr", use_live_search=False).run()
        assert m_br["selected_ecosystem"]["tokens"]["display_primary"]["$value"] != m_fire["selected_ecosystem"]["tokens"]["display_primary"]["$value"] or m_br["web_ready_bridge"]["display_fallback_family"] != m_fire["web_ready_bridge"]["display_fallback_family"]
    print("✅ FONTGEN ENGINE v7.0 UNIT TESTS PASSED (Zero silent Oráculo leak, chart-driven Oráculo, Context7 Astro, 0 slop)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fontgen Engine v7.0 — Art-Direction-First & Astro 2026 Fonts Compiler")
    parser.add_argument("--brand", default="BRAND")
    parser.add_argument("--spec", type=Path, default=None, help="Explicit Art-Direction font_spec.json")
    parser.add_argument("--shards", type=Path, default=None)
    parser.add_argument("--brief", type=Path, default=None)
    parser.add_argument("--brand-brief", type=Path, default=None)
    parser.add_argument("--vertical-json", type=Path, default=None)
    parser.add_argument("--style-profile", default="auto")
    parser.add_argument("--sort", default="hybrid", choices=["hybrid", "latest", "popular"])
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sibling-workspaces-dir", type=Path, default=None)
    parser.add_argument("--exclude-fonts", default="")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--eco", default="eco-1", choices=["eco-1", "eco-2", "eco-3"])
    parser.add_argument("--include-mono", action="store_true")
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

    ov = {k: v for k, v in {"sun_sign": args.sun_sign, "mc_sign": args.mc_sign, "day_master": args.day_master, "nakshatra": args.nakshatra, "dominant_element": args.dominant_element}.items() if v}
    excl = [x.strip() for x in args.exclude_fonts.split(",") if x.strip()] if args.exclude_fonts else None
    eng = FontgenEngine(
        brand=args.brand, shards_path=args.shards, brief_path=args.brief, brand_brief_path=args.brand_brief,
        vertical_json_path=args.vertical_json, output_dir=args.output_dir, use_live_search=not args.no_live,
        allow_default=args.allow_default, override_params=ov or None, create_brand_dirs=args.create_brand_dirs,
        style_profile=args.style_profile, sort_mode=args.sort, seed=args.seed, sibling_workspaces_dir=args.sibling_workspaces_dir,
        exclude_fonts=excl, include_mono=True if args.include_mono else None, spec_path=args.spec,
    )
    manifest, _ = eng.run(selected_eco_id=args.eco, dry_run=args.dry_run)
    if args.dry_run:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0
    sel = manifest["selected_ecosystem"]
    print(f"✅ FONTGEN ENGINE v7.0 COMPLETED FOR: {manifest['brand']}/{manifest['vertical_slug']} ({manifest['selected_ecosystem_id']}, has_oraculo={manifest['has_oraculo']}, web={sel['web_pair']['display_family']} + {sel['web_pair']['body_family']})")
    print(f"  • Envato Display: {sel['tokens']['display_primary']['$value']} ({sel['tokens']['display_primary']['url']})")
    print(f"  • Envato Accent:  {sel['tokens']['accent_brand']['$value']} ({sel['tokens']['accent_brand']['url']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
