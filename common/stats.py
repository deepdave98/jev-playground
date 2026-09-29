"""The two numbers every week's scorer needs."""

import statistics


def pct(xs, p):
    """Nearest-rank percentile. The sets here are 16 to 60 items, so no interpolation."""
    s = sorted(xs)
    return s[max(0, min(len(s) - 1, round(p / 100 * len(s) + 0.5) - 1))]


def brier(pairs):
    """Mean squared gap between a stated probability and what happened.

    pairs is (probability, outcome). 0 is perfect, 0.25 is a coin flip.
    """
    return statistics.fmean((p - float(y)) ** 2 for p, y in pairs)
