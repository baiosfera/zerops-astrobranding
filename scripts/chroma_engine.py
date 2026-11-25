#!/usr/bin/env python3
"""
chroma_engine.py — Sovereign OKLCH Color Architecture & Dual WCAG 2.2 AAA / APCA Engine (v4.1).
Multi-Axis Oráculo 15-Shards + 5-Tier Vertical Archetype Synthesizer + Anti-Slop Editorial Rules.
Complies with W3C DTCG 2025.10, Display P3, Tailwind CSS v4 @theme, Impeccable & Design-Taste rules:
- Same founder Oráculo 15-shards + different vertical JSONs yield genuinely distinct visual worlds.
- Fixes brief_path yong_shen regex overwriting shards, preserves shard Element normalization.
- Rejects AI neon-blue-on-navy clichés (#38b6ff/#080c14) and warm-beige/brass slop (#f5f1ea/#b08947).
- 100% brand-agnostic and isolated to --output-dir (0 phantom directories).
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import math
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


BANNED_SLOP_HEXES = {
    "#38b6ff", "#7be5ff", "#080c14",
    "#f5f1ea", "#f7f5f1", "#fbf8f1", "#efeae0", "#ece6db", "#faf7f1", "#e8dfcb",
    "#b08947", "#b6553a", "#9a2436", "#9c6e2a", "#bc7c3a", "#7d5621",
    "#1a1714", "#1a1814", "#1b1814",
}

ELEMENT_BASE_HUES = {
    "Fire": 28.0,
    "Earth": 148.0,
    "Air": 258.0,
    "Water": 236.0,
    "Wood": 162.0,
    "Metal": 252.0,
}

PLANET_HUE_SHIFTS = {
    "Sun": 18.0,
    "Moon": 222.0,
    "Mercury": 256.0,
    "Venus": 158.0,
    "Mars": 26.0,
    "Jupiter": 274.0,
    "Saturn": 248.0,
}


# -----------------------------------------------------------------------------
# Physical Color Science: OKLCH -> OKLab -> Linear sRGB / Display P3 -> WCAG & APCA
# -----------------------------------------------------------------------------

def _oklch_to_linear_srgb(l: float, c: float, h_deg: float) -> Tuple[float, float, float]:
    h_rad = math.radians(h_deg)
    a = c * math.cos(h_rad)
    b = c * math.sin(h_rad)

    l_ = l + 0.3963377774 * a + 0.2158037573 * b
    m_ = l - 0.1055613458 * a - 0.0638541728 * b
    s_ = l - 0.0894841775 * a - 1.2914855480 * b

    l3 = l_ ** 3
    m3 = m_ ** 3
    s3 = s_ ** 3

    r_lin = +4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3
    g_lin = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3
    b_lin = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3
    return r_lin, g_lin, b_lin


def _lin_to_gamma_srgb(x: float) -> float:
    x = max(0.0, min(1.0, x))
    if x <= 0.0031308:
        return 12.92 * x
    return 1.055 * (x ** (1.0 / 2.4)) - 0.055


def _lin_srgb_to_p3(r: float, g: float, b: float) -> Tuple[float, float, float]:
    p3_r = max(0.0, min(1.0, 0.8224621 * r + 0.1775380 * g + 0.0000000 * b))
    p3_g = max(0.0, min(1.0, 0.0331941 * r + 0.9668058 * g + 0.0000000 * b))
    p3_b = max(0.0, min(1.0, 0.0170827 * r + 0.0723974 * g + 0.9105199 * b))
    return (
        _lin_to_gamma_srgb(p3_r),
        _lin_to_gamma_srgb(p3_g),
        _lin_to_gamma_srgb(p3_b),
    )


def oklch_to_hex_and_p3(l: float, c: float, h_deg: float) -> Tuple[str, str]:
    r_lin, g_lin, b_lin = _oklch_to_linear_srgb(l, c, h_deg)
    r_s = int(round(_lin_to_gamma_srgb(r_lin) * 255.0))
    g_s = int(round(_lin_to_gamma_srgb(g_lin) * 255.0))
    b_s = int(round(_lin_to_gamma_srgb(b_lin) * 255.0))
    hex_val = f"#{r_s:02x}{g_s:02x}{b_s:02x}"

    pr, pg, pb = _lin_srgb_to_p3(r_lin, g_lin, b_lin)
    p3_val = f"color(display-p3 {pr:.3f} {pg:.3f} {pb:.3f})"
    return hex_val, p3_val


def hex_to_rgb_int(hex_str: str) -> Tuple[int, int, int]:
    h = hex_str.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        return (128, 128, 128)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def wcag_relative_luminance(hex_str: str) -> float:
    r, g, b = hex_to_rgb_int(hex_str)
    def _lin(ch: int) -> float:
        s = ch / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def wcag_contrast_ratio(hex_fg: str, hex_bg: str) -> float:
    l1 = wcag_relative_luminance(hex_fg)
    l2 = wcag_relative_luminance(hex_bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return round((hi + 0.05) / (lo + 0.05), 2)


def apca_contrast_lc(hex_fg: str, hex_bg: str) -> float:
    """Computes APCA W3 (0.0.98G-4g) perceptual lightness contrast |Lc|."""
    def _srgb_to_y(hex_val: str) -> float:
        r, g, b = hex_to_rgb_int(hex_val)
        return (
            0.2126729 * ((r / 255.0) ** 2.4)
            + 0.7151522 * ((g / 255.0) ** 2.4)
            + 0.0721750 * ((b / 255.0) ** 2.4)
        )

    y_txt = _srgb_to_y(hex_fg)
    y_bg = _srgb_to_y(hex_bg)

    if y_txt < 0.022:
        y_txt += (0.022 - y_txt) ** 1.414
    if y_bg < 0.022:
        y_bg += (0.022 - y_bg) ** 1.414

    if abs(y_bg - y_txt) < 0.0005:
        return 0.0

    if y_bg > y_txt:
        sapc = ((y_bg ** 0.56) - (y_txt ** 0.57)) * 1.14
        out = 0.0 if sapc < 0.1 else (sapc - 0.027) * 100.0
    else:
        sapc = ((y_bg ** 0.65) - (y_txt ** 0.62)) * 1.14
        out = 0.0 if sapc > -0.1 else (sapc + 0.027) * 100.0
    return round(abs(out), 1)


def parse_oklch_str(val: str) -> Tuple[float, float, float]:
    m = re.search(r"oklch\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)", val)
    if not m:
        return 0.5, 0.1, 220.0
    return float(m.group(1)), float(m.group(2)), float(m.group(3))


def make_color_token(l: float, c: float, h: float, desc: str, hex_override: Optional[str] = None) -> Dict[str, Any]:
    l_r = round(max(0.0, min(1.0, l)), 3)
    c_r = round(max(0.0, min(0.32, c)), 3)
    h_r = round(h % 360.0, 1)
    calc_hex, calc_p3 = oklch_to_hex_and_p3(l_r, c_r, h_r)
    final_hex = hex_override.lower() if hex_override and re.match(r"^#[0-9a-fA-F]{6}$", hex_override) else calc_hex
    l_str = f"{l_r:.2f}" if abs(l_r - round(l_r, 2)) < 1e-4 else f"{l_r:.3f}".rstrip("0")
    c_str = f"{c_r:.2f}" if abs(c_r - round(c_r, 2)) < 1e-4 else f"{c_r:.3f}".rstrip("0")
    h_str = f"{h_r:.1f}".rstrip("0").rstrip(".") if h_r else "0"
    return {
        "$value": f"oklch({l_str} {c_str} {h_str})",
        "$type": "color",
        "$description": desc,
        "colorSpace": "oklch",
        "components": {
            "lightness": l_r,
            "chroma": c_r,
            "hue": h_r,
        },
        "alpha": 1,
        "hex": final_hex,
        "p3": calc_p3,
    }


def _ensure_aaa_contrast(fg_tok: Dict[str, Any], bg_hex: str, is_dark_bg: bool, min_wcag: float = 7.0, min_lc: float = 75.0) -> Dict[str, Any]:
    """Adjusts token lightness only if contrast falls below WCAG or APCA floor."""
    wcag = wcag_contrast_ratio(fg_tok["hex"], bg_hex)
    lc = apca_contrast_lc(fg_tok["hex"], bg_hex)
    if wcag >= min_wcag and lc >= min_lc:
        return fg_tok
    l_cur = fg_tok["components"]["lightness"]
    c_cur = fg_tok["components"]["chroma"]
    h_cur = fg_tok["components"]["hue"]
    step = 0.02 if is_dark_bg else -0.02
    cand = fg_tok
    for _ in range(36):
        l_cur = max(0.06, min(0.985, l_cur + step))
        c_adj = min(c_cur, 0.11 if l_cur > 0.88 or l_cur < 0.25 else c_cur)
        cand = make_color_token(l_cur, c_adj, h_cur, fg_tok["$description"])
        if wcag_contrast_ratio(cand["hex"], bg_hex) >= min_wcag and apca_contrast_lc(cand["hex"], bg_hex) >= min_lc:
            return cand
    return cand


def _audit_ecosystem(themes: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
    dark = themes["dark"]
    light = themes["light"]

    body_dark = wcag_contrast_ratio(dark["text_primary"]["hex"], dark["background"]["hex"])
    head_dark = wcag_contrast_ratio(dark["primary"]["hex"], dark["background"]["hex"])
    btn_dark = wcag_contrast_ratio(dark["background"]["hex"], dark["primary"]["hex"])
    lc_body_dark = apca_contrast_lc(dark["text_primary"]["hex"], dark["background"]["hex"])
    lc_head_dark = apca_contrast_lc(dark["primary"]["hex"], dark["background"]["hex"])
    lc_ui_dark = apca_contrast_lc(dark["accent"]["hex"], dark["surface"]["hex"])

    body_light = wcag_contrast_ratio(light["text_primary"]["hex"], light["background"]["hex"])
    head_light = wcag_contrast_ratio(light["primary"]["hex"], light["background"]["hex"])
    btn_light = wcag_contrast_ratio(light["background"]["hex"], light["primary"]["hex"])
    lc_body_light = apca_contrast_lc(light["text_primary"]["hex"], light["background"]["hex"])
    lc_head_light = apca_contrast_lc(light["primary"]["hex"], light["background"]["hex"])

    worst_body_ratio = min(body_dark, body_light)
    worst_body_lc = min(lc_body_dark, lc_body_light)

    return {
        "wcag_aaa_ratio": worst_body_ratio,
        "apca_lc": worst_body_lc,
        "dark": {
            "body_to_bg_ratio": body_dark,
            "headings_to_bg_ratio": head_dark,
            "button_to_bg_ratio": btn_dark,
            "body_lc": lc_body_dark,
            "headings_lc": lc_head_dark,
            "ui_components_lc": lc_ui_dark,
        },
        "light": {
            "body_to_bg_ratio": body_light,
            "headings_to_bg_ratio": head_light,
            "button_to_bg_ratio": btn_light,
            "body_lc": lc_body_light,
            "headings_lc": lc_head_light,
        },
        "status_aaa": worst_body_ratio >= 7.0 and worst_body_lc >= 75.0,
    }


def synthesize_light_theme(dark_theme: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Composes an intentional Light Mode theme respecting paper tint & >=4.5:1 CTA contrast."""
    p_comp = dark_theme["primary"]["components"]
    s_comp = dark_theme["secondary"]["components"]
    a_comp = dark_theme["accent"]["components"]
    bg_comp = dark_theme["background"]["components"]

    paper_h = bg_comp["hue"] or p_comp["hue"]
    bg_light = make_color_token(0.985, 0.004, paper_h, f"{dark_theme['background']['$description']} (Light Canvas)")
    surf_light = make_color_token(0.952, 0.007, paper_h, f"{dark_theme['surface']['$description']} (Light Surface)")
    txt_light = _ensure_aaa_contrast(
        make_color_token(0.165, 0.014, bg_comp["hue"], f"{dark_theme['text_primary']['$description']} (Light Ink)"),
        bg_light["hex"], is_dark_bg=False, min_wcag=12.0, min_lc=95.0
    )
    muted_light = _ensure_aaa_contrast(
        make_color_token(0.43, 0.018, bg_comp["hue"], f"{dark_theme['text_muted']['$description']} (Light Muted)"),
        bg_light["hex"], is_dark_bg=False, min_wcag=4.6, min_lc=55.0
    )
    prim_light = _ensure_aaa_contrast(
        make_color_token(0.41, min(0.145, max(0.02, p_comp["chroma"])), p_comp["hue"], f"{dark_theme['primary']['$description']} (Light CTA)"),
        bg_light["hex"], is_dark_bg=False, min_wcag=5.5, min_lc=65.0
    )
    sec_light = make_color_token(0.49, min(0.09, max(0.02, s_comp["chroma"])), s_comp["hue"], f"{dark_theme['secondary']['$description']} (Light)")
    acc_light = _ensure_aaa_contrast(
        make_color_token(0.36, min(0.14, max(0.02, a_comp["chroma"])), a_comp["hue"], f"{dark_theme['accent']['$description']} (Light Accent)"),
        bg_light["hex"], is_dark_bg=False, min_wcag=5.5, min_lc=65.0
    )
    return {
        "primary": prim_light,
        "secondary": sec_light,
        "accent": acc_light,
        "background": bg_light,
        "surface": surf_light,
        "text_primary": txt_light,
        "text_muted": muted_light,
    }


