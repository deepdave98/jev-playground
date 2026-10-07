"""Synthetic call summaries. Label order follows MEDDPICC; levels are 0, 1, 2."""

import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from spec import ELEMENTS, LEVEL_NAMES, forecast_ready  # noqa: E402

CALLS = [
    ("C01", "Northwind", "discovery", (2, 0, 0, 0, 0, 2, 0, 1),
     "Discovery call: Northwind (32 min, zoom). Attendees: Tomás Reyes, Hannah Voss (RevOps Manager). "
     "Summary: Northwind's 40 support agents handle about 12,000 tickets a month and first response "
     "averages six hours. Two enterprise customers cited slow support when they churned last quarter, "
     "roughly $180K of ARR between them. Hannah wants first response under one hour by the end of Q2. "
     "She said they looked at a couple of tools last year without naming them and didn't go further. "
     "Next steps: Tomás to send a short overview."),

    ("C02", "Tidepool", "discovery", (1, 1, 0, 0, 0, 2, 0, 0),
     "Discovery call: Tidepool (28 min, google_meet). Attendees: Tomás Reyes, Omar Farouk (Head of Growth). "
     "Summary: Inbound leads get routed by hand from a spreadsheet and can sit for up to two days. Sales "
     "thinks they lose about 15% of demo requests to vendors who reply faster. Omar wants to speed things "
     "up but didn't put a number on it. He said budget for anything like this would come from the COO's "
     "side. Next steps: Omar to share their lead volume by source."),

    ("C03", "Kestrel Labs", "discovery", (0, 0, 1, 0, 0, 1, 0, 2),
     "Discovery call: Kestrel Labs (25 min, zoom). Attendees: Tomás Reyes, Lucia Romero (VP Sales). "
     "Summary: Lucia called their routing a mess but didn't go into detail. They're in a trial with Corvid "
     "that ends next month, and she wanted to see an alternative before it does. Whatever they pick has to "
     "work with their stack, she said, without saying what that means. Next steps: demo booked for next week."),

    ("C04", "Harbor Freight Co", "discovery", (0, 0, 0, 0, 0, 1, 0, 0),
     "Discovery call: Harbor Freight Co (15 min, zoom). Attendees: Arjun Nair, Ellie Brooks (Account "
     "Executive). Summary: Short call. Ellie said reps sometimes chase the same lead twice and she thought "
     "a tool might help. She wasn't sure who looks after the sales tools and said she'd ask around. "
     "Next steps: none agreed."),

    ("C05", "Halcyon Bio", "discovery", (2, 1, 1, 1, 0, 2, 1, 0),
     "Discovery call: Halcyon Bio (40 min, zoom). Attendees: Tomás Reyes, Priya Nair (RevOps Lead). "
     "Summary: Leads take about 90 minutes to reach a rep, and by then a lot of them have gone cold. "
     "Conversion from demo request to first meeting fell from 40% to 25% this year. Priya wants every lead "
     "routed within five minutes. She'll take it to her team first and then to leadership, and said their "
     "VP of Sales would have to approve the spend. Security matters to them. She was keen and said she'd "
     "try to get this in front of people. Next steps: Tomás to send the security overview."),

    ("C06", "Orbital Freight", "demo", (1, 0, 2, 1, 0, 2, 1, 2),
     "Demo: Orbital Freight (50 min, google_meet). Attendees: Tomás Reyes, Arjun Nair, Mei Tanaka (Sales Ops "
     "Manager). Summary: About 30% of their EMEA tickets miss SLA because they land with agents who don't "
     "speak the customer's language, and they paid $40K in SLA credits last quarter. Requirements are firm: "
     "it has to integrate with Zendesk and HubSpot, route by region and language, and pass their SOC 2 "
     "vendor check. Mei wants faster response times across the board and said they'd decide sometime this "
     "quarter. They're demoing Hexline next week. Mei liked the regional routing. Next steps: Arjun to send "
     "the Zendesk integration docs."),

    ("C07", "Pinecrest", "demo", (2, 2, 2, 1, 0, 2, 2, 1),
     "Demo: Pinecrest (45 min, zoom). Attendees: Tomás Reyes, Rachel Kim (CRO), Jonah Adeyemi (RevOps "
     "Manager). Summary: Inbound leads wait four hours on average and they traced about $300K of lost deals "
     "last half to slow follow-up. Rachel wants response time down to 15 minutes, which she put at about "
     "$1.2M of pipeline a year, and confirmed the budget for this is hers. It has to integrate natively with "
     "Salesforce, support round-robin with territory rules, and come in under $150K a year. She said they'd "
     "looked around and would figure out next steps internally. Jonah has already booked time with the "
     "sales managers to walk them through it and is writing the business case for Rachel. Next steps: "
     "Tomás to send pricing."),

    ("C08", "Quarry Health", "technical", (0, 0, 2, 0, 1, 1, 1, 0),
     "Technical call: Quarry Health (55 min, zoom). Attendees: Arjun Nair, Ben Adler (Director of Sales "
     "Ops), Priya Menon (IT Security). Summary: Priya's requirements are HIPAA compliance with a signed BAA, "
     "SSO through Okta, and all data stored in the US. Ben said the current setup isn't great and that "
     "there would be a security review at some point. Ben was positive about what he saw. Next steps: "
     "Arjun to send the BAA template."),

    ("C09", "Graniteworks", "technical", (0, 0, 2, 1, 2, 0, 0, 1),
     "Technical call: Graniteworks (35 min, zoom). Attendees: Arjun Nair, Mark Hollis (VP Sales), Tanya Reed "
     "(Procurement). Summary: Hard requirements are SAML SSO and a 99.9% uptime SLA. Tanya walked through "
     "their paperwork: InfoSec reviews the security questionnaire, legal reviews the MSA, then procurement "
     "issues a PO, and each step takes about two weeks. They'll pick a vendor after the evaluation and are "
     "comparing a few options. Next steps: Arjun to return the security questionnaire by Friday."),

    ("C10", "Lumen Health", "demo", (2, 1, 1, 2, 0, 2, 2, 2),
     "Demo: Lumen Health (45 min, zoom). Attendees: Tomás Reyes, Anika Rao (RevOps Director). Summary: "
     "Agents spend about eight minutes triaging each ticket by hand, around 1,100 hours a month. Anika "
     "wants that down to two minutes. She's presenting to the leadership team on October 14, they'll "
     "shortlist two vendors, and they'll decide by November 1. Tallyworks is the other vendor on the list. "
     "The CFO will make the final call on budget, though they haven't talked to him yet. It needs to be "
     "secure and easy to use. Anika asked for slides she can use in the leadership presentation. "
     "Next steps: Tomás to send slides by October 7."),

    ("C11", "Keystone", "commercial", (2, 2, 2, 2, 2, 2, 2, 2),
     "Commercial call: Keystone (40 min, zoom). Attendees: Tomás Reyes, Robert Asante (VP Customer "
     "Experience), Yuki Tanaka (Director of Support). Summary: Ticket volume doubled this year and handle "
     "time is up 30%, so they're about to hire 15 agents they'd rather not. Robert wants average handle "
     "time down 20%, which he estimates at about $400K a year, and confirmed the budget is his and he "
     "signs. Requirements are Zendesk integration, EU data residency, and under $200K a year. Robert and "
     "the head of IT decide after a two week pilot, by October 30. Legal redlines the MSA, then InfoSec "
     "signs off, then Robert signs, and legal already has the MSA. Corvid is the other finalist. Yuki set "
     "up this call and is lining up the agents for the pilot. Next steps: pilot kickoff on October 6."),

    ("C12", "Redwood", "commercial", (2, 2, 1, 2, 1, 2, 1, 0),
     "Commercial call: Redwood (35 min, zoom). Attendees: Hannah Lindqvist, Andre Silva (COO), Mei Chen "
     "(Director of Support). Summary: The expansion into Brazil and Mexico adds roughly 60 agents' worth of "
     "volume next year, and hiring for it would cost about $2.4M a year. Andre wants to take on 60% more "
     "tickets without adding headcount, and confirmed he approves the spend. Andre decides with Mei after "
     "the QBR on October 20 and they want to sign before November. It has to scale, Andre said. Mei "
     "mentioned procurement will want to look at it, and she's supportive. Next steps: Hannah to send an "
     "expansion proposal."),

    ("C13", "Fairhaven", "commercial", (1, 1, 2, 2, 2, 1, 2, 2),
     "Commercial call: Fairhaven (30 min, zoom). Attendees: Tomás Reyes, Nikhil Rao (IT Manager), Kara "
     "Benson (Legal Counsel). Summary: Nikhil said support is stretched and wants to save the team time. "
     "Requirements are SOC 2 Type II, a signed DPA, and SSO. The DPA is signed, the MSA is with legal, and "
     "procurement needs a W-9 and a certificate of insurance. Nikhil, the head of support and the CEO meet "
     "on October 12, and if it's a yes they start in November. Nikhil thinks the CEO signs anything over "
     "$50K but wasn't sure. Building it in-house is still on the table if the price comes in too high. "
     "Nikhil got the security review done early and booked the October 12 meeting himself. Next steps: "
     "Tomás to send the W-9 and insurance certificate."),

    ("C14", "Marlow", "commercial", (2, 2, 2, 2, 2, 2, 2, 1),
     "Commercial call: Marlow (35 min, zoom). Attendees: Hannah Lindqvist, Chloe Durand (Support Operations "
     "Manager). Summary: The backlog sits at about 3,000 tickets and CSAT has fallen from 92 to 78. Chloe "
     "wants the backlog under 500 and held there. It needs a Salesforce Service Cloud integration and a "
     "99.9% uptime SLA. Chloe confirmed their CFO, Martin Ekberg, owns this budget and has approved it in "
     "principle. She presents to Martin and the COO on October 9 and they'll decide that week. The "
     "security review is done, legal has the MSA, and Martin signs. She said they'd talked to others. "
     "Chloe booked the October 9 meeting and is writing the proposal herself. Next steps: Hannah to review "
     "Chloe's proposal draft."),

    ("C15", "Cascade", "demo", (0, 0, 0, 0, 0, 1, 1, 0),
     "Demo: Cascade (30 min, zoom). Attendees: Tomás Reyes, Leo Martins (Support Lead). Summary: Leo loved "
     "the demo and said it was the best tool he'd seen. He's not involved in purchasing and didn't know who "
     "is. He said the team is struggling to keep up. Next steps: none agreed."),

    ("C16", "Wrenfield", "discovery", (1, 0, 1, 0, 0, 2, 0, 2),
     "Discovery call: Wrenfield (25 min, google_meet). Attendees: Tomás Reyes, Hollis Grant (COO). Summary: "
     "Escalations from support to engineering doubled this year and cost each engineer about a day a week. "
     "Hollis wants fewer escalations. He was frank that the real alternative is doing nothing and living "
     "with it for another year, and that anything they buy would have to be cheap. Next steps: Tomás to "
     "send a one-page cost comparison."),
]


def main():
    out = pathlib.Path(__file__).resolve().parents[1] / "data" / "calls.jsonl"
    seen = set()
    with out.open("w") as fh:
        for cid, account, stage, levels, text in CALLS:
            assert cid not in seen and len(levels) == len(ELEMENTS), cid
            seen.add(cid)
            card = {e: LEVEL_NAMES[v] for e, v in zip(ELEMENTS, levels)}
            fh.write(json.dumps({"id": cid, "call": {"account": account, "stage": stage, "summary": text},
                                 "label": card}) + "\n")

    cards = [{e: LEVEL_NAMES[v] for e, v in zip(ELEMENTS, lv)} for _, _, _, lv, _ in CALLS]
    print(f"wrote {len(CALLS)} calls -> {out}")
    print("levels:", dict(Counter(v for c in cards for v in c.values())))
    ready = [CALLS[i][1] for i, c in enumerate(cards) if forecast_ready(c)]
    print(f"forecast-ready: {len(ready)} {ready}")


if __name__ == "__main__":
    main()
