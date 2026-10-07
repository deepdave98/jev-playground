# Week 05: duplicate CRM accounts

Given two candidate records, decide whether they describe the same company,
related companies, or unrelated companies. The benchmark rule merges `same`
pairs at a score of 0.9 or higher, reviews the rest, and keeps related
companies as separate linked records.

50 fixture pairs use real and fictional company names: 18 duplicates,
14 related pairs and 18 unrelated pairs. Fourteen labels require knowledge
beyond the supplied records. [Label rules](rubric.md).

## Saved results

| | Jev | Haiku 4.5 | Sonnet 5 | Sonnet 5, thinking |
|---|---|---|---|---|
| wrong merges | 0 | 1 | 2 | 0 |
| duplicates missed | 0 of 18 | 0 of 18 | 0 of 18 | 0 of 18 |
| sent to review | 12 | 0 | 1 | 0 |
| relationship correct | 48 of 50 | 46 of 50 | 46 of 50 | 50 of 50 |
| needs external knowledge | 13 of 14 | 10 of 14 | 10 of 14 | 14 of 14 |
| records sufficient | 35 of 36 | 36 of 36 | 36 of 36 | 36 of 36 |
| pair latency, p50 | 364 ms | 2,803 ms | 2,124 ms | 10,161 ms |
| cost per 1,000 pairs | $0.025 | $0.814 | $1.299 | $11.894 |

[Metrics](results/results.json) and [raw runs](results/raw/).
Costs are extrapolated from these runs. Thinking uses max effort; the other
Claude runs disable thinking. A duplicate sent to review counts as found.

Haiku merged Google with Alphabet. Sonnet without thinking merged that pair
and Instagram with Meta. Both runs gave a wrong merge the same 0.95 score
they gave real duplicates, so a higher score threshold cannot separate them.

Jev merged 6 duplicates and sent 12 to review. Replacing those 12 decisions
with Sonnet's saved thinking responses merges all 18, with no wrong merges,
for an estimated $2.810 per 1,000 pairs. This is a simulation using the
independent runs; the combined workflow was not run.

Jev's two relationship errors still matter: it called Tableau unrelated to
Salesforce and linked Apple Inc. to Apple Leisure Group. Neither produced a
merge under the benchmark rule.

## Run

From the repository root, with dependencies from `requirements.txt` installed:

```bash
cd week-05-account-dedup
python3 src/score.py                # rescore saved runs, no API calls
python3 src/pairs.py                # rebuild the fixture
python3 src/bench.py                # new Jev and Claude runs
python3 src/why.py claude-sonnet-5   # new diagnostic calls on misses
```

New runs need `TYPESAFE_API_KEY` and an authenticated `claude` CLI.
`bench.py jev` runs Jev alone. [`dedup_pair`](../mcp-server/README.md) returns
the proposed action for records supplied by a CRM or import workflow.

The fixture has one run per setup. It tests a specific policy for company
identity, including how subsidiaries are retained. Corporate relationships
can change, and 50 pairs cannot establish a safe automatic-merge threshold.
Diagnostic explanations are new responses and do not reveal why a prior
response failed.
