"""The scrolling band itself: wave to intensity field to a dot-matrix PNG."""

import base64
import math

from . import png
from .themes import to_rgb

# Geometry constants carried over from the original header, expressed as
# fractions of the row count so the band scales with any height.
BASELINE = 22 / 35      # where a trough sits
AMPLITUDE = 15 / 35     # how far a crest climbs above it

LEVELS = 48             # quantisation steps between background and accent


def intensity(wave, rows, floor=0.07):
    """Light each cell of the grid according to its distance from the water line.

    Returns the field plus the integer ridge row per column, which the sparkle
    layer and the rider both ride on.
    """
    cols = len(wave)
    baseline = rows * BASELINE
    amp = rows * AMPLITUDE
    field = [[0.0] * cols for _ in range(rows)]
    cores = []
    for c in range(cols):
        lr = baseline - wave[c] * amp
        core = int(round(lr))
        cores.append(core)
        for r in range(rows):
            d = r - lr
            if abs(d) < 0.8:
                v = 1.35 if r == core else 1.0          # a hotter cap on the ridge itself
            elif -1.7 < d < -0.8:
                v = 0.34                                # one cell of ember haze above
            elif d >= 0.8 and r < rows - 1:
                v = 0.56 * math.exp(-(d - 0.8) / 3.5)   # the body falling away beneath
            else:
                v = 0.0
            field[r][c] = v if v > floor else floor
    return field, cores


def render_png(field, cols, rows, cell, colors, floor=0.07):
    """Draw the field twice side by side, so translating by one width loops seamlessly."""
    bg, acc, hot = to_rgb(colors["bg"]), to_rgb(colors["accent"]), to_rgb(colors["hot"])
    palette = [bg]
    for i in range(1, LEVELS + 1):
        v = i / LEVELS
        palette.append(tuple(round(bg[k] + (acc[k] - bg[k]) * v) for k in range(3)))
    palette.append(hot)
    hot_index = LEVELS + 1

    width, height = cols * cell * 2, rows * cell
    block = max(1, cell - 1)
    rows_px = [bytearray(width) for _ in range(height)]

    for r in range(rows):
        band_rows = rows_px[r * cell:r * cell + block]
        for c in range(cols):
            v = field[r][c]
            if v <= 0:
                continue
            idx = hot_index if v > 1 else max(1, min(LEVELS, int(round(v * LEVELS))))
            run = bytes([idx]) * block
            for rep in (0, cols):
                x0 = (c + rep) * cell
                for line in band_rows:
                    line[x0:x0 + block] = run

    return png.encode_indexed(rows_px, palette, width, height)


def data_uri(raw):
    return "data:image/png;base64," + base64.b64encode(raw).decode()
