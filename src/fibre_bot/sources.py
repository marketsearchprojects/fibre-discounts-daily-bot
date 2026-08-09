from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import requests

from .models import Candidate


ALLOWED_FEED_HOSTS = frozenset({"www.ispreview.co.uk"})
ALLOWED_ARTICLE_HOSTS = frozenset({"ispreview.co.uk", "www.ispreview.co.uk"})
KEYWORDS = (
    "broadband",
    "fibre",
    "fiber",
    "fttp",
    "xgs-pon",
    "openreach",
    "altnet",
    "isp",
    "wi-fi 7",
    "wifi 7",
)
FIXED_NETWORK_TERMS = (
    "fibre",
    "fiber",
    "fttp",
    "xgs-pon",
    "openreach",
    "altnet",
    "full-fibre",
    "fixed broadband",
    "ethernet",
)
MOBILE_ONLY_TERMS = ("mobile broadband", "2g", "3g", "4g", "5g", "mobile network")


def _clean_markup(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return re.sub(r"\s+", " ", no_tags).strip()


def _first_text(element: ET.Element, names: tuple[str, ...]) -> str:
    for child in element.iter():
        local = child.tag.rsplit("}", 1)[-1]
        if local in names and child.text:
            return child.text.strip()
    return ""


def _entry_link(entry: ET.Element) -> str:
    for child in entry.iter():
        if child.tag.rsplit("}", 1)[-1] != "link":
            continue
        href = child.attrib.get("href", "").strip()
        if href:
            return href
        if child.text:
            return child.text.strip()
    return ""


def _parse_date(raw: str, now: datetime) -> datetime:
    if not raw:
        return now
    try:
        result = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            result = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return now
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


def _validate_feed_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_FEED_HOSTS:
        raise ValueError(f"Feed is not on the HTTPS allowlist: {url}")


def _article_url_is_allowed(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_ARTICLE_HOSTS


def fetch_candidates(
    feed_urls: tuple[str, ...],
    *,
    now: datetime | None = None,
    max_age_days: int = 7,
) -> list[Candidate]:
    current = (now or datetime.now(UTC)).astimezone(UTC)
    candidates: list[Candidate] = []
    headers = {"User-Agent": "FibreDiscountsFeedReader/0.1 (+u/FrierenInsights)"}

    for feed_url in feed_urls:
        _validate_feed_url(feed_url)
        response = requests.get(feed_url, headers=headers, timeout=20)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        entries = [
            item
            for item in root.iter()
            if item.tag.rsplit("}", 1)[-1] in {"item", "entry"}
        ]
        for entry in entries[:25]:
            title = _clean_markup(_first_text(entry, ("title",)))
            summary = _clean_markup(
                _first_text(entry, ("description", "summary", "content"))
            )
            url = _entry_link(entry)
            published = _parse_date(
                _first_text(entry, ("pubDate", "published", "updated")), current
            )
            haystack = f"{title} {summary}".lower()
            if (
                not title
                or not _article_url_is_allowed(url)
                or not any(word in haystack for word in KEYWORDS)
            ):
                continue
            if any(word in haystack for word in MOBILE_ONLY_TERMS) and not any(
                word in haystack for word in FIXED_NETWORK_TERMS
            ):
                continue
            if published < current - timedelta(days=max_age_days):
                continue
            candidates.append(
                Candidate(
                    title=title[:300],
                    url=url,
                    summary=summary[:3000],
                    published_at=published,
                    feed_url=feed_url,
                )
            )

    unique: dict[str, Candidate] = {}
    for candidate in sorted(candidates, key=lambda item: item.published_at, reverse=True):
        unique.setdefault(candidate.url, candidate)
    return list(unique.values())
