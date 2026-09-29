# Week 04: filling in MEDDPICC from call summaries

Every AE is supposed to update MEDDPICC after a call, and almost nobody
does. The call recorder already has a summary. This week reads it and fills
the eight fields: metrics, economic buyer, decision criteria, decision
process, paper process, pain, champion and competition, each as none,
mentioned or established.

The number that matters is the forecast. A deal goes in only when metrics,
economic buyer and decision process are all established, so a model that
reads a field one level too high puts an unready deal in the forecast.

16 call summaries, 128 labels, written by hand against
[rubric.md](rubric.md). One request per call with all eight fields in it.

## Results

| | Jev | Jev, corrected | Haiku 4.5 | Sonnet 5 |
|---|---|---|---|---|
| put in forecast, shouldn't be | 1 | 1 | 0 | 0 |
| left out, should be in | 0 of 3 | 0 of 3 | 0 of 3 | 0 of 3 |
| elements, exact | 74.2% | 83.6% | 79.7% | **90.6%** |
| elements, within one | 93.8% | 98.4% | 96.1% | **100%** |
| overstated / understated | 33 / 0 | 20 / 1 | 25 / 1 | 9 / 3 |
| | | | | |
| per call, p50 | **428 ms** | 428 ms | 2,320 ms | 2,419 ms |
| per 1,000 calls | **$0.055** | $0.055 | $1.599 | $3.714 |

"Jev, corrected" is the same run with a fixed 0.30 taken off each raw score
before rounding. More on where that number came from below.

## Everyone reads MEDDPICC too generously

Every setup overstated more than it understated. Jev did it 33 times and
never once went the other way. Haiku overstated 25 times, Sonnet 9.

The clearest case is champion. Jev and Haiku each missed it 8 times, all
too high, and it was the same mistake both times: whoever was on the call
became the champion. Hannah at Northwind, Omar at Tidepool and Hollis at
Wrenfield each joined a first discovery call on their own, and both models
marked them an established champion. A champion is someone doing
things for the deal inside their company, and nothing on those calls shows
that. Sonnet's six champion misses split three high and three low.

## The bias correction worked, on a week it had never seen

Weeks 01 to 03 all found Jev's score answers running high, and each README
said to correct for it without ever trying. So I measured the offset on
the first three weeks only: +0.25 on intent, +0.34 on severity, +0.31 on
meeting intent, +0.30 pooled over 193 answers. That went into `common/jev.py` as `SCORE_BIAS` in its own
commit, before this week's run was scored, so the correction couldn't be
tuned to it. `src/bias.py` reproduces the number.

Taking 0.30 off every raw score lifted Jev from 74% exact to 84%, past
Haiku, and cut its overstatements from 33 to 20. It costs nothing, because
it's the same answers read differently.

## It didn't fix the one that mattered

Jev's false commit is Pinecrest. The summary says the team "would figure out
next steps internally", which is a decision process mentioned and nothing
more. Jev scored it 1.83 out of 2, and 1.53 after the correction still
rounds up. On that one field Jev was 0.83 high, nearly three times its
average.

A stricter bar for the three forecast fields doesn't save it either. Every
field that really was established scored 1.96 or more, but Jev also gave
1.91, 1.92 and a flat 2.00 to fields that weren't. The 2.00 was Graniteworks'
decision process, and the same call's "99.9% uptime SLA" came back as a
metric at 1.91, when it's a requirement. There's no raw score that cleanly
separates right from wrong on the fields that put money in a forecast.

## What does fix it

Let Jev fill every call, and get a second opinion only on the deals it puts
in the forecast. Jev marked four ready: Pinecrest plus the three real ones.
Using Sonnet's answers on just those four gives:

| | put in forecast, shouldn't be | left out | per 1,000 calls |
|---|---|---|---|
| Sonnet on every call | 0 | 0 | $3.714 |
| Jev on every call, Sonnet on the four it marks ready | 0 | 0 | **$0.994** |

Sonnet's forecast accuracy for about a quarter of the price. Week 02 landed
on the same shape: Jev casts the net, and Claude only looks at what it
catches. `src/score.py` prints this from the two runs, and none of it is a
new call.

## What I'd ship

```
call summary -> Jev: all eight fields, raw scores less 0.30
             -> gaps go to the AE as next-call questions
marked forecast-ready -> Claude checks metrics, economic buyer, decision process
```

Don't let the champion field drive anything automatic. Two of the three
models couldn't tell a champion from someone who just attended the call.

## Running it

```bash
cd week-04-meddpicc
python3 src/calls.py        # builds data/calls.jsonl from the labelled source
python3 src/bias.py         # Jev's score bias, measured on weeks 01 to 03
python3 src/bench.py        # Jev, Haiku and Sonnet, about 8 minutes
python3 src/score.py
```

16 calls is a small set. One call is six points on the forecast rows, and
the whole finding about false commits rests on a single deal. The bias
measurement is the sturdier result, because it was fixed from 193 earlier
answers before this week was scored.
