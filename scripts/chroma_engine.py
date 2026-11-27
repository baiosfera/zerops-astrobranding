#!/usr/bin/env python3
"""
chroma_engine.py — Sovereign Art-Direction-First OKLCH Compiler & Dual WCAG 2.2 / APCA Engine (v8.0).
Clean-slate Nov 2026 + Playbook 19 architecture:
- Separates creative Art Direction (--spec chroma_spec.json) from deterministic color engineering.
- Zero canned archetype template buckets & zero hidden Oráculo leakage unless explicitly requested.
- CSS Color 4 binary-search OKLCH -> Linear sRGB gamut mapping & Display-P3 serialization.
- Preserves rich Step-9 editorial CTAs (with crisp white or deep dark on_primary ink) instead of flattening dark mode into pastels.
- Emits 4-tier Z-elevation, W3C DTCG 2025.10 3-layer tokens + resolver, CSS Color Level 5, brandfont_export, and rich UI preview.
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
    "#f5f1ea", "#f7f5f1", "#fbf8f1", "#efeae0", "#ece6db", "#faf7f1", "#e8dfcb",
    "#b08947", "#b6553a", "#9a2436", "#9c6e2a", "#bc7c3a", "#7d5621",
    "#1a1714", "#1a1814", "#1b1814",
}

# Pure Surface Geometry Metadata (PB19) — zero hardcoded color templates
SURFACE_GEOMETRY_PROFILES: Dict[str, Dict[str, Any]] = {
    "architectural_b2b": {"color_strategy": "Restrained", "recommended_mode": "light", "radius_card": "12px", "radius_control": "8px", "elevation_style": "border_1px", "proportion": "60-30-10"},
    "luxury_editorial": {"color_strategy": "Committed", "recommended_mode": "light", "radius_card": "12px", "radius_control": "999px", "elevation_style": "border_1px", "proportion": "60-30-10"},
    "organic_wellness": {"color_strategy": "Restrained", "recommended_mode": "light", "radius_card": "16px", "radius_control": "999px", "elevation_style": "soft_shadow", "proportion": "60-30-10"},
    "bold_brutalist": {"color_strategy": "Drenched", "recommended_mode": "light", "radius_card": "0px", "radius_control": "0px", "elevation_style": "border_1px", "proportion": "60-30-10"},
    "fintech_clinical": {"color_strategy": "Restrained", "recommended_mode": "light", "radius_card": "12px", "radius_control": "8px", "elevation_style": "border_1px", "proportion": "60-30-10"},
    "warm_hospitality": {"color_strategy": "Committed", "recommended_mode": "light", "radius_card": "16px", "radius_control": "12px", "elevation_style": "soft_shadow", "proportion": "60-30-10"},
    "creative_playful": {"color_strategy": "Full Palette", "recommended_mode": "light", "radius_card": "16px", "radius_control": "999px", "elevation_style": "soft_shadow", "proportion": "60-30-10"},
    "cosmic_archetypal": {"color_strategy": "Committed", "recommended_mode": "dark", "radius_card": "14px", "radius_control": "10px", "elevation_style": "border_1px", "proportion": "60-30-10"},
    "design_system_atelier": {"color_strategy": "Restrained", "recommended_mode": "dark", "radius_card": "12px", "radius_control": "8px", "elevation_style": "border_1px", "proportion": "60-30-10"},
    "editorial_manifesto": {"color_strategy": "Committed", "recommended_mode": "light", "radius_card": "0px", "radius_control": "0px", "elevation_style": "border_1px", "proportion": "60-30-10"},
    "editorial_brand": {"color_strategy": "Committed", "recommended_mode": "light", "radius_card": "10px", "radius_control": "6px", "elevation_style": "border_1px", "proportion": "60-30-10"},
}


# -----------------------------------------------------------------------------
# Physical Color Science: OKLCH <-> OKLab <-> Linear sRGB / Display P3 -> WCAG & APCA
# -----------------------------------------------------------------------------

def _oklch_to_linear_srgb(l: float, c: float, h_deg: float) -> Tuple[float, float, float]:
    h_rad = math.radians(h_deg % 360.0)
    a = c * math.cos(h_rad)
    b = c * math.sin(h_rad)

    l_ = l + 0.3963377774 * a + 0.2158037573 * b
    m_ = l - 0.1055613458 * a - 0.0638541728 * b
    s_ = l - 0.0894841775 * a - 1.2914855480 * b

    l_c, m_c, s_c = l_ ** 3, m_ ** 3, s_ ** 3
    r_lin = +4.0767416621 * l_c - 3.3077115913 * m_c + 0.2309699292 * s_c
    g_lin = -1.2684380046 * l_c + 2.6097574011 * m_c - 0.3413193965 * s_c
    b_lin = -0.0041960863 * l_c - 0.7034186147 * m_c + 1.7076147010 * s_c
    return r_lin, g_lin, b_lin


def _in_srgb_gamut(r: float, g: float, b: float, eps: float = 1e-4) -> bool:
    return (-eps <= r <= 1.0 + eps) and (-eps <= g <= 1.0 + eps) and (-eps <= b <= 1.0 + eps)


def gamut_map_oklch(l: float, c: float, h_deg: float) -> Tuple[float, float, float, float, float, float]:
    """CSS Color 4 binary-search chroma reduction preserving perceptual Lightness and Hue."""
    l_clamped = max(0.0, min(1.0, l))
    c_clamped = max(0.0, c)
    h_norm = h_deg % 360.0
    r, g, b = _oklch_to_linear_srgb(l_clamped, c_clamped, h_norm)
    if _in_srgb_gamut(r, g, b):
        return l_clamped, c_clamped, h_norm, max(0.0, min(1.0, r)), max(0.0, min(1.0, g)), max(0.0, min(1.0, b))

    lo, hi = 0.0, c_clamped
    best_c, best_rgb = 0.0, _oklch_to_linear_srgb(l_clamped, 0.0, h_norm)
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        rm, gm, bm = _oklch_to_linear_srgb(l_clamped, mid, h_norm)
        if _in_srgb_gamut(rm, gm, bm):
            best_c = mid
            best_rgb = (rm, gm, bm)
            lo = mid
        else:
            hi = mid
    return (
        l_clamped,
        round(best_c, 4),
        h_norm,
        max(0.0, min(1.0, best_rgb[0])),
        max(0.0, min(1.0, best_rgb[1])),
        max(0.0, min(1.0, best_rgb[2])),
    )


def _lin_to_gamma_srgb(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 12.92 * x if x <= 0.0031308 else 1.055 * (x ** (1.0 / 2.4)) - 0.055


def _lin_srgb_to_p3(r: float, g: float, b: float) -> Tuple[float, float, float]:
    pr = 0.8224621 * r + 0.1775380 * g + 0.0000000 * b
    pg = 0.0331941 * r + 0.9668058 * g + 0.0000000 * b
    pb = 0.0170827 * r + 0.0723974 * g + 0.9105199 * b
    return (_lin_to_gamma_srgb(pr), _lin_to_gamma_srgb(pg), _lin_to_gamma_srgb(pb))


def oklch_to_hex_and_p3(l: float, c: float, h_deg: float) -> Tuple[str, str]:
    _, _, _, r_lin, g_lin, b_lin = gamut_map_oklch(l, c, h_deg)
    r = round(_lin_to_gamma_srgb(r_lin) * 255)
    g = round(_lin_to_gamma_srgb(g_lin) * 255)
    b = round(_lin_to_gamma_srgb(b_lin) * 255)
    hex_str = f"#{r:02x}{g:02x}{b:02x}"
    pr, pg, pb = _lin_srgb_to_p3(r_lin, g_lin, b_lin)
    return hex_str, f"color(display-p3 {pr:.3f} {pg:.3f} {pb:.3f})"


def hex_to_rgb_int(hex_str: str) -> Tuple[int, int, int]:
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        return (128, 128, 128)
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def hex_to_oklch(hex_str: str) -> Tuple[float, float, float]:
    r_i, g_i, b_i = hex_to_rgb_int(hex_str)
    def _to_lin(u: int) -> float:
        x = u / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = _to_lin(r_i), _to_lin(g_i), _to_lin(b_i)
    l_ = math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m_ = math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s_ = math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b_ok = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    C = math.hypot(a, b_ok)
    H = (math.degrees(math.atan2(b_ok, a)) + 360.0) % 360.0 if C > 1e-5 else 0.0
    return round(L, 4), round(C, 4), round(H, 1)


def parse_oklch_str(val: str) -> Tuple[float, float, float]:
    m = re.search(r"oklch\(\s*([\d.]+)%?\s+([\d.]+)\s+([\d.]+)", val, re.IGNORECASE)
    if not m:
        return (0.5, 0.1, 230.0)
    l_v = float(m.group(1))
    if "%" in val.split(m.group(1))[1][:2]:
        l_v /= 100.0
    return (round(l_v, 4), round(float(m.group(2)), 4), round(float(m.group(3)) % 360.0, 1))


def wcag_relative_luminance(hex_str: str) -> float:
    r_i, g_i, b_i = hex_to_rgb_int(hex_str)
    def _lin(u: int) -> float:
        x = u / 255.0
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * _lin(r_i) + 0.7152 * _lin(g_i) + 0.0722 * _lin(b_i)


def wcag_contrast_ratio(hex_fg: str, hex_bg: str) -> float:
    l1 = wcag_relative_luminance(hex_fg)
    l2 = wcag_relative_luminance(hex_bg)
    return round((max(l1, l2) + 0.05) / (min(l1, l2) + 0.05), 2)


def apca_contrast_lc(hex_fg: str, hex_bg: str) -> float:
    def _y(hx: str) -> float:
        r, g, b = hex_to_rgb_int(hx)
        y = 0.2126729 * ((r / 255.0) ** 2.4) + 0.7151522 * ((g / 255.0) ** 2.4) + 0.0721750 * ((b / 255.0) ** 2.4)
        return y if y >= 0.022 else y + (0.022 - y) ** 1.414

    y_txt, y_bg = _y(hex_fg), _y(hex_bg)
    if abs(y_bg - y_txt) < 0.0005:
        return 0.0
    if y_bg > y_txt:
        sapc = ((y_bg ** 0.56) - (y_txt ** 0.57)) * 1.14
        out = 0.0 if sapc < 0.1 else (sapc - 0.027) * 100.0
    else:
        sapc = ((y_bg ** 0.65) - (y_txt ** 0.62)) * 1.14
        out = 0.0 if sapc > -0.1 else (sapc + 0.027) * 100.0
    return round(abs(out), 1)


def make_color_token(l: float, c: float, h: float, desc: str, hex_override: Optional[str] = None) -> Dict[str, Any]:
    h_norm = round(h % 360.0, 1)
    l_safe = max(0.095, min(0.992, l)) if not hex_override else max(0.0, min(1.0, l))
    hex_calc, p3_str = oklch_to_hex_and_p3(l_safe, max(0.0, c), h_norm)
    final_hex = hex_override.lower() if hex_override else hex_calc
    if final_hex == "#000000":
        l_safe = 0.105
        final_hex, p3_str = oklch_to_hex_and_p3(l_safe, max(0.006, c), h_norm)
    l_r, c_r, h_r = (hex_to_oklch(final_hex) if hex_override else (round(l_safe, 3), round(c, 3), h_norm))
    ok_str = f"oklch({round(l_r, 3)} {round(c_r, 3)} {round(h_r, 1)})"
    return {
        "$value": ok_str,
        "$type": "color",
        "$description": desc,
        "colorSpace": "oklch",
        "components": {"lightness": round(l_r, 3), "chroma": round(c_r, 3), "hue": round(h_r, 1)},
        "alpha": 1,
        "hex": final_hex,
        "p3": p3_str,
    }


def token_from_input(raw_val: Any, desc: str, fallback_hex: str = "#16161a") -> Dict[str, Any]:
    s = str(raw_val or "").strip()
    if s.startswith("#"):
        if s.lower() == "#000000":
            s = "#121316"
        l, c, h = hex_to_oklch(s)
        _, p3 = oklch_to_hex_and_p3(l, c, h)
        return {
            "$value": f"oklch({round(l, 3)} {round(c, 3)} {round(h, 1)})",
            "$type": "color",
            "$description": desc,
            "colorSpace": "oklch",
            "components": {"lightness": round(l, 3), "chroma": round(c, 3), "hue": round(h, 1)},
            "alpha": 1,
            "hex": s.lower(),
            "p3": p3,
        }
    if "oklch(" in s.lower():
        l, c, h = parse_oklch_str(s)
        return make_color_token(l, c, h, desc)
    return token_from_input(fallback_hex, desc)


def pick_on_color(bg_hex: str, desc: str = "Texto sobre color de marca", hue: float = 240.0) -> Dict[str, Any]:
    """Selects crisp tinted alabaster vs deep tinted charcoal ink maximizing WCAG + APCA contrast (>=4.5:1)."""
    candidates_l = [make_color_token(0.982, 0.006, hue, desc), make_color_token(0.996, 0.002, hue, desc)]
    candidates_d = [make_color_token(0.145, 0.012, hue, desc), make_color_token(0.105, 0.008, hue, desc)]
    best = candidates_l[0]
    best_key = (-1.0, -1.0)
    for tok in candidates_l + candidates_d:
        w = wcag_contrast_ratio(tok["hex"], bg_hex)
        a = apca_contrast_lc(tok["hex"], bg_hex)
        key = (1.0 if w >= 4.5 else 0.0, w + (a / 20.0))
        if key > best_key:
            best_key = key
            best = tok
    return best


def _ensure_contrast(
    fg_tok: Dict[str, Any],
    bg_hex: str,
    is_dark_bg: bool,
    min_wcag: float = 7.0,
    min_lc: float = 75.0,
    preserve_if_ok: bool = True,
) -> Dict[str, Any]:
    if preserve_if_ok:
        cur_w = wcag_contrast_ratio(fg_tok["hex"], bg_hex)
        cur_a = apca_contrast_lc(fg_tok["hex"], bg_hex)
        if cur_w >= min_wcag and cur_a >= min_lc:
            return fg_tok
    c = fg_tok["components"]
    l_cur, cr, hue = c["lightness"], c["chroma"], c["hue"]
    step = 0.018 if is_dark_bg else -0.018
    for _ in range(32):
        cand = make_color_token(l_cur, cr, hue, fg_tok["$description"])
        if wcag_contrast_ratio(cand["hex"], bg_hex) >= min_wcag and apca_contrast_lc(cand["hex"], bg_hex) >= min_lc:
            return cand
        l_cur = max(0.10, min(0.988, l_cur + step))
    return make_color_token(0.94 if is_dark_bg else 0.14, min(0.04, cr), hue, fg_tok["$description"])


def _build_elevation_and_feedback(bg_hex: str, bg_l: float, neu_h: float, neu_c: float, is_dark: bool) -> Dict[str, Dict[str, Any]]:
    elev_l = round(min(0.27, max(0.22, bg_l + 0.095)), 3) if is_dark else round(min(0.996, bg_l + 0.008), 3)
    bord_l = round(min(0.35, max(0.295, bg_l + 0.165)), 3) if is_dark else round(max(0.84, bg_l - 0.13), 3)
    surf_elev = make_color_token(elev_l, max(0.005, round(neu_c * 0.85, 3)), neu_h, "Superficie elevada Z2")
    border_sub = make_color_token(bord_l, max(0.005, round(neu_c * 0.90, 3)), neu_h, "Borde sutil Z3")
    fb_l = 0.72 if is_dark else 0.43
    fb_c = 0.135 if is_dark else 0.15
    return {
        "surface_elevated": surf_elev,
        "border_subtle": border_sub,
        "feedback_success": _ensure_contrast(make_color_token(fb_l, fb_c, 152.0, "Estado positivo / éxito"), bg_hex, is_dark, min_wcag=4.6, min_lc=55.0, preserve_if_ok=False),
        "feedback_warning": _ensure_contrast(make_color_token(0.77 if is_dark else 0.50, 0.14, 72.0, "Estado advertencia"), bg_hex, is_dark, min_wcag=4.6, min_lc=55.0, preserve_if_ok=False),
        "feedback_error": _ensure_contrast(make_color_token(0.70 if is_dark else 0.47, 0.165, 24.0, "Estado error / bloqueo"), bg_hex, is_dark, min_wcag=4.6, min_lc=55.0, preserve_if_ok=False),
        "feedback_info": _ensure_contrast(make_color_token(0.73 if is_dark else 0.45, 0.135, 242.0, "Estado informativo"), bg_hex, is_dark, min_wcag=4.6, min_lc=55.0, preserve_if_ok=False),
    }


def _audit_ecosystem(themes: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for mode_name in ("dark", "light"):
        t = themes[mode_name]
        bg = t["background"]["hex"]
        txt = t["text_primary"]["hex"]
        prim = t["primary"]["hex"]
        on_p = t["on_primary"]["hex"]
        mut = t["text_muted"]["hex"]
        out[mode_name] = {
            "body_to_bg_ratio": wcag_contrast_ratio(txt, bg),
            "headings_to_bg_ratio": wcag_contrast_ratio(prim, bg),
            "button_to_bg_ratio": wcag_contrast_ratio(on_p, prim),
            "muted_to_bg_ratio": wcag_contrast_ratio(mut, bg),
            "body_lc": apca_contrast_lc(txt, bg),
            "headings_lc": apca_contrast_lc(prim, bg),
            "ui_components_lc": apca_contrast_lc(on_p, prim),
        }
    d_t, l_t = themes["dark"], themes["light"]
    d_bg_l = d_t["background"]["components"]["lightness"]
    d_sf_l = d_t["surface"]["components"]["lightness"]
    d_el_l = d_t["surface_elevated"]["components"]["lightness"]
    d_bd_l = d_t["border_subtle"]["components"]["lightness"]
    d_delta = round(d_t["text_primary"]["components"]["lightness"] - d_bg_l, 3)
    l_delta = round(l_t["background"]["components"]["lightness"] - l_t["text_primary"]["components"]["lightness"], 3)
    z_mono = (d_bd_l >= d_el_l >= d_sf_l > d_bg_l)
    achrom = {
        "dark_luminance_delta": d_delta,
        "light_luminance_delta": l_delta,
        "dark_z_monotonic": z_mono,
        "status_pass": bool(d_delta >= 0.55 and l_delta >= 0.55 and z_mono),
    }
    min_body = min(out["dark"]["body_to_bg_ratio"], out["light"]["body_to_bg_ratio"])
    min_btn = min(out["dark"]["button_to_bg_ratio"], out["light"]["button_to_bg_ratio"])
    min_lc = min(out["dark"]["body_lc"], out["light"]["body_lc"])
    out["wcag_aaa_ratio"] = out["dark"]["body_to_bg_ratio"]
    out["apca_lc"] = out["dark"]["body_lc"]
    out["achromatic_audit"] = achrom
    out["status_aaa"] = bool(min_body >= 7.0 and min_btn >= 4.5 and min_lc >= 75.0)
    return out


def _harden_mode_tokens(raw_spec: Dict[str, Any], is_dark: bool, label_suffix: str = "") -> Dict[str, Dict[str, Any]]:
    """Preserves rich art-director colors verbatim whenever accessible; enforces WCAG, APCA, and PB19 Z-elevation."""
    bg_default = "#111216" if is_dark else "#f8f6f2"
    sf_default = "#191b20" if is_dark else "#efece6"
    prim_default = "#9b1c26" if is_dark else "#8c151c"
    txt_default = "#edeae4" if is_dark else "#161514"
    mut_default = "#a7a49d" if is_dark else "#55524c"

    bg_tok = token_from_input(raw_spec.get("background") or raw_spec.get("bg") or bg_default, f"Lienzo base{label_suffix}")
    sf_tok = token_from_input(raw_spec.get("surface") or sf_default, f"Superficie Z1{label_suffix}")
    prim_tok = token_from_input(raw_spec.get("primary") or prim_default, f"Acción principal{label_suffix}")
    acc_tok = token_from_input(raw_spec.get("accent") or raw_spec.get("primary") or prim_default, f"Acento focal{label_suffix}")
    sec_tok = token_from_input(raw_spec.get("secondary") or mut_default, f"Soporte estructural{label_suffix}")
    txt_tok = token_from_input(raw_spec.get("text_primary") or raw_spec.get("text") or txt_default, f"Tinta principal{label_suffix}")
    mut_tok = token_from_input(raw_spec.get("text_muted") or raw_spec.get("muted") or mut_default, f"Texto secundario{label_suffix}")

    bg_hex = bg_tok["hex"]
    bg_l = bg_tok["components"]["lightness"]
    neu_c = max(0.006, bg_tok["components"]["chroma"])
    neu_h = bg_tok["components"]["hue"] or prim_tok["components"]["hue"] or 35.0

    # Ensure dark surface step Z1 > Z0 strictly for achromatic monotonicity
    if is_dark and sf_tok["components"]["lightness"] <= bg_l + 0.025:
        sf_tok = make_color_token(bg_l + 0.05, max(0.005, sf_tok["components"]["chroma"]), sf_tok["components"]["hue"] or neu_h, sf_tok["$description"])

    txt_tok = _ensure_contrast(txt_tok, bg_hex, is_dark, min_wcag=7.0, min_lc=75.0, preserve_if_ok=True)
    mut_tok = _ensure_contrast(mut_tok, bg_hex, is_dark, min_wcag=4.5, min_lc=50.0, preserve_if_ok=True)

    # Guarantee primary CTA pops cleanly off its background (>=3.0:1 UI graphic contrast) without washing out rich dark pigments
    if wcag_contrast_ratio(prim_tok["hex"], bg_hex) < 3.0:
        prim_tok = _ensure_contrast(prim_tok, bg_hex, is_dark, min_wcag=3.2, min_lc=42.0, preserve_if_ok=True)

    on_prim = (
        token_from_input(raw_spec["on_primary"], "Texto sobre primario")
        if raw_spec.get("on_primary") and wcag_contrast_ratio(str(raw_spec["on_primary"]), prim_tok["hex"]) >= 4.5
        else pick_on_color(prim_tok["hex"], "Texto sobre primario", hue=prim_tok["components"]["hue"] or neu_h)
    )
    on_acc = (
        token_from_input(raw_spec["on_accent"], "Texto sobre acento")
        if raw_spec.get("on_accent") and wcag_contrast_ratio(str(raw_spec["on_accent"]), acc_tok["hex"]) >= 4.5
        else pick_on_color(acc_tok["hex"], "Texto sobre acento", hue=acc_tok["components"]["hue"] or neu_h)
    )

    extra = _build_elevation_and_feedback(bg_hex, bg_l, neu_h, neu_c, is_dark=is_dark)
    return {
        "primary": prim_tok,
        "on_primary": on_prim,
        "secondary": sec_tok,
        "accent": acc_tok,
        "on_accent": on_acc,
        "background": bg_tok,
        "surface": sf_tok,
        "text_primary": txt_tok,
        "text_muted": mut_tok,
        **extra,
    }


def _synthesize_opposite_mode(source_theme: Dict[str, Dict[str, Any]], source_is_dark: bool) -> Dict[str, Dict[str, Any]]:
    """Derives balanced Light <-> Dark polarity without losing Step-9 pigment richness or monochrome fidelity."""
    p_c = source_theme["primary"]["components"]
    a_c = source_theme["accent"]["components"]
    s_c = source_theme["secondary"]["components"]
    bg_c = source_theme["background"]["components"]
    is_mono = p_c["chroma"] <= 0.025 and a_c["chroma"] <= 0.025
    neu_h = bg_c["hue"] or p_c["hue"] or 30.0

    if source_is_dark:
        # Derive rich editorial Light mode
        bg_l, sf_l, txt_l, mut_l = 0.980, 0.946, 0.160, 0.435
        bg_ch = min(0.012, max(0.004, bg_c["chroma"] * 0.5))
        if is_mono:
            prim_spec = make_color_token(0.18, min(0.012, p_c["chroma"]), p_c["hue"], "Primario monocromo")
            acc_spec = make_color_token(0.28, min(0.014, a_c["chroma"]), a_c["hue"] or neu_h, "Acento monocromo")
        else:
            # Keep rich saturated Step-9 pigment on light canvas (L 0.42–0.50, rich C)
            prim_spec = make_color_token(min(0.49, max(0.38, p_c["lightness"] * 0.72)), max(0.08, p_c["chroma"]), p_c["hue"], "Primario editorial")
            acc_spec = make_color_token(min(0.46, max(0.36, a_c["lightness"] * 0.70)), max(0.06, a_c["chroma"] * 0.95), a_c["hue"], "Acento editorial")
        opp = {
            "background": make_color_token(bg_l, bg_ch, neu_h, "Lienzo claro")["hex"],
            "surface": make_color_token(sf_l, min(0.016, bg_ch * 1.4), neu_h, "Superficie clara")["hex"],
            "primary": prim_spec["hex"],
            "secondary": make_color_token(0.48, min(0.08, s_c["chroma"]), s_c["hue"] or neu_h, "Secundario claro")["hex"],
            "accent": acc_spec["hex"],
            "text_primary": make_color_token(txt_l, 0.008 if is_mono else 0.012, neu_h, "Tinta principal")["hex"],
            "text_muted": make_color_token(mut_l, 0.009 if is_mono else 0.013, neu_h, "Tinta secundaria")["hex"],
        }
        return _harden_mode_tokens(opp, is_dark=False)

    # Derive composed Dark mode (Step-9 solid vivid CTA with crisp white ink OR crisp bone monochrome CTA — NO washed pastels!)
    bg_l, sf_l, txt_l, mut_l = 0.132, 0.182, 0.932, 0.730
    bg_ch = min(0.014, max(0.005, bg_c["chroma"] * 1.2))
    if is_mono:
        prim_spec = make_color_token(0.92, min(0.012, p_c["chroma"]), p_c["hue"], "Primario platino")
        acc_spec = make_color_token(0.78, min(0.014, a_c["chroma"]), a_c["hue"] or neu_h, "Acento platino")
    else:
        # Step-9 vivid solid fill tuned for dark canvas (L 0.46–0.53 with rich chroma -> crisp #fafaf9 text!)
        prim_spec = make_color_token(min(0.53, max(0.46, p_c["lightness"] + 0.05)), max(0.09, min(0.22, p_c["chroma"] * 0.92)), p_c["hue"], "Primario intenso oscuro")
        acc_spec = make_color_token(min(0.76, max(0.58, a_c["lightness"] + 0.20)), max(0.07, min(0.18, a_c["chroma"] * 0.85)), a_c["hue"], "Acento luminoso oscuro")
    opp = {
        "background": make_color_token(bg_l, bg_ch, neu_h, "Lienzo oscuro")["hex"],
        "surface": make_color_token(sf_l, min(0.016, bg_ch * 1.1), neu_h, "Superficie oscura")["hex"],
        "primary": prim_spec["hex"],
        "secondary": make_color_token(0.58, min(0.07, s_c["chroma"]), s_c["hue"] or neu_h, "Secundario oscuro")["hex"],
        "accent": acc_spec["hex"],
        "text_primary": make_color_token(txt_l, 0.007 if is_mono else 0.010, neu_h, "Tinta oscura")["hex"],
        "text_muted": make_color_token(mut_l, 0.009 if is_mono else 0.012, neu_h, "Tinta secundaria oscura")["hex"],
    }
    return _harden_mode_tokens(opp, is_dark=True)


def compile_art_direction_ecosystems(
    items: List[Dict[str, Any]],
    source_label: str = "art_direction_spec",
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Compiles Art-Director palette specs (chroma_spec.json or palette_json) into full PB19 ecosystems."""
    ecosystems: List[Dict[str, Any]] = []
    override_geom: Optional[Dict[str, Any]] = None
    for idx, item in enumerate(items[:4]):
        if not isinstance(item, dict):
            continue
        eco_id = str(item.get("id") or f"eco_{idx + 1}_world")
        name = str(item.get("name") or f"Mundo Visual {idx + 1}")
        concept = str(item.get("concept") or "Dirección de arte compilada en OKLCH.")
        rec_mode = str(item.get("recommended_mode") or "light").lower()
        if rec_mode not in ("light", "dark"):
            rec_mode = "light"

        if "light" in item and isinstance(item["light"], dict) and "dark" in item and isinstance(item["dark"], dict):
            light_t = _harden_mode_tokens(item["light"], is_dark=False)
            dark_t = _harden_mode_tokens(item["dark"], is_dark=True)
        elif "light" in item and isinstance(item["light"], dict):
            light_t = _harden_mode_tokens(item["light"], is_dark=False)
            dark_t = _synthesize_opposite_mode(light_t, source_is_dark=False)
        elif "dark" in item and isinstance(item["dark"], dict):
            dark_t = _harden_mode_tokens(item["dark"], is_dark=True)
            light_t = _synthesize_opposite_mode(dark_t, source_is_dark=True)
        else:
            bg_h = str(item.get("background") or item.get("bg") or "#f8f6f2")
            is_base_dark = wcag_relative_luminance(bg_h) < 0.25 if bg_h.startswith("#") else False
            if is_base_dark:
                rec_mode = str(item.get("recommended_mode") or "dark").lower()
                dark_t = _harden_mode_tokens(item, is_dark=True)
                light_t = _synthesize_opposite_mode(dark_t, source_is_dark=True)
            else:
                light_t = _harden_mode_tokens(item, is_dark=False)
                dark_t = _synthesize_opposite_mode(light_t, source_is_dark=False)

        themes = {"dark": dark_t, "light": light_t}
        audit = _audit_ecosystem(themes)
        if idx == 0 and isinstance(item.get("surface_geometry"), dict):
            override_geom = item["surface_geometry"]
        ecosystems.append({
            "id": eco_id,
            "name": name,
            "recommended_mode": rec_mode,
            "color_strategy": str(item.get("color_strategy") or "Committed"),
            "proportion": "60-30-10",
            "surface_geometry": item.get("surface_geometry"),
            "concept": concept,
            "derivation_parameters": {"mode": source_label, "authored_polarity": rec_mode},
            "themes": themes,
            "audit": {
                "wcag_aaa_ratio": audit["wcag_aaa_ratio"],
                "apca_lc": audit["apca_lc"],
                "achromatic_audit": audit["achromatic_audit"],
                "dark": audit["dark"],
                "light": audit["light"],
            },
        })
    return ecosystems, override_geom


