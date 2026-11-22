"""Draw the three pictures for the site's "how a year becomes a wave" steps.

All three come from one sample year, so the calendar, the weekly totals and the
wave agree with each other. Each is 1200x900 (4:3) with its content held in the
middle band, so the 16:9 phone crop never cuts it.

    python3 tools/site_art.py
"""

import math
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from timeline import band, render, themes, wave           # noqa: E402
from timeline.options import Options                      # noqa: E402

OUT = ROOT / "public" / "img"
W, H = 1200, 900
BG = "#071017"
COLOURS = themes.resolve("ember")


def sample_days(seed=11):
    """364 days with a weekday rhythm, a busy spring, a quiet stretch and a late push."""
    rng = random.Random(seed)
    days = []
    for d in range(364):
        week = d // 7
        season = 3.2 + 2.4 * math.sin(week / 52 * 2 * math.pi - 0.8) + (2.2 if 40 <= week <= 47 else 0)
        weekday = 1.0 if d % 7 < 5 else 0.35
        base = max(0.0, season * weekday + rng.gauss(0, 1.3))
        days.append(0 if rng.random() < 0.12 else int(round(base)))
    return days


def frame(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="{BG}"/>{body}</svg>')


def level_colour(level):
    if level == 0:
        return themes.mix(BG, COLOURS["accent"], 0.10)
    return themes.mix(BG, COLOURS["accent"], [0, 0.32, 0.55, 0.78, 1.0][level])


def calendar(days):
    pitch, cell = 20, 15
    cols = len(days) // 7
    x0 = (W - cols * pitch + (pitch - cell)) // 2
    y0 = (H - 7 * pitch) // 2
    top = max(days) or 1
    out = []
    for i, n in enumerate(days):
        c, r = divmod(i, 7)
        level = 0 if n == 0 else min(4, 1 + int(3.999 * n / top))
        out.append(f'<rect x="{x0 + c * pitch}" y="{y0 + r * pitch}" width="{cell}" height="{cell}" '
                   f'rx="2" fill="{level_colour(level)}"/>')
    return frame("".join(out))


def weekly(totals):
    pitch, bar = 20, 13
    x0 = (W - len(totals) * pitch + (pitch - bar)) // 2
    base, tall = 640, 380
    top = max(totals) or 1
    out = [f'<rect x="{x0 - 8}" y="{base}" width="{len(totals) * pitch + 3}" height="2" '
           f'fill="{themes.mix(BG, COLOURS["line"], 1)}"/>']
    for i, t in enumerate(totals):
        h = max(3, round(tall * t / top))
        out.append(f'<rect x="{x0 + i * pitch}" y="{base - h}" width="{bar}" height="{h}" rx="2" '
                   f'fill="{themes.mix(BG, COLOURS["accent"], 0.45 + 0.55 * t / top)}"/>')
    return frame("".join(out))


def wave_still(totals):
    opts = Options({"width": "1040", "height": "320", "cell": "8", "rider_at": "38", "dots": "0"})
    # Drawn on the frame's own colour so the band reads as part of the picture, not a box on it.
    svg = render.build(wave.from_totals(totals, opts.cols), opts, themes.resolve("ember", bg=BG), "A contribution wave")
    # A still for the page: every animation off, so the rider rests where the first frame puts it.
    svg = svg.replace("</style>", "*{animation:none!important}</style>", 1)
    inner = re.sub(r'^<svg[^>]*>', '', svg)[:-len("</svg>")]
    inner = re.sub(r'<title>.*?</title>', '', inner)
    x, y = (W - opts.px_width) // 2, (H - opts.px_height) // 2
    return frame(f'<svg x="{x}" y="{y}" width="{opts.px_width}" height="{opts.px_height}" '
                 f'viewBox="0 0 {opts.px_width} {opts.px_height}">{inner}</svg>')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    days = sample_days()
    totals = [sum(days[i:i + 7]) for i in range(0, len(days), 7)]
    for name, svg in (("step-calendar.svg", calendar(days)),
                      ("step-weeks.svg", weekly(totals)),
                      ("step-wave.svg", wave_still(totals))):
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"{name}: {len(svg) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
