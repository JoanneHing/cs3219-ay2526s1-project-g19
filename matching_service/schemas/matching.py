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

    @field_validator('topics', mode='after')
    @classmethod
    def topics_are_valid(cls, value: list[str]) -> list[str]:
        valid_topics = django_question_service.get_topics()
        if len(value) > 0:
            for topic in value:
                if topic not in valid_topics:
                    raise ValueError(f"Topic {topic} is not a valid topic in the list {valid_topics}")
        return value

    @field_validator('difficulty', mode='after')
    @classmethod
    def difficulty_not_empty(cls, value: list[str]) -> list[str]:
        return value if len(value) > 0 else django_question_service.get_difficulty()

    @field_validator('topics', mode='after')
    @classmethod
    def difficulty_are_valid(cls, value: list[str]) -> list[str]:
        # skip validation for now
        return value
        valid_diffs = django_question_service.get_difficulty()
        if len(value) > 0:
            for diff in value:
                if diff not in valid_diffs:
                    raise ValueError(f"Difficulty {diff} is not a valid difficulty in the list {valid_diffs}")
        return value

    @model_validator(mode="after")
    def language_validation(self) -> Self:
        valid_languages = django_question_service.get_languages()
        invalid_lang_msg = "Language {} is not a valid language in the list " + str(valid_languages)
        if self.primary_lang is not None and self.primary_lang not in valid_languages:
            # skip validation for now
            # raise ValueError(invalid_lang_msg.format(self.primary_lang))
            pass
        for lang in self.secondary_lang:
            if lang not in valid_languages:
                # skip validation for now
                # raise ValueError(invalid_lang_msg.format(lang))
                pass
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
