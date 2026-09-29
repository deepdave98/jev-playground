# Week 05: duplicate accounts in a CRM

Duplicate accounts pile up in any CRM. List imports, reps and enrichment
tools all create them, and enrichment tends to use the legal name. Most are
easy to spot. The ones that cost you look like duplicates and aren't:
Instagram and Meta Platforms are two companies in one family, and merging
them loses one.

Each candidate pair gets two questions: are these the same company, related,
or different, and how likely is it that merging is right. Code turns the
answers into an action. Same at 0.9 or more merges, same below that goes to
a person, related gets linked as parent and child, and different is left
alone.

A wrong merge is the mistake to avoid. It folds two companies' contacts,
deals and history into one record, and it's hard to undo.

50 candidate pairs, labelled by hand against [rubric.md](rubric.md). 14 of
them can't be settled from the records. You have to know that Square became
Block, or that Microsoft owns GitHub.

## Results

| | Jev | Haiku 4.5 | Sonnet 5 | Sonnet 5, thinking |
|---|---|---|---|---|
| wrong merges | **0** | 1 | 2 | **0** |
| duplicates missed | 0 of 18 | 0 of 18 | 0 of 18 | 0 of 18 |
| sent to a person | 12 | 0 | 1 | 0 |
| relationship right | 48 of 50 | 46 of 50 | 46 of 50 | **50 of 50** |
| needs world knowledge | 13 of 14 | 10 of 14 | 10 of 14 | **14 of 14** |
| records are enough | 35 of 36 | 36 of 36 | 36 of 36 | 36 of 36 |
| | | | | |
| per pair, p50 | **364 ms** | 2,803 ms | 2,124 ms | 10,161 ms |
| per 1,000 pairs | **$0.025** | $0.814 | $1.299 | $11.894 |

"Sonnet 5, thinking" is the same model at max effort with thinking on. Every
other Claude run in this repo has thinking off. Why it's here is below.

## Jev knew who owns whom

Jev got 13 of the 14 pairs that need world knowledge, including all four
renames and Google against Alphabet. It called Tableau unrelated to
Salesforce, and on the records-only side it linked Apple Inc. to Apple
Leisure Group. Neither mistake merges anything.

## Haiku and Sonnet knew too

Both got 10 of the 14, and they knew the answers. `src/why.py` asked each of
them again about every miss, with the same prompt and one line of reasoning
after the answer. Two of the eight came back right the second time, Sonnet
on Instagram and Haiku on Tableau. Of the rest, Haiku wrote "While Microsoft
acquired LinkedIn in 2016, they maintain distinct legal entities" and
answered different. Sonnet called LinkedIn "a wholly-owned subsidiary" of
Microsoft and answered different too. Haiku did the same with Slack, and
Sonnet with GitHub. Both models read "different" as "not the same company",
with "related" sitting in the prompt and parent and subsidiary spelled out
under it.

Google and Alphabet went the other way. Both merged them, and both argued
that for a CRM they're one operating company, citing the 180,000 headcount
on both records. The prompt says a parent and its subsidiary are two
companies.

## Thinking fixed it, at about 470 times the price

Every week so far has run Claude with thinking off, because nobody waits 22
seconds for a lead to be routed. Dedup usually runs as a batch job, so I ran
Sonnet again with thinking on. At medium and high effort it still answered
straight away. Only max effort made it think.

With thinking, Sonnet got all 50 right. It took 10 seconds a pair at the
median and cost $11.89 per 1,000 pairs, about 470 times what Jev cost.

## Whose confidence can gate a merge

The merge bar is 0.9, and I set it before the run. Jev put every real
duplicate between 0.68 and 0.95 and nothing else above 0.29, so any bar
between those two would have merged all 18 with no mistakes. At 0.9 it
merged 6 on its own and sent 12 to a person.

Haiku gave 0.95 to every duplicate and 0.95 to Google and Alphabet. Sonnet
without thinking gave Instagram and Meta 0.95, higher than two of its real
duplicates. No bar separates those. Sonnet with thinking kept every real
duplicate at 0.90 or more and everything else at 0.15 or less.

## What I'd ship

Jev on every pair, and Sonnet with thinking where the person would be.
`src/score.py` works this out from the two runs, without asking anything
again:

| | wrong merges | duplicates merged | sent to a person | per 1,000 pairs |
|---|---|---|---|---|
| Jev alone | 0 | 6 of 18 | 12 | $0.025 |
| Jev, with Sonnet thinking on the 12 it sends to a person | 0 | 18 of 18 | 0 | **$2.810** |
| Sonnet thinking on every pair | 0 | 18 of 18 | 0 | $11.894 |

```
candidate pairs from code: a shared word in the name, a shared domain, a rep's merge request
  -> Jev: relationship and same_company
  -> same at 0.9 or more: merge
  -> same below 0.9: Sonnet with thinking, and a person when the two disagree
  -> related: link as parent and child
  -> different: leave both
```

Start at 0.9 and bring the bar down once the second look has agreed with
Jev for a while. Fifty pairs is too few to pick the number.

Don't gate merges on a Claude probability from a run with thinking off.
Both of those runs gave a wrong merge the same 0.95 they gave real
duplicates.

## Running it

```bash
cd week-05-account-dedup
python3 src/pairs.py                   # builds data/pairs.jsonl from the labelled source
python3 src/bench.py                   # all four setups, about 30 minutes
python3 src/score.py
python3 src/why.py claude-sonnet-5     # re-asks a Claude run about its misses
```

Needs `TYPESAFE_API_KEY` and a logged-in `claude` CLI.

50 pairs is small, and one pair is two points. Where the misses fall is the
part I'd trust. Every one of them is about a corporate family: a real one
read wrong, or the one Jev imagined between Apple and Apple Leisure Group.
