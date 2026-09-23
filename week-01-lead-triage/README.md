# Week 01: inbound lead triage and routing

A lead fills in a form. Six things have to happen before a rep sees it.

1. Is this a real lead, or a job applicant, a student, an agency, a competitor,
   or spam?
2. Are they in our ICP?
3. What segment are they?
4. How much buying intent is in what they wrote?
5. Which queue do they go in?
6. Write the first email.

Steps 1 to 4 are judgments. Step 5 is a rule. Step 6 is writing. I gave the
judgments to Jev and to two Claude models, ran the rule in code for everyone,
and gave the writing to Claude because Jev cannot do it.

60 hand-labelled leads. The answer key and the rules behind it are in
[rubric.md](rubric.md). Every raw response is in
[results/raw/](results/raw/), including the wrong ones.

## The result

| | Jev | Haiku 4.5 | Haiku 4.5, split | Sonnet 5 |
|---|---|---|---|---|
| **route accuracy** | **90.0%** | 53.3% | 61.7% | 78.3% |
| all four judgments right | 71.7% | 38.3% | 45.0% | 63.3% |
| funded buyers binned | **0 of 16** | 7 of 16 | 6 of 16 | 1 of 16 |
| disqualified leads let through | 2 of 12 | 1 of 12 | 1 of 12 | 1 of 12 |
| | | | | |
| latency p50 | **366 ms** | 2,630 ms | 13,631 ms | 2,571 ms |
| latency p90 | 417 ms | 2,868 ms | 16,086 ms | 4,055 ms |
| latency p99 | 507 ms | 6,091 ms | 17,738 ms | 5,752 ms |
| API calls per lead | 1 | 1 | 4 | 1 |
| **cost per 1,000 leads** | **$0.042** | $1.339 | $3.933 | $3.006 |
| | | | | |
| disqualify | 96.7% | 58.3% | 66.7% | 86.7% |
| icp_fit | 95.0% | 51.7% | 71.7% | 85.0% |
| segment | 100% | 95.0% | 98.3% | 100% |
| intent | 75.0% | 83.3% | 81.7% | 81.7% |
| | | | | |
| Brier, disqualify | **0.041** | 0.365 | 0.281 | 0.130 |
| Brier, icp_fit | **0.041** | 0.383 | 0.216 | 0.130 |
| failed calls | 0 | 0 | 0 | 0 |

Against the closest Claude model on quality, Jev routed 90% correctly to
Sonnet's 78%, ran about 7 times faster, and cost about 70 times less.

The row I care about most is "funded buyers binned". Those are leads with
budget, a timeline and a seat count who got dropped in the reject pile.
Haiku did that to 7 of the 16. Accuracy percentages hide that. A VP of Sales
will not.

## What I had to fix before any of this was fair

Three things, all of which made Claude look worse than it is. I am listing
them because the first version of this table was wrong and someone should be
able to check my work.

**Extended thinking was on.** The Claude CLI enables it by default. Haiku
was spending about 1,800 thinking tokens and 22 seconds per lead working out
whether a resume was a resume. Setting `MAX_THINKING_TOKENS=0` took the same
call to 2.6 seconds. Nobody would ship lead triage with thinking on, so
benchmarking it that way would have been dishonest by a factor of 23.

**Prompt caching was billed at list price.** Sonnet's CLI caches the system
prompt, so its real token count lands in `cache_creation` and `cache_read`,
not `input_tokens`. I was charging cache reads at full input price. Cache
writes bill at 1.25x and reads at 0.1x, and Claude gets credit for that now.

**The overhead calibration was reading the wrong field.** Because of the
caching above, my measurement of the CLI's own scaffolding came back as 2
tokens for Sonnet instead of 2,214, so Claude was being billed for a prompt
it did not write. Sonnet's cost per thousand dropped from $7.71 to $3.01
when I fixed it.

Both prompts are generated from [one shared spec file](src/spec.py). Jev gets
the criteria as typed questions, Claude gets the same strings rendered as
text. Neither sees wording the other did not see.

## "You strawmanned Claude by asking four questions at once"

This was my first thought too, and it is worth taking seriously, because
Haiku's errors were obviously correlated. All 29 of its icp_fit errors ran
the same direction, and they lined up with 27 over-disqualifications. It was
deciding "bad lead" once and writing that answer into both fields.

So I ran it again with one call per question, four calls per lead, each with
its own prompt and no knowledge of the others.
[src/split_runner.py](src/split_runner.py).

It helped. icp_fit went from 51.7% to 71.7%, route accuracy from 53.3% to
61.7%, and the Brier score nearly halved. The conflation was real.

It also cost 5.2 times the latency and 2.9 times the money, and it still lost
to Jev by 28 points.

At 18 leads in, the split run was sitting at 88.9% and I thought it had
closed the gap. At 60 leads it was 61.7%. If you run your own version of
this, do not read the partial.

## Where Jev loses

**Intent, by a lot.** 75% against Sonnet's 82%, and it is Jev's worst
number. 15 errors, 14 of them off by exactly one level, and every single one
in the same direction: it reads leads as keener than they are. `none` becomes
`researching`, `researching` becomes `evaluating`, `evaluating` becomes
`ready_to_buy`. So it runs about half a level hot, consistently enough that
a threshold shift fixes it. You do not need a different model.

**It does not know who your competitors are.** Jev's two disqualify misses
were L009 and L010, a RevOps manager at Clay and a PM at Apollo.io, both
written to look like ordinary demo requests. Jev waved both through at 0.06
and 0.18. Those are the two most expensive misses in the set.

