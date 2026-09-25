# Week 02: which deals are at risk, from an AckDB activity ledger

AckDB's demo has a screen that says "8 deals at risk · $1.2M", with a reason
next to each one. Champion left. Competitor mentioned twice. Two tickets
escalated. No exec calls in 30 days.

Every one of those reasons has to be earned from events. Something has to
decide that a Zendesk ticket counts as an escalation, that the person who
left on LinkedIn was the champion, that a VP took part in the meeting rather
than being cc'd on the follow-up. On a live ledger that's thousands of small
decisions a day, which is the work Jev was built for.

So this week: 20 open deals, 73 events in AckDB's ledger format, three typed
judgments per event, a rule in code that turns them into reasons, and Claude
at the end writing the note to the deal owner. The first five deals are the
ones from AckDB's demo screen, rebuilt as full ledgers.

The answer key is hand-written against [rubric.md](rubric.md). Every raw
response is in [results/raw/](results/raw/).

## The six setups

The same work can be split up in different ways, and the split turned out to
matter as much as the model.

| setup | what it does | calls |
|---|---|---|
| `jev` | one request per event, three questions each | 73 |
| `jev-per-deal` | one request per deal, all its events asked about at once | 20 |
| `claude-haiku-4-5` | one call per event, same three questions | 73 |
| `claude-sonnet-5` | one call per event, same three questions | 73 |
| `claude-sonnet-5-per-deal` | one call per deal, labels every event in one answer | 20 |
| `claude-sonnet-5-ledger` | one call per deal, reads the ledger and says at risk or not | 20 |

The last one is how most people would use Claude for this, so it's in there.
All the others hand their event labels to the same `spec.assess()` function
the answer key goes through.

## Results

| | jev | jev per deal | haiku 4.5 | sonnet 5 | sonnet per deal | sonnet ledger |
|---|---|---|---|---|---|---|
| at-risk deals caught | 8 of 8 | 8 of 8 | 8 of 8 | 8 of 8 | 8 of 8 | 8 of 8 |
| false alarms | 1 | 1 | 3 | 1 | **0** | 6 |
| deal accuracy | 95% | 95% | 85% | 95% | **100%** | 70% |
| reasons exactly right | 8 of 8 | 8 of 8 | 8 of 8 | 8 of 8 | 6 of 8 | 6 of 8 |
| | | | | | | |
| whole ledger, sequential | 25.6 s | **7.3 s** | 191.6 s | 224.3 s | 75.1 s | 67.5 s |
| per call, p50 | 347 ms | 355 ms | 2,404 ms | 2,703 ms | 3,307 ms | 3,004 ms |
| cost, whole ledger | $0.0031 | **$0.0023** | $0.0622 | $0.1716 | $0.0806 | $0.0566 |
| | | | | | | |
| signal | 91.8% | 89.0% | 91.8% | 87.7% | 90.4% | |
| severity, exact | 67.1% | 63.0% | 87.7% | 87.7% | 87.7% | |
| severity, within one level | 97.3% | 98.6% | 97.3% | 97.3% | 98.6% | |
| exec_engaged | 94.5% | 98.6% | 94.5% | 94.5% | 98.6% | |
| Brier, exec_engaged | 0.046 | **0.009** | 0.055 | 0.057 | 0.016 | |

Nobody missed an at-risk deal. All six caught the full $1.145M. This task
turned out easier than last week's, mostly because the competitor names were
in the prompt from the start. What separates the setups
is false alarms, cost and time.

The best accuracy was Sonnet labelling each deal in one call: 20 of 20. Jev
doing the same job per deal got 19 of 20, 35 times cheaper and 10 times
faster.

## Three models, the same four misses

When each event is judged on its own, Jev, Haiku and Sonnet all score exactly
94.5% on exec_engaged, and all three get the same four events wrong: E026,
E033, E046 and E055.

All four are messages from an exec whose title only shows up in an earlier
event. E026 is an email from Grace Liu. You know she's the CFO because the
meeting in E025 says so. A model looking at E026 alone has no way to know,
and a better model wouldn't help, because the title isn't in the event.

Give the model the whole deal and they mostly go away. Jev per deal gets all
four right. Sonnet per deal gets three of them, still missing Rachel Kim's
edit to the Pinecrest order form. Both land at 98.6% with one miss each.

This is the finding I'd take to anyone designing one of these pipelines. If
a judgment depends on who someone is, and who they are gets established
elsewhere in the ledger, per-event classification has a ceiling. Batch by
entity.

## Claude applying the rule is worse than code applying it

Same model, same ledger. When Sonnet labels events and code applies the risk
rule, it gets 20 of 20. When Sonnet reads the ledger and applies the rule
itself, it gets 14 of 20.

All six of its false alarms are `no_exec_30d`, the one rule with a threshold
and date arithmetic in it. Three were on deals under $100K, which that rule
excludes (Marlow, Oakridge, Fairhaven). The other three had an exec engaged
12, 17 and 29 days before today. Counting the two at-risk deals where it
tacked the same reason on anyway, it got `no_exec_30d` wrong on 8 of 20.

Week 01 said routing should live in code because it's a rule. This is the
same point with a number on it: the same model scored 100% one way and 70%
the other.

## Where Jev loses

**Severity runs high. Second week in a row.** Jev's exact severity is 63 to
67% against Claude's 88%, and almost every miss goes the same way: 21 of 24
per event and 24 of 27 per deal rate the event as more threatening than it
is. Last week its intent scores ran high in exactly the
same way. Both are `score` questions. If you use Jev's score type, expect
about half a level of upward bias and correct for it.

