"""Scores results/raw/*.jsonl against the hand labels.

    python3 src/score.py

Deal level, for every run:
  at-risk deals caught, false alarms, and the ARR sitting in missed deals,
  which is the number a revenue leader actually cares about.
Event level, for runs that label events:
  signal, severity and exec_engaged accuracy, plus the Brier score on
  exec_engaged, which is the probability the no_exec_30d rule leans on.
"""

import json
import pathlib
import statistics
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ORDER = ["jev", "jev-per-deal", "claude-haiku-4-5", "claude-sonnet-5",
         "claude-sonnet-5-per-deal", "claude-sonnet-5-ledger"]


def pct(xs, p):
    s = sorted(xs)
    return s[max(0, min(len(s) - 1, round(p / 100 * len(s) + 0.5) - 1))]


def score(name, truth, events_by_id):
    lines = [json.loads(l) for l in (ROOT / "results/raw" / f"{name}.jsonl").open()]
    recs = [r for r in lines if "_meta" not in r]
    ok = [r for r in recs if not r["error"]]

    caught = missed = alarms = right_reasons = 0
    missed_arr = 0
    for r in ok:
        t = truth[r["deal"]]
        said = r["p_at_risk"] >= 0.5 if "p_at_risk" in r else bool(r["reasons"])
        if t["at_risk"] and said:
            caught += 1
            right_reasons += sorted(r["reasons"]) == sorted(t["reasons"])
        elif t["at_risk"]:
            missed += 1
            missed_arr += t["arr"]
        elif said:
            alarms += 1

    calls = [c for r in ok for c in r["calls"]]
    deal_ms = [sum(c["ms"] for c in r["calls"]) for r in ok]
    out = {
        "run": name, "deals": len(ok), "failed": len(recs) - len(ok),
        "caught": caught, "missed": missed, "false_alarms": alarms,
        "missed_arr": missed_arr, "reasons_exact": right_reasons,
        "deal_accuracy": (caught + len(ok) - sum(truth[r["deal"]]["at_risk"] for r in ok) - alarms) / len(ok),
        "calls": len(calls),
        "ms_per_call_p50": pct([c["ms"] for c in calls], 50),
        "ms_per_call_p90": pct([c["ms"] for c in calls], 90),
        "ms_per_deal_p50": pct(deal_ms, 50),
        "ms_all_deals": sum(deal_ms),
        "usd_total": sum(c["usd"] for c in calls),
        "tokens_in_per_event": sum(c["in"] for c in calls) / len(events_by_id),
    }

    if all("labels" in r for r in ok):
        n = sig = sev = sev_near = ex = 0
        brier = []
        sevs = ["none", "watch", "serious", "critical"]
        for r in ok:
            for eid, got in r["labels"].items():
                want = events_by_id[eid]["label"]
                n += 1
                sig += got["signal"] == want["signal"]
                sev += got["severity"] == want["severity"]
                sev_near += abs(sevs.index(got["severity"]) - sevs.index(want["severity"])) <= 1
                ex += got["exec_engaged"] == want["exec_engaged"]
                brier.append((got["p_exec"] - want["exec_engaged"]) ** 2)
        out.update(events=n, signal=sig / n, severity=sev / n, severity_within_one=sev_near / n,
                   exec_engaged=ex / n, brier_exec=statistics.fmean(brier))
    return out


def main():
    ledger = [json.loads(l) for l in (ROOT / "data/ledger.jsonl").open()]
    truth = {row["deal"]["id"]: {**row["label"], "arr": row["deal"]["arr"]} for row in ledger}
    events = {e["id"]: e for row in ledger for e in row["events"]}
    at_risk = sum(t["at_risk"] for t in truth.values())

    have = [n for n in ORDER if (ROOT / "results/raw" / f"{n}.jsonl").exists()]
    if not have:
        sys.exit("nothing in results/raw yet, run src/bench.py")
    results = [score(n, truth, events) for n in have]
    (ROOT / "results/results.json").write_text(json.dumps(results, indent=2))

    # A run still in flight scores as if it were finished. Week 01 nearly
    # published one of those, so say so in the header instead.
    for r in results:
        if r["deals"] + r["failed"] < len(truth):
            r["run"] = f"{r['run']} (partial {r['deals']}/{len(truth)})"

    w = 26
    print(f"{'':30}" + "".join(f"{r['run'][:w - 2]:>{w}}" for r in results))

    def row(label, f):
        print(f"{label:30}" + "".join(f"{f(r):>{w}}" for r in results))

    row(f"at-risk deals caught (of {at_risk})", lambda r: f"{r['caught']}")
    row("false alarms (of 12 healthy)", lambda r: f"{r['false_alarms']}")
    row("ARR in missed deals", lambda r: f"${r['missed_arr']:,}")
    row("reasons exactly right", lambda r: f"{r['reasons_exact']} of {r['caught']}")
    row("deal accuracy", lambda r: f"{r['deal_accuracy'] * 100:.0f}%")
    print()
    row("calls", lambda r: f"{r['calls']}")
    row("ms per call, p50", lambda r: f"{r['ms_per_call_p50']:,.0f}")
    row("ms per deal, p50", lambda r: f"{r['ms_per_deal_p50']:,.0f}")
    row("all 20 deals, sequential", lambda r: f"{r['ms_all_deals'] / 1000:.1f} s")
    row("cost, whole ledger", lambda r: f"${r['usd_total']:.4f}")
    row("input tokens per event", lambda r: f"{r['tokens_in_per_event']:.0f}")
    print()
    row("signal", lambda r: f"{r['signal'] * 100:.1f}%" if "signal" in r else "-")
    row("severity, exact", lambda r: f"{r['severity'] * 100:.1f}%" if "severity" in r else "-")
    row("severity, within one level", lambda r: f"{r['severity_within_one'] * 100:.1f}%" if "severity" in r else "-")
    row("exec_engaged", lambda r: f"{r['exec_engaged'] * 100:.1f}%" if "exec_engaged" in r else "-")
    row("Brier, exec_engaged", lambda r: f"{r['brier_exec']:.3f}" if "brier_exec" in r else "-")
    row("failed", lambda r: f"{r['failed']}")


if __name__ == "__main__":
    main()
