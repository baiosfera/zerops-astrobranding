#!/usr/bin/env python3
"""
kinetic_engine.py — Sovereign PB19 60fps GPU-Only Motion & Live Preview Engine (v2.1).
PB19 v2.1.0 + Oráculo-First + Astro-Web Compliant:
- Reads real semantic parts from symbol_manifest.json (#symbol-part-1..N), optional chroma_manifest.json, and optional Oráculo astrobranding_*.md (§5 cadence).
- Deliberate human-readable entrances (1150ms–1618ms) chained seamlessly into subtle continuous living loops (6.8s–8.0s infinite) that never distort or detach the mark.
- Emits 0KB-JS kinetic_motion.css + Astro View Transitions lifecycle snippet (astro:before-swap / astro:page-load).
- Strict @media (prefers-reduced-motion: reduce) degradation + W3C DTCG 2025.10 motion tokens + interactive loop toggle in kinetic_preview.html.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


BANNED_LAYOUT_PROPS = ("width:", "height:", "margin:", "margin-top:", "margin-left:", "top:", "left:", "transition: all")


def _inject_root_id(svg_text: str, root_id: str) -> str:
    def _rew(match: re.Match[str]) -> str:
        tag = re.sub(r'\s+(?:id|width|height|preserveAspectRatio)="[^"]*"', "", match.group(0), flags=re.IGNORECASE)
        return tag[:-1] + f' id="{root_id}" width="124" height="124" preserveAspectRatio="xMidYMid meet">'
    return re.sub(r"<svg\b[^>]*>", _rew, svg_text, count=1, flags=re.IGNORECASE)


def _extract_oraculo_cadence(brief_path: Optional[Path]) -> Dict[str, Any]:
    """Extracts human-readable §5 kinetic cadence from astrobranding_*.md if present."""
    cadence = {"entrance_ms": 1618, "stagger_entrance_ms": 1150, "stagger_delay_ms": 320, "ambient_ms": 1380, "loop_ms": 7200, "source": "pb19_deliberate_default"}
    if not brief_path or not brief_path.is_file():
        return cadence
    try:
        txt = brief_path.read_text(encoding="utf-8", errors="replace")
        m_hero = re.search(r"Secuencia hero completa\s*\|\s*\*\*([\d.]+)s\*\*", txt)
        if m_hero:
            ms = int(round(float(m_hero.group(1)) * 1000))
            cadence["entrance_ms"] = max(1100, min(2200, ms))
            cadence["source"] = f"oraculo:{brief_path.name}"
        m_rev = re.search(r"Reveal de sección\s*\|\s*\*\*([\d.]+)s\*\*", txt)
        if m_rev:
            ms_r = int(round(float(m_rev.group(1)) * 1000))
            cadence["stagger_entrance_ms"] = max(900, min(1600, int(round(ms_r * 1.6))))
    except Exception:
        pass
    return cadence


def generate_kinetic(
    symbol_manifest_path: Path,
    output_dir: Path,
    chroma_manifest_path: Optional[Path] = None,
    brief_path: Optional[Path] = None,
    brand: str = "BRAND",
    selected_preset: str = "staggered_precision",
) -> Dict[str, Any]:
    s_data = json.loads(symbol_manifest_path.read_text(encoding="utf-8"))
    brand_upper = (brand or s_data.get("brand") or "BRAND").upper()
    parts = s_data.get("parts") or [{"id": "symbol-mark", "index": 1}]
    part_ids = [p["id"] for p in parts]
    svg_mono = s_data.get("svg_mono") or ""
    if not svg_mono and s_data.get("assets", {}).get("symbol_mono_svg"):
        svg_mono = Path(s_data["assets"]["symbol_mono_svg"]).read_text(encoding="utf-8")

    cadence = _extract_oraculo_cadence(brief_path)
    ent_ms = cadence["entrance_ms"]
    stag_ent_ms = cadence["stagger_entrance_ms"]
    stag_step_ms = cadence["stagger_delay_ms"]
    amb_ms = cadence["ambient_ms"]
    loop_ms = cadence["loop_ms"]

    # Resolve real brand colors if chroma_manifest.json provided
    dark_bg, dark_prim, dark_ink = "#111318", "#60a5fa", "#f3f4f6"
    light_bg, light_prim, light_ink = "#f6f7f9", "#1d4ed8", "#111318"
    if chroma_manifest_path and chroma_manifest_path.is_file():
        c_data = json.loads(chroma_manifest_path.read_text(encoding="utf-8"))
        dk = c_data.get("themes", {}).get("dark", {})
        lt = c_data.get("themes", {}).get("light", {})
        dark_bg = dk.get("background", {}).get("hex", dark_bg)
        dark_prim = dk.get("primary", {}).get("hex", dark_prim)
        dark_ink = dk.get("text_primary", {}).get("hex", dark_ink)
        light_bg = lt.get("background", {}).get("hex", light_bg)
        light_prim = lt.get("primary", {}).get("hex", light_prim)
        light_ink = lt.get("text_primary", {}).get("hex", light_ink)

    # Build deliberate staggered entrance + gentle staggered living pulse per REAL SVG part
    stagger_rules = []
    for idx, pid in enumerate(part_ids):
        ent_delay = idx * stag_step_ms
        loop_delay = stag_ent_ms + (len(part_ids) - 1) * stag_step_ms + idx * 850
        stagger_rules.append(
            f".kinetic-staggered.is-playing #{pid} {{\n"
            f"  animation:\n"
            f"    kineticPartRise {stag_ent_ms}ms cubic-bezier(0.22, 1, 0.36, 1) {ent_delay}ms both,\n"
            f"    kineticPartAlive 6800ms ease-in-out {loop_delay}ms infinite;\n"
            "}\n"
            f"body.no-loop .kinetic-staggered.is-playing #{pid} {{\n"
            f"  animation: kineticPartRise {stag_ent_ms}ms cubic-bezier(0.22, 1, 0.36, 1) {ent_delay}ms both;\n"
            "}"
        )

    motion_css = f"""/* PB19 60fps GPU-Only Motion System — {brand_upper} (Deliberate Entrance + Subtle Living Loop) */
