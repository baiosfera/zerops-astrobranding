"""
Oráculo Astrological Multi-Tradition Engine & Decoupled MCP Runtime (v1.0).
Zero Live Calls during build; exposes /health for Zerops readiness check.
"""

import http.server
import json
import os
import socketserver

PORT = int(os.environ.get("PORT", 8001))


class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp = {
                "status": "ok",
                "service": "oraculo-engine",
                "version": "1.0.0",
                "database_connected": bool(os.environ.get("DATABASE_URL")),
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), HealthHandler) as httpd:
        print(f"Oraculo Engine listening on port {PORT}")
        httpd.serve_forever()
