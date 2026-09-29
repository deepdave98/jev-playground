"""Scores results/raw/*.jsonl against the hand labels.

    python3 src/score.py

Overstating an element is the error that matters here. A field marked
established that wasn't makes a deal look more qualified than it is, and if
it's one of the three the forecast rule needs, the deal gets committed.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT / "src"))
from common.bench import load  # noqa: E402
from common.jev import SCORE_BIAS  # noqa: E402
from common.stats import pct  # noqa: E402
from spec import ELEMENTS, LEVEL_NAMES, forecast_ready  # noqa: E402

ORDER = ["jev", "jev-corrected", "claude-haiku-4-5", "claude-sonnet-5"]
# jev-corrected isn't a separate run. It's Jev's own raw scores with
# SCORE_BIAS, measured on weeks 01 to 03, taken off before rounding.
SOURCE = {"jev-corrected": "jev"}


def rank(level):
    return LEVEL_NAMES.index(level)


def corrected(cards):
    top = len(LEVEL_NAMES) - 1
    return {i: {e: LEVEL_NAMES[max(0, min(top, round(c[e + "_score"] - SCORE_BIAS)))] for e in ELEMENTS}
            for i, c in cards.items()}


def score(name, truth):
    cards, calls, failed = load(ROOT / "results/raw" / f"{SOURCE.get(name, name)}.jsonl")
    if name == "jev-corrected":
        cards = corrected(cards)
    ids = [i for i in truth if i in cards]
    pairs = [(rank(cards[i][e]), rank(truth[i][e]), e) for i in ids for e in ELEMENTS]

    per_element = {e: sum(g == w for g, w, x in pairs if x == e) / len(ids) for e in ELEMENTS}
    return {
        "run": name, "calls": len(ids), "failed": len(failed),
        "false_commits": sum(forecast_ready(cards[i]) and not forecast_ready(truth[i]) for i in ids),
        "missed_commits": sum(forecast_ready(truth[i]) and not forecast_ready(cards[i]) for i in ids),
        "ready": sum(forecast_ready(truth[i]) for i in ids),
        "exact": sum(g == w for g, w, _ in pairs) / len(pairs),
        "near": sum(abs(g - w) <= 1 for g, w, _ in pairs) / len(pairs),
        "over": sum(g > w for g, w, _ in pairs),
        "under": sum(g < w for g, w, _ in pairs),
        "per_element": per_element,
        "requests": len(calls),
        "ms_p50": pct([c["ms"] for c in calls], 50),
        "ms_p90": pct([c["ms"] for c in calls], 90),
        "usd_per_1000": sum(c["usd"] for c in calls) / len(ids) * 1000,
        "tokens_per_call": sum(c["in"] for c in calls) / len(ids),
    }


def main():
    truth = {}
    for line in (ROOT / "data/calls.jsonl").open():
        r = json.loads(line)
        truth[r["id"]] = r["label"]

    have = [n for n in ORDER if (ROOT / "results/raw" / f"{SOURCE.get(n, n)}.jsonl").exists()]
    if not have:
        sys.exit("nothing in results/raw yet, run src/bench.py")
    results = [score(n, truth) for n in have]
    (ROOT / "results/results.json").write_text(json.dumps(results, indent=2))

    for r in results:
        if r["calls"] + r["failed"] < len(truth):
            r["run"] += f" (partial {r['calls']}/{len(truth)})"

    w = 20
    print(f"{'':30}" + "".join(f"{r['run'][:w - 1]:>{w}}" for r in results))

    def row(label, f):
        print(f"{label:30}" + "".join(f"{f(r):>{w}}" for r in results))

    row("put in forecast, shouldn't be", lambda r: f"{r['false_commits']}")
    row("left out, should be in", lambda r: f"{r['missed_commits']} of {r['ready']}")
    row("elements, exact", lambda r: f"{r['exact'] * 100:.1f}%")
    row("elements, within one", lambda r: f"{r['near'] * 100:.1f}%")
    row("overstated / understated", lambda r: f"{r['over']} / {r['under']}")
    print()
    for e in ELEMENTS:
        row(f"  {e}", lambda r, e=e: f"{r['per_element'][e] * 100:.0f}%")
    print()
    row("ms per call, p50", lambda r: f"{r['ms_p50']:,.0f}")
    row("ms per call, p90", lambda r: f"{r['ms_p90']:,.0f}")
    row("$ per 1,000 calls", lambda r: f"${r['usd_per_1000']:.3f}")
    row("input tokens per call", lambda r: f"{r['tokens_per_call']:.0f}")
    row("failed", lambda r: f"{r['failed']}")


if __name__ == "__main__":
    main()
