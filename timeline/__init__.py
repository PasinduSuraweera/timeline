"""timeline: a GitHub contribution calendar, rendered as a wave you can ride."""

from . import band, options, png, render, source, sprites, themes, wave
from .options import Options
from .source import NotFound, Unavailable

__version__ = "1.0.0"

__all__ = ["Options", "NotFound", "Unavailable", "NoData", "generate", "error_svg",
           "band", "options", "png", "render", "source", "sprites", "themes", "wave"]


class NoData(Exception):
    """No calendar, and the caller asked for no stand-in."""


def generate(params, token=None):
    """Render the band for one request.

    Returns (svg, meta). `meta["source"]` is "api" when a token answered,
    "public" when the tokenless fragment did, and "fallback" for the stand-in swell.
    """
    opts = Options(params)
    colours = themes.resolve(opts.theme, opts.bg, opts.accent,
                             opts.hot, opts.glint, opts.line)

    if opts.user_invalid:
        raise NotFound(opts.user_raw)

    values, origin, weeks_used = None, "fallback", 0
    if opts.user:
        try:
            totals, origin = source.cached_weekly_totals(opts.user, token, opts.weeks)
            weeks_used = len(totals)
            values = wave.from_totals(totals, opts.cols, opts.smooth)
        except Unavailable:
            values = None                    # GitHub is having a moment, still draw something
        if values is None:
            origin = "fallback"

    if values is None:
        if opts.fallback == "none":
            raise NoData(opts.user or "no user given")
        values = wave.flat(opts.cols) if opts.fallback == "flat" else wave.sine(opts.cols)

    title = f"{opts.user}'s contribution wave" if opts.user else "Contribution wave"
    svg = render.build(values, opts, colours, title)
    return svg, {"source": origin, "user": opts.user, "weeks": weeks_used,
                 "width": opts.px_width, "height": opts.px_height, "theme": opts.theme}


def error_svg(message, params=None):
    """A quiet still band carrying a short message, for the paths that cannot draw a wave."""
    opts = Options(params or {})
    colours = themes.resolve(opts.theme, opts.bg, opts.accent,
                             opts.hot, opts.glint, opts.line)
    w, h = opts.px_width, min(opts.px_height, 140)
    mid = h // 2
    dash = (f'<line x1="16" y1="{mid + 18}.5" x2="{w - 16}" y2="{mid + 18}.5" '
            f'stroke="{colours["accent"]}" stroke-opacity=".45" stroke-dasharray="3 5"/>')
    # The one place a typeface appears: an error nobody can read is not much of an error.
    text = (f'<text x="{w // 2}" y="{mid}" text-anchor="middle" font-size="13" '
            f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
            f'fill="{colours["hot"]}">{render.esc(message)}</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
            f'<title>{render.esc(message)}</title>'
            f'<rect width="{w}" height="{h}" fill="{colours["bg"]}"/>{dash}{text}</svg>')
