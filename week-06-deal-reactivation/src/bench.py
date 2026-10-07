"""Measure one model on the fixed reactivation cases; preserve responses."""

import argparse
import hashlib
import json
import pathlib
import sys
import time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from common.claude import Claude
from common.jev import Jev, decode
from common.prompt import answer_shape, render
from reactivation import decide, prepare, questions

AS_OF = "2026-10-07"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=["jev", "claude-haiku-4-5"])
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    cases = [json.loads(line) for line in (ROOT / "data/deals.jsonl").read_text().splitlines()]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents a rerun from silently replacing published evidence.
    with args.output.open("x") as output:
        client = Jev() if args.model == "jev" else Claude(args.model)
        meta = {"model": args.model, "started": datetime.now(timezone.utc).isoformat(), "as_of": AS_OF,
                "thinking": False, "warmup": False, "latency": "wall_ms includes client startup and retries",
                "sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in [ROOT / "data/deals.jsonl", ROOT / "src/reactivation.py"]}}
        output.write(json.dumps({"_meta": meta}) + "\n")
        try:
            for record in cases:
                state, excluded = prepare(record, AS_OF)
                entry = {"id": record["id"], "excluded": excluded}
                if excluded:
                    entry["decision"] = decide(record, AS_OF)
                else:
                    qs = questions(state)
                    started = time.perf_counter()
                    try:
                        if args.model == "jev":
                            raw, api_ms = client.ask(state, qs)
                            labels = decode(raw["answers"], qs)
                        else:
                            system = "Answer using only the supplied record.\n" + render(qs) + "\nReturn JSON only:\n" + answer_shape(qs)
                            raw, api_ms = client.call(system, json.dumps(state))
                            from common.claude import parse
                            labels = parse(raw.get("result", ""))
                        entry.update(raw=raw, labels=labels, api_ms=api_ms)
                        entry["decision"] = decide(record, AS_OF, labels)
                    except Exception as exc:
                        entry["error"] = type(exc).__name__
                    entry["wall_ms"] = (time.perf_counter() - started) * 1000
                output.write(json.dumps(entry) + "\n")
                output.flush()
                print(record["id"], entry.get("error") or entry["decision"]["reason"], flush=True)
        finally:
            if args.model == "jev":
                client.close()


if __name__ == "__main__":
    main()
