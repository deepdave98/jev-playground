"""Scores results/raw/*.jsonl into results/results.json and a printed table.

Metrics:
  per-step accuracy   how often each judgment matched the hand-written key
  route accuracy      how often the whole workflow put the lead in the right
                      queue, which is the only number a GTM team feels
  latency             p50 / p90 / p99 per lead
  cost                dollars per 1,000 leads at published list prices
  Brier + ECE         whether the confidence number means anything

Route is computed with spec.route() from each runner's four judgments, the
same function applied to the answer key. No model is asked to route.
"""

import json
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from spec import route  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "raw"
FIELDS = ["disqualify", "icp_fit", "segment", "intent"]


def pct(xs: list[float], p: float) -> float:
    """Nearest-rank percentile. n=60, so interpolation would be false precision."""
    if not xs:
        return 0.0
    s = sorted(xs)
    k = max(0, min(len(s) - 1, int(round(p / 100 * len(s) + 0.5)) - 1))
    return s[k]


def brier(pairs: list[tuple[float, bool]]) -> float:
    """Mean squared error of the stated probability. Lower is better."""
    return sum((p - (1.0 if y else 0.0)) ** 2 for p, y in pairs) / len(pairs)


def ece(pairs: list[tuple[float, bool]], bins: int = 5) -> float:
    """Expected calibration error: gap between stated confidence and reality."""
    total, n = 0.0, len(pairs)
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        chunk = [(p, y) for p, y in pairs
                 if (lo <= p < hi or (b == bins - 1 and p == 1.0))]
        if not chunk:
            continue
        conf = statistics.fmean(p for p, _ in chunk)
        acc = statistics.fmean(1.0 if y else 0.0 for _, y in chunk)
        total += len(chunk) / n * abs(conf - acc)
    return total


def score_file(path: pathlib.Path) -> dict:
    rows, meta = [], {}
    with path.open() as fh:
        for line in fh:
            d = json.loads(line)
            if "_meta" in d:
                meta = d["_meta"]
            else:
                rows.append(d)

    ok = [r for r in rows if not r.get("error")]
    failed = [r for r in rows if r.get("error")]

    per_field = {}
    for f in FIELDS:
        hits = sum(1 for r in ok if r["prediction"][f] == r["labels"][f])
        per_field[f] = hits / len(ok) if ok else 0.0

    route_hits = sum(1 for r in ok if route(**r["prediction"]) == route(**r["labels"]))
    all_four = sum(1 for r in ok if all(r["prediction"][f] == r["labels"][f] for f in FIELDS))

    lat = [r["latency_ms"] for r in ok]
    usd = [r["billed_usd"] for r in ok]

    # Calibration is only meaningful on the two probability questions.
    cal = {}
    for f in ["disqualify", "icp_fit"]:
        pairs = [(float(r["confidence"][f]), bool(r["labels"][f])) for r in ok]
        cal[f] = ({"brier": brier(pairs), "ece": ece(pairs)} if pairs
                  else {"brier": float("nan"), "ece": float("nan")})

    # The two errors a GTM team actually feels. Accuracy treats every mistake
    # the same; these do not. Binning a funded buyer costs revenue, and handing
    # a competitor a demo costs something worse.
    buyers_binned = sum(1 for r in ok
                        if route(**r["labels"]) == "ae_now"
                        and route(**r["prediction"]) == "reject")
    real_buyers = sum(1 for r in ok if route(**r["labels"]) == "ae_now")
    leaked = sum(1 for r in ok
                 if r["labels"]["disqualify"] and not r["prediction"]["disqualify"])
    should_reject = sum(1 for r in ok if r["labels"]["disqualify"])

    # Confusion detail: which routes the workflow got wrong, and into what.
    confusion: dict[str, dict[str, int]] = {}
    for r in ok:
        t, p = route(**r["labels"]), route(**r["prediction"])
        confusion.setdefault(t, {}).setdefault(p, 0)
        confusion[t][p] += 1

    return {
        "runner": meta.get("runner", path.stem),
        "variant": meta.get("variant", "v1"),
        "meta": meta,
        "n": len(ok),
        "failed": len(failed),
        "accuracy": per_field,
        "all_four_correct": all_four / len(ok) if ok else 0.0,
        "route_accuracy": route_hits / len(ok) if ok else 0.0,
        "latency_ms": {
            "p50": pct(lat, 50), "p90": pct(lat, 90), "p99": pct(lat, 99),
            "mean": statistics.fmean(lat) if lat else 0.0,
        },
        "cost": {
            "usd_per_lead": statistics.fmean(usd) if usd else 0.0,
            "usd_per_1000_leads": (statistics.fmean(usd) if usd else 0.0) * 1000,
            "mean_input_tokens": statistics.fmean(r["input_tokens"] for r in ok) if ok else 0,
            "mean_output_tokens": statistics.fmean(r["output_tokens"] for r in ok) if ok else 0,
        },
        "calibration": cal,
        "buyers_binned": {"n": buyers_binned, "of": real_buyers},
        "competitors_leaked": {"n": leaked, "of": should_reject},
        "route_confusion": confusion,
    }


