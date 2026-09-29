"""The answer key: 60 replies to an outbound sequence, every label by hand.

Each reply is what came back after we emailed someone cold. Prospects,
companies and contacts are all made up. Replies arrived between September 24
and 28, 2026, which matters for the out of office dates.

The labels are category, opt_out and meeting_intent. Out of office replies
also carry the return date, and wrong_person replies the contact they point
to, so the extraction step has something to be scored against.

    python3 src/replies.py
"""

import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from spec import QUESTIONS, route  # noqa: E402

# (id, prospect, received, our subject, reply, category, opt_out, meeting_intent, extra)
REPLIES = [
    # interested
    ("R01", "Hannah Voss, RevOps Manager, Northwind", "2026-09-24T14:02:00Z", "Lead routing at Northwind",
     "Sure, what does pricing look like for a team of about 40?",
     "interested", False, "curious", {}),
    ("R02", "Omar Farouk, Head of Growth, Tidepool", "2026-09-24T16:40:00Z", "Quick question",
     "Do you have a case study from a company our size? If it's relevant I'll take a look.",
     "interested", False, "curious", {}),
    ("R03", "Lucia Romero, VP Sales, Kestrel Labs", "2026-09-25T09:15:00Z", "Following up",
     "Interesting. How is this different from what we already get out of Salesforce?",
     "interested", False, "curious", {}),
    ("R04", "Ben Adler, Director of Sales Ops, Quarry Health", "2026-09-25T11:30:00Z", "Re: routing rules",
     "Interested, but please stop emailing my colleague Dan Ortiz, he's not involved in this. Can you send pricing?",
     "interested", False, "curious", {}),
    ("R05", "Priya Nair, RevOps Lead, Halcyon Bio", "2026-09-25T13:05:00Z", "Lead routing at Halcyon",
     "This is timely. Happy to chat, I'll need to pull in our ops lead.",
     "interested", False, "open", {}),
    ("R06", "Grant Ellis, VP Revenue, Fernway", "2026-09-25T15:22:00Z", "Following up",
     "Sounds interesting, I'd be up for a call at some point.",
     "interested", False, "open", {}),
    ("R07", "Mei Tanaka, Sales Ops Manager, Orbital Freight", "2026-09-26T08:48:00Z", "Quick question",
     "We've been looking at exactly this problem. Would be good to talk.",
     "interested", False, "open", {}),
    ("R08", "Diego Salas, Head of Sales, Vela Pagos", "2026-09-26T10:10:00Z", "Enrutamiento de leads",
     "Me interesa. ¿Podemos hablar en algún momento?",
     "interested", False, "open", {}),
    ("R09", "Rachel Kim, CRO, Pinecrest", "2026-09-26T12:31:00Z", "Re: routing rules",
     "Tuesday at 2pm ET works. Send an invite.",
     "interested", False, "ready", {}),
    ("R10", "Tom Becker, VP Sales, Halvorsen", "2026-09-26T14:00:00Z", "Following up",
     "Send me your calendar link.",
     "interested", False, "ready", {}),
    ("R11", "Anika Rao, RevOps Director, Lumen Health", "2026-09-27T09:02:00Z", "Lead routing at Lumen",
     "I can do Thursday morning or Friday after 3. Pick one.",
     "interested", False, "ready", {}),
    ("R12", "Chris Doyle, Head of Growth, Brightline", "2026-09-27T11:44:00Z", "Quick question",
     "Booked a slot on your calendar for Wednesday.",
     "interested", False, "ready", {}),

    # not now
    ("R13", "Nadia Petrova, Support Ops Manager, Cloudmark", "2026-09-24T10:20:00Z", "Following up",
     "Not a priority this quarter. Try me in January.",
     "not_now", False, "none", {}),
    ("R14", "Leo Martins, Support Lead, Cascade", "2026-09-24T12:55:00Z", "Quick question",
     "We're mid-migration to a new CRM until November. Circle back after that.",
     "not_now", False, "none", {}),
    ("R15", "Grace Liu, CFO, Halvard", "2026-09-25T08:30:00Z", "Lead routing at Halvard",
     "Budget is locked until the new fiscal year in February. Happy to talk then.",
     "not_now", False, "open", {}),
    ("R16", "Sam Whitaker, Support Lead, Oakridge", "2026-09-25T17:12:00Z", "Following up",
     "Bad timing, we just went through a reorg. Maybe Q2.",
     "not_now", False, "none", {}),
    ("R17", "Ingrid Solberg, CTO, Datacore", "2026-09-26T07:45:00Z", "Re: routing rules",
     "Ping me after our board meeting on the 20th.",
     "not_now", False, "none", {}),
    ("R18", "Owen Price, VP Operations, Brightwater", "2026-09-26T16:05:00Z", "Quick question",
     "Interesting, but we can't take on anything new until our product launch is out in December. "
     "Would love to revisit then.",
     "not_now", False, "open", {}),
    ("R19", "Julia Stein, VP Customer Care, Driftwood", "2026-09-27T10:18:00Z", "Following up",
     "Maybe next year. In the meantime please take me off this sequence.",
     "not_now", True, "none", {}),
    ("R20", "Victor Lam, VP Support, Summit Labs", "2026-09-27T13:33:00Z", "Lead routing at Summit",
     "Loop back in the spring once we've hired a RevOps lead.",
     "not_now", False, "none", {}),

    # wrong person
    ("R21", "Kai Anders, Sales Manager, Northwind", "2026-09-24T09:40:00Z", "Lead routing at Northwind",
     "I'm not the right person. Sarah Chen runs RevOps, sarah.chen@northwind.io.",
     "wrong_person", False, "none", {"referral": "sarah.chen@northwind.io"}),
    ("R22", "Ellie Brooks, Account Executive, Harbor Freight Co", "2026-09-24T15:15:00Z", "Quick question",
     "Wrong person, try our VP Sales, Marcus Webb.",
     "wrong_person", False, "none", {"referral": "Marcus Webb"}),
    ("R23", "Jonah Adeyemi, RevOps Analyst, Tidepool", "2026-09-25T10:50:00Z", "Following up",
     "Not me, but this sounds useful. Loop in Priya Shah, she owns our data stack.",
     "wrong_person", False, "none", {"referral": "Priya Shah"}),
    ("R24", "Carla Mendes, Sales Director, Acme Logistics", "2026-09-25T14:25:00Z", "Re: routing rules",
     "I've left Acme Logistics. Please reach out to maria.lopez@acmelogistics.com, who took over my accounts.",
     "wrong_person", False, "none", {"referral": "maria.lopez@acmelogistics.com"}),
    ("R25", "Peter Novak, VP Sales, Brightline", "2026-09-26T09:00:00Z", "Lead routing at Brightline",
     "I no longer work at Brightline.",
     "wrong_person", False, "none", {"referral": None}),
    ("R26", "Fiona Walsh, Sales Ops, Halvorsen", "2026-09-26T11:11:00Z", "Quick question",
     "Forwarding to Tom, he handles vendor evaluations. tom.becker@halvorsen.com",
     "wrong_person", False, "none", {"referral": "tom.becker@halvorsen.com"}),
    ("R27", "Raj Patel, Growth Marketer, Kettlebridge", "2026-09-27T08:20:00Z", "Following up",
     "You want our ops team for this. ops@kettlebridge.com",
     "wrong_person", False, "none", {"referral": "ops@kettlebridge.com"}),
    ("R28", "Nora Quinn, Office Manager, Stillwater", "2026-09-27T15:50:00Z", "Lead routing at Stillwater",
     "Please contact our procurement team instead: vendors@stillwater.co",
     "wrong_person", False, "none", {"referral": "vendors@stillwater.co"}),

    # objection, with an opt-out
    ("R29", "Mark Hollis, VP Sales, Graniteworks", "2026-09-24T11:05:00Z", "Following up",
     "Not interested. Please remove me from your list.",
     "objection", True, "none", {}),
    ("R30", "Tessa Byrne, RevOps Manager, Corbel", "2026-09-24T13:40:00Z", "Quick question",
     "Unsubscribe",
     "objection", True, "none", {}),
    ("R31", "Dev Malhotra, Head of Sales, Arclight", "2026-09-25T09:58:00Z", "Lead routing at Arclight",
     "STOP",
     "objection", True, "none", {}),
    ("R32", "Sofie Jansen, Data Protection Officer, Veldt", "2026-09-25T12:12:00Z", "Re: routing rules",
     "Please delete all personal data you hold about me under GDPR Article 17 and confirm when done.",
     "objection", True, "none", {}),
    ("R33", "Aaron Fisk, Sales Director, Redpoint Freight", "2026-09-26T08:05:00Z", "Following up",
     "Take me off this. Third email this week.",
     "objection", True, "none", {}),
    ("R34", "Camille Durand, Directrice commerciale, Lyonnaise Data", "2026-09-26T10:44:00Z", "Following up",
     "Merci, mais ce n'est pas pour nous. Merci de ne plus me contacter.",
     "objection", True, "none", {}),
    ("R35", "Wes Harlan, Operations Lead, Tallmark", "2026-09-26T17:30:00Z", "Quick question",
     "Remove.",
     "objection", True, "none", {}),
    ("R36", "Jonas Weber, Vertriebsleiter, Nordbahn Logistik", "2026-09-27T07:12:00Z", "Lead routing at Nordbahn",
     "Bitte keine weiteren E-Mails.",
     "objection", True, "none", {}),

    # objection, no opt-out
    ("R37", "Lena Hoffmann, Customer Support Lead, Precision", "2026-09-24T10:02:00Z", "Following up",
     "Not interested.",
     "objection", False, "none", {}),
    ("R38", "Robert Asante, VP Customer Experience, Keystone", "2026-09-24T14:48:00Z", "Quick question",
     "We're happy with Hexline, thanks.",
     "objection", False, "none", {}),
    ("R39", "Ruth Okoye, Founder, Pellucid", "2026-09-25T11:26:00Z", "Lead routing at Pellucid",
     "Too expensive for a team our size.",
     "objection", False, "none", {}),
    ("R40", "Stuart Lang, Head of RevOps, Marlowe", "2026-09-25T16:37:00Z", "Following up",
     "Great, the fifth email this week. Really appreciated.",
     "objection", False, "none", {}),
    ("R41", "Beatriz Costa, Sales Manager, Oakridge", "2026-09-26T09:39:00Z", "Re: routing rules",
     "Dana moved to a different role and I've taken over her territory. This isn't something we'd use.",
     "objection", False, "none", {}),
    ("R42", "Ian Petrie, CTO, Framewell", "2026-09-26T13:20:00Z", "Quick question",
     "We built something in-house for this last year.",
     "objection", False, "none", {}),
    ("R43", "Hollis Grant, COO, Wrenfield", "2026-09-27T10:55:00Z", "Following up",
     "No budget for new tools, and honestly no need either.",
     "objection", False, "none", {}),
    ("R44", "Amelia Stone, Founder, Tinderbox Studio", "2026-09-27T14:14:00Z", "Lead routing at Tinderbox",
     "Not for us. We're a 6-person team.",
     "objection", False, "none", {}),

    # out of office
    ("R45", "Nikhil Rao, IT Manager, Fairhaven", "2026-09-24T08:00:00Z", "Following up",
     "I'm out of the office until Monday, October 5 with limited access to email.",
     "out_of_office", False, "none", {"return_date": "2026-10-05"}),
    ("R46", "Helena Voss, Chief Customer Officer, Northgate", "2026-09-24T08:01:00Z", "Quick question",
     "Thank you for your message. I am on parental leave until January 12, 2027. For urgent matters "
     "please contact jon.park@northgatehq.com.",
     "out_of_office", False, "none", {"return_date": "2027-01-12"}),
    ("R47", "Paul Okonkwo, VP Sales, Ironbridge", "2026-09-25T06:30:00Z", "Lead routing at Ironbridge",
     "Auto-reply: I'm travelling for our sales kickoff and back on 10/08.",
     "out_of_office", False, "none", {"return_date": "2026-10-08"}),
    ("R48", "Katrin Vogel, Leiterin Vertrieb, Hafenwerk", "2026-09-25T06:31:00Z", "Following up",
     "Ich bin bis zum 9. Oktober nicht im Büro und habe keinen Zugriff auf meine E-Mails.",
     "out_of_office", False, "none", {"return_date": "2026-10-09"}),
    ("R49", "Marcus Bell, Sales Ops Manager, Halcyon", "2026-09-28T07:00:00Z", "Quick question",
     "Out until the 6th. Will reply when I'm back.",
     "out_of_office", False, "none", {"return_date": "2026-10-06"}),
    ("R50", "Tariq Hussain, Support Ops Manager, Northgate", "2026-09-28T07:01:00Z", "Re: routing rules",
     "I'm on PTO this week, returning Wednesday Sept 30.",
     "out_of_office", False, "none", {"return_date": "2026-09-30"}),
    ("R51", "Irene Castillo, Support Ops Manager, Summit Labs", "2026-09-26T06:15:00Z", "Lead routing at Summit",
     "On sabbatical, back November 2. For RevOps questions reach revops@clearpath.io.",
     "out_of_office", False, "none", {"return_date": "2026-11-02"}),
    ("R52", "Fatima Zahra, Support Manager, Brightwater", "2026-09-27T05:40:00Z", "Following up",
     "I'm away at a conference until Thursday 1 October.",
     "out_of_office", False, "none", {"return_date": "2026-10-01"}),
    ("R53", "Mei Chen, Director of Support, Redwood", "2026-09-28T05:05:00Z", "Quick question",
     "Out of office. Back 13 October.",
     "out_of_office", False, "none", {"return_date": "2026-10-13"}),

    # other automatic messages
    ("R54", "Gordon Frye, Sales Lead, Fernbrook", "2026-09-24T12:00:00Z", "Following up",
     "This mailbox is no longer monitored. Please direct enquiries to hello@fernbrook.com.",
     "auto_reply", False, "none", {}),
    ("R55", "Support, Brightwave", "2026-09-24T12:01:00Z", "Quick question",
     "Thanks for contacting Brightwave Support! Your ticket #88412 has been created. We aim to "
     "respond within 24 hours.",
     "auto_reply", False, "none", {}),
    ("R56", "Mail Delivery Subsystem", "2026-09-25T10:00:00Z", "Lead routing at Corvane",
     "Delivery Status Notification (Failure). The email account that you tried to reach does not exist.",
     "auto_reply", False, "none", {}),
    ("R57", "Info, Pellmore", "2026-09-26T09:00:00Z", "Following up",
     "Your message has been received. Due to high volume, responses may take 3-5 business days.",
     "auto_reply", False, "none", {}),
    ("R58", "Dylan Shaw, Head of Sales, Quillon", "2026-09-26T09:01:00Z", "Quick question",
     "This is an automated message. I only read email twice a day and will get back to you if needed.",
     "auto_reply", False, "none", {}),
    ("R59", "Mail Delivery Subsystem", "2026-09-27T10:00:00Z", "Re: routing rules",
     "Message blocked: the recipient's mailbox is full.",
     "auto_reply", False, "none", {}),
    ("R60", "Jess Halloran, RevOps Manager, Oldco", "2026-09-27T10:01:00Z", "Lead routing at Oldco",
     "This is an automated reply. I'm now using a new address, please update your records: "
     "j.halloran@newco.io.",
     "auto_reply", False, "none", {}),
]


