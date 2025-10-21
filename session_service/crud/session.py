from uuid import UUID
from sqlmodel import select
from models.session import Session, SessionUser
from sqlalchemy.ext.asyncio import AsyncSession


class SessionRepo:
    def __init__(self):
        self.model = Session

    async def insert(
        self,
        obj: Session,
        db_session: AsyncSession
    ) -> None:
        db_session.add(obj)
        await db_session.commit()
        return

    async def get_active_session(
        self,
        user_id: UUID,
        db_session: AsyncSession
    ) -> Session:
        query = select(
            self.model
        ).join(
            SessionUser,
            self.model.id == SessionUser.session_id
        ).where(
            SessionUser.user_id == user_id,
            self.model.ended_at.is_(None)
        )
        res = await db_session.execute(query)
        return res.scalars().first()


session_repo = SessionRepo()