def main() -> None:
    # step6-emails.jsonl lives here too and has a different shape.
    files = sorted(f for f in RAW.glob("*.jsonl") if not f.stem.startswith("step6"))
    if not files:
        sys.exit(f"no result files in {RAW}. run src/bench.py first.")
    # A run still in flight has a header and no rows yet.
    results = [r for r in (score_file(f) for f in files) if r["n"]]

    out = ROOT / "results" / "results.json"
    out.write_text(json.dumps(results, indent=2))

    for variant in sorted({r["variant"] for r in results}):
        block = sorted((r for r in results if r["variant"] == variant),
                       key=lambda r: (r["runner"] != "jev", r["runner"]))
        title = {"v1": "Round 1: competitors not named",
                 "v2": "Round 2: competitor set named in the prompt"}.get(variant, variant)
        w = 18
        print(f"\n{title}")
        print(f"{'':<24}" + "".join(f"{r['runner']:>{w}}" for r in block))
        print("-" * (24 + w * len(block)))

        def row(label, fn, block=block, w=w):
            print(f"{label:<24}" + "".join(f"{fn(r):>{w}}" for r in block))

        for f in FIELDS:
            row(f"accuracy: {f}", lambda r, f=f: f"{r['accuracy'][f]*100:.1f}%")
        row("all four correct", lambda r: f"{r['all_four_correct']*100:.1f}%")
        row("ROUTE ACCURACY", lambda r: f"{r['route_accuracy']*100:.1f}%")
        print()
        row("funded buyers binned",
            lambda r: f"{r['buyers_binned']['n']}/{r['buyers_binned']['of']}")
        row("disqualified leaked",
            lambda r: f"{r['competitors_leaked']['n']}/{r['competitors_leaked']['of']}")
        print()
        for k in ["p50", "p90", "p99"]:
            row(f"latency {k} (ms)", lambda r, k=k: f"{r['latency_ms'][k]:.0f}")
        print()
        row("$ / 1000 leads", lambda r: f"${r['cost']['usd_per_1000_leads']:.3f}")
        row("mean input tokens", lambda r: f"{r['cost']['mean_input_tokens']:.0f}")
        row("mean output tokens", lambda r: f"{r['cost']['mean_output_tokens']:.0f}")
        print()
        for f in ["disqualify", "icp_fit"]:
            row(f"Brier: {f}", lambda r, f=f: f"{r['calibration'][f]['brier']:.4f}")
            row(f"ECE: {f}", lambda r, f=f: f"{r['calibration'][f]['ece']:.4f}")
        print()
        row("failed calls", lambda r: str(r["failed"]))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
