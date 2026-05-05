#!/usr/bin/env python3
"""Simple HTTP server for system monitor dashboard with multi-machine support."""

import http.server
import json
import os
import re
import socketserver
from pathlib import Path

PORT = 8765
DIR = Path(__file__).parent.resolve()
DATA_DIR = DIR / "data"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/machines":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            machines = self._discover_machines()
            self.wfile.write(json.dumps(machines).encode())
            return
        return super().do_GET()

    def _discover_machines(self):
        """Scan data dir for unique hostname+gpctype+gpunum combos."""
        pattern = re.compile(r"^metrics_(.+)_(\d{8})\.json$")
        seen = {}
        try:
            for fname in os.listdir(DATA_DIR):
                m = pattern.match(fname)
                if m:
                    hostname = m.group(1)
                    key = hostname
                    if key not in seen:
                        # peek into file to get gpu info
                        path = DATA_DIR / fname
                        try:
                            with open(path) as f:
                                first_line = f.readline()
                                record = json.loads(first_line)
                                gpu_type = record.get("gpu_type")
                                gpu_count = record.get("gpu_count", 0)
                                # Fallback: check if GPU data exists in record itself
                                has_gpu = record.get("gpu") and not record.get("gpu", {}).get("error")
                                if gpu_type is None and has_gpu:
                                    gpu_type = "NVIDIA GPU"
                                if gpu_count == 0 and has_gpu:
                                    gpu_count = 1
                                seen[key] = {
                                    "hostname": hostname,
                                    "gpu_type": gpu_type,
                                    "gpu_count": gpu_count,
                                }
                        except Exception:
                            seen[key] = {
                                "hostname": hostname,
                                "gpu_type": None,
                                "gpu_count": 0,
                            }
        except FileNotFoundError:
            pass
        return list(seen.values())


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"System Monitor Dashboard → http://localhost:{PORT}")
        httpd.serve_forever()
