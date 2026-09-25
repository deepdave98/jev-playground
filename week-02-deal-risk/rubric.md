# How the answer key was written

73 events across 20 open deals, every label by hand. The rules below are the
same strings the models get, so if you disagree with a label you are
disagreeing with a rule you can see, and you can change it in
`src/ledger.py` and rerun.

Today is 2026-09-25 for the whole benchmark. It matters for two rules that
count days.

## The deals

Twenty deals, $2.79M of pipeline. Eight are at risk ($1.145M) and twelve are
healthy. The first five are the deals on AckDB's at-risk demo screen, rebuilt
as full ledgers. The rest are made up, as is every person in the set.

The seller is never named. The three competitors are Hexline, Corvid and
Tallyworks, which are invented, and both models are told who they are.
Last week Jev couldn't recognise Clay or Apollo as competitors even when the
prompt named them. That was worth knowing once. It isn't what this week is
testing.

## Three questions per event

### signal

What the event tells you about the deal. Exactly one of these.

| signal | means |
|---|---|
| `competitor` | the account is considering, trialling or comparing a competitor, or has picked one |
| `escalation` | a support problem: a bug, an outage, a complaint, an escalated ticket |
| `champion_exit` | our champion or sponsor has left, is leaving, or has been moved off the project |
| `stall` | budget cut or frozen, seats reduced, close date pushed, procurement or legal stuck |
| `momentum` | something that makes the deal likelier to close or grow |
| `routine` | normal activity that changes nothing |

The traps are the edges between these, which is where real ledgers get
confusing:

- A customer who names a competitor to say they rejected it (E036, Lumen
  Health) is `momentum`. They told you why they're choosing you.
- Someone who isn't the champion leaving the company (E048, a support agent
  at Oakridge) is `routine`. The champion's name is on the deal record.
- A champion promoted inside the account (E044, Pinecrest) is `momentum`. He
  said so himself two events later: the promotion came with budget authority.
- A how-to ticket (E031, E073) is `routine`. Nothing is broken.
- Layoffs at the customer where the team says the renewal is protected (E072,
  Driftwood) is `stall`, severity `watch`. It's worth knowing about, and it
  isn't a problem yet.

### severity

How much this one event threatens the deal: `none`, `watch`, `serious`,
`critical`. Good news is always `none`. Only E033 is critical, the Keystone VP
writing to say they've gone with Corvid.

E066 is the one I expect models to get wrong. The Northgate Chief Customer
Officer writes "I need this live by November 15 or we have a problem." Read
quickly, it sounds like a threat. Read properly, she's pushing to buy faster
and asking what we need from her. It's `momentum`, severity `none`.

### exec_engaged

Did a senior person at the customer take an active part? Senior means VP and
above, any C-level title, President or Founder. Directors, heads of
department, managers and leads do not count. Neither does being cc'd, being
mentioned, or changing jobs.

This is the question with the most money on it, because it drives the one
reason no single event can show: no exec involvement in 30 days. Three events
are built around it:

- E004, Datacore: the CTO is cc'd on an email. That isn't engagement, so the
  last real exec contact is the meeting 41 days earlier, and the $185K deal is
  at risk.
- E051, Summit Labs: a VP is cc'd, but he ran a meeting twelve days before,
  so the deal is fine.
- E068, Silverline: the SVP sponsor call was 29 days before today. One day
  inside the window, on the biggest deal in the set.

There's a structural trap in here too. Several emails come from execs whose
title only appears in an earlier event. E026 is from Grace Liu, and you only
know she's the CFO from the meeting in E025. Anything judging one event at a
time can't know that.

## From events to a verdict

`spec.assess()` turns the judged events into reasons. The same function runs
over the answer key and over every model's labels. Nobody is asked to apply
it except the one run that reads whole ledgers.

| reason | fires when |
|---|---|
| `competitor` | 2+ competitor events at `watch` or worse, or one `critical` |
| `escalations` | 2+ escalations at `serious` or worse, or one `critical` |
| `champion_left` | a `champion_exit` at `serious` or worse |
| `stalled` | a `stall` at `serious` or worse |
| `no_exec_30d` | deal is $100K or more and no `exec_engaged` event in 30 days |
| `closing_with_issues` | closes within 7 days with anything `serious` open |

It checks the signal before it looks at severity, which turned out to matter.
A model that rates a page visit as `watch` can't raise an alarm with it,
because routine events never count.

## What the eight at-risk deals should say

| deal | ARR | reasons |
|---|---|---|
| Ironbridge | $240K | competitor mentioned x2 |
| Keystone | $210K | competitor mentioned x2 |
| Datacore | $185K | no exec engagement in 30d |
| Halcyon | $150K | budget or timing slipped |
| Vantage | $128K | champion left |
| Cloudmark | $94K | 2 tickets escalated |
| Tidewater | $76K | budget or timing slipped |
| Precision | $62K | 3 tickets escalated, closes in 3d with open issues |

`src/ledger.py` checks that the rule over my labels produces exactly this
before it writes the dataset. If I mislabel an event it refuses to build,
which is how that kind of mistake gets caught before it moves a number.

## Distribution

| label | counts |
|---|---|
| signal | 32 momentum, 21 routine, 8 escalation, 5 competitor, 5 stall, 2 champion_exit |
| severity | 53 none, 6 watch, 13 serious, 1 critical |
| exec_engaged | 17 true, 56 false |

`champion_exit` has two examples, both on Vantage. Treat anything about that
class as an anecdote.
