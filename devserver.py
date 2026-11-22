#!/usr/bin/env python3
"""Local preview, mirroring the routes vercel.json sets up in production.

    python3 devserver.py          then open http://localhost:8000

Set GITHUB_TOKEN first for exact daily counts; without it the public fragment
is used instead.
"""

import argparse
import importlib.util
import pathlib
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


TIMELINE = _load("api_timeline", ROOT / "api" / "timeline.py")
META = _load("api_meta", ROOT / "api" / "meta.py")


class Router(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "public"), **kwargs)

    def log_message(self, fmt, *args):
        sys.stderr.write("  %s\n" % (fmt % args))

    def do_GET(self):
        parsed = urlparse(self.path)
        path, query = parsed.path, parsed.query

        if path in ("/api/timeline", "/timeline.svg"):
            return TIMELINE.handler.do_GET(self)
        if path == "/api/meta":
            return META.handler.do_GET(self)
        # /<username>.svg is the short form of /api/timeline?user=<username>
        if path.endswith(".svg") and path.count("/") == 1:
            user = path[1:-4]
            self.path = f"/api/timeline?user={user}" + (f"&{query}" if query else "")
            return TIMELINE.handler.do_GET(self)
        return super().do_GET()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    print(f"timeline dev server on http://localhost:{args.port}")
    ThreadingHTTPServer(("127.0.0.1", args.port), Router).serve_forever()
