"""Turn a year of weekly contribution totals into a seamless, loopable wave.

A faithful port of the numpy version, written against the standard library only
so the whole renderer cold-starts in a few milliseconds.
"""

import math

MIN_WEEKS = 8


def seam_blend(totals):
    """Pull both ends of the year toward a shared value so the loop has no visible seam.

    The band scrolls forever, which means the last week sits next to the first. Without
    this the join shows up as a step in the water.
    """
    y = [float(v) for v in totals]
    n = len(y)
    win = min(5, n // 5)
    if win < 1:
        return y
    target = 0.5 * (y[0] + y[-1])
    for i in range(win):
        ramp = 0.5 * (1 - math.cos(math.pi * i / (win - 1))) if win > 1 else 0.0
        pull = 1 - ramp
        y[i] = y[i] * (1 - pull) + target * pull
    for i in range(win):
        # The tail uses the same curve reversed, so the final week lands on the target.
        ramp = 0.5 * (1 - math.cos(math.pi * (win - 1 - i) / (win - 1))) if win > 1 else 0.0
        pull = 1 - ramp
        j = n - win + i
        y[j] = y[j] * (1 - pull) + target * pull
    return y


def resample_loop(values, cols):
    """Stretch `values` across `cols` samples, wrapping back to the first value at the end."""
    n = len(values)
    closed = list(values) + [values[0]]
    out = []
    for i in range(cols):
        p = i * n / cols
        k = int(p)
        f = p - k
        out.append(closed[k] + f * (closed[k + 1] - closed[k]))
    return out


def smooth_loop(values, sigma):
    """Circular Gaussian blur, so week-to-week spikes read as swell rather than noise."""
    cols = len(values)
    radius = max(1, int(round(sigma * 3)))
    kernel = [math.exp(-0.5 * (x / sigma) ** 2) for x in range(-radius, radius + 1)]
    total = sum(kernel)
    kernel = [k / total for k in kernel]
    out = []
    for i in range(cols):
        acc = 0.0
        for j, k in enumerate(kernel):
            acc += values[(i + j - radius) % cols] * k
        out.append(acc)
    return out


def normalise(values):
    lo, hi = min(values), max(values)
    span = hi - lo
    if span < 1e-9:
        return None
    return [(v - lo) / span for v in values]


def from_totals(totals, cols, smooth=1.0):
    """Build a 0..1 wave from weekly totals, or None when the data cannot carry one."""
    if not totals or len(totals) < MIN_WEEKS:
        return None
    if max(totals) - min(totals) < 1:
        return None
    y = seam_blend(totals)
    sampled = resample_loop(y, cols)
    sigma = max(0.6, cols / len(y) * 1.8 * max(0.1, smooth))
    return normalise(smooth_loop(sampled, sigma))


def sine(cols):
    """The stand-in swell used when there is no usable calendar."""
    out = []
    for x in range(cols):
        t = 2 * math.pi * x / cols
        out.append(math.sin(2 * t + 0.4) + 0.36 * math.sin(t) + 0.16 * math.sin(3 * t + 2.1))
    return normalise(out)


def flat(cols):
    return [0.5] * cols
