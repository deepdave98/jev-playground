"""Recompute counts and wall latency from saved responses."""

import argparse
import json
import math
import pathlib
import statistics

ROOT = pathlib.Path(__file__).resolve().parents[1]


def summarize(path):
    expected = json.loads((ROOT / "data/expected.json").read_text())
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    meta, records = lines[0]["_meta"], lines[1:]
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError(f"{path}: incomplete run or duplicate ids")
    judged = [r for r in records if not r["excluded"]]
    mismatches = []
    for row in records:
        want = expected[row["id"]]
        got = row.get("labels", {})
        if row.get("decision", {}).get("reason") != want["reason"] or any(got.get(k) != v for k,v in want.items() if k != "reason"):
            mismatches.append(row["id"])
    candidates = [r for r in records if r.get("decision", {}).get("reason") == "blocker_cleared"]
    wanted = {i for i, e in expected.items() if e["reason"] == "blocker_cleared"}
    latencies = sorted(r["wall_ms"] for r in judged)
    return {"model": meta["model"], "records": len(records), "model_calls": len(judged),
            "excluded_before_model": len(records)-len(judged),
            "correct": len(records)-len(mismatches), "mismatches": mismatches,
            "expected_candidates": len(wanted),
            "candidates_found": sum(r["id"] in wanted for r in candidates),
            "false_candidates": [r["id"] for r in candidates if r["id"] not in wanted],
            "errors": [r["id"] for r in records if "error" in r],
            "wall_ms_p50": round(statistics.median(latencies)),
            "wall_ms_p95": round(latencies[math.ceil(.95*len(latencies))-1]),
            "wall_ms_total": round(sum(latencies))}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", type=pathlib.Path)
    args=parser.parse_args()
    print(json.dumps([summarize(p) for p in args.runs], indent=2))


if __name__ == "__main__":
    main()
