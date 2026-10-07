# Week 02: deal risk from an activity ledger

Read CRM, email, meeting and support events, classify their risk signals, then
flag deals for an owner to review. Each event gets a signal, severity and
executive-engagement label. Code applies the date, value and count rules.

## Results

20 synthetic deals, 73 events in AckDB's ledger format, with eight deals
labelled at risk. The benchmark date is September 25, 2026.
[Reference rules](rubric.md), [full metrics](results/results.json),
[raw responses](results/raw/).

| Setup | Caught, of 8 | False alarms | Total time | Estimated cost |
|---|---|---|---|---|
| Jev, per event | 8 | 1 | 25.6 s | $0.0031 |
| Jev, per deal | 8 | 1 | 7.3 s | $0.0023 |
| Haiku 4.5, per event | 8 | 3 | 191.6 s | $0.0622 |
| Sonnet 5, per event | 8 | 1 | 224.3 s | $0.1716 |
| Sonnet 5, per deal | 8 | 0 | 75.1 s | $0.0806 |
| Sonnet 5, direct risk verdict | 8 | 6 | 67.5 s | $0.0566 |

Per-event runs make 73 calls; per-deal runs make 20. All except the direct
verdict use [spec.assess()](src/spec.py) to decide risk from event labels.

- Context mattered: all three per-event models missed executive engagement
  on E026, E033, E046 and E055. The person's title appeared in another event.
  Passing the whole deal fixed all four for Jev and three for Sonnet.
- Sonnet's direct verdict produced six false alarms, all involving
  `no_exec_30d`. Labelling events and applying the rules in code produced none.
- Jev's per-deal false alarm was Silverline: its SVP call scored 0.49 for
  executive engagement, below the 0.5 cutoff. Its exact severity accuracy was
  63%; 24 of 27 severity errors rated the event too high.
- A Sonnet review of Jev's nine flagged deals got all nine verdicts right
  when supplied with computed day counts. This brought the combined run to
  $0.0399 and 52.1 seconds. It did not review the eleven unflagged deals.

## Use it

The [MCP server](../mcp-server/) exposes `deal_risk` and `deals_at_risk`.
Retrieve each deal's activity from your CRM and support tools, pass the events
together, and return the flagged deals to their owners with supporting events.
The [brief script](src/brief.py) drafts owner notes; it does not send them.

Use current activity and exclude resolved issues. The benchmark rule has no
resolution field and can keep flagging old incidents. It also assumes events are dated
on or before the evaluation date. Validate timestamps before applying it to a
live ledger.

## Run

To score the saved responses without API access:

```bash
cd week-02-deal-risk
python3 src/score.py
```

To rerun, export `TYPESAFE_API_KEY` and sign in to the `claude` CLI. Python
3.10+; no third-party Python packages. These commands replace saved outputs.

```bash
python3 src/ledger.py
python3 src/bench.py
python3 src/brief.py --facts
python3 src/score.py
```

Costs use recorded tokens and the rates in the runners, with measured CLI
prompt overhead subtracted and cache rates included. Thinking was disabled.
Times sum sequential calls: Jev request wall time on a reused connection,
Claude CLI API duration. These are different measurement boundaries.

One deal changes accuracy by five percentage points. These synthetic ledgers
contain no duplicate events or resolved-issue history; the results do not
establish production accuracy or throughput.