def main():
    out = pathlib.Path(__file__).resolve().parents[1] / "data" / "replies.jsonl"
    cats = set(QUESTIONS["category"]["criteria"])
    intents = [c.split(":")[0] for c in QUESTIONS["meeting_intent"]["criteria"]]
    seen = set()
    with out.open("w") as fh:
        for rid, prospect, received, subject, text, cat, opt, intent, extra in REPLIES:
            assert rid not in seen, rid
            assert cat in cats and intent in intents, rid
            if cat == "out_of_office":
                assert "return_date" in extra, rid
            if cat == "wrong_person":
                assert "referral" in extra, rid
            seen.add(rid)
            fh.write(json.dumps({
                "id": rid,
                "reply": {"from": prospect, "received": received,
                          "in_reply_to": subject, "text": text},
                "label": {"category": cat, "opt_out": opt, "meeting_intent": intent, **extra},
            }) + "\n")

    labels = [r[5:8] for r in REPLIES]
    print(f"wrote {len(REPLIES)} replies -> {out}")
    print("category:", dict(Counter(c for c, _, _ in labels)))
    print("opt_out:", sum(o for _, o, _ in labels), "of", len(labels))
    print("route:", dict(Counter(route(*x) for x in labels)))


if __name__ == "__main__":
    main()
