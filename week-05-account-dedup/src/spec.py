"""Shared account-pair prompts and merge rule."""

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

# Lower scores go to review.
AUTO_MERGE = 0.9


def action(relationship, p_same):
    if relationship == "same":
        return "merge" if p_same >= AUTO_MERGE else "review"
    if relationship == "related":
        return "link"
    return "keep"
