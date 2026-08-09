from __future__ import annotations

import re
from urllib.parse import unquote

import requests

from .config import Settings
from .models import ValidatedPost


class RedditClient:
    def __init__(self, settings: Settings) -> None:
        settings.require_reddit_credentials()
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent})
        self._authenticate()
        self._verify_identity()

    def _authenticate(self) -> None:
        response = self.session.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(self.settings.reddit_client_id, self.settings.reddit_client_secret),
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.settings.reddit_refresh_token,
            },
            timeout=30,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise RuntimeError("Reddit OAuth response contained no access token")
        self.session.headers.update({"Authorization": f"bearer {token}"})

    def _verify_identity(self) -> None:
        response = self.session.get(
            "https://oauth.reddit.com/api/v1/me", timeout=30
        )
        response.raise_for_status()
        actual = response.json().get("name")
        if actual != self.settings.reddit_username:
            raise RuntimeError(
                f"Authenticated Reddit identity is {actual!r}; expected "
                f"{self.settings.reddit_username!r}"
            )

    def recent_source_urls(self) -> set[str]:
        response = self.session.get(
            f"https://oauth.reddit.com/r/{self.settings.subreddit}/new",
            params={"limit": 25, "raw_json": 1},
            timeout=30,
        )
        response.raise_for_status()
        urls: set[str] = set()
        for child in response.json().get("data", {}).get("children", []):
            data = child.get("data", {})
            if data.get("author") != self.settings.reddit_username:
                continue
            text = data.get("selftext", "")
            for url in re.findall(r"https://[^\s)]+", text):
                urls.add(unquote(url.rstrip(".,")))
        return urls

    def _flair_id(self, flair_text: str) -> str:
        response = self.session.get(
            f"https://oauth.reddit.com/r/{self.settings.subreddit}/api/link_flair_v2",
            timeout=30,
        )
        response.raise_for_status()
        matches = [item for item in response.json() if item.get("text") == flair_text]
        if len(matches) != 1 or not matches[0].get("id"):
            raise RuntimeError(f"Could not resolve one unique flair: {flair_text}")
        return str(matches[0]["id"])

    def submit(self, post: ValidatedPost) -> str:
        response = self.session.post(
            "https://oauth.reddit.com/api/submit",
            data={
                "api_type": "json",
                "kind": "self",
                "sr": self.settings.subreddit,
                "title": post.title,
                "text": post.body,
                "flair_id": self._flair_id(post.flair),
                "resubmit": "false",
                "sendreplies": "true",
                "raw_json": 1,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        errors = payload.get("json", {}).get("errors", [])
        if errors:
            raise RuntimeError(f"Reddit rejected the submission: {errors}")
        post_id = payload.get("json", {}).get("data", {}).get("id")
        if not post_id:
            raise RuntimeError("Reddit submission response contained no post ID")
        return str(post_id)

