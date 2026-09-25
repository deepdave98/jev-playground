"""Runs every configuration over the ledger, one after another.

    python3 src/bench.py                       # all six
    python3 src/bench.py jev jev-per-deal      # just these

Sequential on purpose, same as week 01: run them together and every latency
number measures the queue instead of the model.
"""

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from claude import Claude  # noqa: E402
from jev import Jev, visible  # noqa: E402
from spec import assess  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNS = ["jev", "jev-per-deal", "claude-haiku-4-5", "claude-sonnet-5",
        "claude-sonnet-5-per-deal", "claude-sonnet-5-ledger"]


def load():
    return [json.loads(line) for line in (ROOT / "data" / "ledger.jsonl").open()]


def judged(events, labels):
    return [{**e, **labels[e["id"]]} for e in events]


def run(name, ledger):
    out = ROOT / "results" / "raw" / f"{name}.jsonl"
    meta = {"run": name, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z")}

    if name.startswith("jev"):
        client = Jev()
        client.ask({"warm": True}, {"q": {"type": "noul", "instructions": "Is this a warmup?"}})
    else:
        client = Claude(name.replace("-per-deal", "").replace("-ledger", ""))
        meta["cli_overhead_samples"] = client.calibrate()
        meta["cli_overhead"] = client.overhead
        print(f"[{name}] CLI overhead {client.overhead} tokens, subtracted from every call")

    t0 = time.perf_counter()
    with out.open("w") as fh:
        fh.write(json.dumps({"_meta": meta}) + "\n")
        for i, row in enumerate(ledger, 1):
            deal, events = row["deal"], row["events"]
            # The answer lives next to the deal, never inside it. Everything
            # in `deal` and `seen` goes to a model.
            assert "label" not in deal
            seen = [visible(e) for e in events]
            rec = {"deal": deal["id"], "calls": [], "error": None}
            try:
                if name == "jev":
                    labels = {}
                    for e in events:
                        lab, ms, tok = client.per_event(deal, e)
                        labels[e["id"]] = lab
                        rec["calls"].append({"ms": ms, "in": tok, "out": 0, "usd": tok * 42e-9})
                elif name == "jev-per-deal":
                    labels, ms, tok = client.per_deal(deal, events)
                    rec["calls"].append({"ms": ms, "in": tok, "out": 0, "usd": tok * 42e-9})
                elif name.endswith("-ledger"):
                    verdict, ms, usd, tin, tout = client.ledger(deal, seen)
                    rec["calls"].append({"ms": ms, "in": tin, "out": tout, "usd": usd})
                    rec["p_at_risk"] = verdict["p_at_risk"]
                    rec["reasons"] = sorted(verdict["reasons"])
                    labels = None
                elif name.endswith("-per-deal"):
                    labels, ms, usd, tin, tout = client.per_deal(deal, seen)
                    rec["calls"].append({"ms": ms, "in": tin, "out": tout, "usd": usd})
                else:
                    labels = {}
                    for e in seen:
                        lab, ms, usd, tin, tout = client.per_event(deal, e)
                        labels[e["id"]] = lab
                        rec["calls"].append({"ms": ms, "in": tin, "out": tout, "usd": usd})

                if labels is not None:
                    rec["labels"] = labels
                    rec["reasons"] = sorted(assess(deal, judged(events, labels)))
            except Exception as exc:
                rec["error"] = f"{type(exc).__name__}: {exc}"

            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            if i % 5 == 0 or i == len(ledger):
                print(f"[{name}] {i}/{len(ledger)} deals ({time.perf_counter() - t0:.0f}s)")

    if hasattr(client, "close"):
        client.close()


def main():
    which = sys.argv[1:] or RUNS
    bad = [w for w in which if w not in RUNS]
    if bad:
        sys.exit(f"unknown: {bad}. pick from {RUNS}")
    ledger = load()
    print(f"{len(ledger)} deals, {sum(len(r['events']) for r in ledger)} events\n")
    for name in which:
        run(name, ledger)
        print()


if __name__ == "__main__":
    main()
