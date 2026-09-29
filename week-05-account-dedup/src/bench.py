"""Runs every setup over the 50 candidate pairs, one request at a time.

    python3 src/bench.py                  # all three
    python3 src/bench.py jev              # just this one
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT / "src"))
from common.bench import run  # noqa: E402
from common.claude import Claude  # noqa: E402
from common.jev import USD_PER_TOKEN, Jev, decode  # noqa: E402
from common.prompt import answer_shape, read, render  # noqa: E402
from spec import QUESTIONS  # noqa: E402

RUNS = ["jev", "claude-haiku-4-5", "claude-sonnet-5"]

SYSTEM = f"""You clean up duplicate accounts in a CRM. You get two account records that
look alike. Answer two questions about them.

{render(QUESTIONS)}

Answer with JSON only, no fence:
{answer_shape(QUESTIONS)}"""


def seen(item):
    """What a model gets: the two records, never the label."""
    return item["pair"]


def jev_step(jev):
    def step(chunk):
        item = chunk[0]
        data, ms = jev.ask(seen(item), QUESTIONS)
        tokens = data["usage"]["input_tokens"]
        call = {"ms": ms, "in": tokens, "out": 0, "usd": tokens * USD_PER_TOKEN}
        return {item["id"]: decode(data["answers"], QUESTIONS)}, [call]
    return step


def claude_step(claude):
    def step(chunk):
        item = chunk[0]
        obj, ms, usd, tokens_in, tokens_out = claude.ask(SYSTEM, seen(item))
        call = {"ms": ms, "in": tokens_in, "out": tokens_out, "usd": usd}
        return {item["id"]: read(obj, QUESTIONS)}, [call]
    return step


def main():
    items = [json.loads(line) for line in (ROOT / "data/pairs.jsonl").open()]
    assert all("label" not in seen(x) for x in items)
    out = ROOT / "results/raw"

    which = sys.argv[1:] or RUNS
    unknown = [w for w in which if w not in RUNS]
    if unknown:
        sys.exit(f"unknown: {unknown}. pick from {RUNS}")

    for name in which:
        if name == "jev":
            jev = Jev()
            jev.warm()
            run(name, items, jev_step(jev), out)
            jev.close()
        else:
            claude = Claude(name)
            samples = claude.calibrate()
            print(f"[{name}] CLI overhead {claude.overhead} tokens, subtracted from every call")
            run(name, items, claude_step(claude), out,
                meta={"cli_overhead": claude.overhead, "cli_overhead_samples": samples})
        print()


if __name__ == "__main__":
    main()