So in round 2 I added one sentence naming the competitor set, Clay, Apollo,
ZoomInfo, Outreach and Salesloft, to both models' prompts and changed nothing
else.

| on the two competitor leads | Jev v1 | Jev v2 | Sonnet v1 | Sonnet v2 |
|---|---|---|---|---|
| Clay (L009) | 0.06 | 0.27 | 0.03 | **0.95** |
| Apollo (L010) | 0.18 | 0.23 | 0.85 | **0.97** |

Sonnet took the fact and used it. Both leads flipped, and its overall
disqualify accuracy went from 86.7% to 90.0%. Jev moved in the right
direction and never crossed the line. Round 2 left Jev's route accuracy at
exactly 90.0%, unchanged.

That is the sharpest difference I found all week. Jev applies a rubric you
describe to it. It has no idea what Clay and Apollo actually are, so naming
them bought almost nothing. Claude already knows both companies, so one
sentence was enough to flip it.

Neither of them should be doing this job. A competitor check is a domain
lookup against a list your CRO already maintains. It belongs in code, and
both models are the wrong tool for it.

## Step 6, which Jev cannot do

Jev has three question types: `choice`, `score` and `noul`. There is no text
type. Asking for one returns a 400:

```
$ python3 src/step6_email.py --prove
asking Jev for a `text` question type -> HTTP 400
{"detail":{"error_type":"api_usage_error","message":"Invalid request."}}
```

So Sonnet writes the emails, conditioned on the judgments Jev already made.
29 of the 60 leads earned one, at a mean of 4,052 ms and $0.0026 each. The
other 31 got rejected or dropped into nurture and cost nothing to write to.

The output is good. Here is the Siemens one, which came in with a Q1
deadline, 400 seats and a security review:

> **Subject: SOC 2 Type II, VPAT, and your Q1 timeline**
>
> Given the end-of-Q1 close and 400 seats, let's get security and procurement
> moving in parallel. We have SOC 2 Type II report and VPAT ready to share
> now, plus a standard enterprise MSA our legal team can turn around fast.
>
> Can we get 20 minutes this week with you and whoever leads procurement to
> map out the path to paper?

That gating is where the saving comes from. Jev works out which leads
justify a Claude call, and 31 of the 60 never reach one.

| per 1,000 inbound leads | triage | emails | total |
|---|---|---|---|
| Jev triage, Sonnet writes | $0.042 | $1.27 | **$1.31** |
| Sonnet does both | $3.006 | $1.27 | $4.28 |

3.3x cheaper end to end, and the saving gets bigger the worse your inbound
is, because the junk never reaches the expensive step.

Two quirks in step 6. The prompt says "no em dashes" and 10
of the 29 emails have one anyway, so if you care about house style you are
post-processing regardless. And the emails come out signed with a name that
was never in my prompt, which means the CLI is leaking something from the
environment. Neither affects the triage numbers, since none of the four
judgments depends on a signature.

One of the 29 emails went to L009, the RevOps manager at Clay. That is Jev's
competitor miss turning into a warm, specific, well-written email to a
competitor. Worth keeping in mind when you read the 90%.

## What I would ship

```
every lead      -> domain blocklist         free, instant, exact
                -> Jev, four typed questions  366 ms, $0.042 per 1,000
                -> route in code              free, five branches, testable
qualified only  -> Sonnet writes the email
```

Four notes on that.

The blocklist goes first because it is the one step with a right answer that
does not need a model at all.

Routing stays in code. Five branches, free, instant, and you can unit test
it. The models are there for the four fuzzy judgments underneath. A model
call spent on a branch is a failure mode you paid for.

Jev's calibration is the part I did not expect to care about. A Brier score
of 0.041 against Sonnet's 0.130 means the probability it hands back is worth
something. You can send everything over 0.9 straight through and queue the
0.4 to 0.6 band for a human, which is a real workflow you cannot build on a
number a model made up to sound confident.

And send the intent score to a human review queue until you have recalibrated
it, because it runs half a level hot.

## Running it

```bash
cd week-01-lead-triage
python3 src/build_dataset.py          # rebuild leads.jsonl from the labelled source
python3 src/bench.py                  # all three runners, ~25 min
python3 src/bench.py --variant=v2     # round 2, competitors named
python3 src/split_runner.py claude-haiku-4-5 --resume
python3 src/step6_email.py            # the emails
python3 src/score.py                  # the tables
```

Needs `TYPESAFE_API_KEY` and a logged-in `claude` CLI. Standard library only.

The runs are sequential on purpose. Running them concurrently finishes sooner
and makes every latency number meaningless.

## Caveats

One laptop, one location, one afternoon, 60 leads.

Latency depends on where you sit relative to the API. Jev's first call
measured 970 ms; about 600 ms of that was the TLS handshake and about 290 ms
was round trip time, leaving roughly 80 ms of actual inference. The numbers
above reuse the connection, so they carry one round trip each. Run it from
your own machine and you will get different wall clock and the same ratio.

60 cases gives roughly plus or minus 8 points at 90% confidence. The 12 point
gap between Jev and Sonnet is probably real. The 2 point move from naming the
competitors is probably not.

Claude went through the CLI rather than the API, because there was no
`ANTHROPIC_API_KEY` on this machine. Latency is `duration_api_ms`, which
excludes process startup, and token counts have the measured CLI scaffolding
subtracted. Both choices favour Claude. If you have an API key, wire it in
and the numbers should move slightly in Claude's favour again.

Cost is the number I trust most, because it is measured token counts against
published list prices, and the ratio is large enough that none of this
changes the answer.
