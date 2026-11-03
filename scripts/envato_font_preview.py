#!/usr/bin/env python3
"""
Envato Elements Font Previewer & SVG Vector Extractor (v2.0)
Extrae y visualiza fuentes de Envato Elements con cualquier texto de marca
sin descargar fuentes completas ni requerir login. Genera SVGs y galería HTML interactiva.
"""
import sys
import os
import re
import json
import base64
import argparse
import html
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch_page_data(url: str) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8")
        
    m = re.search(r'window\.INITIAL_HYDRATION_DATA="([^"]+)"', content)
    if not m:
        raise ValueError(f"No se encontró INITIAL_HYDRATION_DATA en la URL: {url}")
        
    raw_json = base64.b64decode(m.group(1)).decode("utf-8")
    data = json.loads(raw_json)
    item = data.get("page", {}).get("data", {}).get("data", {}).get("item", {})
    
    item_uuid = item.get("itemUuid")
    title = item.get("title", "Fuente sin título")
    font_preview = item.get("fontPreview") or {}
    variants = font_preview.get("variants", [])
    
    if not item_uuid:
        raise ValueError(f"No se pudo extraer itemUuid para: {url}")
        
    if not variants:
        variants = [{"id": None, "styleName": "Default"}]
        
    return {
        "title": title,
        "itemUuid": item_uuid,
        "variants": variants,
        "url": url
    }

def fetch_svg_preview(item_uuid: str, text: str, variant_id: Optional[str], referer: str) -> str:
    params = {
        "itemUuid": item_uuid,
        "text": text,
        "typed": "1"
    }
    if variant_id:
        params["variant"] = variant_id
        
    svg_url = f"https://elements.envato.com/font-preview.svg?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        svg_url,
        headers={"User-Agent": USER_AGENT, "Referer": referer}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name).strip('_')

