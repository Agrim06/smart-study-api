from pydantic import BaseModel
from typing import List

class StudyRequest(BaseModel):
    topic: str

class StudyResponse(BaseModel):
    title:str
    summary: str
    key_concepts: List[str]
    examples: List[str]
    practice_questions: List[str]
    