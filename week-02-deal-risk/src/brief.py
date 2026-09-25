"""The last step: Claude reviews what Jev flagged and writes to the deal owner.

Jev can't write the note (week 01 has the HTTP 400 that proves it), and it
would be a waste to have Claude read every deal. So Claude only sees the deals
Jev flagged, with the full ledger and Jev's reasons, and does two things: says
whether the flag holds up, and writes the owner a short note with a next step.

    python3 src/brief.py              # Claude gets the ledger and the reasons
    python3 src/brief.py --facts      # plus the dates, worked out in code

The first version let Claude do its own date arithmetic, and it decided an
August 15 meeting was inside a 30 day window ending September 25. --facts
hands it the day counts so it only has to make judgment calls.
"""

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from claude import Claude  # noqa: E402
from jev import visible  # noqa: E402
from spec import AS_OF, RISK_RULES, days  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = "claude-sonnet-5"

SYSTEM = f"""An automated check flagged this deal as at risk. You get the deal, its full
activity ledger and the reasons the check gave. Today is {AS_OF}.

These are the rules the check applies:

{RISK_RULES}

First decide whether the flag holds up against the ledger. The check reads
events one field at a time and can be wrong, for example about whether
someone senior took part and when.

If a "computed" block is present, its numbers came from code and are exact.
Use them rather than working dates out yourself. You can still argue that
some event shows senior engagement the check missed.

Then write the deal owner a note for Slack. Two or three sentences, plain,
no greeting, no sign-off. Say what is actually going on, naming the people
and events involved, and the one thing they should do this week. If the flag
does not hold up, say why in one sentence and stop.

No em dashes. Answer with JSON only, no fence:
{{"holds_up": true, "note": "..."}}"""


def facts(deal, events, labels):
    """The arithmetic, done once in code, from Jev's own event labels."""
    execs = [e for e in events if labels[e["id"]]["exec_engaged"]]
    last = max(execs, key=lambda e: e["ts"]) if execs else None
    return {
        "deal_value_meets_100k_rule": deal["arr"] >= 100_000,
        "days_until_close": days(AS_OF, deal["close_date"]),
        "last_senior_engagement_jev_found":
            {"event": last["id"], "days_ago": days(last["ts"], AS_OF)} if last else None,
    }


def main():
    use_facts = "--facts" in sys.argv
    ledger = {json.loads(l)["deal"]["id"]: json.loads(l) for l in (ROOT / "data/ledger.jsonl").open()}
    flagged = [json.loads(l) for l in (ROOT / "results/raw/jev-per-deal.jsonl").open()
               if "_meta" not in l and json.loads(l)["reasons"]]
    print(f"Jev flagged {len(flagged)} of {len(ledger)} deals. Claude reviews only those.\n")

    claude = Claude(MODEL)
    claude.calibrate()
    out = []
    for rec in flagged:
        row = ledger[rec["deal"]]
        payload = {"deal": row["deal"], "flagged_for": rec["reasons"],
                   "events": [visible(e) for e in row["events"]]}
        if use_facts:
            payload["computed"] = facts(row["deal"], row["events"], rec["labels"])
        t = time.perf_counter()
        data, ms = claude.call(SYSTEM, json.dumps(payload))
        usd, tokens = claude.cost(data["usage"])
        reply = json.loads(data["result"][data["result"].find("{"):data["result"].rfind("}") + 1])
        truth = row["label"]["at_risk"]
        out.append({"deal": row["deal"]["account"], "arr": row["deal"]["arr"],
                    "jev_reasons": rec["reasons"], "really_at_risk": truth,
                    "holds_up": reply["holds_up"], "note": reply["note"],
                    "ms": ms, "usd": usd, "tokens_in": tokens,
                    "tokens_out": data["usage"]["output_tokens"]})
        mark = "ok " if reply["holds_up"] == truth else "WRONG"
        print(f"  {mark} {row['deal']['account']:<13} holds_up={reply['holds_up']!s:<5} "
              f"really at risk={truth!s:<5} {ms:5.0f} ms ${usd:.5f}")

    dest = ROOT / "results/raw" / ("brief-facts.jsonl" if use_facts else "brief.jsonl")
    with dest.open("w") as fh:
        for o in out:
            fh.write(json.dumps(o) + "\n")

    agree = sum(o["holds_up"] == o["really_at_risk"] for o in out)
    print(f"\nClaude agreed with the answer key on {agree} of {len(out)} flags")
    print(f"total ${sum(o['usd'] for o in out):.4f}, "
          f"mean {sum(o['ms'] for o in out) / len(out):.0f} ms -> {dest}")


if __name__ == "__main__":
    main()
