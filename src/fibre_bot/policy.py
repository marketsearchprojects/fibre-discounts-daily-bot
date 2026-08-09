from __future__ import annotations

import re

from .models import ALLOWED_FLAIRS, Candidate, GeneratedDraft, ValidatedPost


DEAL_PARAGRAPH = (
    "Ad — If YouFibre is available at your address and suits your needs, enter "
    "referral code `KFJY3B` during checkout to claim any currently eligible "
    "switching reward. I may also receive a referral reward. Check "
    "[YouFibre's current terms](https://www.youfibre.com/legal/) before ordering "
    "or cancelling an existing service."
)

BLOCKED_CLAIMS = (
    r"\balways superior\b",
    r"\bguaranteed\b",
    r"\bthe best(?: broadband| provider| isp)?\b",
    r"£\s?\d+\b",
    r"\bup to £\s?\d+\b",
)


def _one_paragraph(value: str) -> bool:
    return bool(value.strip()) and not re.search(r"\n\s*\n", value.strip())


def validate_and_compose(draft: GeneratedDraft, source: Candidate) -> ValidatedPost:
    if draft.flair not in ALLOWED_FLAIRS:
        raise ValueError(f"Unapproved flair: {draft.flair}")
    if not 20 <= len(draft.title) <= 140:
        raise ValueError("Title must contain 20-140 characters")
    if not _one_paragraph(draft.news_paragraph):
        raise ValueError("News summary must be exactly one paragraph")

    words = re.findall(r"\b[\w’'-]+\b", draft.news_paragraph)
    if not 35 <= len(words) <= 110:
        raise ValueError("News summary must contain 35-110 words")

    inspected = f"{draft.title}\n{draft.news_paragraph}".lower()
    for pattern in BLOCKED_CLAIMS:
        if re.search(pattern, inspected, flags=re.IGNORECASE):
            raise ValueError(f"Blocked advertising claim matched: {pattern}")

    news = (
        f"{draft.news_paragraph} Source: "
        f"[{source.title}]({source.url})."
    )
    body = f"{news}\n\n{DEAL_PARAGRAPH}"
    if len(re.split(r"\n\s*\n", body.strip())) != 2:
        raise AssertionError("Post body must contain exactly two paragraphs")
    if "I may also receive a referral reward" not in body:
        raise AssertionError("Referral disclosure is mandatory")
    return ValidatedPost(
        title=f"Ad | {draft.title}",
        flair=draft.flair,
        body=body,
        source_url=source.url,
    )