@keyframes kineticClipReveal {{
  0% {{ opacity: 0; clip-path: inset(100% 0 0 0); transform: translateY(14px); }}
  100% {{ opacity: 1; clip-path: inset(0 0 0 0); transform: translateY(0); }}
}}

@keyframes kineticLivingBreathe {{
  0%, 100% {{ opacity: 1; transform: scale(1); }}
  50% {{ opacity: 0.88; transform: scale(1.018); }}
}}

@keyframes kineticPartRise {{
  0% {{ opacity: 0; transform: translateY(14px) scale(0.95); }}
  100% {{ opacity: 1; transform: translateY(0) scale(1); }}
}}

@keyframes kineticPartAlive {{
  0%, 100% {{ opacity: 1; transform: translateY(0) scale(1); }}
  50% {{ opacity: 0.87; transform: translateY(-1.8px) scale(1.012); }}
}}

@keyframes kineticAmbientEntrance {{
  0% {{ opacity: 0; transform: scale(0.92); }}
  100% {{ opacity: 1; transform: scale(1); }}
}}

@keyframes kineticSolarFloat {{
  0%, 100% {{ opacity: 1; transform: translateY(0) scale(1); }}
  50% {{ opacity: 0.90; transform: translateY(-2.2px) scale(1.022); }}
}}

/* Preset A: Editorial Reveal + Living Breath ({ent_ms}ms entrance -> {loop_ms}ms calm breath loop) */
.kinetic-editorial #symbol-mark {{
  transform-box: fill-box;
  transform-origin: center;
}}
.kinetic-editorial.is-playing #symbol-mark {{
  animation:
    kineticClipReveal {ent_ms}ms cubic-bezier(0.22, 1, 0.36, 1) both,
    kineticLivingBreathe {loop_ms}ms ease-in-out {ent_ms + 150}ms infinite;
}}
body.no-loop .kinetic-editorial.is-playing #symbol-mark {{
  animation: kineticClipReveal {ent_ms}ms cubic-bezier(0.22, 1, 0.36, 1) both;
}}

