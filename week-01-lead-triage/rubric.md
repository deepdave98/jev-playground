# Lead labels and routing

The synthetic records and reference labels are in
[src/build_dataset.py](src/build_dataset.py). The prompts are in
[src/spec.py](src/spec.py).

The seller is a GTM data and workflow platform for B2B SaaS revenue teams.

| Field | Rule |
|---|---|
| `disqualify` | Job applicant, student seeking free access, vendor selling to us, direct competitor, or spam. Personal email, a short message, and a small company do not disqualify a buyer. |
| `icp_fit` | B2B company with at least 50 employees and a revenue, marketing, operations, data or executive role. Evaluate independently of disqualification. |
| `segment` | `enterprise`: 1,000+ employees; `mid_market`: 200-999; `smb`: under 200. Infer from the record if headcount is absent. |

## Intent

| Label | Evidence in the message or activity |
|---|---|
| `none` | No commercial signal, including support or billing problems. |
| `researching` | General curiosity without a named use case or vendor comparison. |
| `evaluating` | Comparing vendors, requesting a demo, trial or pricing, or describing a concrete use case. |
| `ready_to_buy` | A purchase timeline, budget, seat count, contract, procurement, security review, or request to speak to sales now. |

A competitor can meet the ICP criteria and still be rejected. L016 uses a
personal email but meets the ICP; L044 works at Salesforce but has a facilities
role. Support requests L046 and L048 have no buying intent; expansion request
L047 does.

## Routing

Apply in order with `spec.route()`:

| Condition | Queue |
|---|---|
| Disqualified | `reject` |
| In ICP, ready to buy | `ae_now` |
| In ICP, evaluating, enterprise | `ae_now` |
| In ICP, evaluating | `sdr_sequence` |
| In ICP, lower intent | `nurture` |
| Outside ICP, SMB, evaluating or ready to buy | `self_serve` |
| Otherwise | `nurture` |

Both reference labels and model predictions use this function.

## Coverage

60 leads: 12 disqualified, 44 in ICP; 24 enterprise, 19 mid-market, 17 SMB.
Intent labels: 13 none, 14 researching, 20 evaluating, 13 ready to buy.
Routes: 16 AE, 19 nurture, 10 SDR, 12 reject, 3 self-serve. Three self-serve
examples provide little evidence about that route.