def parse_ecosystems_from_brief(brief_text: str) -> List[Dict[str, Any]]:
    """Explicit opt-in compiler for Oráculo astrobranding_*.md §3 OKLCH tables."""
    section_matches = list(re.finditer(r"^###\s+3\.\d+\s+Ecosistema\s+[^:]+:\s*(.+)$", brief_text, re.MULTILINE))
    if not section_matches:
        return []
    role_map = {
        "color-primary": "primary", "primary": "primary",
        "color-secondary": "secondary", "secondary": "secondary",
        "color-accent": "accent", "accent": "accent",
        "color-background": "background", "background": "background", "bg": "background",
        "color-surface": "surface", "surface": "surface",
        "color-text-primary": "text_primary", "text_primary": "text_primary", "text-primary": "text_primary", "text": "text_primary",
        "color-text-muted": "text_muted", "text_muted": "text_muted", "text-muted": "text_muted", "muted": "text_muted",
    }
    specs: List[Dict[str, Any]] = []
    for idx, m in enumerate(section_matches):
        start = m.end()
        end = section_matches[idx + 1].start() if idx + 1 < len(section_matches) else len(brief_text)
        nh2 = re.search(r"^##\s+", brief_text[start:end], re.MULTILINE)
        if nh2:
            end = start + nh2.start()
        block = brief_text[start:end]
        raw_title = m.group(1).strip()
        concept = f"Ecosistema Oráculo §3 ({raw_title})."
        for line in block.splitlines():
            ls = line.strip()
            if ls and not ls.startswith(("#", "|", "**Narrativa")):
                concept = re.sub(r"\*\*", "", ls)
                break
        ml = re.search(r"^####\s+Modo Claro\b.*$", block, re.MULTILINE | re.IGNORECASE)
        md = re.search(r"^####\s+Modo Oscuro\b.*$", block, re.MULTILINE | re.IGNORECASE)
        if ml and md:
            if md.start() < ml.start():
                d_blk, l_blk, rec_m = block[md.end():ml.start()], block[ml.end():], "dark"
            else:
                l_blk, d_blk, rec_m = block[ml.end():md.start()], block[md.end():], "light"
        elif ml:
            l_blk, d_blk, rec_m = block[ml.end():], "", "light"
        else:
            d_blk, l_blk, rec_m = block, "", "dark"

        def _pt(sub: str) -> Dict[str, str]:
            out: Dict[str, str] = {}
            for line in sub.splitlines():
                if not line.strip().startswith("|"):
                    continue
                parts = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(parts) < 3 or "oklch(" not in parts[1].lower():
                    continue
                role = role_map.get(re.sub(r"[*_`]", "", parts[0]).strip().lower())
                if not role:
                    continue
                hm = re.search(r"(#[0-9a-fA-F]{6})", parts[2])
                out[role] = hm.group(1).lower() if hm else parts[1]
            return out

        dt = _pt(d_blk) if d_blk else {}
        lt = _pt(l_blk) if l_blk else {}
        if not {"primary", "background", "text_primary"}.issubset(dt.keys() or lt.keys()):
            continue
        clean = re.sub(r"[^a-zA-Z0-9]+", "_", raw_title.split("(")[0].strip().lower()).strip("_")
        eco_id = f"eco_{idx + 1}_" + ("_".join(clean.split("_")[:2]) or "oraculo")
        item: Dict[str, Any] = {"id": eco_id, "name": raw_title, "concept": concept, "recommended_mode": rec_m, "color_strategy": "Committed"}
        if dt:
            item["dark"] = dt
        if lt:
            item["light"] = lt
        specs.append(item)
    ecos, _ = compile_art_direction_ecosystems(specs, source_label="oraculo_brief_section_3")
    return ecos


