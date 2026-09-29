# How the answer key was written

50 candidate pairs, each labelled same, related or different against the
strings in `src/spec.py`. A record has a name, domain, country, industry,
headcount and the place it came from, which is roughly what a CRM account
carries. Labels were set in `src/pairs.py` before any model saw a pair.

## The three labels

| label | means | what `spec.action()` does |
|---|---|---|
| `same` | one company with two records | merge if the model is at least 0.9 sure, otherwise send to a person |
| `related` | two companies in one corporate family | link them, keep both |
| `different` | unrelated | leave both alone |

## Same or related

This is the line that matters, because a merge is hard to undo.

A renamed company is the same company: Facebook and Meta Platforms (P09),
Square and Block (P15). A company another one bought is related to it, even
when everyone treats them as one: Instagram and Meta (P19), YouTube and
Google (P25). Google LLC and Alphabet (P28) are related too. Alphabet is the
parent, and both records show 180,000 people.

A second domain doesn't make a second company. Orbital Freight on
orbitalfreight.com and on orbital.io (P07) has the same headcount in the same
country, so it's one company. Orbital Freight UK Ltd (P30) is a 60-person
British entity of a 420-person US one, so it's related. A .ca domain goes
either way. Framewell (P18) has both records in Canada at 75 people, so it's
same. Acme Logistics Canada (P31) is a 90-person arm of an 850-person US
company, so it's related.

Sharing a domain doesn't make one company either. Veldt Analytics B.V. and
Veldt Analytics Inc. (P32) both use veldt.io, but one is Dutch with 180
people and the other American with 20. That's related.

## Related or different

Mostly a question of knowing who owns whom. Delta Air Lines and Delta Faucet
(P33) share a word and nothing else. So do Apple Inc. and Apple Leisure
Group, Oracle and Oracle Lighting, and Stripe and Stripes.

## Which pairs need world knowledge

14 pairs can't be settled from the records. Four are renames that changed
both the name and the domain (Facebook, Twitter, Weight Watchers, Square).
Ten are a parent and a subsidiary with nothing in the records to connect
them. The other 36 can be judged from domain, legal suffix, country,
industry and headcount.

Dunkin', Salesforce and Google also renamed, but they kept their domains, so
the records already say they're one company. They count as records-enough.

Every real relationship here is public and settled. The newest acquisition
is Slack, which closed in 2021. The newest rename is Twitter to X Corp in
2023.

## Distribution

50 pairs: 18 same, 14 related, 18 different.
