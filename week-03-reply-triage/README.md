# Week 03: outbound reply triage

Classify a reply, check for an opt-out, then route it to suppression,
scheduling, follow-up or review. Extract return dates and referral contacts
only from replies routed to pause or reroute.

The fixture contains 60 synthetic replies, including 9 opt-outs and 12
interested prospects. [Labels and routing rules](rubric.md).

## Saved results

| | Jev | Jev, 10 per request | Haiku 4.5 | Sonnet 5 |
|---|---|---|---|---|
| missed opt-outs | 1 of 9 | 0 of 9 | 0 of 9 | 0 of 9 |
| false suppressions | 0 | 0 | 0 | 1 |
| interested replies routed away | 0 of 12 | 1 of 12 | 0 of 12 | 0 of 12 |
| sent to review | 0 | 0 | 6 | 0 |
| route accuracy | 98.3% | 96.7% | 88.3% | 95.0% |
| category accuracy | 100% | 95.0% | 88.3% | 96.7% |
| exact meeting intent | 83.3% | 73.3% | 98.3% | 96.7% |
| all 60, sequential | 22.3 s | 2.9 s | 119.4 s | 141.2 s |
| request latency, p50 | 365 ms | 449 ms | 1,930 ms | 2,200 ms |
| cost per 1,000 replies | $0.033 | $0.024 | $0.699 | $2.018 |

[Metrics](results/results.json) and [raw runs](results/raw/).
Costs are extrapolated from these runs. Jev latency is request wall time;
Claude latency is the CLI-reported API duration.

Jev missed the reply "STOP" at an opt-out score of 0.41. Sonnet treated
sarcasm about five emails as an opt-out at 0.50. The MCP tool handles exact
stop words before calling Jev and sends opt-out scores from 0.4 to 0.6 to
review. These extra rules are absent from the table above.

Haiku returned meeting-intent values in the category field six times.
Invalid categories go to review. Batching cut Jev's total time from 22.3 to
2.9 seconds, with two routing errors instead of one.

Jev routed 17 replies to extraction. Haiku got all 17 dates or contacts
right for $0.0062 total; Sonnet got 15 right for $0.0160. Sonnet returned a
backup contact instead of a return date for two away messages.
[Extraction records](results/raw/extract.jsonl).

## Run

From the repository root (Python 3.10+, no Python packages needed):

```bash
cd week-03-reply-triage
python3 src/score.py                # rescore saved runs, no API calls
python3 src/replies.py              # rebuild the fixture
python3 src/bench.py                # new Jev and Claude runs
python3 src/extract.py              # new extraction calls
```

New runs need `TYPESAFE_API_KEY` and an authenticated `claude` CLI.
`bench.py` also accepts run names, for example `jev jev-batched`.

Use [`triage_reply`](../mcp-server/README.md) to apply the routing rules to
incoming replies. The benchmark has one run per setup; 60 synthetic replies
are too few to estimate error rates for a live inbox. Date extraction uses
US month/day and the reply timestamp supplied in the fixture.
