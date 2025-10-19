from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class Session(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True, nullable=False)
    language: str = Field(nullable=False)


class SessionUser(SQLModel, table=True):
    session_id: UUID = Field(foreign_key="session.id")
    user_id: UUID = Field(nullable=False)


class SessionMetadata(SQLModel, table=True):
    session_id: UUID = Field(primary_key=True, foreign_key="session.id", ondelete="CASCADE")
    question_id: UUID = Field(nullable=False)
    time_taken: int = Field(nullable=False)
    attempts: int = Field(nullable=False)
