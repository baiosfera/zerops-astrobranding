#!/usr/bin/env python3
"""
chroma_engine.py — Sovereign OKLCH Color Architecture & Dual WCAG 2.2 AAA / APCA Engine.
Zero-Hallucination Math | W3C DTCG 2025.10 Tokens | Display P3 | Tailwind CSS v4 @theme.
100% brand-agnostic: derives 3 complete chromatic ecosystems (Dark & Light) from
astrobranding_[brand].md, 15 relational shards, or explicit astrological parameters,
and never creates unrequested global directories.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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
    # Linear sRGB (D65) -> XYZ -> Linear Display P3 (D65)
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

    if y_bg > y_txt:  # Dark text on light background (BoW)
        sapc = ((y_bg ** 0.56) - (y_txt ** 0.57)) * 1.14
        out = 0.0 if sapc < 0.1 else (sapc - 0.027) * 100.0
    else:  # Light text on dark background (WoB)
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
    c_r = round(max(0.0, min(0.4, c)), 3)
    h_r = round(h % 360.0, 1)
    calc_hex, calc_p3 = oklch_to_hex_and_p3(l_r, c_r, h_r)
    final_hex = hex_override.lower() if hex_override and re.match(r"^#[0-9a-fA-F]{6}$", hex_override) else calc_hex
    # Keep formatted oklch string clean (2 decimals if exact, else 3)
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
    """Adjusts token lightness only if contrast falls below WCAG AAA or APCA floor."""
    wcag = wcag_contrast_ratio(fg_tok["hex"], bg_hex)
    lc = apca_contrast_lc(fg_tok["hex"], bg_hex)
    if wcag >= min_wcag and lc >= min_lc:
        return fg_tok
    l_cur = fg_tok["components"]["lightness"]
    c_cur = fg_tok["components"]["chroma"]
    h_cur = fg_tok["components"]["hue"]
    step = 0.02 if is_dark_bg else -0.02
    for _ in range(30):
        l_cur = max(0.05, min(0.99, l_cur + step))
        cand = make_color_token(l_cur, min(c_cur, 0.14 if l_cur > 0.9 else c_cur), h_cur, fg_tok["$description"])
        if wcag_contrast_ratio(cand["hex"], bg_hex) >= min_wcag and apca_contrast_lc(cand["hex"], bg_hex) >= min_lc:
            return cand
    return cand


def synthesize_light_theme(dark_theme: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Mathematically derives a WCAG AAA & APCA Light Mode palette from any Dark Mode palette."""
    p_comp = dark_theme["primary"]["components"]
    s_comp = dark_theme["secondary"]["components"]
    a_comp = dark_theme["accent"]["components"]
    bg_comp = dark_theme["background"]["components"]
    txt_comp = dark_theme["text_primary"]["components"]

    bg_light = make_color_token(0.98, min(0.01, bg_comp["chroma"]), txt_comp["hue"] or p_comp["hue"], f"{dark_theme['background']['$description']} (Light Canvas)")
    surf_light = make_color_token(0.94, min(0.015, bg_comp["chroma"] + 0.005), txt_comp["hue"] or p_comp["hue"], f"{dark_theme['surface']['$description']} (Light Surface)")
    txt_light = _ensure_aaa_contrast(
        make_color_token(0.15, min(0.025, bg_comp["chroma"] + 0.01), bg_comp["hue"], f"{dark_theme['text_primary']['$description']} (Light Ink)"),
        bg_light["hex"], is_dark_bg=False, min_wcag=10.0, min_lc=90.0
    )
    muted_light = make_color_token(0.45, min(0.03, bg_comp["chroma"] + 0.01), bg_comp["hue"], f"{dark_theme['text_muted']['$description']} (Light Muted)")
    prim_light = _ensure_aaa_contrast(
        make_color_token(min(0.42, max(0.28, p_comp["lightness"] - 0.25)), max(0.02, p_comp["chroma"]), p_comp["hue"], f"{dark_theme['primary']['$description']} (Light Contrast)"),
        bg_light["hex"], is_dark_bg=False, min_wcag=7.0, min_lc=75.0
    )
    sec_light = make_color_token(min(0.50, max(0.35, s_comp["lightness"] - 0.08)), max(0.02, s_comp["chroma"]), s_comp["hue"], f"{dark_theme['secondary']['$description']} (Light)")
    acc_light = _ensure_aaa_contrast(
        make_color_token(min(0.36, max(0.24, a_comp["lightness"] - 0.38)), max(0.02, a_comp["chroma"]), a_comp["hue"], f"{dark_theme['accent']['$description']} (Light CTA)"),
        bg_light["hex"], is_dark_bg=False, min_wcag=7.0, min_lc=75.0
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


def _audit_ecosystem(themes: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
    dark = themes["dark"]
    light = themes["light"]

    body_dark = wcag_contrast_ratio(dark["text_primary"]["hex"], dark["background"]["hex"])
    head_dark = wcag_contrast_ratio(dark["primary"]["hex"], dark["background"]["hex"])
    btn_dark = wcag_contrast_ratio(dark["accent"]["hex"], dark["background"]["hex"])
    lc_body_dark = apca_contrast_lc(dark["text_primary"]["hex"], dark["background"]["hex"])
    lc_head_dark = apca_contrast_lc(dark["primary"]["hex"], dark["background"]["hex"])
    lc_ui_dark = apca_contrast_lc(dark["accent"]["hex"], dark["surface"]["hex"])

    body_light = wcag_contrast_ratio(light["text_primary"]["hex"], light["background"]["hex"])
    lc_body_light = apca_contrast_lc(light["text_primary"]["hex"], light["background"]["hex"])

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
            "body_lc": lc_body_light,
            "headings_to_bg_ratio": wcag_contrast_ratio(light["primary"]["hex"], light["background"]["hex"]),
            "headings_lc": apca_contrast_lc(light["primary"]["hex"], light["background"]["hex"]),
        },
        "status_aaa": worst_body_ratio >= 7.0 and worst_body_lc >= 75.0,
    }


