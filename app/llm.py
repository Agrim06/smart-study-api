from typing import Optional
import json

from openai import OpenAI
from pydantic import ValidationError

from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from app.schemas import StudyResponse
from app.cache import cache

import logging

logger = logging.getLogger(__name__)


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
                try:
                    normalized_items.append(json.dumps(item, ensure_ascii=False))
                except TypeError:
                    normalized_items.append(str(item))
        data[field] = normalized_items

    for field in ("key_concepts", "examples", "practice_questions"):
        _ensure_list(field)
        _ensure_str_items(field)

    return data


def generate_notes(topic: str , difficulty: str) -> StudyResponse:
    logger.info(f"Generating {difficulty} level notes for the topic:{topic}")

    cache_key = f"{topic}:{difficulty}"

    if cache_key in cache:
        logger.info(f"Cache HIT for {cache_key}")
        return cache[cache_key]
    else:
        logger.info(f"Cache MISS for {cache_key}")

    if client is None:
        fallback = _fallback_notes(topic)

        cache[cache_key] = fallback
        return fallback

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
                    Generate {difficulty} level study notes for: {topic}

                    Return ONLY valid JSON in this exact format:

                    {{
                    "title": "string",
                    "summary": "string",
                    "key_concepts": ["string","string"],
                    "examples": ["string"],
                    "practice_questions": ["string","string"]
                    }}

                    Do not include explanations or text outside the JSON.
                    """
                    }
            ],
            temperature=0.7,
        )

        raw_content = response.choices[0].message.content
        content = _extract_content(raw_content)

        if not content or not str(content).strip():
            return _fallback_notes(topic)

        data = json.loads(content)
        normalized = _normalize_llm_payload(data)

        result = StudyResponse(**normalized)
        cache[cache_key] = result

        return result
    
    except (json.JSONDecodeError, ValidationError, Exception) as e:
        print("LLM ERROR:", e)
        return _fallback_notes(topic)