# -----------------------------------------------------------------------------
# Clean Fallback Synthesizer (Editorial Step-9 Grade, Zero Canned Pastel Clichés)
# -----------------------------------------------------------------------------

def _extract_vertical_identity_blob(vdata: Dict[str, Any]) -> str:
    cap = vdata.get("category_and_positioning") or {}
    return json.dumps([
        vdata.get("vertical_slug", ""), vdata.get("display_name", ""), vdata.get("name", ""),
        vdata.get("funnel_type", ""), vdata.get("category", ""), vdata.get("tagline", ""),
        cap.get("category_name", ""), cap.get("primary_positioning_terms", []),
        vdata.get("ontological_foundation", {}), vdata.get("unique_mechanism", {}),
    ], ensure_ascii=False)


def classify_vertical_archetype(vblob: str, vertical_slug: str = "") -> str:
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


def _collect_sibling_selected_ids(sib_root: Optional[Path], own_dir: Optional[Path]) -> set[str]:
    used: set[str] = set()
    if not sib_root or not sib_root.is_dir():
        return used
    own_res = (own_dir / "chroma_manifest.json").resolve() if own_dir else None
    for child in sorted(sib_root.iterdir()):
        cm = (child / "brand" / "chroma_manifest.json")
        if not cm.is_file():
            continue
        if own_res and cm.resolve() == own_res:
            continue
        try:
            d = json.loads(cm.read_text(encoding="utf-8"))
            if d.get("selected_ecosystem_id"):
                used.add(str(d["selected_ecosystem_id"]))
        except Exception:
            pass
    return used


