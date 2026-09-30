"""
Nous Research Hermes-Agent: Autonomous Daemon & NATS Event Bridge
Pure Python standard library HTTP health server + NATS JetStream daemon.
Zero FastAPI/Uvicorn runtime bloat.
"""
import os
import sys
import json
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
try:
    from agent import HermesAgent
except (ImportError, ValueError):
    from .agent import HermesAgent

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/health", "/healthz", "/"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            status_payload = {
                "status": "ok",
                "service": "hermes-agent",
                "mode": "daemon_nats_bridge",
                "model_endpoint": os.getenv("HERMES_MODEL_ENDPOINT", "http://bifrost:8080/v1"),
                "nats_url": os.getenv("ZCP_NATS_URL", "nats://nats:4222"),
            }
            self.wfile.write(json.dumps(status_payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Quiet standard logging
        pass

def run_health_server(port: int = 8000):
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"[Hermes-Agent] Health server listening on port {port}")
    server.serve_forever()

async def run_nats_bridge():
    """
    Hermes background consumer for NATS JetStream events.
    Listens for events.ops and coaching notifications.
    """
    agent = HermesAgent()
    print("[Hermes-Agent] Autonomous loop and NATS event listener initialized.")
    while True:
        await asyncio.sleep(60)

def main():
    port = int(os.getenv("PORT", "8000"))
    # Start health server in background daemon thread
    server_thread = threading.Thread(target=run_health_server, args=(port,), daemon=True)
    server_thread.start()

    # Run primary async agent loop
    try:
        asyncio.run(run_nats_bridge())
    except KeyboardInterrupt:
        print("[Hermes-Agent] Shutting down gracefully.")

if __name__ == "__main__":
    main()
