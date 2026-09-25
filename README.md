# jev playground

Every week I build something real with [Jev](https://www.typesafe.ai/) and put
the numbers here.

Jev is TypeSafe AI's typed decision model. You send it state and typed
questions, it sends back a choice, a score, or a probability with a
confidence attached. There is no text output at all. Input bills at $42 per
billion tokens and output is free, since the output is a label and a number.

Whether Jev beats Claude is a boring question. The useful one is which steps
of a real workflow are decisions, which are writing, and what happens to your
latency and your bill when you stop paying a frontier model to do the
decisions. Each week here measures that on something I would ship.

## Weeks

| week | use case | headline |
|---|---|---|
| [01](week-01-lead-triage/) | Inbound lead triage and routing | Jev routed 90% of leads correctly at 366ms and $0.04 per thousand. Sonnet 5 got 78% at 2.6s and $3.01. Haiku 4.5 binned 7 of 16 funded buyers. Then Sonnet wrote the emails, because Jev structurally cannot. |
| [02](week-02-deal-risk/) | Deal risk from an AckDB activity ledger | Every setup caught all 8 at-risk deals. Jev did the whole ledger in 7.3s for $0.0023 with one false alarm. Sonnet had none, at 35 times the cost. Asked to apply the rule itself, Sonnet dropped from 100% to 70%. |

## Using it from an agent

[mcp-server/](mcp-server/) puts both weeks behind an MCP server with three
tools: `triage_lead`, `deal_risk` and `deals_at_risk`. Add it next to the
servers your agent already uses for enrichment, the CRM and Slack, and Jev
takes the typed decisions off the agent. The README in there has setup, two
worked workflows, and the mistakes I made building it.

## House rules for the benchmarks

These are the rules I hold myself to. They are why the numbers here come out
lower than the ones in the launch posts.

**The answer key is written by hand.** If a model writes the labels, then
scoring that model against them measures self-agreement and quietly penalises
every other model for disagreeing. Every label in here is hand-written
against a published rubric you can argue with.

**Both sides get the same words.** The prompts are generated from one shared
spec file. Jev gets the criteria as typed questions, Claude gets the same
strings rendered as text. Nobody gets a hint the other did not get.

**Fix the unfair thing even when it helps the other side.** Week 01 started
with Claude burning 1,800 thinking tokens and 22 seconds per lead because the
CLI turns thinking on by default. Publishing that would have been a lie.
Turning it off took Claude from 22 seconds to 2.6. Same for prompt caching,
which was being billed at full price until I caught it.

**Measure the network, not just the model.** Jev's first call from my laptop
looked like 970ms. About 600ms of that was the TLS handshake and about 290ms
was round trip time to their API. The model was doing roughly 80ms of work.
Every latency number here says which is which.

**Publish the failures.** Every raw response is committed, including the
wrong ones. If a number looks too good, go read `results/raw/`.

**Say where the other thing wins.** Jev cannot write an email. Week 01 asks
the live API to and shows the HTTP 400.

## Running any of this

You need a TypeSafe API key and either an Anthropic API key or the `claude`
CLI logged in.

```bash
cp .env.example .env.local     # add your TYPESAFE_API_KEY
cd week-01-lead-triage
python3 src/build_dataset.py   # regenerates the dataset from the labelled source
python3 src/bench.py           # runs every model over every lead
python3 src/score.py           # prints the tables
```

Each week has its own run steps in its README. The benchmarks use nothing
beyond the Python standard library. The MCP server needs
[uv](https://docs.astral.sh/uv/), which fetches the MCP SDK on first run.

## A caveat on my numbers

Each week runs from one laptop in one place on one afternoon, on a small
hand-labelled set: 60 leads in week 01, 20 deals and 73 events in week 02.
Latency depends heavily on where you are relative to the API. Accuracy on
sets this size has a wide confidence interval, roughly plus or minus 8 points
at 90% on 60 cases and one deal is five points on 20. The cost numbers are
the solid ones, since those are token counts against published rates.

Take the shape of the result, not the third decimal place.
