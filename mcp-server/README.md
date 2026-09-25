# Using this from an agent

Each week in this repo ends with a pipeline that works. This folder puts those
pipelines behind an MCP server, so an agent that already talks to your GTM
tools can hand Jev the decisions instead of making them itself.

```
jev_server.py       the server, three tools
check.py            starts it the way an agent would and calls each tool
mcp.example.json    config to copy
```

## Why bother

A GTM agent in 2026 usually has a handful of MCP servers wired in. One for
the activity database (AckDB, in my case), one for whatever enrichment tool
fills in headcount, titles and funding, one for the CRM, one for Slack. The
agent pulls rows out of those and decides things about them. Is this lead
worth an AE. Is this deal slipping. Did that email come from someone senior.

Deciding is where the bill goes. Every row the agent looks at is frontier
model tokens, and most of those decisions are the typed kind Jev does at a
fraction of the price and a tenth of the latency. Week 01 and week 02 have
the numbers. This server is how you use them without rewriting your agent.

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

## The three tools

| tool | give it | get back | time |
|---|---|---|---|
| `triage_lead` | company, title, message, and headcount if you have it | disqualify, icp_fit, segment, intent, the queue to route to | 360 ms warm |
| `deal_risk` | one deal and its events | at risk or not, the reasons, each event's labels | ~360 ms |
| `deals_at_risk` | the name of a ledger export | only the deals at risk, biggest first, with reasons | ~2 s for 20 deals |

The first call on a fresh connection pays for the TLS handshake. Eight
`triage_lead` calls in a row through the server came back at 979 ms for the
first and a median of 360 ms for the rest. Every tool declares an output
schema, so clients get structured results and not a blob of JSON text.

All three load their questions straight from the week folders. Change a
prompt in `week-02-deal-risk/src/spec.py` and the tool changes with it. That
also means any benchmark number in this repo describes what the tool
actually does, as long as you re-run the benchmark after changing a prompt.

None of the tools write anything. They return labels and probabilities and
leave the writing to the agent, which is the split both weeks landed on.

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

The enrichment step matters more than it looks. `segment` reads headcount
directly, so a lead that arrives with headcount filled in gets segmented from
a number instead of a guess. Run enrichment first and pass the headcount
through.

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

Here's what happened when I pointed Claude Code at it with a plain request:

> Which of our open deals are at risk? Our activity database exported this
> week's ledger to ledger.jsonl. Use 2026-09-25 as today. I want a short list
> for the Monday pipeline review, biggest first, one line each.

It called `deals_at_risk` once and came back with all eight at-risk deals
from the week 02 answer key, $1.145M, correct reasons. Then it added
something the tool didn't give it: Precision is the smallest deal and the
most urgent, because it closes in three days. That's the split working. Jev
made 219 small decisions, and the agent spent its effort on the one call that
needed judgment.

It never opened the ledger, and that was a design decision in the tool.

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

That's with 20 deals. The ledger grows with the number of events. The answer
only grows with the number of deals at risk. On a real pipeline the gap gets
much bigger, and the agent's context stays small enough to leave room for the
part it's good at.

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
September 25. It was right about everything else. If your agent reviews what these
tools return, give it the numbers. Don't ask it to count days.

## What it costs to run

Per call, from the benchmarks:

| | Jev | the same work on Sonnet 5 |
|---|---|---|
| one lead through `triage_lead` | $0.00004 | $0.0030 |
| one deal through `deal_risk` | $0.00012 | $0.0040 |
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

The competitor list lives in the prompt, which is Hexline, Corvid and
Tallyworks, all made up. Put yours in. Week 01 showed Jev won't work out who
your competitors are on its own.
