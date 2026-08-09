from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


ALLOWED_FLAIRS = (
    "UK Fibre News",
    "Technology Explainer",
    "Market Development",
)


@dataclass(frozen=True)
class Candidate:
    title: str
    url: str
    summary: str
    published_at: datetime
    feed_url: str


@dataclass(frozen=True)
class GeneratedDraft:
    title: str
    flair: str
    news_paragraph: str


@dataclass(frozen=True)
class ValidatedPost:
    title: str
    flair: str
    body: str
    source_url: str

