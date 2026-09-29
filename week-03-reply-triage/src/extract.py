"""The step Jev can't do: pull the return date or the new contact out of a reply.

Jev answers with a choice, a score or a probability, never a date or a name.
So after Jev triages, Claude reads only the replies it routed to pause (out
of office) or reroute (wrong person) and extracts what the next step needs.
Both Haiku and Sonnet run it, to see whether the cheap model is enough.

    python3 src/extract.py
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT / "src"))
from common.bench import load  # noqa: E402
from common.claude import Claude  # noqa: E402
from score import routed  # noqa: E402

SYSTEM = """You read a reply to an outbound sales email and pull out one thing.

If it is an out of office message, give the date the sender is back, as
YYYY-MM-DD. Read "the 6th" or "Thursday" as the next such date after the
reply's received timestamp. Dates like 10/08 are US month/day.

If the sender points to someone else, give that contact: their email if the
reply has one, otherwise their full name. If there is nobody to contact, use
null.

Answer with JSON only, no fence:
{"return_date": "YYYY-MM-DD or null", "contact": "email, name, or null"}"""


def contact_matches(got, want):
    if want is None:
        return got in (None, "", "null")
    return bool(got) and want.lower() in str(got).lower()


def main():
    items = {json.loads(line)["id"]: json.loads(line) for line in (ROOT / "data/replies.jsonl").open()}
    triage, _, _ = load(ROOT / "results/raw/jev.jsonl")
    todo = [i for i, lab in triage.items() if routed(lab) in ("pause", "reroute")]
    print(f"Jev routed {len(todo)} of {len(items)} replies to pause or reroute.\n")

    results = []
    for model in ("claude-haiku-4-5", "claude-sonnet-5"):
        claude = Claude(model)
        claude.calibrate()
        for i in todo:
            item, label = items[i], items[i]["label"]
            obj, ms, usd, tokens_in, tokens_out = claude.ask(SYSTEM, item["reply"])
            date, contact = obj.get("return_date"), obj.get("contact")
            if isinstance(date, str) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                date = None
            if label["category"] == "out_of_office":
                ok = date == label["return_date"]
            elif label["category"] == "wrong_person":
                ok = contact_matches(contact, label["referral"])
            else:
                ok = False  # Jev routed it here by mistake, so nothing right to extract
            results.append({"model": model, "id": i, "category": label["category"],
                            "return_date": date, "contact": contact, "correct": ok,
                            "ms": ms, "usd": usd, "tokens_in": tokens_in, "tokens_out": tokens_out})
            print(f"  {model:<17} {i} {'ok   ' if ok else 'WRONG'} {date or contact}")

    dest = ROOT / "results/raw/extract.jsonl"
    with dest.open("w") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")

    for model in ("claude-haiku-4-5", "claude-sonnet-5"):
        rs = [r for r in results if r["model"] == model]
        print(f"\n{model}: {sum(r['correct'] for r in rs)} of {len(rs)} right, "
              f"${sum(r['usd'] for r in rs):.4f}, mean {sum(r['ms'] for r in rs) / len(rs):.0f} ms")


if __name__ == "__main__":
    main()