/* Preset B: Staggered Precision + Gentle Stroke Pulse (binds to: {', '.join(part_ids)}) */
.kinetic-staggered #{', .kinetic-staggered #'.join(part_ids)} {{
  transform-box: fill-box;
  transform-origin: center;
}}
{chr(10).join(stagger_rules)}
.kinetic-staggered {{
  transition: transform 280ms cubic-bezier(0.22, 1, 0.36, 1);
}}
.kinetic-staggered:hover {{
  transform: translateY(-2px);
}}

/* Preset C: Solar Signature Entrance + Continuous Presence ({amb_ms}ms entrance -> 8000ms subtle float) */
.kinetic-ambient {{
  transition: transform 280ms cubic-bezier(0.22, 1, 0.36, 1), opacity 280ms ease;
}}
.kinetic-ambient #symbol-mark {{
  transform-box: fill-box;
  transform-origin: center;
}}
.kinetic-ambient.is-playing #symbol-mark {{
  animation:
    kineticAmbientEntrance {amb_ms}ms cubic-bezier(0.22, 1, 0.36, 1) both,
    kineticSolarFloat 8000ms ease-in-out {amb_ms + 150}ms infinite;
}}
body.no-loop .kinetic-ambient.is-playing #symbol-mark {{
  animation: kineticAmbientEntrance {amb_ms}ms cubic-bezier(0.22, 1, 0.36, 1) both;
}}
.kinetic-ambient:hover {{
  transform: scale(1.035);
}}

@media (prefers-reduced-motion: reduce) {{
  .kinetic-editorial.is-playing #symbol-mark,
  .kinetic-staggered.is-playing #symbol-mark,
  .kinetic-staggered.is-playing #{', .kinetic-staggered.is-playing #'.join(part_ids)},
  .kinetic-ambient.is-playing #symbol-mark {{
    animation: none !important;
    opacity: 1 !important;
    clip-path: none !important;
    transform: none !important;
  }}
  .kinetic-staggered,
  .kinetic-ambient {{
    transition: none !important;
  }}
}}
"""

    astro_lifecycle_ts = """// Lazy View-Transitions Lifecycle Hook for astro-web (BaseLayout.astro)
