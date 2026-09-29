# Using this from an agent

Each week in this repo ends with a pipeline that works. This folder puts those
pipelines behind an MCP server, so an agent that already talks to your GTM
tools can hand Jev the decisions instead of making them itself.

```
jev_server.py       the server, six tools
check.py            starts it the way an agent would and calls each tool
mcp.example.json    config to copy
```

## Why bother

A GTM agent in 2026 usually has a handful of MCP servers wired in. One for
the activity database (AckDB, in my case), one for whatever enrichment tool
fills in headcount, titles and funding, one for the CRM, one for Slack. The
agent pulls rows out of those and decides things about them: whether a lead
is worth an AE, whether a deal is slipping, whether an email came from
someone senior.

Every row the agent decides on costs frontier model tokens, and most of
those decisions are the typed kind Jev does for 1% to 3% of Sonnet's price,
at 13% to 18% of its latency. Weeks 01 to 05 have the numbers.

## Setup

You need [uv](https://docs.astral.sh/uv/) and a TypeSafe API key. The server
declares its own dependency at the top of the file, so `uv run` fetches the
MCP SDK the first time and there's nothing to install.

For Claude Code:

```bash
claude mcp add jev-gtm -e TYPESAFE_API_KEY=your-key \
  -- uv run --quiet /path/to/jev-playground/mcp-server/jev_server.py
```

For anything that takes a JSON config, like Claude Desktop, copy
`mcp.example.json` and fill in the paths. `JEV_LEDGER_DIR` is the folder
`deals_at_risk` is allowed to read from. The server refuses anything outside
it, including `../../.env.local`, which I checked.

To see it working before you wire it into anything:

```bash
TYPESAFE_API_KEY=your-key uv run mcp-server/check.py
```

## The tools

| tool | give it | get back | time |
|---|---|---|---|
| `triage_lead` | company, title, message, and headcount if you have it | disqualify, icp_fit, segment, intent, the queue to route to | 360 ms warm |
| `deal_risk` | one deal and its events | at risk or not, the reasons, each event's labels | ~360 ms |
| `deals_at_risk` | the name of a ledger export | only the deals at risk, biggest first, with reasons | ~2 s for 20 deals |
| `triage_reply` | a reply, and who sent it if you have that | category, opt_out, meeting_intent, the route | ~380 ms |
| `meddpicc` | one call summary | all eight elements, forecast_ready, what to confirm, the gaps | ~380 ms |
| `dedup_pair` | two account records | same, related or different, p_same, the action | ~400 ms |

The first call on a fresh connection pays for the TLS handshake. Eight
`triage_lead` calls in a row through the server came back at 979 ms for the
first and a median of 360 ms for the rest. Every tool declares an output
schema, so clients get structured results and not a blob of JSON text.

Every tool loads its questions straight from the week folders. Change a
prompt in `week-02-deal-risk/src/spec.py` and the tool changes with it. That
also means any benchmark number in this repo describes what the tool
does, as long as you re-run the benchmark after changing a prompt.

None of the tools write anything. They return labels and probabilities and
leave the writing to the agent.

## How it fits into a real workflow

### A new inbound lead

```
form fill lands in the CRM
  -> enrichment server: headcount, title, company type
  -> triage_lead: disqualify, icp_fit, segment, intent, route
  -> CRM server: set owner and stage from the route
  -> only if the route is ae_now or sdr_sequence:
       the agent writes the first email and drafts it in Slack for the rep
```

`segment` reads headcount directly, so a lead that arrives with headcount
filled in gets segmented from a number instead of a guess. Run enrichment
first and pass the headcount through.

In week 01, 29 of 60 leads earned an email. The other 31 cost about four
thousandths of a cent each to reject or nurture, and no email tokens at all.

### The Monday risk sweep

```
activity database exports the week's ledger to JEV_LEDGER_DIR
  -> deals_at_risk: every deal checked, only the risky ones returned
  -> the agent reads those, checks each flag against the ledger,
     and writes a note to each owner
  -> Slack server: post the notes
```

I gave Claude Code a plain request:

> Which of our open deals are at risk? Our activity database exported this
> week's ledger to ledger.jsonl. Use 2026-09-25 as today. I want a short list
> for the Monday pipeline review, biggest first, one line each.

It called `deals_at_risk` once and came back with all eight at-risk deals
from the week 02 answer key, $1.145M, correct reasons. Then it added
something the tool didn't give it: Precision is the smallest deal and the
most urgent, because it closes in three days. Jev answered the 219
questions underneath, three for each of the 73 events, and the point about
Precision was the agent's own. It never opened the ledger, because
`deals_at_risk` reads the file itself.

### Replies to a sequence

```
reply lands in the sequencing tool
  -> triage_reply: category, opt_out, meeting_intent, route
  -> suppress: sequencing server pulls them from every sequence
  -> review: a person reads it
  -> pause or reroute: the agent pulls out the return date or the new contact
  -> book_meeting or send_info: the agent drafts the answer for the rep
```

Week 03 had two opt-out mistakes, one from Jev and one from Sonnet, and both
scored between 0.4 and 0.6. The tool sends that band to review. A reply that
says nothing but "STOP" is suppressed in code and never reaches Jev.

### After a sales call

```
call recorder posts the summary
  -> meddpicc: eight elements, forecast_ready, confirm, gaps
  -> CRM server: write the elements onto the opportunity
  -> gaps go to the AE as questions for the next call
  -> if confirm isn't empty, the agent reads the summary and checks
     those three fields before the deal moves to commit
```

`check.py` runs this on Pinecrest, the deal Jev wrongly put in the week 04
forecast. It still comes back forecast_ready, and confirm tells the agent
which three fields to check. Week 04 measured that split: Jev on every call
and a Sonnet check on the deals it marks ready made no false commits, at
about a quarter of what Sonnet costs on every call.

### Duplicate accounts

```
a job in code finds candidate pairs: a shared word in the name, a shared domain
  -> dedup_pair on each
  -> merge: CRM server merges the two
  -> link: CRM server sets the parent account
  -> review: a second look, by a person or by the agent with thinking on
  -> keep: nothing
```

In week 05 Jev got 48 of 50 pairs right with no wrong merges. Haiku and
Sonnet with thinking off both merged Google into Alphabet and were 0.95 sure
about it. Sonnet with thinking on got all 50, at about 470 times Jev's cost.
With Sonnet taking only Jev's review pile, every real duplicate got merged
for $2.81 per 1,000 pairs. So if the agent does the review itself, turn
thinking on.

## Do the fan-out inside the tool

The obvious way to build `deals_at_risk` is to let the agent loop: read the
ledger, call `deal_risk` once per deal, collect the answers. It works, and it
throws away most of the reason for having the server, because every event
still passes through the agent's context on the way in.

Measured on the week 02 ledger:

| | size |
|---|---|
| the ledger, as the agent would read it | 20,042 bytes |
| what `deals_at_risk` hands back | 669 bytes |

That's 30 times less for the agent to read, with 20 deals. The ledger grows
with the number of events, and the answer only grows with the number of
deals at risk, so the gap widens on a real pipeline.

So the tool reads the file itself, fans out to Jev on eight threads, applies
the rule in code, and returns only what someone should act on.

## Things I got wrong the first time

**The tool description sent the agent searching my filesystem.** The first
version said the file lived "inside the directory set by JEV_LEDGER_DIR".
Claude read that as an instruction to go and find it, and made four shell
calls first, one of them a `find /` across the whole disk. The description
now says to pass just the file name and that the server opens it. That took
the run from 7 turns to 4 and cut the searching to a single `ls`. It never got
to zero. The description is the only instruction the agent gets about a tool,
and it followed mine more literally than I meant it.

**A plain exception hid the reason from the agent.** When the path check
refused a file, I raised `ValueError`. The SDK treats that as unexpected,
logs a traceback, and sends the agent a blank failure it can't learn from.
`ToolError` from `mcp.server.mcpserver.exceptions` is the one for failures
you saw coming. The agent gets your message and can fix its call.

**The SDK moved under me.** `mcp` is on 2.x now. `FastMCP` became `MCPServer`
in `mcp.server.mcpserver`, and results use `structured_content` and
`is_error` where 1.x used camelCase. The server pins `mcp>=2.2,<3`.

**Returning a plain dict gave clients no structure.** The SDK decides whether
a tool has structured output from its return annotation, and `-> dict`
doesn't count. The results still arrived, as JSON text, which is why the
agent run above worked and why I didn't notice. Each tool now returns a
`TypedDict`, so there's an output schema and a structured result. `check.py`
fails if one goes missing, because my first version quietly fell back to
parsing the text and hid the problem.

**Asking the agent to do date arithmetic.** In week 02, Claude reviewing
Jev's flags decided an August 15 meeting fell inside a 30 day window ending
September 25. It was right about everything else. If your agent reviews
what these tools return, work out the day counts in code and pass them in.

## What it costs to run

Per call, from the benchmarks:

| | Jev | the same work on Sonnet 5 |
|---|---|---|
| one lead through `triage_lead` | $0.00004 | $0.0030 |
| one deal through `deal_risk` | $0.00012 | $0.0040 |
| one reply through `triage_reply` | $0.00003 | $0.0020 |
| one call summary through `meddpicc` | $0.00005 | $0.0037 |
| one pair through `dedup_pair` | $0.00003 | $0.0013 |
| a million ledger events a day | about $1,255 a month | about $70,500 a month |

The agent's own tokens come on top of that, and they're what the fan-out
rule keeps small.

## Limits

The tools use the week 02 rule as written: $100K for the exec rule, 30 days,
7 days to close. Those numbers suit the synthetic pipeline in this repo and
yours will want different ones. They're `EXEC_MIN_ARR`, `EXEC_WINDOW_DAYS`
and `CLOSING_SOON_DAYS` at the top of `week-02-deal-risk/src/spec.py`, and
they feed both the rule in code and the text Claude reads, so changing one
place changes both. Re-run the week 02 benchmark after you do.

`deals_at_risk` reads JSONL in the shape the week 02 ledger uses, one deal
per line with its events. Whatever your activity database exports, you'll
want a small step that reshapes it into that before the sweep.

The competitor list (Hexline, Corvid and Tallyworks, all made up) lives in
the prompt. Put yours in. Week 01 showed Jev won't work out who
your competitors are on its own.

`STOP_WORDS` in `week-03-reply-triage/src/spec.py` is four phrases, and it
only fires when the reply says nothing else. Add the ones your own replies
use.

`meddpicc` returns a champion level like the other seven, but in week 04 Jev
and Haiku both marked whoever attended the call as the champion. Don't let
that field drive anything automatic.

`dedup_pair` merges at 0.9, which is `AUTO_MERGE` in
`week-05-account-dedup/src/spec.py`. On week 05's pairs Jev never scored a
non-duplicate above 0.29 or a real one below 0.68, so there's room to lower
it. Wait until your own review pile has agreed with Jev for a while, because
50 pairs can't pick the number for you.
