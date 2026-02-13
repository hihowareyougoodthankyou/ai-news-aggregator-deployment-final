"""Entry point for Railway - runs the scheduler (daily digest at 1:30 PM EST)"""
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from app.database.create_tables import create_tables
from app.scheduler import start_scheduler


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


def run_health_server():
    """Bind to PORT so Railway health checks pass - keeps the service running"""
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("", port), HealthHandler)
    server.serve_forever()


if __name__ == "__main__":
    create_tables()
    port = os.getenv("PORT")
    if port:
        t = threading.Thread(target=run_health_server, daemon=True)
        t.start()
    start_scheduler()