_SIGN_MAP: Dict[str, str] = {
    "aries": "Aries", "taurus": "Taurus", "tauro": "Taurus",
    "gemini": "Gemini", "geminis": "Gemini", "géminis": "Gemini",
    "cancer": "Cancer", "cáncer": "Cancer", "leo": "Leo", "virgo": "Virgo",
    "libra": "Libra", "scorpio": "Scorpio", "escorpio": "Scorpio",
    "sagittarius": "Sagittarius", "sagitario": "Sagittarius",
    "capricorn": "Capricorn", "capricornio": "Capricorn",
    "aquarius": "Aquarius", "acuario": "Aquarius",
    "pisces": "Pisces", "piscis": "Pisces",
}
_ELEMENT_MAP: Dict[str, str] = {
    "water": "Water", "agua": "Water",
    "fire": "Fire", "fuego": "Fire",
    "wood": "Wood", "madera": "Wood",
    "earth": "Earth", "tierra": "Earth",
    "metal": "Metal",
    "air": "Air", "aire": "Air",
}
_DAY_MASTER_ELEMENT: Dict[str, str] = {
    "jia": "Wood", "yi": "Wood", "bing": "Fire", "ding": "Fire",
    "wu": "Earth", "ji": "Earth", "geng": "Metal", "xin": "Metal",
    "ren": "Water", "gui": "Water",
}
_ZODIAC_ELEMENT: Dict[str, str] = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}
_NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
)


def _norm_sign(val: str) -> str:
    tok = re.sub(r"[^a-zA-ZáéíóúÁÉÍÓÚ]", "", str(val or "").strip()).lower()
    return _SIGN_MAP.get(tok, "")


def _norm_element(val: str) -> str:
    for part in re.findall(r"[A-Za-záéíóúÁÉÍÓÚ]+", str(val or "").lower()):
        if part in _ELEMENT_MAP:
            return _ELEMENT_MAP[part]
    return ""


def parse_oraculo_brief_signals(txt: str) -> Dict[str, Any]:
    """Strict extractor for Oráculo astrobranding_*.md files; never captures prose stop-words."""
    out: Dict[str, Any] = {}
    sign_alts = "|".join(sorted(_SIGN_MAP.keys(), key=len, reverse=True))
    m_sol = re.search(rf"(?:Sol\s*Natal|Tropical\s+Placidus)[^\n]{{0,120}}\b({sign_alts})\b", txt, re.IGNORECASE)
    if m_sol and _norm_sign(m_sol.group(1)):
        out["sun_sign"] = _norm_sign(m_sol.group(1))
    m_mc = re.search(rf"Medio\s*Cielo[^\n|]{{0,80}}\|[^\n]{{0,40}}\b({sign_alts})\b|MC\s+en\s+\**({sign_alts})\b", txt, re.IGNORECASE)
    if m_mc:
        out["mc_sign"] = _norm_sign(m_mc.group(1) or m_mc.group(2) or "")
    m_lon = re.search(r"Longitud\s+solar[^\d]{0,30}(\d+(?:\.\d+)?)", txt, re.IGNORECASE)
    if m_lon:
        out["sun_lon"] = float(m_lon.group(1))
    m_ys = re.search(r"Yong\s*Shen\**\s*:?\**\s*([A-Za-záéíóúÁÉÍÓÚ]+)", txt, re.IGNORECASE)
    if m_ys and _norm_element(m_ys.group(1)):
        out["yong_shen"] = _norm_element(m_ys.group(1))
    m_dom = re.search(r"Elemento\s+dominante\**\s*:?\**\s*([A-Za-záéíóúÁÉÍÓÚ]+)", txt, re.IGNORECASE)
    if m_dom and _norm_element(m_dom.group(1)):
        out["dominant_element"] = _norm_element(m_dom.group(1))
    nak_alts = "|".join(_NAKSHATRAS)
    m_nak = re.search(rf"Nakshatra[^\n]{{0,80}}\b({nak_alts})\b", txt, re.IGNORECASE)
    if m_nak:
        out["nakshatra"] = next((n for n in _NAKSHATRAS if n.lower() == m_nak.group(1).lower()), "")
    dm_alts = "|".join(k.title() for k in _DAY_MASTER_ELEMENT)
    m_dm = re.search(rf"Day\s*Master[^\n]{{0,40}}\b({dm_alts})\b", txt, re.IGNORECASE)
    if m_dm:
        out["bazi_day_master"] = m_dm.group(1).title()
    return {k: v for k, v in out.items() if v}


def extract_inputs(
    brief_path: Optional[Path] = None,
    shards_path: Optional[Path] = None,
    vertical_json_path: Optional[Path] = None,
    brand_brief_path: Optional[Path] = None,
    vertical_slug: Optional[str] = None,
) -> Dict[str, Any]:
    sig: Dict[str, Any] = {
        "sources": [],
        "vertical_archetype": "editorial_brand",
        "vertical_slug": vertical_slug or "",
        "vertical_display_name": "",
        "has_oraculo": False,
        "sun_lon": 0.0,
        "sun_sign": "",
        "mc_sign": "",
        "dominant_element": "",
        "yong_shen": "",
        "nakshatra": "",
        "bazi_day_master": "",
    }
    if shards_path and shards_path.is_file():
        sig["sources"].append(f"shards:{shards_path.name}")
        sd = json.loads(shards_path.read_text(encoding="utf-8"))
        s1 = sd.get("shard_01", {}).get("data", {})
        s3 = sd.get("shard_03", {}).get("data", {})
        s4 = sd.get("shard_04", {}).get("data", {})
        sig["sun_lon"] = float(s1.get("planets", {}).get("Sun", {}).get("longitude") or s1.get("tripod_of_iron", {}).get("sun", {}).get("longitude") or 0.0)
        sig["sun_sign"] = _norm_sign(s1.get("tripod_of_iron", {}).get("sun", {}).get("sign") or "") or str(s1.get("tripod_of_iron", {}).get("sun", {}).get("sign") or "")
        sig["mc_sign"] = _norm_sign(s1.get("tripod_of_iron", {}).get("midheaven_house_10", {}).get("sign") or "") or str(s1.get("tripod_of_iron", {}).get("midheaven_house_10", {}).get("sign") or "")
        sig["dominant_element"] = _norm_element(s1.get("arroyo_elements", {}).get("dominant_element") or "")
        sig["nakshatra"] = str(s3.get("nakshatra", {}).get("name") or "").split()[0]
        sig["bazi_day_master"] = str(s4.get("day_master", {}).get("name") or "").split()[0].title()
        sig["yong_shen"] = _norm_element(s4.get("yong_shen", {}).get("element") or "")
        sig["has_oraculo"] = True

    if brief_path and brief_path.is_file():
        sig["sources"].append(f"brief:{brief_path.name}")
        txt = brief_path.read_text(encoding="utf-8", errors="replace")
        parsed = parse_oraculo_brief_signals(txt)
        for k, v in parsed.items():
            if not sig.get(k):
                sig[k] = v
        if parsed:
            sig["has_oraculo"] = True

    vfile = vertical_json_path if (vertical_json_path and vertical_json_path.is_file()) else (brand_brief_path if (brand_brief_path and brand_brief_path.is_file()) else None)
    if vfile:
        label_k = "vertical" if vfile == vertical_json_path else "brand_brief"
        sig["sources"].append(f"{label_k}:{vfile.name}")
        raw_txt = vfile.read_text(encoding="utf-8", errors="replace")
        if vfile.suffix.lower() == ".json":
            vdata = json.loads(raw_txt)
            sig["vertical_display_name"] = str(vdata.get("display_name") or vdata.get("name") or "")
            sig["vertical_slug"] = str(vdata.get("vertical_slug") or vertical_slug or vfile.stem)
            blob = _extract_vertical_identity_blob(vdata)
            sig["vertical_archetype"] = str(vdata.get("vertical_archetype") or "") or classify_vertical_archetype(blob, sig["vertical_slug"])
        else:
            sig["vertical_archetype"] = classify_vertical_archetype(raw_txt, sig["vertical_slug"])
    elif vertical_slug:
        sig["vertical_archetype"] = classify_vertical_archetype("", vertical_slug)
    return sig


