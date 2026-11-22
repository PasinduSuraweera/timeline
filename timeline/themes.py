"""Colour presets for the timeline band, plus hex parsing and overrides.

Every value that reaches the SVG passes through `parse_hex`, so a request can
never inject markup through a colour parameter.
"""

import re

_HEX = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

# bg    band background
# accent the body of the wave
# hot    the cap sitting on the ridge
# glint  the sparkle that travels along the crest
# line   the hairline border, when one is drawn
THEMES = {
    "ember":    {"bg": "#02070A", "accent": "#FF6A3D", "hot": "#FF9A58", "glint": "#FFD0AE", "line": "#16232D"},
    "ice":      {"bg": "#02070A", "accent": "#38BDF8", "hot": "#7DD3FC", "glint": "#E0F2FE", "line": "#15242F"},
    "matrix":   {"bg": "#020A06", "accent": "#22C55E", "hot": "#4ADE80", "glint": "#DCFCE7", "line": "#12261A"},
    "grape":    {"bg": "#07040E", "accent": "#A855F7", "hot": "#C084FC", "glint": "#F3E8FF", "line": "#1F1630"},
    "rose":     {"bg": "#0B0409", "accent": "#F43F5E", "hot": "#FB7185", "glint": "#FFE4E8", "line": "#2A121B"},
    "gold":     {"bg": "#0A0702", "accent": "#F59E0B", "hot": "#FBBF24", "glint": "#FEF3C7", "line": "#2A1F08"},
    "mono":     {"bg": "#05070A", "accent": "#94A3B8", "hot": "#CBD5E1", "glint": "#F1F5F9", "line": "#1B2430"},
    "daylight": {"bg": "#FFFFFF", "accent": "#FF6A3D", "hot": "#E2451A", "glint": "#7A2206", "line": "#D8DEE4"},
    "paper":    {"bg": "#F6F8FA", "accent": "#1F6FEB", "hot": "#0B4FC4", "glint": "#07306F", "line": "#D0D7DE"},
}

DEFAULT_THEME = "ember"


def parse_hex(value, default=None):
    """Return a normalised #rrggbb string, or `default` if the input is not a hex colour."""
    if not value:
        return default
    m = _HEX.match(value.strip())
    if not m:
        return default
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return "#" + h.lower()


def to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def mix(a, b, t):
    """Blend two hex colours, t=0 gives a, t=1 gives b."""
    ra, rb = to_rgb(a), to_rgb(b)
    return to_hex(tuple(ra[i] + (rb[i] - ra[i]) * t for i in range(3)))


def luma(h):
    r, g, b = to_rgb(h)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def resolve(theme=None, bg=None, accent=None, hot=None, glint=None, line=None):
    """Pick a preset, then apply any explicit colour overrides.

    Giving only an accent is enough: the cap and the sparkle are derived from it,
    away from whichever background is in play so they stay visible on light themes.
    """
    name = (theme or DEFAULT_THEME).strip().lower()
    base = dict(THEMES.get(name, THEMES[DEFAULT_THEME]))

    bg = parse_hex(bg)
    accent = parse_hex(accent)
    hot = parse_hex(hot)
    glint = parse_hex(glint)
    line = parse_hex(line)

    if bg:
        base["bg"] = bg
    if accent:
        base["accent"] = accent
        if not hot or not glint:
            # On a dark background brighten toward white, on a light one deepen toward black,
            # so a custom accent keeps its ridge readable either way.
            pole = "#000000" if luma(base["bg"]) > 0.5 else "#ffffff"
            base["hot"] = hot or mix(accent, pole, 0.28)
            base["glint"] = glint or mix(accent, pole, 0.62)
        if not line:
            base["line"] = mix(base["bg"], accent, 0.18)
    if hot:
        base["hot"] = hot
    if glint:
        base["glint"] = glint
    if line:
        base["line"] = line
    return base
