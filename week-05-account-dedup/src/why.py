"""Request new explanations for a saved Claude run's incorrect labels."""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT / "src"))
from bench import SYSTEM, seen  # noqa: E402
from common.bench import load  # noqa: E402
from common.claude import Claude  # noqa: E402

ASK_WHY = SYSTEM + "\n\nAfter the JSON, add one line saying why."


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "claude-sonnet-5"
    items = {r["id"]: r for r in map(json.loads, (ROOT / "data/pairs.jsonl").open())}
    labels, _, _ = load(ROOT / "results/raw" / f"{name}.jsonl")
    wrong = [i for i, got in labels.items() if got["relationship"] != items[i]["label"]["relationship"]]

    claude = Claude(name.removesuffix("-thinking"), thinking=name.endswith("-thinking"))
    with (ROOT / "results" / f"why-{name}.jsonl").open("w") as fh:
        for i in wrong:
            data, _ = claude.call(ASK_WHY, json.dumps(seen(items[i])))
            rec = {"id": i, "truth": items[i]["label"]["relationship"],
                   "in_the_run": labels[i]["relationship"], "text": data.get("result", "")}
            fh.write(json.dumps(rec) + "\n")
            print(f"{i}  truth {rec['truth']}, run said {rec['in_the_run']}\n  {rec['text']}\n")


if __name__ == "__main__":
    main()
