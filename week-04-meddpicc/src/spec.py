"""Questions and the forecast rule for week 04: MEDDPICC from call summaries.

Eight score questions per call, one for each MEDDPICC element, all with the
same three levels. Both models get these exact strings.
"""

LEVELS = [
    "none: not discussed on this call.",
    "mentioned: came up, but without specifics.",
    "established: stated specifically, with a number, a named person and their "
    "role, named steps or dates, or a named alternative.",
]


def element(instructions):
    return {"type": "score", "instructions": instructions, "criteria": LEVELS}


QUESTIONS = {
    "metrics": element(
        "Did the call establish the measurable result the customer wants? It is "
        "established when there is a number or a target, like cutting first "
        "response time from six hours to one."
    ),
    "economic_buyer": element(
        "Did the call establish who controls the budget for this purchase? It is "
        "established when a named person is confirmed as the one who signs off on "
        "the money. A title with no name, or a guess, is mentioned."
    ),
    "decision_criteria": element(
        "Did the call establish what the customer will judge vendors on? It is "
        "established when there are specific requirements, like SOC 2, a Zendesk "
        "integration, or a price ceiling."
    ),
    "decision_process": element(
        "Did the call establish how the decision gets made? It is established when "
        "the steps, the people involved and the timing are laid out."
    ),
    "paper_process": element(
        "Did the call establish what happens between a yes and a signature? It is "
        "established when named steps are laid out, like a security review, legal "
        "redlines, procurement, or who signs."
    ),
    "identify_pain": element(
        "Did the call establish the business problem behind the purchase? It is "
        "established when the problem is specific and so is what it costs them."
    ),
    "champion": element(
        "Did the call establish someone at the customer who is actively pushing "
        "this internally? It is established when a named person is taking action "
        "for the deal, like setting up meetings or making the case to their boss. "
        "Someone who likes the product but isn't pushing it is mentioned."
    ),
    "competition": element(
        "Did the call establish what else the customer is weighing? It is "
        "established when a named vendor, an in-house build, or doing nothing is a "
        "real option they are considering."
    ),
}

ELEMENTS = list(QUESTIONS)
LEVEL_NAMES = [x.split(":")[0] for x in LEVELS]

# A deal goes in the forecast only when these three are established. Plenty
# of teams use some version of this rule, and it's the one place in this week
# where a model rating things too high costs real money.
FORECAST_NEEDS = ("metrics", "economic_buyer", "decision_process")


def forecast_ready(card):
    return all(card[e] == "established" for e in FORECAST_NEEDS)


def gaps(card):
    """What to ask about on the next call."""
    return [e for e in ELEMENTS if card[e] != "established"]
