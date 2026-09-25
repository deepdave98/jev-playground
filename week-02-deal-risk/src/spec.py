"""Questions, definitions and the deal risk rule for week 02.

Every model gets these exact strings. The Claude prompts are rendered from
the same dicts Jev receives, so a wording change here lands on both sides.
"""

from datetime import date

AS_OF = "2026-09-25"

# The three numbers in the risk rule. They feed both assess() and the
# RISK_RULES text Claude reads in the ledger run, so change them here and the
# two can't drift apart. Set them for your own pipeline before trusting a flag.
EXEC_MIN_ARR = 100_000
EXEC_WINDOW_DAYS = 30
CLOSING_SOON_DAYS = 7

# Made up, so nobody's real product ends up in a synthetic loss report. Both
# models are told the names up front. Week 01 showed Jev can't be expected to
# know who a company's competitors are, and this week isn't testing that.
COMPETITORS = ["Hexline", "Corvid", "Tallyworks"]

SIGNALS = {
    "competitor": (
        "The account is considering, trialling or comparing a competing product, "
        "or has picked one. The competitors are Hexline, Corvid and Tallyworks. "
        "If they name a competitor only to say they rejected it, that is momentum."
    ),
    "escalation": (
        "A support problem: a bug, an outage, a complaint, or a ticket that has "
        "been escalated. A how-to question is routine."
    ),
    "champion_exit": (
        "Our champion, sponsor or main buyer has left the account, is leaving, or "
        "has been moved off the project. Someone else leaving is routine, and a "
        "champion promoted inside the account is momentum."
    ),
    "stall": (
        "Budget cut or frozen, seats reduced, the close date pushed out, or "
        "procurement or legal stuck."
    ),
    "momentum": (
        "Something that makes the deal more likely to close or grow: expansion "
        "talk, an exec leaning in, legal or procurement moving, a stage "
        "advancing, a trial going well, strong praise."
    ),
    "routine": (
        "Normal activity that changes nothing: page visits, how-to questions, "
        "scheduling, auto-renewals, first calls, check-ins."
    ),
}

SEVERITY = [
    "none: no threat to this deal. Good news is always none.",
    "watch: worth knowing about, not a problem yet.",
    "serious: a real threat to this deal that someone should act on.",
    "critical: we could lose this deal outright if nobody acts.",
]
SEV = [s.split(":")[0] for s in SEVERITY]

SENIOR = (
    "VP and above, any C-level title (CEO, CFO, COO, CTO, CRO, CCO and so on), "
    "President or Founder. Directors, heads of departments, managers and leads "
    "do not count."
)

EVENT_QUESTIONS = {
    "signal": {
        "type": "choice",
        "instructions": "What does this event tell us about the open deal?",
        "criteria": SIGNALS,
    },
    "severity": {
        "type": "score",
        "instructions": (
            "How much does this one event threaten the deal? Judge the event on "
            "its own, using the deal record for context."
        ),
        "criteria": SEVERITY,
    },
    "exec_engaged": {
        "type": "noul",
        "instructions": (
            "Does a senior person at the customer take an active part in this "
            "event? Senior means " + SENIOR + " Being cc'd, being mentioned, or "
            "changing jobs is not taking part."
        ),
        "criteria": {
            "true": "A senior customer person spoke, wrote, decided or edited something here.",
            "false": "No senior customer person took an active part.",
        },
    },
}

# The same rule written out in words, for the run where Claude reads the whole
# ledger and judges the deal directly instead of labelling events.
RISK_RULES = f"""A deal is at risk if any of these hold. Use the keys in brackets.

- [competitor] two or more events show the account considering or trialling a
  competitor, or one shows them choosing one
- [escalations] two or more serious support escalations, or one critical one
- [champion_left] our champion or sponsor has left or been moved off it
- [stalled] budget cut or frozen, seats reduced, or the deal pushed out
- [no_exec_30d] the deal is worth ${EXEC_MIN_ARR // 1000}K or more and no senior customer person
  has taken an active part in the last {EXEC_WINDOW_DAYS} days. Senior means {SENIOR}
  Being cc'd does not count.
- [closing_with_issues] the deal closes within {CLOSING_SOON_DAYS} days and at least one serious
  issue is still open

A competitor named only to be rejected does not count. Neither does someone
other than the champion leaving, or a champion promoted inside the account."""

REASON_KEYS = ["competitor", "escalations", "champion_left", "stalled",
               "no_exec_30d", "closing_with_issues"]


def days(a: str, b: str) -> int:
    return (date.fromisoformat(b[:10]) - date.fromisoformat(a[:10])).days


def assess(deal: dict, judged: list[dict], as_of: str = AS_OF) -> list[str]:
    """Risk reasons for a deal, from its events once they have been judged.

    Runs on the hand labels and on every model's labels, so the answer key and
    the models go through the same function. An empty list means healthy.
    as_of is fixed for the benchmark. The MCP server passes the real date.
    """
    sev = lambda e: SEV.index(e["severity"])  # noqa: E731
    out = []

    comp = [e for e in judged if e["signal"] == "competitor" and sev(e) >= 1]
    if len(comp) >= 2 or any(sev(e) == 3 for e in comp):
        out.append("competitor")

    esc = [e for e in judged if e["signal"] == "escalation" and sev(e) >= 2]
    if len(esc) >= 2 or any(sev(e) == 3 for e in esc):
        out.append("escalations")

    if any(e["signal"] == "champion_exit" and sev(e) >= 2 for e in judged):
        out.append("champion_left")

    if any(e["signal"] == "stall" and sev(e) >= 2 for e in judged):
        out.append("stalled")

    # A missing exec is the one reason no single event can show. It only exists
    # across the whole ledger, which is why it lives here and not in a question.
    if deal["arr"] >= EXEC_MIN_ARR:
        if not any(e["exec_engaged"] and days(e["ts"], as_of) <= EXEC_WINDOW_DAYS for e in judged):
            out.append("no_exec_30d")

    left = days(as_of, deal["close_date"])
    if 0 <= left <= CLOSING_SOON_DAYS and any(sev(e) >= 2 for e in judged):
        out.append("closing_with_issues")

    return out


def describe(reasons: list[str], deal: dict, judged: list[dict], as_of: str = AS_OF) -> str:
    """The reasons the way the AckDB risk view prints them."""
    words = []
    for r in reasons:
        if r == "competitor":
            n = sum(1 for e in judged if e["signal"] == "competitor" and e["severity"] != "none")
            words.append(f"competitor mentioned x{n}")
        elif r == "escalations":
            n = sum(1 for e in judged if e["signal"] == "escalation"
                    and SEV.index(e["severity"]) >= 2)
            words.append(f"{n} tickets escalated")
        elif r == "champion_left":
            words.append("champion left")
        elif r == "stalled":
            words.append("budget or timing slipped")
        elif r == "no_exec_30d":
            words.append("no exec engagement in 30d")
        elif r == "closing_with_issues":
            words.append(f"closes in {days(as_of, deal['close_date'])}d with open issues")
    return " · ".join(words)
