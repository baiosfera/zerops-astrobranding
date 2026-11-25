#!/usr/bin/env python3
"""
Envato Elements Font Previewer & SVG Vector Extractor (v3.0)
Supports app.envato.com/fonts/{uuid}, bare UUIDs, elements.envato.com URLs,
and --from-manifest font_manifest.json + --chroma chroma_manifest.json.
Generates standalone SVG vector files and interactive Dark/Light HTML comparison galleries
with live text tester (parity with baiosfera/brandfont).
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
UUID_RE = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", re.IGNORECASE)


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name).strip("_") or "font"


def fetch_page_data(url_or_uuid: str, title_hint: str = "") -> Dict[str, Any]:
    raw = url_or_uuid.strip()
    uuid_m = UUID_RE.search(raw)

    if uuid_m and not raw.startswith("http"):
        raw = f"https://app.envato.com/fonts/{uuid_m.group(1)}"

    # Modern app.envato.com/fonts/{uuid} path
    if uuid_m and ("app.envato.com" in raw or raw.endswith(uuid_m.group(1))):
        item_uuid = uuid_m.group(1).lower()
        title = title_hint or f"Envato Font {item_uuid[:8]}"
        author = ""
        try:
            req = urllib.request.Request(raw, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=12) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
            m_t = re.search(r'data-analytics-item_title="([^"]+)"', content) or re.search(r"<title>([^<]+?)\s*(?:-|—|\|).*?</title>", content)
            if m_t and not title_hint:
                title = html.unescape(m_t.group(1).strip())
            m_a = re.search(r'data-analytics-item_author="([^"]+)"', content)
            if m_a:
                author = html.unescape(m_a.group(1).strip())
        except Exception:
            pass
        return {
            "title": title,
            "author": author,
            "itemUuid": item_uuid,
            "variants": [{"id": None, "styleName": "Default"}],
            "url": raw,
        }

    # Classic elements.envato.com path via INITIAL_HYDRATION_DATA
    req = urllib.request.Request(raw, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8", errors="ignore")

    m = re.search(r'window\.INITIAL_HYDRATION_DATA="([^"]+)"', content)
    if not m:
        raise ValueError(f"No se encontró INITIAL_HYDRATION_DATA ni UUID en: {raw}")

    raw_json = base64.b64decode(m.group(1)).decode("utf-8")
    data = json.loads(raw_json)
    item = data.get("page", {}).get("data", {}).get("data", {}).get("item", {})
    item_uuid = item.get("itemUuid")
    if not item_uuid:
        raise ValueError(f"No se pudo extraer itemUuid para: {raw}")

    variants = (item.get("fontPreview") or {}).get("variants") or [{"id": None, "styleName": "Default"}]
    return {
        "title": title_hint or item.get("title", "Fuente sin título"),
        "author": item.get("author", ""),
        "itemUuid": item_uuid,
        "variants": variants,
        "url": raw,
    }


def fetch_svg_preview(item_uuid: str, text: str, variant_id: Optional[str], referer: str) -> str:
    params = {"itemUuid": item_uuid, "text": text, "typed": "1"}
    if variant_id:
        params["variant"] = variant_id
    svg_url = f"https://elements.envato.com/font-preview.svg?{urllib.parse.urlencode(params)}"
    last_err: Optional[Exception] = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(svg_url, headers={"User-Agent": USER_AGENT, "Referer": referer or "https://elements.envato.com/"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                svg_body = resp.read().decode("utf-8", errors="replace")
                if "<svg" in svg_body.lower():
                    return svg_body
                raise ValueError(f"Respuesta no SVG recibida ({len(svg_body)} bytes)")
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(0.6 * (attempt + 1))
                continue
            raise
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise
    if last_err:
        raise last_err
    return ""


def _fallback_on_hex(hex_str: str) -> str:
    h = hex_str.strip().lstrip("#")
    if len(h) != 6:
        return "#ffffff"
    r, g, b = int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#0a0a0a" if lum > 0.42 else "#ffffff"


def _extract_chroma_palettes(chroma_path: Optional[Path]) -> Tuple[str, str, Dict[str, Any], str, str]:
    dark_vars = "--bg:#0d1016;--surface:#161a23;--border:rgba(255,255,255,.12);--text:#f3f5f8;--muted:#9aa3b2;--primary:#3b82f6;--on-primary:#ffffff;--accent:#f59e0b;--on-accent:#0a0a0a;--secondary:#64748b;"
    light_vars = "--bg:#fafaf8;--surface:#eff1f5;--border:rgba(15,23,42,.12);--text:#0f1419;--muted:#4b5563;--primary:#1d4ed8;--on-primary:#ffffff;--accent:#d97706;--on-accent:#ffffff;--secondary:#475569;"
    palettes: Dict[str, Any] = {}
    default_eco = "default"
    default_mode = "light"
    if not chroma_path or not chroma_path.exists():
        return dark_vars, light_vars, palettes, default_eco, default_mode
    try:
        cdata = json.loads(chroma_path.read_text(encoding="utf-8"))
        sel_id = cdata.get("selected_ecosystem_id")
        default_mode = cdata.get("recommended_mode", "light")
        ecos = cdata.get("ecosystems", [])

        def _pack_mode(m: Dict[str, Any]) -> Dict[str, str]:
            p_hex = m["primary"]["hex"]
            a_hex = (m.get("accent") or m["primary"])["hex"]
            return {
                "--bg": m["background"]["hex"],
                "--surface": m["surface"]["hex"],
                "--border": f"{m['text_muted']['hex']}44",
                "--text": m["text_primary"]["hex"],
                "--muted": m["text_muted"]["hex"],
                "--primary": p_hex,
                "--on-primary": (m.get("on_primary") or {}).get("hex") or _fallback_on_hex(p_hex),
                "--accent": a_hex,
                "--on-accent": (m.get("on_accent") or {}).get("hex") or _fallback_on_hex(a_hex),
                "--secondary": (m.get("secondary") or m["text_muted"])["hex"],
            }

        for idx, eco in enumerate(ecos):
            eid = eco.get("id") or f"eco_{idx + 1}"
            d = eco.get("themes", {}).get("dark", {})
            lt = eco.get("themes", {}).get("light", {})
            palettes[eid] = {
                "name": eco.get("name", eid),
                "recommended_mode": eco.get("recommended_mode", default_mode),
                "dark": _pack_mode(d) if d else {},
                "light": _pack_mode(lt) if lt else {},
            }
        eco = next((e for e in ecos if e.get("id") == sel_id), ecos[0] if ecos else None)
        if eco:
            default_eco = eco.get("id") or default_eco
            default_mode = eco.get("recommended_mode", default_mode)
            if palettes[default_eco]["dark"]:
                dark_vars = "".join(f"{k}:{v};" for k, v in palettes[default_eco]["dark"].items())
            if palettes[default_eco]["light"]:
                light_vars = "".join(f"{k}:{v};" for k, v in palettes[default_eco]["light"].items())
    except Exception:
        pass
    return dark_vars, light_vars, palettes, default_eco, default_mode


def generate_gallery_html(
    items: List[Dict[str, Any]],
    output_file: str,
    chroma_path: Optional[Path] = None,
    gallery_title: str = "Visualizador de Fuentes Envato + Google Fonts",
) -> None:
    dark_vars, light_vars, palettes_map, default_eco, default_mode = _extract_chroma_palettes(chroma_path)
    eco_options = "".join(
        f'<option value="{html.escape(eid)}"{" selected" if eid == default_eco else ""}>{html.escape(pdata["name"])}</option>'
        for eid, pdata in palettes_map.items()
    )
    palettes_json = json.dumps(palettes_map, ensure_ascii=False)

    google_links: List[str] = []
    seen_gf: set[str] = set()
    for it in items:
        gf_url = it.get("google_fonts_v2_url")
        if gf_url and gf_url not in seen_gf:
            seen_gf.add(gf_url)
            google_links.append(f'<link rel="stylesheet" href="{html.escape(gf_url)}">')

    cards_html: List[str] = []
    for idx, item in enumerate(items):
        font_title = html.escape(item["title"])
        brand_text = html.escape(item["text"])
        font_url = html.escape(item["url"])
        eco_badge = html.escape(item.get("ecosystem_label") or "Envato Preview")
        role_badge = html.escape(item.get("role_label") or "Specimen")
        item_uuid = html.escape(item.get("itemUuid") or "")
        body_fam = html.escape(item.get("body_family") or "system-ui")

        variant_cards: List[str] = []
        for v in item["results"]:
            style_name = html.escape(v["styleName"])
            svg_content = v["svgContent"]
            svg_url = html.escape(v["svgUrl"])
            rel_svg = html.escape(v.get("filename", ""))
            variant_id = html.escape(str(v.get("variantId") or ""))

            card = f"""
            <div class="variant-card">
                <div class="variant-header">
                    <span class="style-badge">{style_name}</span>
                    <div class="actions">
                        <a href="{rel_svg}" download class="btn-download">Descargar SVG</a>
                        <a href="{svg_url}" target="_blank" class="btn-external">SVG Envato</a>
                    </div>
                </div>
                <div class="brand-lockup-grid">
                    <div class="lockup lockup-primary">
                        <small>1. Primario sobre Fondo</small>
                        <div class="svg-container svg-primary" data-uuid="{item_uuid}" data-variant="{variant_id}" data-tone="primary">{svg_content}</div>
                    </div>
                    <div class="lockup lockup-accent">
                        <small>2. Acento sobre Superficie</small>
                        <div class="svg-container svg-accent" data-uuid="{item_uuid}" data-variant="{variant_id}" data-tone="accent">{svg_content}</div>
                    </div>
                    <div class="lockup lockup-card">
                        <small>3. Tarjeta Invertida de Marca</small>
                        <div class="svg-container svg-on-primary" data-uuid="{item_uuid}" data-variant="{variant_id}" data-tone="on-primary">{svg_content}</div>
                    </div>
                    <div class="lockup lockup-hero">
                        <small>4. Mini Hero + Botón CTA Real ({body_fam})</small>
                        <div class="mini-hero" style="font-family:'{body_fam}', system-ui, sans-serif">
                            <p>Sistemas comerciales con identidad propia, sin fórmulas genéricas.</p>
                            <span class="cta-sample">Agendar sesión →</span>
                        </div>
                    </div>
                </div>
            </div>"""
            variant_cards.append(card)

        body_sample_html = ""
        if item.get("body_family"):
            body_sample_html = (
                f'<div class="body-pair" style="font-family:\'{body_fam}\', system-ui, sans-serif">'
                f'<small>Pareo Body UI (Google Fonts): <strong>{body_fam}</strong></small>'
                f'<p>Diseñamos sistemas claros para profesionales independientes: captación medible, asistentes conectados y finanzas en orden.</p>'
                f'</div>'
            )

        cards_html.append(f"""
        <section class="font-section" id="font-{idx}">
            <div class="font-meta">
                <div class="badges">
                    <span class="eco-pill">{eco_badge}</span>
                    <span class="role-pill">{role_badge}</span>
                </div>
                <h2>{font_title}</h2>
                <p class="brand-preview">Texto: <strong>"{brand_text}"</strong> · <a href="{font_url}" target="_blank">Abrir / Descargar en Envato Elements ↗</a></p>
            </div>
            <div class="variants-grid">{''.join(variant_cards)}</div>
            {body_sample_html}
        </section>""")

    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(gallery_title)}</title>
{''.join(google_links)}
<style>
  :root {{ --preview-h: 72px; {light_vars if default_mode == "light" else dark_vars} }}
  [data-theme="dark"] {{ {dark_vars} }}
  [data-theme="light"] {{ {light_vars} }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 32px 24px; transition: background .2s, color .2s; }}
  .header {{ max-width: 1260px; margin: 0 auto 28px; display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 16px; border-bottom: 1px solid var(--border); padding-bottom: 20px; }}
  .header h1 {{ font-size: 22px; font-weight: 700; }}
  .header p {{ color: var(--muted); font-size: 14px; margin-top: 4px; }}
  .controls {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
  .live-input, .eco-select {{ background: var(--surface); color: var(--text); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; font-size: 13px; }}
  .live-input {{ min-width: 220px; }}
  .btn {{ background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 8px 14px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; }}
  .btn-primary {{ background: var(--primary); color: var(--on-primary); border-color: var(--primary); }}
  .container {{ max-width: 1260px; margin: 0 auto; display: flex; flex-direction: column; gap: 28px; }}
  .font-section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 14px; padding: 22px; }}
  .badges {{ display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }}
  .eco-pill, .role-pill {{ font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 999px; border: 1px solid var(--border); color: var(--primary); }}
  .font-meta {{ margin-bottom: 16px; }}
  .font-meta h2 {{ font-size: 19px; font-weight: 600; }}
  .font-meta a {{ color: var(--primary); text-decoration: none; }}
  .brand-preview {{ color: var(--muted); font-size: 13px; margin-top: 4px; }}
  .variants-grid {{ display: flex; flex-direction: column; gap: 16px; }}
  .variant-card {{ background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 16px; display: flex; flex-direction: column; gap: 12px; }}
  .variant-header {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }}
  .actions {{ display: flex; gap: 6px; }}
  .style-badge {{ color: var(--muted); font-size: 11px; font-weight: 700; text-transform: uppercase; }}
  .btn-download, .btn-external {{ font-size: 12px; color: var(--muted); text-decoration: none; padding: 4px 8px; border-radius: 6px; border: 1px solid var(--border); }}
  .btn-download:hover, .btn-external:hover {{ color: var(--text); border-color: var(--primary); }}
  .brand-lockup-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
  .lockup {{ border-radius: 10px; padding: 12px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 8px; }}
  .lockup small {{ font-size: 11px; font-weight: 700; opacity: .78; }}
  .lockup-primary {{ background: var(--bg); }}
  .lockup-accent {{ background: var(--surface); }}
  .lockup-card {{ background: var(--primary); color: var(--on-primary); border-color: var(--primary); }}
  .lockup-hero {{ background: var(--surface); justify-content: space-between; }}
  .mini-hero p {{ font-size: 13px; line-height: 1.45; margin-bottom: 10px; color: var(--text); }}
  .cta-sample {{ display: inline-block; background: var(--primary); color: var(--on-primary); padding: 7px 14px; border-radius: 999px; font-size: 12px; font-weight: 700; }}
  .svg-container {{ min-height: 88px; display: flex; align-items: center; justify-content: center; padding: 10px; overflow-x: auto; }}
  .svg-container svg {{ max-width: 100%; height: auto; max-height: var(--preview-h); display: block; }}
  .svg-primary svg, .svg-primary svg * {{ fill: var(--primary) !important; stroke: none; }}
  .svg-accent svg, .svg-accent svg * {{ fill: var(--accent) !important; stroke: none; }}
  .svg-on-primary svg, .svg-on-primary svg * {{ fill: var(--on-primary) !important; stroke: none; }}
  .tone-neutral .svg-primary svg, .tone-neutral .svg-primary svg * {{ fill: var(--text) !important; }}
  .live-mask {{ width: 100%; height: var(--preview-h); -webkit-mask-repeat: no-repeat; mask-repeat: no-repeat; -webkit-mask-position: center; mask-position: center; -webkit-mask-size: contain; mask-size: contain; }}
  .svg-primary .live-mask {{ background-color: var(--primary); }}
  .svg-accent .live-mask {{ background-color: var(--accent); }}
  .svg-on-primary .live-mask {{ background-color: var(--on-primary); }}
  .tone-neutral .svg-primary .live-mask {{ background-color: var(--text); }}
  .body-pair {{ margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border); color: var(--text); }}
  .body-pair small {{ color: var(--muted); display: block; margin-bottom: 4px; }}
  .body-pair p {{ font-size: 15px; line-height: 1.55; max-width: 72ch; }}
</style>
</head>
<body data-theme="{html.escape(default_mode)}">
  <div class="header">
    <div>
      <h1>{html.escape(gallery_title)}</h1>
      <p>Vectores SVG Envato + Colores Reales de Marca (`--primary`, `--accent`, `--on-primary`) · Prueba la fuente aplicada en lockups reales.</p>
    </div>
    <div class="controls">
      {f'<select id="ecoSelect" class="eco-select" onchange="applyChromaPalette()">{eco_options}</select>' if eco_options else ''}
      <select id="brandToneSelect" class="eco-select" onchange="applyBrandTone()">
        <option value="brand">Modo Lockup: Colores de Marca</option>
        <option value="neutral">Modo Lockup: Tinta Neutra (Lectura)</option>
      </select>
      <input id="liveText" class="live-input" type="text" placeholder="Probar tu nombre de marca o frase..." />
      <label style="font-size:12px;color:var(--muted)">Tamaño <input id="sizeRange" type="range" min="48" max="130" value="72" oninput="document.documentElement.style.setProperty('--preview-h', this.value + 'px')" /></label>
      <button class="btn btn-primary" onclick="updateLivePreviews()">Probar en vivo</button>
      <button class="btn" onclick="document.getElementById('liveText').value='DISEÑO MÉTODO ÑÁÉ ¿¡';updateLivePreviews()">Probar Tildes ES</button>
      <button class="btn" onclick="toggleTheme()">Modo Oscuro / Claro</button>
    </div>
  </div>
  <div class="container">{''.join(cards_html)}</div>
  <script>
    const CHROMA_PALETTES = {palettes_json};
    function applyChromaPalette() {{
      const sel = document.getElementById('ecoSelect');
      if (!sel || !CHROMA_PALETTES[sel.value]) return;
      const mode = document.body.getAttribute('data-theme') || '{html.escape(default_mode)}';
      const vars = CHROMA_PALETTES[sel.value][mode] || CHROMA_PALETTES[sel.value].light || CHROMA_PALETTES[sel.value].dark;
      if (!vars) return;
      Object.entries(vars).forEach(([k, v]) => document.body.style.setProperty(k, v));
    }}
    function applyBrandTone() {{
      const val = document.getElementById('brandToneSelect')?.value || 'brand';
      document.body.classList.toggle('tone-neutral', val === 'neutral');
    }}
    function toggleTheme() {{
      const next = document.body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.body.setAttribute('data-theme', next);
      applyChromaPalette();
    }}
    function updateLivePreviews() {{
      const txt = document.getElementById('liveText').value.trim();
      if (!txt) return;
      document.querySelectorAll('.svg-container[data-uuid]').forEach(el => {{
        const uuid = el.getAttribute('data-uuid');
        if (!uuid) return;
        const variant = el.getAttribute('data-variant');
        const params = new URLSearchParams({{ itemUuid: uuid, text: txt, typed: '1' }});
        if (variant) params.set('variant', variant);
        const u = 'https://elements.envato.com/font-preview.svg?' + params.toString();
        el.innerHTML = '<div class="live-mask" role="img" aria-label="' + txt.replace(/"/g, '&quot;') + '" style="-webkit-mask-image:url(\'' + u + '\');mask-image:url(\'' + u + '\');"></div>';
      }});
    }}
    applyChromaPalette();
  </script>
</body>
</html>"""
    Path(output_file).write_text(full_html, encoding="utf-8")


