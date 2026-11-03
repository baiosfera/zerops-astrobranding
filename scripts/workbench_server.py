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

PORT = 8888
STATIC_DIR = "/var/www/font_previews"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class WorkbenchHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_HEAD(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.endswith("/api/render") or parsed.path.endswith("/api/extract"):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return
        return super().do_HEAD()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
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
                    "variants": results
                }
                
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
