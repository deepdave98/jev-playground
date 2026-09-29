"""Scores results/raw/*.jsonl against the hand labels.

    python3 src/score.py

A wrong merge costs the most. Two companies collapse into one
record, and their contacts, deals and history go with it. A missed
duplicate only means two records live on for a while.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT / "src"))
from common.bench import load  # noqa: E402
from common.stats import brier, pct  # noqa: E402
from spec import action  # noqa: E402

ORDER = ["jev", "claude-haiku-4-5", "claude-sonnet-5", "claude-sonnet-5-thinking"]


def score(name, truth):
    labels, calls, failed = load(ROOT / "results/raw" / f"{name}.jsonl")
    ids = [i for i in truth if i in labels]
    did = {i: action(labels[i]["relationship"], labels[i]["same_company"]) for i in ids}

    groups = {
        "world": [i for i in ids if truth[i]["needs_world_knowledge"]],
        "local": [i for i in ids if not truth[i]["needs_world_knowledge"]],
        **{rel: [i for i in ids if truth[i]["relationship"] == rel] for rel in ("same", "related", "different")},
    }
    same = groups["same"]
    return {
        "run": name, "pairs": len(ids), "failed": len(failed),
        "wrong_merges": sum(did[i] == "merge" and truth[i]["relationship"] != "same" for i in ids),
        "subsidiaries_merged": sum(did[i] == "merge" and truth[i]["relationship"] == "related" for i in ids),
        "missed_duplicates": sum(labels[i]["relationship"] != "same" for i in same),
        "sent_to_review": sum(did[i] == "review" for i in ids),
        "duplicates": len(same),
        "relationship": sum(labels[i]["relationship"] == truth[i]["relationship"] for i in ids) / len(ids),
        "by_group": {g: [sum(labels[i]["relationship"] == truth[i]["relationship"] for i in v), len(v)]
                     for g, v in groups.items()},
        "same_company": sum((labels[i]["same_company"] >= 0.5) == truth[i]["same_company"] for i in ids) / len(ids),
        "brier": brier([(labels[i]["same_company"], truth[i]["same_company"]) for i in ids]),
        # If the lowest real duplicate scores above the highest non-duplicate,
        # some merge bar would have been right on every pair.
        "lowest_duplicate": min(labels[i]["same_company"] for i in same),
        "highest_other": max(labels[i]["same_company"] for i in ids if i not in same),
        "requests": len(calls),
        "ms_p50": pct([c["ms"] for c in calls], 50),
        "ms_p90": pct([c["ms"] for c in calls], 90),
        "usd_per_1000": sum(c["usd"] for c in calls) / len(ids) * 1000,
        "tokens_per_pair": sum(c["in"] for c in calls) / len(ids),
    }


def main():
    truth = {}
    for line in (ROOT / "data/pairs.jsonl").open():
        r = json.loads(line)
        truth[r["id"]] = r["label"]

    have = [n for n in ORDER if (ROOT / "results/raw" / f"{n}.jsonl").exists()]
    if not have:
        sys.exit("nothing in results/raw yet, run src/bench.py")
    results = [score(n, truth) for n in have]
    (ROOT / "results/results.json").write_text(json.dumps(results, indent=2))

    for r in results:
        if r["pairs"] + r["failed"] < len(truth):
            r["run"] += f" (partial {r['pairs']}/{len(truth)})"

    w = 26
    print(f"{'':32}" + "".join(f"{r['run'][:w - 1]:>{w}}" for r in results))

    def row(label, f):
        print(f"{label:32}" + "".join(f"{f(r):>{w}}" for r in results))

    row("wrong merges", lambda r: f"{r['wrong_merges']}")
    row("  of which a subsidiary", lambda r: f"{r['subsidiaries_merged']}")
    row("duplicates missed", lambda r: f"{r['missed_duplicates']} of {r['duplicates']}")
    row("sent to a person", lambda r: f"{r['sent_to_review']}")
    print()
    row("relationship, all pairs", lambda r: f"{r['relationship'] * 100:.0f}%")
    for g, label in [("world", "needs world knowledge"), ("local", "records are enough"),
                     ("same", "really same"), ("related", "really related"), ("different", "really different")]:
        row(f"  {label}", lambda r, g=g: "{} of {}".format(*r["by_group"][g]))
    row("same_company", lambda r: f"{r['same_company'] * 100:.0f}%")
    row("Brier, same_company", lambda r: f"{r['brier']:.3f}")
    row("lowest p on a real duplicate", lambda r: f"{r['lowest_duplicate']:.2f}")
    row("highest p on anything else", lambda r: f"{r['highest_other']:.2f}")
    print()
    row("ms per pair, p50", lambda r: f"{r['ms_p50']:,.0f}")
    row("ms per pair, p90", lambda r: f"{r['ms_p90']:,.0f}")
    row("$ per 1,000 pairs", lambda r: f"${r['usd_per_1000']:.3f}")
    row("input tokens per pair", lambda r: f"{r['tokens_per_pair']:.0f}")
    row("failed", lambda r: f"{r['failed']}")

    if {"jev", "claude-sonnet-5-thinking"} <= set(have):
        print()
        second_look(truth)


def usd_by_pair(name):
    out = {}
    for line in (ROOT / "results/raw" / f"{name}.jsonl").open():
        rec = json.loads(line)
        if "_meta" not in rec:
            out.update({i: sum(c["usd"] for c in rec["calls"]) / len(rec["ids"]) for i in rec["ids"]})
    return out


def second_look(truth):
    """Jev decides every pair, and Sonnet with thinking takes Jev's review queue.

    Sonnet's answers come from its own full run, so nothing here is re-asked.
    """
    jev, _, _ = load(ROOT / "results/raw/jev.jsonl")
    son, _, _ = load(ROOT / "results/raw/claude-sonnet-5-thinking.jsonl")
    did = {i: action(jev[i]["relationship"], jev[i]["same_company"]) for i in truth}
    queue = [i for i in truth if did[i] == "review"]
    did.update({i: action(son[i]["relationship"], son[i]["same_company"]) for i in queue})

    jev_usd, son_usd = usd_by_pair("jev"), usd_by_pair("claude-sonnet-5-thinking")
    usd = (sum(jev_usd.values()) + sum(son_usd[i] for i in queue)) / len(truth) * 1000
    dupes = [i for i in truth if truth[i]["relationship"] == "same"]
    print(f"Jev on every pair, Sonnet thinking on the {len(queue)} Jev sends to a person:")
    print(f"  wrong merges: {sum(did[i] == 'merge' for i in truth if i not in dupes)}")
    print(f"  duplicates merged: {sum(did[i] == 'merge' for i in dupes)} of {len(dupes)}")
    print(f"  still sent to a person: {sum(did[i] == 'review' for i in truth)}")
    print(f"  $ per 1,000 pairs: ${usd:.3f}")


if __name__ == "__main__":
    main()
