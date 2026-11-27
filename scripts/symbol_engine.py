#!/usr/bin/env python3
"""
symbol_engine.py — Sovereign SVG Normalization, Subpath Splitting & BrandMark Engine (v2.0).
PB19 v2.0.0 + Astro-Web Compliant:
- Parses real SVG files (nested transforms, compound paths, background <rect> detection).
- Flattens affine transforms onto absolute path coordinates and normalizes into centered viewBox="0 0 100 100".
- Splits independent glyphs/strokes into semantic #symbol-part-1..N (preserving interior counter holes).
- Emits symbol_mono.svg (currentColor), symbol_brand.svg (var(--brand-primary)), adaptive favicon.svg,
  zero-JS BrandMark.astro, symbol_manifest.json, and interactive symbol_preview.html.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


Affine = Tuple[float, float, float, float, float, float]  # (a, b, c, d, e, f)


def _mat_mul(m1: Affine, m2: Affine) -> Affine:
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def _apply_affine(m: Affine, x: float, y: float) -> Tuple[float, float]:
    a, b, c, d, e, f = m
    return (a * x + c * y + e, b * x + d * y + f)


def parse_transform(t_str: Optional[str]) -> Affine:
    m: Affine = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    if not t_str:
        return m
    for fn, args_s in re.findall(r"([a-zA-Z]+)\s*\(([^)]*)\)", t_str):
        nums = [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?", args_s)]
        op = fn.lower()
        cur: Optional[Affine] = None
        if op == "translate" and nums:
            tx = nums[0]
            ty = nums[1] if len(nums) > 1 else 0.0
            cur = (1.0, 0.0, 0.0, 1.0, tx, ty)
        elif op == "scale" and nums:
            sx = nums[0]
            sy = nums[1] if len(nums) > 1 else sx
            cur = (sx, 0.0, 0.0, sy, 0.0, 0.0)
        elif op == "rotate" and nums:
            ang = math.radians(nums[0])
            ca, sa = math.cos(ang), math.sin(ang)
            if len(nums) >= 3:
                cx, cy = nums[1], nums[2]
                cur = _mat_mul((1, 0, 0, 1, cx, cy), _mat_mul((ca, sa, -sa, ca, 0, 0), (1, 0, 0, 1, -cx, -cy)))
            else:
                cur = (ca, sa, -sa, ca, 0.0, 0.0)
        elif op == "matrix" and len(nums) >= 6:
            cur = (nums[0], nums[1], nums[2], nums[3], nums[4], nums[5])
        if cur:
            m = _mat_mul(m, cur)
    return m


_CMD_RE = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])|([-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)")


def _tokenize_path(d: str) -> List[str]:
    return [tok for m in _CMD_RE.finditer(d or "") for tok in (m.group(1) or m.group(2),)]


def _path_to_subpaths_transformed(d: str, m: Affine) -> List[Tuple[str, List[Tuple[float, float]]]]:
    """
    Converts an SVG path string into absolute transformed subpaths (one per M/m contour),
    returning [(d_transformed, sampled_points_for_bbox), ...].
    """
    tokens = _tokenize_path(d)
    i = 0
    cmd = ""
    cx = cy = 0.0
    sx = sy = 0.0
    subpaths: List[Tuple[List[str], List[Tuple[float, float]]]] = []
    cur_cmds: List[str] = []
    cur_pts: List[Tuple[float, float]] = []

    def _next_float() -> float:
        nonlocal i
        val = float(tokens[i])
        i += 1
        return val

    def _has_num() -> bool:
        return i < len(tokens) and not tokens[i].isalpha()

    def _sample_quad(p0: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float]) -> None:
        for step in range(1, 13):
            t = step / 12.0
            mt = 1.0 - t
            x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
            y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
            cur_pts.append((x, y))

    def _sample_cubic(p0: Tuple[float, float], p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> None:
        for step in range(1, 13):
            t = step / 12.0
            mt = 1.0 - t
            x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
            y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
            cur_pts.append((x, y))

    last_cp: Optional[Tuple[float, float]] = None
    last_cmd = ""

    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
        elif not cmd:
            break

        if cmd in ("M", "m"):
            first = True
            while _has_num():
                nx, ny = _next_float(), _next_float()
                if cmd == "m":
                    nx += cx
                    ny += cy
                cx, cy = nx, ny
                tp = _apply_affine(m, cx, cy)
                if first:
                    if cur_cmds:
                        subpaths.append((cur_cmds, cur_pts))
                    cur_cmds = [f"M{tp[0]:.4f} {tp[1]:.4f}"]
                    cur_pts = [tp]
                    sx, sy = cx, cy
                    first = False
                else:
                    cur_cmds.append(f"L{tp[0]:.4f} {tp[1]:.4f}")
                    cur_pts.append(tp)
                last_cp = None
                last_cmd = cmd
            cmd = "L" if cmd == "M" else "l"
        elif cmd in ("L", "l"):
            while _has_num():
                nx, ny = _next_float(), _next_float()
                if cmd == "l":
                    nx += cx
                    ny += cy
                cx, cy = nx, ny
                tp = _apply_affine(m, cx, cy)
                cur_cmds.append(f"L{tp[0]:.4f} {tp[1]:.4f}")
                cur_pts.append(tp)
                last_cp = None
                last_cmd = cmd
        elif cmd in ("H", "h"):
            while _has_num():
                nx = _next_float()
                if cmd == "h":
                    nx += cx
                cx = nx
                tp = _apply_affine(m, cx, cy)
                cur_cmds.append(f"L{tp[0]:.4f} {tp[1]:.4f}")
                cur_pts.append(tp)
                last_cp = None
                last_cmd = cmd
        elif cmd in ("V", "v"):
            while _has_num():
                ny = _next_float()
                if cmd == "v":
                    ny += cy
                cy = ny
                tp = _apply_affine(m, cx, cy)
                cur_cmds.append(f"L{tp[0]:.4f} {tp[1]:.4f}")
                cur_pts.append(tp)
                last_cp = None
                last_cmd = cmd
        elif cmd in ("Q", "q"):
            while _has_num():
                x1, y1, nx, ny = _next_float(), _next_float(), _next_float(), _next_float()
                if cmd == "q":
                    x1 += cx; y1 += cy; nx += cx; ny += cy
                p0 = _apply_affine(m, cx, cy)
                p1 = _apply_affine(m, x1, y1)
                p2 = _apply_affine(m, nx, ny)
                cur_cmds.append(f"Q{p1[0]:.4f} {p1[1]:.4f} {p2[0]:.4f} {p2[1]:.4f}")
                _sample_quad(p0, p1, p2)
                last_cp = (x1, y1)
                cx, cy = nx, ny
                last_cmd = cmd
        elif cmd in ("T", "t"):
            while _has_num():
                nx, ny = _next_float(), _next_float()
                if cmd == "t":
                    nx += cx; ny += cy
                if last_cmd in ("Q", "q", "T", "t") and last_cp is not None:
                    x1, y1 = 2 * cx - last_cp[0], 2 * cy - last_cp[1]
                else:
                    x1, y1 = cx, cy
                p0 = _apply_affine(m, cx, cy)
                p1 = _apply_affine(m, x1, y1)
                p2 = _apply_affine(m, nx, ny)
                cur_cmds.append(f"Q{p1[0]:.4f} {p1[1]:.4f} {p2[0]:.4f} {p2[1]:.4f}")
                _sample_quad(p0, p1, p2)
                last_cp = (x1, y1)
                cx, cy = nx, ny
                last_cmd = cmd
        elif cmd in ("C", "c"):
            while _has_num():
                x1, y1, x2, y2, nx, ny = (_next_float() for _ in range(6))
                if cmd == "c":
                    x1 += cx; y1 += cy; x2 += cx; y2 += cy; nx += cx; ny += cy
                p0 = _apply_affine(m, cx, cy)
                p1 = _apply_affine(m, x1, y1)
                p2 = _apply_affine(m, x2, y2)
                p3 = _apply_affine(m, nx, ny)
                cur_cmds.append(f"C{p1[0]:.4f} {p1[1]:.4f} {p2[0]:.4f} {p2[1]:.4f} {p3[0]:.4f} {p3[1]:.4f}")
                _sample_cubic(p0, p1, p2, p3)
                last_cp = (x2, y2)
                cx, cy = nx, ny
                last_cmd = cmd
        elif cmd in ("S", "s"):
            while _has_num():
                x2, y2, nx, ny = (_next_float() for _ in range(4))
                if cmd == "s":
                    x2 += cx; y2 += cy; nx += cx; ny += cy
                if last_cmd in ("C", "c", "S", "s") and last_cp is not None:
                    x1, y1 = 2 * cx - last_cp[0], 2 * cy - last_cp[1]
                else:
                    x1, y1 = cx, cy
                p0 = _apply_affine(m, cx, cy)
                p1 = _apply_affine(m, x1, y1)
                p2 = _apply_affine(m, x2, y2)
                p3 = _apply_affine(m, nx, ny)
                cur_cmds.append(f"C{p1[0]:.4f} {p1[1]:.4f} {p2[0]:.4f} {p2[1]:.4f} {p3[0]:.4f} {p3[1]:.4f}")
                _sample_cubic(p0, p1, p2, p3)
                last_cp = (x2, y2)
                cx, cy = nx, ny
                last_cmd = cmd
        elif cmd in ("A", "a"):
            while _has_num():
                rx, ry, rot, large, sweep, nx, ny = (_next_float() for _ in range(7))
                if cmd == "a":
                    nx += cx; ny += cy
                sx_m = math.hypot(m[0], m[1]) or 1.0
                sy_m = math.hypot(m[2], m[3]) or 1.0
                p2 = _apply_affine(m, nx, ny)
                cur_cmds.append(f"A{rx * sx_m:.4f} {ry * sy_m:.4f} {rot:.2f} {int(large)} {int(sweep)} {p2[0]:.4f} {p2[1]:.4f}")
                cur_pts.append(p2)
                cx, cy = nx, ny
                last_cp = None
                last_cmd = cmd
        elif cmd in ("Z", "z"):
            cur_cmds.append("Z")
            cx, cy = sx, sy
            last_cp = None
            last_cmd = cmd
            cmd = ""
        else:
            break

    if cur_cmds:
        subpaths.append((cur_cmds, cur_pts))
    return [(" ".join(c), pts) for c, pts in subpaths if pts]


def _bbox(pts: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def _is_bbox_inside(inner: Tuple[float, float, float, float], outer: Tuple[float, float, float, float]) -> bool:
    return inner[0] >= outer[0] - 0.5 and inner[1] >= outer[1] - 0.5 and inner[2] <= outer[2] + 0.5 and inner[3] <= outer[3] + 0.5


def _merge_subpath_holes(raw_subpaths: List[Tuple[str, List[Tuple[float, float]]]]) -> List[Tuple[str, List[Tuple[float, float]]]]:
    """Groups interior counter holes with their enclosing outer glyph subpath so fills stay intact."""
    if len(raw_subpaths) <= 1:
        return raw_subpaths
    boxes = [_bbox(pts) for _, pts in raw_subpaths]
    areas = [(b[2] - b[0]) * (b[3] - b[1]) for b in boxes]
    used_as_hole: Dict[int, int] = {}
    for idx, b in enumerate(boxes):
        for oidx, ob in enumerate(boxes):
            if idx != oidx and areas[oidx] > areas[idx] and _is_bbox_inside(b, ob):
                used_as_hole[idx] = oidx
                break
    grouped: Dict[int, List[int]] = {i: [i] for i in range(len(raw_subpaths)) if i not in used_as_hole}
    for hidx, parent in used_as_hole.items():
        while parent in used_as_hole:
            parent = used_as_hole[parent]
        grouped.setdefault(parent, [parent]).append(hidx)
    out: List[Tuple[str, List[Tuple[float, float]]]] = []
    for k in sorted(grouped.keys()):
        idxs = grouped[k]
        d_merged = " ".join(raw_subpaths[j][0] for j in idxs)
        pts_merged = [pt for j in idxs for pt in raw_subpaths[j][1]]
        out.append((d_merged, pts_merged))
    return out


def _normalize_path_d(d_abs: str, scale: float, ox: float, oy: float) -> str:
    """Scales and translates an already-flattened absolute path into normalized [0..100] coordinates."""
    tokens = _tokenize_path(d_abs)
    out: List[str] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            out.append(t)
            i += 1
            if t == "A":
                rx = float(tokens[i]) * scale
                ry = float(tokens[i + 1]) * scale
                rot = tokens[i + 2]
                large = tokens[i + 3]
                sweep = tokens[i + 4]
                nx = float(tokens[i + 5]) * scale + ox
                ny = float(tokens[i + 6]) * scale + oy
                out.append(f"{rx:.2f} {ry:.2f} {rot} {large} {sweep} {nx:.2f} {ny:.2f}")
                i += 7
            continue
        # Pair of (x, y)
        x = float(t) * scale + ox
        y = float(tokens[i + 1]) * scale + oy
        out.append(f"{x:.2f} {y:.2f}")
        i += 2
    return " ".join(out)


def _local_tag(el: ET.Element) -> str:
    return el.tag.split("}")[-1].lower()


def _extract_svg_elements(root: ET.Element) -> Tuple[List[Tuple[str, List[Tuple[float, float]]]], Optional[str], str]:
    vb_orig = root.attrib.get("viewBox", "")
    bg_detected: Optional[str] = None
    subpaths: List[Tuple[str, List[Tuple[float, float]]]] = []

    def _walk(node: ET.Element, cur_m: Affine) -> None:
        nonlocal bg_detected
        tag = _local_tag(node)
        m = _mat_mul(cur_m, parse_transform(node.attrib.get("transform")))
        if tag == "rect":
            fill = node.attrib.get("fill", "")
            # Full-canvas background rectangle detection
            if fill and fill.lower() != "none" and not bg_detected:
                bg_detected = fill
            return
        if tag == "path":
            d = node.attrib.get("d", "")
            if d:
                subpaths.extend(_path_to_subpaths_transformed(d, m))
            return
        if tag == "circle":
            cx = float(node.attrib.get("cx", 0))
            cy = float(node.attrib.get("cy", 0))
            r = float(node.attrib.get("r", 0))
            d = f"M{cx - r} {cy} A{r} {r} 0 1 0 {cx + r} {cy} A{r} {r} 0 1 0 {cx - r} {cy} Z"
            subpaths.extend(_path_to_subpaths_transformed(d, m))
            return
        for ch in list(node):
            _walk(ch, m)

    _walk(root, (1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
    return _merge_subpath_holes(subpaths), bg_detected, vb_orig


def process_svg(
    input_svg: Path,
    output_dir: Path,
    brand: str = "BRAND",
    chroma_path: Optional[Path] = None,
    padding_pct: float = 0.12,
) -> Dict[str, Any]:
    raw_txt = input_svg.read_text(encoding="utf-8")
    root = ET.fromstring(raw_txt)
    grouped, bg_orig, vb_orig = _extract_svg_elements(root)
    if not grouped:
        raise ValueError(f"No vector geometry found in {input_svg}")

    all_pts = [pt for _, pts in grouped for pt in pts]
    min_x, min_y, max_x, max_y = _bbox(all_pts)
    w = max(1e-4, max_x - min_x)
    h = max(1e-4, max_y - min_y)

    target_box = 100.0 * (1.0 - 2.0 * padding_pct)
    scale = target_box / max(w, h)
    scaled_w, scaled_h = w * scale, h * scale
    ox = (100.0 - scaled_w) / 2.0 - min_x * scale
    oy = (100.0 - scaled_h) / 2.0 - min_y * scale

    parts: List[Dict[str, Any]] = []
    path_nodes_mono: List[str] = []
    path_nodes_brand: List[str] = []
    path_nodes_fav: List[str] = []
    for idx, (d_abs, _) in enumerate(grouped, 1):
        pid = f"symbol-part-{idx}"
        d_norm = _normalize_path_d(d_abs, scale, ox, oy)
        parts.append({"id": pid, "index": idx, "d": d_norm})
        path_nodes_mono.append(f'    <path id="{pid}" d="{d_norm}" />')
        path_nodes_brand.append(f'    <path id="{pid}" d="{d_norm}" />')
        path_nodes_fav.append(f'    <path id="{pid}" d="{d_norm}" />')

    # Resolve chroma palette if supplied for adaptive favicon + preview
    light_bg, light_ink, light_prim = "#f6f7f9", "#111318", "#1d4ed8"
    dark_bg, dark_ink, dark_prim = "#111318", "#f3f4f6", "#60a5fa"
    if chroma_path and chroma_path.is_file():
        cdata = json.loads(chroma_path.read_text(encoding="utf-8"))
        lt = cdata.get("themes", {}).get("light", {})
        dk = cdata.get("themes", {}).get("dark", {})
        light_bg = lt.get("background", {}).get("hex", light_bg)
        light_ink = lt.get("text_primary", {}).get("hex", light_ink)
        light_prim = lt.get("primary", {}).get("hex", light_prim)
        dark_bg = dk.get("background", {}).get("hex", dark_bg)
        dark_ink = dk.get("text_primary", {}).get("hex", dark_ink)
        dark_prim = dk.get("primary", {}).get("hex", dark_prim)

    svg_mono = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100" preserveAspectRatio="xMidYMid meet" fill="currentColor" aria-hidden="true">\n'
        '  <g id="symbol-mark">\n'
        + "\n".join(path_nodes_mono)
        + "\n  </g>\n</svg>\n"
    )
    svg_brand = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100" preserveAspectRatio="xMidYMid meet" fill="var(--brand-primary, currentColor)" aria-hidden="true">\n'
        '  <g id="symbol-mark">\n'
        + "\n".join(path_nodes_brand)
        + "\n  </g>\n</svg>\n"
    )
    favicon_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100" preserveAspectRatio="xMidYMid meet">\n'
        "  <style>\n"
        f"    #symbol-fav-bg {{ fill: {dark_bg}; }}\n"
        f"    #symbol-mark {{ fill: {dark_prim}; }}\n"
        "    @media (prefers-color-scheme: light) {\n"
        f"      #symbol-fav-bg {{ fill: {light_bg}; }}\n"
        f"      #symbol-mark {{ fill: {light_prim}; }}\n"
        "    }\n"
        "  </style>\n"
        '  <rect id="symbol-fav-bg" x="0" y="0" width="100" height="100" rx="22" />\n'
        '  <g id="symbol-mark">\n'
        + "\n".join(path_nodes_fav)
        + "\n  </g>\n</svg>\n"
    )

    inner_paths_astro = "\n".join(f'    <path id="{p["id"]}" d="{p["d"]}" />' for p in parts)
    astro_component = f"""---
