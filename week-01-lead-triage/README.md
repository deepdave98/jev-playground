# Week 01: inbound lead triage

Classify a lead's fit, intent, segment and disqualification status, then route
it to an AE, SDR, self-serve, nurture or reject queue. Routing runs in code.
Sonnet drafts emails for leads sent to an AE or SDR; it does not send them.

## Results

60 synthetic leads, recorded September 22, 2026. Labels and routing rules are
in [rubric.md](rubric.md); the [scorer](src/score.py) produces these figures
from the committed [responses](results/raw/).

| | Jev | Haiku 4.5 | Haiku, four calls | Sonnet 5 |
|---|---|---|---|---|
| Correct route | 90.0% | 53.3% | 61.7% | 78.3% |
| AE leads rejected, of 16 | 0 | 7 | 6 | 1 |
| Disqualified leads let through, of 12 | 2 | 1 | 1 | 1 |
| Intent accuracy | 75.0% | 83.3% | 81.7% | 81.7% |
| Latency p50 | 366 ms | 2,630 ms | 13,631 ms | 2,571 ms |
| Estimated cost / 1,000 leads | $0.042 | $1.339 | $3.933 | $3.006 |

Each runner receives the criteria in [spec.py](src/spec.py). The split Haiku
run answers each question separately. Full metrics, including the second
prompt variant, are in [results.json](results/results.json).

- Jev missed both competitor leads, L009 and L010. Naming competitors in the
  second prompt still left both below the rejection threshold. Sonnet
  rejected both with that prompt. Use a maintained domain blocklist before
  classification.
- Jev overstated intent in all 15 intent errors. Check intent thresholds
  against your own reviewed leads before using them for sales handoffs.
- The email step drafted 29 messages, including one for competitor lead
  L009. The saved drafts also contain unsupported product claims and
  signatures. They need review before sending.

## Use it

The [MCP server](../mcp-server/) exposes `triage_lead`. Pass an enriched form
submission, then use its route and confidence values to choose a CRM queue.
Keep a review queue for uncertain classifications and check known competitors
before requesting a draft.

To inspect the saved run without API access:

```bash
cd week-01-lead-triage
python3 src/score.py
```

To rerun, export `TYPESAFE_API_KEY` and sign in to the `claude` CLI. Python
3.10+; no third-party Python packages. These commands replace saved outputs.

```bash
python3 src/build_dataset.py
python3 src/bench.py
python3 src/bench.py --variant=v2
python3 src/split_runner.py claude-haiku-4-5
python3 src/step6_email.py
python3 src/score.py
```

Costs use recorded token counts and the rates in the runners. Claude's
estimate subtracts measured CLI prompt overhead and accounts for cache rates;
it is not an invoice. Thinking was disabled. Claude latency uses the CLI's
API duration; Jev latency uses request wall time on a reused connection.
These timings use different measurement boundaries.

This is one run on 60 constructed examples. It does not establish accuracy,
probability calibration, or savings on a production lead stream.
