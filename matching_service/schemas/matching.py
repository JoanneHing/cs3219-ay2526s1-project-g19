from typing import Self
from uuid import UUID
from pydantic import BaseModel, field_validator, model_validator

from service.django_question_service import django_question_service


class MatchingCriteriaSchema(BaseModel):
    topics: list[str]
    difficulty: list[str]
    primary_lang: str | None = None
    secondary_lang: list[str]
    proficiency: int = 0


class MatchUserRequestSchema(BaseModel):
    user_id: UUID
    criteria: MatchingCriteriaSchema


class MatchedCriteriaSchema(BaseModel):
    topic: str
    difficulty: str
    language: str


VALID_LANGUAGE_LIST = [
    "Python",
    "Java",
    "Javascript",
    "C",
    "C++"
]
