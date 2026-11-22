"""Assemble the finished SVG: a scrolling band, a travelling sparkle, a rider."""

from . import band, sprites

GLINT_PHASES = 22
GLINT_SECONDS = 5.5


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _glints(cores, cols, cell, colour):
    """Sparkles that run along the ridge, lit in waves so the crest looks alive."""
    block = max(1, cell - 1)
    buckets = [[] for _ in range(GLINT_PHASES)]
    for c, core in enumerate(cores):
        phase = min(GLINT_PHASES - 1, (c * GLINT_PHASES) // cols)
        y = core * cell
        for rep in (0, 1):
            buckets[phase].append(
                f'<rect x="{(c + rep * cols) * cell}" y="{y}" width="{block}" height="{block}"/>')
    step = GLINT_SECONDS / GLINT_PHASES
    out = []
    for i, rects in enumerate(buckets):
        if not rects:
            continue
        delay = ("%.2f" % (i * step)).rstrip("0").rstrip(".")
        out.append(f'<g class="gl" fill="{colour}" style="animation-delay:{delay}s">'
                   f'{"".join(rects)}</g>')
    return "".join(out)


def _rider(cores, cols, cell, spec, colours, at_percent, speed):
    """Hold the figure at a fixed x and step it up and down as the swell passes under.

    The band scrolls, so the ridge row beneath the figure changes over the loop.
    One keyframe is emitted per change, with a stepped easing: the rider lands on
    whole pixels rather than sliding between them, which keeps the pixel art crisp.
    """
    cells = spec["cells"]
    if not cells:
        return "", ""
    board_row = spec["board_row"]
    sprite_w = max(c for c, _, _ in cells) + 1
    left = max(0, min(cols - sprite_w, int(cols * at_percent / 100)))
    contact = (left + sprite_w // 2) % cols
    n = len(cores)

    def y_of(core):
        return (core - 1 - board_row) * cell

    y0 = y_of(cores[contact])
    frames = ["0%%{transform:translateY(%dpx)}" % y0]
    i = 0
    while i < n:
        here = y_of(cores[(contact + i) % n])
        j = i + 1
        while j < n and y_of(cores[(contact + j) % n]) == here:
            j += 1
        if j < n:
            frames.append("%.4f%%{transform:translateY(%dpx)}" % (100 * j / n, y_of(cores[(contact + j) % n])))
        i = j
    frames.append("100%%{transform:translateY(%dpx)}" % y0)

    css = ("@keyframes bob{%s}.rd{transform:translateY(%dpx);animation:bob %gs steps(1,end) infinite}"
           % ("".join(frames), y0, speed))
    block = max(1, cell - 1)
    rects = "".join(
        f'<rect x="{(left + c) * cell}" y="{r * cell}" width="{block}" height="{block}" '
        f'fill="{colours[role]}"/>' for c, r, role in cells)
    return css, f'<g class="rd">{rects}</g>'


def build(wave_values, opts, colours, title=None):
    cols, rows, cell = opts.cols, opts.rows, opts.cell
    width, height = opts.px_width, opts.px_height
    floor = 0.07 if opts.dots else 0.0

    field, cores = band.intensity(wave_values, rows, floor=floor)
    href = band.data_uri(band.render_png(field, cols, rows, cell, colours, floor=floor))

    glints = _glints(cores, cols, cell, colours["glint"]) if opts.glints else ""
    rider_css, rider = _rider(cores, cols, cell, sprites.get(opts.rider),
                              colours, opts.rider_at, opts.speed)

    css = [
        "@keyframes tape{from{transform:translateX(0)}to{transform:translateX(-%dpx)}}" % width,
        ".tape{animation:tape %gs steps(%d,end) infinite}" % (opts.speed, width),
        "image{image-rendering:pixelated}",
    ]
    if glints:
        css.append("@keyframes gleam{0%{opacity:0}3%{opacity:1}16%{opacity:1}30%{opacity:0}100%{opacity:0}}")
        css.append(".gl{opacity:0;animation:gleam %gs linear infinite}" % GLINT_SECONDS)
    if rider_css:
        css.append(rider_css)
    # Anyone who asks their system to calm animation gets a still frame instead.
    css.append("@media(prefers-reduced-motion:reduce){.tape,.gl,.rd{animation:none}}")
    # A page can ask for the still frame outright, for a pause button or a print.
    if opts.still:
        css.append(".tape,.gl,.rd{animation:none!important}")

    body = [
        f'<rect width="{width}" height="{height}" fill="{colours["bg"]}"/>',
        f'<svg x="0" y="0" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<g class="tape"><image width="{width * 2}" height="{height}" href="{href}" '
        f'xlink:href="{href}"/>{glints}</g>{rider}</svg>',
    ]
    if opts.border:
        body.append(f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" '
                    f'fill="none" stroke="{colours["line"]}"/>')

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">'
        f'<title>{esc(title or "Contribution wave")}</title>'
        f'<style>{"".join(css)}</style>{"".join(body)}</svg>'
    )
