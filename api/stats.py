"""GET /api/stats -> {"stars": n, "users": [{"login", "avatar"}] | null, "count": n | null}.

The site reads this for the star count in the nav and the row of people using the
wave: everyone GitHub has loaded a wave for lately (timeline/seen.py), plus anyone
code search finds. The CDN keeps each answer for five minutes, so someone new shows up within a few.
"""

import json
import os
import pathlib
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from timeline import seen, usage   # noqa: E402

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("TIMELINE_GITHUB_TOKEN") or ""
CACHE_SECONDS = 300


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        people = usage.merge(seen.recent(), usage.users(TOKEN))
        out = {"ok": True, "stars": usage.stars(TOKEN), "users": people,
               "count": None if people is None else len(people)}

        payload = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", f"public, max-age=60, s-maxage={CACHE_SECONDS}, "
                                          f"stale-while-revalidate={CACHE_SECONDS}")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)
