# MEDDPICC labels

16 synthetic call summaries with eight labels each.
[`spec.py`](src/spec.py) contains the shared prompt strings and forecast
rule; [`calls.py`](src/calls.py) contains the fixtures.

| Level | Definition |
|---|---|
| `none` | absent from the call |
| `mentioned` | raised without specifics |
| `established` | supported by a number, a named person and role, named steps or dates, or a named alternative |

"Decide sometime this quarter" is `mentioned`. Named decision steps with
owners and dates are `established`.

- **Metrics:** the measurable result the customer wants. A costed problem
  establishes pain; it does not supply a target. C02 has pain without metrics.
- **Economic buyer:** a named person confirmed to control the budget. C02
  names only a title; C13 guesses who approves. Both are `mentioned`.
  C14 confirms the named CFO's authority even though he missed the call.
- **Decision criteria:** specific vendor requirements.
- **Decision process:** steps, participants and timing for choosing a vendor.
- **Paper process:** steps between the decision and a signature.
- **Pain:** a specific business problem with its cost or consequence.
- **Champion:** a named person acting internally for the purchase. C07's
  contact arranges meetings and writes the business case. C15's enthusiasm
  without involvement in buying is `mentioned`.
- **Competition:** a named alternative under consideration. An internal
  build or doing nothing counts; C16 explicitly weighs waiting another year.

The forecast rule requires metrics, economic buyer and decision process to
be `established`. C11 Keystone, C12 Redwood and C14 Marlow qualify.

| Near miss | Missing evidence |
|---|---|
| C07 Pinecrest | specific decision process |
| C10 Lumen Health | confirmed economic buyer |
| C13 Fairhaven | metrics and confirmed economic buyer |

Distribution: 48 `established`, 47 `none`, 33 `mentioned`.
