"""Questions and the routing rule for week 03: replies to outbound sequences.

Both models get these exact strings. Jev takes them as typed questions and
Claude reads the text common.prompt.render() makes from them.
"""

QUESTIONS = {
    "category": {
        "type": "choice",
        "instructions": "What kind of reply is this? Go by what the sender means.",
        "criteria": {
            "interested": "They want to talk, see a demo, or learn more about the product.",
            "not_now": (
                "Open to it later. They name a time, a quarter or an event to wait "
                "for, or say the timing is wrong."
            ),
            "wrong_person": "They point you to someone else, or say they have left the company.",
            "objection": (
                "A no. It may come with a reason, such as price, a competitor they "
                "are happy with, no budget or no need, or with none at all."
            ),
            "out_of_office": "An automatic away message, usually with a return date or a backup contact.",
            "auto_reply": (
                "Any other automatic message: ticket receipts, unmonitored mailboxes, "
                "delivery failures."
            ),
        },
    },
    "opt_out": {
        "type": "noul",
        "instructions": (
            "Does the sender ask to stop receiving emails, to be taken off a list, "
            "or to have their data deleted? It has to be a request about "
            "themselves, in any wording or language. A plain no, a complaint, or "
            "asking you to stop emailing a colleague does not count."
        ),
        "criteria": {
            "true": "They asked to stop being emailed, to be removed, or to have their data deleted.",
            "false": "No such request about the sender, even if the answer is no.",
        },
    },
    "meeting_intent": {
        "type": "score",
        "instructions": "How close is the sender to agreeing to a meeting?",
        "criteria": [
            "none: no interest in talking.",
            "curious: asks a question or wants material first, without agreeing to talk.",
            "open: agrees to talk at some point, without a time.",
            "ready: proposes a time, accepts one, or asks for a calendar link.",
        ],
    },
}

ROUTES = ["suppress", "pause", "ignore", "reroute", "snooze", "close", "send_info",
          "book_meeting", "review"]


def route(category, opt_out, meeting_intent):
    """Where a reply goes next. Runs in code on every model's answers.

    An opt-out beats everything else. Emailing someone who asked you to stop
    is the one mistake here with a legal cost.
    """
    if opt_out:
        return "suppress"
    if category == "out_of_office":
        return "pause"
    if category == "auto_reply":
        return "ignore"
    if category == "wrong_person":
        return "reroute"
    if category == "not_now":
        return "snooze"
    if category == "objection":
        return "close"
    if category != "interested":
        # A model answered with something that isn't a category. Don't guess.
        return "review"
    return "book_meeting" if meeting_intent in ("open", "ready") else "send_info"


# Two rules from the write-up that sit around the model, used by the MCP
# server. A reply that is nothing but an opt-out word never needs a model,
# and an opt_out answer this close to a coin flip goes to a person.
STOP_WORDS = {"stop", "unsubscribe", "remove me", "opt out"}
UNSURE = (0.4, 0.6)


def only_stop_word(text):
    return text.strip().strip(".!").lower() in STOP_WORDS
