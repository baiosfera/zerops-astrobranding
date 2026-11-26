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
import hashlib
import html as html_lib
import json
import math
import re
import shutil
import subprocess
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


def hex_to_oklch(hex_str: str) -> Tuple[float, float, float]:
    """Converts sRGB hex to exact OKLCH (L, C, H)."""
    r_i, g_i, b_i = hex_to_rgb_int(hex_str)
    def _lin(ch: int) -> float:
        s = ch / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = _lin(r_i), _lin(g_i), _lin(b_i)
    l_ = math.cbrt(max(0.0, 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b))
    m_ = math.cbrt(max(0.0, 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b))
    s_ = math.cbrt(max(0.0, 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b))
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    C = math.hypot(A, B)
    H = (math.degrees(math.atan2(B, A)) % 360.0) if C > 1e-5 else 0.0
    return round(L, 3), round(C, 3), round(H, 1)


def token_from_hex(hex_str: str, desc: str) -> Dict[str, Any]:
    """Builds a W3C DTCG color token preserving the exact input hex."""
    h_clean = "#" + re.sub(r"[^0-9a-fA-F]", "", hex_str.strip())[:6].lower()
    if len(h_clean) != 7:
        h_clean = "#000000"
    l, c, h = hex_to_oklch(h_clean)
    return make_color_token(l, c, h, desc, hex_override=h_clean)