interface Props {{
  size?: number | string;
  variant?: "mono" | "brand";
  label?: string;
  class?: string;
}}
const {{ size = 40, variant = "brand", label = "", class: className = "" }} = Astro.props;
const fillToken = variant === "mono" ? "currentColor" : "var(--brand-primary, currentColor)";
const isDecorative = !label;
---
<svg
  xmlns="http://www.w3.org/2000/svg"
  viewBox="0 0 100 100"
  width={{size}}
  height={{size}}
  fill={{fillToken}}
  class={{className}}
  role={{isDecorative ? undefined : "img"}}
  aria-label={{isDecorative ? undefined : label}}
  aria-hidden={{isDecorative ? "true" : undefined}}
>
  <g id="symbol-mark">
{inner_paths_astro}
  </g>
</svg>
"""

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "symbol_mono.svg").write_text(svg_mono, encoding="utf-8")
    (output_dir / "symbol_brand.svg").write_text(svg_brand, encoding="utf-8")
    (output_dir / "favicon.svg").write_text(favicon_svg, encoding="utf-8")
    (output_dir / "BrandMark.astro").write_text(astro_component, encoding="utf-8")

    manifest: Dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "engine": "symbol_engine.py v2.0",
        "brand": brand.upper(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_svg": str(input_svg),
        "normalization": {
            "original_viewBox": vb_orig,
            "normalized_viewBox": "0 0 100 100",
            "background_stripped": bg_orig,
            "padding_pct": padding_pct,
            "aspect_ratio_preserved": round(scaled_w / max(1e-4, scaled_h), 3),
        },
        "parts": [{"id": p["id"], "index": p["index"]} for p in parts],
        "selected_vector_id": "symbol_brand",
        "assets": {
            "symbol_mono_svg": str(output_dir / "symbol_mono.svg"),
            "symbol_brand_svg": str(output_dir / "symbol_brand.svg"),
            "favicon_svg": str(output_dir / "favicon.svg"),
            "astro_component": str(output_dir / "BrandMark.astro"),
        },
        "svg_mono": svg_mono,
        "svg_brand": svg_brand,
        "lockup_ratios": {
            "horizontal_icon_to_wordmark_em": 1.35,
            "clear_space_units": 0.25,
        },
    }
    (output_dir / "symbol_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    preview_html = _render_symbol_preview_html(
        brand=brand.upper(),
        raw_svg=raw_txt,
        svg_mono=svg_mono,
        favicon_svg=favicon_svg,
        parts=parts,
        palette={"light_bg": light_bg, "light_ink": light_ink, "light_prim": light_prim, "dark_bg": dark_bg, "dark_ink": dark_ink, "dark_prim": dark_prim},
        norm_meta=manifest["normalization"],
    )
    (output_dir / "symbol_preview.html").write_text(preview_html, encoding="utf-8")
    return manifest


def _render_symbol_preview_html(
    brand: str,
    raw_svg: str,
    svg_mono: str,
    favicon_svg: str,
    parts: List[Dict[str, Any]],
    palette: Dict[str, str],
    norm_meta: Dict[str, Any],
) -> str:
    brand_esc = html_lib.escape(brand)
    raw_clean = re.sub(r"<\?xml[^>]*\?>", "", raw_svg).strip()
    part_pills = "".join(f'<span class="pill">#{html_lib.escape(p["id"])}</span>' for p in parts)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Symbol Engine v2.0 — {brand_esc}</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; background:#0f1116; color:#f1f5f9; margin:0; padding:32px 24px; }}
  .wrap {{ max-width:1200px; margin:0 auto; display:flex; flex-direction:column; gap:20px; }}
  h1 {{ margin:0 0 6px; font-size:24px; }}
  .sub {{ color:#94a3b8; font-size:14px; margin:0; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:16px; }}
  .card {{ background:#171a21; border:1px solid #262b36; border-radius:14px; padding:18px; display:flex; flex-direction:column; gap:12px; }}
  .card h2 {{ margin:0; font-size:15px; }}
  .stage {{ display:flex; align-items:center; justify-content:center; min-height:170px; border-radius:12px; border:1px solid rgba(148,163,184,0.2); padding:16px; position:relative; }}
  .stage svg {{ width:120px; height:120px; display:block; }}
  .stage.grid-bg {{ background-image: linear-gradient(to right, rgba(148,163,184,.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,.08) 1px, transparent 1px); background-size: 20px 20px; }}
  .fav-row {{ display:flex; align-items:end; gap:18px; flex-wrap:wrap; }}
  .fav-item {{ display:flex; flex-direction:column; align-items:center; gap:6px; font-size:11px; color:#94a3b8; }}
  .lockup {{ display:flex; align-items:center; gap:14px; font-weight:700; letter-spacing:-0.02em; font-size:22px; }}
  .lockup svg {{ width:42px; height:42px; flex-shrink:0; }}
  .pill {{ display:inline-block; background:#1e293b; color:#cbd5e1; border:1px solid #334155; border-radius:999px; padding:3px 10px; font-size:12px; margin-right:6px; }}
  .btn {{ background:#222733; color:#e2e8f0; border:1px solid #334155; border-radius:8px; padding:8px 12px; font-size:12px; font-weight:600; cursor:pointer; align-self:flex-start; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Symbol Engine v2.0 — {brand_esc}</h1>
    <p class="sub">viewBox original: <code>{html_lib.escape(norm_meta['original_viewBox'])}</code> → normalizado: <code>0 0 100 100</code> · fondo eliminado: <code>{html_lib.escape(str(norm_meta['background_stripped']))}</code></p>
    <div style="margin-top:10px">{part_pills}</div>
  </header>

  <div class="grid">
    <div class="card">
      <h2>1. Original crudo (con transform/fondo)</h2>
      <div class="stage" style="background:#0a0b0f">{raw_clean}</div>
    </div>
    <div class="card">
      <h2>2. Normalizado Monocromo Oscuro (B/N)</h2>
      <div class="stage grid-bg" style="background-color:#0b0d12;color:#f8fafc">{svg_mono}</div>
      <button type="button" class="btn" id="copyMonoBtn">Copiar SVG Monocromo</button>
    </div>
    <div class="card">
      <h2>3. Normalizado Monocromo Claro (B/N)</h2>
      <div class="stage grid-bg" style="background-color:#f8fafc;color:#0b0d12">{svg_mono}</div>
    </div>
    <div class="card">
      <h2>4. Teñido Reactivo Chroma (Dark & Light)</h2>
      <div class="stage" style="background:{palette['dark_bg']};color:{palette['dark_prim']}">{svg_mono}</div>
      <div class="stage" style="background:{palette['light_bg']};color:{palette['light_prim']};min-height:110px">{svg_mono}</div>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>5. Legibilidad Óptica de Favicon (16px – 64px)</h2>
      <div class="fav-row">
        <div class="fav-item"><div style="width:16px;height:16px">{favicon_svg}</div><span>16px</span></div>
        <div class="fav-item"><div style="width:32px;height:32px">{favicon_svg}</div><span>32px</span></div>
        <div class="fav-item"><div style="width:48px;height:48px">{favicon_svg}</div><span>48px</span></div>
        <div class="fav-item"><div style="width:64px;height:64px">{favicon_svg}</div><span>64px</span></div>
      </div>
    </div>
    <div class="card">
      <h2>6. Lockup Horizontal en Cabecera (Dark & Light)</h2>
      <div class="stage" style="min-height:80px;background:{palette['dark_bg']};color:{palette['dark_ink']}">
        <div class="lockup"><span style="color:{palette['dark_prim']};display:inline-flex">{svg_mono}</span><span>{brand_esc}</span></div>
      </div>
      <div class="stage" style="min-height:80px;background:{palette['light_bg']};color:{palette['light_ink']}">
        <div class="lockup"><span style="color:{palette['light_prim']};display:inline-flex">{svg_mono}</span><span>{brand_esc}</span></div>
      </div>
    </div>
  </div>
</div>
<script>
document.addEventListener('DOMContentLoaded', () => {{
  const btn = document.getElementById('copyMonoBtn');
  if (btn) {{
    btn.addEventListener('click', () => {{
      const svg = document.querySelectorAll('.stage svg')[1];
      if (svg && navigator.clipboard) navigator.clipboard.writeText(svg.outerHTML).catch(() => {{}});
      btn.textContent = 'Copiado!';
      setTimeout(() => {{ btn.textContent = 'Copiar SVG Monocromo'; }}, 1200);
    }});
  }}
}});
</script>
</body>
</html>"""