def _compose_intentional_ecosystem(
    eco_id: str,
    name: str,
    concept: str,
    recommended_mode: str,
    primary_hue: float,
    primary_chroma: float,
    accent_hue: float,
    neutral_hue: float,
    neutral_chroma: float,
    dark_bg_l: float = 0.135,
    light_bg_l: float = 0.985,
    light_bg_c: float = 0.004,
    light_surf_l: float = 0.952,
    derivation_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Builds an anti-slop composed Light + Dark ecosystem (never naive inversion)."""
    p_c = min(0.165, max(0.015, primary_chroma))
    n_c = min(0.022, max(0.002, neutral_chroma))

    bg_d = make_color_token(dark_bg_l, n_c * 0.72, neutral_hue, "Lienzo oscuro calibrado")
    surf_d = make_color_token(dark_bg_l + 0.055, n_c * 0.9, neutral_hue, "Superficie elevada")
    txt_d = _ensure_aaa_contrast(
        make_color_token(0.962, min(0.008, n_c * 0.4), neutral_hue, "Texto principal nítido"),
        bg_d["hex"], is_dark_bg=True, min_wcag=12.0, min_lc=94.0
    )
    muted_d = _ensure_aaa_contrast(
        make_color_token(0.695, n_c * 1.0, neutral_hue, "Texto secundario legible"),
        bg_d["hex"], is_dark_bg=True, min_wcag=4.8, min_lc=55.0
    )
    prim_d = _ensure_aaa_contrast(
        make_color_token(0.71, min(0.14, p_c), primary_hue, "Acento primario interactivo"),
        bg_d["hex"], is_dark_bg=True, min_wcag=5.2, min_lc=60.0
    )
    sec_d = make_color_token(0.56, min(0.085, p_c * 0.65), (primary_hue + 14.0) % 360.0, "Secundario estructural")
    acc_d = _ensure_aaa_contrast(
        make_color_token(0.77, min(0.13, p_c * 0.88), accent_hue, "Acento de foco / estado"),
        surf_d["hex"], is_dark_bg=True, min_wcag=5.0, min_lc=58.0
    )
    dark_theme = {
        "primary": prim_d, "secondary": sec_d, "accent": acc_d,
        "background": bg_d, "surface": surf_d, "text_primary": txt_d, "text_muted": muted_d,
    }

    bg_l = make_color_token(light_bg_l, light_bg_c, neutral_hue, "Lienzo claro arquitectónico")
    surf_l = make_color_token(light_surf_l, min(0.012, light_bg_c + 0.004), neutral_hue, "Superficie elevada clara")
    txt_l = _ensure_aaa_contrast(
        make_color_token(0.165, min(0.016, n_c * 0.85), neutral_hue, "Tinta principal"),
        bg_l["hex"], is_dark_bg=False, min_wcag=12.0, min_lc=94.0
    )
    muted_l = _ensure_aaa_contrast(
        make_color_token(0.445, n_c * 1.0, neutral_hue, "Texto secundario claro"),
        bg_l["hex"], is_dark_bg=False, min_wcag=4.8, min_lc=55.0
    )
    prim_l = _ensure_aaa_contrast(
        make_color_token(0.425, min(0.15, p_c * 1.02), primary_hue, "Acento primario sobre claro"),
        bg_l["hex"], is_dark_bg=False, min_wcag=5.2, min_lc=62.0
    )
    sec_l = make_color_token(0.50, min(0.085, p_c * 0.65), (primary_hue + 14.0) % 360.0, "Secundario estructural claro")
    acc_l = _ensure_aaa_contrast(
        make_color_token(0.37, min(0.145, p_c), accent_hue, "Acento de estado claro"),
        surf_l["hex"], is_dark_bg=False, min_wcag=5.2, min_lc=60.0
    )
    light_theme = {
        "primary": prim_l, "secondary": sec_l, "accent": acc_l,
        "background": bg_l, "surface": surf_l, "text_primary": txt_l, "text_muted": muted_l,
    }

    themes = {"dark": dark_theme, "light": light_theme}
    audit = _audit_ecosystem(themes)
    return {
        "id": eco_id,
        "name": name,
        "recommended_mode": recommended_mode,
        "concept": concept,
        "derivation_parameters": derivation_params or {},
        "themes": themes,
        "audit": {
            "wcag_aaa_ratio": audit["wcag_aaa_ratio"],
            "apca_lc": audit["apca_lc"],
            "dark": audit["dark"],
            "light": audit["light"],
        },
    }


def _norm_element(raw: str, default: str = "Water") -> str:
    txt = str(raw or "").lower()
    for tok, norm in (
        ("water", "Water"), ("agua", "Water"),
        ("wood", "Wood"), ("madera", "Wood"),
        ("fire", "Fire"), ("fuego", "Fire"),
        ("earth", "Earth"), ("tierra", "Earth"),
        ("metal", "Metal"),
        ("air", "Air"), ("aire", "Air"),
    ):
        if re.search(rf"\b{tok}\b", txt):
            return norm
    return default


def classify_vertical_archetype(vblob: str, vertical_slug: str = "") -> str:
    """5-tier brand-agnostic classifier driving distinct aesthetics under one umbrella chart."""
    t = f"{vertical_slug} {vblob}".lower()
    if any(k in t for k in ("astrotipia", "sabidurías cósmicas", "arquetipo vocacional", "kabbalah", "human design", "numerolog", "tarot", "autoconocimiento")):
        return "cosmic_archetypal"
    if any(k in t for k in ("synthemika", "astrobranding aplicado", "tokens de diseño", "brandbook", "monogramas vectoriales", "tipografía curada", "tokens dtcg")):
        return "design_system_atelier"
    if any(k in t for k in ("apotelos", "causalidad inversa", "arqueología del futuro", "saga editorial", "manifiesto conceptual", "book_waitlist")):
        return "editorial_manifesto"
    if any(k in t for k in ("consultor", "b2b", "financier", "abogado", "médico", "unipersonal", "agencia", "automatiz", "saas", "seo local", "google maps", "baiosfera")):
        return "architectural_b2b"
    return "editorial_brand"


# -----------------------------------------------------------------------------
# Signal Extraction: Oráculo 15-Shards + Vertical JSON + Brief Markdown
# -----------------------------------------------------------------------------

def extract_oraculo_and_vertical_signals(
    brief_path: Optional[Path] = None,
    shards_path: Optional[Path] = None,
    vertical_json_path: Optional[Path] = None,
    vertical_slug: Optional[str] = None,
) -> Dict[str, Any]:
    sig: Dict[str, Any] = {
        "sources": [],
        "sun_lon": 210.0,
        "sun_sign": "Scorpio",
        "mc_sign": "Leo",
        "venus_deg": 225.0,
        "venus_sign": "Scorpio",
        "dominant_element": "Earth",
        "sidereal_sun_sign": "",
        "sidereal_mc_sign": "",
        "sidereal_asc_sign": "",
        "vedic_shadbala_planet": "Jupiter",
        "vedic_shadbala_rupas": 7.0,
        "nakshatra": "Rohini",
        "nakshatra_lord": "Moon",
        "bazi_day_master": "Wu",
        "bazi_day_element": "Earth",
        "bazi_month_element": "Earth",
        "yong_shen": "Water",
        "vertical_archetype": "editorial_brand",
        "vertical_slug": vertical_slug or "",
        "vertical_display_name": "",
        "vertical_is_b2b": False,
        "vertical_category": "",
    }

    shards_had_ys = False
    shards_had_el = False
    shards_had_sun = False

    if shards_path and shards_path.is_file():
        sdata = json.loads(shards_path.read_text(encoding="utf-8"))
        sig["sources"].append(f"shards:{shards_path.name}")
        s1 = sdata.get("shard_01", {}).get("data", {})
        s2 = sdata.get("shard_02", {}).get("data", {})
        s3 = sdata.get("shard_03", {}).get("data", {})
        s4 = sdata.get("shard_04", {}).get("data", {})

        planets = s1.get("planets", {})
        tripod = s1.get("tripod_of_iron", {})
        arroyo = s1.get("arroyo_elements", {})
        if planets.get("Sun", {}).get("longitude") is not None:
            sig["sun_lon"] = float(planets["Sun"]["longitude"])
            shards_had_sun = True
        elif tripod.get("sun", {}).get("longitude") is not None:
            sig["sun_lon"] = float(tripod["sun"]["longitude"])
            shards_had_sun = True
        if tripod.get("sun", {}).get("sign"):
            sig["sun_sign"] = str(tripod["sun"]["sign"])
        if tripod.get("midheaven_house_10", {}).get("sign"):
            sig["mc_sign"] = str(tripod["midheaven_house_10"]["sign"])
        if planets.get("Venus", {}).get("longitude") is not None:
            sig["venus_deg"] = float(planets["Venus"]["longitude"])
        if planets.get("Venus", {}).get("sign"):
            sig["venus_sign"] = str(planets["Venus"]["sign"])
        if arroyo.get("dominant_element"):
            sig["dominant_element"] = _norm_element(arroyo["dominant_element"], "Earth")
            shards_had_el = True

        fb = s2.get("fagan_bradley", {})
        if fb.get("sun", {}).get("sign") or fb.get("planets", {}).get("Sun", {}).get("sign"):
            sig["sidereal_sun_sign"] = str((fb.get("sun") or fb.get("planets", {}).get("Sun", {})).get("sign", ""))
        if fb.get("midheaven", {}).get("sign"):
            sig["sidereal_mc_sign"] = str(fb["midheaven"]["sign"])
        if fb.get("ascendant", {}).get("sign"):
            sig["sidereal_asc_sign"] = str(fb["ascendant"]["sign"])

        sh = s3.get("shadbala", {})
        if sh.get("dominant_planet"):
            sig["vedic_shadbala_planet"] = str(sh["dominant_planet"])
        if sh.get("max_rupas"):
            sig["vedic_shadbala_rupas"] = round(float(sh["max_rupas"]), 2)
        nk = s3.get("nakshatra", {})
        if nk.get("name"):
            sig["nakshatra"] = str(nk["name"]).split()[0]
        if nk.get("lord") or nk.get("ruler"):
            sig["nakshatra_lord"] = str(nk.get("lord") or nk.get("ruler"))

        dm = s4.get("day_master", {})
        if dm.get("name"):
            sig["bazi_day_master"] = str(dm["name"]).split()[0]
        if dm.get("element"):
            sig["bazi_day_element"] = _norm_element(dm["element"], "Earth")
        fp = s4.get("four_pillars", {})
        if fp.get("month", {}).get("element"):
            sig["bazi_month_element"] = _norm_element(fp["month"]["element"], "Earth")
        ys = s4.get("yong_shen", {})
        if ys.get("element"):
            sig["yong_shen"] = _norm_element(ys["element"], "Water")
            shards_had_ys = True

    if brief_path and brief_path.is_file():
        sig["sources"].append(f"brief:{brief_path.name}")
        txt = brief_path.read_text(encoding="utf-8", errors="replace")
        if not shards_had_sun:
            m_sun = re.search(r"Longitud solar[^:\n]*:\s*([\d.]+)", txt, re.IGNORECASE)
            if m_sun:
                sig["sun_lon"] = float(m_sun.group(1))
        if not shards_had_el:
            m_el = re.search(r"Elemento dominante[^:\n]*:\s*([A-Za-zÁÉÍÓÚáéíóú]+)", txt, re.IGNORECASE)
            if m_el:
                sig["dominant_element"] = _norm_element(m_el.group(1), sig["dominant_element"])
        if not shards_had_ys:
            m_ys = re.search(r"Elemento balancín Yong Shen[^:\n]*:\s*([^\n]+)", txt, re.IGNORECASE)
            if m_ys:
                sig["yong_shen"] = _norm_element(m_ys.group(1), "Water")
        m_lord = re.search(r"\*\*Regente:\*\*\s*([A-Za-zÁÉÍÓÚáéíóú]+)", txt, re.IGNORECASE)
        if m_lord and sig["nakshatra_lord"] == "Moon":
            lord_raw = m_lord.group(1).lower()
            sig["nakshatra_lord"] = {"marte": "Mars", "sol": "Sun", "luna": "Moon", "mercurio": "Mercury", "venus": "Venus", "jupiter": "Jupiter", "júpiter": "Jupiter", "saturno": "Saturn"}.get(lord_raw, lord_raw.title())

    if vertical_json_path and vertical_json_path.is_file():
        sig["sources"].append(f"vertical:{vertical_json_path.name}")
        vdata = json.loads(vertical_json_path.read_text(encoding="utf-8"))
        vblob = json.dumps(vdata, ensure_ascii=False)
        sig["vertical_display_name"] = str(vdata.get("display_name") or "")
        sig["vertical_slug"] = str(vdata.get("vertical_slug") or vertical_slug or vertical_json_path.stem)
        sig["vertical_category"] = str(vdata.get("category") or vdata.get("role_in_ecosystem") or "")
        arch = classify_vertical_archetype(vblob, sig["vertical_slug"])
        sig["vertical_archetype"] = arch
        sig["vertical_is_b2b"] = arch == "architectural_b2b"
    elif vertical_slug:
        sig["vertical_archetype"] = classify_vertical_archetype("", vertical_slug)
        sig["vertical_is_b2b"] = sig["vertical_archetype"] == "architectural_b2b"

    return sig


def synthesize_multiaxis_ecosystems(sig: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Synthesizes 3 differentiated visual worlds calibrated BOTH to Oráculo coordinates
    AND the vertical's commercial/psychological archetype (`vertical_archetype`).
    """
    ys = sig.get("yong_shen", "Water")
    dom_el = sig.get("dominant_element", "Earth")
    nak_lord = sig.get("nakshatra_lord", "Mars")
    sh_planet = sig.get("vedic_shadbala_planet", "Sun")
    bazi_day = sig.get("bazi_day_element", "Wood")
    sun_lon = float(sig.get("sun_lon", 79.0))
    venus_deg = float(sig.get("venus_deg", 77.3))
    arch = sig.get("vertical_archetype", "editorial_brand")

    if arch == "cosmic_archetypal":
        # Eco 1 (Dark-first nocturnal observatory: refined astral indigo slate, zero AI-cyan & zero neon purple)
        h1 = (PLANET_HUE_SHIFTS.get("Jupiter", 274.0) + (sun_lon % 12.0) - 6.0) % 360.0
        eco1 = _compose_intentional_ecosystem(
            eco_id="eco_1_nocturnal_observatory",
            name=f"Observatorio Nocturno & Índigo Astral (Casa 7 · Yong Shen {ys})",
            concept=(
                f"Atmósfera introspectiva nocturna de alta legibilidad para lectura vocacional: "
                f"pizarra celeste profunda con acento índigo astral (Chitra + {ys}), cero púrpuras neón."
            ),
            recommended_mode="dark",
            primary_hue=h1,
            primary_chroma=0.132,
            accent_hue=(h1 + 18.0) % 360.0,
            neutral_hue=272.0,
            neutral_chroma=0.020,
            dark_bg_l=0.132,
            light_bg_l=0.985,
            light_bg_c=0.005,
            light_surf_l=0.948,
            derivation_params={
                "vertical_archetype": arch,
                "axes": ["house_7_mirror", "yong_shen", "jupiter_dharma"],
                "yong_shen": ys,
                "sun_sign": sig["sun_sign"],
            },
        )
        # Eco 2 (Light-first ephemeris solstice paper: archival cool paper + Mars/Sun vermilion-crimson)
        h2 = PLANET_HUE_SHIFTS.get(nak_lord, 24.0)
        eco2 = _compose_intentional_ecosystem(
            eco_id="eco_2_ephemeris_solstice",
            name=f"Efemérides de Solsticio & Carmesí {nak_lord} (Shadbala {sh_planet} · {sig['nakshatra']})",
            concept=(
                f"Cuaderno técnico de efemérides en papel frío archival con tinta nocturna y señal "
                f"solar carmesí ({sh_planet} {sig['vedic_shadbala_rupas']} Rupas · {sig['nakshatra']})."
            ),
            recommended_mode="light",
            primary_hue=h2,
            primary_chroma=0.145,
            accent_hue=(h2 + 12.0) % 360.0,
            neutral_hue=248.0,
            neutral_chroma=0.006,
            dark_bg_l=0.125,
            light_bg_l=0.986,
            light_bg_c=0.004,
            light_surf_l=0.950,
            derivation_params={
                "vertical_archetype": arch,
                "axes": ["vedic_shadbala", "nakshatra_lord"],
                "vedic_shadbala": f"{sh_planet} ({sig['vedic_shadbala_rupas']} Rupas)",
                "nakshatra": f"{sig['nakshatra']} ({nak_lord})",
            },
        )
        # Eco 3 (Dual sea-jade alchemy: Jia Wood + Cancer Casa 11 + Water Yong Shen)
        h3 = 192.0
        eco3 = _compose_intentional_ecosystem(
            eco_id="eco_3_alchemical_aegean",
            name=f"Alquimia Egeo & Madera {sig['bazi_day_master']} (Casa 11 · {bazi_day})",
            concept=(
                f"Equilibrio entre profundidad oceánica ({ys}) y crecimiento estructural ({sig['bazi_day_master']} {bazi_day}) "
                f"para reportes interactivos y mapas natales sin ruido visual."
            ),
            recommended_mode="dark",
            primary_hue=h3,
            primary_chroma=0.115,
            accent_hue=(h3 + 14.0) % 360.0,
            neutral_hue=196.0,
            neutral_chroma=0.016,
            dark_bg_l=0.138,
            light_bg_l=0.984,
            light_bg_c=0.005,
            light_surf_l=0.948,
            derivation_params={
                "vertical_archetype": arch,
                "axes": ["bazi_day_master", "yong_shen", "house_11"],
                "bazi_day_master": f"{sig['bazi_day_master']} ({bazi_day})",
            },
        )
        return [eco1, eco2, eco3]

    if arch in ("design_system_atelier", "editorial_manifesto"):
        mode_1 = "light" if arch == "editorial_manifesto" else "dark"
        h1 = 248.0 if arch == "editorial_manifesto" else 224.0
        eco1 = _compose_intentional_ecosystem(
            eco_id=f"eco_1_{arch[:8]}_ink",
            name=f"Monolito Editorial & Tinta Pura ({sig['mc_sign']} MC · {ys})",
            concept=f"Jerarquía suiza de alto contraste inspirada en {sig['nakshatra']} y rigor estructural {sig['mc_sign']}.",
            recommended_mode=mode_1,
            primary_hue=h1,
            primary_chroma=0.065 if arch == "editorial_manifesto" else 0.125,
            accent_hue=(h1 + 16.0) % 360.0,
            neutral_hue=250.0,
            neutral_chroma=0.005,
            derivation_params={"vertical_archetype": arch, "mc_sign": sig["mc_sign"], "yong_shen": ys},
        )
        h2 = PLANET_HUE_SHIFTS.get(nak_lord, 26.0)
        eco2 = _compose_intentional_ecosystem(
            eco_id=f"eco_2_{arch[:8]}_signal",
            name=f"Edición Contundente & Señal {nak_lord} ({sh_planet} · {sig['bazi_month_element']})",
            concept=f"Composición editorial intensa regida por {nak_lord} ({sig['nakshatra']}) y precisión {sig['bazi_month_element']}.",
            recommended_mode="dark",
            primary_hue=h2,
            primary_chroma=0.145,
            accent_hue=(h2 + 12.0) % 360.0,
            neutral_hue=255.0,
            neutral_chroma=0.004,
            derivation_params={"vertical_archetype": arch, "nakshatra_lord": nak_lord},
        )
        eco3 = _compose_intentional_ecosystem(
            eco_id=f"eco_3_{arch[:8]}_mineral",
            name=f"Piedra Mineral & Trazo {sig['bazi_day_master']} ({bazi_day})",
            concept=f"Base mineral templada derivada de Day Master {sig['bazi_day_master']} ({bazi_day}).",
            recommended_mode="light",
            primary_hue=166.0,
            primary_chroma=0.11,
            accent_hue=178.0,
            neutral_hue=170.0,
            neutral_chroma=0.012,
            derivation_params={"vertical_archetype": arch, "bazi_day_master": sig["bazi_day_master"]},
        )
        return [eco1, eco2, eco3]

    # Default / architectural_b2b (Light-first cool porcelain + deep cobalt; Carbon+Mars; Viridian+Bone)
    ys_hue = ELEMENT_BASE_HUES.get(ys, 236.0)
    h1_prim = 262.0 if ys == "Water" and sig.get("vertical_is_b2b") else (ys_hue + (sun_lon % 18.0) - 9.0) % 360.0
    h1_neutral = (h1_prim - 6.0) % 360.0
    eco1 = _compose_intentional_ecosystem(
        eco_id="eco_1_porcelain_cobalt",
        name=f"Porcelana Mineral & Cobalto Profundo ({sig['mc_sign']} MC · {ys})",
        concept=(
            f"Mundo visual claro de alta legibilidad ejecutiva B2B (Sol {sig['sun_sign']} / MC {sig['mc_sign']} balanceado por "
            f"Yong Shen {ys} sobre papel frío mineral)."
        ),
        recommended_mode="light",
        primary_hue=h1_prim,
        primary_chroma=0.145,
        accent_hue=(h1_prim - 14.0) % 360.0,
        neutral_hue=h1_neutral,
        neutral_chroma=0.012,
        dark_bg_l=0.135,
        light_bg_l=0.986,
        light_bg_c=0.004,
        light_surf_l=0.954,
        derivation_params={
            "vertical_archetype": arch,
            "axes": ["tropical_mc", "yong_shen", "vertical_context"],
            "mc_sign": sig["mc_sign"],
            "yong_shen": ys,
        },
    )

    lord_hue = PLANET_HUE_SHIFTS.get(nak_lord, 26.0)
    if abs((lord_hue - h1_prim + 180) % 360 - 180) < 45.0:
        lord_hue = (h1_prim + 130.0) % 360.0
    eco2 = _compose_intentional_ecosystem(
        eco_id="eco_2_carbon_signal",
        name=f"Carbón Arquitectónico & Señal {nak_lord} (Védico {sh_planet} · {sig['nakshatra']})",
        concept=(
            f"Mundo oscuro neutro sin tinte azulado AI: grafito de precisión ({sig['bazi_month_element']}) "
            f"con único acento activo regido por {nak_lord} ({sig['nakshatra']}) y Shadbala {sh_planet}."
        ),
        recommended_mode="dark",
        primary_hue=lord_hue,
        primary_chroma=0.155,
        accent_hue=(lord_hue + 10.0) % 360.0,
        neutral_hue=255.0,
        neutral_chroma=0.004,
        dark_bg_l=0.125,
        light_bg_l=0.985,
        light_bg_c=0.003,
        light_surf_l=0.950,
        derivation_params={
            "vertical_archetype": arch,
            "axes": ["vedic_shadbala", "nakshatra_lord", "bazi_month_element"],
            "vedic_shadbala": f"{sh_planet} ({sig['vedic_shadbala_rupas']} Rupas)",
            "nakshatra": f"{sig['nakshatra']} (Lord: {nak_lord})",
            "bazi_month_element": sig["bazi_month_element"],
        },
    )

    h3_prim = ELEMENT_BASE_HUES.get(bazi_day, 162.0)
    if abs((h3_prim - h1_prim + 180) % 360 - 180) < 40.0 or abs((h3_prim - lord_hue + 180) % 360 - 180) < 40.0:
        h3_prim = 164.0
    h3_prim = (h3_prim + ((venus_deg % 10.0) - 5.0)) % 360.0
    eco3 = _compose_intentional_ecosystem(
        eco_id="eco_3_mineral_viridian",
        name=f"Basalto Mineral & Viridiano ({sig['bazi_day_master']} {bazi_day} · Sideral {sig.get('sidereal_sun_sign') or 'Earth'})",
        concept=(
            f"Síntesis entre Day Master {sig['bazi_day_master']} ({bazi_day}) y Venus sideral "
            f"({sig.get('sidereal_sun_sign') or sig['venus_sign']}): piedra mineral verde-grafito y hueso glacial."
        ),
        recommended_mode="light" if dom_el in ("Earth", "Air") else "dark",
        primary_hue=h3_prim,
        primary_chroma=0.115,
        accent_hue=(h3_prim + 12.0) % 360.0,
        neutral_hue=(h3_prim + 8.0) % 360.0,
        neutral_chroma=0.014,
        dark_bg_l=0.145,
        light_bg_l=0.984,
        light_bg_c=0.005,
        light_surf_l=0.948,
        derivation_params={
            "vertical_archetype": arch,
            "axes": ["bazi_day_master", "sidereal_sun_venus"],
            "bazi_day_master": f"{sig['bazi_day_master']} ({bazi_day})",
            "sidereal_sun": sig.get("sidereal_sun_sign") or sig["sun_sign"],
        },
    )

    return [eco1, eco2, eco3]


# -----------------------------------------------------------------------------
# Legacy Static §3 Brief Parser (Used ONLY when --mode brief)
# -----------------------------------------------------------------------------

def _role_norm(raw_role: str) -> Optional[str]:
    r = re.sub(r"[*_`]", "", raw_role).strip().lower()
    mapping = {
        "color-primary": "primary", "primary": "primary",
        "color-secondary": "secondary", "secondary": "secondary",
        "color-accent": "accent", "accent": "accent",
        "color-background": "background", "background": "background", "bg": "background",
        "color-surface": "surface", "surface": "surface",
        "color-text-primary": "text_primary", "text_primary": "text_primary", "text-primary": "text_primary", "text": "text_primary",
        "color-text-muted": "text_muted", "text_muted": "text_muted", "text-muted": "text_muted", "muted": "text_muted",
    }
    return mapping.get(r)


def parse_ecosystems_from_brief(brief_text: str) -> List[Dict[str, Any]]:
    section_matches = list(re.finditer(r"^###\s+3\.\d+\s+Ecosistema\s+[^:]+:\s*(.+)$", brief_text, re.MULTILINE))
    if not section_matches:
        return []

    ecosystems: List[Dict[str, Any]] = []
    for idx, m in enumerate(section_matches):
        start = m.end()
        end = section_matches[idx + 1].start() if idx + 1 < len(section_matches) else len(brief_text)
        next_h2 = re.search(r"^##\s+", brief_text[start:end], re.MULTILINE)
        if next_h2:
            end = start + next_h2.start()
        block = brief_text[start:end]
        raw_title = m.group(1).strip()

        concept = f"Ecosistema literal de brief ({raw_title})."
        for line in block.splitlines():
            ls = line.strip()
            if not ls or ls.startswith("#") or ls.startswith("|") or ls.startswith("**Narrativa"):
                continue
            concept = re.sub(r"\*\*", "", ls)
            break

        dark_block, light_block = block, ""
        m_light = re.search(r"^####\s+Modo Claro\b.*$", block, re.MULTILINE | re.IGNORECASE)
        if m_light:
            dark_block = block[:m_light.start()]
            light_block = block[m_light.start():]

        def _parse_table(sub: str) -> Dict[str, Dict[str, Any]]:
            tokens: Dict[str, Dict[str, Any]] = {}
            for line in sub.splitlines():
                if not line.strip().startswith("|"):
                    continue
                parts = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(parts) < 3 or "oklch(" not in parts[1].lower():
                    continue
                role = _role_norm(parts[0])
                if not role:
                    continue
                l, c, h = parse_oklch_str(parts[1])
                hex_m = re.search(r"(#[0-9a-fA-F]{6})", parts[2])
                desc = re.sub(r"[*_`]", "", parts[3]).strip() if len(parts) >= 4 else role
                tokens[role] = make_color_token(l, c, h, desc, hex_override=hex_m.group(1) if hex_m else None)
            return tokens

        dark_tokens = _parse_table(dark_block)
        required = {"primary", "secondary", "accent", "background", "surface", "text_primary", "text_muted"}
        if not required.issubset(dark_tokens.keys()):
            continue

        light_tokens = _parse_table(light_block) if light_block else {}
        if not required.issubset(light_tokens.keys()):
            light_tokens = synthesize_light_theme(dark_tokens)

        dark_tokens["text_primary"] = _ensure_aaa_contrast(dark_tokens["text_primary"], dark_tokens["background"]["hex"], is_dark_bg=True)
        light_tokens["text_primary"] = _ensure_aaa_contrast(light_tokens["text_primary"], light_tokens["background"]["hex"], is_dark_bg=False)
        themes = {"dark": dark_tokens, "light": light_tokens}
        audit = _audit_ecosystem(themes)
        clean = re.sub(r"[^a-zA-Z0-9]+", "_", raw_title.split("(")[0].strip().lower()).strip("_")
        eco_id = "eco_" + "_".join(clean.split("_")[:2])

        ecosystems.append({
            "id": eco_id,
            "name": raw_title,
            "recommended_mode": "dark",
            "concept": concept,
            "themes": themes,
            "audit": {
                "wcag_aaa_ratio": audit["wcag_aaa_ratio"],
                "apca_lc": audit["apca_lc"],
                "dark": audit["dark"],
                "light": audit["light"],
            },
        })
    return ecosystems


def build_css_blocks(selected: Dict[str, Any]) -> Dict[str, str]:
    d = selected["themes"]["dark"]
    lt = selected["themes"]["light"]
    default_mode = selected.get("recommended_mode", "light")
    root_src, alt_src, alt_attr = (lt, d, '[data-theme="dark"]') if default_mode == "light" else (d, lt, '[data-theme="light"]')
    tailwind_block = (
        "@theme {\n"
        "  --color-brand-primary: var(--brand-primary);\n"
        "  --color-brand-secondary: var(--brand-secondary);\n"
        "  --color-brand-accent: var(--brand-accent);\n"
        "  --color-brand-bg: var(--brand-bg);\n"
        "  --color-brand-surface: var(--brand-surface);\n"
        "  --color-brand-text: var(--brand-text);\n"
        "  --color-brand-muted: var(--brand-muted);\n"
        "}"
    )
    css_root = (
        f"/* Default visual mode: {default_mode} */\n"
        ":root {\n"
        f"  --brand-primary: {root_src['primary']['$value']};\n"
        f"  --brand-secondary: {root_src['secondary']['$value']};\n"
        f"  --brand-accent: {root_src['accent']['$value']};\n"
        f"  --brand-bg: {root_src['background']['$value']};\n"
        f"  --brand-surface: {root_src['surface']['$value']};\n"
        f"  --brand-text: {root_src['text_primary']['$value']};\n"
        f"  --brand-muted: {root_src['text_muted']['$value']};\n"
        "}\n"
        f"{alt_attr} {{\n"
        f"  --brand-primary: {alt_src['primary']['$value']};\n"
        f"  --brand-secondary: {alt_src['secondary']['$value']};\n"
        f"  --brand-accent: {alt_src['accent']['$value']};\n"
        f"  --brand-bg: {alt_src['background']['$value']};\n"
        f"  --brand-surface: {alt_src['surface']['$value']};\n"
        f"  --brand-text: {alt_src['text_primary']['$value']};\n"
        f"  --brand-muted: {alt_src['text_muted']['$value']};\n"
        "}"
    )
    return {
        "default_mode": default_mode,
        "tailwind_v4_theme_block": tailwind_block,
        "css_variables_root": css_root,
        "gradient_interpolation": "in oklch",
    }


def render_chroma_preview_html(manifest: Dict[str, Any]) -> str:
    brand_esc = html_lib.escape(str(manifest.get("brand", "BRAND")))
    vslug = html_lib.escape(str(manifest.get("vertical_slug") or manifest.get("brand", "")))
    varch = html_lib.escape(str(manifest.get("vertical_archetype") or "editorial_brand"))
    sel_id = manifest.get("selected_ecosystem_id", "")
    sections: List[str] = []

    for eco in manifest.get("ecosystems", []):
        eid = html_lib.escape(eco["id"])
        ename = html_lib.escape(eco["name"])
        econ = html_lib.escape(eco["concept"])
        rmode = html_lib.escape(str(eco.get("recommended_mode", "light")).upper())
        badge = " · SELECCIONADO" if eco["id"] == sel_id else ""
        audit = eco.get("audit", {})
        params_json = html_lib.escape(json.dumps(eco.get("derivation_parameters", {}), ensure_ascii=False))

        mode_cards: List[str] = []
        order = ("light", "dark") if eco.get("recommended_mode") == "light" else ("dark", "light")
        for mode_name in order:
            theme = eco["themes"][mode_name]
            bg = theme["background"]["hex"]
            surf = theme["surface"]["hex"]
            txt = theme["text_primary"]["hex"]
            mut = theme["text_muted"]["hex"]
            prim = theme["primary"]["hex"]
            acc = theme["accent"]["hex"]
            maud = audit.get(mode_name, {})

            swatches = []
            for role, tok in theme.items():
                swatches.append(
                    f'<div class="swatch">'
                    f'<div class="chip" style="background:{html_lib.escape(tok["hex"])}"></div>'
                    f'<div class="meta"><strong>{html_lib.escape(role)}</strong>'
                    f'<span>{html_lib.escape(tok["hex"])} · {html_lib.escape(tok["$value"])}</span></div></div>'
                )

            mode_cards.append(
                f'<div class="mode-card" style="background:{bg};color:{txt};border-color:{mut}44">'
                f'<div class="mode-head"><span>{mode_name.upper()} MODE</span>'
                f'<span class="metrics">Texto {maud.get("body_to_bg_ratio", audit.get("wcag_aaa_ratio"))}:1 · Botón {maud.get("button_to_bg_ratio", "4.5+")}:1 · APCA Lc {maud.get("body_lc", audit.get("apca_lc"))}</span></div>'
                f'<div class="sample-ui" style="background:{surf};border-color:{mut}33">'
                f'<h3 style="color:{txt}">Muestra tipográfica y jerarquía ({vslug})</h3>'
                f'<p style="color:{mut}">Ejemplo real de contraste y elevación sin resplandor AI ni relleno artificial.</p>'
                f'<button style="background:{prim};color:{bg}">Acción principal</button> '
                f'<span class="pill" style="border:1px solid {acc};color:{acc}">Estado</span>'
                f'</div>'
                f'<div class="swatches">{"".join(swatches)}</div>'
                f'</div>'
            )

        sections.append(
            f'<section class="eco-block" id="{eid}">'
            f'<h2>{ename}<span class="tag">{badge} · Recomendado: {rmode}</span></h2>'
            f'<p class="concept">{econ}</p>'
            f'<p class="params">Parámetros Oráculo/Vertical: <code>{params_json}</code></p>'
            f'<div class="modes-grid">{"".join(mode_cards)}</div>'
            f'</section>'
        )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Chroma v4.1 OKLCH Preview — {brand_esc} / {vslug}</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; background:#101216; color:#f1f5f9; margin:0; padding:32px 24px; }}
  .wrap {{ max-width:1280px; margin:0 auto; display:flex; flex-direction:column; gap:28px; }}
  h1 {{ margin:0 0 6px; font-size:24px; }}
  .sub {{ color:#94a3b8; font-size:14px; margin:0; }}
  .eco-block {{ background:#171a21; border:1px solid #262b36; border-radius:14px; padding:24px; }}
  .eco-block h2 {{ margin:0 0 6px; font-size:18px; }}
  .tag {{ font-size:12px; color:#a3b8ff; font-weight:700; margin-left:6px; }}
  .concept {{ color:#cbd5e1; font-size:14px; margin:0 0 6px; }}
  .params {{ color:#94a3b8; font-size:12px; margin:0 0 18px; word-break:break-word; }}
  .modes-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(360px,1fr)); gap:18px; }}
  .mode-card {{ border:1px solid; border-radius:12px; padding:18px; display:flex; flex-direction:column; gap:14px; }}
  .mode-head {{ display:flex; justify-content:space-between; font-size:12px; font-weight:700; opacity:.85; }}
  .sample-ui {{ padding:16px; border-radius:10px; border:1px solid; }}
  .sample-ui h3 {{ margin:0 0 6px; font-size:16px; }}
  .sample-ui p {{ margin:0 0 12px; font-size:13px; line-height:1.5; }}
  .sample-ui button {{ border:none; border-radius:6px; padding:8px 14px; font-weight:700; font-size:12px; }}
  .pill {{ display:inline-block; border-radius:999px; padding:4px 10px; font-size:12px; font-weight:600; }}
  .swatches {{ display:grid; grid-template-columns:1fr; gap:8px; }}
  .swatch {{ display:flex; align-items:center; gap:10px; font-size:12px; }}
  .chip {{ width:28px; height:28px; border-radius:6px; border:1px solid rgba(128,128,128,.35); flex-shrink:0; }}
  .meta {{ display:flex; flex-direction:column; line-height:1.25; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Chroma Engine v4.1 — {brand_esc} / {vslug} ({varch})</h1>
    <p class="sub">Auditoría física WCAG 2.2 AAA (≥7:1 texto, ≥4.5:1 botón) + APCA (Lc ≥75) · Oráculo 15 Shards + Vertical.</p>
  </header>
  {"".join(sections)}
</div>
</body>
</html>"""


def generate_chroma_manifest(
    brand: str,
    brief_path: Optional[Path] = None,
    shards_path: Optional[Path] = None,
    vertical_json_path: Optional[Path] = None,
    selected_eco_id: Optional[str] = None,
    vertical_slug: Optional[str] = None,
    mode: str = "auto",
) -> Dict[str, Any]:
    brand_upper = re.sub(r"[^a-zA-Z0-9_-]+", "", brand.strip()).upper() or "BRAND"
    signals = extract_oraculo_and_vertical_signals(brief_path, shards_path, vertical_json_path, vertical_slug=vertical_slug)

    use_brief_literal = (
        mode == "brief"
        or (mode == "auto" and not (shards_path and shards_path.is_file()) and not (vertical_json_path and vertical_json_path.is_file()))
    )

    if use_brief_literal and brief_path and brief_path.is_file():
        ecosystems = parse_ecosystems_from_brief(brief_path.read_text(encoding="utf-8", errors="replace"))
        source_ssot = f"{brief_path.name} §3 (literal)"
    else:
        ecosystems = synthesize_multiaxis_ecosystems(signals)
        source_ssot = " + ".join(signals["sources"]) or "oraculo_multiaxis_synthesizer"

    if not ecosystems:
        ecosystems = synthesize_multiaxis_ecosystems(signals)
        source_ssot = "oraculo_multiaxis_synthesizer"

    selected = next((e for e in ecosystems if e["id"] == selected_eco_id), ecosystems[0])
    sel_audit = _audit_ecosystem(selected["themes"])
    sel_dark = sel_audit["dark"]

    manifest: Dict[str, Any] = {
        "$schema": "https://www.designtokens.org/tr/2025.10/color/",
        "brand": brand_upper,
        "vertical_archetype": signals["vertical_archetype"],
        "engine": "chroma_engine.py v4.1 (Oráculo 15-Shards + 5-Tier Vertical Anti-Slop)",
        "color_space": "oklch",
        "selected_ecosystem_id": selected["id"],
        "recommended_mode": selected.get("recommended_mode", "light"),
        "source_ssot": source_ssot,
        "inputs_used": signals,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ecosystems": ecosystems,
        "themes": selected["themes"],
        "accessibility_audit": {
            "wcag_2_2_compliance": {
                "body_to_bg_ratio": sel_audit["wcag_aaa_ratio"],
                "headings_to_bg_ratio": sel_dark["headings_to_bg_ratio"],
                "button_to_bg_ratio": min(sel_dark["button_to_bg_ratio"], sel_audit["light"]["button_to_bg_ratio"]),
                "status_aaa": sel_audit["status_aaa"],
            },
            "apca_compliance": {
                "body_lc": sel_audit["apca_lc"],
                "headings_lc": sel_dark["headings_lc"],
                "ui_components_lc": sel_dark["ui_components_lc"],
            },
        },
        "css_integration": build_css_blocks(selected),
    }
    if vertical_slug or signals.get("vertical_slug"):
        manifest["vertical_slug"] = vertical_slug or signals.get("vertical_slug")
    return manifest


def run_unit_tests() -> int:
    print("Running chroma_engine v4.1 unit tests...")
    with tempfile.TemporaryDirectory(prefix="chroma_v41_test_") as tmp:
        tp = Path(tmp)
        shards_p = tp / "client_dumps_15_shards.json"
        brief_p = tp / "astrobranding_testcorp.md"
        vert_b2b = tp / "juan-damaren.json"
        vert_cos = tp / "astrotipia.json"

        shards_p.write_text(json.dumps({
            "shard_01": {"data": {
                "arroyo_elements": {"dominant_element": "Air"},
                "planets": {"Sun": {"longitude": 79.01}, "Venus": {"longitude": 77.31, "sign": "Gemini"}},
                "tripod_of_iron": {"sun": {"sign": "Gemini"}, "midheaven_house_10": {"sign": "Gemini"}},
            }},
            "shard_02": {"data": {"fagan_bradley": {"sun": {"sign": "Taurus"}, "midheaven": {"sign": "Taurus"}, "ascendant": {"sign": "Leo"}}}},
            "shard_03": {"data": {"shadbala": {"dominant_planet": "Sun", "max_rupas": 9.85}, "nakshatra": {"name": "Chitra Pada 4", "lord": "Mars"}}},
            "shard_04": {"data": {"day_master": {"name": "Jia", "element": "Wood"}, "four_pillars": {"month": {"element": "Metal"}}, "yong_shen": {"element": "Water"}}},
        }), encoding="utf-8")
        # Intentionally include a trap Spanish sentence matching "Yong Shen: La tinta" to test overwrite guard!
        brief_p.write_text("# Brief\n**Elemento balancín Yong Shen:** La tinta abisal.\n", encoding="utf-8")
        vert_b2b.write_text(json.dumps({"vertical_slug": "acme-b2b", "display_name": "Consultoría B2B e IA", "category": "b2b"}), encoding="utf-8")
        vert_cos.write_text(json.dumps({"vertical_slug": "astrotipia", "display_name": "Astrotipia — Sabidurías Cósmicas & Arquetipos Vocacionales"}), encoding="utf-8")

        m_b2b = generate_chroma_manifest("TESTCORP", brief_path=brief_p, shards_path=shards_p, vertical_json_path=vert_b2b, mode="synthesize")
        m_cos = generate_chroma_manifest("TESTCORP", brief_path=brief_p, shards_path=shards_p, vertical_json_path=vert_cos, mode="synthesize")

        assert m_b2b["inputs_used"]["yong_shen"] == "Water", f"yong_shen overwritten: {m_b2b['inputs_used']['yong_shen']}"
        assert m_b2b["vertical_archetype"] == "architectural_b2b"
        assert m_cos["vertical_archetype"] == "cosmic_archetypal"
        assert m_b2b["selected_ecosystem_id"] != m_cos["selected_ecosystem_id"]
        assert m_b2b["recommended_mode"] == "light" and m_cos["recommended_mode"] == "dark"
        assert m_b2b["themes"]["light"]["primary"]["hex"] != m_cos["themes"]["dark"]["primary"]["hex"]

        for man in (m_b2b, m_cos):
            for eco in man["ecosystems"]:
                assert eco["audit"]["wcag_aaa_ratio"] >= 7.0
                assert eco["audit"]["apca_lc"] >= 75.0
                for mode_name in ("dark", "light"):
                    t = eco["themes"][mode_name]
                    btn_ratio = wcag_contrast_ratio(t["background"]["hex"], t["primary"]["hex"])
                    assert btn_ratio >= 4.5, f"Button contrast < 4.5 in {eco['id']} {mode_name}: {btn_ratio}"
                    for tok in t.values():
                        assert tok["hex"].lower() not in BANNED_SLOP_HEXES, f"Banned slop hex {tok['hex']}"

        assert "Chroma Engine v4.1" in render_chroma_preview_html(m_cos)
    assert not Path("/mnt/localstorage/TESTCORP").exists()
    print("✅ CHROMA ENGINE v4.1 UNIT TESTS PASSED (Multi-vertical differentiation, Water preserved, >=4.5:1 buttons, 0 slop hexes, 0 phantom dirs)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Chroma Engine v4.1 — Sovereign OKLCH & WCAG AAA/APCA Synthesizer")
    parser.add_argument("--brand", default="BRAND")
    parser.add_argument("--vertical", default=None)
    parser.add_argument("--brief", type=Path, default=None)
    parser.add_argument("--shards", type=Path, default=None)
    parser.add_argument("--vertical-json", type=Path, default=None)
    parser.add_argument("--mode", default="auto", choices=["auto", "synthesize", "brief"])
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--eco", default=None)
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        return run_unit_tests()

    manifest = generate_chroma_manifest(
        brand=args.brand,
        brief_path=args.brief,
        shards_path=args.shards,
        vertical_json_path=args.vertical_json,
        selected_eco_id=args.eco,
        vertical_slug=args.vertical,
        mode=args.mode,
    )

    if args.dry_run:
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0

    out_dir = (args.output_dir or Path.cwd()).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "chroma_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not args.no_preview:
        (out_dir / "chroma_preview.html").write_text(render_chroma_preview_html(manifest), encoding="utf-8")

    audit = manifest["accessibility_audit"]
    print(f"✅ CHROMA ENGINE v4.1 COMPLETED FOR: {manifest['brand']}/{manifest.get('vertical_slug', 'root')} (arch={manifest['vertical_archetype']}, selected={manifest['selected_ecosystem_id']}, default={manifest['recommended_mode']})")
    print(f"  • Source SSoT: {manifest['source_ssot']}")
    print(f"  • WCAG 2.2 AAA: {audit['wcag_2_2_compliance']['body_to_bg_ratio']}:1 | Btn: {audit['wcag_2_2_compliance']['button_to_bg_ratio']}:1 | APCA Lc: {audit['apca_compliance']['body_lc']}")
    print(f"  • Output: {out_dir / 'chroma_manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
