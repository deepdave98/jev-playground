"""Score saved reply classifications and routing decisions."""

import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT / "src"))
from common.bench import load  # noqa: E402
from common.jev import levels  # noqa: E402
from common.stats import brier, pct  # noqa: E402
from spec import QUESTIONS, route  # noqa: E402

ORDER = ["jev", "jev-batched", "claude-haiku-4-5", "claude-sonnet-5"]
WANTS_US = {"book_meeting", "send_info"}
INTENT = levels(QUESTIONS["meeting_intent"])


def routed(label):
    return route(label["category"], label["opt_out"] >= 0.5 if isinstance(label["opt_out"], float)
                 else label["opt_out"], label["meeting_intent"])


def score(name, truth):
    labels, calls, failed = load(ROOT / "results/raw" / f"{name}.jsonl")
    ids = [i for i in truth if i in labels]
    n = len(ids)

    got_route = {i: routed(labels[i]) for i in ids}
    want_route = {i: routed(truth[i]) for i in ids}
    opt_in = [i for i in ids if truth[i]["opt_out"]]
    keen = [i for i in ids if want_route[i] in WANTS_US]

    drift = Counter()
    for i in ids:
        a, b = INTENT.index(labels[i]["meeting_intent"]), INTENT.index(truth[i]["meeting_intent"])
        if a != b:
            drift["high" if a > b else "low"] += 1

    return {
        "run": name, "replies": n, "failed": len(failed),
        "opt_outs_missed": sum(got_route[i] != "suppress" for i in opt_in),
        "opt_outs": len(opt_in),
        "false_opt_outs": sum(labels[i]["opt_out"] >= 0.5 for i in ids if not truth[i]["opt_out"]),
        "interested_lost": sum(got_route[i] not in WANTS_US | {"review"} for i in keen),
        "to_review": sum(got_route[i] == "review" for i in ids),
        "interested": len(keen),
        "route": sum(got_route[i] == want_route[i] for i in ids) / n,
        "category": sum(labels[i]["category"] == truth[i]["category"] for i in ids) / n,
        "opt_out": sum((labels[i]["opt_out"] >= 0.5) == truth[i]["opt_out"] for i in ids) / n,
        "intent": sum(labels[i]["meeting_intent"] == truth[i]["meeting_intent"] for i in ids) / n,
        "intent_near": sum(abs(INTENT.index(labels[i]["meeting_intent"])
                               - INTENT.index(truth[i]["meeting_intent"])) <= 1 for i in ids) / n,
        "intent_high": drift["high"], "intent_low": drift["low"],
        "brier_opt_out": brier([(labels[i]["opt_out"], truth[i]["opt_out"]) for i in ids]),
        "requests": len(calls),
        "ms_p50": pct([c["ms"] for c in calls], 50),
        "ms_p90": pct([c["ms"] for c in calls], 90),
        "seconds_all": sum(c["ms"] for c in calls) / 1000,
        "usd_per_1000": sum(c["usd"] for c in calls) / n * 1000,
        "tokens_per_reply": sum(c["in"] for c in calls) / n,
    }


def main():
    truth = {}
    for line in (ROOT / "data/replies.jsonl").open():
        r = json.loads(line)
        truth[r["id"]] = r["label"]

    have = [n for n in ORDER if (ROOT / "results/raw" / f"{n}.jsonl").exists()]
    if not have:
        sys.exit("nothing in results/raw yet, run src/bench.py")
    results = [score(n, truth) for n in have]
    (ROOT / "results/results.json").write_text(json.dumps(results, indent=2))

    for r in results:
        if r["replies"] + r["failed"] < len(truth):
            r["run"] += f" (partial {r['replies']}/{len(truth)})"

    w = 22
    print(f"{'':28}" + "".join(f"{r['run'][:w - 1]:>{w}}" for r in results))

    def row(label, f):
        print(f"{label:28}" + "".join(f"{f(r):>{w}}" for r in results))

    row("opt-outs still emailed", lambda r: f"{r['opt_outs_missed']} of {r['opt_outs']}")
    row("suppressed, never asked", lambda r: f"{r['false_opt_outs']}")
    row("interested, routed away", lambda r: f"{r['interested_lost']} of {r['interested']}")
    row("sent to a person", lambda r: f"{r['to_review']}")
    row("route", lambda r: f"{r['route'] * 100:.1f}%")
    print()
    row("category", lambda r: f"{r['category'] * 100:.1f}%")
    row("opt_out", lambda r: f"{r['opt_out'] * 100:.1f}%")
    row("meeting_intent, exact", lambda r: f"{r['intent'] * 100:.1f}%")
    row("meeting_intent, within one", lambda r: f"{r['intent_near'] * 100:.1f}%")
    row("intent misses high / low", lambda r: f"{r['intent_high']} / {r['intent_low']}")
    row("Brier, opt_out", lambda r: f"{r['brier_opt_out']:.3f}")
    print()
    row("requests", lambda r: f"{r['requests']}")
    row("ms per request, p50", lambda r: f"{r['ms_p50']:,.0f}")
    row("ms per request, p90", lambda r: f"{r['ms_p90']:,.0f}")
    row("all 60, sequential", lambda r: f"{r['seconds_all']:.1f} s")
    row("$ per 1,000 replies", lambda r: f"${r['usd_per_1000']:.3f}")
    row("input tokens per reply", lambda r: f"{r['tokens_per_reply']:.0f}")
    row("failed", lambda r: f"{r['failed']}")


if __name__ == "__main__":
    main()
