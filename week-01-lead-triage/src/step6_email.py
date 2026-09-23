"""Step 6: write the first-touch email.

This is the step Jev cannot do, and the reason the repo is not a Jev
advertisement. Jev returns a choice, a score, or a probability. There is no
primitive that returns prose. Running `--prove` shows that against the live
API rather than asserting it.

So the workflow is not "Jev instead of Claude". It is Jev deciding which leads
are worth a Claude call, and Claude writing to those. Emails are only written
for leads that routed to ae_now or sdr_sequence, which is where the saving
actually comes from.

  python3 src/step6_email.py --prove      # ask Jev for prose, show the error
  python3 src/step6_email.py              # write emails for qualified leads
"""

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from claude_runner import PRICING, ClaudeRunner, input_cost  # noqa: E402
from spec import route  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = "claude-sonnet-5"

SYSTEM = """You write the first outbound email to an inbound lead at a B2B SaaS
company selling a GTM data and workflow platform.

You are given the lead and the triage judgments already made about them. Use
them. An enterprise lead that is ready to buy gets a different email from a
mid-market lead that is still evaluating.

Rules:
- Under 90 words.
- Reference something specific they actually wrote. No generic openers.
- One ask, and make it easy to say yes to.
- No exclamation marks, no "I hope this finds you well", no "circling back",
  no "synergy", no em dashes.
- Output the subject line on the first line prefixed with "Subject: ", then a
  blank line, then the body. Nothing else."""


def prove_jev_cannot_write() -> None:
    """Ask the live Jev API for a text answer and print what comes back."""
    import http.client
    import os

    body = json.dumps({
        "model": "jev-latest",
        "state": {"company": "Gusto", "message": "Contract ends in 45 days, need 60 seats."},
        "questions": {
            "email": {
                "type": "text",
                "instructions": "Write a short first-touch email to this lead.",
            }
        },
    })
    conn = http.client.HTTPSConnection("api.typesafe.ai", timeout=30)
    conn.request("POST", "/v1/systemone", body=body, headers={
        "authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}",
        "content-type": "application/json",
    })
    resp = conn.getresponse()
    print(f"asking Jev for a `text` question type -> HTTP {resp.status}")
    print(resp.read().decode()[:600])
    print("\nJev exposes choice, score and noul. There is no text primitive, so "
          "step 6 is Claude's whether you like it or not.")


def main() -> None:
    if "--prove" in sys.argv:
        prove_jev_cannot_write()
        return

    jev_path = ROOT / "results" / "raw" / "jev.jsonl"
    if not jev_path.exists():
        sys.exit("run src/bench.py first")

    leads = {json.loads(l)["id"]: json.loads(l)
             for l in (ROOT / "data" / "leads.jsonl").open()}

    rows = [json.loads(l) for l in jev_path.open() if "_meta" not in l]
    qualified = [r for r in rows
                 if not r.get("error")
                 and route(**r["prediction"]) in ("ae_now", "sdr_sequence")]

    print(f"{len(qualified)} of {len(rows)} leads earned an email "
          f"({len(qualified)/len(rows)*100:.0f}%). Writing those.\n")

    runner = ClaudeRunner(MODEL)
    runner.calibrate()
    price = PRICING[MODEL]
    out, total_usd, lat = [], 0.0, []

    for r in qualified:
        lead = leads[r["id"]]["lead"]
        payload = json.dumps({"lead": lead, "triage": r["prediction"]})
        t = time.perf_counter()
        data, _ = runner._invoke(SYSTEM, payload)
        lat.append(float(data.get("duration_api_ms", (time.perf_counter() - t) * 1000)))

        u = data["usage"]
        in_usd, adj_in = input_cost(u, MODEL, runner.overhead_tokens)
        usd = in_usd + u["output_tokens"] * price["output"]
        total_usd += usd

        out.append({
            "id": r["id"], "company": lead["company"], "title": lead["title"],
            "route": route(**r["prediction"]), "triage": r["prediction"],
            "email": data.get("result", "").strip(),
            "input_tokens": adj_in, "output_tokens": u["output_tokens"],
            "billed_usd": usd, "latency_ms": lat[-1],
        })
        print(f"  {r['id']} {lead['company'][:20]:<20} {lat[-1]:6.0f}ms  ${usd:.5f}")

    dest = ROOT / "results" / "raw" / "step6-emails.jsonl"
    with dest.open("w") as fh:
        for o in out:
            fh.write(json.dumps(o) + "\n")

    n = len(out)
    print(f"\nwrote {n} emails -> {dest}")
    print(f"mean latency {sum(lat)/n:.0f} ms, total ${total_usd:.4f}, "
          f"${total_usd/n:.5f} per email")
    print(f"per 1,000 inbound leads at this qualify rate: "
          f"${total_usd/len(rows)*1000:.2f} of email writing")


if __name__ == "__main__":
    main()
