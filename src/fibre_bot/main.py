from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import Settings
from .generator import generate_draft
from .policy import validate_and_compose
from .reddit import RedditClient
from .sources import fetch_candidates
from .state import load_posted_urls, record_post


LONDON = ZoneInfo("Europe/London")


def scheduled_time_is_eligible() -> bool:
    if os.getenv("GITHUB_EVENT_NAME") != "schedule":
        return True
    return datetime.now(LONDON).hour == 9


def run(*, dry_run: bool) -> int:
    if not scheduled_time_is_eligible():
        print("Not the 09:00 Europe/London schedule window; exiting safely.")
        return 0

    settings = Settings.from_env()
    settings.require_generation_credentials()
    posted = load_posted_urls(settings.state_path)

    reddit = None
    if not dry_run:
        reddit = RedditClient(settings)
        posted.update(reddit.recent_source_urls())

    candidates = fetch_candidates(settings.feeds)
    source = next((item for item in candidates if item.url not in posted), None)
    if source is None:
        print("No recent unused source item was found; no post created.")
        return 0

    draft = generate_draft(source, settings.openai_api_key, settings.openai_model)
    post = validate_and_compose(draft, source)

    if dry_run:
        print(json.dumps(post.__dict__, ensure_ascii=False, indent=2))
        return 0

    assert reddit is not None
    post_id = reddit.submit(post)
    record_post(settings.state_path, source.url, post_id)
    print(f"Published Reddit post {post_id} from {source.url}")
    return 0


def cli() -> None:
    parser = argparse.ArgumentParser(description="Post one UK fibre update")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="generate and validate a draft without contacting Reddit",
    )
    args = parser.parse_args()
    raise SystemExit(run(dry_run=args.dry_run))


if __name__ == "__main__":
    cli()

