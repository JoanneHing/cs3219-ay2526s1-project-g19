from uuid import UUID
from pydantic import BaseModel


class MatchUserRequestSchema(BaseModel):
    user_id: UUID
    topics: list[str]
    difficulty: list = []
    primary_lang: None = None
    secondary_lang: list = []
    proficiency: int = 0
