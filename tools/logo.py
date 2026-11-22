"""Draws Timeline's logo files: the week wave, seven contribution squares riding one swell.

    python tools/logo.py

writes docs/logo/mark.svg, docs/logo/lockup-dark.svg, docs/logo/lockup-light.svg,
docs/logo/icon.svg, public/favicon.svg, public/share.svg, and, when rsvg-convert is on
the PATH, public/apple-touch-icon.png, docs/logo/icon-512.png and public/share.png.

The wordmark is set in Instrument Sans (public/fonts) and written out as outlines, so
the files look the same wherever they are shown, GitHub included. Needs fontTools,
brotli and uharfbuzz, which only this script uses:

    pip install fonttools brotli uharfbuzz
"""

import io
import math
import os
import shutil
import subprocess
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
import uharfbuzz as hb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from site_art import sample_days    # noqa: E402

FONT = os.path.join(ROOT, "public", "fonts", "instrument-sans.woff2")
LOGO = os.path.join(ROOT, "docs", "logo")
PUBLIC = os.path.join(ROOT, "public")

EMBER = "#ff6a3d"
NIGHT = "#02070a"
INK = "#e6edf2"
MUTED = "#95a2ad"


def num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


# ---------- the mark ----------

def mark_cells(size=24.0, x=0.0, y=0.0):
    """The seven squares on a 24 unit grid, scaled to size and moved to x, y."""
    k = size / 24
    out = []
    for i in range(7):
        top = round((10.75 - 5.25 * math.sin(i / 6 * 2 * math.pi)) * 4) / 4
        out.append((x + (1.5 + i * 3) * k, y + top * k, 2.5 * k, 0.6 * k))
    return out


def rects(cells, fill):
    return "".join(
        f'<rect x="{num(cx)}" y="{num(cy)}" width="{num(s)}" height="{num(s)}" rx="{num(r)}" fill="{fill}"/>'
        for cx, cy, s, r in cells)


def svg(w, h, body, label="Timeline"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{num(w)}" height="{num(h)}" '
            f'viewBox="0 0 {num(w)} {num(h)}" role="img" aria-label="{label}">'
            f'<title>{label}</title>{body}</svg>\n')


# The favicon is its own cut: at 16 pixels seven squares blur, so it keeps five,
# one full swell, each square on whole pixels.
FAVICON = ("".join(f'<rect x="{x}" y="{y}" width="3" height="3" fill="{EMBER}"/>'
                   for x, y in zip([1, 4, 7, 10, 13], [6, 2, 6, 10, 6])))


# ---------- the wordmark, as outlines ----------

