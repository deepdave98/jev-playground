"""Shared lead questions and routing rules."""

PRODUCT_CONTEXT = (
    "We sell a GTM data and workflow platform to B2B SaaS revenue teams. "
    "Buyers are RevOps, Sales Ops, Growth, Demand Gen, and the VPs and CROs "
    "above them. We are not a fit for consumer apps, agencies reselling our "
    "data, or teams under 50 people."
)

# claude_runner.py renders these same criteria into text.
QUESTIONS = {
    "disqualify": {
        "type": "noul",
        "instructions": (
            "Should this inbound lead be disqualified and never routed to a "
            "human? Disqualify job applicants, students or academics asking "
            "for free access, vendors or agencies pitching services to us, "
            "people who work at a direct competitor, and generic spam such as "
            "SEO or link-building outreach. Do not disqualify a real buyer "
            "just because they used a personal email address, wrote a short "
            "message, or work at a small company."
        ),
        "criteria": {
            "true": "Job applicant, student or academic wanting free access, vendor or agency selling to us, employee of a direct competitor, or spam.",
            "false": "Anyone else, including weak or early-stage buyers.",
        },
    },
    "icp_fit": {
        "type": "noul",
        "instructions": (
            "Is this lead inside our ideal customer profile? " + PRODUCT_CONTEXT
            + " A lead is in ICP when the company sells to other businesses, "
            "has at least 50 employees, and the person holds a revenue, "
            "marketing, operations, data or executive role. Judge the company "
            "and the role, not the email domain."
        ),
        "criteria": {
            "true": "B2B company, 50 or more employees, and a revenue, marketing, ops, data or exec role.",
            "false": "Consumer company, under 50 employees, or a role with no connection to revenue.",
        },
    },
    "segment": {
        "type": "choice",
        "instructions": (
            "Which segment does this company belong to, based on employee "
            "headcount? Use the headcount given in the lead record. If "
            "headcount is missing, infer it from the company name and the "
            "message."
        ),
        "criteria": {
            "enterprise": "1000 or more employees.",
            "mid_market": "200 to 999 employees.",
            "smb": "Fewer than 200 employees.",
        },
    },
    "intent": {
        "type": "score",
        "instructions": (
            "How strong is this lead's buying intent right now, based only on "
            "what they wrote and the activity attached to the record? Judge "
            "urgency and specificity, not company quality."
        ),
        "criteria": [
            "none: no buying signal at all. A support question, an existing customer issue, or a message with no commercial content.",
            "researching: general curiosity. Asking how something works, reading content, no use case named, no vendor comparison.",
            "evaluating: an active evaluation. Comparing vendors, asking for a demo, a trial or pricing, or describing a concrete use case they want solved.",
            "ready_to_buy: ready to transact. Names a timeline, a budget, a seat count, a contract, procurement or a security review, or asks to speak to sales now.",
        ],
    },
}

INTENT_LEVELS = ["none", "researching", "evaluating", "ready_to_buy"]
SEGMENTS = ["enterprise", "mid_market", "smb"]

# v2 adds this clarification to both runners.
COMPETITOR_CLARIFICATION = (
    " Direct competitors are companies selling GTM data, sales engagement or "
    "lead routing tools, for example Clay, Apollo, ZoomInfo, Outreach and "
    "Salesloft. A company that sells some other kind of B2B software is a "
    "prospect, not a competitor."
)


def build_questions(variant: str = "v1") -> dict:
    """Return v1, or v2 with the explicit competitor list."""
    import copy

    q = copy.deepcopy(QUESTIONS)
    if variant == "v2":
        q["disqualify"]["instructions"] += COMPETITOR_CLARIFICATION
        q["disqualify"]["criteria"]["true"] = (
            "Job applicant, student or academic wanting free access, vendor or "
            "agency selling to us, employee of a GTM data, sales engagement or "
            "lead routing company, or spam."
        )
    elif variant != "v1":
        raise ValueError(f"unknown variant {variant!r}")
    return q

ROUTES = ["reject", "ae_now", "sdr_sequence", "self_serve", "nurture"]


def route(disqualify: bool, icp_fit: bool, segment: str, intent: str) -> str:
    """Deterministic routing rule, applied identically to both models' output."""
    if disqualify:
        return "reject"
    intent_rank = INTENT_LEVELS.index(intent)
    if icp_fit:
        if intent_rank >= 3:
            return "ae_now"
        if intent_rank == 2:
            return "ae_now" if segment == "enterprise" else "sdr_sequence"
        return "nurture"
    if intent_rank >= 2 and segment == "smb":
        return "self_serve"
    return "nurture"
