# Event labels and risk rules

[src/ledger.py](src/ledger.py) defines 20 synthetic deals and 73 events.
[src/spec.py](src/spec.py) contains the prompts and decision rules.
The fixed evaluation date is `2026-09-25`. Competitors Hexline, Corvid and
Tallyworks are fictional and named in the prompts.

## Event labels

| Signal | Meaning |
|---|---|
| `competitor` | Considering, trialling, comparing or choosing a competitor. Rejecting a competitor is `momentum`. |
| `escalation` | A bug, outage, complaint or escalated support ticket. How-to questions are `routine`. |
| `champion_exit` | The named champion or sponsor leaves or is moved off the project. Another employee leaving is `routine`; an internal promotion is `momentum`. |
| `stall` | Budget frozen or cut, seats reduced, close date pushed, or procurement/legal stuck. |
| `momentum` | Progress toward closing or expanding. |
| `routine` | Activity that does not change the deal's outlook. |

Severity measures the threat from that event: `none`, `watch`, `serious`,
`critical`. Good news is `none`. E066's request to go live sooner is
`momentum` with severity `none`, despite the phrase "or we have a problem."

`exec_engaged` requires active participation by a VP or above, C-level,
President or Founder. Being cc'd, mentioned, or changing jobs does not count.
Directors, department heads, managers and leads do not qualify. A person's
title may appear in an earlier event, as with E025 and E026.

## Deal rules

`spec.assess()` flags a deal when any rule fires. It runs on reference labels
and model predictions; only the direct-ledger run asks the model to apply it.

| Reason | Condition |
|---|---|
| `competitor` | Two competitor events at `watch` or higher, or one `critical`. |
| `escalations` | Two escalations at `serious` or higher, or one `critical`. |
| `champion_left` | A champion exit at `serious` or higher. |
| `stalled` | A stall at `serious` or higher. |
| `no_exec_30d` | ARR at least $100,000 with no executive participation in the last 30 days, inclusive. |
| `closing_with_issues` | Close date in the next 0-7 days, inclusive, and any event at `serious` or higher. |

The rule has no issue-resolution tracking. The supplied events must exclude
resolved issues and future timestamps before use with live data.

## Expected flags

| Deal | Reasons |
|---|---|
| Ironbridge, Keystone | `competitor` |
| Datacore | `no_exec_30d` |
| Halcyon, Tidewater | `stalled` |
| Vantage | `champion_left` |
| Cloudmark | `escalations` |
| Precision | `escalations`, `closing_with_issues` |

The dataset builder checks these expected reasons against the event labels.
The other twelve deals are healthy under these rules. Both `champion_exit`
examples belong to Vantage, so that class has limited coverage.