class Type:
    def __init__(self, weight=500):
        font = TTFont(FONT)
        self.font = instancer.instantiateVariableFont(font, {"wght": weight, "wdth": 100})
        self.upem = self.font["head"].unitsPerEm
        self.cap = self.font["OS/2"].sCapHeight
        self.glyphs = self.font.getGlyphSet()
        self.order = self.font.getGlyphOrder()
        # HarfBuzz reads plain sfnt, not woff2, so shape with the instance as bytes.
        raw = io.BytesIO()
        self.font.flavor = None
        self.font.save(raw)
        self.hb_font = hb.Font(hb.Face(hb.Blob(raw.getvalue())))

    def path(self, text, px, x, baseline, tracking=-0.02):
        """Outline of text set at px, its baseline at y=baseline.

        Returns (d, width, top): top is the highest point of the ink."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb_font, buf, {"kern": True, "liga": True})
        scale = px / self.upem
        pen = SVGPathPen(self.glyphs)
        bounds = BoundsPen(self.glyphs)
        pen_x = 0.0
        last = len(buf.glyph_infos) - 1
        for n, (info, pos) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
            name = self.order[info.codepoint]
            t = TransformPen(pen, (scale, 0, 0, -scale, x + (pen_x + pos.x_offset) * scale, baseline))
            self.glyphs[name].draw(t)
            self.glyphs[name].draw(TransformPen(bounds, (scale, 0, 0, -scale, x + (pen_x + pos.x_offset) * scale, baseline)))
            pen_x += pos.x_advance
            if n < last:
                pen_x += tracking * self.upem
        top = bounds.bounds[1] if bounds.bounds else baseline
        return pen.getCommands(), pen_x * scale, top


def lockup(type_, px, colour, x=0.0, y=0.0):
    """Mark plus wordmark. The mark sits centred on the capitals. Returns (body, w, h)."""
    cap = type_.cap / type_.upem * px
    # The squares fill 11.5 of the mark's 24 units, so a box this size makes the
    # wave as tall as the capitals.
    msize = cap * 24 / 11.5
    gap = px * 0.2
    # The squares are centred in the mark's box, so centring the capitals on the
    # box lines the wave up with the letters.
    baseline = y + msize / 2 + cap / 2
    d, tw, _ = type_.path("Timeline", px, x + msize + gap, baseline)
    body = rects(mark_cells(msize, x, y), EMBER) + f'<path d="{d}" fill="{colour}"/>'
    return body, msize + gap + tw, msize


def lockup_file(type_, px, colour):
    """The lockup cropped to its ink, so it sits tight in a README or a slide."""
    body, w, h = lockup(type_, px, colour)
    cells = mark_cells(h)
    cap = type_.cap / type_.upem * px
    _, _, text_top = type_.path("Timeline", px, 0, h / 2 + cap / 2)
    top = min(text_top, cells[0][1], min(c[1] for c in cells))
    bottom = max(h / 2 + cap / 2, max(c[1] + c[2] for c in cells))
    left = cells[0][0]
    pad = px * 0.06
    inner = f'<g transform="translate({num(pad - left)} {num(pad - top)})">{body}</g>'
    return svg(w - left + 2 * pad, bottom - top + 2 * pad, inner)


# ---------- the share card ----------

def share_card(type_):
    w, h = 1280, 640
    pad = 96
    body = f'<rect width="{w}" height="{h}" fill="{NIGHT}"/>'
    lk, lw, lh = lockup(type_, 88, INK, pad, 128)
    body += lk
    d, _, _ = type_.path("Your last 52 weeks as a scrolling pixel wave.", 34, pad, 128 + lh + 78, tracking=-0.01)
    body += f'<path d="{d}" fill="{MUTED}"/>'
    # A year of weeks, one square each, riding its own smoothed swell.
    days = sample_days()
    weeks = [sum(days[i:i + 7]) for i in range(0, len(days), 7)][:52]
    soft = []
    for i in range(len(weeks)):
        win = [weeks[(i + j) % len(weeks)] for j in range(-3, 4)]
        soft.append(sum(win) / len(win))
    lo, hi = min(soft), max(soft)
    span = w - 2 * pad
    step = span / len(soft)
    cell = step * 0.72
    band_top, band_bottom = 392, h - pad
    for i, v in enumerate(soft):
        t = (v - lo) / (hi - lo or 1)
        cy = band_bottom - cell - t * (band_bottom - band_top - cell)
        cy = round(cy / 4) * 4
        body += f'<rect x="{num(pad + i * step)}" y="{num(cy)}" width="{num(cell)}" height="{num(cell)}" rx="3" fill="{EMBER}"/>'
    return svg(w, h, body, "Timeline: your last 52 weeks as a scrolling pixel wave")


# ---------- write it all ----------

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def png(src, dst, w, h):
    if not shutil.which("rsvg-convert"):
        print(f"skipped {os.path.relpath(dst, ROOT)}: rsvg-convert is not installed")
        return
    subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), src, "-o", dst], check=True)


def main():
    type_ = Type()

    write(os.path.join(LOGO, "mark.svg"), svg(24, 24, rects(mark_cells(), EMBER)))

    for name, colour in (("lockup-dark.svg", INK), ("lockup-light.svg", NIGHT)):
        write(os.path.join(LOGO, name), lockup_file(type_, 64, colour))

    # A square icon for avatars and app tiles: the mark on the night ground.
    icon = f'<rect width="512" height="512" rx="112" fill="{NIGHT}"/>' + rects(mark_cells(352, 80, 80), EMBER)
    write(os.path.join(LOGO, "icon.svg"), svg(512, 512, icon))

    write(os.path.join(PUBLIC, "favicon.svg"), svg(16, 16, FAVICON))
    write(os.path.join(PUBLIC, "share.svg"), share_card(type_))

    png(os.path.join(LOGO, "icon.svg"), os.path.join(PUBLIC, "apple-touch-icon.png"), 180, 180)
    png(os.path.join(LOGO, "icon.svg"), os.path.join(LOGO, "icon-512.png"), 512, 512)
    png(os.path.join(PUBLIC, "share.svg"), os.path.join(PUBLIC, "share.png"), 1280, 640)
    print("logo files written")


if __name__ == "__main__":
    main()