let motionObserver: IntersectionObserver | null = null;
const cleanupMotion = () => {
  motionObserver?.disconnect();
  motionObserver = null;
};
const initMotion = () => {
  cleanupMotion();
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const run = window.requestIdleCallback ?? ((cb: () => void) => setTimeout(cb, 80));
  run(() => {
    const targets = document.querySelectorAll('[data-kinetic-preset]');
    if (!targets.length) return;
    motionObserver = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          e.target.classList.add('is-playing');
          motionObserver?.unobserve(e.target);
        }
      }
    }, { threshold: 0.15 });
    targets.forEach((el) => motionObserver!.observe(el));
  });
};
document.addEventListener('astro:before-swap', cleanupMotion);
document.addEventListener('astro:page-load', initMotion);
"""

    presets = [
        {
            "id": "editorial_reveal",
            "name": "Revelado Editorial + Respiración Viva",
            "css_class": "kinetic-editorial",
            "duration_ms": ent_ms,
            "loop_duration_ms": loop_ms,
            "continuous_loop": True,
            "easing": "cubic-bezier(0.22, 1, 0.36, 1)",
            "targets": ["#symbol-mark"],
            "gpu_properties": ["opacity", "clip-path", "transform"],
            "use_case": "Entrada pausada de hero y respiración continua casi imperceptible sin romper proporciones.",
        },
        {
            "id": "staggered_precision",
            "name": "Precisión Escalonada + Pulso de Trazos",
            "css_class": "kinetic-staggered",
            "duration_ms": stag_ent_ms + max(0, len(part_ids) - 1) * stag_step_ms,
            "stagger_ms": stag_step_ms,
            "loop_duration_ms": 6800,
            "continuous_loop": True,
            "easing": "cubic-bezier(0.22, 1, 0.36, 1)",
            "targets": [f"#{pid}" for pid in part_ids],
            "gpu_properties": ["opacity", "transform"],
            "use_case": "Trazos reales entran en secuencia legible y quedan latiendo en desfase sutil sin deformarse.",
        },
        {
            "id": "ambient_signature",
            "name": "Presencia Solar Viva & Hover",
            "css_class": "kinetic-ambient",
            "duration_ms": amb_ms,
            "loop_duration_ms": 8000,
            "continuous_loop": True,
            "easing": "cubic-bezier(0.22, 1, 0.36, 1)",
            "targets": ["#symbol-mark"],
            "gpu_properties": ["opacity", "transform"],
            "use_case": "Logotipo en cabecera/footer con flotación orgánica de baja amplitud (2.2px / 1.022x).",
        },
    ]

    manifest: Dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "engine": "kinetic_engine.py v2.1",
        "brand": brand_upper,
        "cadence_source": cadence["source"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "selected_animation_id": selected_preset,
        "bound_symbol_parts": part_ids,
        "pb19_compliance": {
            "gpu_composited_only": True,
            "zero_layout_thrashing": True,
            "prefers_reduced_motion_enforced": True,
            "zero_bounce_elastic": True,
            "continuous_subtle_loop": True,
        },
        "dtcg_tokens": {
            "$schema": "https://www.designtokens.org/tr/2025.10/format/",
            "motion": {
                "duration": {
                    "part_stagger": {"$type": "duration", "$value": {"value": stag_step_ms, "unit": "ms"}},
                    "entrance": {"$type": "duration", "$value": {"value": ent_ms, "unit": "ms"}},
                    "living_loop": {"$type": "duration", "$value": {"value": loop_ms, "unit": "ms"}},
                },
                "easing": {
                    "editorial_out": {"$type": "cubicBezier", "$value": [0.22, 1, 0.36, 1]},
                },
            },
        },
        "presets": presets,
        "astro_lifecycle_ts": astro_lifecycle_ts,
        "assets": {
            "kinetic_motion_css": str(output_dir / "kinetic_motion.css"),
            "kinetic_preview_html": str(output_dir / "kinetic_preview.html"),
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "kinetic_motion.css").write_text(motion_css, encoding="utf-8")
    (output_dir / "kinetic_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    preview_html = _render_kinetic_preview_html(
        brand=brand_upper,
        svg_mono=svg_mono,
        motion_css=motion_css,
        presets=presets,
        part_ids=part_ids,
        palette={"dark_bg": dark_bg, "dark_prim": dark_prim, "dark_ink": dark_ink, "light_bg": light_bg, "light_prim": light_prim, "light_ink": light_ink},
    )
    (output_dir / "kinetic_preview.html").write_text(preview_html, encoding="utf-8")
    return manifest


def _render_kinetic_preview_html(
    brand: str,
    svg_mono: str,
    motion_css: str,
    presets: List[Dict[str, Any]],
    part_ids: List[str],
    palette: Dict[str, str],
) -> str:
    brand_esc = html_lib.escape(brand)
    cards = []
    for p in presets:
        svg_inst = _inject_root_id(svg_mono, f"svg-{p['id']}")
        targets_str = ", ".join(p["targets"])
        props_str = ", ".join(p["gpu_properties"])
        loop_lbl = f" · Loop {p['loop_duration_ms']}ms" if p.get("continuous_loop") else ""
        cards.append(
            f'<div class="card">'
            f'  <div class="card-head"><h2>{html_lib.escape(p["name"])}</h2><span class="badge">{p["duration_ms"]}ms{loop_lbl}</span></div>'
            f'  <p class="desc">{html_lib.escape(p["use_case"])}</p>'
            f'  <div class="stage" data-kinetic-box>'
            f'    <div class="mark-wrap {p["css_class"]} is-playing" data-kinetic-preset="{p["id"]}">{svg_inst}</div>'
            f'  </div>'
            f'  <div class="meta"><span>Targets: <code>{html_lib.escape(targets_str)}</code></span><span>GPU: <code>{html_lib.escape(props_str)}</code></span></div>'
            f'  <button type="button" class="btn replay-one" data-target="{p["id"]}">Repetir animación</button>'
            f'</div>'
        )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Kinetic Engine v2.1 — {brand_esc}</title>
<style>
  :root {{ --stage-bg: {palette['dark_bg']}; --stage-fg: {palette['dark_prim']}; }}
  body.light-mode {{ --stage-bg: {palette['light_bg']}; --stage-fg: {palette['light_prim']}; }}
  body {{ font-family: system-ui, -apple-system, sans-serif; background:#0f1116; color:#f1f5f9; margin:0; padding:32px 24px; }}
  .wrap {{ max-width:1200px; margin:0 auto; display:flex; flex-direction:column; gap:20px; }}
  h1 {{ margin:0 0 6px; font-size:24px; }}
  .sub {{ color:#94a3b8; font-size:14px; margin:0; }}
  .controls {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; background:#171a21; border:1px solid #262b36; padding:12px 14px; border-radius:12px; }}
  .btn {{ background:#222733; color:#e2e8f0; border:1px solid #334155; border-radius:8px; padding:8px 14px; font-size:12px; font-weight:600; cursor:pointer; }}
  .btn.active {{ background:#e2e8f0; color:#0f172a; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:18px; }}
  .card {{ background:#171a21; border:1px solid #262b36; border-radius:14px; padding:18px; display:flex; flex-direction:column; gap:12px; }}
  .card-head {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
  .card-head h2 {{ margin:0; font-size:15px; }}
  .badge {{ font-size:11px; font-family:ui-monospace, monospace; background:#1e293b; padding:3px 8px; border-radius:999px; color:#cbd5e1; white-space:nowrap; }}
  .desc {{ margin:0; font-size:13px; color:#94a3b8; line-height:1.45; }}
  .stage {{ background:var(--stage-bg); color:var(--stage-fg); border:1px solid rgba(148,163,184,0.22); border-radius:12px; min-height:180px; display:flex; align-items:center; justify-content:center; }}
  .mark-wrap svg {{ width:124px; height:124px; display:block; }}
  .meta {{ display:flex; flex-direction:column; gap:4px; font-size:12px; color:#94a3b8; }}
  body.reduced-sim .mark-wrap, body.reduced-sim .mark-wrap * {{ animation: none !important; transition: none !important; opacity: 1 !important; transform: none !important; clip-path: none !important; }}
  {motion_css}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Kinetic Engine v2.1 — {brand_esc}</h1>
    <p class="sub">3 presets 60fps GPU-only con entrada legible y loop vivo sutil continuo sobre trazos reales (<code>{html_lib.escape(', '.join(part_ids))}</code>) + degradación <code>prefers-reduced-motion</code>.</p>
  </header>
  <div class="controls">
    <button type="button" class="btn" id="replayAllBtn">Repetir los 3 presets</button>
    <button type="button" class="btn active" id="loopToggleBtn">Loop continuo: ON</button>
    <button type="button" class="btn" id="themeBtn">Alternar Light / Dark</button>
    <button type="button" class="btn" id="reduceBtn">Simular prefers-reduced-motion</button>
  </div>
  <div class="grid">{"".join(cards)}</div>
</div>
<script>
document.addEventListener('DOMContentLoaded', () => {{
  const replay = (el) => {{
    el.classList.remove('is-playing');
    void el.offsetWidth;
    el.classList.add('is-playing');
  }};
  const allBtn = document.getElementById('replayAllBtn');
  if (allBtn) {{
    allBtn.addEventListener('click', () => {{
      document.querySelectorAll('[data-kinetic-preset]').forEach(replay);
    }});
  }}
  const loopBtn = document.getElementById('loopToggleBtn');
  if (loopBtn) {{
    loopBtn.addEventListener('click', () => {{
      const noLoop = document.body.classList.toggle('no-loop');
      loopBtn.classList.toggle('active', !noLoop);
      loopBtn.textContent = noLoop ? 'Loop continuo: OFF' : 'Loop continuo: ON';
    }});
  }}
  document.querySelectorAll('.replay-one').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const pid = btn.getAttribute('data-target');
      const target = document.querySelector('[data-kinetic-preset="' + pid + '"]');
      if (target) replay(target);
    }});
  }});
  const themeBtn = document.getElementById('themeBtn');
  if (themeBtn) {{
    themeBtn.addEventListener('click', () => {{
      document.body.classList.toggle('light-mode');
      themeBtn.classList.toggle('active', document.body.classList.contains('light-mode'));
    }});
  }}
  const reduceBtn = document.getElementById('reduceBtn');
  if (reduceBtn) {{
    reduceBtn.addEventListener('click', () => {{
      document.body.classList.toggle('reduced-sim');
      reduceBtn.classList.toggle('active', document.body.classList.contains('reduced-sim'));
    }});
  }}
}});
</script>
</body>
</html>"""


