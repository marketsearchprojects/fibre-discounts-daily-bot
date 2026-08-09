from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


FIXED_USERNAME = "FrierenInsights"
FIXED_SUBREDDIT = "FibreDiscounts"

DEFAULT_FEEDS = (
    "https://www.ispreview.co.uk/index.php/feed",
)


def _truthy(value: str | None) -> bool:
    return value == "true"


@dataclass(frozen=True)
class Settings:
    approval_granted: bool
    reddit_client_id: str
    reddit_client_secret: str
    reddit_refresh_token: str
    reddit_username: str
    subreddit: str
    openai_api_key: str
    openai_model: str
    feeds: tuple[str, ...]
    state_path: Path
    user_agent: str

    @classmethod
    def from_env(cls) -> "Settings":
        username = os.getenv("REDDIT_USERNAME", FIXED_USERNAME)
        subreddit = os.getenv("REDDIT_SUBREDDIT", FIXED_SUBREDDIT)
        if username != FIXED_USERNAME or subreddit != FIXED_SUBREDDIT:
            raise ValueError(
                "This application is approved only for u/FrierenInsights in "
                "r/FibreDiscounts; scope overrides are rejected."
            )

        raw_feeds = os.getenv("FIBRE_NEWS_FEEDS", "")
        feeds = tuple(item.strip() for item in raw_feeds.split(",") if item.strip())
        if not feeds:
            feeds = DEFAULT_FEEDS

        return cls(
            approval_granted=_truthy(os.getenv("REDDIT_APPROVAL_GRANTED")),
            reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
            reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
            reddit_refresh_token=os.getenv("REDDIT_REFRESH_TOKEN", ""),
            reddit_username=username,
            subreddit=subreddit,
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5.6-terra"),
            feeds=feeds,
            state_path=Path(os.getenv("BOT_STATE_PATH", "state/posted.json")),
            user_agent=(
                "linux:fibre-discounts-daily-bot:v0.1.0 "
                "(by /u/FrierenInsights)"
            ),
        )

    def require_generation_credentials(self) -> None:
        if not self.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required to generate a draft")

    def require_reddit_credentials(self) -> None:
        if not self.approval_granted:
            raise RuntimeError(
                "Reddit publishing is disabled until REDDIT_APPROVAL_GRANTED=true"
            )
        missing = [
            name
            for name, value in (
                ("REDDIT_CLIENT_ID", self.reddit_client_id),
                ("REDDIT_CLIENT_SECRET", self.reddit_client_secret),
                ("REDDIT_REFRESH_TOKEN", self.reddit_refresh_token),
            )
            if not value
        ]
        if missing:
            raise RuntimeError("Missing Reddit credentials: " + ", ".join(missing))