def generate_gallery_html(items: List[Dict[str, Any]], output_file: str):
    cards_html = []
    
    for item in items:
        font_title = html.escape(item["title"])
        brand_text = html.escape(item["text"])
        font_url = html.escape(item["url"])
        
        variant_cards = []
        for v in item["results"]:
            style_name = html.escape(v["styleName"])
            svg_content = v["svgContent"]
            svg_url = html.escape(v["svgUrl"])
            rel_svg_path = html.escape(v.get("filename", ""))
            
            # Make sure svg has fill or currentColor
            card = f"""
            <div class="variant-card">
                <div class="variant-header">
                    <span class="style-badge">{style_name}</span>
                    <a href="{rel_svg_path}" download class="btn-download" title="Descargar archivo SVG">📥 Descargar SVG</a>
                    <a href="{svg_url}" target="_blank" class="btn-external" title="Abrir URL original de Envato">🔗 Link Envato</a>
                </div>
                <div class="svg-container">
                    {svg_content}
                </div>
            </div>
            """
            variant_cards.append(card)
            
        font_block = f"""
        <section class="font-section">
            <div class="font-meta">
                <h2>{font_title}</h2>
                <p class="brand-preview">Texto: <strong>"{brand_text}"</strong> · <a href="{font_url}" target="_blank">Ficha en Envato Elements ↗</a></p>
            </div>
            <div class="variants-grid">
                {''.join(variant_cards)}
            </div>
        </section>
        """
        cards_html.append(font_block)
        
    full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visualizador de Marcas & Fuentes - Envato Elements</title>
    <style>
        :root {{
            --bg: #090a0f;
            --surface: #12141c;
            --surface-border: #232738;
            --text-primary: #f0f2f8;
            --text-muted: #8b92a8;
            --accent: #ff0055;
            --accent-glow: rgba(255, 0, 85, 0.2);
            --badge-bg: #1e2233;
        }}
        [data-theme="light"] {{
            --bg: #f8f9fc;
            --surface: #ffffff;
            --surface-border: #e2e5ec;
            --text-primary: #0f1117;
            --text-muted: #646a7e;
            --accent: #e0004c;
            --badge-bg: #edf0f7;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            padding: 32px 24px;
            transition: background 0.2s, color 0.2s;
        }}
        .header {{
            max-width: 1200px;
            margin: 0 auto 36px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            border-bottom: 1px solid var(--surface-border);
            padding-bottom: 24px;
        }}
        .header h1 {{ font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }}
        .header p {{ color: var(--text-muted); font-size: 14px; margin-top: 4px; }}
        .controls {{ display: flex; gap: 12px; align-items: center; }}
        .btn-theme {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 40px; }}
        .font-section {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 14px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }}
        .font-meta {{ margin-bottom: 20px; }}
        .font-meta h2 {{ font-size: 20px; font-weight: 600; }}
        .font-meta a {{ color: var(--accent); text-decoration: none; }}
        .font-meta a:hover {{ text-decoration: underline; }}
        .brand-preview {{ color: var(--text-muted); font-size: 14px; margin-top: 6px; }}
        .variants-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
        }}
        .variant-card {{
            background: var(--bg);
            border: 1px solid var(--surface-border);
            border-radius: 10px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}
        .variant-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .style-badge {{
            background: var(--badge-bg);
            color: var(--text-primary);
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .btn-download, .btn-external {{
            font-size: 12px;
            color: var(--text-muted);
            text-decoration: none;
            padding: 4px 8px;
            border-radius: 6px;
            border: 1px solid var(--surface-border);
            transition: all 0.15s;
        }}
        .btn-download:hover, .btn-external:hover {{
            color: var(--text-primary);
            border-color: var(--accent);
        }}
        .svg-container {{
            min-height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
            background: var(--surface);
            border-radius: 8px;
            border: 1px dashed var(--surface-border);
            overflow-x: auto;
        }}
        .svg-container svg {{
            max-width: 100%;
            height: auto;
            max-height: 100px;
            display: block;
        }}
        /* Color handling for SVG paths */
        [data-theme="dark"] .svg-container svg path {{ fill: #ffffff !important; }}
        [data-theme="light"] .svg-container svg path {{ fill: #111111 !important; }}
        body:not([data-theme]) .svg-container svg path {{ fill: #ffffff !important; }}
    </style>
</head>
<body data-theme="dark">
    <div class="header">
        <div>
            <h1>🎨 Visualizador de Fuentes & Marcas (Envato Elements)</h1>
            <p>Vectores SVG extraídos en tiempo real sin login ni instalación de fuentes.</p>
        </div>
        <div class="controls">
            <button class="btn-theme" onclick="toggleTheme()">🌓 Alternar Fondo (Oscuro / Claro)</button>
        </div>
    </div>

    <div class="container">
        {''.join(cards_html)}
    </div>

    <script>
        function toggleTheme() {{
            const body = document.body;
            const current = body.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            body.setAttribute('data-theme', next);
        }}
    </script>
</body>
</html>
"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_html)

def process_batch(items_to_process: List[Dict[str, str]], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    all_gallery_items = []
    
    print(f"\n🚀 Procesando {len(items_to_process)} fuente(s) con destino: {output_dir}")
    
    for idx, entry in enumerate(items_to_process, 1):
        url = entry["url"].strip()
        brand_text = entry["text"].strip()
        
        print(f"\n[{idx}/{len(items_to_process)}] Consultando: {url}")
        print(f"      Texto: \"{brand_text}\"")
        
        try:
            page_data = fetch_page_data(url)
            font_title = page_data["title"]
            item_uuid = page_data["itemUuid"]
            variants = page_data["variants"]
            
            print(f"      Fuente: {font_title} (UUID: {item_uuid})")
            print(f"      Variantes encontradas: {len(variants)}")
            
            results = []
            safe_title = sanitize_filename(font_title)[:25]
            safe_text = sanitize_filename(brand_text)[:20]
            
            for v in variants:
                v_id = v.get("id")
                v_name = v.get("styleName", "Default")
                safe_style = sanitize_filename(v_name)
                
                svg_content = fetch_svg_preview(item_uuid, brand_text, v_id, url)
                
                params = {"itemUuid": item_uuid, "text": brand_text, "typed": "1"}
                if v_id:
                    params["variant"] = v_id
                svg_url = f"https://elements.envato.com/font-preview.svg?{urllib.parse.urlencode(params)}"
                
                svg_filename = f"{safe_text}_{safe_title}_{safe_style}.svg"
                svg_filepath = os.path.join(output_dir, svg_filename)
                
                with open(svg_filepath, "w", encoding="utf-8") as f:
                    f.write(svg_content)
                    
                results.append({
                    "styleName": v_name,
                    "variantId": v_id,
                    "svgUrl": svg_url,
                    "svgContent": svg_content,
                    "filename": svg_filename,
                    "filepath": svg_filepath
                })
                print(f"      ✓ Estilo [{v_name}] guardado en: {svg_filename}")
                
            all_gallery_items.append({
                "title": font_title,
                "text": brand_text,
                "url": url,
                "results": results
            })
            
        except Exception as e:
            print(f"      ❌ Error procesando {url}: {e}", file=sys.stderr)
            
    # Generate HTML Gallery
    gallery_path = os.path.join(output_dir, "preview_gallery.html")
    generate_gallery_html(all_gallery_items, gallery_path)
    print(f"\n✨ ¡Galería HTML generada exitosamente en:\n👉 {gallery_path}\n")
    
    # Save Manifest JSON
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(all_gallery_items, f, indent=2, ensure_ascii=False)
    print(f"📄 Manifiesto JSON guardado en: {manifest_path}\n")

def main():
    parser = argparse.ArgumentParser(description="Envato Elements Font Previewer & SVG Extractor")
    parser.add_argument("url", nargs="?", help="URL de la fuente en Envato Elements")
    parser.add_argument("text", nargs="?", help="Nombre de marca / texto a previsualizar")
    parser.add_argument("--out", "-o", default="./font_previews", help="Carpeta de salida (default: ./font_previews)")
    parser.add_argument("--batch", "-b", help="Ruta a archivo JSON con lista de objetos [{url, text}]")
    
    args = parser.parse_args()
    
    items = []
    if args.batch:
        if not os.path.exists(args.batch):
            print(f"Error: No existe el archivo batch {args.batch}", file=sys.stderr)
            sys.exit(1)
        with open(args.batch, "r", encoding="utf-8") as f:
            items = json.load(f)
    elif args.url and args.text:
        items = [{"url": args.url, "text": args.text}]
    else:
        parser.print_help()
        print("\nEjemplos:")
        print("  envato-font-preview https://elements.envato.com/es/klise-modern-branding-elegant-font-U5HKGHT \"JUAN KREISS\"")
        print("  envato-font-preview --batch lista_fuentes.json --out ./galeria_marcas")
        sys.exit(1)
        
    process_batch(items, args.out)

if __name__ == "__main__":
    main()