def entries_from_urls(raw_urls: List[str], texts: List[str]) -> List[Dict[str, Any]]:
    """Builds batch entries directly from user-provided Envato Elements URLs or UUIDs."""
    entries: List[Dict[str, Any]] = []
    for i, u in enumerate(raw_urls):
        clean_u = u.strip()
        if not clean_u:
            continue
        for t in (texts or ["MARCA"]):
            entries.append({
                "url": clean_u,
                "text": t,
                "title_hint": "",
                "ecosystem_label": "Selección Directa del Fundador",
                "role_label": f"Fuente Curada #{i + 1}",
                "body_family": "Plus Jakarta Sans",
                "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap",
            })
    return entries


def entries_from_manifest(manifest_path: Path, texts: List[str], include_shortlist: bool = False) -> List[Dict[str, Any]]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    ecos = data.get("candidate_ecosystems", [])
    entries: List[Dict[str, Any]] = []
    seen_pairs: set[Tuple[str, str]] = set()
    for eco in ecos:
        eco_id = eco.get("id", "eco")
        eco_name = eco.get("name", eco_id)
        tokens = eco.get("tokens", {})
        ui = tokens.get("ui_secondary", {})
        body_fam = ui.get("$value", "")
        gf_url = ui.get("google_fonts_v2_url", "")
        for role_key, role_label in (("display_primary", "Display / Titulares"), ("accent_brand", "Monograma / Acento")):
            tok = tokens.get(role_key)
            if not isinstance(tok, dict) or tok.get("source") != "envato":
                continue
            url = tok.get("url") or ""
            if not url:
                continue
            for t in texts:
                seen_pairs.add((url, t))
                entries.append({
                    "url": url,
                    "text": t,
                    "title_hint": tok.get("$value", ""),
                    "ecosystem_label": f"{eco_id}: {eco_name}",
                    "role_label": role_label,
                    "body_family": body_fam,
                    "google_fonts_v2_url": gf_url,
                })
        if include_shortlist and texts:
            sc = eco.get("shortlist_candidates", {})
            primary_text = texts[0]
            for alt_key, alt_lbl in (("display_alternatives", "Alternativa Vanguardia (Display)"), ("accent_alternatives", "Alternativa Vanguardia (Acento)")):
                for alt in sc.get(alt_key, [])[:2]:
                    aurl = alt.get("url") or ""
                    if not aurl or (aurl, primary_text) in seen_pairs:
                        continue
                    seen_pairs.add((aurl, primary_text))
                    entries.append({
                        "url": aurl,
                        "text": primary_text,
                        "title_hint": alt.get("family", ""),
                        "ecosystem_label": f"{eco_id}: {eco_name}",
                        "role_label": f"{alt_lbl} · {alt.get('sort_source', 'vanguard')}",
                        "body_family": body_fam,
                        "google_fonts_v2_url": gf_url,
                    })
    return entries


