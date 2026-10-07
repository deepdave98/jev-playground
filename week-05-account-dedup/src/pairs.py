"""Account-pair fixtures and labels, using real and fictional company names."""

import json
import pathlib
import sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from spec import QUESTIONS  # noqa: E402

# Each record is (name, domain, country, industry, employees, source).
PAIRS = [
    # same company: formatting, typos, a second domain
    ("P01", ("Acme Logistics", "acmelogistics.com", "US", "Logistics", 850, "rep created"),
            ("ACME LOGISTICS INC.", "acmelogistics.com", "US", "Transportation", 850, "enrichment import"), "same"),
    ("P02", ("Northwind Traders", "northwind.io", "US", "Wholesale", 320, "web form"),
            ("Northwind", "northwind.io", "US", "Wholesale", 310, "trade show list"), "same"),
    ("P03", ("Halvorsen Group", "halvorsen.com", "NO", "Engineering", 2400, "CRM migration"),
            ("Halvorsen Grp", "halvorsen.com", "NO", "Engineering", 2400, "rep created"), "same"),
    ("P04", ("Kettlebridge", "kettlebridge.com", "US", "Software", 140, "web form"),
            ("Kettle Bridge", "kettlebridge.com", "US", "SaaS", 150, "rep created"), "same"),
    ("P05", ("Tidepool", "tidepool.io", "US", "SaaS", 210, "enrichment import"),
            ("Tidepol", "tidepool.io", "US", "SaaS", 210, "rep created"), "same"),
    ("P06", ("Stillwater Co", "stillwater.co", "US", "Consumer goods", 95, "web form"),
            ("Stillwater Company", "stillwater.co", "US", "CPG", 95, "enrichment import"), "same"),
    ("P07", ("Orbital Freight", "orbitalfreight.com", "US", "Logistics", 420, "CRM migration"),
            ("Orbital Freight", "orbital.io", "US", "Logistics", 420, "web form"), "same"),
    ("P08", ("Pellucid", "pellucid.io", "GB", "Analytics", 60, "trade show list"),
            ("Pellucid Ltd", "pellucid.io", "GB", "Analytics", 60, "enrichment import"), "same"),

    # same company: a rename or a change of legal form
    ("P09", ("Facebook, Inc.", "facebook.com", "US", "Internet", 60000, "CRM migration"),
            ("Meta Platforms", "meta.com", "US", "Internet", 70000, "enrichment import"), "same"),
    ("P10", ("Twitter", "twitter.com", "US", "Internet", 7500, "CRM migration"),
            ("X Corp", "x.com", "US", "Internet", 2500, "enrichment import"), "same"),
    ("P11", ("Dunkin' Donuts", "dunkindonuts.com", "US", "Restaurants", 1100, "trade show list"),
            ("Dunkin'", "dunkindonuts.com", "US", "Food and beverage", 1100, "enrichment import"), "same"),
    ("P12", ("Weight Watchers International", "weightwatchers.com", "US", "Health", 3000, "CRM migration"),
            ("WW International", "ww.com", "US", "Wellness", 3000, "enrichment import"), "same"),
    ("P13", ("Salesforce.com", "salesforce.com", "US", "Software", 70000, "CRM migration"),
            ("Salesforce, Inc.", "salesforce.com", "US", "Software", 72000, "enrichment import"), "same"),
    ("P14", ("Google Inc.", "google.com", "US", "Internet", 150000, "CRM migration"),
            ("Google LLC", "google.com", "US", "Internet", 180000, "enrichment import"), "same"),
    ("P15", ("Square, Inc.", "squareup.com", "US", "Fintech", 8000, "CRM migration"),
            ("Block, Inc.", "block.xyz", "US", "Fintech", 12000, "enrichment import"), "same"),
    ("P16", ("Veldt Analytics", "veldt.io", "NL", "Analytics", 180, "web form"),
            ("Veldt Analytics B.V.", "veldt.io", "NL", "Analytics", 180, "enrichment import"), "same"),
    ("P17", ("Graniteworks", "graniteworks.com", "US", "Construction", 1300, "rep created"),
            ("Graniteworks", "graniteworks.com", "US", "Building materials", 1250, "trade show list"), "same"),
    ("P18", ("Framewell Inc", "framewell.com", "CA", "Software", 75, "web form"),
            ("Framewell", "framewell.ca", "CA", "Software", 75, "rep created"), "same"),

    # related: a parent and a subsidiary or a brand it bought
    ("P19", ("Instagram", "instagram.com", "US", "Internet", 1500, "web form"),
            ("Meta Platforms", "meta.com", "US", "Internet", 70000, "enrichment import"), "related"),
    ("P20", ("WhatsApp", "whatsapp.com", "US", "Internet", 1000, "trade show list"),
            ("Meta Platforms", "meta.com", "US", "Internet", 70000, "enrichment import"), "related"),
    ("P21", ("Slack Technologies", "slack.com", "US", "Software", 2500, "web form"),
            ("Salesforce, Inc.", "salesforce.com", "US", "Software", 72000, "enrichment import"), "related"),
    ("P22", ("Tableau Software", "tableau.com", "US", "Software", 4000, "rep created"),
            ("Salesforce", "salesforce.com", "US", "Software", 72000, "CRM migration"), "related"),
    ("P23", ("LinkedIn", "linkedin.com", "US", "Internet", 20000, "web form"),
            ("Microsoft", "microsoft.com", "US", "Software", 220000, "enrichment import"), "related"),
    ("P24", ("GitHub", "github.com", "US", "Software", 3000, "trade show list"),
            ("Microsoft Corporation", "microsoft.com", "US", "Software", 220000, "CRM migration"), "related"),
    ("P25", ("YouTube", "youtube.com", "US", "Internet", 5000, "web form"),
            ("Google LLC", "google.com", "US", "Internet", 180000, "enrichment import"), "related"),
    ("P26", ("Zappos", "zappos.com", "US", "Retail", 1500, "rep created"),
            ("Amazon.com, Inc.", "amazon.com", "US", "Retail", 1500000, "enrichment import"), "related"),
    ("P27", ("Whole Foods Market", "wholefoodsmarket.com", "US", "Grocery", 100000, "trade show list"),
            ("Amazon", "amazon.com", "US", "Retail", 1500000, "CRM migration"), "related"),
    ("P28", ("Google LLC", "google.com", "US", "Internet", 180000, "enrichment import"),
            ("Alphabet Inc.", "abc.xyz", "US", "Internet", 180000, "CRM migration"), "related"),

    # related: a regional arm with its own legal entity
    ("P29", ("Halvorsen Group", "halvorsen.com", "NO", "Engineering", 2400, "CRM migration"),
            ("Halvorsen Nordic AB", "halvorsen.se", "SE", "Engineering", 300, "enrichment import"), "related"),
    ("P30", ("Orbital Freight", "orbitalfreight.com", "US", "Logistics", 420, "CRM migration"),
            ("Orbital Freight UK Ltd", "orbitalfreight.co.uk", "GB", "Logistics", 60, "web form"), "related"),
    ("P31", ("Acme Logistics", "acmelogistics.com", "US", "Logistics", 850, "rep created"),
            ("Acme Logistics Canada", "acmelogistics.ca", "CA", "Logistics", 90, "trade show list"), "related"),
    ("P32", ("Veldt Analytics B.V.", "veldt.io", "NL", "Analytics", 180, "enrichment import"),
            ("Veldt Analytics Inc.", "veldt.io", "US", "Analytics", 20, "web form"), "related"),

    # different: a well-known name and an unrelated company that shares it
    ("P33", ("Delta Air Lines", "delta.com", "US", "Airlines", 100000, "CRM migration"),
            ("Delta Faucet Company", "deltafaucet.com", "US", "Manufacturing", 5000, "trade show list"), "different"),
    ("P34", ("Apple Inc.", "apple.com", "US", "Technology", 160000, "enrichment import"),
            ("Apple Leisure Group", "appleleisuregroup.com", "US", "Travel", 3000, "web form"), "different"),
    ("P35", ("Zoom Video Communications", "zoom.us", "US", "Software", 7400, "enrichment import"),
            ("Zoom Telephonics", "zoomtel.com", "US", "Hardware", 50, "rep created"), "different"),
    ("P36", ("Mercury", "mercury.com", "US", "Fintech", 900, "web form"),
            ("Mercury Insurance", "mercuryinsurance.com", "US", "Insurance", 4000, "trade show list"), "different"),
    ("P37", ("Notion Labs", "notion.so", "US", "Software", 800, "web form"),
            ("Notion Capital", "notion.vc", "GB", "Venture capital", 40, "enrichment import"), "different"),
    ("P38", ("Stripe", "stripe.com", "US", "Fintech", 8000, "enrichment import"),
            ("Stripes", "stripes.com", "US", "Private equity", 60, "rep created"), "different"),
    ("P39", ("Oracle", "oracle.com", "US", "Software", 160000, "CRM migration"),
            ("Oracle Lighting", "oraclelights.com", "US", "Automotive", 150, "trade show list"), "different"),
    ("P40", ("Brightline", "brightline.io", "US", "SaaS", 90, "web form"),
            ("Brightline", "gobrightline.com", "US", "Rail", 1500, "enrichment import"), "different"),

    # different: smaller lookalikes
    ("P41", ("Summit Labs", "summitlabs.io", "US", "SaaS", 120, "web form"),
            ("Summit Lab Supplies", "summitlabsupply.com", "US", "Lab equipment", 45, "trade show list"), "different"),
    ("P42", ("Nova", "nova.com.br", "BR", "Fintech", 600, "enrichment import"),
            ("Nova", "nova.se", "SE", "Energy", 300, "enrichment import"), "different"),
    ("P43", ("Keystone", "keystonecx.com", "US", "Software", 210, "rep created"),
            ("Keystone Foods", "keystonefoods.com", "US", "Food processing", 20000, "trade show list"), "different"),
    ("P44", ("Redwood", "redwood.io", "US", "Software", 230, "web form"),
            ("Redwood Credit Union", "redwoodcu.org", "US", "Banking", 600, "enrichment import"), "different"),
    ("P45", ("Pinecrest", "pinecrest.io", "US", "SaaS", 175, "web form"),
            ("Pinecrest Academy", "pinecrestacademy.org", "US", "Education", 400, "trade show list"), "different"),
    ("P46", ("Cascade", "cascade.dev", "US", "Software", 55, "rep created"),
            ("Cascade Natural Gas", "cngc.com", "US", "Utilities", 400, "enrichment import"), "different"),
    ("P47", ("Halcyon Bio", "halcyonbio.com", "US", "Biotech", 150, "web form"),
            ("Halcyon", "halcyon.io", "US", "Software", 40, "rep created"), "different"),
    ("P48", ("Meridian Capital", "meridiancap.com", "US", "Finance", 300, "trade show list"),
            ("Meridian Health", "meridianhealth.org", "US", "Healthcare", 12000, "enrichment import"), "different"),
    ("P49", ("Gap Inc.", "gap.com", "US", "Retail", 80000, "enrichment import"),
            ("Gap Analytics", "gapanalytics.io", "US", "Consulting", 25, "web form"), "different"),
    ("P50", ("Tidepool", "tidepool.io", "US", "SaaS", 210, "enrichment import"),
            ("Tidepool", "tidepool.org", "US", "Nonprofit", 60, "web form"), "different"),
]

FIELDS = ("name", "domain", "country", "industry", "employees", "source")

# Four renames changing both name and domain, plus ten parent/subsidiary pairs.
WORLD = {"P09", "P10", "P12", "P15", *(f"P{n}" for n in range(19, 29))}


def main():
    out = pathlib.Path(__file__).resolve().parents[1] / "data" / "pairs.jsonl"
    kinds = set(QUESTIONS["relationship"]["criteria"])
    seen = set()
    with out.open("w") as fh:
        for pid, a, b, rel in PAIRS:
            assert pid not in seen and rel in kinds, pid
            seen.add(pid)
            fh.write(json.dumps({
                "id": pid,
                "pair": {"record_a": dict(zip(FIELDS, a)), "record_b": dict(zip(FIELDS, b))},
                "label": {"relationship": rel, "same_company": rel == "same",
                          "needs_world_knowledge": pid in WORLD},
            }) + "\n")
    print(f"wrote {len(PAIRS)} pairs -> {out}")
    print("relationship:", dict(Counter(p[3] for p in PAIRS)))
    print("need world knowledge:", len(WORLD), dict(Counter(p[3] for p in PAIRS if p[0] in WORLD)))


if __name__ == "__main__":
    main()