def run_unit_tests() -> int:
    print("Running kinetic_engine v2.1 unit tests...")
    with tempfile.TemporaryDirectory(prefix="kinetic_v2_test_") as tmp:
        tp = Path(tmp)
        sym_p = tp / "symbol_manifest.json"
        sym_p.write_text(json.dumps({
            "brand": "TEST",
            "parts": [{"id": "symbol-part-1", "index": 1}, {"id": "symbol-part-2", "index": 2}],
            "svg_mono": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" fill="currentColor"><g id="symbol-mark"><path id="symbol-part-1" d="M10 10 L40 90 Z"/><path id="symbol-part-2" d="M60 10 L90 90 Z"/></g></svg>',
        }), encoding="utf-8")
        out_dir = tp / "kinetic_out"
        man = generate_kinetic(sym_p, out_dir, brand="TEST")
        assert len(man["presets"]) == 3
        assert man["bound_symbol_parts"] == ["symbol-part-1", "symbol-part-2"]
        assert all(p["duration_ms"] >= 1100 and p["continuous_loop"] is True for p in man["presets"])
        css_txt = (out_dir / "kinetic_motion.css").read_text(encoding="utf-8")
        assert "#symbol-part-1" in css_txt and "#symbol-part-2" in css_txt
        assert "infinite" in css_txt and "prefers-reduced-motion: reduce" in css_txt
        for bad in BANNED_LAYOUT_PROPS:
            assert bad not in css_txt.lower(), f"Layout-thrashing CSS found: {bad}"
        html_txt = (out_dir / "kinetic_preview.html").read_text(encoding="utf-8")
        assert "loopToggleBtn" in html_txt
        if shutil.which("node"):
            for i, sb in enumerate(re.findall(r"<script[^>]*>(.*?)</script>", html_txt, re.S)):
                js_f = tp / f"kin_{i}.js"
                js_f.write_text(sb, encoding="utf-8")
                res = subprocess.run(["node", "--check", str(js_f)], capture_output=True, text=True)
                assert res.returncode == 0, res.stderr
    print("✅ KINETIC ENGINE v2.1 UNIT TESTS PASSED (Deliberate entrance + subtle continuous living loop, real part binding, GPU-only 60fps)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Kinetic Engine v2.1 — PB19 60fps GPU-Only Motion System")
    parser.add_argument("--symbol", type=Path, default=None, help="Path to symbol_manifest.json")
    parser.add_argument("--chroma", type=Path, default=None, help="Optional chroma_manifest.json")
    parser.add_argument("--brief", type=Path, default=None, help="Optional astrobranding_*.md for Oráculo kinetic cadence")
    parser.add_argument("--brand", default="BRAND")
    parser.add_argument("--preset", default="staggered_precision", choices=["editorial_reveal", "staggered_precision", "ambient_signature"])
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        return run_unit_tests()
    if not args.symbol or not args.symbol.is_file():
        print("Error: --symbol symbol_manifest.json is required", file=sys.stderr)
        return 1
    out_dir = (args.output_dir or args.symbol.parent.parent / "kinetic").resolve()
    man = generate_kinetic(args.symbol, out_dir, chroma_manifest_path=args.chroma, brief_path=args.brief, brand=args.brand, selected_preset=args.preset)
    print(f"✅ KINETIC ENGINE v2.1 COMPLETED FOR: {man['brand']} (3 presets, parts={man['bound_symbol_parts']}, cadence={man['cadence_source']} -> {out_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
