from pydantic import BaseModel, Field
from typing import List

class StudyRequest(BaseModel):
    topic: str = Field(... , min_length=3 , max_length= 100)
    difficulty: str = "medium"

class StudyResponse(BaseModel):
    title:str
    summary: str
    key_concepts: List[str]
    examples: List[str]
    practice_questions: List[str]
    