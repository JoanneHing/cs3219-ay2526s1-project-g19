from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


class Session(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: datetime | None = Field(default=None, nullable=True)
    question_id: UUID = Field(nullable=False)
    language: str = Field(nullable=False)


class SessionUser(SQLModel, table=True):
    session_id: UUID = Field(foreign_key="session.id", primary_key=True)
    user_id: UUID = Field(nullable=False, primary_key=True)


class SessionMetadata(SQLModel, table=True):
    session_id: UUID = Field(primary_key=True, foreign_key="session.id", ondelete="CASCADE")
    attempts: int = Field(nullable=False)
