# Account-pair labels

50 fixture pairs with name, domain, country, industry, headcount and source.
[`spec.py`](src/spec.py) defines the prompt and action rule;
[`pairs.py`](src/pairs.py) contains the records and answer key.

| Relationship | Definition | Action |
|---|---|---|
| `same` | two records for one company | merge at score >= 0.9; otherwise review |
| `related` | separate companies in one corporate family | link and retain both |
| `different` | unrelated companies | retain both |

The fixture treats renames as `same`: Facebook / Meta Platforms (P09),
Square / Block (P15). Acquired companies and subsidiaries are `related`:
Instagram / Meta (P19), YouTube / Google (P25), Google LLC / Alphabet (P28).

Domains and headcounts provide context, but do not settle identity alone:

- P07 uses two domains for the same fictional Orbital Freight record.
- P18 has matching Canadian Framewell records under .com and .ca domains.
- P30 and P31 are separate regional entities with different headcounts.
- P32's Dutch and American legal entities share a domain and remain separate.

Name overlap alone does not establish a relationship. Examples include
Delta Air Lines / Delta Faucet and Apple Inc. / Apple Leisure Group.

The `needs_world_knowledge` group contains 14 pairs: four renames changing
both name and domain, and ten parent/subsidiary pairs. The remaining 36 use
record-level clues. The grouping is part of this fixture's answer key.

The real company relationships are dated examples, not a current ownership
registry. Labels follow this benchmark's account-retention policy.

Distribution: 18 `same`, 14 `related`, 18 `different`.
