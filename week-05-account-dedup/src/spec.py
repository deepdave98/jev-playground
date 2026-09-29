"""Questions and the merge rule for week 05: duplicate accounts in a CRM.

Each pair was flagged upstream as a possible duplicate, by a shared word in
the name, a shared domain, or a rep asking for a merge. The models only see
pairs that already look alike, which is where the hard calls are. Both
models get these exact strings.
"""

QUESTIONS = {
    "relationship": {
        "type": "choice",
        "instructions": "How are the companies behind these two account records related?",
        "criteria": {
            "same": (
                "The same company. It might show up under an old name, a rebrand, a "
                "typo or a second domain. One record should be merged into the other."
            ),
            "related": (
                "Two separate companies in the same corporate family: a parent and a "
                "subsidiary, a company and a brand it bought, or a regional arm with its "
                "own legal entity. Link them and keep both."
            ),
            "different": "Unrelated companies that happen to look alike. Leave both alone.",
        },
    },
    "same_company": {
        "type": "noul",
        "instructions": (
            "Are these two records the same company, so that merging them would be "
            "correct? A parent and its subsidiary are two companies."
        ),
        "criteria": {
            "true": "Same company. Merging is right.",
            "false": "Two companies, related or not. Merging would lose one of them.",
        },
    },
}

# Merges are hard to undo, so only confident ones happen on their own. The
# rest go to a person.
AUTO_MERGE = 0.9


def action(relationship, p_same):
    if relationship == "same":
        return "merge" if p_same >= AUTO_MERGE else "review"
    if relationship == "related":
        return "link"
    return "keep"
