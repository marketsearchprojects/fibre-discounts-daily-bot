from __future__ import annotations

import json

import requests

from .models import ALLOWED_FLAIRS, Candidate, GeneratedDraft


OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "flair": {"type": "string", "enum": list(ALLOWED_FLAIRS)},
        "news_paragraph": {"type": "string"},
    },
    "required": ["title", "flair", "news_paragraph"],
    "additionalProperties": False,
}


INSTRUCTIONS = """You edit a small UK fibre-broadband education community.
Use only the supplied external RSS title, summary, date and URL. Do not add a
fact that is absent from that material. Produce one plain-English paragraph of
45-90 words explaining what changed and why it matters to a UK broadband
customer. Do not advertise in this paragraph. Do not claim any provider is
always superior, the best, guaranteed, or cheaper unless the supplied material
states an objective comparison. Choose exactly one allowed flair. The title
must be factual, 20-140 characters, and contain no clickbait."""


def generate_draft(candidate: Candidate, api_key: str, model: str) -> GeneratedDraft:
    payload = {
        "model": model,
        "reasoning": {"effort": "none"},
        "instructions": INSTRUCTIONS,
        "input": json.dumps(
            {
                "source_title": candidate.title,
                "source_summary": candidate.summary,
                "source_published_at": candidate.published_at.isoformat(),
                "source_url": candidate.url,
            },
            ensure_ascii=False,
        ),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "fibre_reddit_draft",
                "strict": True,
                "schema": OUTPUT_SCHEMA,
            }
        },
        "max_output_tokens": 700,
        "store": False,
    }
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "completed":
        raise RuntimeError(f"OpenAI response was not completed: {data.get('status')}")

    output_text = ""
    for item in data.get("output", []):
        if item.get("type") != "message":
            continue
        for part in item.get("content", []):
            if part.get("type") == "refusal":
                raise RuntimeError("OpenAI declined to draft this source item")
            if part.get("type") == "output_text":
                output_text += part.get("text", "")
    if not output_text:
        raise RuntimeError("OpenAI response contained no draft text")

    parsed = json.loads(output_text)
    return GeneratedDraft(
        title=str(parsed["title"]).strip(),
        flair=str(parsed["flair"]).strip(),
        news_paragraph=str(parsed["news_paragraph"]).strip(),
    )

