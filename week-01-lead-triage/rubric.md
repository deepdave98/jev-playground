# The answer key, and how it was written

Every label in `data/leads.jsonl` was written by hand against the rules below.
No model produced any label. This matters more than it sounds. If Claude had
written the answer key, then scoring Claude against it would measure how well
Claude agrees with itself, and Jev would lose a point everywhere Claude was
wrong.

The rules are here so you can disagree with them. If you think a lead is
mislabelled, send a pull request against `src/build_dataset.py`. Arguing
about it in the abstract gets nobody anywhere.

## What the company sells

A GTM data and workflow platform sold to B2B SaaS revenue teams. Buyers are
RevOps, Sales Ops, Growth, Demand Gen, and the VPs and CROs above them. Not a
fit for consumer apps, for agencies reselling the data, or for teams under 50
people.

## disqualify

True when the sender is one of:

- a job applicant
- a student or academic asking for free access
- a vendor or agency selling something to us
- an employee of a direct competitor
- generic spam, for example SEO outreach or link building

False for everyone else, including weak and early-stage buyers. Short
messages still count. So do gmail addresses.

Competitors are judged by where they work. L009 and L010 read like ordinary
demo requests, which is how they arrive in a real inbox.

## icp_fit

True when all three hold:

1. the company sells to other businesses
2. headcount is 50 or more
3. the person's role touches revenue, marketing, operations, data, or is an
   executive role

This is judged independently of `disqualify`. A RevOps manager at a competitor
is a fit on company and role and still gets rejected, because the routing rule
checks disqualification first. Keeping the two questions separate is
deliberate: it stops one judgment from quietly absorbing another, and it means
a model that confuses the two shows up in the numbers.

Look at the company itself. L016 is a real Cisco buyer writing from a gmail
address. Then look at what the role actually does. L044 is a Facilities
Coordinator at Salesforce, a 75,000 person B2B company, and still no fit.

## segment

Straight from headcount:

| headcount | segment |
|---|---|
| 1000 or more | `enterprise` |
| 200 to 999 | `mid_market` |
| under 200 | `smb` |

Where headcount is missing the label follows what the record implies. This is
the easiest of the four questions and it is in the set on purpose, as a floor.
Getting this one wrong means the model did not read the record properly.

## intent

| level | means |
|---|---|
| `none` | no buying signal. Support questions, billing problems, wrong department. |
| `researching` | general curiosity. No use case named, no vendor comparison. |
| `evaluating` | an active evaluation. Comparing vendors, asking for a demo, a trial or pricing, or naming a concrete use case. |
| `ready_to_buy` | ready to transact. A timeline, a budget, a seat count, a contract, procurement, a security review, or asking for sales now. |

Intent comes out of the message itself. Company quality has nothing to do
with it. A 300,000 person enterprise asking an idle question is
`researching`. A 55 person startup with budget approved and a date is
`ready_to_buy`.

Two awkward ones. L046 and L048 are existing customers with a billing
problem and a broken webhook. Both are `none`, because a support
ticket is not intent no matter how large the account. L047 is an existing
customer adding 20 seats, which is `ready_to_buy`, because expansion is a
purchase.

## route

Routing is a rule, so it runs as one. `spec.route()` takes the four judgments
and returns a queue. The same function runs over the answer key and over each
model's output, and no model is ever asked to route.

```
disqualify                            -> reject
icp_fit and ready_to_buy              -> ae_now
icp_fit and evaluating and enterprise -> ae_now
icp_fit and evaluating                -> sdr_sequence
icp_fit and anything lower            -> nurture
not icp_fit, evaluating or better, smb -> self_serve
everything else                       -> nurture
```

People hand this bit to a model all the time and they should not. Five
branches, free, instant, testable, and it cannot drift on you. Spending a
model call here buys nothing and adds a way to fail.

Save the models for the four judgments underneath, which are genuinely fuzzy
and which no amount of branching will solve.

## Distribution

60 leads.

| label | counts |
|---|---|
| disqualify | 12 true, 48 false |
| icp_fit | 44 true, 16 false |
| segment | 24 enterprise, 19 mid_market, 17 smb |
| intent | 13 none, 14 researching, 20 evaluating, 13 ready_to_buy |
| route | 16 ae_now, 19 nurture, 10 sdr_sequence, 12 reject, 3 self_serve |

Roughly a third are written to be awkward on purpose: real buyers on personal
email, competitors posing as buyers, huge companies with no fit, senior people
with no intent, and two messages that are basically empty. A test set of
obvious cases puts every model at 100% and tells you nothing.

`self_serve` only has 3 cases, so treat that row of the confusion matrix as
directional.
