"""Runs every setup over the 60 replies, one request at a time.

    python3 src/bench.py                      # all four
    python3 src/bench.py jev jev-batched      # just these

jev-batched puts ten replies in one request. Replies don't share context the
way week 02's events did, so batching can't help accuracy here. What it tests
is whether Jev keeps ten unrelated items apart when they arrive together.
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

RUNS = ["jev", "jev-batched", "claude-haiku-4-5", "claude-sonnet-5"]
BATCH = 10

SYSTEM = f"""You triage replies to an outbound email sequence. You get one reply and
who it came from. Answer three questions about it.

{render(QUESTIONS)}

Answer with JSON only, no fence:
{answer_shape(QUESTIONS)}"""


def seen(item):
    """What a model gets: the reply and its envelope, never the label."""
    return item["reply"]


def jev_call(data, ms):
    tokens = data["usage"]["input_tokens"]
    return {"ms": ms, "in": tokens, "out": 0, "usd": tokens * USD_PER_TOKEN}


def jev_one(jev):
    def step(chunk):
        item = chunk[0]
        data, ms = jev.ask(seen(item), QUESTIONS)
        return {item["id"]: decode(data["answers"], QUESTIONS)}, [jev_call(data, ms)]
    return step


def jev_batched(jev):
    def step(chunk):
        questions = {f"{x['id']}_{name}": {**q, "instructions": f"About reply {x['id']} only. "
                                            + q["instructions"]}
                     for x in chunk for name, q in QUESTIONS.items()}
        data, ms = jev.ask({"replies": [{"id": x["id"], **seen(x)} for x in chunk]}, questions)
        labels = {x["id"]: decode(data["answers"], QUESTIONS, prefix=f"{x['id']}_") for x in chunk}
        return labels, [jev_call(data, ms)]
    return step


def claude_one(claude):
    def step(chunk):
        item = chunk[0]
        obj, ms, usd, tokens_in, tokens_out = claude.ask(SYSTEM, seen(item))
        call = {"ms": ms, "in": tokens_in, "out": tokens_out, "usd": usd}
        return {item["id"]: read(obj, QUESTIONS)}, [call]
    return step


def main():
    items = [json.loads(line) for line in (ROOT / "data/replies.jsonl").open()]
    assert all("label" not in seen(x) for x in items)
    out = ROOT / "results/raw"

    which = sys.argv[1:] or RUNS
    unknown = [w for w in which if w not in RUNS]
    if unknown:
        sys.exit(f"unknown: {unknown}. pick from {RUNS}")

    for name in which:
        if name.startswith("jev"):
            jev = Jev()
            jev.warm()
            if name == "jev":
                run(name, items, jev_one(jev), out)
            else:
                run(name, items, jev_batched(jev), out, batch=BATCH)
            jev.close()
        else:
            claude = Claude(name)
            samples = claude.calibrate()
            print(f"[{name}] CLI overhead {claude.overhead} tokens, subtracted from every call")
            run(name, items, claude_one(claude), out,
                meta={"cli_overhead": claude.overhead, "cli_overhead_samples": samples})
        print()


if __name__ == "__main__":
    main()