def pick_on_color(bg_hex: str, desc: str = "Texto legible sobre color de marca") -> Dict[str, Any]:
    """Selects pure white or near-black ink guaranteeing >= 4.5:1 WCAG contrast on vivid surfaces."""
    dark_ink = "#0a0a0a"
    light_ink = "#ffffff"
    r_dark = wcag_contrast_ratio(dark_ink, bg_hex)
    r_light = wcag_contrast_ratio(light_ink, bg_hex)
    chosen = dark_ink if r_dark >= r_light else light_ink
    return token_from_hex(chosen, desc)


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
    on_p_dark = (dark.get("on_primary") or dark["background"])["hex"]
    btn_dark = wcag_contrast_ratio(on_p_dark, dark["primary"]["hex"])
    lc_body_dark = apca_contrast_lc(dark["text_primary"]["hex"], dark["background"]["hex"])
    lc_head_dark = apca_contrast_lc(dark["primary"]["hex"], dark["background"]["hex"])
    lc_ui_dark = apca_contrast_lc(dark["accent"]["hex"], dark["surface"]["hex"])

    body_light = wcag_contrast_ratio(light["text_primary"]["hex"], light["background"]["hex"])
    head_light = wcag_contrast_ratio(light["primary"]["hex"], light["background"]["hex"])
    on_p_light = (light.get("on_primary") or light["background"])["hex"]
    btn_light = wcag_contrast_ratio(on_p_light, light["primary"]["hex"])
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
        "status_aaa": worst_body_ratio >= 7.0 and worst_body_lc >= 75.0 and min(btn_dark, btn_light) >= 4.5,
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
        make_color_token(0.42, min(0.22, max(0.03, p_c_val := p_comp["chroma"])), p_comp["hue"], f"{dark_theme['primary']['$description']} (Light CTA)"),
        bg_light["hex"], is_dark_bg=False, min_wcag=4.6, min_lc=55.0
    )
    sec_light = make_color_token(0.49, min(0.14, max(0.02, s_comp["chroma"])), s_comp["hue"], f"{dark_theme['secondary']['$description']} (Light)")
    acc_light = _ensure_aaa_contrast(
        make_color_token(0.38, min(0.21, max(0.03, a_comp["chroma"])), a_comp["hue"], f"{dark_theme['accent']['$description']} (Light Accent)"),
        surf_light["hex"], is_dark_bg=False, min_wcag=4.6, min_lc=55.0
    )
    _ = p_c_val
    return {
        "primary": prim_light,
        "on_primary": pick_on_color(prim_light["hex"], "Texto sobre botón primario claro"),
        "secondary": sec_light,
        "accent": acc_light,
        "on_accent": pick_on_color(acc_light["hex"], "Texto sobre acento claro"),
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
    """Builds a high-conviction Light + Dark ecosystem preserving saturated primaries + explicit on_primary/on_accent."""
    p_c = min(0.24, max(0.02, primary_chroma))
    n_c = min(0.024, max(0.002, neutral_chroma))

    bg_d = make_color_token(dark_bg_l, n_c * 0.72, neutral_hue, "Lienzo oscuro calibrado")
    surf_d = make_color_token(dark_bg_l + 0.055, n_c * 0.9, neutral_hue, "Superficie elevada")
    txt_d = _ensure_aaa_contrast(
        make_color_token(0.968, min(0.008, n_c * 0.4), neutral_hue, "Texto principal nítido"),
        bg_d["hex"], is_dark_bg=True, min_wcag=12.0, min_lc=94.0
    )
    muted_d = _ensure_aaa_contrast(
        make_color_token(0.70, n_c * 1.0, neutral_hue, "Texto secundario legible"),
        bg_d["hex"], is_dark_bg=True, min_wcag=4.8, min_lc=55.0
    )
    prim_d = _ensure_aaa_contrast(
        make_color_token(0.68, min(0.21, p_c), primary_hue, "Acento primario interactivo"),
        bg_d["hex"], is_dark_bg=True, min_wcag=4.8, min_lc=58.0
    )
    sec_d = make_color_token(0.56, min(0.11, p_c * 0.65), (primary_hue + 14.0) % 360.0, "Secundario estructural")
    acc_d = _ensure_aaa_contrast(
        make_color_token(0.75, min(0.20, p_c * 0.92), accent_hue, "Acento de foco / estado"),
        surf_d["hex"], is_dark_bg=True, min_wcag=4.8, min_lc=58.0
    )
    dark_theme = {
        "primary": prim_d,
        "on_primary": pick_on_color(prim_d["hex"], "Texto sobre botón primario oscuro"),
        "secondary": sec_d,
        "accent": acc_d,
        "on_accent": pick_on_color(acc_d["hex"], "Texto sobre acento oscuro"),
        "background": bg_d, "surface": surf_d, "text_primary": txt_d, "text_muted": muted_d,
    }

    bg_l = make_color_token(light_bg_l, light_bg_c, neutral_hue, "Lienzo claro arquitectónico")
    surf_l = make_color_token(light_surf_l, min(0.015, light_bg_c + 0.005), neutral_hue, "Superficie elevada clara")
    txt_l = _ensure_aaa_contrast(
        make_color_token(0.155, min(0.016, n_c * 0.85), neutral_hue, "Tinta principal"),
        bg_l["hex"], is_dark_bg=False, min_wcag=12.0, min_lc=94.0
    )
    muted_l = _ensure_aaa_contrast(
        make_color_token(0.445, n_c * 1.0, neutral_hue, "Texto secundario claro"),
        bg_l["hex"], is_dark_bg=False, min_wcag=4.8, min_lc=55.0
    )
    prim_l = _ensure_aaa_contrast(
        make_color_token(0.45, min(0.22, p_c * 1.15), primary_hue, "Acento primario sobre claro"),
        bg_l["hex"], is_dark_bg=False, min_wcag=4.6, min_lc=55.0
    )
    sec_l = make_color_token(0.52, min(0.12, p_c * 0.65), (primary_hue + 14.0) % 360.0, "Secundario estructural claro")
    acc_l = _ensure_aaa_contrast(
        make_color_token(0.42, min(0.22, p_c), accent_hue, "Acento de estado claro"),
        surf_l["hex"], is_dark_bg=False, min_wcag=4.6, min_lc=55.0
    )
    light_theme = {
        "primary": prim_l,
        "on_primary": pick_on_color(prim_l["hex"], "Texto sobre botón primario claro"),
        "secondary": sec_l,
        "accent": acc_l,
        "on_accent": pick_on_color(acc_l["hex"], "Texto sobre acento claro"),
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


def _extract_vertical_identity_blob(vdata: Dict[str, Any]) -> str:
    """Extract only primary vertical identity fields; exclude cross-vertical exclusion disclaimers."""
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


def classify_vertical_archetype(vblob: str, vertical_slug: str = "") -> str:
    """5-tier brand-agnostic classifier driving distinct aesthetics under one umbrella chart."""
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


# -----------------------------------------------------------------------------
# Signal Extraction: Oráculo 15-Shards + Vertical JSON + Brief Markdown
# -----------------------------------------------------------------------------

SPANISH_SIGN_MAP = {
    "aries": "Aries",
    "tauro": "Taurus", "taurus": "Taurus",
    "geminis": "Gemini", "géminis": "Gemini", "gemini": "Gemini",
    "cancer": "Cancer", "cáncer": "Cancer",
    "leo": "Leo",
    "virgo": "Virgo",
    "libra": "Libra",
    "escorpio": "Scorpio", "scorpio": "Scorpio",
    "sagitario": "Sagittarius", "sagittarius": "Sagittarius",
    "capricornio": "Capricorn", "capricorn": "Capricorn",
    "acuario": "Aquarius", "aquarius": "Aquarius",
    "piscis": "Pisces", "pisces": "Pisces",
}


def _norm_sign(raw: str, default: str = "") -> str:
    tok = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚ]", "", str(raw or "").strip()).lower()
    return SPANISH_SIGN_MAP.get(tok, default or (str(raw or "").strip().title()))


def _collect_sibling_chroma_info(sibling_workspaces_dir: Optional[Path], own_output_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    info: List[Dict[str, Any]] = []
    if not sibling_workspaces_dir or not sibling_workspaces_dir.is_dir():
        return info
    own_res = own_output_dir.resolve() if own_output_dir else None
    for child in sorted(sibling_workspaces_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        brand_dir = (child / "brand").resolve()
        if own_res and brand_dir == own_res:
            continue
        cm_path = brand_dir / "chroma_manifest.json"
        if not cm_path.is_file():
            continue
        try:
            cm = json.loads(cm_path.read_text(encoding="utf-8"))
            sel_id = str(cm.get("selected_ecosystem_id") or "")
            arch = str(cm.get("vertical_archetype") or "")
            p_hex = cm.get("themes", {}).get("dark", {}).get("primary", {}).get("hex") or cm.get("themes", {}).get("light", {}).get("primary", {}).get("hex") or ""
            p_hue = hex_to_oklch(p_hex)[2] if p_hex else None
            info.append({"vertical": child.name, "selected_id": sel_id, "archetype": arch, "primary_hue": p_hue})
        except Exception:
            pass
    return info


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
    shards_had_mc = False
    shards_had_dm = False
    shards_had_nak = False

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
            sig["sun_sign"] = _norm_sign(str(tripod["sun"]["sign"]), "Scorpio")
            shards_had_sun = True
        if tripod.get("midheaven_house_10", {}).get("sign"):
            sig["mc_sign"] = _norm_sign(str(tripod["midheaven_house_10"]["sign"]), "Leo")
            shards_had_mc = True
        if planets.get("Venus", {}).get("longitude") is not None:
            sig["venus_deg"] = float(planets["Venus"]["longitude"])
        if planets.get("Venus", {}).get("sign"):
            sig["venus_sign"] = _norm_sign(str(planets["Venus"]["sign"]), "Scorpio")
        if arroyo.get("dominant_element"):
            sig["dominant_element"] = _norm_element(arroyo["dominant_element"], "Earth")
            shards_had_el = True

        fb = s2.get("fagan_bradley", {})
        if fb.get("sun", {}).get("sign") or fb.get("planets", {}).get("Sun", {}).get("sign"):
            sig["sidereal_sun_sign"] = _norm_sign(str((fb.get("sun") or fb.get("planets", {}).get("Sun", {})).get("sign", "")))
        if fb.get("midheaven", {}).get("sign"):
            sig["sidereal_mc_sign"] = _norm_sign(str(fb["midheaven"]["sign"]))
        if fb.get("ascendant", {}).get("sign"):
            sig["sidereal_asc_sign"] = _norm_sign(str(fb["ascendant"]["sign"]))

        sh = s3.get("shadbala", {})
        if sh.get("dominant_planet"):
            sig["vedic_shadbala_planet"] = str(sh["dominant_planet"])
        if sh.get("max_rupas"):
            sig["vedic_shadbala_rupas"] = round(float(sh["max_rupas"]), 2)
        nk = s3.get("nakshatra", {})
        if nk.get("name"):
            sig["nakshatra"] = str(nk["name"]).split()[0]
            shards_had_nak = True
        if nk.get("lord") or nk.get("ruler"):
            sig["nakshatra_lord"] = str(nk.get("lord") or nk.get("ruler"))

        dm = s4.get("day_master", {})
        if dm.get("name"):
            sig["bazi_day_master"] = str(dm["name"]).split()[0]
            shards_had_dm = True
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
            m_sun_l = re.search(r"Longitud solar[^:\n]*:\s*([\d.]+)", txt, re.IGNORECASE)
            if m_sun_l:
                sig["sun_lon"] = float(m_sun_l.group(1))
            m_sun_s = re.search(r"\|\s*\*\*Sol Natal\*\*\s*\|\s*\*\*([A-Za-zÁÉÍÓÚáéíóú]+)", txt) or re.search(
                r"(?:Sun Natal|Sol Natal|Sol)[\s:\*|]+(?:en\s+\*\*)?([A-Za-zÁÉÍÓÚáéíóú]+)", txt, re.IGNORECASE
            )
            if m_sun_s:
                sig["sun_sign"] = _norm_sign(m_sun_s.group(1), sig["sun_sign"])
        if not shards_had_mc:
            m_mc = re.search(r"\|\s*\*\*Medio Cielo[^*]*\*\*\s*\|\s*\*\*([A-Za-zÁÉÍÓÚáéíóú]+)", txt) or re.search(
                r"(?:Midheaven|Medio Cielo)[\s:\*|]+(?:en\s+\*\*)?([A-Za-zÁÉÍÓÚáéíóú]+)", txt, re.IGNORECASE
            )
            if m_mc:
                sig["mc_sign"] = _norm_sign(m_mc.group(1), sig["mc_sign"])
        if not shards_had_nak:
            m_nak = re.search(r"\*\*Nakshatra[^:\n]*:\*\*\s*([A-Za-z]+)", txt)
            if m_nak:
                sig["nakshatra"] = m_nak.group(1).strip()
        if not shards_had_dm:
            m_dm = re.search(r"\*\*Day Master:\*\*\s*([A-Za-z]+)", txt)
            if m_dm:
                sig["bazi_day_master"] = m_dm.group(1).strip()
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
        vblob = _extract_vertical_identity_blob(vdata)
        sig["vertical_display_name"] = str(vdata.get("display_name") or "")
        sig["vertical_slug"] = str(vdata.get("vertical_slug") or vertical_slug or vertical_json_path.stem)
        sig["vertical_category"] = str(vdata.get("category") or vdata.get("category_and_positioning", {}).get("category_name") or "")
        arch = str(vdata.get("vertical_archetype") or "") or classify_vertical_archetype(vblob, sig["vertical_slug"])
        sig["vertical_archetype"] = arch
        sig["vertical_is_b2b"] = arch == "architectural_b2b"
    elif vertical_slug:
        sig["vertical_archetype"] = classify_vertical_archetype("", vertical_slug)
        sig["vertical_is_b2b"] = sig["vertical_archetype"] == "architectural_b2b"

    return sig


def synthesize_multiaxis_ecosystems(
    sig: Dict[str, Any],
    sibling_info: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Synthesizes 3 differentiated visual worlds calibrated BOTH to Oráculo coordinates
    AND the vertical's commercial/psychological archetype (`vertical_archetype`),
    applying deterministic per-vertical hue shifts and sibling rotation when siblings share an archetype.
    """
    ys = sig.get("yong_shen", "Water")
    dom_el = sig.get("dominant_element", "Earth")
    nak_lord = sig.get("nakshatra_lord", "Mars")
    sh_planet = sig.get("vedic_shadbala_planet", "Sun")
    bazi_day = sig.get("bazi_day_element", "Wood")
    sun_lon = float(sig.get("sun_lon", 79.0))
    venus_deg = float(sig.get("venus_deg", 77.3))
    arch = sig.get("vertical_archetype", "editorial_brand")
    vslug = str(sig.get("vertical_slug") or "").strip().lower()
    sibs = sibling_info or []
    same_arch_sibs = [s for s in sibs if s.get("archetype") == arch]
    v_hash = hashlib.sha256(vslug.encode("utf-8")).digest()[0] if vslug else 0
    hue_shift = ((v_hash % 5) * 18.0) if same_arch_sibs else 0.0

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
        ecos = [eco1, eco2, eco3]
    elif arch in ("design_system_atelier", "editorial_manifesto"):
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
        ecos = [eco1, eco2, eco3]
    else:
        # Default / architectural_b2b (Light-first cool porcelain + deep cobalt; Carbon+Mars; Viridian+Bone)
        ys_hue = ELEMENT_BASE_HUES.get(ys, 236.0)
        h1_prim = 262.0 if ys == "Water" and sig.get("vertical_is_b2b") else (ys_hue + (sun_lon % 18.0) - 9.0) % 360.0
        h1_prim = (h1_prim + hue_shift) % 360.0
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
        ecos = [eco1, eco2, eco3]

    used_sel_ids = {s.get("selected_id") for s in sibs if s.get("selected_id")}
    if same_arch_sibs and ecos[0]["id"] in used_sel_ids:
        for alt_i in range(1, len(ecos)):
            if ecos[alt_i]["id"] not in used_sel_ids:
                ecos = ecos[alt_i:] + ecos[:alt_i]
                break
    return ecos


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


def _compose_curated_mode_tokens(spec: Dict[str, Any], is_dark: bool) -> Dict[str, Dict[str, Any]]:
    """Preserves exact curated hexes for primary/accent/background/surface and computes accessible on_*."""
    bg_hex = spec.get("background") or ("#0b0d11" if is_dark else "#f9fafb")
    surf_hex = spec.get("surface") or ("#151820" if is_dark else "#eef1f5")
    prim_hex = spec.get("primary") or ("#63a4ff" if is_dark else "#1d4ed8")
    acc_hex = spec.get("accent") or prim_hex
    sec_hex = spec.get("secondary") or acc_hex
    txt_hex = spec.get("text_primary") or ("#f4f5f7" if is_dark else "#0e1116")
    mut_hex = spec.get("text_muted") or ("#9aa3b2" if is_dark else "#4b5563")

    bg_tok = token_from_hex(bg_hex, "Lienzo de dirección de arte")
    surf_tok = token_from_hex(surf_hex, "Superficie curada")
    prim_tok = token_from_hex(prim_hex, "Color primario curado")
    acc_tok = token_from_hex(acc_hex, "Color acento curado")
    sec_tok = token_from_hex(sec_hex, "Color secundario curado")

    txt_tok = token_from_hex(txt_hex, "Texto principal")
    if wcag_contrast_ratio(txt_tok["hex"], bg_tok["hex"]) < 7.0 or apca_contrast_lc(txt_tok["hex"], bg_tok["hex"]) < 75.0:
        txt_tok = _ensure_aaa_contrast(txt_tok, bg_tok["hex"], is_dark_bg=is_dark, min_wcag=10.5, min_lc=85.0)

    mut_tok = token_from_hex(mut_hex, "Texto secundario")
    if wcag_contrast_ratio(mut_tok["hex"], bg_tok["hex"]) < 4.5:
        mut_tok = _ensure_aaa_contrast(mut_tok, bg_tok["hex"], is_dark_bg=is_dark, min_wcag=4.6, min_lc=52.0)

    on_prim = (
        token_from_hex(spec["on_primary"], "Texto sobre botón primario")
        if spec.get("on_primary") and wcag_contrast_ratio(spec["on_primary"], prim_tok["hex"]) >= 4.5
        else pick_on_color(prim_tok["hex"], "Texto sobre botón primario")
    )
    on_acc = (
        token_from_hex(spec["on_accent"], "Texto sobre acento")
        if spec.get("on_accent") and wcag_contrast_ratio(spec["on_accent"], acc_tok["hex"]) >= 4.5
        else pick_on_color(acc_tok["hex"], "Texto sobre acento")
    )
    return {
        "primary": prim_tok,
        "on_primary": on_prim,
        "secondary": sec_tok,
        "accent": acc_tok,
        "on_accent": on_acc,
        "background": bg_tok,
        "surface": surf_tok,
        "text_primary": txt_tok,
        "text_muted": mut_tok,
    }


def _build_ecosystem_from_curated(idx: int, spec: Dict[str, Any]) -> Dict[str, Any]:
    eco_id = str(spec.get("id") or f"eco_{idx + 1}_art_direction")
    name = str(spec.get("name") or f"Dirección de Arte {idx + 1}")
    concept = str(spec.get("concept") or "Paleta curada con contraste real de marca.")
    rec_mode = str(spec.get("recommended_mode") or "light").lower()
    if rec_mode not in ("light", "dark"):
        rec_mode = "light"

    if "light" in spec or "dark" in spec:
        l_spec = spec.get("light") or {}
        d_spec = spec.get("dark") or {}
        if l_spec and not d_spec:
            light_t = _compose_curated_mode_tokens(l_spec, is_dark=False)
            l_p, c_p, h_p = hex_to_oklch(light_t["primary"]["hex"])
            l_a, c_a, h_a = hex_to_oklch(light_t["accent"]["hex"])
            _, _, h_n = hex_to_oklch(light_t["background"]["hex"])
            d_bg = make_color_token(0.115, 0.008, h_n, "Lienzo oscuro derivado").get("hex")
            d_sf = make_color_token(0.175, 0.011, h_n, "Superficie oscura derivada").get("hex")
            d_pr = make_color_token(max(0.62, l_p), max(0.08, c_p * 0.92), h_p, "Primario oscuro").get("hex")
            d_ac = make_color_token(max(0.65, l_a), max(0.08, c_a * 0.92), h_a, "Acento oscuro").get("hex")
            dark_t = _compose_curated_mode_tokens({"background": d_bg, "surface": d_sf, "primary": d_pr, "accent": d_ac}, is_dark=True)
        elif d_spec and not l_spec:
            dark_t = _compose_curated_mode_tokens(d_spec, is_dark=True)
            l_p, c_p, h_p = hex_to_oklch(dark_t["primary"]["hex"])
            l_a, c_a, h_a = hex_to_oklch(dark_t["accent"]["hex"])
            _, _, h_n = hex_to_oklch(dark_t["background"]["hex"])
            l_bg = make_color_token(0.985, 0.004, h_n, "Lienzo claro derivado").get("hex")
            l_sf = make_color_token(0.945, 0.008, h_n, "Superficie clara derivada").get("hex")
            l_pr = make_color_token(min(0.55, l_p), max(0.08, c_p), h_p, "Primario claro").get("hex")
            l_ac = make_color_token(min(0.52, l_a), max(0.08, c_a), h_a, "Acento claro").get("hex")
            light_t = _compose_curated_mode_tokens({"background": l_bg, "surface": l_sf, "primary": l_pr, "accent": l_ac}, is_dark=False)
        else:
            light_t = _compose_curated_mode_tokens(l_spec, is_dark=False)
            dark_t = _compose_curated_mode_tokens(d_spec, is_dark=True)
    else:
        bg_luma = wcag_relative_luminance(spec.get("background", "#ffffff"))
        base_is_dark = bg_luma < 0.25
        if base_is_dark:
            rec_mode = str(spec.get("recommended_mode") or "dark").lower()
            return _build_ecosystem_from_curated(idx, {**spec, "recommended_mode": rec_mode, "dark": spec})
        return _build_ecosystem_from_curated(idx, {**spec, "recommended_mode": rec_mode, "light": spec})

    themes = {"dark": dark_t, "light": light_t}
    audit = _audit_ecosystem(themes)
    return {
        "id": eco_id,
        "name": name,
        "recommended_mode": rec_mode,
        "concept": concept,
        "derivation_parameters": {"mode": "curated_art_direction", "preserved_exact_hexes": True},
        "themes": themes,
        "audit": audit,
    }


def compose_ecosystems_from_palette_json(palette_path: Path) -> List[Dict[str, Any]]:
    raw = json.loads(palette_path.read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw.get("ecosystems") or raw.get("palettes") or [raw]
    out: List[Dict[str, Any]] = []
    for i, item in enumerate(items[:3]):
        if isinstance(item, dict):
            out.append(_build_ecosystem_from_curated(i, item))
    return out


def compose_ecosystems_from_seed_hex(seed_hex: str, bg_hex: Optional[str] = None, accent_hex: Optional[str] = None) -> List[Dict[str, Any]]:
    _, c, h = hex_to_oklch(seed_hex)
    comp_h = (h + 155.0) % 360.0
    bg_l = bg_hex or "#fafaf8"
    acc_h = accent_hex or seed_hex
    eco1 = _build_ecosystem_from_curated(0, {
        "id": "eco_1_editorial_conviction",
        "name": "Convingente & Puro (Seed Curado)",
        "recommended_mode": "light" if wcag_relative_luminance(bg_l) >= 0.25 else "dark",
        "concept": "Dirección de arte centrada en el color semilla exacto con CTA de máximo contraste.",
        "background": bg_l,
        "surface": "#eff2f6" if wcag_relative_luminance(bg_l) >= 0.25 else "#161920",
        "primary": seed_hex,
        "accent": acc_h,
    })
    _, c_comp, _ = hex_to_oklch(acc_h)
    eco2 = _compose_intentional_ecosystem(
        eco_id="eco_2_nocturnal_tension",
        name="Oscuro de Tensión & Complemento",
        concept="Fondo carbón neutro con tensión complementaria al color semilla.",
        recommended_mode="dark",
        primary_hue=h, primary_chroma=max(0.14, c),
        accent_hue=comp_h, neutral_hue=h, neutral_chroma=0.008,
    )
    eco3 = _compose_intentional_ecosystem(
        eco_id="eco_3_split_editorial",
        name="Papel Cálido/Frío & Complemento Editorial",
        concept="Alternativa editorial luminosa con acento secundario contrastado.",
        recommended_mode="light",
        primary_hue=comp_h, primary_chroma=max(0.13, c_comp),
        accent_hue=h, neutral_hue=comp_h, neutral_chroma=0.010,
    )
    ecos = [eco1, eco2, eco3]
    used_sel_ids = {s.get("selected_id") for s in sibs if s.get("selected_id")}
    if same_arch_sibs and ecos[0]["id"] in used_sel_ids:
        for alt_i in range(1, len(ecos)):
            if ecos[alt_i]["id"] not in used_sel_ids:
                ecos = ecos[alt_i:] + ecos[:alt_i]
                break
    return ecos


def build_css_blocks(selected: Dict[str, Any]) -> Dict[str, str]:
    d = selected["themes"]["dark"]
    lt = selected["themes"]["light"]
    default_mode = selected.get("recommended_mode", "light")
    root_src, alt_src, alt_attr = (lt, d, '[data-theme="dark"]') if default_mode == "light" else (d, lt, '[data-theme="light"]')
    r_on_p = (root_src.get("on_primary") or root_src["background"])["$value"]
    r_on_a = (root_src.get("on_accent") or root_src["background"])["$value"]
    a_on_p = (alt_src.get("on_primary") or alt_src["background"])["$value"]
    a_on_a = (alt_src.get("on_accent") or alt_src["background"])["$value"]
    tailwind_block = (
        "@theme {\n"
        "  --color-brand-primary: var(--brand-primary);\n"
        "  --color-brand-on-primary: var(--brand-on-primary);\n"
        "  --color-brand-secondary: var(--brand-secondary);\n"
        "  --color-brand-accent: var(--brand-accent);\n"
        "  --color-brand-on-accent: var(--brand-on-accent);\n"
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
        f"  --brand-on-primary: {r_on_p};\n"
        f"  --brand-secondary: {root_src['secondary']['$value']};\n"
        f"  --brand-accent: {root_src['accent']['$value']};\n"
        f"  --brand-on-accent: {r_on_a};\n"
        f"  --brand-bg: {root_src['background']['$value']};\n"
        f"  --brand-surface: {root_src['surface']['$value']};\n"
        f"  --brand-text: {root_src['text_primary']['$value']};\n"
        f"  --brand-muted: {root_src['text_muted']['$value']};\n"
        "}\n"
        f"{alt_attr} {{\n"
        f"  --brand-primary: {alt_src['primary']['$value']};\n"
        f"  --brand-on-primary: {a_on_p};\n"
        f"  --brand-secondary: {alt_src['secondary']['$value']};\n"
        f"  --brand-accent: {alt_src['accent']['$value']};\n"
        f"  --brand-on-accent: {a_on_a};\n"
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
    inputs = manifest.get("inputs_used") or {}
    vslug = html_lib.escape(str(manifest.get("vertical_slug") or manifest.get("brand", "")))
    vdisp = html_lib.escape(str(inputs.get("vertical_display_name") or vslug))
    varch = html_lib.escape(str(manifest.get("vertical_archetype") or "editorial_brand"))
    sel_id = manifest.get("selected_ecosystem_id", "")

    oraculo_badge = html_lib.escape(
        f"Sol {inputs.get('sun_sign','-')} · MC {inputs.get('mc_sign','-')} · "
        f"Sideral {inputs.get('sidereal_mc_sign') or inputs.get('mc_sign','-')} · "
        f"Shadbala {inputs.get('vedic_shadbala_planet','-')} · Nakshatra {inputs.get('nakshatra','-')} · "
        f"BaZi {inputs.get('bazi_day_master','-')} (Mes {inputs.get('bazi_month_element','-')}) · "
        f"Yong Shen {inputs.get('yong_shen','-')}"
    )

    sections: List[str] = []
    eco_buttons: List[str] = []
    ecos = manifest.get("ecosystems", [])

    for eco in ecos:
        eid = html_lib.escape(eco["id"])
        ename = html_lib.escape(eco["name"])
        econ = html_lib.escape(eco["concept"])
        rmode = html_lib.escape(str(eco.get("recommended_mode", "light")).upper())
        badge = " · SELECCIONADO" if eco["id"] == sel_id else ""
        audit = eco.get("audit", {})
        params_json = html_lib.escape(json.dumps(eco.get("derivation_parameters", {}), ensure_ascii=False))
        eco_buttons.append(f'<button type="button" class="ctrl-btn eco-btn" data-eco-filter="{eid}">{ename}</button>')

        mode_cards: List[str] = []
        order = ("light", "dark") if eco.get("recommended_mode") == "light" else ("dark", "light")
        for mode_name in order:
            theme = eco["themes"][mode_name]
            bg = theme["background"]["hex"]
            surf = theme["surface"]["hex"]
            txt = theme["text_primary"]["hex"]
            mut = theme["text_muted"]["hex"]
            prim = theme["primary"]["hex"]
            on_prim = (theme.get("on_primary") or theme["background"])["hex"]
            acc = theme["accent"]["hex"]
            maud = audit.get(mode_name, {})

            swatches = []
            for role, tok in theme.items():
                hex_val = html_lib.escape(tok["hex"])
                swatches.append(
                    f'<button type="button" class="swatch copy-swatch" data-hex="{hex_val}" title="Copiar {hex_val}">'
                    f'<div class="chip" style="background:{hex_val}"></div>'
                    f'<div class="meta"><strong>{html_lib.escape(role)}</strong>'
                    f'<span>{hex_val} · {html_lib.escape(tok["$value"])}</span></div></button>'
                )

            mode_cards.append(
                f'<div class="mode-card" data-mode="{mode_name}" style="background:{bg};color:{txt};border-color:{mut}44">'
                f'<div class="mode-head"><span>{mode_name.upper()} MODE</span>'
                f'<span class="metrics">Texto {maud.get("body_to_bg_ratio", audit.get("wcag_aaa_ratio"))}:1 · Botón {maud.get("button_to_bg_ratio", "4.5+")}:1 · APCA Lc {maud.get("body_lc", audit.get("apca_lc"))}</span></div>'
                f'<div class="sample-ui" style="background:{surf};border-color:{mut}33">'
                f'<h3 style="color:{txt}">Muestra tipográfica y jerarquía ({vslug})</h3>'
                f'<p style="color:{mut}">Ejemplo real de contraste y elevación sin resplandor AI ni relleno artificial.</p>'
                f'<button type="button" style="background:{prim};color:{on_prim}">Acción principal</button> '
                f'<span class="pill" style="border:1px solid {acc};color:{acc}">Estado</span>'
                f'</div>'
                f'<div class="swatches">{"".join(swatches)}</div>'
                f'</div>'
            )

        sections.append(
            f'<section class="eco-block" id="{eid}" data-eco-id="{eid}">'
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
<title>Chroma v5.1 OKLCH Preview — {vdisp} ({brand_esc})</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; background:#101216; color:#f1f5f9; margin:0; padding:32px 24px; }}
  .wrap {{ max-width:1280px; margin:0 auto; display:flex; flex-direction:column; gap:24px; }}
  h1 {{ margin:0 0 6px; font-size:24px; }}
  .sub {{ color:#cbd5e1; font-size:14px; margin:0 0 8px; }}
  .oraculo-line {{ font-size:12px; color:#93c5fd; background:#172030; border:1px solid #2b3a55; padding:8px 12px; border-radius:8px; display:inline-block; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; padding:12px 14px; background:#171a21; border:1px solid #262b36; border-radius:12px; }}
  .ctrl-btn {{ background:#222733; color:#e2e8f0; border:1px solid #334155; border-radius:8px; padding:7px 12px; font-size:12px; font-weight:600; cursor:pointer; }}
  .ctrl-btn.active {{ background:#e2e8f0; color:#0f172a; border-color:#f8fafc; }}
  .sep {{ width:1px; height:22px; background:#334155; margin:0 4px; }}
  .eco-block {{ background:#171a21; border:1px solid #262b36; border-radius:14px; padding:24px; }}
  .eco-block.is-hidden, .mode-card.is-hidden {{ display:none; }}
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
  .sample-ui button {{ border:none; border-radius:6px; padding:8px 14px; font-weight:700; font-size:12px; cursor:pointer; }}
  .pill {{ display:inline-block; border-radius:999px; padding:4px 10px; font-size:12px; font-weight:600; }}
  .swatches {{ display:grid; grid-template-columns:1fr; gap:8px; }}
  .swatch {{ display:flex; align-items:center; gap:10px; font-size:12px; background:transparent; border:1px solid transparent; border-radius:6px; padding:3px 4px; color:inherit; text-align:left; cursor:pointer; width:100%; }}
  .swatch:hover {{ border-color:rgba(148,163,184,.4); }}
  .chip {{ width:28px; height:28px; border-radius:6px; border:1px solid rgba(128,128,128,.35); flex-shrink:0; }}
  .meta {{ display:flex; flex-direction:column; line-height:1.25; }}
  .static-notice {{ background:#2a2010; color:#fde68a; border:1px solid #92400e; padding:10px 14px; border-radius:8px; font-size:13px; }}
  .toast {{ position:fixed; bottom:20px; right:20px; background:#0f172a; color:#f8fafc; border:1px solid #475569; padding:8px 14px; border-radius:8px; font-size:12px; display:none; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Chroma Engine v5.1 — {vdisp} ({varch})</h1>
    <p class="sub">Marca base: {brand_esc} · Auditoría WCAG 2.2 AAA (≥7:1 texto, ≥4.5:1 botón on_primary) + APCA (Lc ≥75).</p>
    <div class="oraculo-line">Coordenadas Oráculo: {oraculo_badge}</div>
  </header>
  <div id="chromaNoJsNotice" class="static-notice">
    Vista estática detectada (p. ej. visor embebido sin JavaScript): se muestran todos los ecosistemas en modo claro y oscuro. Para filtrar o copiar hexes con 1 clic, descarga y abre el archivo en tu navegador.
  </div>
  <div class="controls" id="chromaControls">
    <button type="button" class="ctrl-btn eco-btn active" data-eco-filter="all">Todos ({len(ecos)})</button>
    {"".join(eco_buttons)}
    <span class="sep"></span>
    <button type="button" class="ctrl-btn mode-btn active" data-mode-filter="all">Ambos Modos</button>
    <button type="button" class="ctrl-btn mode-btn" data-mode-filter="light">Solo Light</button>
    <button type="button" class="ctrl-btn mode-btn" data-mode-filter="dark">Solo Dark</button>
  </div>
  {"".join(sections)}
</div>
<div id="copyToast" class="toast"></div>
<script>
document.addEventListener('DOMContentLoaded', () => {{
  const notice = document.getElementById('chromaNoJsNotice');
  if (notice) notice.style.display = 'none';
  let activeEco = 'all';
  let activeMode = 'all';
  const applyFilters = () => {{
    document.querySelectorAll('.eco-block').forEach(el => {{
      const eid = el.getAttribute('data-eco-id');
      el.classList.toggle('is-hidden', activeEco !== 'all' && eid !== activeEco);
    }});
    document.querySelectorAll('.mode-card').forEach(card => {{
      const m = card.getAttribute('data-mode');
      card.classList.toggle('is-hidden', activeMode !== 'all' && m !== activeMode);
    }});
  }};
  document.querySelectorAll('.eco-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      activeEco = btn.getAttribute('data-eco-filter') || 'all';
      document.querySelectorAll('.eco-btn').forEach(b => b.classList.toggle('active', b === btn));
      applyFilters();
    }});
  }});
  document.querySelectorAll('.mode-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      activeMode = btn.getAttribute('data-mode-filter') || 'all';
      document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b === btn));
      applyFilters();
    }});
  }});
  document.querySelectorAll('.copy-swatch').forEach(sw => {{
    sw.addEventListener('click', () => {{
      const hx = sw.getAttribute('data-hex') || '';
      if (navigator.clipboard && hx) navigator.clipboard.writeText(hx).catch(() => {{}});
      const t = document.getElementById('copyToast');
      if (t) {{ t.textContent = 'Copiado: ' + hx; t.style.display = 'block'; setTimeout(() => {{ t.style.display = 'none'; }}, 1400); }}
    }});
  }});
}});
</script>
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
    brand_brief_path: Optional[Path] = None,
    palette_json_path: Optional[Path] = None,
    seed_hex: Optional[str] = None,
    bg_hex: Optional[str] = None,
    accent_hex: Optional[str] = None,
    sibling_workspaces_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    brand_upper = re.sub(r"[^a-zA-Z0-9_-]+", "", brand.strip()).upper() or "BRAND"
    signals = extract_oraculo_and_vertical_signals(brief_path, shards_path, vertical_json_path, vertical_slug=vertical_slug)
    sib_root = sibling_workspaces_dir
    if not sib_root and output_dir:
        od_res = Path(output_dir).resolve()
        if od_res.name == "brand" and od_res.parent.parent.name == "workspaces":
            sib_root = od_res.parent.parent
    sib_info = _collect_sibling_chroma_info(sib_root, own_output_dir=output_dir)

    if brand_brief_path and brand_brief_path.is_file():
        bb_raw = json.loads(brand_brief_path.read_text(encoding="utf-8"))
        signals["sources"].append(f"brand_brief:{brand_brief_path.name}")
        vslug_bb = str(bb_raw.get("vertical_slug") or vertical_slug or "").strip()
        if vslug_bb and not signals.get("vertical_slug"):
            signals["vertical_slug"] = vslug_bb
        if not vertical_json_path:
            signals["vertical_archetype"] = str(bb_raw.get("vertical_archetype") or "") or classify_vertical_archetype(
                json.dumps(bb_raw, ensure_ascii=False), signals.get("vertical_slug", "")
            )
            signals["vertical_is_b2b"] = signals["vertical_archetype"] == "architectural_b2b"

    use_brief_literal = (
        mode == "brief"
        or (mode == "auto" and not (shards_path and shards_path.is_file()) and not (vertical_json_path and vertical_json_path.is_file()) and not (brand_brief_path and brand_brief_path.is_file()))
    )

    if palette_json_path and palette_json_path.is_file():
        ecosystems = compose_ecosystems_from_palette_json(palette_json_path)
        source_ssot = f"art_direction:{palette_json_path.name}"
    elif seed_hex:
        ecosystems = compose_ecosystems_from_seed_hex(seed_hex, bg_hex=bg_hex, accent_hex=accent_hex)
        source_ssot = f"seed_hex:{seed_hex}"
    elif use_brief_literal and brief_path and brief_path.is_file():
        ecosystems = parse_ecosystems_from_brief(brief_path.read_text(encoding="utf-8", errors="replace"))
        source_ssot = f"{brief_path.name} §3 (literal)"
    else:
        ecosystems = synthesize_multiaxis_ecosystems(signals, sibling_info=sib_info)
        source_ssot = " + ".join(signals["sources"]) or "oraculo_multiaxis_synthesizer"

    if not ecosystems:
        ecosystems = synthesize_multiaxis_ecosystems(signals, sibling_info=sib_info)
        source_ssot = "oraculo_multiaxis_synthesizer"

    selected = next((e for e in ecosystems if e["id"] == selected_eco_id), ecosystems[0])
    sel_audit = _audit_ecosystem(selected["themes"])
    sel_dark = sel_audit["dark"]

    manifest: Dict[str, Any] = {
        "$schema": "https://www.designtokens.org/tr/2025.10/color/",
        "brand": brand_upper,
        "vertical_archetype": signals["vertical_archetype"],
        "engine": "chroma_engine.py v5.1 (Art-Direction + Sibling-Aware + Oráculo-Grounded)",
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
    print("Running chroma_engine v5.0 unit tests...")
    with tempfile.TemporaryDirectory(prefix="chroma_v50_test_") as tmp:
        tp = Path(tmp)
        shards_p = tp / "client_dumps_15_shards.json"
        brief_p = tp / "astrobranding_testcorp.md"
        vert_b2b = tp / "acme-b2b.json"
        vert_cos = tp / "orion-cosmic.json"
        bb_client = tp / "brand_brief.json"
        pal_json = tp / "art_direction_palettes.json"

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
        brief_p.write_text("# Brief\n**Elemento balancín Yong Shen:** La tinta abisal.\n", encoding="utf-8")
        vert_b2b.write_text(json.dumps({
            "vertical_slug": "acme-b2b", "display_name": "Consultoría B2B e IA", "category": "b2b",
            "role_in_ecosystem": "Otra vertical derivada de Orion y Sabidurías Cósmicas.",
        }), encoding="utf-8")
        vert_cos.write_text(json.dumps({"vertical_slug": "orion-cosmic", "display_name": "Orion — Sabidurías Cósmicas & Arquetipos Vocacionales"}), encoding="utf-8")

        m_b2b = generate_chroma_manifest("TESTCORP", brief_path=brief_p, shards_path=shards_p, vertical_json_path=vert_b2b, mode="synthesize")
        m_cos = generate_chroma_manifest("TESTCORP", brief_path=brief_p, shards_path=shards_p, vertical_json_path=vert_cos, mode="synthesize")
        assert m_b2b["inputs_used"]["yong_shen"] == "Water"
        assert m_b2b["vertical_archetype"] == "architectural_b2b"
        assert m_cos["vertical_archetype"] == "cosmic_archetypal"
        assert m_b2b["selected_ecosystem_id"] != m_cos["selected_ecosystem_id"]

        # Test WITHOUT Oraculo: BrandBrief + Curated Palette JSON preserving exact vivid hexes!
        bb_client.write_text(json.dumps({
            "vertical_slug": "vivid-studio", "display_name": "Estratega Digital B2B",
            "category": "b2b", "intake_mode": "client",
        }), encoding="utf-8")
        pal_json.write_text(json.dumps([
            {"id": "eco_1_crimson", "name": "Bermellón Editorial", "recommended_mode": "light",
             "background": "#f9f7f1", "surface": "#efece3", "primary": "#f50023", "accent": "#121212"},
            {"id": "eco_2_gold", "name": "Piedra & Oro", "recommended_mode": "light",
             "background": "#f3f1ec", "surface": "#e7e3da", "primary": "#c8a84b", "accent": "#0a0a0a"},
            {"id": "eco_3_emerald", "name": "Esmeralda & Lima", "recommended_mode": "light",
             "background": "#ffffff", "surface": "#f3f5f4", "primary": "#193d3b", "accent": "#c0ce43"},
        ]), encoding="utf-8")
        m_cur = generate_chroma_manifest("VIVIDCORP", brand_brief_path=bb_client, palette_json_path=pal_json)
        assert m_cur["themes"]["light"]["primary"]["hex"] == "#f50023", "Exact curated primary washed out!"
        assert wcag_contrast_ratio(m_cur["themes"]["light"]["on_primary"]["hex"], "#f50023") >= 4.5
        assert m_cur["ecosystems"][1]["themes"]["light"]["primary"]["hex"] == "#c8a84b"
        assert m_cur["ecosystems"][1]["themes"]["light"]["on_primary"]["hex"] == "#0a0a0a", "Gold CTA must get dark ink!"
        assert m_cur["ecosystems"][2]["themes"]["light"]["primary"]["hex"] == "#193d3b"
        assert m_cur["ecosystems"][2]["themes"]["light"]["on_primary"]["hex"] == "#ffffff", "Deep emerald CTA must get white ink!"
        assert "--brand-on-primary" in m_cur["css_integration"]["css_variables_root"]

        for man in (m_b2b, m_cos, m_cur):
            for eco in man["ecosystems"]:
                assert eco["audit"]["wcag_aaa_ratio"] >= 7.0
                for mode_name in ("dark", "light"):
                    t = eco["themes"][mode_name]
                    btn_ratio = wcag_contrast_ratio(t["on_primary"]["hex"], t["primary"]["hex"])
                    assert btn_ratio >= 4.5, f"Button contrast < 4.5 in {eco['id']} {mode_name}: {btn_ratio}"
                    for tok in t.values():
                        assert tok["hex"].lower() not in BANNED_SLOP_HEXES, f"Banned slop hex {tok['hex']}"

        html_out = render_chroma_preview_html(m_cur)
        assert "Chroma Engine v5.1" in html_out and "chromaControls" in html_out
        if shutil.which("node"):
            for i, s_body in enumerate(re.findall(r"<script[^>]*>(.*?)</script>", html_out, re.S)):
                js_tmp = tp / f"chroma_{i}.js"
                js_tmp.write_text(s_body, encoding="utf-8")
                res = subprocess.run(["node", "--check", str(js_tmp)], capture_output=True, text=True)
                assert res.returncode == 0, f"JS syntax error in chroma_preview: {res.stderr}"
        # Brief-only parsing check (no Scorpio/Rohini stale defaults)
        brief_full = tp / "astrobranding_fullbrief.md"
        brief_full.write_text("# Brief\n| **Sol Natal** | **Géminis** |\n| **Medio Cielo** | **Géminis** |\n**Day Master:** Jia\n**Nakshatra:** Chitra\n", encoding="utf-8")
        sig_bf = extract_oraculo_and_vertical_signals(brief_path=brief_full)
        assert sig_bf["sun_sign"] == "Gemini" and sig_bf["mc_sign"] == "Gemini" and sig_bf["nakshatra"] == "Chitra"
    assert not Path("/mnt/localstorage/TESTCORP").exists()
    print("✅ CHROMA ENGINE v5.1 UNIT TESTS PASSED (Curated hex fidelity, interactive preview HTML, brief fallback, 0 slop hexes, 0 phantom dirs)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Chroma Engine v5.1 — Art Direction & OKLCH Contrast Synthesizer")
    parser.add_argument("--brand", default="BRAND")
    parser.add_argument("--vertical", default=None)
    parser.add_argument("--brief", type=Path, default=None)
    parser.add_argument("--shards", type=Path, default=None)
    parser.add_argument("--vertical-json", type=Path, default=None)
    parser.add_argument("--brand-brief", type=Path, default=None)
    parser.add_argument("--palette-json", type=Path, default=None)
    parser.add_argument("--sibling-workspaces-dir", type=Path, default=None)
    parser.add_argument("--seed-hex", default=None)
    parser.add_argument("--bg-hex", default=None)
    parser.add_argument("--accent-hex", default=None)
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
        brand_brief_path=args.brand_brief,
        palette_json_path=args.palette_json,
        seed_hex=args.seed_hex,
        bg_hex=args.bg_hex,
        accent_hex=args.accent_hex,
        sibling_workspaces_dir=args.sibling_workspaces_dir,
        output_dir=args.output_dir,
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
    print(f"✅ CHROMA ENGINE v5.1 COMPLETED FOR: {manifest['brand']}/{manifest.get('vertical_slug', 'root')} (arch={manifest['vertical_archetype']}, selected={manifest['selected_ecosystem_id']}, default={manifest['recommended_mode']})")
    print(f"  • Source SSoT: {manifest['source_ssot']}")
    print(f"  • WCAG 2.2 AAA: {audit['wcag_2_2_compliance']['body_to_bg_ratio']}:1 | Btn: {audit['wcag_2_2_compliance']['button_to_bg_ratio']}:1 | APCA Lc: {audit['apca_compliance']['body_lc']}")
    print(f"  • Output: {out_dir / 'chroma_manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
