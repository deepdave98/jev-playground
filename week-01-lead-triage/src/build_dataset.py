"""Builds leads.jsonl.

Every lead below was written and labelled by hand against rubric.md. No model
produced any label. That matters: if Claude had written the answer key, then
scoring Claude against it would measure agreement with itself.

Labels are the four judgments. Nothing stores a route. spec.route() computes
it from the labels, so the answer key and the models go through the same
function.

Roughly a third of these are deliberately awkward. Real inbound is mostly
awkward, and a test set of obvious cases would put every model at 100% and
tell you nothing.
"""

import json
import pathlib

# (id, company, headcount, title, email, source, message, activity,
#  disqualify, icp_fit, segment, intent)
LEADS = [
    # --- disqualify: job applicants -------------------------------------
    ("L001", "Segment", 1200, "Account Executive", "marcus.boyle@gmail.com", "contact_form",
     "Hi, I saw the Enterprise AE opening on your careers page. 6 years closing GTM software, "
     "president's club twice. Resume attached. Who should I send this to?",
     "1 page view: /careers", True, True, "enterprise", "none"),

    ("L002", "Freelance", None, "Software Engineer", "dev.priyanka@proton.me", "contact_form",
     "Looking for backend roles. I work in Go and Postgres and I like what you're building on the "
     "pipeline side. Are you hiring outside the US?",
     "2 page views: /careers, /engineering-blog", True, False, "smb", "none"),

    ("L003", "Northwestern University", 20000, "PhD Candidate", "r.okonkwo@u.northwestern.edu", "contact_form",
     "I'm writing a dissertation on firmographic data quality. Could you provide free academic access "
     "to your dataset for research purposes? Happy to cite you.",
     "3 page views: /data-coverage", True, False, "enterprise", "researching"),

    ("L004", "MIT Media Lab", 1100, "Research Assistant", "tlin@mit.edu", "demo_request",
     "Requesting a demo for a class project on sales automation. We have no budget, this is coursework.",
     "1 page view: /demo", True, False, "enterprise", "researching"),

    # --- disqualify: vendors and agencies -------------------------------
    ("L005", "GrowthLabs Digital", 24, "Head of Partnerships", "sam@growthlabsdigital.io", "contact_form",
     "We help B2B SaaS companies rank #1 for high-intent keywords. I ran an audit on your site and "
     "found 34 technical SEO issues. 15 minutes to walk you through them?",
     "1 page view: /", True, False, "smb", "none"),

    ("L006", "Devsource Global", 400, "Business Development", "arun@devsource-global.com", "contact_form",
     "We provide dedicated offshore engineering teams at $28/hour. Our clients include three YC "
     "companies. Can I send over some profiles?",
     "1 page view: /", True, True, "mid_market", "none"),

    ("L007", "Apex Talent Partners", 60, "Recruiting Director", "j.whitfield@apextalent.com", "contact_form",
     "Noticed you're scaling the sales org. We place enterprise AEs on a contingency basis, 20% fee, "
     "90 day guarantee. Worth a conversation?",
     "2 page views: /careers, /about", True, True, "smb", "none"),

    ("L008", "Cloudbridge Consulting", 310, "Salesforce Practice Lead", "dm@cloudbridge.consulting", "contact_form",
     "We're a Salesforce SI and several of our clients are asking about GTM data tooling. Would you be "
     "open to a referral partnership? We'd also like to pitch you on our own RevOps managed service.",
     "4 page views: /integrations/salesforce, /partners", True, True, "mid_market", "researching"),

    # --- disqualify: competitors ----------------------------------------
    ("L009", "Clay", 180, "RevOps Manager", "n.fischer@clay.com", "demo_request",
     "Interested in seeing how your waterfall enrichment compares. Can we get a demo and a copy of "
     "your coverage benchmarks?",
     "11 page views: /pricing, /data-coverage, /vs-competitors x3", True, True, "smb", "evaluating"),

    ("L010", "Apollo.io", 900, "Product Manager", "hchen@apollo.io", "contact_form",
     "Doing some market research on workflow builders. Could I get 30 minutes with someone on product "
     "to understand your architecture?",
     "7 page views: /product, /changelog x4", True, True, "mid_market", "researching"),

    # --- disqualify: spam ------------------------------------------------
    ("L011", "N/A", None, "N/A", "backlinks.outreach9931@mail.ru", "contact_form",
     "Dear Sir/Madam, We have high DA 70+ sites available for guest posting. Permanent do-follow links. "
     "Payment via crypto. Price list attached.",
     "1 page view: /", True, False, "smb", "none"),

    ("L012", "Meridian Capital Group", None, "Funding Specialist", "offers@meridiancapitalfast.biz", "contact_form",
     "PRE-APPROVED: Your business qualifies for up to $500,000 in working capital. No collateral. "
     "Funds in 24 hours. Reply YES to claim.",
     "1 page view: /", True, False, "smb", "none"),

    # --- enterprise, ready to buy ---------------------------------------
    ("L013", "Siemens", 320000, "Director of Revenue Operations", "k.brandt@siemens.com", "demo_request",
     "We've shortlisted three vendors and need to close by end of Q1. 400 seats. Our security team "
     "needs SOC 2 Type II and a completed VPAT before we can move to paper. Who handles procurement?",
     "18 page views: /pricing, /security, /enterprise x4", False, True, "enterprise", "ready_to_buy"),

    ("L014", "Workday", 18000, "VP Sales Operations", "dana.reyes@workday.com", "contact_form",
     "Budget is approved for this fiscal year. We need to replace our current enrichment vendor before "
     "renewal on March 31. Can someone from your team get on a call this week?",
     "9 page views: /pricing, /migration-guide", False, True, "enterprise", "ready_to_buy"),

    ("L015", "Shopify", 11000, "Senior Manager, GTM Systems", "priya.n@shopify.com", "demo_request",
     "We're running a formal RFP for GTM data infrastructure. Timeline is six weeks. I need your "
     "response to a security questionnaire and pricing for 250 seats.",
     "14 page views: /security, /pricing, /api-docs", False, True, "enterprise", "ready_to_buy"),

    # tricky: real enterprise buyer using a personal email address
    ("L016", "Cisco", 84000, "Head of Sales Strategy", "mreilly1978@gmail.com", "demo_request",
     "Writing from my personal address because our firewall blocks vendor forms. I run sales strategy "
     "for the Americas at Cisco. We have budget allocated and want to pilot with 120 reps in Q2. "
     "Reach me at this address or on LinkedIn.",
     "6 page views: /pricing, /enterprise", False, True, "enterprise", "ready_to_buy"),

    # --- enterprise, evaluating -----------------------------------------
    ("L017", "Atlassian", 12000, "RevOps Lead", "s.vandenberg@atlassian.com", "demo_request",
     "Comparing you against two other platforms for our outbound data layer. Can we see a demo focused "
     "on CRM sync and how you handle duplicate accounts?",
     "8 page views: /integrations, /product", False, True, "enterprise", "evaluating"),

    ("L018", "Adobe", 30000, "Director, Demand Generation", "lchambers@adobe.com", "demo_request",
     "We want to see how your scoring model works before we commit to a trial. Specifically interested "
     "in whether we can bring our own fit criteria.",
     "5 page views: /product/scoring", False, True, "enterprise", "evaluating"),

    ("L019", "ServiceNow", 22000, "Manager, Marketing Operations", "t.aliyev@servicenow.com", "pricing_page",
     "What does pricing look like for around 80 seats? Also need to know if you support SSO via Okta.",
     "4 page views: /pricing x2, /security", False, True, "enterprise", "evaluating"),

    # --- enterprise, low intent -----------------------------------------
    ("L020", "Oracle", 140000, "Sales Operations Analyst", "greg.tolliver@oracle.com", "newsletter",
     "Enjoyed the post on routing rules. Do you publish anything on territory design?",
     "2 page views: /blog/routing-rules", False, True, "enterprise", "researching"),

    ("L021", "SAP", 107000, "CRM Administrator", "n.dasgupta@sap.com", "contact_form",
     "Our sync has been failing since yesterday with a 429 error. We're already a customer on the "
     "Growth plan. Who do I talk to about this?",
     "3 page views: /docs/errors, /support", False, True, "enterprise", "none"),

    # tricky: huge headcount but consumer business, so not ICP
    ("L022", "Chipotle", 110000, "Director of Loyalty Marketing", "b.santos@chipotle.com", "demo_request",
     "We're looking at tools to segment our rewards members and trigger offers. We have about 40 "
     "million app users. Is that something you handle?",
     "3 page views: /product", False, False, "enterprise", "evaluating"),

    ("L023", "Delta Air Lines", 100000, "Manager, Customer Insights", "hollis.j@delta.com", "contact_form",
     "Interested in understanding passenger booking behaviour across channels. Do you have travel data?",
     "2 page views: /data-coverage", False, False, "enterprise", "researching"),

    # --- mid-market, ready to buy ---------------------------------------
    ("L024", "Gusto", 900, "VP Revenue Operations", "amelia.k@gusto.com", "demo_request",
     "Our contract with our current provider ends in 45 days and we don't want to renew. We need 60 "
     "seats live before then. What does onboarding look like?",
     "12 page views: /pricing, /onboarding, /migration-guide", False, True, "mid_market", "ready_to_buy"),

    ("L025", "Vanta", 700, "Head of Growth", "j.okafor@vanta.com", "demo_request",
     "We have sign-off from our CFO for a 6 figure annual spend on GTM infrastructure. Want to get "
     "moving this month. Can you do a technical deep dive with our data team?",
     "15 page views: /pricing, /api-docs x5", False, True, "mid_market", "ready_to_buy"),

    ("L026", "Ramp", 950, "Director of Sales Development", "cfontaine@ramp.com", "contact_form",
     "Ready to start a paid pilot. 25 SDRs. Need it running before our sales kickoff on the 14th.",
     "7 page views: /pricing", False, True, "mid_market", "ready_to_buy"),

    # --- mid-market, evaluating -----------------------------------------
    ("L027", "Linear", 250, "Head of Revenue Operations", "mira.s@linear.app", "demo_request",
     "Evaluating three options for enrichment and routing. Can we get a trial with our own data so we "
     "can measure match rates ourselves?",
     "9 page views: /pricing, /data-coverage x3", False, True, "mid_market", "evaluating"),

    ("L028", "Notion", 900, "Sales Operations Manager", "j.chen@notion.so", "pricing_page",
     "What's the difference between the Growth and Scale tiers? We'd be somewhere around 50 users.",
     "6 page views: /pricing x3", False, True, "mid_market", "evaluating"),

    ("L029", "Rippling", 800, "Marketing Ops Lead", "d.whitmore@rippling.com", "demo_request",
     "We want to automate lead routing between three regional teams. Currently doing it with Zapier "
     "and it breaks constantly. Can you show us how you'd handle that?",
     "8 page views: /product/routing, /integrations", False, True, "mid_market", "evaluating"),

    ("L030", "Airtable", 900, "Growth Marketing Manager", "s.bellamy@airtable.com", "demo_request",
     "Interested in a demo. We're mapping out our 2027 stack and want to understand what's possible.",
     "4 page views: /product", False, True, "mid_market", "evaluating"),

    # --- mid-market, low intent -----------------------------------------
    ("L031", "Figma", 800, "Revenue Operations Analyst", "p.kowalski@figma.com", "newsletter",
     "Signed up for the newsletter. Curious how other companies structure their RevOps team. Any "
     "resources?",
     "2 page views: /blog", False, True, "mid_market", "researching"),

    ("L032", "Amplitude", 700, "Data Engineer", "y.tanaka@amplitude.com", "contact_form",
     "Does your API support cursor based pagination? Reading the docs and it isn't clear.",
     "5 page views: /api-docs x4", False, True, "mid_market", "researching"),

    ("L033", "PagerDuty", 1200, "Customer Success Manager", "e.novak@pagerduty.com", "contact_form",
     "One of our accounts asked whether you integrate with us. Just checking on your side.",
     "1 page view: /integrations", False, True, "enterprise", "none"),

    # --- smb but in ICP (50+ employees, B2B) ----------------------------
    ("L034", "Cal.com", 90, "Head of Sales", "t.mendez@cal.com", "demo_request",
     "We just raised a Series A and are hiring 8 reps. Need to get data and routing sorted before they "
     "start on the 1st. Budget is set aside.",
     "10 page views: /pricing x2, /product", False, True, "smb", "ready_to_buy"),

    ("L035", "Resend", 60, "Growth Lead", "b.aggarwal@resend.com", "pricing_page",
     "Comparing you with two others. Main question is match rate on European companies. Can we test "
     "with a sample of 500 domains?",
     "7 page views: /pricing, /data-coverage x2", False, True, "smb", "evaluating"),

    ("L036", "Dub", 55, "Founder", "steven@dub.co", "contact_form",
     "Early stage but growing fast. Want to understand your pricing before we outgrow our current "
     "setup. Not buying this quarter.",
     "3 page views: /pricing", False, True, "smb", "researching"),

    ("L037", "Liveblocks", 75, "VP Marketing", "n.duarte@liveblocks.io", "demo_request",
     "We need to enrich about 40k records from a webinar and score them. Can you do that as a one off "
     "or is it subscription only?",
     "6 page views: /pricing, /product", False, True, "smb", "evaluating"),

    # --- smb, not in ICP (under 50 employees) ---------------------------
    ("L038", "Kiteline", 12, "Founder", "ravi@kiteline.io", "pricing_page",
     "Two person sales team. Do you have a starter plan? We'd want to buy today if the price works.",
     "5 page views: /pricing x3", False, False, "smb", "ready_to_buy"),

    ("L039", "Overmap", 8, "Co-founder", "hannah@overmap.dev", "demo_request",
     "Tiny team, big ambitions. Want to see a demo and understand if we can self-serve without talking "
     "to sales.",
     "4 page views: /pricing, /docs", False, False, "smb", "evaluating"),

    ("L040", "Foldstack", 30, "Head of Growth", "m.ibrahim@foldstack.com", "pricing_page",
     "Is there a monthly plan? Annual commitment is hard for us right now. We're comparing against "
     "doing it manually.",
     "6 page views: /pricing x4", False, False, "smb", "evaluating"),

    ("L041", "Tuckerbox", 18, "Operations Manager", "claire@tuckerbox.com.au", "contact_form",
     "Just browsing, saw you on a podcast. What does the product actually do?",
     "2 page views: /", False, False, "smb", "researching"),

    # --- not ICP: consumer / wrong role ---------------------------------
    ("L042", "Strava", 600, "Community Manager", "j.paulsen@strava.com", "contact_form",
     "We want to reach out to running clubs and gyms. Would your data cover those?",
     "3 page views: /data-coverage", False, False, "mid_market", "evaluating"),

    ("L043", "Peloton", 3000, "Director of Member Experience", "a.kowalczyk@onepeloton.com", "demo_request",
     "Looking at tools to personalise our member communications. We have 6 million subscribers.",
     "4 page views: /product", False, False, "enterprise", "evaluating"),

    # tricky: big B2B company, but the role has nothing to do with revenue
    ("L044", "Salesforce", 75000, "Facilities Coordinator", "d.brennan@salesforce.com", "contact_form",
     "Trying to find a vendor list for our office in Dublin. Is this the right form?",
     "1 page view: /contact", False, False, "enterprise", "none"),

    ("L045", "Snowflake", 7000, "Principal Software Engineer", "vkrishnan@snowflake.com", "contact_form",
     "Reading your engineering blog on entity resolution. Do you dedupe on domain or on a hash of the "
     "legal entity name?",
     "4 page views: /engineering-blog x3", False, False, "enterprise", "researching"),

    # --- existing customers / support ------------------------------------
    ("L046", "Datadog", 5000, "Revenue Operations Manager", "l.fortier@datadoghq.com", "contact_form",
     "We're already on the Scale plan. Our January invoice looks wrong, it's double what we expected. "
     "Can someone from billing call me?",
     "2 page views: /billing", False, True, "enterprise", "none"),

    ("L047", "Zapier", 800, "Sales Ops Lead", "c.mwangi@zapier.com", "contact_form",
     "Existing customer. Want to add 20 more seats to our current contract. Who do I talk to?",
     "3 page views: /pricing", False, True, "mid_market", "ready_to_buy"),

    ("L048", "Miro", 1800, "Marketing Operations Manager", "f.rossi@miro.com", "contact_form",
     "Our webhook stopped firing last Thursday. Already opened a ticket but no response in 4 days. "
     "Escalating here.",
     "6 page views: /support, /docs/webhooks", False, True, "enterprise", "none"),

    # --- ambiguous / short messages --------------------------------------
    ("L049", "Braze", 1500, "VP Revenue Operations", "k.ahmadi@braze.com", "demo_request",
     "Demo please.",
     "1 page view: /demo", False, True, "enterprise", "evaluating"),

    ("L050", "Intercom", 1000, "Head of Sales Ops", "r.gallagher@intercom.com", "contact_form",
     "Hi.",
     "1 page view: /", False, True, "enterprise", "none"),

    ("L051", "Twilio", 5500, "Senior Director, GTM Strategy", "m.oyelaran@twilio.com", "pricing_page",
     "Pricing for 300 seats, and do you have a BAA? We handle PHI for some customers.",
     "5 page views: /pricing, /security x2", False, True, "enterprise", "ready_to_buy"),

    ("L052", "Databricks", 7000, "Manager, Sales Development", "j.petrov@databricks.com", "demo_request",
     "Saw you at SaaStr. The routing demo was good. Not sure we're ready to switch but want to keep "
     "the conversation going for next year's planning.",
     "3 page views: /product/routing", False, True, "enterprise", "researching"),

    # --- more mid-market and smb spread ----------------------------------
    ("L053", "Loom", 400, "Director of Demand Generation", "s.eriksen@loom.com", "demo_request",
     "We're spending a lot on a data vendor with poor match rates. Want to run a head to head test "
     "against our current provider on 2000 records this month.",
     "9 page views: /data-coverage x4, /pricing", False, True, "mid_market", "evaluating"),

    ("L054", "Webflow", 600, "RevOps Manager", "t.nakamura@webflow.com", "contact_form",
     "How long does implementation usually take? Asking because our CRO wants this done before the "
     "fiscal year starts in six weeks and I need to know if that's realistic.",
     "8 page views: /onboarding, /pricing", False, True, "mid_market", "ready_to_buy"),

    ("L055", "Retool", 500, "Growth Engineer", "a.silva@retool.com", "contact_form",
     "Is there a Terraform provider? We manage everything as code and won't adopt a tool we have to "
     "click through.",
     "6 page views: /api-docs, /integrations", False, True, "mid_market", "researching"),

    ("L056", "Census", 200, "Head of Revenue", "p.lindqvist@getcensus.com", "demo_request",
     "We want to buy. Need pricing for 35 seats and a start date in the next three weeks.",
     "7 page views: /pricing x3", False, True, "mid_market", "ready_to_buy"),

    ("L057", "Hex", 300, "Marketing Operations", "b.oconnell@hex.tech", "pricing_page",
     "Trying to work out whether we'd be on the Growth or Scale plan. Roughly 30 users, mostly "
     "read-only.",
     "5 page views: /pricing x2", False, True, "mid_market", "evaluating"),

    ("L058", "Modal", 120, "Head of Sales", "e.vasquez@modal.com", "demo_request",
     "We've outgrown spreadsheets. Six reps, growing to fifteen. Want to see the product and "
     "understand pricing.",
     "6 page views: /pricing, /product", False, True, "smb", "evaluating"),

    ("L059", "Baseten", 85, "VP Marketing", "n.haddad@baseten.co", "contact_form",
     "What's your coverage like for AI infrastructure companies specifically? Our TAM is narrow and "
     "generic databases have been useless.",
     "5 page views: /data-coverage x3", False, True, "smb", "evaluating"),

    ("L060", "Warp", 70, "Head of Growth", "i.demir@warp.dev", "newsletter",
     "Subscribed. We might look at this in the second half of the year, not before.",
     "2 page views: /blog, /pricing", False, True, "smb", "researching"),
]


def main() -> None:
    out = pathlib.Path(__file__).resolve().parents[1] / "data" / "leads.jsonl"
    seen = set()
    with out.open("w") as fh:
        for (lid, company, headcount, title, email, source, message, activity,
             disq, icp, seg, intent) in LEADS:
            assert lid not in seen, f"duplicate id {lid}"
            seen.add(lid)
            fh.write(json.dumps({
                "id": lid,
                "lead": {
                    "company": company,
                    "headcount": headcount,
                    "title": title,
                    "email": email,
                    "source": source,
                    "message": message,
                    "recent_activity": activity,
                },
                "labels": {
                    "disqualify": disq,
                    "icp_fit": icp,
                    "segment": seg,
                    "intent": intent,
                },
            }) + "\n")
    print(f"wrote {len(LEADS)} leads to {out}")


if __name__ == "__main__":
    main()
