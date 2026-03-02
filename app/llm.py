from openai import OpenAI
from app.schemas import StudyResponse
import json

client = OpenAI()

def generate_notes(topic: str) -> StudyResponse:
    prompt = f"""
    Generate stuctured study notes for : {topic}

    Return only valid JSON with:
    title, summary, key_concepts, examples, practice_questions
    """
    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
        response_format={"type", "json_object"}
    )

    data = json.loads(response.choices[0].message.content)

    return StudyResponse(**data)