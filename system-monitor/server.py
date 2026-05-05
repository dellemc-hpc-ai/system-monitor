#!/usr/bin/env python3
"""Simple HTTP server for system monitor dashboard."""

import http.server
import os
import socketserver
from pathlib import Path

PORT = 8765
DIR = Path(__file__).parent.resolve()

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"System Monitor Dashboard → http://localhost:{PORT}")
        httpd.serve_forever()
