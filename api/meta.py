"""GET /api/meta?user=<login> -> JSON describing what the renderer found.

The configurator calls this to tell someone their username resolved, and whether
the deployment is reading exact counts or the public approximation.
"""

import json
import os
import pathlib
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from timeline import Options, NotFound, Unavailable, source, wave   # noqa: E402

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("TIMELINE_GITHUB_TOKEN") or ""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query, keep_blank_values=True)
        opts = Options({k: v[0] for k, v in query.items()})

        if not opts.user:
            status, out = 400, {"ok": False, "error": "give a GitHub username"}
        else:
            try:
                totals, origin = source.cached_weekly_totals(opts.user, TOKEN, opts.weeks)
                usable = wave.from_totals(totals, opts.cols, opts.smooth) is not None
                out = {"ok": True, "user": opts.user, "weeks": len(totals), "source": origin,
                       "exact": origin == "api", "usable": usable,
                       "busiest_week": max(totals) if totals else 0,
                       "total": sum(totals)}
                status = 200
            except NotFound:
                status, out = 404, {"ok": False, "error": f"no GitHub user called {opts.user}"}
            except Unavailable as exc:
                status, out = 503, {"ok": False, "error": f"GitHub unreachable: {exc}"}

        payload = json.dumps(out).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "public, max-age=300")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)
