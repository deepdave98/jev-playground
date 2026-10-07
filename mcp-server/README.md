# Jev MCP server

Run the weekly workflows from an agent with structured inputs and outputs.
The tools return decisions; your CRM or sequencing integration applies them.

## Setup

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/) and a TypeSafe API key.

```bash
claude mcp add jev-gtm -e TYPESAFE_API_KEY=your-key \
  -- uv run --quiet /path/to/jev-playground/mcp-server/jev_server.py
```

For other clients, copy [mcp.example.json](mcp.example.json) and replace the
paths and key. `uv run` installs the declared MCP SDK on first use.

`JEV_LEDGER_DIR` sets the folder `deals_at_risk` can read. It defaults to
`week-02-deal-risk/data`; paths outside that folder are rejected. The server
does not load `.env.local`, so pass the key through your client's config.

Run the live API check before connecting a workflow:

```bash
TYPESAFE_API_KEY=your-key uv run mcp-server/check.py
```

## Tools

| Tool | Input | Output |
|---|---|---|
| `triage_lead` | Company, title, message, optional headcount | Disqualification, ICP fit, segment, intent, route |
| `deal_risk` | One deal and its activity | Risk reasons and event labels |
| `deals_at_risk` | Ledger filename | Risky deals, sorted by ARR |
| `triage_reply` | Reply text, optional sender and subject | Category, opt-out probability, meeting intent, route |
| `meddpicc` | Call summary | Eight qualification levels, forecast readiness, fields to confirm |
| `dedup_pair` | Two account records | Same, related or different; suggested action |
| `reactivation_queue` | Closed-lost records, releases, `as_of` date | One candidate per account with release evidence; all exclusions |

Each tool uses its week's questions. See the [weekly benchmarks](../README.md)
for measured results. Rerun that week's benchmark after changing its prompt.

## Pipeline review

Export activity as JSONL, one object per deal with `deal` and `events` keys.
[ledger.jsonl](../week-02-deal-risk/data/ledger.jsonl) shows the schema.
Put the export in `JEV_LEDGER_DIR`, then ask the agent:

> Call `deals_at_risk` with `ledger_file="ledger.jsonl"` and
> `today="2026-09-25"`. Show each flagged deal's ARR and reason.

The server reads the file, checks deals in parallel and returns only flagged
deals. An agent can review those reasons and draft notes for the owners.
Pass today's date for your own export; the example date matches the fixture.

## Before using your own data

- **Lead triage:** pass enriched headcount and replace the competitor list in
  [week 01's spec](../week-01-lead-triage/src/spec.py).
- **Deal risk:** set `EXEC_MIN_ARR`, `EXEC_WINDOW_DAYS` and
  `CLOSING_SOON_DAYS` in [week 02's spec](../week-02-deal-risk/src/spec.py).
- **Replies:** bare opt-out phrases bypass Jev. Probabilities from 0.4 to 0.6
  go to review. Add your phrases to `STOP_WORDS` in
  [week 03's spec](../week-03-reply-triage/src/spec.py).
- **Qualification:** check the fields in `confirm` before accepting a
  forecast-ready result. The benchmark included a false positive.
- **Deduplication:** `merge` is a suggestion at `p_same >= 0.9`. Validate the
  threshold on your records before applying merges. `related` means link the
  records; a parent and subsidiary remain separate accounts.

For [deal reactivation](../week-06-deal-reactivation/), fetch closed-lost
opportunities and current account flags from your CRM, then attach recent
product releases. Pass up to 100 records to `reactivation_queue`. Review
`queue` with the owner; check `decisions` for missing evidence or API errors.
Persist reviewed opportunity/release pairs in your CRM to avoid repeat tasks.

No tool writes to your CRM or sends messages.
