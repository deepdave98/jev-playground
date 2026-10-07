# Reply labels

60 synthetic replies. [`spec.py`](src/spec.py) contains the prompt strings
and routing function; [`replies.py`](src/replies.py) contains the fixtures.

| Category | Definition |
|---|---|
| `interested` | wants to talk, see a demo or learn more |
| `not_now` | open to it later, or the timing is wrong |
| `wrong_person` | points to someone else, or has left the company |
| `objection` | declines, with or without a reason |
| `out_of_office` | automatic away message |
| `auto_reply` | other automatic message |

Away messages with backup contacts stay `out_of_office` (R46, R51).
Machine-generated address changes are `auto_reply` (R54, R60). R41 says the
sender took over the territory and declines, so it is an `objection`.
R43's lack of need also makes it an `objection`.

`opt_out` requires the sender to request that their own email, sequence
membership or stored data be removed. R04 requests removal of a colleague;
R37 declines; R40 complains without requesting removal. Those are false.
R19 asks to leave the sequence despite suggesting contact next year: true.

| Meeting intent | Definition |
|---|---|
| `none` | no interest in talking |
| `curious` | asks questions or requests material |
| `open` | agrees to talk without a time |
| `ready` | proposes or accepts a time, or asks for a calendar link |

Categories other than `interested` and `not_now` have intent `none`.

`route()` checks opt-out first, then category. Unknown categories go to
`review`. It maps away messages to `pause`, automatic replies to `ignore`,
wrong contacts to `reroute`, bad timing to `snooze`, and objections to
`close`. Interested replies with intent `open` or `ready` go to
`book_meeting`; the remaining interested replies go to `send_info`.

The extraction key stores return dates for away messages and contacts for
referrals. It interprets R47's "10/08" as October 8 using US month/day and
R49's "the 6th" as October 6 after its September 28 timestamp. R25 names no
contact, so its referral is null.

| Field | Distribution |
|---|---|
| category | 16 objection, 12 interested, 9 out_of_office, 8 not_now, 8 wrong_person, 7 auto_reply |
| opt_out | 9 true, 51 false |
| meeting_intent | 46 none, 6 open, 4 curious, 4 ready |
