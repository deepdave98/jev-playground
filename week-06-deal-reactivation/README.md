# Closed-lost deal reactivation

A buyer passed because SAML required Enterprise. SAML ships on Team. Put
that deal back in front of its owner with the old objection and release text.

Jev matches product releases to loss reasons. Code excludes customers,
opt-outs, accounts with open deals, and anyone contacted in the last 30 days.
Releases must postdate the loss and fall within the last 90 days.

## Run

Python 3.11+, no packages. Set `TYPESAFE_API_KEY`, then from the repo root:

```bash
python3 week-06-deal-reactivation/src/run.py your-export.jsonl --as-of 2026-10-07 > queue.json
```

Use today's date for your export. Copy the shape in [deals.jsonl](data/deals.jsonl):
opportunity/account IDs, owner, stage, loss date/reason, current CRM flags,
optional last-contact date, and up to 20 releases with IDs, dates and text.
Missing contact dates mean no known contact. Required flags must be booleans.

The output contains `queue` for candidates with release evidence and `decisions` for every
record, including exclusions, uncertainty and API failures. It keeps one
candidate per account, in input order. Exit code 1 means a model call or
answer failed; 2 means invalid input. Review the evidence before contacting anyone.

For an agent, use [`reactivation_queue`](../mcp-server/) after fetching CRM
records and your changelog. Refresh account flags across the whole export.
Save reviewed opportunity/release pairs in your CRM to prevent repeat tasks
on the next run. This script has no persistent state and sends no messages.

## Measured run

32 synthetic cases, 2026-10-07. Eight are excluded before either model runs.
The remaining 24 use identical evidence and question wording.

| | Jev | Haiku 4.5 |
|---|---:|---:|
| Candidates found | 10/10 | 10/10 |
| False candidates | 0 | 0 |
| Exact model labels | 19/24 | 21/24 |
| Median wall time per model call | 358 ms | 6,713 ms |

Jev marked two vague updates as unchanged; the reference labels call them
unclear. Both models also confused partial progress with an unchanged blocker.
These cases test review-queue behavior, not conversion or revenue impact.

Times include HTTP connection setup and Claude subprocess startup. Haiku ran
with thinking disabled. No warmup or overhead subtraction.
This is the latency of these two integrations. [Raw responses](results/raw/)
and [scores](results/results.json) include all misses. Account-wide exclusions
and deduplication are covered by local tests, separately from the model run.

```bash
python3 -m unittest discover -s week-06-deal-reactivation/tests
python3 week-06-deal-reactivation/src/bench.py jev --output /tmp/jev-reactivation.jsonl
python3 week-06-deal-reactivation/src/bench.py claude-haiku-4-5 --output /tmp/haiku-reactivation.jsonl
python3 week-06-deal-reactivation/src/score.py week-06-deal-reactivation/results/raw/*.jsonl
```

The prompt asks for one release supporting every requirement. A cleared
answer without a selected release stays out of the candidate queue. Review
cases that need several releases together separately. The tool cannot verify
that release text and CRM flags are current. A private beta or roadmap promise
does not establish availability.
