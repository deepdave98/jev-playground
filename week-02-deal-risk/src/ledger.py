"""The ledger: 20 open deals, 73 events, every label written by hand.

Events follow the AckDB ledger format: subject first, a typed prefix on
anything that isn't a person doing something, raw timestamps left raw, and
the provider in brackets at the end.

The first five deals are the ones on AckDB's at-risk demo (Datacore,
Cloudmark, Ironbridge, Precision, Vantage), rebuilt as full ledgers so the
reasons on that screen have to be earned from events. Everything else is
made up, including every person.

Each event is (id, timestamp, source, text, signal, severity, exec_engaged).
`expect` is the risk verdict I meant each deal to have. main() checks the
rule in spec.py agrees before writing anything, so a labelling slip fails
loudly here instead of quietly moving a benchmark number.

    python3 src/ledger.py
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from spec import assess  # noqa: E402

DEALS = [
    dict(id="D01", account="Datacore", arr=185_000, stage="Negotiation", kind="new",
         close_date="2026-11-14", champion="Rafael Mendes, Data Platform Lead",
         expect=["no_exec_30d"],
         events=[
             ("E001", "2026-08-15T15:04:00Z", "fireflies",
              "Meeting: Datacore exec alignment between Tomás Reyes, Rafael Mendes and Ingrid Solberg (CTO) (45 min, zoom). Summary: Ingrid confirmed the platform is on the Q4 roadmap and asked for a security review before anything gets signed.",
              "momentum", "none", True),
             ("E002", "2026-09-03T10:12:00Z", "gmail",
              "Email: “SSO config questions” from Rafael Mendes to Arjun Nair (3 in thread, gmail). “Can you confirm SCIM works with our Okta groups before we set up the pilot tenant?”",
              "routine", "none", False),
             ("E003", "2026-09-11T16:30:00Z", "fireflies",
              "Meeting: Datacore pilot check-in between Arjun Nair and Rafael Mendes (30 min, google_meet). Summary: pilot tenant is live, two analysts onboarded, Rafael wants dashboards by next week.",
              "momentum", "none", False),
             ("E004", "2026-09-17T09:41:00Z", "gmail",
              "Email: “Pilot scope” from Rafael Mendes to Arjun Nair, cc Ingrid Solberg (5 in thread, gmail). “Looping Ingrid in so she has the scope doc. Nothing needed from her yet.”",
              "routine", "none", False),
             ("E005", "2026-09-19T15:02:11Z", "web",
              "Rafael Mendes visited /docs/dashboards 4 times at 2026-09-19T15:02:11.204Z",
              "routine", "none", False),
             ("E006", "2026-09-23T13:20:00Z", "slack",
              "Rafael Mendes posted in #ext-datacore: “dashboards look good, sharing with the analysts tomorrow” (2 reactions)",
              "momentum", "none", False),
         ]),

    dict(id="D02", account="Cloudmark", arr=94_000, stage="Renewal", kind="renewal",
         close_date="2026-12-01", champion="Nadia Petrova, Support Ops Manager",
         expect=["escalations"],
         events=[
             ("E007", "2026-09-08T11:15:00Z", "zendesk",
              "Ticket #51720 opened by Nadia Petrova: “Routing rules not applying to new inbox” (priority: normal, zendesk)",
              "escalation", "watch", False),
             ("E008", "2026-09-12T08:02:00Z", "zendesk",
              "Ticket #51720 escalated to P1 by Nadia Petrova: “Still broken after 4 days, agents are hand-assigning 300 tickets a day” (zendesk)",
              "escalation", "serious", False),
             ("E009", "2026-09-18T06:47:00Z", "zendesk",
              "Ticket #52044 escalated to P1 by Omar Haddad: “SLA timers stopped counting for the EMEA queue, we missed 40 SLAs overnight” (zendesk)",
              "escalation", "serious", False),
             ("E010", "2026-09-19T17:30:00Z", "gmail",
              "Email: “Re: ticket #52044” from Hannah Lindqvist to Nadia Petrova (5 in thread, gmail). “Engineering has a fix in review, I'll update you by end of day tomorrow.”",
              "routine", "none", False),
             ("E011", "2026-09-22T09:41:52Z", "web",
              "Nadia Petrova visited /status 7 times at 2026-09-22T09:41:52.117Z",
              "escalation", "watch", False),
         ]),

    dict(id="D03", account="Ironbridge", arr=240_000, stage="Evaluation", kind="new",
         close_date="2026-10-30", champion="Dana Whitfield, Director of RevOps",
         expect=["competitor"],
         events=[
             ("E012", "2026-09-09T14:00:00Z", "fireflies",
              "Meeting: Ironbridge technical evaluation between Arjun Nair and Dana Whitfield (52 min, zoom). Summary: Dana said the team trialled Hexline in August and liked its Snowflake connector. She wants a side by side before the steering committee.",
              "competitor", "serious", False),
             ("E013", "2026-09-15T12:25:00Z", "gmail",
              "Email: “Pricing comparison” from Dana Whitfield to Tomás Reyes (4 in thread, gmail). “Hexline came in about 30% under your number for the same seat count. Is there room here?”",
              "competitor", "serious", False),
             ("E014", "2026-09-17T15:00:00Z", "fireflies",
              "Meeting: Ironbridge steering committee between Tomás Reyes, Dana Whitfield and Paul Okonkwo (VP Sales) (35 min, zoom). Summary: Paul asked how quickly reps would see enriched accounts and was positive on the roadmap.",
              "momentum", "none", True),
             ("E015", "2026-09-22T10:05:00Z", "salesforce",
              "Opportunity: Ironbridge Platform moved Discovery to Evaluation ($240K ARR, close 2026-10-30)",
              "momentum", "none", False),
             ("E016", "2026-09-24T16:10:07Z", "web",
              "Dana Whitfield visited /pricing at 2026-09-24T16:10:07.882Z",
              "routine", "none", False),
         ]),

    dict(id="D04", account="Precision", arr=62_000, stage="Renewal", kind="renewal",
         close_date="2026-09-28", champion="Lena Hoffmann, Customer Support Lead",
         expect=["escalations", "closing_with_issues"],
         events=[
             ("E017", "2026-09-10T13:22:00Z", "zendesk",
              "Ticket #51933 escalated to P1 by Lena Hoffmann: “Macros deleting internal notes on save, agents losing context on every escalation” (zendesk)",
              "escalation", "serious", False),
             ("E018", "2026-09-16T07:55:00Z", "zendesk",
              "Ticket #52101 escalated to P1 by Lena Hoffmann: “Search returns nothing for tickets older than 30 days” (zendesk)",
              "escalation", "serious", False),
             ("E019", "2026-09-20T00:00:00Z", "stripe",
              "Subscription: Precision renews 2026-09-28 at $62,000/yr, 50 seats, auto-renew on (stripe)",
              "routine", "none", False),
             ("E020", "2026-09-23T15:48:00Z", "gmail",
              "Email: “Before we renew” from Lena Hoffmann to Hannah Lindqvist (2 in thread, gmail). “Both tickets are still open. I need to know they're fixed before I sign off on the renewal Friday.”",
              "escalation", "serious", False),
         ]),

    dict(id="D05", account="Vantage", arr=128_000, stage="Renewal", kind="renewal",
         close_date="2027-01-15", champion="Declan Moore, RevOps Lead",
         expect=["champion_left"],
         events=[
             ("E021", "2026-09-02T14:30:00Z", "fireflies",
              "Meeting: Vantage QBR between Hannah Lindqvist, Declan Moore and Sofia Marchetti (COO) (40 min, google_meet). Summary: usage up 22% quarter on quarter. Sofia asked about adding the finance team next year.",
              "momentum", "none", True),
             ("E022", "2026-09-14T08:00:00Z", "linkedin",
              "Declan Moore is now Director of RevOps at Kestrel Labs, previously RevOps Lead at Vantage (linkedin)",
              "champion_exit", "serious", False),
             ("E023", "2026-09-16T11:12:00Z", "slack",
              "Hannah Lindqvist posted in #ext-vantage: “Hi all, with Declan moving on, who should we loop in on the renewal?” (0 replies)",
              "champion_exit", "watch", False),
             ("E024", "2026-09-21T11:03:44Z", "web",
              "Priya Anand visited /docs/admin at 2026-09-21T11:03:44.019Z",
              "routine", "none", False),
         ]),

    dict(id="D06", account="Halcyon", arr=150_000, stage="Negotiation", kind="new",
         close_date="2027-02-15", champion="Marcus Bell, Sales Ops Manager",
         expect=["stalled"],
         events=[
             ("E025", "2026-09-05T16:00:00Z", "fireflies",
              "Meeting: Halcyon commercial review between Tomás Reyes, Marcus Bell and Grace Liu (CFO) (30 min, zoom). Summary: Grace approved the budget line, pending legal review.",
              "momentum", "none", True),
             ("E026", "2026-09-18T19:14:00Z", "gmail",
              "Email: “Update on timing” from Grace Liu to Tomás Reyes (3 in thread, gmail). “The board froze all new software spend until next fiscal year after last week's results. I'm sorry, we'll have to revisit in February.”",
              "stall", "serious", True),
             ("E027", "2026-09-19T09:30:00Z", "salesforce",
              "Opportunity: Halcyon Platform close date moved from 2026-10-20 to 2027-02-15 by Tomás Reyes ($150K ARR)",
              "stall", "serious", False),
             ("E028", "2026-09-22T13:27:10Z", "web",
              "Marcus Bell visited /blog/roi-calculator at 2026-09-22T13:27:10.551Z",
              "routine", "none", False),
         ]),

    dict(id="D07", account="Tidewater", arr=76_000, stage="Renewal", kind="renewal",
         close_date="2026-11-30", champion="Ben Okafor, Support Manager",
         expect=["stalled"],
         events=[
             ("E029", "2026-09-04T00:00:00Z", "stripe",
              "Subscription: Tidewater changed plan from 80 to 45 seats, effective 2026-10-01 (stripe)",
              "stall", "serious", False),
             ("E030", "2026-09-06T10:20:00Z", "gmail",
              "Email: “Seat count” from Ben Okafor to Hannah Lindqvist (2 in thread, gmail). “We had a restructure and lost half the support team. Keeping the core seats for now.”",
              "stall", "watch", False),
             ("E031", "2026-09-17T14:05:00Z", "zendesk",
              "Ticket #52077 opened by Ben Okafor: “How do I reassign tickets from deactivated agents?” (priority: low, zendesk)",
              "routine", "none", False),
         ]),

    dict(id="D08", account="Keystone", arr=210_000, stage="Negotiation", kind="new",
         close_date="2026-10-15", champion="Yuki Tanaka, Director of Support",
         expect=["competitor"],
         events=[
             ("E032", "2026-09-10T17:00:00Z", "fireflies",
              "Meeting: Keystone final review between Tomás Reyes, Yuki Tanaka and Robert Asante (VP Customer Experience) (45 min, zoom). Summary: Robert raised concerns about implementation time and said Corvid offered a two week go-live.",
              "competitor", "serious", True),
             ("E033", "2026-09-23T08:31:00Z", "gmail",
              "Email: “Decision” from Robert Asante to Tomás Reyes (1 in thread, gmail). “We've decided to move forward with Corvid. Thank you for the time your team put in.”",
              "competitor", "critical", True),
             ("E034", "2026-09-24T00:00:00Z", "salesforce",
              "Opportunity: Keystone Platform unchanged at Negotiation ($210K ARR, close 2026-10-15), last activity 1 day ago",
              "routine", "none", False),
         ]),

    dict(id="D09", account="Lumen Health", arr=140_000, stage="Evaluation", kind="new",
         close_date="2026-11-20", champion="Amara Nwosu, Patient Support Manager",
         expect=[],
         events=[
             ("E035", "2026-09-11T15:00:00Z", "fireflies",
              "Meeting: Lumen Health discovery between Tomás Reyes, Amara Nwosu and Daniel Frost (CEO) (50 min, zoom). Summary: Daniel wants patient response times under 2 hours by January and asked for a HIPAA addendum.",
              "momentum", "none", True),
             ("E036", "2026-09-16T10:40:00Z", "gmail",
              "Email: “Re: vendors” from Amara Nwosu to Tomás Reyes (5 in thread, gmail). “We looked at Tallyworks last year and it didn't come close on routing. Not considering them.”",
              "momentum", "none", False),
             ("E037", "2026-09-19T12:00:00Z", "documents",
              "Doc: “Lumen x Platform HIPAA addendum” edited by Tomás Reyes and Amara Nwosu, 2 collaborators (google_docs)",
              "momentum", "none", False),
             ("E038", "2026-09-24T10:15:33Z", "web",
              "Amara Nwosu visited /security at 2026-09-24T10:15:33.690Z",
              "routine", "none", False),
         ]),

    dict(id="D10", account="Marlow", arr=88_000, stage="Renewal", kind="renewal",
         close_date="2026-11-20", champion="Chloe Durand, Support Operations Manager",
         expect=[],
         events=[
             ("E039", "2026-09-06T22:10:00Z", "zendesk",
              "Ticket #51688 escalated to P1 by Chloe Durand: “Email channel down, customers getting bounce-backs” (zendesk)",
              "escalation", "serious", False),
             ("E040", "2026-09-07T01:45:00Z", "zendesk",
              "Ticket #51688 solved by Arjun Nair: root cause was an expired DNS record on their side, fixed on the call (zendesk)",
              "routine", "none", False),
             ("E041", "2026-09-12T09:18:00Z", "slack",
              "Chloe Durand posted in #ext-marlow: “thanks Arjun for jumping on that so fast, saved our weekend” (4 reactions)",
              "momentum", "none", False),
             ("E042", "2026-09-20T00:00:00Z", "stripe",
              "Subscription: Marlow renews 2026-11-20 at $88,000/yr, 70 seats, auto-renew on (stripe)",
              "routine", "none", False),
         ]),

    dict(id="D11", account="Pinecrest", arr=175_000, stage="Negotiation", kind="new",
         close_date="2026-11-05", champion="Jonah Adeyemi, RevOps Manager",
         expect=[],
         events=[
             ("E043", "2026-09-08T16:00:00Z", "fireflies",
              "Meeting: Pinecrest pricing call between Tomás Reyes, Jonah Adeyemi and Rachel Kim (CRO) (35 min, zoom). Summary: Rachel agreed the pricing and asked for a November start date.",
              "momentum", "none", True),
             ("E044", "2026-09-15T08:00:00Z", "linkedin",
              "Jonah Adeyemi is now Head of Revenue Operations at Pinecrest, previously RevOps Manager at Pinecrest (linkedin)",
              "momentum", "none", False),
             ("E045", "2026-09-18T11:22:00Z", "gmail",
              "Email: “Congrats + next steps” from Jonah Adeyemi to Tomás Reyes (3 in thread, gmail). “Thanks! This gives me budget authority, so we can skip the extra approval step.”",
              "momentum", "none", False),
             ("E046", "2026-09-23T14:50:00Z", "documents",
              "Doc: “Pinecrest order form” edited by Rachel Kim and Tomás Reyes, 2 collaborators (docusign)",
              "momentum", "none", True),
         ]),

    dict(id="D12", account="Oakridge", arr=64_000, stage="Evaluation", kind="new",
         close_date="2026-11-10", champion="Sam Whitaker, Support Lead",
         expect=[],
         events=[
             ("E047", "2026-09-09T13:12:00Z", "hubspot",
              "Form: “Start a trial” submitted by Sam Whitaker (utm_source=google, utm_campaign=support-automation)",
              "momentum", "none", False),
             ("E048", "2026-09-14T08:00:00Z", "linkedin",
              "Ellie Brooks is now Support Specialist at Harbor Freight Co, previously Support Agent at Oakridge (linkedin)",
              "routine", "none", False),
             ("E049", "2026-09-20T15:30:00Z", "fireflies",
              "Meeting: Oakridge trial review between Arjun Nair and Sam Whitaker (25 min, google_meet). Summary: trial is going well and Sam wants to add two more agents.",
              "momentum", "none", False),
         ]),

    dict(id="D13", account="Summit Labs", arr=120_000, stage="Evaluation", kind="new",
         close_date="2026-11-25", champion="Irene Castillo, Support Ops Manager",
         expect=[],
         events=[
             ("E050", "2026-09-13T15:00:00Z", "fireflies",
              "Meeting: Summit Labs exec briefing between Tomás Reyes, Irene Castillo and Victor Lam (VP Support) (30 min, zoom). Summary: Victor wants a phased rollout starting with tier 1.",
              "momentum", "none", True),
             ("E051", "2026-09-22T10:02:00Z", "gmail",
              "Email: “Rollout plan v2” from Irene Castillo to Tomás Reyes, cc Victor Lam (6 in thread, gmail). “Attached the phased plan. Victor is cc'd for visibility.”",
              "momentum", "none", False),
             ("E052", "2026-09-24T14:48:02Z", "web",
              "Irene Castillo visited /pricing at 2026-09-24T14:48:02.395Z",
              "routine", "none", False),
         ]),

    dict(id="D14", account="Brightwater", arr=105_000, stage="Renewal", kind="renewal",
         close_date="2026-12-15", champion="Fatima Zahra, Support Manager",
         expect=[],
         events=[
             ("E053", "2026-09-10T14:00:00Z", "fireflies",
              "Meeting: Brightwater renewal kickoff between Hannah Lindqvist, Fatima Zahra and Owen Price (VP Operations) (30 min, google_meet). Summary: Owen is happy with results and wants the renewal done early.",
              "momentum", "none", True),
             ("E054", "2026-09-18T12:40:00Z", "slack",
              "Fatima Zahra posted in #ext-brightwater: “someone on our team asked what Hexline charges, do you have a comparison sheet?” (0 reactions)",
              "competitor", "watch", False),
             ("E055", "2026-09-21T09:05:00Z", "gmail",
              "Email: “Renewal paperwork” from Owen Price to Hannah Lindqvist (2 in thread, gmail). “Send it over, I'll sign this week.”",
              "momentum", "none", True),
         ]),

    dict(id="D15", account="Cascade", arr=55_000, stage="Discovery", kind="new",
         close_date="2026-12-10", champion="Leo Martins, Support Lead",
         expect=[],
         events=[
             ("E056", "2026-09-15T18:22:00Z", "hubspot",
              "Form: “Book a demo” submitted by Leo Martins (utm_source=linkedin, utm_campaign=q3-support)",
              "routine", "none", False),
             ("E057", "2026-09-19T16:00:00Z", "fireflies",
              "Meeting: Cascade intro between Tomás Reyes and Leo Martins (30 min, zoom). Summary: 12 agents on a shared inbox today, wants routing and macros.",
              "routine", "none", False),
             ("E058", "2026-09-23T17:20:45Z", "web",
              "Leo Martins visited /pricing at 2026-09-23T17:20:45.118Z",
              "routine", "none", False),
         ]),

    dict(id="D16", account="Redwood", arr=230_000, stage="Renewal", kind="renewal",
         close_date="2027-01-31", champion="Mei Chen, Director of Support",
         expect=[],
         events=[
             ("E059", "2026-09-19T14:00:00Z", "fireflies",
              "Meeting: Redwood QBR between Hannah Lindqvist, Mei Chen and Andre Silva (COO) (55 min, zoom). Summary: Andre wants to roll the platform out to the Brazil and Mexico teams next quarter, roughly 60 more seats.",
              "momentum", "none", True),
             ("E060", "2026-09-22T10:00:00Z", "salesforce",
              "Opportunity: Redwood Expansion created by Hannah Lindqvist ($95K ARR, Stage: Discovery)",
              "momentum", "none", False),
             ("E061", "2026-09-24T12:14:00Z", "slack",
              "Mei Chen posted in #ext-redwood: “LatAm leads keep asking when they get access” (6 reactions)",
              "momentum", "none", False),
         ]),

    dict(id="D17", account="Fairhaven", arr=92_000, stage="Negotiation", kind="new",
         close_date="2026-10-31", champion="Nikhil Rao, IT Manager",
         expect=[],
         events=[
             ("E062", "2026-09-12T11:30:00Z", "gmail",
              "Email: “Security questionnaire” from Nikhil Rao to Arjun Nair (4 in thread, gmail). “Our security team signed off. Only open item is the DPA.”",
              "momentum", "none", False),
             ("E063", "2026-09-18T15:00:00Z", "documents",
              "Doc: “Fairhaven MSA redlines” edited by Tomás Reyes and Kara Benson (Legal Counsel), 2 collaborators (google_docs)",
              "momentum", "none", False),
             ("E064", "2026-09-23T16:45:00Z", "gmail",
              "Email: “DPA signed” from Kara Benson to Tomás Reyes (2 in thread, gmail). “Countersigned DPA attached. MSA should be back by Monday.”",
              "momentum", "none", False),
         ]),

    dict(id="D18", account="Northgate", arr=160_000, stage="Negotiation", kind="new",
         close_date="2026-11-01", champion="Tariq Hussain, Support Ops Manager",
         expect=[],
         events=[
             ("E065", "2026-09-11T14:00:00Z", "fireflies",
              "Meeting: Northgate scoping between Arjun Nair and Tariq Hussain (40 min, zoom). Summary: integration with their Service Cloud instance confirmed feasible.",
              "momentum", "none", False),
             ("E066", "2026-09-22T07:58:00Z", "gmail",
              "Email: “Timeline” from Helena Voss (Chief Customer Officer) to Tomás Reyes (1 in thread, gmail). “Our board is pushing hard on support costs. I need this live by November 15 or we have a problem. What do you need from us to get there?”",
              "momentum", "none", True),
             ("E067", "2026-09-24T09:00:00Z", "salesforce",
              "Opportunity: Northgate Platform moved Evaluation to Negotiation ($160K ARR, close 2026-11-01)",
              "momentum", "none", False),
         ]),

    dict(id="D19", account="Silverline", arr=300_000, stage="Evaluation", kind="new",
         close_date="2026-12-20", champion="Grace Obi, Director of Customer Support",
         expect=[],
         events=[
             ("E068", "2026-08-27T15:00:00Z", "fireflies",
              "Meeting: Silverline executive sponsor call between Tomás Reyes, Grace Obi and William Hart (SVP Customer Success) (30 min, zoom). Summary: William confirmed he is sponsoring the project and will join the final review.",
              "momentum", "none", True),
             ("E069", "2026-09-12T14:00:00Z", "fireflies",
              "Meeting: Silverline technical workshop between Arjun Nair and Grace Obi (90 min, zoom). Summary: mapped 14 workflows, two need custom webhooks.",
              "routine", "none", False),
             ("E070", "2026-09-20T12:33:18Z", "web",
              "Grace Obi visited /docs/webhooks 5 times at 2026-09-20T12:33:18.460Z",
              "routine", "none", False),
         ]),

    dict(id="D20", account="Driftwood", arr=118_000, stage="Renewal", kind="renewal",
         close_date="2026-12-05", champion="Ravi Menon, Support Operations Lead",
         expect=[],
         events=[
             ("E071", "2026-09-08T15:30:00Z", "fireflies",
              "Meeting: Driftwood mid-term review between Hannah Lindqvist, Ravi Menon and Julia Stein (VP Customer Care) (35 min, google_meet). Summary: Julia said the platform is one of the tools they are keeping through the cost review.",
              "momentum", "none", True),
             ("E072", "2026-09-16T18:05:00Z", "slack",
              "Ravi Menon posted in #ext-driftwood: “heads up, company announced 10% layoffs today. our team isn't affected and the renewal is still on” (1 reaction)",
              "stall", "watch", False),
             ("E073", "2026-09-22T10:30:00Z", "zendesk",
              "Ticket #52188 opened by Ravi Menon: “Can we export last quarter's CSAT by agent?” (priority: low, zendesk)",
              "routine", "none", False),
         ]),
]


def rows():
    """Deals with events as dicts, labels split out from what a model sees."""
    for d in DEALS:
        deal = {k: d[k] for k in ("id", "account", "arr", "stage", "kind",
                                   "close_date", "champion")}
        events = []
        for eid, ts, source, text, signal, severity, exec_ in d["events"]:
            events.append({"id": eid, "ts": ts, "source": source, "text": text,
                           "label": {"signal": signal, "severity": severity,
                                     "exec_engaged": exec_}})
        yield deal, events, d["expect"]


def main():
    out = pathlib.Path(__file__).resolve().parents[1] / "data" / "ledger.jsonl"
    wrong, n_events, seen = [], 0, set()

    with out.open("w") as fh:
        for deal, events, expect in rows():
            for e in events:
                assert e["id"] not in seen, f"duplicate event id {e['id']}"
                seen.add(e["id"])
            judged = [{**e, **e["label"]} for e in events]
            reasons = assess(deal, judged)
            if sorted(reasons) != sorted(expect):
                wrong.append((deal["account"], expect, reasons))
            label = {"at_risk": bool(reasons), "reasons": reasons}
            fh.write(json.dumps({"deal": deal, "label": label, "events": events}) + "\n")
            n_events += len(events)

    if wrong:
        for account, expect, got in wrong:
            print(f"  {account}: meant {expect}, rule says {got}")
        sys.exit("labels and the rule disagree, fix the labels before benchmarking")

    at_risk = [d for d, _, x in rows() if x]
    print(f"wrote {len(DEALS)} deals, {n_events} events -> {out}")
    print(f"{len(at_risk)} at risk, ${sum(d['arr'] for d in at_risk):,} of ARR")


if __name__ == "__main__":
    main()
