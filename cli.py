#!/usr/bin/env python3
"""Render a contribution wave to an SVG file.

    python3 cli.py --user octocat --out assets/timeline.svg --theme ice

Set GITHUB_TOKEN for exact daily counts. Without it the public calendar is read
instead, which needs no credentials. Every flag maps to the same setting the HTTP
endpoint accepts, and is validated and clamped by the same code.
"""

import argparse
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from timeline import NoData, NotFound, generate   # noqa: E402

PARAMS = ["theme", "bg", "accent", "hot", "glint", "line", "width", "height",
          "cell", "speed", "smooth", "weeks", "rider", "rider_at",
          "glints", "dots", "border", "fallback"]


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Render a GitHub contribution calendar as an animated wave.")
    ap.add_argument("--user", required=True, help="GitHub username")
    ap.add_argument("--out", default="assets/timeline.svg", help="where to write the SVG")
    ap.add_argument("--token", default="", help="GitHub token (defaults to $GITHUB_TOKEN)")
    ap.add_argument("--strict", action="store_true",
                    help="fail instead of drawing the stand-in swell")
    for key in PARAMS:
        ap.add_argument("--" + key, default="", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    # Empty strings mean "not set", so the Action can pass every input unconditionally.
    params = {k: getattr(args, k) for k in PARAMS if str(getattr(args, k)).strip()}
    params["user"] = args.user
    if args.strict:
        params["fallback"] = "none"

    token = args.token.strip() or os.environ.get("GITHUB_TOKEN", "")

    try:
        svg, meta = generate(params, token)
    except NotFound:
        sys.exit(f"no GitHub user called {args.user}")
    except NoData:
        sys.exit(f"no usable contribution data for {args.user}")

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"{out}: {len(svg) / 1024:.1f} KB, {meta['weeks']} weeks via {meta['source']}, "
          f"{meta['width']}x{meta['height']}")
    if meta["source"] == "fallback":
        print("note: drew the stand-in swell, the calendar could not be read")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
