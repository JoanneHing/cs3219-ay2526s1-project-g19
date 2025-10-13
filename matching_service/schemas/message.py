from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, model_validator


class MatchingStatus(StrEnum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    RELAX_LANGUAGE = "relax"


class MatchedCriteriaSchema(BaseModel):
    topic: str
    difficulty: str
    language: str


class MatchingEventMessage(BaseModel):
    status: MatchingStatus
    matched_user_id: UUID | None = None
    criteria: MatchedCriteriaSchema | None = None

    @model_validator(mode="after")
    def check_success(self) -> Self:
        if self.status == MatchingStatus.SUCCESS:
            if self.matched_user_id == None or self.criteria == None:
                raise ValueError(f"Success status message must have matched user id and criteria")
        return self

    @model_validator(mode="after")
    def check_non_success(self) -> Self:
        if self.status != MatchingStatus.SUCCESS:
            if self.matched_user_id or self.criteria:
                raise ValueError(f"Non-success status message cannot have matched user id or criteria")
        return self