def process_batch(
    items_to_process: List[Dict[str, Any]],
    output_dir: str,
    chroma_path: Optional[Path] = None,
    svg_fetcher=fetch_svg_preview,
    page_fetcher=fetch_page_data,
    gallery_title: str = "Visualizador de Fuentes Envato + Google Fonts",
) -> Path:
    os.makedirs(output_dir, exist_ok=True)
    all_gallery_items: List[Dict[str, Any]] = []

    for entry in items_to_process:
        url = str(entry["url"]).strip()
        brand_text = str(entry["text"]).strip()
        title_hint = str(entry.get("title_hint") or "")
        try:
            page_data = page_fetcher(url, title_hint=title_hint) if "title_hint" in getattr(page_fetcher, "__code__", type("", (), {"co_varnames": ("title_hint",)})()).co_varnames else page_fetcher(url)
            font_title = page_data["title"]
            item_uuid = page_data["itemUuid"]
            variants = page_data["variants"]

            results = []
            safe_title = sanitize_filename(font_title)[:25]
            safe_text = sanitize_filename(brand_text)[:20]

            for v in variants:
                v_id = v.get("id")
                v_name = v.get("styleName", "Default")
                safe_style = sanitize_filename(v_name)
                svg_content = svg_fetcher(item_uuid, brand_text, v_id, url)
                params = {"itemUuid": item_uuid, "text": brand_text, "typed": "1"}
                if v_id:
                    params["variant"] = v_id
                svg_url = f"https://elements.envato.com/font-preview.svg?{urllib.parse.urlencode(params)}"
                svg_filename = f"{safe_text}_{safe_title}_{safe_style}.svg"
                svg_filepath = os.path.join(output_dir, svg_filename)
                Path(svg_filepath).write_text(svg_content, encoding="utf-8")
                results.append({
                    "styleName": v_name,
                    "variantId": v_id,
                    "svgUrl": svg_url,
                    "svgContent": svg_content,
                    "filename": svg_filename,
                    "filepath": svg_filepath,
                })

            all_gallery_items.append({
                "title": font_title,
                "itemUuid": item_uuid,
                "text": brand_text,
                "url": url,
                "ecosystem_label": entry.get("ecosystem_label", ""),
                "role_label": entry.get("role_label", ""),
                "body_family": entry.get("body_family", ""),
                "google_fonts_v2_url": entry.get("google_fonts_v2_url", ""),
                "results": results,
            })
        except Exception as e:
            print(f"❌ Error procesando {url}: {e}", file=sys.stderr)

    gallery_path = Path(output_dir) / "preview_gallery.html"
    generate_gallery_html(all_gallery_items, str(gallery_path), chroma_path=chroma_path, gallery_title=gallery_title)
    manifest_out = Path(output_dir) / "manifest.json"
    manifest_out.write_text(json.dumps(all_gallery_items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return gallery_path


def run_unit_tests() -> int:
    print("Running envato_font_preview v4.0 offline unit tests...")
    with tempfile.TemporaryDirectory(prefix="envato_preview_test_") as tmp:
        tp = Path(tmp)
        fm_path = tp / "font_manifest.json"
        cm_path = tp / "chroma_manifest.json"
        out_dir = tp / "previews"

        fm_path.write_text(json.dumps({
            "brand": "AURELIUS",
            "candidate_ecosystems": [{
                "id": "eco-1",
                "name": "Test Editorial",
                "tokens": {
                    "display_primary": {"$value": "Domani", "source": "envato", "url": "https://app.envato.com/fonts/1de94cfa-3ac9-4fd1-b5b2-113405506be3"},
                    "ui_secondary": {"$value": "Manrope", "source": "google_fonts", "google_fonts_v2_url": "https://fonts.googleapis.com/css2?family=Manrope:wght@400..700&display=swap"},
                    "accent_brand": {"$value": "Monogram Holder", "source": "envato", "url": "https://app.envato.com/fonts/b072395d-990e-4637-a1ca-2c8b0355aed0"},
                }
            }]
        }), encoding="utf-8")
        cm_path.write_text(json.dumps({
            "selected_ecosystem_id": "eco_1",
            "recommended_mode": "light",
            "ecosystems": [{
                "id": "eco_1",
                "themes": {
                    "dark": {"background": {"hex": "#0d1016"}, "surface": {"hex": "#161a23"}, "primary": {"hex": "#f50023"}, "on_primary": {"hex": "#ffffff"}, "accent": {"hex": "#c8a84b"}, "on_accent": {"hex": "#0a0a0a"}, "text_primary": {"hex": "#f2f6fa"}, "text_muted": {"hex": "#8e9cb0"}},
                    "light": {"background": {"hex": "#f9f7f1"}, "surface": {"hex": "#efece3"}, "primary": {"hex": "#f50023"}, "on_primary": {"hex": "#ffffff"}, "accent": {"hex": "#c8a84b"}, "on_accent": {"hex": "#0a0a0a"}, "text_primary": {"hex": "#121212"}, "text_muted": {"hex": "#566273"}},
                }
            }]
        }), encoding="utf-8")

        entries = entries_from_manifest(fm_path, ["AURELIUS", "NEXUS"])
        custom_entries = entries_from_urls(["https://app.envato.com/fonts/1de94cfa-3ac9-4fd1-b5b2-113405506be3"], ["AURELIUS"])
        assert len(entries) == 4 and len(custom_entries) == 1

        mock_page = lambda url, title_hint="": {
            "title": title_hint or "Mock Font",
            "itemUuid": UUID_RE.search(url).group(1),
            "variants": [{"id": None, "styleName": "Regular"}],
            "url": url,
        }
        mock_svg = lambda uuid, text, vid, ref: f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 30"><path d="M0 0h10v10"/></svg>'
        gal = process_batch(entries, str(out_dir), chroma_path=cm_path, svg_fetcher=mock_svg, page_fetcher=mock_page)
        assert gal.exists()
        html_out = gal.read_text(encoding="utf-8")
        assert "#f50023" in html_out and "--on-primary" in html_out and "brand-lockup-grid" in html_out
        assert "live-mask" in html_out and "filter: invert(1)" not in html_out
        assert (out_dir / "manifest.json").exists()
    print("✅ ENVATO FONT PREVIEW v4.0 UNIT TESTS PASSED (4-color brand lockups, --envato-urls, CSS mask tint, 0 B/W invert)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Envato Elements Full-Color Brand Previewer v4.0")
    parser.add_argument("url", nargs="?", help="URL de fuente Envato (app.envato.com o elements.envato.com) o UUID")
    parser.add_argument("text", nargs="?", help="Texto a previsualizar")
    parser.add_argument("--out", "-o", default="./font_previews", help="Carpeta de salida")
    parser.add_argument("--batch", "-b", help="Archivo JSON con [{url, text}]")
    parser.add_argument("--from-manifest", type=Path, help="Leer fuentes Envato desde font_manifest.json")
    parser.add_argument("--envato-urls", default="", help="URLs/UUIDs directas de Envato separadas por coma")
    parser.add_argument("--chroma", type=Path, default=None, help="Chroma manifest JSON para aplicar colores reales de marca")
    parser.add_argument("--texts", default="BRAND,MARCA", help="Textos separados por coma para --from-manifest o --envato-urls")
    parser.add_argument("--include-shortlist", action="store_true", help="Incluir alternativas vanguardia de shortlist_candidates")
    parser.add_argument("--title", default="Visualizador Full-Color Envato + Google Fonts", help="Título HTML de la galería")
    parser.add_argument("--test", action="store_true", help="Ejecutar pruebas unitarias offline")
    args = parser.parse_args()

    if args.test:
        return run_unit_tests()

    items: List[Dict[str, Any]] = []
    texts = [t.strip() for t in args.texts.split(",") if t.strip()] or ["MARCA"]
    if args.from_manifest:
        items.extend(entries_from_manifest(args.from_manifest, texts, include_shortlist=args.include_shortlist))
    if args.envato_urls:
        raw_urls = [u.strip() for u in args.envato_urls.split(",") if u.strip()]
        items.extend(entries_from_urls(raw_urls, texts))
    if not items and args.batch:
        items = json.loads(Path(args.batch).read_text(encoding="utf-8"))
    elif not items and args.url and args.text:
        items = [{"url": args.url, "text": args.text}]
    elif not items:
        parser.print_help()
        return 1

    gal = process_batch(items, args.out, chroma_path=args.chroma, gallery_title=args.title)
    print(f"✅ Galería HTML Full-Color Envato v4.0 generada en: {gal}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
