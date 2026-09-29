# How the answer key was written

16 call summaries, each labelled on all eight MEDDPICC elements against the
strings in `src/spec.py`. I set the labels first and then wrote each
summary to carry them, so every label points at a sentence you can find.

## Three levels, the same for every element

| level | means |
|---|---|
| `none` | not discussed on this call |
| `mentioned` | came up, without specifics |
| `established` | stated specifically: a number, a named person and their role, named steps or dates, a named alternative |

The line that decides most labels is between mentioned and established.
"They'd decide sometime this quarter" is mentioned. "Leadership meets on
October 14, shortlists two vendors and decides by November 1" is
established.

## Where each element gets hard

**Economic buyer** needs a name and a confirmed hold on the money. "Budget
would come from the COO's side" (C02) is mentioned. So is Fairhaven (C13),
where Nikhil thinks the CEO signs anything over $50K but isn't sure. Marlow
(C14) is established even though the CFO wasn't on the call, because the
champion named him and confirmed he owns the budget.

**Champion** needs someone doing things for the deal. Jonah at Pinecrest
(C07) booked time with the sales managers and is writing the business case.
Leo at Cascade (C15) loved the demo and isn't involved in buying, so he's
mentioned.

**Competition** counts an in-house build or doing nothing when the customer
is really weighing it. Wrenfield's COO (C16) said the real alternative is
living with it for another year. That's established.

**Metrics and pain** are easy to mix up. Pain is the problem and what it
costs: "$180K of ARR lost to churn". Metrics is the target they want to
hit: "first response under one hour". A call can have one without the
other. Tidepool (C02) has a costed problem and no target.

## The forecast rule

`spec.forecast_ready()` puts a deal in the forecast only when metrics,
economic buyer and decision process are all established. Three calls meet
it: Keystone, Redwood and Marlow.

Three more are one or two levels short, on purpose:

| call | short on |
|---|---|
| C07 Pinecrest | decision process: "would figure out next steps internally" |
| C10 Lumen Health | economic buyer: "the CFO will make the final call, though they haven't talked to him yet" |
| C13 Fairhaven | metrics and economic buyer |

Any model that reads these a level high puts a deal in the forecast that
isn't ready. That's the error this week is built to catch.

## Distribution

128 labels: 48 established, 47 none, 33 mentioned. Discovery calls sit
mostly at none and mentioned, commercial calls mostly at established.
