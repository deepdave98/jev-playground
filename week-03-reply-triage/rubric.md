# How the answer key was written

60 replies to a cold outbound sequence, labelled by hand against the strings
in `src/spec.py`. Every prospect and company is made up.

## category

| category | means |
|---|---|
| `interested` | wants to talk, see a demo, or learn more |
| `not_now` | open to it later, or the timing is wrong |
| `wrong_person` | points to someone else, or has left the company |
| `objection` | a no, with or without a reason |
| `out_of_office` | an automatic away message |
| `auto_reply` | any other automatic message |

The hard cases:

- R41 sounds like a wrong-person reply ("Dana moved to a different role") but
  the sender took over the territory and says no. `objection`.
- R46 and R51 are away messages that name a backup contact. Still
  `out_of_office`, because the prospect is coming back.
- R54 and R60 give a new address, but a machine sent them. `auto_reply`.
- R43 says no budget and no need. The "no need" makes it an `objection` and
  not a `not_now`.

## opt_out

Did the sender ask, about themselves, to stop being emailed, to come off a
list, or to have their data deleted? Nine replies say yes, in English,
French, German, and one GDPR Article 17 request.

- R37, "Not interested.", is a no and not an opt-out. The sequence stops
  either way, but only a real opt-out goes on the suppression list.
- R40 is sarcasm about getting five emails. It's a complaint, with no
  request in it.
- R04 is interested and asks you to stop emailing a colleague. The sender
  didn't opt out.
- R19 says "maybe next year" and then asks to come off the sequence. It
  looks like a snooze and has to be treated as an opt-out.

## meeting_intent

`none`, `curious`, `open`, `ready`. Curious wants material first. Open
agrees to talk without a time. Ready names a time, accepts one, or asks for
a calendar link. Anything that isn't interested or not_now is `none`.

## Routing

`spec.route()` runs over the answer key and over every model's answers.

```
opt_out                             -> suppress
out_of_office                       -> pause
auto_reply                          -> ignore
wrong_person                        -> reroute
not_now                             -> snooze
objection                           -> close
interested, open or ready           -> book_meeting
interested, curious                 -> send_info
```

Opt-out is checked first on purpose. A reply can be a snooze and an opt-out
at once, and only one of those has a legal cost if you get it wrong.

A model answer whose category isn't one of the six goes to `review`. The
answer key never produces it.

## For the extraction step

Out of office replies carry the return date and wrong-person replies the
contact they point to. R47 says "back on 10/08", which is October 8 in a US
inbox. R49 says "out until the 6th" and arrived September 28, so it means
October 6. R25 names nobody, so the right answer there is no contact.

## Distribution

| label | counts |
|---|---|
| category | 16 objection, 12 interested, 9 out_of_office, 8 not_now, 8 wrong_person, 7 auto_reply |
| opt_out | 9 true, 51 false |
| meeting_intent | 46 none, 6 open, 4 curious, 4 ready |
| route | 9 suppress, 9 pause, 8 reroute, 8 close, 8 book_meeting, 7 snooze, 7 ignore, 4 send_info |
