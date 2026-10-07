"""Read a CRM JSONL export and write a reactivation review queue to stdout."""

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from common.jev import Jev, decode
from reactivation import build_queue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("--as-of", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()
    try:
        records = [json.loads(line) for line in args.input.read_text().splitlines() if line.strip()]
        # Construct the client only when a record passes the CRM filters.
        clients = []
        def judge(state, questions):
            if not clients:
                clients.append(Jev())
            return decode(clients[0].ask(state, questions)[0]["answers"], questions)
        try:
            result = build_queue(records, args.as_of, judge)
        finally:
            for client in clients:
                client.close()
        print(json.dumps(result, indent=2))
        if any(d["reason"] in {"model_error", "invalid_model_answer"} for d in result["decisions"]):
            return 1
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Cannot build queue: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
