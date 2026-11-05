#!/usr/bin/env python3
"""
Workbench Server & Font Extraction / Rendering API (v2.2)
Sirve la aplicación estática del Workbench y proporciona los endpoints:
  - GET /api/extract?url=<url>&text=<text> -> Extrae itemUuid y variantes de Envato Elements
  - GET /api/render?itemUuid=<uuid>&text=<text>&variant=<id> -> Proxy SVG que elimina CORS
"""
import http.server
import socketserver
import urllib.parse
import urllib.request
import json
import base64
import re
import os
import sys
import mimetypes

mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("font/woff", ".woff")
mimetypes.add_type("font/ttf", ".ttf")
mimetypes.add_type("font/otf", ".otf")
mimetypes.add_type("image/svg+xml", ".svg")

PORT = 8888
STATIC_DIR = "/var/www/font_previews"
CATALOG_FILE = os.path.join(STATIC_DIR, "catalog.json")
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class WorkbenchHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        # Allow CORS on all endpoints and static assets (fonts, svgs, etc.)
        self.send_header("Access-Control-Allow-Origin", "*")
        # Force no-cache on HTML so browsers never serve stale UI versions
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.endswith(".html") or parsed.path == "/" or parsed.path.endswith("/"):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, HEAD")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.end_headers()

    def do_HEAD(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.endswith("/api/render") or parsed.path.endswith("/api/extract") or parsed.path.endswith("/api/fonts") or parsed.path.endswith("/api/catalog"):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return
        return super().do_HEAD()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.endswith("/api/fonts") or parsed.path.endswith("/api/catalog"):
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(body)
                fonts = None
                if isinstance(payload, dict) and "fonts" in payload:
                    fonts = payload["fonts"]
                elif isinstance(payload, list):
                    fonts = payload
                
                if isinstance(fonts, list):
                    # Backup old catalog before overwriting
                    if os.path.exists(CATALOG_FILE):
                        try:
                            with open(CATALOG_FILE, "r", encoding="utf-8") as f_old:
                                old_data = f_old.read()
                            with open(CATALOG_FILE + ".bak", "w", encoding="utf-8") as f_bak:
                                f_bak.write(old_data)
                        except Exception:
                            pass
                    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
                        json.dump(fonts, f, indent=2, ensure_ascii=False)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": True, "count": len(fonts)}).encode("utf-8"))
                    return
                else:
                    raise ValueError("Se esperaba lista de fuentes en 'fonts'")
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
                return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        # 0. Endpoint Catálogo Persistente de Fuentes
        if parsed.path.endswith("/api/fonts") or parsed.path.endswith("/api/catalog"):
            try:
                fonts = []
                if os.path.exists(CATALOG_FILE):
                    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
                        fonts = json.load(f)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "fonts": fonts}).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
                return
        
        # 1. Endpoint Proxy SVG para renderizar cualquier texto con fuente Envato (Sin problemas de CORS)
        if parsed.path.endswith("/api/render"):
            query = urllib.parse.parse_qs(parsed.query)
            item_uuid = query.get("itemUuid", [""])[0].strip()
            text = query.get("text", ["BRAND"])[0].strip()
            variant_id = query.get("variant", [""])[0].strip()
            
            if not item_uuid:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "itemUuid requerido"}).encode("utf-8"))
                return
                
            params = {
                "itemUuid": item_uuid,
                "text": text,
                "typed": "1"
            }
            if variant_id:
                params["variant"] = variant_id
                
            svg_url = f"https://elements.envato.com/font-preview.svg?{urllib.parse.urlencode(params)}"
            try:
                req = urllib.request.Request(
                    svg_url,
                    headers={"User-Agent": USER_AGENT, "Referer": "https://elements.envato.com/"}
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    svg_data = resp.read()
                    
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(svg_data)
                return
            except Exception as e:
                self.send_response(502)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Error conectando con Envato: {e}"}).encode("utf-8"))
                return

        # 2. Endpoint de extracción de fuentes Envato
        if parsed.path.endswith("/api/extract"):
            query = urllib.parse.parse_qs(parsed.query)
            envato_url = query.get("url", [""])[0].strip()
            brand_text = query.get("text", ["BRAND"])[0].strip()
            
            if not envato_url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Parámetro 'url' requerido"}).encode("utf-8"))
                return
                
            try:
                if not envato_url.startswith("http"):
                    envato_url = f"https://{envato_url}"
                    
                req = urllib.request.Request(envato_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    html_content = resp.read().decode("utf-8")
                    
                m = re.search(r'window\.INITIAL_HYDRATION_DATA="([^"]+)"', html_content)
                if not m:
                    raise ValueError("No se encontró INITIAL_HYDRATION_DATA en la página de Envato Elements")
                    
                data = json.loads(base64.b64decode(m.group(1)).decode("utf-8"))
                item = data.get("page", {}).get("data", {}).get("data", {}).get("item", {})
                item_uuid = item.get("itemUuid")
                title = item.get("title", "Fuente Envato")
                font_preview = item.get("fontPreview") or {}
                variants = font_preview.get("variants", [])
                item_attributes = item.get("itemAttributes") or {}
                total_style_count = font_preview.get("totalStyleCount", len(variants))
                default_style_name = font_preview.get("defaultStyleName", "Regular")
                
                if not item_uuid:
                    raise ValueError("No se pudo obtener el itemUuid del ítem")
                    
                if not variants:
                    variants = [{"id": None, "styleName": "Default"}]
                    
                # Fetch preview SVG para cada variante
                results = []
                for v in variants:
                    v_id = v.get("id")
                    v_name = v.get("styleName", "Default")
                    
                    params = {
                        "itemUuid": item_uuid,
                        "text": brand_text,
                        "typed": "1"
                    }
                    if v_id:
                        params["variant"] = v_id
                        
                    svg_url = f"https://elements.envato.com/font-preview.svg?{urllib.parse.urlencode(params)}"
                    try:
                        req_svg = urllib.request.Request(svg_url, headers={"User-Agent": USER_AGENT, "Referer": envato_url})
                        with urllib.request.urlopen(req_svg, timeout=8) as s_resp:
                            svg_code = s_resp.read().decode("utf-8")
                    except Exception:
                        svg_code = ""
                        
                    results.append({
                        "styleName": v_name,
                        "variantId": v_id,
                        "svgUrl": svg_url,
                        "svgContent": svg_code
                    })
                    
                response_data = {
                    "ok": True,
                    "title": title,
                    "itemUuid": item_uuid,
                    "url": envato_url,
                    "text": brand_text,
                    "totalStyleCount": total_style_count,
                    "defaultStyleName": default_style_name,
                    "itemAttributes": {
                        "ligatures": item_attributes.get("ligatures", False),
                        "stylisticSet": item_attributes.get("stylisticSet", False),
                        "alternates": item_attributes.get("alternates", False),
                        "spacing": item_attributes.get("spacing", []),
                        "serifSansSerif": item_attributes.get("serifSansSerif", ""),
                        "fontUsage": item_attributes.get("fontUsage", []),
                        "supportedLanguages": item_attributes.get("supportedLanguages", [])
                    },
                    "variants": results
                }

                # Auto-persist extracted font into CATALOG_FILE
                try:
                    font_entry = {
                        "id": f"envato_{item_uuid}",
                        "title": title,
                        "url": envato_url,
                        "itemUuid": item_uuid,
                        "totalStyleCount": total_style_count,
                        "defaultStyleName": default_style_name,
                        "itemAttributes": response_data["itemAttributes"],
                        "variants": results,
                        "previewSvg": results[0]["svgContent"] if results else ""
                    }
                    catalog = []
                    if os.path.exists(CATALOG_FILE):
                        with open(CATALOG_FILE, "r", encoding="utf-8") as cf:
                            catalog = json.load(cf)
                    existing_idx = next((i for i, f in enumerate(catalog) if f.get("id") == font_entry["id"]), -1)
                    if existing_idx != -1:
                        catalog[existing_idx] = font_entry
                    else:
                        catalog.insert(0, font_entry)
                    with open(CATALOG_FILE, "w", encoding="utf-8") as cf:
                        json.dump(catalog, cf, indent=2, ensure_ascii=False)
                except Exception as cat_err:
                    print("Error auto-guardando en catalog.json:", cat_err)
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
                return
                
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
                return
                
        # 3. Servir archivos estáticos normales
        return super().do_GET()

def run_server():
    os.makedirs(STATIC_DIR, exist_ok=True)
    server_address = ("0.0.0.0", PORT)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(server_address, WorkbenchHandler) as httpd:
        print(f"🚀 Workbench Server corriendo en http://0.0.0.0:{PORT} sirviendo {STATIC_DIR}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