def _synthesize_fallback_ecosystems(
    brand: str,
    sig: Dict[str, Any],
    seed_hex: Optional[str] = None,
    bg_hex: Optional[str] = None,
    accent_hex: Optional[str] = None,
    sib_used_ids: Optional[set[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Editorial-grade OKLCH synthesizer when no --spec is supplied.
    Generates 3 distinct worlds (Rich Crimson/Cobalt/Forest Step-9, Architectural Monochrome, Warm Stone/Mineral)
    without washing Dark Mode CTAs into pastels.
    """
    arch = sig.get("vertical_archetype", "editorial_brand")
    vslug = sig.get("vertical_slug") or brand.lower()
    digest = hashlib.sha256(f"{brand.lower()}::{vslug}::{sig.get('sun_lon', 0)}".encode("utf-8")).digest()
    h_shift = float((digest[0] % 8) * 14)

    if seed_hex:
        _, seed_c, seed_h = hex_to_oklch(seed_hex)
        prim_l_tok = make_color_token(min(0.50, max(0.36, hex_to_oklch(seed_hex)[0])), max(0.08, seed_c), seed_h, "Semilla primaria", hex_override=seed_hex)
        item1 = {
            "id": "eco_1_seed_identity",
            "name": f"Identidad Directa ({seed_hex.upper()})",
            "recommended_mode": "light" if (not bg_hex or wcag_relative_luminance(bg_hex) >= 0.25) else "dark",
            "color_strategy": "Committed",
            "concept": f"Paleta derivada desde color semilla {seed_hex.upper()} con neutros tintados.",
            "light": {
                "background": bg_hex or make_color_token(0.982, 0.006, seed_h, "Lienzo")["hex"],
                "surface": make_color_token(0.948, 0.009, seed_h, "Superficie")["hex"],
                "primary": prim_l_tok["hex"],
                "accent": accent_hex or make_color_token(0.42, min(0.16, seed_c), (seed_h + 140.0) % 360.0, "Acento")["hex"],
                "secondary": make_color_token(0.48, 0.05, seed_h, "Secundario")["hex"],
                "text_primary": make_color_token(0.15, 0.012, seed_h, "Tinta")["hex"],
                "text_muted": make_color_token(0.44, 0.012, seed_h, "Tinta secundaria")["hex"],
            },
        }
        ecos, _ = compile_art_direction_ecosystems([
            item1,
            {
                "id": "eco_2_monochrome_charcoal",
                "name": "Monolito Monocromático (Carbón & Alabastro)",
                "recommended_mode": "dark",
                "color_strategy": "Restrained",
                "concept": "Autoridad suiza sin ruido cromático.",
                "dark": {"background": "#121316", "surface": "#1b1c20", "primary": "#f2efe9", "accent": "#c8c4bc", "secondary": "#8c8982", "text_primary": "#f3f1ed", "text_muted": "#a3a098"},
                "light": {"background": "#faf8f4", "surface": "#efede7", "primary": "#18191d", "accent": "#3e4047", "secondary": "#66645e", "text_primary": "#141518", "text_muted": "#53514b"},
            },
            {
                "id": "eco_3_mineral_complement",
                "name": "Contraste Mineral Complementario",
                "recommended_mode": "light",
                "color_strategy": "Full Palette",
                "concept": "Alternativa complementaria dividida para campaña.",
                "light": {
                    "background": "#f6f8f7",
                    "surface": "#eaf0ed",
                    "primary": make_color_token(0.39, 0.125, (seed_h + 152.0) % 360.0, "Primario")["hex"],
                    "accent": seed_hex,
                    "secondary": make_color_token(0.46, 0.04, (seed_h + 152.0) % 360.0, "Secundario")["hex"],
                    "text_primary": "#111715",
                    "text_muted": "#4b5551",
                },
            },
        ], source_label="seed_hex_pb19")
        return ecos

    # 3 genuinely contrasting architectural/editorial palettes
    if sig.get("has_oraculo"):
        oraculo_bases = {
            "Water": (254.0, 0.37, 0.49, 0.142, "Tinta Ultramar Prusia"),
            "Fire": (20.0, 0.40, 0.50, 0.165, "Carmesí Veneciano"),
            "Wood": (154.0, 0.36, 0.48, 0.125, "Pino Alpino Mineral"),
            "Earth": (38.0, 0.40, 0.50, 0.122, "Siena Mineral"),
            "Metal": (268.0, 0.35, 0.48, 0.088, "Pizarra Índigo Forjada"),
            "Air": (244.0, 0.38, 0.49, 0.132, "Cobalto Arquitectónico"),
        }
        ys = _norm_element(sig.get("yong_shen") or "")
        sun_el = _ZODIAC_ELEMENT.get(sig.get("sun_sign") or "", "")
        dom_el = _norm_element(sig.get("dominant_element") or "") or sun_el
        dm_el = _DAY_MASTER_ELEMENT.get(str(sig.get("bazi_day_master") or "").lower(), "")
        prim_el = ys or dom_el or dm_el or "Water"
        counter_candidates = [dm_el, dom_el, "Wood" if prim_el != "Wood" else "Fire", "Earth"]
        counter_el = next((c for c in counter_candidates if c and c != prim_el and c in oraculo_bases), "Wood")

        h1_b, l1_l, l1_d, c1, label1 = oraculo_bases.get(prim_el, oraculo_bases["Water"])
        h3_b, l3_l, l3_d, c3, label3 = oraculo_bases.get(counter_el, oraculo_bases["Wood"])
        sun_mod = (((float(sig.get("sun_lon") or 0.0) % 30.0) - 15.0) * 0.45)
        h1 = (h1_b + sun_mod) % 360.0
        h3 = (h3_b - sun_mod * 0.6) % 360.0
        for hv_name in ("h1", "h3"):
            hv = h1 if hv_name == "h1" else h3
            if 82.0 <= hv <= 122.0:
                hv = 154.0
            elif 195.0 <= hv <= 228.0:
                hv = 252.0  # Keep Prussian/Ultramarine instead of SaaS cyan
            if hv_name == "h1":
                h1 = hv
            else:
                h3 = hv

        oraculo_accents = {
            "Water": ((66.0, 0.80, 0.060), (242.0, 0.33, 0.042)),  # Burnished champagne-bronze (dark) & deep slate (light)
            "Fire":  ((64.0, 0.81, 0.048), (248.0, 0.32, 0.045)),  # Warm bone-bronze & prussian slate
            "Wood":  ((58.0, 0.79, 0.070), (38.0, 0.38, 0.065)),   # Antique ochre stone & roasted umber
            "Earth": ((66.0, 0.80, 0.055), (156.0, 0.35, 0.055)),  # Warm mineral linen & alpine slate
            "Metal": ((68.0, 0.80, 0.050), (240.0, 0.32, 0.040)),  # Champagne pewter & charcoal slate
            "Air":   ((66.0, 0.80, 0.058), (245.0, 0.33, 0.045)),  # Warm mineral champagne & cobalt ink
        }
        (ad_h, ad_l, ad_c), (al_h, al_l, al_c) = oraculo_accents.get(prim_el, oraculo_accents["Water"])
        (a3d_h, a3d_l, a3d_c), _ = oraculo_accents.get(counter_el, oraculo_accents["Wood"])

        p1_light = make_color_token(l1_l, c1, h1, f"Primario {label1}")["hex"]
        a1_light = make_color_token(al_l, al_c, al_h, "Acento sobrio editorial")["hex"]
        p1_dark = make_color_token(l1_d, c1, h1, f"Primario Step-9 {label1}")["hex"]
        a1_dark = make_color_token(ad_l, ad_c, ad_h, "Acento champán mineral")["hex"]
        p3_light = make_color_token(l3_l, c3, h3, f"Primario {label3}")["hex"]
        a3_light = make_color_token(0.42, c1 * 0.85, h1, "Acento focal")["hex"]
        p3_dark = make_color_token(l3_d, c3, h3, f"Primario Step-9 {label3}")["hex"]
        a3_dark = make_color_token(a3d_l, a3d_c, a3d_h, "Acento mineral cálido")["hex"]

        chart_axis = " · ".join([p for p in (f"Yong Shen {ys}" if ys else "", f"DM {sig.get('bazi_day_master')}" if sig.get("bazi_day_master") else "", f"Nakshatra {sig.get('nakshatra')}" if sig.get("nakshatra") else "", f"Sol {sig.get('sun_sign')}" if sig.get("sun_sign") else "") if p]) or "Síntesis Oráculo"
        eco1_id = f"eco_1_oraculo_{prim_el.lower()}"
        eco1_name = f"{label1} & Alabastro ({chart_axis})"
        eco1_concept = f"Síntesis Step-9 derivada de {chart_axis}: neutros profundos tintados, cero cian neón y cero pasteles apagados."
        eco3_name = f"{label3} & Lino ({counter_el} · Contraste Estructural)"
        eco1_rec_mode = "dark" if prim_el in ("Water", "Metal") else "light"
    else:
        hue_curated = {
            "luxury_editorial": (14.0, 152.0),     # Oxblood & Alpine
            "organic_wellness": (150.0, 28.0),     # Forest Botanical & Terracotta Stone
            "bold_brutalist": (20.0, 250.0),       # Vermilion Signal & Deep Blueprint
            "fintech_clinical": (248.0, 165.0),    # Deep Ink Indigo & Emerald Ledger
            "warm_hospitality": (32.0, 160.0),     # Roasted Sienna & Sage
            "creative_playful": (348.0, 158.0),    # Vivid Crimson & Mineral Mint
            "cosmic_archetypal": (262.0, 168.0),   # Astral Observatory Indigo & Jade
            "design_system_atelier": (228.0, 18.0),# Blueprint Cobalt & Editorial Signal
            "editorial_manifesto": (16.0, 238.0),  # Broadsheet Carmine & Prussian Ink
            "architectural_b2b": (244.0, 154.0),   # Deep Cobalt Ink & Mineral Spruce
            "editorial_brand": (16.0, 156.0),      # Deep Oxblood Editorial & Alpine Slate
        }
        base_h, alt_h = hue_curated.get(arch, (16.0, 156.0))
        h1 = (base_h + (h_shift * 0.4)) % 360.0
        h3 = (alt_h + (h_shift * 0.5)) % 360.0
        if 82.0 <= h3 <= 122.0:
            h3 = 156.0

        def _editorial_accent_hue(src_h: float, shift: float) -> Tuple[float, float]:
            cand = (src_h + shift) % 360.0
            if (268.0 <= cand <= 332.0) or (180.0 <= cand <= 232.0):
                return 64.0, 0.062  # Restrained burnished champagne instead of pastel lavender / neon cyan
            return cand, 0.095

        ad1_h, ad1_c = _editorial_accent_hue(h1, 32.0)
        ad3_h, ad3_c = _editorial_accent_hue(h3, 28.0)
        p1_light = make_color_token(0.41, 0.165, h1, "Primario editorial")["hex"]
        a1_light = make_color_token(0.32, 0.065, ad1_h, "Acento secundario")["hex"]
        p1_dark = make_color_token(0.49, 0.165, h1, "Primario sólido intenso")["hex"]
        a1_dark = make_color_token(0.79, ad1_c, ad1_h, "Acento cálido")["hex"]
        p3_light = make_color_token(0.38, 0.115, h3, "Primario mineral")["hex"]
        a3_light = make_color_token(0.44, 0.145, h1, "Acento focal")["hex"]
        p3_dark = make_color_token(0.47, 0.115, h3, "Primario mineral oscuro")["hex"]
        a3_dark = make_color_token(0.78, ad3_c, ad3_h, "Acento mineral")["hex"]

        eco1_id = f"eco_1_{arch[:10].rstrip('_')}_editorial"
        eco1_name = f"Alabastro & Pigmento Rico ({arch.replace('_', ' ').title()})"
        eco1_concept = "Papel cálido mineral y botón Step-9 intenso con texto marfil nítido (sin pasteles lavados)."
        eco3_name = "Bosque Mineral & Lino"
        eco1_rec_mode = "dark" if arch in ("cosmic_archetypal", "design_system_atelier") else "light"

    raw_ecos = [
        {
            "id": eco1_id,
            "name": eco1_name,
            "recommended_mode": eco1_rec_mode,
            "color_strategy": "Committed",
            "concept": eco1_concept,
            "light": {
                "background": make_color_token(0.978, 0.007, h1, "Papel alabastro")["hex"],
                "surface": make_color_token(0.942, 0.010, h1, "Superficie papel")["hex"],
                "primary": p1_light,
                "accent": a1_light,
                "secondary": "#4c4a46",
                "text_primary": make_color_token(0.155, 0.011, h1, "Tinta profunda")["hex"],
                "text_muted": make_color_token(0.440, 0.011, h1, "Tinta secundaria")["hex"],
            },
            "dark": {
                "background": make_color_token(0.132, 0.010, h1, "Obsidiana cálida")["hex"],
                "surface": make_color_token(0.184, 0.011, h1, "Superficie carbón")["hex"],
                "primary": p1_dark,
                "accent": a1_dark,
                "secondary": "#9a958d",
                "text_primary": make_color_token(0.932, 0.007, h1, "Marfil anti-halación")["hex"],
                "text_muted": make_color_token(0.730, 0.009, h1, "Gris cálido")["hex"],
            },
        },
        {
            "id": f"eco_2_{arch[:10].rstrip('_')}_monochrome",
            "name": "Monolito Suizo (Obsidiana & Hueso)",
            "recommended_mode": "dark",
            "color_strategy": "Restrained",
            "concept": "Contraste tipográfico acromático cálido: cero distracciones, máxima autoridad.",
            "dark": {"background": "#121316", "surface": "#1a1c20", "primary": "#f3f0ea", "accent": "#c9c4ba", "secondary": "#8c8982", "text_primary": "#f4f2ec", "text_muted": "#a3a098"},
            "light": {"background": "#faf8f4", "surface": "#efede7", "primary": "#16171b", "accent": "#3f4148", "secondary": "#66635d", "text_primary": "#141518", "text_muted": "#53504a"},
        },
        {
            "id": f"eco_3_{arch[:10].rstrip('_')}_mineral",
            "name": eco3_name,
            "recommended_mode": "light",
            "color_strategy": "Full Palette",
            "concept": "Profundidad orgánica mineral equilibrada con lino natural y señal focal contenida.",
            "light": {
                "background": make_color_token(0.978, 0.007, h3, "Lino mineral")["hex"],
                "surface": make_color_token(0.942, 0.010, h3, "Superficie lino")["hex"],
                "primary": p3_light,
                "accent": a3_light,
                "secondary": "#47554e",
                "text_primary": make_color_token(0.155, 0.010, h3, "Tinta mineral")["hex"],
                "text_muted": make_color_token(0.440, 0.010, h3, "Gris mineral")["hex"],
            },
            "dark": {
                "background": make_color_token(0.132, 0.011, h3, "Basalto oscuro")["hex"],
                "surface": make_color_token(0.184, 0.011, h3, "Pizarra Z1")["hex"],
                "primary": p3_dark,
                "accent": a3_dark,
                "secondary": "#8b9891",
                "text_primary": make_color_token(0.932, 0.007, h3, "Blanco lino")["hex"],
                "text_muted": make_color_token(0.730, 0.009, h3, "Salvia gris")["hex"],
            },
        },
    ]
    ecos, _ = compile_art_direction_ecosystems(raw_ecos, source_label="pb19_editorial_fallback")
    if sib_used_ids and ecos[0]["id"] in sib_used_ids:
        for i in range(1, len(ecos)):
            if ecos[i]["id"] not in sib_used_ids:
                ecos = ecos[i:] + ecos[:i]
                break
    return ecos


# -----------------------------------------------------------------------------
# Downstream Token Compilers: W3C DTCG 2025.10, CSS Color Level 5, brandfont
# -----------------------------------------------------------------------------

def _dtcg_color_obj(tok: Dict[str, Any]) -> Dict[str, Any]:
    c = tok["components"]
    return {
        "$type": "color",
        "$value": {"colorSpace": "oklch", "components": [c["lightness"], c["chroma"], c["hue"]], "alpha": 1, "hex": tok["hex"]},
        "$description": tok.get("$description", ""),
    }


def build_dtcg_3_layer_tokens(selected: Dict[str, Any], geom: Dict[str, Any]) -> Dict[str, Any]:
    lt, dk = selected["themes"]["light"], selected["themes"]["dark"]
    return {
        "$schema": "https://www.designtokens.org/tr/2025.10/format/",
        "color": {
            "primitive": {
                "$type": "color",
                "light": {k: _dtcg_color_obj(v) for k, v in lt.items() if isinstance(v, dict) and "components" in v},
                "dark": {k: _dtcg_color_obj(v) for k, v in dk.items() if isinstance(v, dict) and "components" in v},
            },
            "semantic": {
                "$type": "color",
                "bg": {"$value": "{color.primitive.light.background}"},
                "surface": {"$value": "{color.primitive.light.surface}"},
                "surface_elevated": {"$value": "{color.primitive.light.surface_elevated}"},
                "border": {"$value": "{color.primitive.light.border_subtle}"},
                "text": {"$value": "{color.primitive.light.text_primary}"},
                "muted": {"$value": "{color.primitive.light.text_muted}"},
                "primary": {"$value": "{color.primitive.light.primary}"},
                "on_primary": {"$value": "{color.primitive.light.on_primary}"},
                "accent": {"$value": "{color.primitive.light.accent}"},
                "on_accent": {"$value": "{color.primitive.light.on_accent}"},
                "success": {"$value": "{color.primitive.light.feedback_success}"},
                "warning": {"$value": "{color.primitive.light.feedback_warning}"},
                "error": {"$value": "{color.primitive.light.feedback_error}"},
                "info": {"$value": "{color.primitive.light.feedback_info}"},
            },
        },
        "component": {
            "radius_card": {"$type": "dimension", "$value": {"value": int(str(geom["radius_card"]).replace("px", "")), "unit": "px"}},
            "radius_control": {"$type": "dimension", "$value": {"value": int(str(geom["radius_control"]).replace("px", "")), "unit": "px"}},
            "elevation_style": {"$type": "string", "$value": geom["elevation_style"]},
            "color_strategy": {"$type": "string", "$value": selected.get("color_strategy", geom["color_strategy"])},
            "proportion": {"$type": "string", "$value": "60-30-10"},
        },
        "resolver": {
            "modifiers": {
                "theme": {"contexts": {"light": {"ref": "#/color/primitive/light"}, "dark": {"ref": "#/color/primitive/dark"}}}
            }
        },
    }


def build_brandfont_export(brand: str, vslug: str, arch: str, ecosystems: List[Dict[str, Any]]) -> Dict[str, Any]:
    bf_ecos = []
    for eco in ecosystems:
        rec = eco.get("recommended_mode", "light")
        t = eco["themes"][rec]
        bf_ecos.append({
            "id": eco["id"],
            "title": eco["name"],
            "recommended_mode": rec,
            "color_strategy": eco.get("color_strategy", "Committed"),
            "tokens": [
                {"role": r, "oklch": t[k]["$value"], "hex": t[k]["hex"], "name": t[k].get("$description", lbl)}
                for k, r, lbl in (
                    ("primary", "primary", "Primary"), ("on_primary", "on_primary", "On Primary"),
                    ("secondary", "secondary", "Secondary"), ("accent", "accent", "Accent"),
                    ("background", "bg", "Background"), ("surface", "surface", "Surface"),
                    ("text_primary", "text", "Text Primary"), ("text_muted", "muted", "Text Muted"),
                )
            ],
        })
    return {"id": (vslug or brand).lower(), "name": brand.upper(), "archetype": arch, "ecosystems": bf_ecos}


def build_css_blocks(selected: Dict[str, Any], brand_slug: str, arch: str, geom: Dict[str, Any]) -> Dict[str, Any]:
    d, lt = selected["themes"]["dark"], selected["themes"]["light"]
    default_mode = selected.get("recommended_mode", "light")
    root_src, alt_src, alt_attr = (lt, d, '[data-theme="dark"]') if default_mode == "light" else (d, lt, '[data-theme="light"]')
    elev_rule = (
        "--elevation-card: none; --card-border: 1px solid color-mix(in oklch, var(--brand-muted) 20%, transparent);"
        if geom["elevation_style"] == "border_1px"
        else "--elevation-card: 0 12px 32px -12px color-mix(in oklch, var(--brand-text) 14%, transparent); --card-border: 1px solid transparent;"
    )

    def _mv(src: Dict[str, Any], is_dark: bool) -> str:
        delta = "0.07" if is_dark else "-0.06"
        return (
            f"  color-scheme: {'dark' if is_dark else 'light'};\n"
            f"  --brand-primary: {src['primary']['$value']};\n"
            f"  --brand-primary-hover: oklch(from var(--brand-primary) calc(l + {delta}) c h);\n"
            f"  --brand-on-primary: {src['on_primary']['$value']};\n"
            f"  --brand-secondary: {src['secondary']['$value']};\n"
            f"  --brand-accent: {src['accent']['$value']};\n"
            f"  --brand-on-accent: {src['on_accent']['$value']};\n"
            f"  --brand-bg: {src['background']['$value']};\n"
            f"  --brand-surface: {src['surface']['$value']};\n"
            f"  --brand-surface-elevated: {src['surface_elevated']['$value']};\n"
            f"  --brand-border: {src['border_subtle']['$value']};\n"
            f"  --brand-text: {src['text_primary']['$value']};\n"
            f"  --brand-muted: {src['text_muted']['$value']};\n"
            f"  --feedback-success: {src['feedback_success']['$value']};\n"
            f"  --feedback-warning: {src['feedback_warning']['$value']};\n"
            f"  --feedback-error: {src['feedback_error']['$value']};\n"
            f"  --feedback-info: {src['feedback_info']['$value']};\n"
        )

    tailwind_block = (
        "@theme inline {\n"
        "  --color-brand-primary: var(--brand-primary);\n  --color-brand-primary-hover: var(--brand-primary-hover);\n"
        "  --color-brand-on-primary: var(--brand-on-primary);\n  --color-brand-secondary: var(--brand-secondary);\n"
        "  --color-brand-accent: var(--brand-accent);\n  --color-brand-on-accent: var(--brand-on-accent);\n"
        "  --color-brand-bg: var(--brand-bg);\n  --color-brand-surface: var(--brand-surface);\n"
        "  --color-brand-surface-elevated: var(--brand-surface-elevated);\n  --color-brand-border: var(--brand-border);\n"
        "  --color-brand-text: var(--brand-text);\n  --color-brand-muted: var(--brand-muted);\n"
        "  --radius-card: var(--brand-radius-card);\n  --radius-control: var(--brand-radius-control);\n}"
    )
    bslug = re.sub(r"[^a-z0-9-]+", "-", brand_slug.lower()).strip("-") or "default"
    css_root = (
        f"/* Default: {default_mode} | Strategy: {selected.get('color_strategy')} | Profile: {arch} */\n"
        f":root,\n[data-brand=\"{bslug}\"] {{\n"
        f"  --brand-radius-card: {geom['radius_card']};\n  --brand-radius-control: {geom['radius_control']};\n  {elev_rule}\n"
        + _mv(root_src, default_mode == "dark") + "}\n"
        f"[data-brand=\"{bslug}\"]{alt_attr},\n{alt_attr} {{\n"
        + _mv(alt_src, default_mode != "dark") + "}\n"
        ":root { accent-color: var(--brand-primary); caret-color: var(--brand-primary); scrollbar-color: color-mix(in oklch, var(--brand-text) 28%, transparent) var(--brand-bg); }\n"
        "::selection { background-color: color-mix(in oklch, var(--brand-primary) 24%, transparent); color: var(--brand-text); }\n"
        ":focus-visible { outline: 2px solid var(--brand-accent); outline-offset: 2px; }\n"
        "@media (prefers-contrast: more) { :root { --card-border: 1px solid var(--brand-text); } }"
    )
    anti_fouc = (
        "<script is:inline>\n  (() => {\n    const sync = () => {\n"
        "      const saved = localStorage.getItem('theme');\n"
        "      const sys = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';\n"
        f"      document.documentElement.dataset.theme = (saved === 'light' || saved === 'dark') ? saved : '{default_mode}' || sys;\n"
        "    };\n    sync();\n    document.addEventListener('astro:after-swap', sync);\n  })();\n</script>"
    )
    return {
        "default_mode": default_mode,
        "brand_selector": f'[data-brand="{bslug}"]',
        "tailwind_v4_theme_block": tailwind_block,
        "css_variables_root": css_root,
        "astro_anti_fouc_head_snippet": anti_fouc,
        "gradient_interpolation": "in oklch",
    }


# -----------------------------------------------------------------------------
# Visual HTML Preview (v8.0 — Real Mini Editorial UI Compositions + Token Grid)
# -----------------------------------------------------------------------------

def render_chroma_preview_html(manifest: Dict[str, Any]) -> str:
    brand_esc = html_lib.escape(str(manifest.get("brand", "BRAND")))
    vslug = html_lib.escape(str(manifest.get("vertical_slug") or manifest.get("brand", "")))
    sel_id = manifest.get("selected_ecosystem_id")
    arch_esc = html_lib.escape(str(manifest.get("vertical_archetype") or "editorial_brand"))
    geom = manifest.get("surface_geometry") or {"radius_card": "10px", "radius_control": "6px"}
    rc, rbtn = html_lib.escape(str(geom.get("radius_card", "10px"))), html_lib.escape(str(geom.get("radius_control", "6px")))

    eco_tabs = '<button type="button" class="ctrl-btn active" data-eco-btn="all">Todos ({})</button>'.format(len(manifest.get("ecosystems", [])))
    cards_html = []
    for eco in manifest.get("ecosystems", []):
        eid = eco["id"]
        is_sel = eid == sel_id
        rec = eco.get("recommended_mode", "light").upper()
        eco_tabs += f'<button type="button" class="ctrl-btn" data-eco-btn="{html_lib.escape(eid)}">{html_lib.escape(eco["name"])}</button>'

        mode_panes = []
        order = ("light", "dark") if rec == "LIGHT" else ("dark", "light")
        for mode_name in order:
            t = eco["themes"][mode_name]
            au = eco["audit"][mode_name]
            bg_h, sf_h, el_h, bd_h = t["background"]["hex"], t["surface"]["hex"], t["surface_elevated"]["hex"], t["border_subtle"]["hex"]
            tx_h, mu_h = t["text_primary"]["hex"], t["text_muted"]["hex"]
            pr_h, on_p = t["primary"]["hex"], t["on_primary"]["hex"]
            ac_h, on_a = t["accent"]["hex"], t["on_accent"]["hex"]
            swatches = "".join(
                f'<div class="sw-row"><span class="sw" style="background:{html_lib.escape(tok["hex"])}"></span>'
                f'<code>{html_lib.escape(role)}</code><span class="hx">{html_lib.escape(tok["hex"])}</span>'
                f'<span class="ok">{html_lib.escape(tok["$value"])}</span></div>'
                for role, tok in t.items() if isinstance(tok, dict) and "hex" in tok
            )
            mode_panes.append(f"""
            <div class="mode-pane" data-mode-pane="{mode_name}" style="background:{bg_h};color:{tx_h};border:1px solid {bd_h};border-radius:{rc}">
              <div class="pane-head" style="border-bottom:1px solid {bd_h}">
                <strong>{mode_name.upper()} MODE</strong>
                <span class="metrics">WCAG {au['body_to_bg_ratio']}:1 · Btn {au['button_to_bg_ratio']}:1 · APCA Lc {au['body_lc']}</span>
              </div>
              <div class="ui-comp" style="background:{sf_h};border:1px solid {bd_h};border-radius:{rc}">
                <span class="eyebrow" style="color:{ac_h};border:1px solid {bd_h}">Sistema {vslug}</span>
                <h3>Arquitectura editorial con jerarquía real</h3>
                <p style="color:{mu_h}">Composición verificada sobre neutrales tintados OKLCH, diferenciación acromática y contraste sostenido.</p>
                <div class="cta-row">
                  <span class="btn-solid" style="background:{pr_h};color:{on_p};border-radius:{rbtn}">Acción primaria</span>
                  <span class="btn-acc" style="background:{ac_h};color:{on_a};border-radius:{rbtn}">Acento</span>
                  <span class="btn-ghost" style="color:{tx_h};border:1px solid {bd_h};border-radius:{rbtn}">Secundario</span>
                </div>
                <div class="z2-card" style="background:{el_h};border:1px solid {bd_h};border-radius:{rc}">
                  <small style="color:{mu_h}">Superficie Elevada Z2 · Feedback Semántico</small>
                  <div class="fb-pills">
                    <span style="color:{t['feedback_success']['hex']}">● Éxito</span>
                    <span style="color:{t['feedback_warning']['hex']}">● Aviso</span>
                    <span style="color:{t['feedback_error']['hex']}">● Error</span>
                    <span style="color:{t['feedback_info']['hex']}">● Info</span>
                  </div>
                </div>
              </div>
              <div class="swatches">{swatches}</div>
            </div>""")

        cards_html.append(f"""
        <section class="eco-section{' selected' if is_sel else ''}" data-eco-id="{html_lib.escape(eid)}">
          <div class="eco-head">
            <h2>{html_lib.escape(eco['name'])}</h2>
            <span class="tag">{'SELECCIONADO · ' if is_sel else ''}Recomendado: {rec} · {html_lib.escape(eco.get('color_strategy', 'Committed'))}</span>
          </div>
          <p class="concept">{html_lib.escape(eco['concept'])}</p>
          <div class="modes-grid">{''.join(mode_panes)}</div>
        </section>""")

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Chroma Engine v8.0 — {vslug} ({brand_esc})</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:system-ui,-apple-system,sans-serif; background:#0e1014; color:#eceef2; padding:26px; transition:filter .2s ease; }}
  body.achromatic-sim {{ filter: grayscale(1); }}
  .wrap {{ max-width:1360px; margin:0 auto; display:flex; flex-direction:column; gap:20px; }}
  h1 {{ font-size:22px; margin-bottom:4px; }}
  .sub {{ font-size:13px; color:#9da3b0; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:8px; padding:12px; background:#161920; border:1px solid #282c36; border-radius:12px; }}
  .ctrl-btn {{ background:#1f232c; color:#dde1ea; border:1px solid #343946; border-radius:999px; padding:6px 12px; font-size:12px; font-weight:600; cursor:pointer; }}
  .ctrl-btn.active {{ background:#eceef2; color:#111318; border-color:#eceef2; }}
  .eco-section {{ background:#15181f; border:1px solid #272b35; border-radius:14px; padding:20px; display:flex; flex-direction:column; gap:12px; }}
  .eco-section.selected {{ border-color:#8b95a8; }}
  .eco-section.is-hidden {{ display:none; }}
  .eco-head {{ display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; }}
  .eco-head h2 {{ font-size:17px; }}
  .tag {{ font-size:11px; font-weight:700; padding:4px 10px; border-radius:999px; background:#232834; color:#e2e6ee; }}
  .concept {{ font-size:13px; color:#a2a8b5; }}
  .modes-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(460px, 1fr)); gap:16px; }}
  .mode-pane {{ padding:16px; display:flex; flex-direction:column; gap:14px; }}
  .mode-pane.is-hidden {{ display:none; }}
  .pane-head {{ display:flex; justify-content:space-between; align-items:center; padding-bottom:8px; font-size:12px; }}
  .metrics {{ font-family:ui-monospace,monospace; font-size:11px; opacity:.85; }}
  .ui-comp {{ padding:16px; display:flex; flex-direction:column; gap:10px; }}
  .eyebrow {{ align-self:flex-start; font-size:11px; font-weight:700; padding:2px 8px; border-radius:999px; }}
  .ui-comp h3 {{ font-size:19px; line-height:1.2; }}
  .ui-comp p {{ font-size:13px; line-height:1.5; }}
  .cta-row {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
  .btn-solid, .btn-acc, .btn-ghost {{ font-size:12px; font-weight:700; padding:8px 14px; display:inline-block; }}
  .z2-card {{ padding:10px 12px; display:flex; flex-direction:column; gap:6px; margin-top:4px; }}
  .fb-pills {{ display:flex; gap:12px; flex-wrap:wrap; font-size:11px; font-weight:600; }}
  .swatches {{ display:grid; grid-template-columns:1fr; gap:5px; }}
  .sw-row {{ display:grid; grid-template-columns:18px 135px 72px 1fr; gap:8px; align-items:center; font-size:11px; font-family:ui-monospace,monospace; }}
  .sw {{ width:16px; height:16px; border-radius:4px; border:1px solid rgba(128,128,128,.35); display:inline-block; }}
  .ok {{ opacity:.75; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Chroma Engine v8.0 — {vslug} ({arch_esc})</h1>
    <p class="sub">Fuente: {html_lib.escape(str(manifest.get('source_ssot', '')))} · Contraste WCAG 2.2 AAA + APCA Lc + Elevación Z + Acromático C=0</p>
  </header>
  <div class="controls" id="chromaControls">
    {eco_tabs}
    <button type="button" class="ctrl-btn active" data-mode-btn="both">Ambos Modos</button>
    <button type="button" class="ctrl-btn" data-mode-btn="light">Solo Light</button>
    <button type="button" class="ctrl-btn" data-mode-btn="dark">Solo Dark</button>
    <button type="button" class="ctrl-btn" id="achromBtn">Simular Acromático (C=0)</button>
  </div>
  {''.join(cards_html)}
</div>
<script>
document.addEventListener('DOMContentLoaded', () => {{
  document.querySelectorAll('[data-eco-btn]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const target = btn.getAttribute('data-eco-btn');
      document.querySelectorAll('[data-eco-btn]').forEach(b => b.classList.toggle('active', b === btn));
      document.querySelectorAll('.eco-section').forEach(s => s.classList.toggle('is-hidden', target !== 'all' && s.getAttribute('data-eco-id') !== target));
    }});
  }});
  document.querySelectorAll('[data-mode-btn]').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const mode = btn.getAttribute('data-mode-btn');
      document.querySelectorAll('[data-mode-btn]').forEach(b => b.classList.toggle('active', b === btn));
      document.querySelectorAll('.mode-pane').forEach(p => p.classList.toggle('is-hidden', mode !== 'both' && p.getAttribute('data-mode-pane') !== mode));
    }});
  }});
  const aBtn = document.getElementById('achromBtn');
  if (aBtn) aBtn.addEventListener('click', () => {{
    const on = document.body.classList.toggle('achromatic-sim');
    aBtn.classList.toggle('active', on);
  }});
}});
</script>
</body>
</html>"""


# -----------------------------------------------------------------------------
# Master Orchestration Entrypoint
# -----------------------------------------------------------------------------

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
    spec_path: Optional[Path] = None,
) -> Dict[str, Any]:
    brand_upper = re.sub(r"[^a-zA-Z0-9_-]+", "", brand.strip()).upper() or "BRAND"
    signals = extract_inputs(brief_path, shards_path, vertical_json_path, brand_brief_path, vertical_slug=vertical_slug)
    sib_root = sibling_workspaces_dir
    if not sib_root and output_dir and output_dir.resolve().name == "brand" and output_dir.resolve().parent.parent.name == "workspaces":
        sib_root = output_dir.resolve().parent.parent
    sib_used_ids = _collect_sibling_selected_ids(sib_root, output_dir)

    resolved_spec = spec_path if (spec_path and spec_path.is_file()) else (output_dir / "chroma_spec.json" if (output_dir and (output_dir / "chroma_spec.json").is_file() and mode == "auto") else None)
    override_geom: Optional[Dict[str, Any]] = None

    if resolved_spec:
        raw = json.loads(resolved_spec.read_text(encoding="utf-8"))
        items = raw if isinstance(raw, list) else raw.get("ecosystems") or raw.get("palettes") or [raw]
        ecosystems, override_geom = compile_art_direction_ecosystems(items, source_label=f"art_direction_spec:{resolved_spec.name}")
        source_ssot = f"spec:{resolved_spec.name}"
        if isinstance(raw, dict):
            selected_eco_id = selected_eco_id or raw.get("selected_ecosystem_id")
            if raw.get("vertical_archetype"):
                signals["vertical_archetype"] = str(raw["vertical_archetype"])
            if isinstance(raw.get("surface_geometry"), dict):
                override_geom = raw["surface_geometry"]
    elif palette_json_path and palette_json_path.is_file():
        raw = json.loads(palette_json_path.read_text(encoding="utf-8"))
        items = raw if isinstance(raw, list) else raw.get("ecosystems") or raw.get("palettes") or [raw]
        ecosystems, override_geom = compile_art_direction_ecosystems(items, source_label="curated_palette_json")
        source_ssot = f"art_direction:{palette_json_path.name}"
    elif seed_hex:
        ecosystems = _synthesize_fallback_ecosystems(brand_upper, signals, seed_hex=seed_hex, bg_hex=bg_hex, accent_hex=accent_hex, sib_used_ids=sib_used_ids)
        source_ssot = f"seed_hex:{seed_hex}"
    elif brief_path and brief_path.is_file() and mode in ("brief", "auto"):
        ecosystems = parse_ecosystems_from_brief(brief_path.read_text(encoding="utf-8", errors="replace"))
        if ecosystems:
            source_ssot = f"{brief_path.name} §3 (Oráculo Explicit Opt-In)"
        else:
            ecosystems = _synthesize_fallback_ecosystems(brand_upper, signals, sib_used_ids=sib_used_ids)
            source_ssot = " + ".join(signals["sources"]) or "pb19_editorial_fallback"
    else:
        ecosystems = _synthesize_fallback_ecosystems(brand_upper, signals, sib_used_ids=sib_used_ids)
        source_ssot = " + ".join(signals["sources"]) or "pb19_editorial_fallback"

    if len(ecosystems) < 3:
        fb_pool = _synthesize_fallback_ecosystems(brand_upper, signals, sib_used_ids=sib_used_ids)
        seen_ids = {e["id"] for e in ecosystems}
        for fb in fb_pool:
            if len(ecosystems) >= 3:
                break
            if fb["id"] not in seen_ids:
                ecosystems.append(fb)
                seen_ids.add(fb["id"])

    selected = next((e for e in ecosystems if e["id"] == selected_eco_id), ecosystems[0])
    sel_audit = _audit_ecosystem(selected["themes"])
    arch = signals["vertical_archetype"]
    base_geom = SURFACE_GEOMETRY_PROFILES.get(arch, SURFACE_GEOMETRY_PROFILES["editorial_brand"])
    geom = {**base_geom, **(override_geom or {})}
    vslug_final = vertical_slug or signals.get("vertical_slug") or brand_upper.lower()

    manifest: Dict[str, Any] = {
        "$schema": "https://www.designtokens.org/tr/2025.10/color/",
        "brand": brand_upper,
        "vertical_archetype": arch,
        "color_strategy": selected.get("color_strategy", geom["color_strategy"]),
        "surface_geometry": {
            "radius_card": geom["radius_card"],
            "radius_control": geom["radius_control"],
            "elevation_style": geom["elevation_style"],
            "proportion": "60-30-10",
            "rule": "single_elevation_border_or_shadow_never_both",
        },
        "engine": "chroma_engine.py v8.0 (Art-Direction-First + OKLCH Gamut-Mapped + W3C DTCG 2025.10)",
        "color_space": "oklch",
        "selected_ecosystem_id": selected["id"],
        "recommended_mode": selected.get("recommended_mode", "light"),
        "source_ssot": source_ssot,
        "inputs_used": signals,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ecosystems": ecosystems,
        "themes": selected["themes"],
        "dtcg_tokens": build_dtcg_3_layer_tokens(selected, geom),
        "brandfont_export": build_brandfont_export(brand_upper, vslug_final, arch, ecosystems),
        "accessibility_audit": {
            "wcag_2_2_compliance": {
                "body_to_bg_ratio": min(sel_audit["dark"]["body_to_bg_ratio"], sel_audit["light"]["body_to_bg_ratio"]),
                "headings_to_bg_ratio": min(sel_audit["dark"]["headings_to_bg_ratio"], sel_audit["light"]["headings_to_bg_ratio"]),
                "button_to_bg_ratio": min(sel_audit["dark"]["button_to_bg_ratio"], sel_audit["light"]["button_to_bg_ratio"]),
                "status_aaa": sel_audit["status_aaa"],
            },
            "apca_compliance": {
                "body_lc": min(sel_audit["dark"]["body_lc"], sel_audit["light"]["body_lc"]),
                "headings_lc": min(sel_audit["dark"]["headings_lc"], sel_audit["light"]["headings_lc"]),
                "ui_components_lc": min(sel_audit["dark"]["ui_components_lc"], sel_audit["light"]["ui_components_lc"]),
            },
            "achromatic_audit": sel_audit["achromatic_audit"],
        },
        "css_integration": build_css_blocks(selected, brand_slug=vslug_final, arch=arch, geom=geom),
    }
    if vslug_final:
        manifest["vertical_slug"] = vslug_final
    return manifest


def run_unit_tests() -> int:
    print("Running chroma_engine v8.0 clean-slate unit tests...")
    with tempfile.TemporaryDirectory(prefix="chroma_v80_test_") as tmp:
        tp = Path(tmp)
        spec_p = tp / "chroma_spec.json"
        spec_p.write_text(json.dumps({
            "selected_ecosystem_id": "eco_1_oxblood_alabaster",
            "surface_geometry": {"radius_card": "8px", "radius_control": "4px", "elevation_style": "border_1px"},
            "ecosystems": [
                {
                    "id": "eco_1_oxblood_alabaster",
                    "name": "Alabastro & Carmesí Sangre de Buey",
                    "recommended_mode": "light",
                    "color_strategy": "Committed",
                    "concept": "Editorial de alto contraste sin pasteles ni cian genérico.",
                    "light": {"background": "#f8f6f2", "surface": "#efece6", "primary": "#8c151c", "accent": "#1e293b", "secondary": "#4f4a45", "text_primary": "#141312", "text_muted": "#56514b"},
                    "dark": {"background": "#111216", "surface": "#181a20", "primary": "#c92a34", "accent": "#d9b99b", "secondary": "#8c8982", "text_primary": "#edeae4", "text_muted": "#a7a49d"},
                },
                {
                    "id": "eco_2_obsidian_bone",
                    "name": "Obsidiana & Hueso Suizo",
                    "recommended_mode": "dark",
                    "color_strategy": "Restrained",
                    "dark": {"background": "#121316", "surface": "#1a1c20", "primary": "#f2efe9", "accent": "#c8c4bc", "secondary": "#8c8982", "text_primary": "#f3f1ed", "text_muted": "#a3a098"},
                },
                {
                    "id": "eco_3_alpine_linen",
                    "name": "Bosque Alpino & Lino",
                    "recommended_mode": "light",
                    "color_strategy": "Full Palette",
                    "light": {"background": "#f5f7f5", "surface": "#e8ede9", "primary": "#164632", "accent": "#9e2a2b", "secondary": "#47574e", "text_primary": "#101713", "text_muted": "#4b5951"},
                },
            ],
        }), encoding="utf-8")

        m_spec = generate_chroma_manifest("CLIENTX", vertical_slug="client-x", spec_path=spec_p)
        assert m_spec["source_ssot"] == "spec:chroma_spec.json"
        assert m_spec["inputs_used"]["has_oraculo"] is False
        assert m_spec["themes"]["light"]["primary"]["hex"] == "#8c151c"
        assert m_spec["themes"]["dark"]["primary"]["hex"] == "#c92a34", "Rich dark Step-9 crimson must NOT be washed into pastel!"
        assert m_spec["themes"]["dark"]["on_primary"]["components"]["lightness"] > 0.90, "Rich dark CTA must keep crisp off-white text!"
        assert m_spec["surface_geometry"]["radius_card"] == "8px"
        assert m_spec["accessibility_audit"]["achromatic_audit"]["status_pass"] is True

        # Non-spec seed_hex + fallback tests
        m_seed = generate_chroma_manifest("SEEDBRAND", seed_hex="#1d4ed8")
        assert m_seed["themes"]["light"]["primary"]["hex"] == "#1d4ed8"
        m_fb = generate_chroma_manifest("ACME", vertical_slug="acme-consulting")
        assert len(m_fb["ecosystems"]) == 3 and m_fb["inputs_used"]["has_oraculo"] is False

        # Explicit Oráculo §3 brief test
        brief_p = tp / "astrobranding_test.md"
        brief_p.write_text(
            "### 3.3 Ecosistema Primario: Abyssal Ink & Crisp Alabaster\nEcosistema rector.\n"
            "#### Modo Oscuro\n| Rol | OKLCH | HEX | Nombre |\n|---|---|---|---|\n"
            "| **color-primary** | `oklch(0.72 0.16 230)` | `#38b6ff` | Zafiro |\n"
            "| **color-secondary** | `oklch(0.55 0.12 245)` | `#2b74b8` | Azul |\n"
            "| **color-accent** | `oklch(0.88 0.12 215)` | `#7be5ff` | Chispa |\n"
            "| **color-background** | `oklch(0.12 0.02 250)` | `#080c14` | Abisal |\n"
            "| **color-surface** | `oklch(0.18 0.02 250)` | `#121824` | Grafito |\n"
            "| **color-text-primary** | `oklch(0.97 0.01 240)` | `#f2f6fa` | Alabastro |\n"
            "| **color-text-muted** | `oklch(0.70 0.03 245)` | `#8e9cb0` | Titanio |\n",
            encoding="utf-8",
        )
        m_br = generate_chroma_manifest("TEST", brief_path=brief_p, mode="brief")
        assert m_br["themes"]["dark"]["primary"]["hex"] == "#38b6ff"

        # Oráculo shards-only Water/Jia vs Fire/Geng synthesis differentiation (Step-9 non-generic hues)
        sh_water = tp / "shards_water.json"
        sh_water.write_text(json.dumps({
            "shard_01": {"data": {"tripod_of_iron": {"sun": {"sign": "Gemini", "longitude": 79.0}, "midheaven_house_10": {"sign": "Gemini"}}}},
            "shard_03": {"data": {"nakshatra": {"name": "Chitra"}}},
            "shard_04": {"data": {"day_master": {"name": "Jia"}, "yong_shen": {"element": "Water"}}},
        }), encoding="utf-8")
        sh_fire = tp / "shards_fire.json"
        sh_fire.write_text(json.dumps({
            "shard_01": {"data": {"tripod_of_iron": {"sun": {"sign": "Leo", "longitude": 132.0}, "midheaven_house_10": {"sign": "Aries"}}}},
            "shard_03": {"data": {"nakshatra": {"name": "Ashwini"}}},
            "shard_04": {"data": {"day_master": {"name": "Geng"}, "yong_shen": {"element": "Fire"}}},
        }), encoding="utf-8")
        m_ow = generate_chroma_manifest("CHARTW", shards_path=sh_water)
        m_of = generate_chroma_manifest("CHARTF", shards_path=sh_fire)
        assert m_ow["inputs_used"]["has_oraculo"] is True
        assert m_ow["themes"]["dark"]["primary"]["hex"] != "#934a00" and m_ow["themes"]["dark"]["primary"]["hex"] != "#38b6ff"
        assert 235.0 <= m_ow["themes"]["dark"]["primary"]["components"]["hue"] <= 275.0, "Water chart must synthesize Prussian/Ultramarine Step-9!"
        assert not (270.0 <= m_ow["themes"]["dark"]["accent"]["components"]["hue"] <= 330.0), "Dark accent must NOT drift into pastel lavender!"
        assert m_ow["themes"]["dark"]["primary"]["hex"] != m_of["themes"]["dark"]["primary"]["hex"]

        brief_sig = parse_oraculo_brief_signals(
            "**Sol Natal** | **Gemini 19°**\n**Medio Cielo** | **Gemini 16°**\n**Nakshatra:** Chitra\n**Day Master:** Jia\n**Elemento Yong Shen:** Agua"
        )
        assert brief_sig["sun_sign"] == "Gemini" and brief_sig["mc_sign"] == "Gemini" and brief_sig["yong_shen"] == "Water" and brief_sig["nakshatra"] == "Chitra"

        for man in (m_spec, m_seed, m_fb, m_br, m_ow, m_of):
            assert man["dtcg_tokens"]["color"]["primitive"]["dark"]["primary"]["$value"]["colorSpace"] == "oklch"
            assert len(man["brandfont_export"]["ecosystems"]) == 3
            assert "oklch(from var(--brand-primary)" in man["css_integration"]["css_variables_root"]
            for eco in man["ecosystems"]:
                assert eco["audit"]["wcag_aaa_ratio"] >= 7.0
                assert eco["audit"]["achromatic_audit"]["status_pass"] is True
                for mn in ("dark", "light"):
                    t = eco["themes"][mn]
                    assert wcag_contrast_ratio(t["on_primary"]["hex"], t["primary"]["hex"]) >= 4.5
                    for tok in t.values():
                        assert tok["hex"].lower() != "#000000"
                        assert tok["hex"].lower() not in BANNED_SLOP_HEXES

        html_out = render_chroma_preview_html(m_spec)
        assert "Chroma Engine v8.0" in html_out and "achromBtn" in html_out
        if shutil.which("node"):
            for i, s_body in enumerate(re.findall(r"<script[^>]*>(.*?)</script>", html_out, re.S)):
                js_tmp = tp / f"chroma_{i}.js"
                js_tmp.write_text(s_body, encoding="utf-8")
                res = subprocess.run(["node", "--check", str(js_tmp)], capture_output=True, text=True)
                assert res.returncode == 0, res.stderr
    print("✅ CHROMA ENGINE v8.0 UNIT TESTS PASSED (Art-Direction-First, gamut-mapped OKLCH, Step-9 rich dark CTAs, DTCG 3-layer, 0 slop)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Chroma Engine v8.0 — Art-Direction-First OKLCH Compiler")
    parser.add_argument("--brand", default="BRAND")
    parser.add_argument("--vertical", default=None)
    parser.add_argument("--spec", type=Path, default=None, help="Explicit Art-Direction chroma_spec.json")
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
        spec_path=args.spec,
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
    print(f"✅ CHROMA ENGINE v8.0 COMPLETED FOR: {manifest['brand']}/{manifest.get('vertical_slug', 'root')} (source={manifest['source_ssot']}, selected={manifest['selected_ecosystem_id']}, default={manifest['recommended_mode']})")
    print(f"  • WCAG 2.2 AAA: {audit['wcag_2_2_compliance']['body_to_bg_ratio']}:1 | Btn: {audit['wcag_2_2_compliance']['button_to_bg_ratio']}:1 | APCA Lc: {audit['apca_compliance']['body_lc']}")
    print(f"  • Output: {out_dir / 'chroma_manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
