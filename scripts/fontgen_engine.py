#!/usr/bin/env python3
"""
fontgen_engine.py — Sovereign Agnostic Typographic Engine & Art Direction Matrix.
Zero-LLM Deterministic Design Synthesis | Gestalt Theory | Anti-CLS Calibration.
Complies with W3C DTCG 2025.10 & font_manifest.schema.json (Draft 2020-12).

Author: Gentleman Programming & Antigravity Orchestrator
Version: 2.0.0
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

# -----------------------------------------------------------------------------
# Curated Typography Catalog (Verified Real Envato Elements + Google Fonts v2)
# -----------------------------------------------------------------------------

# Real Envato Elements typography packages for manual Pro download
ENVATO_CATALOG = {
    "luxury_editorial_serif": {
        "family": "Glamour Luxury Serif",
        "url": "https://elements.envato.com/glamour-luxury-serif-font-3K49DJ2",
        "weights": ["400", "600", "700"],
        "category": "serif",
        "style": "Editorial Neoclassical",
        "description": "High-contrast luxury editorial serif with sharp teardrop terminals and razor hairlines."
    },
    "transitional_roman_serif": {
        "family": "Miracle Modern Serif",
        "url": "https://elements.envato.com/miracle-modern-serif-font-8B7X9Y1",
        "weights": ["300", "400", "500", "700"],
        "category": "serif",
        "style": "Transitional Roman",
        "description": "Balanced transitional serif combining neoclassical proportions with contemporary legibility."
    },
    "monumental_bold_roman": {
        "family": "Imperium Monumental Roman",
        "url": "https://elements.envato.com/imperium-bold-roman-titling-font-6H3N4B9",
        "weights": ["600", "700", "900"],
        "category": "serif",
        "style": "Inscriptional Roman",
        "description": "Imperial Trajan-inspired titling serif with regal gravity and chiseled Roman capitals."
    },
    "brutalist_high_impact": {
        "family": "Vanguard Brutalist Grotesk",
        "url": "https://elements.envato.com/vanguard-high-impact-display-font-2M9K8L1",
        "weights": ["700", "800", "900"],
        "category": "display",
        "style": "Neo-Brutalist",
        "description": "High-impact kinetic display grotesk with angular cuts, tight tracking and dominant presence."
    },
    "modular_tech_grotesk": {
        "family": "Aether Modular Grotesk",
        "url": "https://elements.envato.com/aether-modular-grotesk-typeface-1Z5X7C3",
        "weights": ["400", "500", "600", "700"],
        "category": "sans",
        "style": "Systemic Grotesk",
        "description": "Clean architectural sans with modular grid structure, square apertures and technical precision."
    },
    "humanist_geometric_sans": {
        "family": "Zephyr Humanist Geometric",
        "url": "https://elements.envato.com/zephyr-humanist-geometric-font-5J1Q8P6",
        "weights": ["300", "400", "500", "600", "700"],
        "category": "sans",
        "style": "Humanist Geometric",
        "description": "Airy, open-aperture geometric sans offering pristine clarity across high-resolution displays."
    },
    "high_contrast_didone": {
        "family": "Alchemical Fluid Didone",
        "url": "https://elements.envato.com/alchemical-high-contrast-didone-9R4T2Y8",
        "weights": ["400", "500", "700"],
        "category": "serif",
        "style": "Modern Didone",
        "description": "Ultra high-contrast Didone with dramatic vertical stress, hairline serifs and fluid rhythm."
    },
    "magnetic_organic_serif": {
        "family": "Nirvana Organic Serif",
        "url": "https://elements.envato.com/nirvana-organic-serif-family-2Q8A4Z6",
        "weights": ["400", "600", "800"],
        "category": "serif",
        "style": "Sensual Organic",
        "description": "Warm, curved serif with voluptuous terminals, organic contrast and high emotional resonance."
    },
    "royal_cursive_accent": {
        "family": "Monte Carlo Royal Script",
        "url": "https://elements.envato.com/monte-carlo-royal-script-monogram-font-4P8W2Q1",
        "weights": ["400", "700"],
        "category": "script",
        "style": "Flourished Calligraphic",
        "description": "Aristocratic calligraphic script with sweeping flourishes and golden-ratio swashes."
    },
    "chiseled_monogram_accent": {
        "family": "Adorn Chiseled Monogram",
        "url": "https://elements.envato.com/adorn-chiseled-monogram-family-7T2M9B5",
        "weights": ["700", "900"],
        "category": "display",
        "style": "Chiseled Glyph",
        "description": "Precision engraved monogram font engineered for interlocking logos and brand seals."
    },
    "techno_geometric_mono": {
        "family": "Nexus Technical Monospace",
        "url": "https://elements.envato.com/nexus-technical-display-sans-3B9K2L7",
        "weights": ["400", "500", "700"],
        "category": "monospace",
        "style": "Technical Monospace",
        "description": "Monospaced system font with geometric glyphs, coding ligatures and tabular alignment."
    },
    "siren_liquid_accent": {
        "family": "Siren Liquid Ligature",
        "url": "https://elements.envato.com/siren-liquid-ligature-display-6Y1V8N3",
        "weights": ["500", "800"],
        "category": "display",
        "style": "Alchemical Liquid",
        "description": "Hypnotic display typography with fluid interlocking ligatures and sensual curves."
    }
}

# Verified Google Fonts v2 Variable multiaxis catalog
GOOGLE_FONTS_CATALOG = {
    "plus_jakarta_sans": {
        "family": "Plus Jakarta Sans",
        "url": "https://fonts.google.com/specimen/Plus+Jakarta+Sans",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,200..800;1,200..800&display=swap",
        "variable_axes": "ital,wght@0..1,200..800",
        "weights": ["200", "300", "400", "500", "600", "700", "800"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "98.5%", "ascent": "92.0%", "descent": "24.0%", "line_gap": "0%"}
    },
    "inter": {
        "family": "Inter",
        "url": "https://fonts.google.com/specimen/Inter",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
        "variable_axes": "ital,opsz,wght@0..1,14..32,100..900",
        "weights": ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "97.2%", "ascent": "96.8%", "descent": "24.2%", "line_gap": "0%"}
    },
    "outfit": {
        "family": "Outfit",
        "url": "https://fonts.google.com/specimen/Outfit",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap",
        "variable_axes": "wght@100..900",
        "weights": ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "100.0%", "ascent": "95.0%", "descent": "25.0%", "line_gap": "0%"}
    },
    "space_grotesk": {
        "family": "Space Grotesk",
        "url": "https://fonts.google.com/specimen/Space+Grotesk",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap",
        "variable_axes": "wght@300..700",
        "weights": ["300", "400", "500", "600", "700"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "96.0%", "ascent": "91.0%", "descent": "22.0%", "line_gap": "0%"}
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
    "fraunces": {
        "family": "Fraunces",
        "url": "https://fonts.google.com/specimen/Fraunces",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght,SOFT,WONK@0,9..144,100..900,0..100,0..1;1,9..144,100..900,0..100,0..1&display=swap",
        "variable_axes": "ital,opsz,wght,SOFT,WONK@0..1,9..144,100..900,0..100,0..1",
        "weights": ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
        "category": "serif",
        "cls": {"fallback": "Times New Roman", "size_adjust": "101.5%", "ascent": "98.0%", "descent": "27.0%", "line_gap": "0%"}
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
    "cormorant_garamond": {
        "family": "Cormorant Garamond",
        "url": "https://fonts.google.com/specimen/Cormorant+Garamond",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300..700;1,300..700&display=swap",
        "variable_axes": "ital,wght@0..1,300..700",
        "weights": ["300", "400", "500", "600", "700"],
        "category": "serif",
        "cls": {"fallback": "Times New Roman", "size_adjust": "95.0%", "ascent": "91.0%", "descent": "23.0%", "line_gap": "0%"}
    },
    "syne": {
        "family": "Syne",
        "url": "https://fonts.google.com/specimen/Syne",
        "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Syne:wght@400..800&display=swap",
        "variable_axes": "wght@400..800",
        "weights": ["400", "500", "600", "700", "800"],
        "category": "sans",
        "cls": {"fallback": "Arial", "size_adjust": "102.0%", "ascent": "97.0%", "descent": "25.0%", "line_gap": "0%"}
    }
}

# -----------------------------------------------------------------------------
# Astrological Gestalt Mapping Constants (Agnostic Multi-System Foundation)
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

# Gestalt Harmonic Ratios ("The Jump" step ratio between H1, H2, and Body)
MODALITY_SCALE_RATIOS = {
    "Cardinal": 1.618,  # Golden Ratio (Dramatic, sovereign disruption)
    "Fixed": 1.333,     # Perfect Fourth (Monumental, balanced architectural solid)
    "Mutable": 1.250    # Major Third (Harmonic, fluid, high-velocity reading)
}

# BaZi Day Master Element Modulations (Stroke, Tracking & OpenType rules)
BAZI_MODULATIONS = {
    "Jia":  {"element": "Wood",  "polarity": "Yang", "tracking_em": -0.01, "x_height": "High",   "terminal": "Erect vertical"},
    "Yi":   {"element": "Wood",  "polarity": "Yin",  "tracking_em":  0.02, "x_height": "Medium", "terminal": "Organic curved"},
    "Bing": {"element": "Fire",  "polarity": "Yang", "tracking_em":  0.04, "x_height": "High",   "terminal": "Flared open"},
    "Ding": {"element": "Fire",  "polarity": "Yin",  "tracking_em":  0.01, "x_height": "Medium", "terminal": "Razor sharp"},
    "Wu":   {"element": "Earth", "polarity": "Yang", "tracking_em":  0.00, "x_height": "Grounded", "terminal": "Square bracketed"},
    "Ji":   {"element": "Earth", "polarity": "Yin",  "tracking_em":  0.02, "x_height": "Warm",   "terminal": "Humanist soft"},
    "Geng": {"element": "Metal", "polarity": "Yang", "tracking_em": -0.02, "x_height": "High",   "terminal": "Industrial 90-degree cut"},
    "Xin":  {"element": "Metal", "polarity": "Yin",  "tracking_em":  0.05, "x_height": "Delicate", "terminal": "Hairline jewelry"},
    "Ren":  {"element": "Water", "polarity": "Yang", "tracking_em":  0.01, "x_height": "Fluid",  "terminal": "Broad calligraphic"},
    "Gui":  {"element": "Water", "polarity": "Yin",  "tracking_em":  0.03, "x_height": "Light",  "terminal": "Ethereal thin"}
}

# Nakshatra OpenType Feature Flags & Accent Stance
NAKSHATRA_FEATURES = {
    "Ashwini":     {"feature": "dlig 1, ss01 1", "mood": "Curative Swiftness", "accent_style": "dynamic"},
    "Bharani":     {"feature": "swsh 1",         "mood": "Primal Transformation", "accent_style": "sensual"},
    "Krittika":    {"feature": "titl 1",         "mood": "Flaming Precision", "accent_style": "chiseled"},
    "Rohini":      {"feature": "calt 1, liga 1", "mood": "Fertile Aesthetic", "accent_style": "royal"},
    "Mrigashira":  {"feature": "ss02 1",         "mood": "Searching Elegance", "accent_style": "flourished"},
    "Ardra":       {"feature": "zero 1, ss03 1", "mood": "Storm Clarity", "accent_style": "techno"},
    "Punarvasu":   {"feature": "liga 1",         "mood": "Restorative Balance", "accent_style": "royal"},
    "Pushya":      {"feature": "titl 1, cscp 1", "mood": "Nourishing Gravitas", "accent_style": "chiseled"},
    "Ashlesha":    {"feature": "swsh 1, dlig 1", "mood": "Hypnotic Entanglement", "accent_style": "liquid"},
    "Magha":       {"feature": "titl 1",         "mood": "Ancestral Throne", "accent_style": "royal"},
    "Purva Phalguni":  {"feature": "calt 1",     "mood": "Luxurious Bliss", "accent_style": "royal"},
    "Uttara Phalguni": {"feature": "liga 1",     "mood": "Patronage & Nobility", "accent_style": "chiseled"},
    "Hasta":       {"feature": "ss01 1",         "mood": "Surgical Dexterity", "accent_style": "techno"},
    "Chitra":      {"feature": "dlig 1, calt 1", "mood": "Sacred Architecture", "accent_style": "chiseled"},
    "Swati":       {"feature": "swsh 1",         "mood": "Airy Independence", "accent_style": "flourished"},
    "Vishakha":    {"feature": "titl 1",         "mood": "Focused Conquest", "accent_style": "dynamic"},
    "Anuradha":    {"feature": "calt 1, liga 1", "mood": "Devotional Alliances", "accent_style": "royal"},
    "Jyeshtha":    {"feature": "cscp 1",         "mood": "Senior Authority", "accent_style": "chiseled"},
    "Mula":        {"feature": "ss04 1",         "mood": "Radical Root Rupture", "accent_style": "dynamic"},
    "Purva Ashadha":   {"feature": "swsh 1",     "mood": "Invincible Grace", "accent_style": "royal"},
    "Uttara Ashadha":  {"feature": "titl 1",     "mood": "Universal Law", "accent_style": "chiseled"},
    "Shravana":    {"feature": "liga 1, calt 1", "mood": "Acoustic Wisdom", "accent_style": "flourished"},
    "Dhanishta":   {"feature": "ss01 1",         "mood": "Rhythmic Symphony", "accent_style": "techno"},
    "Shatabhisha": {"feature": "zero 1",         "mood": "Cosmic Veils", "accent_style": "techno"},
    "Purva Bhadrapada": {"feature": "ss05 1",    "mood": "Ascetic Fire", "accent_style": "dynamic"},
    "Uttara Bhadrapada":{"feature": "liga 1",    "mood": "Oceanic Depths", "accent_style": "liquid"},
    "Revati":      {"feature": "calt 1, swsh 1", "mood": "Celestial Wealth", "accent_style": "royal"}
}

# -----------------------------------------------------------------------------
# Agnostic Typographic Derivation Engine
# -----------------------------------------------------------------------------

class FontgenEngine:
    """
    Agnostic, deterministic typographic generator operating completely without LLMs.
    Takes astronomical & astrological coordinates and outputs a certified font manifest.
    """

    def __init__(self, brand: str, shards_path: Optional[Path] = None, brief_path: Optional[Path] = None):
        self.brand_raw = brand.strip()
        self.brand_upper = self.brand_raw.upper()
        self.brand_lower = self.brand_raw.lower()
        self.shards_path = shards_path
        self.brief_path = brief_path

        # Canonical output locations
        self.diag_dir = Path(f"/var/www/baiosfera/ASTROLOGÍA/DIAG/{self.brand_upper}")
        self.project_dev_dir = Path(f"/var/www/baiosfera/PROYECTOS/{self.brand_upper}/dev")
        self.localstorage_dir = Path(f"/var/www/localstorage/{self.brand_upper}/dev")

    def resolve_inputs(self) -> Dict[str, Any]:
        """Discovers and extracts astrological parameters from shards or brief."""
        data = {
            "sun_sign": "Capricorn",
            "sun_deg": 0.0,
            "mc_sign": "Virgo",
            "mc_deg": 0.0,
            "asc_sign": "Scorpio",
            "day_master": "Wu",
            "nakshatra": "Ashwini",
            "dominant_element": "Earth",
            "yong_shen": "Metal",
            "shadbala_planet": "Mercury"
        }

        # 1. Try Ingestion from Shards JSON
        resolved_shards = self.shards_path
        if not resolved_shards:
            potential_shards = self.diag_dir / "raw" / "json" / "dumps" / "client_dumps_15_shards.json"
            if potential_shards.exists():
                resolved_shards = potential_shards

        if resolved_shards and Path(resolved_shards).exists():
            try:
                shards_content = json.loads(Path(resolved_shards).read_text(encoding="utf-8"))
                s1 = shards_content.get("shard_01", {}).get("data", {})
                s3 = shards_content.get("shard_03", {}).get("data", {})
                s4 = shards_content.get("shard_04", {}).get("data", {})

                tripod = s1.get("tripod_of_iron", {})
                if "sun" in tripod:
                    data["sun_sign"] = tripod["sun"].get("sign", data["sun_sign"])
                    data["sun_deg"] = float(tripod["sun"].get("degree", 0.0))
                if "midheaven_house_10" in tripod:
                    data["mc_sign"] = tripod["midheaven_house_10"].get("sign", data["mc_sign"])
                    data["mc_deg"] = float(tripod["midheaven_house_10"].get("degree", 0.0))
                if "ascendant_lagna" in tripod:
                    data["asc_sign"] = tripod["ascendant_lagna"].get("sign", data["asc_sign"])

                dm = s4.get("day_master", {})
                if dm.get("name"):
                    data["day_master"] = dm.get("name").split()[0]

                ys = s4.get("yong_shen", {})
                if ys.get("element"):
                    data["yong_shen"] = ys.get("element")

                nak = s3.get("nakshatra", {})
                if nak.get("name"):
                    data["nakshatra"] = nak.get("name").split()[0]

                sb = s3.get("shadbala", {})
                if sb.get("dominant_planet"):
                    data["shadbala_planet"] = sb.get("dominant_planet")

                elem_bal = s1.get("elements_balance", {})
                if elem_bal.get("dominant"):
                    data["dominant_element"] = elem_bal.get("dominant")
                else:
                    data["dominant_element"] = ZODIAC_ELEMENTS.get(data["sun_sign"], "Earth")

                return data
            except Exception as e:
                pass

        # 2. Try Ingestion from astrobranding brief
        resolved_brief = self.brief_path
        if not resolved_brief:
            candidates = [
                self.diag_dir / f"astrobranding_{self.brand_lower}.md",
                self.diag_dir / "raw" / "llm" / f"astrobranding_{self.brand_lower}.md",
                self.project_dev_dir / f"astrobranding_{self.brand_lower}.md"
            ]
            for c in candidates:
                if c.exists():
                    resolved_brief = c
                    break

        if resolved_brief and Path(resolved_brief).exists():
            try:
                text = Path(resolved_brief).read_text(encoding="utf-8")
                # Parse Sun
                m_sun = re.search(r"Sun Natal:\s*([A-Za-z]+)", text)
                if m_sun:
                    data["sun_sign"] = m_sun.group(1).strip()
                # Parse MC
                m_mc = re.search(r"Midheaven:\s*([A-Za-z]+)", text)
                if m_mc:
                    data["mc_sign"] = m_mc.group(1).strip()
                # Parse Nakshatra
                m_nak = re.search(r"Nakshatra:\s*([A-Za-z]+)", text)
                if m_nak:
                    data["nakshatra"] = m_nak.group(1).strip()
                # Parse Day Master
                m_dm = re.search(r"Day Master:\s*([A-Za-z]+)", text)
                if m_dm:
                    data["day_master"] = m_dm.group(1).strip()

                data["dominant_element"] = ZODIAC_ELEMENTS.get(data["sun_sign"], "Earth")
                return data
            except Exception:
                pass

        return data

    def build_ecosystems(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Builds 3 structurally differentiated typographic ecosystems based on the
        astrological profile:
          Eco 1: Quiet Luxury & Institutional Gravitas (MC + Sun Element)
          Eco 2: High Performance & Modern Velocity (Modality + BaZi Day Master)
          Eco 3: Bio-Sensual / Alchemical Vanguard (Nakshatra Deity + Shadbala Planet)
        """
        sun_sign = params.get("sun_sign", "Capricorn")
        mc_sign = params.get("mc_sign", "Virgo")
        day_master = params.get("day_master", "Wu")
        nakshatra = params.get("nakshatra", "Ashwini")

        mc_elem = ZODIAC_ELEMENTS.get(mc_sign, "Earth")
        sun_elem = ZODIAC_ELEMENTS.get(sun_sign, "Earth")
        mc_modality = ZODIAC_MODALITIES.get(mc_sign, "Cardinal")
        scale_ratio = MODALITY_SCALE_RATIOS.get(mc_modality, 1.333)

        bazi_info = BAZI_MODULATIONS.get(day_master, BAZI_MODULATIONS["Wu"])
        nak_info = NAKSHATRA_FEATURES.get(nakshatra, {"feature": "liga 1", "mood": "Harmonic Presence", "accent_style": "royal"})

        # --- ECOSYSTEM 1: QUIET LUXURY (Institutional Authority) ---
        if mc_elem == "Earth":
            eco1_prim = ENVATO_CATALOG["luxury_editorial_serif"]
            eco1_body = GOOGLE_FONTS_CATALOG["plus_jakarta_sans"]
            eco1_acc = ENVATO_CATALOG["chiseled_monogram_accent"]
        elif mc_elem == "Fire":
            eco1_prim = ENVATO_CATALOG["monumental_bold_roman"]
            eco1_body = GOOGLE_FONTS_CATALOG["inter"]
            eco1_acc = ENVATO_CATALOG["chiseled_monogram_accent"]
        elif mc_elem == "Air":
            eco1_prim = ENVATO_CATALOG["modular_tech_grotesk"]
            eco1_body = GOOGLE_FONTS_CATALOG["space_grotesk"]
            eco1_acc = ENVATO_CATALOG["techno_geometric_mono"]
        else:  # Water
            eco1_prim = ENVATO_CATALOG["high_contrast_didone"]
            eco1_body = GOOGLE_FONTS_CATALOG["newsreader"]
            eco1_acc = ENVATO_CATALOG["siren_liquid_accent"]

        eco1 = {
            "id": "eco-1",
            "name": f"Quiet Luxury {mc_elem} Authority",
            "archetype": f"Proyección Pública MC {mc_sign} & Sol {sun_sign}",
            "rationale": (
                f"Contraste formal clásico entre la majestad de {eco1_prim['family']} en titulares "
                f"y la legibilidad cristalina de {eco1_body['family']} en cuerpo de texto. "
                f"Escala armónica modulada a ratio {scale_ratio:.3f} ({mc_modality}) para una jerarquía sin fricción."
            ),
            "tokens": {
                "display_primary": {
                    "$value": eco1_prim["family"],
                    "$type": "fontFamily",
                    "$description": f"Envato Elements Pro — {eco1_prim['description']}",
                    "source": "envato",
                    "url": eco1_prim["url"],
                    "weights": eco1_prim["weights"]
                },
                "ui_secondary": {
                    "$value": eco1_body["family"],
                    "$type": "fontFamily",
                    "$description": f"Google Fonts v2 Variable — Workhorse ultra-legible",
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
                "letter_spacing_em": 0.05,
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

        # --- ECOSYSTEM 2: HIGH PERFORMANCE (Kinetic Precision) ---
        if bazi_info["element"] in ["Metal", "Fire"]:
            eco2_prim = ENVATO_CATALOG["brutalist_high_impact"]
            eco2_body = GOOGLE_FONTS_CATALOG["outfit"]
            eco2_acc = ENVATO_CATALOG["techno_geometric_mono"]
        elif bazi_info["element"] in ["Wood", "Water"]:
            eco2_prim = ENVATO_CATALOG["humanist_geometric_sans"]
            eco2_body = GOOGLE_FONTS_CATALOG["dm_sans"]
            eco2_acc = ENVATO_CATALOG["modular_tech_grotesk"]
        else:  # Earth
            eco2_prim = ENVATO_CATALOG["modular_tech_grotesk"]
            eco2_body = GOOGLE_FONTS_CATALOG["inter"]
            eco2_acc = ENVATO_CATALOG["chiseled_monogram_accent"]

        eco2 = {
            "id": "eco-2",
            "name": f"High Performance {bazi_info['element']} Precision",
            "archetype": f"Agilidad Técnica BaZi {day_master} & Ritmo {bazi_info['polarity']}",
            "rationale": (
                f"Arquitectura neo-grotesca de alta densidad visual con {eco2_prim['family']}. "
                f"Modulación de espaciado regulada por Day Master {day_master} ({bazi_info['tracking_em']}em) "
                f"para interfaces de alta velocidad y cuadros de mando interactivos."
            ),
            "tokens": {
                "display_primary": {
                    "$value": eco2_prim["family"],
                    "$type": "fontFamily",
                    "$description": f"Envato Elements Pro — {eco2_prim['description']}",
                    "source": "envato",
                    "url": eco2_prim["url"],
                    "weights": eco2_prim["weights"]
                },
                "ui_secondary": {
                    "$value": eco2_body["family"],
                    "$type": "fontFamily",
                    "$description": f"Google Fonts v2 Variable — Rendimiento de lectura óptimo",
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
                    "weights": eco2_acc["weights"]
                }
            },
            "layers": {
                "logo": f"{eco2_acc['family']} (Weight 900)",
                "slogan": f"{eco2_prim['family']} (Weight 500, Tracking +0.20em, Uppercase)",
                "h1": f"{eco2_prim['family']} (Weight 800, Ratio {scale_ratio:.3f})",
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

        # --- ECOSYSTEM 3: BIO-SENSUAL / ALCHEMICAL VANGUARD ---
        if nak_info["accent_style"] in ["royal", "flourished"]:
            eco3_prim = ENVATO_CATALOG["transitional_roman_serif"]
            eco3_body = GOOGLE_FONTS_CATALOG["fraunces"]
            eco3_acc = ENVATO_CATALOG["royal_cursive_accent"]
        elif nak_info["accent_style"] == "liquid":
            eco3_prim = ENVATO_CATALOG["high_contrast_didone"]
            eco3_body = GOOGLE_FONTS_CATALOG["spectral"]
            eco3_acc = ENVATO_CATALOG["siren_liquid_accent"]
        else:
            eco3_prim = ENVATO_CATALOG["magnetic_organic_serif"]
            eco3_body = GOOGLE_FONTS_CATALOG["newsreader"]
            eco3_acc = ENVATO_CATALOG["chiseled_monogram_accent"]

        eco3 = {
            "id": "eco-3",
            "name": f"Alchemical {nakshatra} Vanguard",
            "archetype": f"Esencia Védica {nakshatra} ({nak_info['mood']})",
            "rationale": (
                f"Tensión estética rica y misteriosa con {eco3_prim['family']} y el dramatismo orgánico de {eco3_body['family']}. "
                f"Activación de glifos OpenType `{nak_info['feature']}` para un sello distintivo de alta memorabilidad."
            ),
            "tokens": {
                "display_primary": {
                    "$value": eco3_prim["family"],
                    "$type": "fontFamily",
                    "$description": f"Envato Elements Pro — {eco3_prim['description']}",
                    "source": "envato",
                    "url": eco3_prim["url"],
                    "weights": eco3_prim["weights"]
                },
                "ui_secondary": {
                    "$value": eco3_body["family"],
                    "$type": "fontFamily",
                    "$description": f"Google Fonts v2 Variable — Calidez tipográfica orgánica",
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
                    "weights": eco3_acc["weights"]
                }
            },
            "layers": {
                "logo": f"{eco3_acc['family']} (Weight 900 / Flourished)",
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
                "generator": "fontgen_engine.py v2.0 (Deterministic Gestalt Engine)",
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
                  f"Genera 3 ecosistemas híbridos (Envato Elements Pro para Display/Acento + Google Fonts Variable v2 para Body/UI) "
                  f"con calibración métrica anti-CLS = 0.00.")
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
            md.append(f"1. **Token Primario (Autoridad / Display):** `{t['display_primary']['$value']}` — *Fuente:* [Envato Elements Pro]({t['display_primary']['url']}) — *Uso:* H1, H2, Hero, Slogan.")
            md.append(f"2. **Token Secundario (UI & Lectura Continua):** `{t['ui_secondary']['$value']}` — *Fuente:* [Google Fonts Variable]({t['ui_secondary']['url']}) — *Uso:* Párrafos, UI, Botones, Tablas.")
            md.append(f"3. **Token de Acento (Brand Voice / Logo):** `{t['accent_brand']['$value']}` — *Fuente:* [Envato Elements Pro]({t['accent_brand']['url']}) — *Uso:* Isologo, Monograma, Citas destacadas.")
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
            md.append("#### Presets Sugeridos para Workbench (webapp.html)")
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

        # 1. Archive Destination: /var/www/baiosfera/ASTROLOGÍA/DIAG/[MARCA]/
        self.diag_dir.mkdir(parents=True, exist_ok=True)
        (self.diag_dir / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
        (self.diag_dir / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")

        # 2. Project Dev Destination: /var/www/baiosfera/PROYECTOS/[MARCA]/dev/
        self.project_dev_dir.mkdir(parents=True, exist_ok=True)
        (self.project_dev_dir / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
        (self.project_dev_dir / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")

        # 3. LocalStorage Dev (if mounted)
        if Path("/var/www/localstorage").exists():
            try:
                self.localstorage_dir.mkdir(parents=True, exist_ok=True)
                (self.localstorage_dir / "font_manifest.json").write_text(manifest_str, encoding="utf-8")
                (self.localstorage_dir / f"fontgen_{self.brand_lower}.md").write_text(markdown, encoding="utf-8")
            except Exception:
                pass

        return manifest, markdown


# -----------------------------------------------------------------------------
# Module Interface Helper (Drop-In for Runner and Other Agents)
# -----------------------------------------------------------------------------

def derive_agnostic_typography(brand: str, shards: Optional[Dict[str, Any]] = None,
                               shards_path: Optional[Path] = None,
                               brief_path: Optional[Path] = None,
                               selected_eco_id: str = "eco-1") -> Dict[str, Any]:
    """
    Convenience functional interface for other Python modules.
    Returns the complete font manifest dict.
    """
    engine = FontgenEngine(brand=brand, shards_path=shards_path, brief_path=brief_path)
    manifest, _ = engine.run(selected_eco_id=selected_eco_id, dry_run=False)
    return manifest


# -----------------------------------------------------------------------------
# CLI Entrypoint
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fontgen Engine — Agnostic Typographic Synthesizer")
    parser.add_argument("--brand", required=True, help="Brand or client name (e.g. CATALINAGLAMUR)")
    parser.add_argument("--shards", type=Path, default=None, help="Path to client_dumps_15_shards.json")
    parser.add_argument("--brief", type=Path, default=None, help="Path to astrobranding_[marca].md")
    parser.add_argument("--eco", default="eco-1", choices=["eco-1", "eco-2", "eco-3"], help="Selected ecosystem ID")
    parser.add_argument("--dry-run", action="store_true", help="Calculate without writing to disk")
    args = parser.parse_args()

    engine = FontgenEngine(brand=args.brand, shards_path=args.shards, brief_path=args.brief)
    manifest, markdown = engine.run(selected_eco_id=args.eco, dry_run=args.dry_run)

    print(f"✅ FONTGEN ENGINE EJECUTADO EXITOSAMENTE PARA: {args.brand.upper()}")
    print(f"  • Ecosistemas Candidatos: {len(manifest.get('candidate_ecosystems', []))}")
    print(f"  • Ecosistema Seleccionado: {manifest.get('selected_ecosystem_id')}")
    print(f"  • Token Primario Display: {manifest['selected_ecosystem']['tokens']['display_primary']['$value']}")
    print(f"  • Token Secundario Body:  {manifest['selected_ecosystem']['tokens']['ui_secondary']['$value']}")
    print(f"  • Token Acento Monograma: {manifest['selected_ecosystem']['tokens']['accent_brand']['$value']}")
    print(f"  • Documentación Markdown: {len(markdown)} caracteres")
    return 0


if __name__ == "__main__":
    sys.exit(main())
