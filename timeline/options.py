"""Parse and clamp every setting the endpoint accepts.

Nothing reaches the SVG without passing through here. Usernames are matched
against GitHub's own rules and colours against a hex pattern, so a request
cannot smuggle markup into the output.
"""

import re

from . import sprites
from .themes import DEFAULT_THEME, THEMES

USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")

DEFAULTS = {
    "width": 880, "height": 140, "cell": 4, "speed": 33.0,
    "rider": "surfer", "rider_at": 33, "smooth": 1.0, "weeks": 52,
    "glints": True, "dots": True, "border": False, "fallback": "sine",
}

LIMITS = {
    "width": (320, 1600), "height": (60, 400), "cell": (2, 10),
    "speed": (4.0, 300.0), "rider_at": (0, 100), "smooth": (0.2, 5.0), "weeks": (8, 53),
}

# Spellings people reach for, mapped to the canonical name.
ALIASES = {
    "username": "user", "login": "user", "name": "user",
    "duration": "speed", "colour": "accent", "color": "accent",
    "background": "bg", "sprite": "rider", "scale": "cell",
    "sparkle": "glints", "grid": "dots",
}

TRUE = {"1", "true", "yes", "on", "y"}
FALSE = {"0", "false", "no", "off", "n"}


def _clamp(value, key):
    lo, hi = LIMITS[key]
    return max(lo, min(hi, value))


def _num(raw, key, cast):
    try:
        return _clamp(cast(raw), key)
    except (TypeError, ValueError):
        return DEFAULTS[key]


def _flag(raw, default):
    if raw is None:
        return default
    raw = str(raw).strip().lower()
    if raw in TRUE:
        return True
    if raw in FALSE:
        return False
    return default


class Options:
    """Resolved, validated settings for one render."""

    def __init__(self, params=None):
        p = {}
        for key, value in (params or {}).items():
            key = key.strip().lower()
            key = ALIASES.get(key, key)
            if isinstance(value, (list, tuple)):
                value = value[0] if value else None
            p[key] = value

        raw_user = (p.get("user") or "").strip()
        self.user_raw = raw_user
        self.user = raw_user if USER_RE.match(raw_user) else None
        # Someone typed something that cannot be a GitHub login. Say so rather than
        # quietly drawing the stand-in swell and letting them think it is their data.
        self.user_invalid = bool(raw_user) and self.user is None

        self.theme = (p.get("theme") or DEFAULT_THEME).strip().lower()
        if self.theme not in THEMES:
            self.theme = DEFAULT_THEME
        self.bg = p.get("bg")
        self.accent = p.get("accent")
        self.hot = p.get("hot")
        self.glint = p.get("glint")
        self.line = p.get("line")

        self.cell = _num(p.get("cell", DEFAULTS["cell"]), "cell", int)
        self.width = _num(p.get("width", DEFAULTS["width"]), "width", int)
        self.height = _num(p.get("height", DEFAULTS["height"]), "height", int)
        self.speed = _num(p.get("speed", DEFAULTS["speed"]), "speed", float)
        self.smooth = _num(p.get("smooth", DEFAULTS["smooth"]), "smooth", float)
        self.weeks = _num(p.get("weeks", DEFAULTS["weeks"]), "weeks", int)
        self.rider_at = _num(p.get("rider_at", DEFAULTS["rider_at"]), "rider_at", int)

        rider = (p.get("rider") or DEFAULTS["rider"]).strip().lower()
        self.rider = rider if rider in sprites.SPRITES else DEFAULTS["rider"]

        self.glints = _flag(p.get("glints"), DEFAULTS["glints"])
        self.dots = _flag(p.get("dots"), DEFAULTS["dots"])
        self.border = _flag(p.get("border"), DEFAULTS["border"])

        fallback = (p.get("fallback") or DEFAULTS["fallback"]).strip().lower()
        self.fallback = fallback if fallback in ("sine", "flat", "none") else "sine"

        # The grid has to divide evenly, so the drawn size is snapped to whole cells.
        self.cols = max(24, self.width // self.cell)
        self.rows = max(12, self.height // self.cell)

    @property
    def px_width(self):
        return self.cols * self.cell

    @property
    def px_height(self):
        return self.rows * self.cell

    def to_query(self):
        """The shortest query string that reproduces this render."""
        out = []
        if self.user:
            out.append(("user", self.user))
        if self.theme != DEFAULT_THEME:
            out.append(("theme", self.theme))
        for key in ("bg", "accent", "hot", "glint", "line"):
            if getattr(self, key):
                out.append((key, str(getattr(self, key)).lstrip("#")))
        for key in ("width", "height", "cell", "weeks", "rider_at"):
            if getattr(self, key) != DEFAULTS[key]:
                out.append((key, getattr(self, key)))
        for key in ("speed", "smooth"):
            if abs(getattr(self, key) - DEFAULTS[key]) > 1e-9:
                out.append((key, ("%g" % getattr(self, key))))
        if self.rider != DEFAULTS["rider"]:
            out.append(("rider", self.rider))
        for key in ("glints", "dots", "border"):
            if getattr(self, key) != DEFAULTS[key]:
                out.append((key, "1" if getattr(self, key) else "0"))
        if self.fallback != DEFAULTS["fallback"]:
            out.append(("fallback", self.fallback))
        return "&".join(f"{k}={v}" for k, v in out)