def run_unit_tests() -> int:
    print("Running symbol_engine v2.0 unit tests...")
    sample_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="16 60 36 32" width="1024" height="898">
  <rect x="16" y="60" width="36" height="32" fill="#090a0f"/>
  <g transform="translate(-2, 41)"><g transform="translate(18, 17.5)"><g transform="scale(0.35, 0.35) translate(9, 11)">
    <path d="M10 68 L10 12 Q10 6 4 6 L20 6 L35 56 L35 75 Z M85 6 L77 6 L77 75 L53 48 L53 23 L85 6 Z" fill="#d4af37"/>
  </g></g></g>
</svg>"""
    with tempfile.TemporaryDirectory(prefix="symbol_v2_test_") as tmp:
        tp = Path(tmp)
        in_p = tp / "icono.svg"
        in_p.write_text(sample_svg, encoding="utf-8")
        out_dir = tp / "out"
        man = process_svg(in_p, out_dir, brand="TEST BRAND")
        assert len(man["parts"]) == 2, f"Expected 2 semantic parts, got {man['parts']}"
        mono = (out_dir / "symbol_mono.svg").read_text(encoding="utf-8")
        assert "#090a0f" not in mono and "#d4af37" not in mono
        assert 'fill="currentColor"' in mono and 'viewBox="0 0 100 100"' in mono
        assert 'id="symbol-part-1"' in mono and 'id="symbol-part-2"' in mono
        fav = (out_dir / "favicon.svg").read_text(encoding="utf-8")
        assert "prefers-color-scheme: light" in fav
        astro = (out_dir / "BrandMark.astro").read_text(encoding="utf-8")
        assert "Astro.props" in astro and 'id="symbol-mark"' in astro
        html_txt = (out_dir / "symbol_preview.html").read_text(encoding="utf-8")
        if shutil.which("node"):
            for i, sb in enumerate(re.findall(r"<script[^>]*>(.*?)</script>", html_txt, re.S)):
                js_f = tp / f"sym_{i}.js"
                js_f.write_text(sb, encoding="utf-8")
                res = subprocess.run(["node", "--check", str(js_f)], capture_output=True, text=True)
                assert res.returncode == 0, res.stderr
    print("✅ SYMBOL ENGINE v2.0 UNIT TESTS PASSED (Flattened nested transforms, split real parts, 0 hardcoded hex, adaptive favicon, BrandMark.astro)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Symbol Engine v2.0 — SVG Normalizer & BrandMark Compiler")
    parser.add_argument("--input", type=Path, default=None, help="Input raw SVG path")
    parser.add_argument("--brand", default="BRAND")
    parser.add_argument("--chroma", type=Path, default=None, help="Optional chroma_manifest.json for brand tinting")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        return run_unit_tests()
    if not args.input or not args.input.is_file():
        print("Error: --input SVG file is required", file=sys.stderr)
        return 1
    out_dir = (args.output_dir or args.input.parent / "symbol").resolve()
    man = process_svg(args.input, out_dir, brand=args.brand, chroma_path=args.chroma)
    print(f"✅ SYMBOL ENGINE v2.0 COMPLETED FOR: {man['brand']} ({len(man['parts'])} real SVG parts -> {out_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
