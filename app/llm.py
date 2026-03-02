from typing import Optional
import json

from openai import OpenAI
from pydantic import ValidationError

from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from app.schemas import StudyResponse


def _fallback_notes(topic: str) -> StudyResponse:
    """Deterministic offline/test-safe notes generation."""
    return StudyResponse(
        title=f"Study notes for {topic}",
        summary=f"High-level overview of {topic}.",
        key_concepts=[
            f"Core idea 1 of {topic}",
            f"Core idea 2 of {topic}",
        ],
        examples=[
            f"Example scenario applying {topic}.",
        ],
        practice_questions=[
            f"Explain the main ideas of {topic}.",
            f"Give a real-world example of {topic}.",
        ],
    )


client: Optional[OpenAI] = None
if OPENROUTER_API_KEY:
    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )


def _extract_content(raw_content):
    # Newer OpenAI-style clients may return a list of content parts.
    if isinstance(raw_content, str):
        return raw_content
    if isinstance(raw_content, list):
        parts = []
        for part in raw_content:
            if isinstance(part, dict) and "text" in part:
                parts.append(part["text"])
            else:
                parts.append(str(part))
        return "".join(parts)
    return str(raw_content)


def _normalize_llm_payload(data: dict) -> dict:
    """Adapt OpenRouter JSON into the StudyResponse schema."""

    def _ensure_list(field: str) -> None:
        value = data.get(field)
        if isinstance(value, dict):
            # Use the dict values, ordered by key if possible.
            items = []
            try:
                keys = sorted(value.keys(), key=lambda k: str(k))
            except Exception:
                keys = value.keys()
            for k in keys:
                items.append(value[k])
            data[field] = items

    def _ensure_str_items(field: str) -> None:
        value = data.get(field)
        if not isinstance(value, list):
            return
        normalized_items = []
        for item in value:
            if isinstance(item, str):
                normalized_items.append(item)
            else:
                # For structured items (lists/dicts), keep full info as JSON string.
                try:
                    normalized_items.append(json.dumps(item, ensure_ascii=False))
                except TypeError:
                    normalized_items.append(str(item))
        data[field] = normalized_items

    # First, turn mapping-style fields into lists.
    for field in ("key_concepts", "examples", "practice_questions"):
        _ensure_list(field)
        _ensure_str_items(field)

    return data


def generate_notes(topic: str) -> StudyResponse:
    # If there is no configured client (e.g. in tests / local dev),
    # fall back to deterministic notes instead of raising 500.
    if client is None:
        return _fallback_notes(topic)

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a structured study assistant. Always return valid JSON only.",
                },
                {
                    "role": "user",
                    "content": f"""
                    Generate structured study notes for: {topic}

                    Return ONLY valid JSON with:
                    title, summary, key_concepts, examples, practice_questions
                    """,
                },
            ],
            temperature=0.7,
        )

        raw_content = response.choices[0].message.content
        content = _extract_content(raw_content)

        # If the model returned an empty/whitespace response, fall back directly.
        if not content or not str(content).strip():
            return _fallback_notes(topic)

        data = json.loads(content)
        normalized = _normalize_llm_payload(data)
        return StudyResponse(**normalized)
    except (json.JSONDecodeError, ValidationError, Exception) as e:
        # In case of any LLM/JSON issues, return a safe fallback
        print("LLM ERROR:", e)
        return _fallback_notes(topic)