# -----------------------------------------------------------------------------
# Brief Markdown Parser (§3 OKLCH Sections) & Solar Polar Synthesizer
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


def _slug_id(name: str, fallback: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", name.split(":")[0].strip().lower()).strip("_")
    return f"eco_{clean[:36]}" if clean else fallback


def parse_ecosystems_from_brief(brief_text: str) -> List[Dict[str, Any]]:
    """
    Extracts explicit §3 OKLCH color tables from an astrobranding_[brand].md brief.
    Returns up to 3 complete Dark+Light ecosystems preserving author descriptions and exact hex/oklch tokens.
    """
    # Split on ### Ecosistema ... sections inside §3
    section_matches = list(re.finditer(r"^###\s+3\.\d+\s+Ecosistema\s+[^:]+:\s*(.+)$", brief_text, re.MULTILINE))
    if not section_matches:
        return []

    ecosystems: List[Dict[str, Any]] = []
    for idx, m in enumerate(section_matches):
        start = m.end()
        end = section_matches[idx + 1].start() if idx + 1 < len(section_matches) else len(brief_text)
        # Stop at next ## top heading
        next_h2 = re.search(r"^##\s+", brief_text[start:end], re.MULTILINE)
        if next_h2:
            end = start + next_h2.start()
        block = brief_text[start:end]
        raw_title = m.group(1).strip()

        # First non-empty narrative paragraph after title as concept
        concept = f"Ecosistema derivado del brief semiótico ({raw_title})."
        for line in block.splitlines():
            ls = line.strip()
            if not ls or ls.startswith("#") or ls.startswith("|") or ls.startswith("**Narrativa"):
                continue
            concept = re.sub(r"\*\*", "", ls)
            break

        # Detect Dark / Light subblocks
        dark_block = block
        light_block = ""
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
                if len(parts) < 3:
                    continue
                role = _role_norm(parts[0])
                if not role:
                    continue
                if "oklch(" not in parts[1].lower():
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

        # Ensure Dark/Light foreground contrast strictly satisfies WCAG AAA & APCA
        dark_tokens["text_primary"] = _ensure_aaa_contrast(dark_tokens["text_primary"], dark_tokens["background"]["hex"], is_dark_bg=True)
        light_tokens["text_primary"] = _ensure_aaa_contrast(light_tokens["text_primary"], light_tokens["background"]["hex"], is_dark_bg=False)

        themes = {"dark": dark_tokens, "light": light_tokens}
        audit = _audit_ecosystem(themes)
        short_id = _slug_id(raw_title.split("(")[0], f"eco_{idx + 1}")
        # Keep concise readable id (e.g. eco_abyssal_ink, eco_monochromatic_platinum, eco_mineral_basalt)
        words = short_id.replace("eco_", "").split("_")[:2]
        eco_id = "eco_" + "_".join(words)

        ecosystems.append({
            "id": eco_id,
            "name": raw_title,
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


def synthesize_polar_ecosystems(sun_lon: float, dominant_element: str, yong_shen: str, venus_deg: float) -> List[Dict[str, Any]]:
    """Computes 3 unique agnostic OKLCH ecosystems (Dark+Light) from astronomical coordinates."""
    base_hue = (sun_lon + 15.0) % 360.0
    elem = str(dominant_element or "Earth").capitalize()
    elem_lc = {"Earth": (0.58, 0.11), "Fire": (0.64, 0.20), "Air": (0.72, 0.15), "Water": (0.54, 0.16)}.get(elem, (0.60, 0.14))
    l_prim, c_prim = elem_lc

    ys = str(yong_shen or "Water").split()[0].capitalize()
    ys_hue = {"Metal": 260.0, "Water": 245.0, "Wood": 145.0, "Fire": 38.0, "Earth": 78.0}.get(ys, 245.0)

    specs = [
        ("eco_anchor_primary", f"Soberanía Elemental ({elem} & {ys})",
         f"Derivado de longitud solar {sun_lon:.1f}° ({elem}) balanceado con {ys}.",
         l_prim, c_prim, base_hue, (base_hue + 18.0) % 360.0, ys_hue),
        ("eco_vanguard_contrast", "Contraste Polar & Geometría Alta",
         "Ecosistema de alto contraste cromático con acento complementario directo.",
         max(0.50, l_prim - 0.06), min(0.24, c_prim + 0.06), base_hue, (base_hue + 180.0) % 360.0, (ys_hue + 20.0) % 360.0),
        ("eco_organic_balance", f"Calidez Orgánica & Fluidez ({ys})",
         f"Matiz atenuado guiado por Venus ({venus_deg:.1f}°) y armonización elemental.",
         min(0.74, l_prim + 0.08), max(0.08, c_prim - 0.04), (venus_deg + 35.0) % 360.0, (base_hue - 25.0) % 360.0, (ys_hue - 30.0) % 360.0),
    ]

    ecosystems: List[Dict[str, Any]] = []
    for eid, name, concept, lp, cp, hp, ha, hb in specs:
        bg_d = make_color_token(0.12, 0.02, hb, "Lienzo oscuro base")
        surf_d = make_color_token(0.18, 0.025, hb, "Superficie elevada")
        prim_d = _ensure_aaa_contrast(make_color_token(max(0.62, lp), cp, hp, "Primario dominante"), bg_d["hex"], is_dark_bg=True)
        sec_d = make_color_token(0.55, max(0.05, cp * 0.75), (hp + 15.0) % 360.0, "Secundario estructural")
        acc_d = _ensure_aaa_contrast(make_color_token(0.84, min(0.22, cp + 0.03), ha, "Acento interactivo CTA"), bg_d["hex"], is_dark_bg=True)
        txt_d = _ensure_aaa_contrast(make_color_token(0.97, 0.01, hp, "Texto principal"), bg_d["hex"], is_dark_bg=True, min_wcag=10.0, min_lc=90.0)
        muted_d = make_color_token(0.70, 0.03, hb, "Texto secundario")

        dark_theme = {
            "primary": prim_d, "secondary": sec_d, "accent": acc_d,
            "background": bg_d, "surface": surf_d, "text_primary": txt_d, "text_muted": muted_d,
        }
        light_theme = synthesize_light_theme(dark_theme)
        themes = {"dark": dark_theme, "light": light_theme}
        audit = _audit_ecosystem(themes)
        ecosystems.append({
            "id": eid, "name": name, "concept": concept, "themes": themes,
            "audit": {"wcag_aaa_ratio": audit["wcag_aaa_ratio"], "apca_lc": audit["apca_lc"], "dark": audit["dark"], "light": audit["light"]},
        })
    return ecosystems


def build_css_blocks(selected: Dict[str, Any]) -> Dict[str, str]:
    d = selected["themes"]["dark"]
    lt = selected["themes"]["light"]
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
        ":root {\n"
        f"  --brand-primary: {d['primary']['$value']};\n"
        f"  --brand-secondary: {d['secondary']['$value']};\n"
        f"  --brand-accent: {d['accent']['$value']};\n"
        f"  --brand-bg: {d['background']['$value']};\n"
        f"  --brand-surface: {d['surface']['$value']};\n"
        f"  --brand-text: {d['text_primary']['$value']};\n"
        f"  --brand-muted: {d['text_muted']['$value']};\n"
        "}\n"
        "[data-theme=\"light\"] {\n"
        f"  --brand-primary: {lt['primary']['$value']};\n"
        f"  --brand-secondary: {lt['secondary']['$value']};\n"
        f"  --brand-accent: {lt['accent']['$value']};\n"
        f"  --brand-bg: {lt['background']['$value']};\n"
        f"  --brand-surface: {lt['surface']['$value']};\n"
        f"  --brand-text: {lt['text_primary']['$value']};\n"
        f"  --brand-muted: {lt['text_muted']['$value']};\n"
        "}"
    )
    return {
        "tailwind_v4_theme_block": tailwind_block,
        "css_variables_root": css_root,
        "gradient_interpolation": "in oklch",
    }


def render_chroma_preview_html(manifest: Dict[str, Any]) -> str:
    brand_esc = html_lib.escape(str(manifest.get("brand", "BRAND")))
    sel_id = manifest.get("selected_ecosystem_id", "")
    sections: List[str] = []

    for eco in manifest.get("ecosystems", []):
        eid = html_lib.escape(eco["id"])
        ename = html_lib.escape(eco["name"])
        econ = html_lib.escape(eco["concept"])
        badge = " · ACTIVO" if eco["id"] == sel_id else ""
        audit = eco.get("audit", {})

        mode_cards: List[str] = []
        for mode_name in ("dark", "light"):
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
                    f'<span>{html_lib.escape(tok["hex"])} · {html_lib.escape(tok["$value"])}</span>'
                    f'<small>{html_lib.escape(tok.get("$description", ""))}</small></div></div>'
                )

            mode_cards.append(
                f'<div class="mode-card" style="background:{bg};color:{txt};border-color:{prim}33">'
                f'<div class="mode-head"><span>{mode_name.upper()} MODE</span>'
                f'<span class="metrics">WCAG {maud.get("body_to_bg_ratio", audit.get("wcag_aaa_ratio"))}:1 · APCA Lc {maud.get("body_lc", audit.get("apca_lc"))}</span></div>'
                f'<div class="sample-ui" style="background:{surf};border-color:{prim}44">'
                f'<h3 style="color:{txt}">Titular con contraste certificado</h3>'
                f'<p style="color:{mut}">Texto secundario legible sobre superficie elevada y enlace en tono primario.</p>'
                f'<button style="background:{prim};color:{bg}">Acción Principal</button> '
                f'<span class="pill" style="border:1px solid {acc};color:{acc}">Acento</span>'
                f'</div>'
                f'<div class="swatches">{"".join(swatches)}</div>'
                f'</div>'
            )

        sections.append(
            f'<section class="eco-block" id="{eid}">'
            f'<h2>{ename}<span class="tag">{badge}</span></h2>'
            f'<p class="concept">{econ}</p>'
            f'<div class="modes-grid">{"".join(mode_cards)}</div>'
            f'</section>'
        )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Chroma OKLCH Preview — {brand_esc}</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; background:#0b0f17; color:#f1f5f9; margin:0; padding:32px 24px; }}
  .wrap {{ max-width:1280px; margin:0 auto; display:flex; flex-direction:column; gap:32px; }}
  h1 {{ margin:0 0 6px; font-size:24px; }}
  .sub {{ color:#94a3b8; font-size:14px; margin:0; }}
  .eco-block {{ background:#111827; border:1px solid #1f2937; border-radius:14px; padding:24px; }}
  .eco-block h2 {{ margin:0 0 6px; font-size:19px; }}
  .tag {{ font-size:12px; color:#38bdf8; font-weight:700; }}
  .concept {{ color:#94a3b8; font-size:14px; margin:0 0 18px; }}
  .modes-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(360px,1fr)); gap:18px; }}
  .mode-card {{ border:1px solid; border-radius:12px; padding:18px; display:flex; flex-direction:column; gap:14px; }}
  .mode-head {{ display:flex; justify-content:space-between; font-size:12px; font-weight:700; opacity:.85; }}
  .sample-ui {{ padding:14px; border-radius:10px; border:1px solid; }}
  .sample-ui h3 {{ margin:0 0 6px; font-size:16px; }}
  .sample-ui p {{ margin:0 0 12px; font-size:13px; }}
  .sample-ui button {{ border:none; border-radius:6px; padding:7px 14px; font-weight:700; font-size:12px; }}
  .pill {{ display:inline-block; border-radius:999px; padding:4px 10px; font-size:12px; font-weight:600; }}
  .swatches {{ display:grid; grid-template-columns:1fr; gap:8px; }}
  .swatch {{ display:flex; align-items:center; gap:10px; font-size:12px; }}
  .chip {{ width:32px; height:32px; border-radius:6px; border:1px solid rgba(128,128,128,.35); flex-shrink:0; }}
  .meta {{ display:flex; flex-direction:column; line-height:1.25; }}
  .meta small {{ opacity:.7; font-size:11px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Chroma Engine — 3 Ecosistemas OKLCH ({brand_esc})</h1>
    <p class="sub">Auditoría física WCAG 2.2 AAA (≥7:1) y APCA (Lc ≥75) · Dark & Light Mode completos.</p>
  </header>
  {"".join(sections)}
</div>
</body>
</html>"""


def generate_chroma_manifest(
    brand: str,
    brief_path: Optional[Path] = None,
    shards_path: Optional[Path] = None,
    selected_eco_id: Optional[str] = None,
    vertical_slug: Optional[str] = None,
) -> Dict[str, Any]:
    brand_upper = re.sub(r"[^a-zA-Z0-9_-]+", "", brand.strip()).upper() or "BRAND"
    ecosystems: List[Dict[str, Any]] = []
    source_ssot = "polar_oklch_derivation"

    if brief_path and brief_path.exists():
        txt = brief_path.read_text(encoding="utf-8", errors="replace")
        ecosystems = parse_ecosystems_from_brief(txt)
        if ecosystems:
            source_ssot = f"{brief_path.name} §3"
        else:
            m_sun = re.search(r"Longitud solar[^:\n]*:\s*([\d.]+)", txt, re.IGNORECASE)
            m_el = re.search(r"Elemento dominante[^:\n]*:\s*([A-Za-zÁÉÍÓÚáéíóú]+)", txt, re.IGNORECASE)
            m_ys = re.search(r"Yong Shen[^:\n]*:\s*([A-Za-z]+)", txt, re.IGNORECASE)
            sun_lon = float(m_sun.group(1)) if m_sun else 79.0
            el_raw = (m_el.group(1) if m_el else "Earth").lower()
            el_map = {"aire": "Air", "air": "Air", "tierra": "Earth", "earth": "Earth", "fuego": "Fire", "fire": "Fire", "agua": "Water", "water": "Water"}
            ys_raw = (m_ys.group(1) if m_ys else "Water").lower()
            ys_map = {"agua": "Water", "water": "Water", "madera": "Wood", "wood": "Wood", "fuego": "Fire", "fire": "Fire", "tierra": "Earth", "earth": "Earth", "metal": "Metal"}
            ecosystems = synthesize_polar_ecosystems(sun_lon, el_map.get(el_raw, "Earth"), ys_map.get(ys_raw, "Water"), sun_lon + 12.0)

    if not ecosystems and shards_path and shards_path.exists():
        sdata = json.loads(shards_path.read_text(encoding="utf-8"))
        s1 = sdata.get("shard_01", {}).get("data", {})
        s4 = sdata.get("shard_04", {}).get("data", {})
        sun_deg = float(s1.get("planets", {}).get("Sun", {}).get("abs_deg", 79.0))
        ven_deg = float(s1.get("planets", {}).get("Venus", {}).get("abs_deg", sun_deg))
        dom_el = s1.get("arroyo_elements", {}).get("dominant_element", "Earth")
        ys = s4.get("yong_shen", {}).get("element", "Water")
        ecosystems = synthesize_polar_ecosystems(sun_deg, dom_el, ys, ven_deg)
        source_ssot = shards_path.name

    if not ecosystems:
        # Neutral balanced derivation when invoked standalone
        ecosystems = synthesize_polar_ecosystems(210.0, "Earth", "Water", 225.0)

    selected = next((e for e in ecosystems if e["id"] == selected_eco_id), ecosystems[0])
    sel_audit = _audit_ecosystem(selected["themes"])
    sel_dark = sel_audit["dark"]

    manifest: Dict[str, Any] = {
        "$schema": "https://www.designtokens.org/tr/2025.10/color/",
        "brand": brand_upper,
        "color_space": "oklch",
        "selected_ecosystem_id": selected["id"],
        "source_ssot": source_ssot,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ecosystems": ecosystems,
        "themes": selected["themes"],
        "accessibility_audit": {
            "wcag_2_2_compliance": {
                "body_to_bg_ratio": sel_audit["wcag_aaa_ratio"],
                "headings_to_bg_ratio": sel_dark["headings_to_bg_ratio"],
                "button_to_bg_ratio": sel_dark["button_to_bg_ratio"],
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
    if vertical_slug:
        manifest["vertical_slug"] = vertical_slug
    return manifest


def run_unit_tests() -> int:
    print("Running chroma_engine unit tests...")
    sample_brief = """# Master Brief Semiótico: AURELIUS
### 3.3 Ecosistema Primario: Oceanic Cobalt (Agua / Mercurio)
Ecosistema azul profundo de alta legibilidad técnica.
#### Modo Oscuro — Oceanic Cobalt
| Rol | OKLCH | HEX | Nombre |
|---|---|---|---|
| **color-primary** | `oklch(0.72 0.16 230)` | `#38b6ff` | Cobalto Maestro |
| **color-secondary** | `oklch(0.55 0.12 245)` | `#2b74b8` | Azul Estructura |
| **color-accent** | `oklch(0.88 0.12 215)` | `#7be5ff` | Brillo Eléctrico |
| **color-background** | `oklch(0.12 0.02 250)` | `#080c14` | Fondo Nocturno |
| **color-surface** | `oklch(0.18 0.02 250)` | `#121824` | Superficie Basalto |
| **color-text-primary** | `oklch(0.97 0.01 240)` | `#f2f6fa` | Texto Alabastro |
| **color-text-muted** | `oklch(0.70 0.03 245)` | `#8e9cb0` | Texto Atenuado |

### 3.4 Ecosistema Secundario: Platinum Carbon
Contraste neutro acromático editorial.
| Rol | OKLCH | HEX | Nombre |
|---|---|---|---|
| **color-primary** | `oklch(0.92 0.01 260)` | `#e8ecf2` | Platino |
| **color-secondary** | `oklch(0.68 0.02 260)` | `#9ea6b3` | Acero |
| **color-accent** | `oklch(0.98 0.00 0)` | `#ffffff` | Especular |
| **color-background** | `oklch(0.11 0.01 260)` | `#07090d` | Carbón |
| **color-surface** | `oklch(0.17 0.01 260)` | `#14171d` | Grafito |
| **color-text-primary** | `oklch(0.96 0.01 260)` | `#f3f5f8` | Blanco Nítido |
| **color-text-muted** | `oklch(0.65 0.02 260)` | `#949ca8` | Gris Suizo |

### 3.5 Ecosistema Terciario: Sage Mineral
Verde mineral cálido orgánico.
| Rol | OKLCH | HEX | Nombre |
|---|---|---|---|
| **color-primary** | `oklch(0.76 0.09 160)` | `#52c49c` | Salvia Mineral |
| **color-secondary** | `oklch(0.58 0.07 165)` | `#428d74` | Ciprés Técnico |
| **color-accent** | `oklch(0.90 0.08 155)` | `#89f2cd` | Salvia Luminosa |
| **color-background** | `oklch(0.12 0.02 180)` | `#080e0d` | Basalto Verde |
| **color-surface** | `oklch(0.18 0.02 180)` | `#121b19` | Pizarra Musgo |
| **color-text-primary** | `oklch(0.97 0.01 160)` | `#f1f7f4` | Seda Glacial |
| **color-text-muted** | `oklch(0.68 0.03 170)` | `#8ba098` | Piedra Salvia |
"""
    with tempfile.TemporaryDirectory(prefix="chroma_test_") as tmp:
        tp = Path(tmp)
        brief_p = tp / "astrobranding_aurelius.md"
        out_d = tp / "brand_out"
        brief_p.write_text(sample_brief, encoding="utf-8")

        manifest = generate_chroma_manifest("AURELIUS", brief_path=brief_p, vertical_slug="aurelius-core")
        assert len(manifest["ecosystems"]) == 3, f"Expected 3 ecosystems, got {len(manifest['ecosystems'])}"
        for eco in manifest["ecosystems"]:
            assert "dark" in eco["themes"] and "light" in eco["themes"]
            assert eco["audit"]["wcag_aaa_ratio"] >= 7.0, f"WCAG failed for {eco['id']}: {eco['audit']}"
            assert eco["audit"]["apca_lc"] >= 75.0, f"APCA failed for {eco['id']}: {eco['audit']}"
        assert manifest["accessibility_audit"]["wcag_2_2_compliance"]["status_aaa"] is True

        out_d.mkdir(parents=True, exist_ok=True)
        (out_d / "chroma_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (out_d / "chroma_preview.html").write_text(render_chroma_preview_html(manifest), encoding="utf-8")
        assert (out_d / "chroma_manifest.json").exists()
        assert (out_d / "chroma_preview.html").exists()

    assert not Path("/mnt/localstorage/AURELIUS").exists(), "Phantom directory created during test!"
    print("✅ CHROMA ENGINE UNIT TESTS PASSED (3 ecosystems, Dark+Light, WCAG>=7:1, APCA>=75, 0 phantom dirs)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Chroma Engine — Sovereign OKLCH & WCAG AAA/APCA Synthesizer")
    parser.add_argument("--brand", default="BRAND", help="Brand identifier")
    parser.add_argument("--vertical", default=None, help="Optional vertical slug")
    parser.add_argument("--brief", type=Path, default=None, help="Path to astrobranding_<brand>.md")
    parser.add_argument("--shards", type=Path, default=None, help="Path to client_dumps_15_shards.json")
    parser.add_argument("--output-dir", type=Path, default=None, help="Explicit output directory")
    parser.add_argument("--eco", default=None, help="Selected ecosystem id")
    parser.add_argument("--no-preview", action="store_true", help="Skip HTML preview generation")
    parser.add_argument("--dry-run", action="store_true", help="Calculate without writing files")
    parser.add_argument("--test", action="store_true", help="Run deterministic offline unit tests")
    args = parser.parse_args()

    if args.test:
        return run_unit_tests()

    manifest = generate_chroma_manifest(
        brand=args.brand,
        brief_path=args.brief,
        shards_path=args.shards,
        selected_eco_id=args.eco,
        vertical_slug=args.vertical,
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
    print(f"✅ CHROMA ENGINE COMPLETED FOR: {manifest['brand']} (selected={manifest['selected_ecosystem_id']})")
    print(f"  • Ecosystems: {len(manifest['ecosystems'])} (Dark + Light)")
    print(f"  • WCAG 2.2 AAA: {audit['wcag_2_2_compliance']['body_to_bg_ratio']}:1 | APCA Lc: {audit['apca_compliance']['body_lc']}")
    print(f"  • Output: {out_dir / 'chroma_manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
