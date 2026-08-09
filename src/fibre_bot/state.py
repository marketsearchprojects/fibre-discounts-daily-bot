from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


def load_posted_urls(path: Path) -> set[str]:
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(item["source_url"]) for item in data.get("posts", [])}


def record_post(path: Path, source_url: str, reddit_post_id: str) -> None:
    data = {"posts": []}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    posts = list(data.get("posts", []))
    posts.append(
        {
            "source_url": source_url,
            "reddit_post_id": reddit_post_id,
            "published_at": datetime.now(UTC).isoformat(),
        }
    )
    data["posts"] = posts[-365:]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

