# Week 04: MEDDPICC from call summaries

Score eight qualification fields from a call summary. Use missing fields
to plan the next call. The forecast rule requires metrics, economic buyer
and decision process to be `established`.

The fixture contains 16 synthetic summaries and 128 labels. Three deals
meet the forecast rule. [Label definitions](rubric.md).

## Saved results

| | Jev | Jev, corrected | Haiku 4.5 | Sonnet 5 |
|---|---|---|---|---|
| incorrectly forecast-ready | 1 | 1 | 0 | 0 |
| ready deals missed | 0 of 3 | 0 of 3 | 0 of 3 | 0 of 3 |
| exact field accuracy | 74.2% | 83.6% | 79.7% | 90.6% |
| within one level | 93.8% | 98.4% | 96.1% | 100% |
| overstated / understated | 33 / 0 | 20 / 1 | 25 / 1 | 9 / 3 |
| call latency, p50 | 428 ms | 428 ms | 2,320 ms | 2,419 ms |
| cost per 1,000 calls | $0.055 | $0.055 | $1.599 | $3.714 |

[Metrics](results/results.json) and [raw runs](results/raw/).
Costs are extrapolated from these runs. Jev latency is request wall time;
Claude latency is the CLI-reported API duration.

The correction subtracts 0.30 from each Jev score before rounding. It comes
from the mean signed error of 193 saved answers across weeks 01 to 03;
[`bias.py`](src/bias.py) reproduces the calculation. Corrected results reuse
the same responses and add no model calls.

The correction still puts Pinecrest in the forecast. Its summary says the
team would work out next steps internally. Jev scores decision process at
1.83; subtracting 0.30 still rounds to `established`.

Champion is another weak field: Jev and Haiku each overstate it in 8 of 16
calls. Attending a call does not establish that someone is pushing the
purchase internally.

Rescoring the four deals Jev marks ready with Sonnet's saved answers removes
the false forecast and retains all three ready deals. Estimated cost is
$0.994 per 1,000 calls, versus $3.714 for Sonnet on every call. This is a
simulation using the independent runs; the combined workflow was not run.

## Run

From the repository root (Python 3.10+, no Python packages needed):

```bash
cd week-04-meddpicc
python3 src/score.py                # rescore saved runs, no API calls
python3 src/bias.py                 # measure the earlier score offset
python3 src/calls.py                # rebuild the fixture
python3 src/bench.py                # new Jev and Claude runs
```

New runs need `TYPESAFE_API_KEY` and an authenticated `claude` CLI.
`bench.py jev` runs Jev alone. The [`meddpicc`](../mcp-server/README.md) tool
returns the corrected fields and remaining gaps.

This is a small synthetic set with deliberately explicit qualification
signals. The false-forecast result rests on one deal. It does not establish
an error rate for real call transcripts or a threshold for forecast writes.
