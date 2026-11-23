"""Vercel entry point: GET /api/timeline?user=<login>&... returns an animated SVG."""

import os
import pathlib
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from timeline import NoData, NotFound, error_svg, generate, seen   # noqa: E402

CACHE_SECONDS = int(os.environ.get("TIMELINE_CACHE_SECONDS", "1800"))
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("TIMELINE_GITHUB_TOKEN") or ""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query, keep_blank_values=True)
        params = {k: v[0] for k, v in query.items()}

        status, meta = 200, {}
        try:
            body, meta = generate(params, TOKEN)
        except NotFound:
            status, body = 404, error_svg("no such GitHub user", params)
        except NoData:
            status, body = 404, error_svg("no contribution data", params)
        except Exception:                      # never hand a README a broken image
            status, body = 500, error_svg("could not build the wave", params)

        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        if status == 200:
            self.send_header(
                "Cache-Control",
                f"public, max-age={CACHE_SECONDS}, s-maxage={CACHE_SECONDS}, "
                f"stale-while-revalidate={CACHE_SECONDS * 4}")
        else:
            self.send_header("Cache-Control", "public, max-age=300")
        self.send_header("X-Timeline-Source", str(meta.get("source", "error")))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)
        self.wfile.flush()

        # GitHub's image proxy only asks for images that sit on a GitHub page, so a
        # wave it loads is one someone is wearing. Visitors trying the site don't count.
        if (status == 200 and meta.get("user") and meta.get("source") != "fallback"
                and seen.from_camo(self.headers.get("User-Agent"))):
            seen.record(meta["user"])
