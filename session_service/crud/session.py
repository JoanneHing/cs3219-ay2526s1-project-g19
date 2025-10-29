from datetime import datetime
from uuid import UUID
from fastapi import HTTPException, status
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
        return res.scalar_one_or_none()

    async def end_session(
        self,
        session_id: UUID,
        db_session: AsyncSession
    ) -> Session:
        query = select(
            self.model
        ).where(
            self.model.id == session_id,
            self.model.ended_at.is_(None)
        )
        res = await db_session.execute(query)
        session = res.scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )
        session.ended_at = datetime.now()
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        return session


class SessionUserRepo:
    def __init__(self):
        self.model = SessionUser

    async def get_by_session_id(
        self,
        session_id: UUID,
        db_session: AsyncSession
    ) -> list[UUID]:
        query = select(
            self.model.user_id
        ).where(
            self.model.session_id == session_id
        )
        res = await db_session.execute(query)
        return res.scalars().all()


session_repo = SessionRepo()
session_user_repo = SessionUserRepo()
