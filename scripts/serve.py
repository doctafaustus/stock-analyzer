"""Local dev server with auto-reload.

Run:  python scripts/serve.py   then open http://localhost:8765
The page polls /__version and reloads itself when any project file changes.
"""
import http.server
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8765
WATCH = (".html", ".css", ".js")


def version():
    return max((p.stat().st_mtime for p in ROOT.iterdir() if p.suffix in WATCH), default=0)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if self.path == "/__version":
            body = json.dumps({"v": version()}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"Serving {ROOT} at http://localhost:{PORT}")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
