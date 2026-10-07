"""Measure mean signed score error from saved Jev runs for weeks 01 to 03."""

import json
import pathlib
import statistics

REPO = pathlib.Path(__file__).resolve().parents[2]


def jsonl(path):
    return [json.loads(line) for line in (REPO / path).open()]


def week01():
    levels = ["none", "researching", "evaluating", "ready_to_buy"]
    rows = [r for r in jsonl("week-01-lead-triage/results/raw/jev.jsonl") if "_meta" not in r]
    return [r["raw"]["answers"]["intent"]["score"] - levels.index(r["labels"]["intent"])
            for r in rows if not r.get("error")]


def week02():
    levels = ["none", "watch", "serious", "critical"]
    truth = {e["id"]: e["label"]["severity"]
             for row in jsonl("week-02-deal-risk/data/ledger.jsonl") for e in row["events"]}
    rows = [r for r in jsonl("week-02-deal-risk/results/raw/jev.jsonl") if "_meta" not in r]
    return [got["severity_score"] - levels.index(truth[eid])
            for r in rows for eid, got in r["labels"].items()]


def week03():
    levels = ["none", "curious", "open", "ready"]
    truth = {r["id"]: r["label"]["meeting_intent"] for r in jsonl("week-03-reply-triage/data/replies.jsonl")}
    rows = [r for r in jsonl("week-03-reply-triage/results/raw/jev.jsonl") if "_meta" not in r]
    return [got["meeting_intent_score"] - levels.index(truth[i])
            for r in rows for i, got in r["labels"].items()]


def main():
    weeks = {"week 01, intent": week01(), "week 02, severity": week02(),
             "week 03, meeting intent": week03()}
    for name, errors in weeks.items():
        print(f"{name:<26} {len(errors):>3} answers   {statistics.fmean(errors):+.3f}")
    pooled = [e for errors in weeks.values() for e in errors]
    print(f"{'pooled':<26} {len(pooled):>3} answers   {statistics.fmean(pooled):+.3f}")


if __name__ == "__main__":
    main()
