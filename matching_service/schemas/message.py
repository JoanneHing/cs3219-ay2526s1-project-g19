from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, model_validator

from schemas.events import SessionCreatedSchema


class MatchingStatus(StrEnum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    RELAX_LANGUAGE = "relax"


class MatchedCriteriaSchema(BaseModel):
    topic: str
    difficulty: str
    language: str


class SessionCreatedEventMessage(BaseModel):
    status: MatchingStatus
    session: SessionCreatedSchema | None = None

    @model_validator(mode="after")
    def check_success(cls, values) -> Self:
        if values.status == MatchingStatus.SUCCESS:
            if values.session is None:
                raise ValueError(
                    "Success status message must include a session object"
                )
        return values

    @model_validator(mode="after")
    def check_non_success(cls, values) -> Self:
        if values.status != MatchingStatus.SUCCESS:
            if values.session is not None:
                raise ValueError(
                    "Non-success status message cannot include a session object"
                )
        return values