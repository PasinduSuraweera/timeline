"""Draws the pictures in the README from one sample year, so they never depend on
anyone's live calendar.

    python tools/readme_art.py

writes docs/banner-dark.svg, docs/banner-light.svg, one docs/themes/<theme>.svg per
theme and one docs/riders/<rider>.svg per rider. They animate as the real thing does.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from timeline import render, themes, wave          # noqa: E402
from timeline.options import Options                # noqa: E402
from site_art import sample_days                    # noqa: E402

DOCS = os.path.join(ROOT, "docs")
THEMES = ["ember", "ice", "matrix", "grape", "rose", "gold", "mono", "daylight", "paper"]
RIDERS = ["surfer", "sail", "buoy", "flag", "none"]


def year():
    days = sample_days()
    return [sum(days[i:i + 7]) for i in range(0, len(days), 7)]


def draw(totals, params, title):
    opts = Options(params)
    colours = themes.resolve(opts.theme, bg=opts.bg, accent=opts.accent, hot=opts.hot, glint=opts.glint, line=opts.line)
    return render.build(wave.from_totals(totals, opts.cols, opts.smooth), opts, colours, title)


def write(path, svg):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("wrote", os.path.relpath(path, ROOT))


def main():
    totals = year()
    banner = {"width": "1200", "height": "180", "cell": "6", "rider_at": "30"}
    write(os.path.join(DOCS, "banner-dark.svg"), draw(totals, dict(banner, theme="ember"), "Timeline"))
    write(os.path.join(DOCS, "banner-light.svg"), draw(totals, dict(banner, theme="daylight"), "Timeline"))
    for t in THEMES:
        write(os.path.join(DOCS, "themes", t + ".svg"),
              draw(totals, {"theme": t, "width": "420", "height": "90", "cell": "4"}, f"The {t} theme"))
    for r in RIDERS:
        write(os.path.join(DOCS, "riders", r + ".svg"),
              draw(totals, {"rider": r, "width": "260", "height": "90", "cell": "4", "rider_at": "45"},
                   f"The {r} rider"))


if __name__ == "__main__":
    main()
