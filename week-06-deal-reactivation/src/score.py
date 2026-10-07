"""Recompute counts and wall latency from saved responses."""

import argparse
import hashlib
import json
import math
import pathlib
import statistics

from reactivation import decide, prepare

ROOT = pathlib.Path(__file__).resolve().parents[1]


def summarize(path):
    expected = json.loads((ROOT / "data/expected.json").read_text())
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    meta, records = lines[0]["_meta"], lines[1:]
    fixture = ROOT / "data/deals.jsonl"
    if hashlib.sha256(fixture.read_bytes()).hexdigest() != meta["sha256"]["data/deals.jsonl"]:
        raise ValueError(f"{path}: input data changed since the run")
    inputs = {r["id"]: r for r in map(json.loads, fixture.read_text().splitlines())}
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise ValueError(f"{path}: incomplete run or duplicate ids")
    judged = [r for r in records if not r["excluded"]]
    mismatches = []
    for row in records:
        if row["excluded"] != prepare(inputs[row["id"]], meta["as_of"])[1]:
            raise ValueError(f"{path}: exclusion rule changed for {row['id']}")
        if "error" not in row and decide(inputs[row["id"]], meta["as_of"], row.get("labels")) != row["decision"]:
            raise ValueError(f"{path}: decision rule changed for {row['id']}")
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
            "model_correct": sum(r["id"] not in mismatches for r in judged),
            "expected_sha256": hashlib.sha256((ROOT / "data/expected.json").read_bytes()).hexdigest(),
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
