# Week 03: triaging replies to outbound sequences

Every reply to a cold sequence needs sorting before anyone acts on it. Is
this person interested, out of office, the wrong contact, saying no, or
asking to be taken off the list? The last one is the only mistake here with
a legal cost, so it gets its own question.

60 replies, labelled by hand against [rubric.md](rubric.md). Three typed
questions per reply: category, opt-out, meeting intent. Routing runs in
code. Claude pulls out the return date or the new contact for the replies
that need one, because Jev can't return a date or a name.

## Results

| | Jev | Jev, 10 per request | Haiku 4.5 | Sonnet 5 |
|---|---|---|---|---|
| opt-outs still emailed | 1 of 9 | 0 of 9 | 0 of 9 | 0 of 9 |
| suppressed, never asked | 0 | 0 | 0 | 1 |
| interested, routed away | 0 of 12 | 1 of 12 | 0 of 12 | 0 of 12 |
| sent to a person | 0 | 0 | 6 | 0 |
| route | **98.3%** | 96.7% | 88.3% | 95.0% |
| | | | | |
| category | **100%** | 95.0% | 88.3% | 96.7% |
| opt_out | 98.3% | 100% | 100% | 98.3% |
| meeting intent, exact | 83.3% | 73.3% | **98.3%** | 96.7% |
| | | | | |
| all 60, sequential | 22.3 s | **2.9 s** | 119.4 s | 141.2 s |
| per request, p50 | 365 ms | 449 ms | 1,930 ms | 2,200 ms |
| per 1,000 replies | $0.033 | **$0.024** | $0.699 | $2.018 |

Jev, batched Jev and Sonnet route at least 95% of replies correctly. Haiku
gets 88%, for a reason covered below.

## Both opt-out mistakes scored between 0.4 and 0.6

Jev missed one opt-out. It was R31, a reply that just says "STOP", scored
0.41. Sonnet suppressed someone who never asked. That was R40, a sarcastic
"Great, the fifth email this week", scored 0.50 exactly.

Week 02 ended with a rule: send anything between 0.4 and 0.6 to a person.
On a different task it catches both mistakes, Jev's and Sonnet's.

"STOP" also shouldn't reach a model at all. Opt-out keywords are a short,
fixed list, and matching them is a job for code. Run it before the model
and the model only sees the replies worth thinking about.

## Haiku answered the wrong question six times

For six interested replies Haiku put a meeting intent level in the category
field, answering "curious" or "ready" where it should have said
"interested". My routing code first let anything it didn't recognise fall
through to the interested branch, so those six still landed in the right
place and Haiku scored 98.3%. Unparseable answers now go to a person, and
Haiku's real number is 88.3%.

Jev can't make this mistake. A choice question comes back as one of the
keys it was given.

## Batching unrelated replies costs a little accuracy

Ten replies per request took all 60 from 22 seconds to 3 and cut the cost
by a quarter. Category accuracy fell from 100% to 95% and exact meeting
intent from 83% to 73%. Week 02's batching helped because a deal's events
share context. These replies share nothing, so batching could only cost
accuracy. For a high-volume inbox the speed may be worth it.

## Jev's score answers run high, third week running

Meeting intent is a `score` question. All 10 of Jev's misses on it were too
high, and all 16 when batched. Weeks 01 and 02 showed the same thing on
intent and severity. Haiku and Sonnet missed high too, once and twice.

All ten were not-now or out-of-office replies that should have been `none`.
Jev read "Try me in January" as open to a meeting. None of the ten changed a
route, because for those replies the category decides where they go. It
starts to matter when a threshold sits on the level Jev inflates, which is
what week 04 tests.

## Pulling out return dates and new contacts

Jev routed 17 replies to pause or reroute. Claude read only those and pulled
out the return date or the new contact.

| | right | cost for all 17 | mean |
|---|---|---|---|
| Haiku 4.5 | **17 of 17** | $0.0062 | 1,970 ms |
| Sonnet 5 | 15 of 17 | $0.0160 | 2,368 ms |

Both read "back on 10/08" as October 8 and "out until the 6th", sent on
September 28, as October 6. Sonnet's two misses were R46 and R51, away
messages that also name a backup contact. It returned the backup contact and
left the return date empty. Haiku got both, for less than half the price.

## What I'd ship

```
reply lands -> opt-out keywords, in code
            -> Jev: category, opt_out, meeting_intent
            -> opt_out between 0.4 and 0.6 goes to a person
            -> route in code
pause or reroute only -> Haiku pulls out the date or the contact
```

## Running it

```bash
cd week-03-reply-triage
python3 src/replies.py      # builds data/replies.jsonl from the labelled source
python3 src/bench.py        # all four setups, about 17 minutes, almost all Claude
python3 src/extract.py      # the date and contact step
python3 src/score.py
```

Needs `TYPESAFE_API_KEY` and a logged-in `claude` CLI. Claude runs with week
01's three corrections, now in `common/claude.py`.

60 replies is small. One reply is 1.7 points, so read the gaps between the
top three setups as ties and the specific mistakes as the finding.
