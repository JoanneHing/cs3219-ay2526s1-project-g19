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

    @field_validator('topics', mode='after')
    @classmethod
    def topics_not_empty(cls, value: list[str]) -> list[str]:
        return value if len(value) > 0 else django_question_service.get_topics()

    @field_validator('difficulty', mode='after')
    @classmethod
    def difficulty_not_empty(cls, value: list[str]) -> list[str]:
        return value if len(value) > 0 else django_question_service.get_difficulty()

    @model_validator(mode="after")
    def language_validation(self) -> Self:
        if self.primary_lang is not None and len(self.secondary_lang) > 0:
            if self.primary_lang in self.secondary_lang:
                raise ValueError(f"Primary language {self.primary_lang} cannot be in secondary languages list {self.secondary_lang}")
        if self.primary_lang is None:
            if len(self.secondary_lang) > 0:
                raise ValueError(f"Cannot have secondary languages without primary language")
            self.secondary_lang = django_question_service.get_languages()
        return self


class MatchUserRequestSchema(BaseModel):
    user_id: UUID
    criteria: MatchingCriteriaSchema