It didn't cost Jev a single false alarm here, which comes down to how the
rule is written. The rule looks at the signal before the severity, so a page
visit rated `watch` still can't raise an alarm. Put the category check before
the magnitude check in your own rules and the bias stops mattering this much.

**It doesn't check who left.** E048 is a support agent leaving Oakridge.
The deal record names the champion, and it's someone else. Jev per event
called it `champion_exit`, serious, and raised a false alarm. So did Haiku.
Sonnet compared the names and called it routine both times. Checking a fact
against the record is Claude's strength, same as last week.

**Its one per-deal false alarm was a coin flip.** Silverline is the biggest
deal in the set at $300K. The SVP sponsor call scored `p_exec = 0.49`, one
hundredth under the line, and the deal got flagged for no exec engagement.
A hard 0.5 cutoff turned an honest "I don't know" into an alarm. Route
anything between 0.4 and 0.6 to a person instead.

## The trap that caught Sonnet

E066 is the Northgate Chief Customer Officer: "I need this live by November
15 or we have a problem. What do you need from us to get there?" She's
pushing to buy faster.

Haiku called it momentum, severity none. Exactly right. Sonnet per event
called it a stall at serious and raised a false alarm on a healthy $160K
deal. Jev got the signal right and then rated it serious anyway, which is the
severity bias again.

## The last step, and the mistake it made first

Jev can't write the note to the deal owner, so Claude does. It only sees the
9 deals Jev flagged, with the full ledger and Jev's reasons, and it has to
say whether each flag holds up before writing anything.

The first version got 8 of 9. It correctly threw out Silverline, Jev's false
alarm. Then it also threw out Datacore, which really is at risk. Here's why,
in its own words:

> Ingrid Solberg, CTO, actively engaged on August 15 [...] all within the
> 30-day window.

August 15 is 41 days before September 25. It had fixed a false alarm by
introducing a missed deal, and missing a real $185K risk is the worse of the
two errors.

So the second version passes it the arithmetic, worked out in code: whether
the deal clears $100K, days to close, and when Jev last saw a senior person
take part. Claude can still argue about the judgment calls, and it did. It
overruled the code on Silverline, correctly, by pointing at the SVP call. It
just doesn't get to do the subtraction anymore.

9 of 9. The Datacore note now reads:

> Ingrid Solberg (CTO) hasn't been actively engaged since the Aug 15 exec
> alignment call, 41 days ago; the Sep 17 email just cc'd her with no action,
> which doesn't count. [...] Get Ingrid back into a live conversation this
> week, ideally tied to the pilot results Rafael just shared.

## What it costs to get to 100%

| | deal accuracy | cost | time, sequential |
|---|---|---|---|
| Sonnet per deal, on every deal | 100% | $0.0806 | 75.1 s |
| Jev per deal, then Claude reviews the 9 flagged | 100% | $0.0399 | 52.1 s |
| Jev per deal alone | 95% | $0.0023 | 7.3 s |

The hybrid costs half as much as Sonnet on its own at the same accuracy. Most
of that saving comes from Claude never opening the 11 healthy deals. Review
cost scales with how many deals get flagged. This set is 40% at risk, which
is far more than a real pipeline, so on real data the gap should be wider.

## At the volume AckDB is drawn for

The AckDB architecture diagram is labelled for a million events a day. From
the measured per-event costs above:

| classifying every event as it lands | per day | per month | calls in flight at p50 |
|---|---|---|---|
| Jev | $41.82 | $1,255 | about 4 |
| Haiku 4.5 | $852.17 | $25,565 | about 28 |
| Sonnet 5 | $2,350.10 | $70,503 | about 31 |

That's linear extrapolation from 73 events, so treat it as a sense of scale.
The per-token prices are published and the token counts are measured, so the
ratio holds.

## What I would ship

```
event lands in AckDB  -> Jev, three typed questions, batched per deal
                      -> spec.assess() in code, all the thresholds and dates
flagged deals only    -> Claude checks the flag against the ledger,
                         with the arithmetic handed to it, then writes the note
```

Three rules from this week:

1. Batch by deal. Per-event judgment can't see what earlier events
   established, and it costs more round trips.
2. Keep arithmetic out of prompts. Thresholds, date windows, counts. Every
   model error in this benchmark that involved a number was a model doing
   maths it should have been given.
3. Treat Jev's probabilities as a band. 0.49 and 0.51 are the same answer.

The [MCP server](../mcp-server/) wraps this whole pipeline as a tool, so an
agent can run the sweep without reading the ledger itself.

## Running it

```bash
cd week-02-deal-risk
python3 src/ledger.py          # builds the ledger, checks the labels against the rule
python3 src/bench.py           # all six setups, about an hour, almost all of it Claude
python3 src/brief.py --facts   # Claude reviews what Jev flagged
python3 src/score.py
```

`TYPESAFE_API_KEY` in `.env.local`, and a logged-in `claude` CLI. Standard
library only.

Claude goes through the CLI with the same three corrections as week 01:
thinking off, the CLI's own scaffolding measured and subtracted, cache reads
billed at the cache rate. The CLI's scaffolding came to 2,822 tokens for
Haiku and 3,823 for Sonnet this time, both subtracted.

## Caveats

20 deals and 73 events is small. At the deal level one deal is five points,
so 95% and 100% are one deal apart. The architecture finding is the sturdiest
thing here, since three different models produced identical misses for a
reason you can read off the events.

The ledger is synthetic. It follows AckDB's event format and the reasons on
AckDB's demo screen, but a real ledger is messier, with duplicate events,
half-empty meeting summaries and timezones. I'd expect every setup to lose
some accuracy on real data, with per-event labelling losing the most, because
the context it lacks is exactly what real data scatters around.

One laptop, one afternoon. Latency depends on where you are. Cost doesn't.
