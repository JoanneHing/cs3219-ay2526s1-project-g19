from datetime import datetime
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from pg_db.core import engine
from crud.session import session_repo
from models.session import Session, SessionUser
from schemas.events import SessionCreated


logger = logging.getLogger(__name__)


class SessionService:
    def __init__(self):
        pass

    async def start_new_session(
        self,
        session_id: UUID,
        session_created: SessionCreated,
        db_session: AsyncSession
    ) -> None:
        async with AsyncSession(engine) as db_session:
            for user_id in session_created.user_id_list:
                active_session = await session_repo.get_active_session(
                    user_id=user_id,
                    db_session=db_session
                )
                if active_session:
                    logger.error(f"User {user_id} has an active session {active_session.id}")
                    return
            session=Session(
                id=session_id,
                started_at=datetime.now(),
                language=session_created.language,
                question_id=session_created.question_id,
                session_users=[
                    SessionUser(
                        session_id=session_id,
                        user_id=user_id
                    )
                    for user_id in session_created.user_id_list
                ]
            )
            logger.info(f"Creating new session {session_created.id}")
            await session_repo.insert(
                obj=session,
                db_session=db_session
            )
        return

    async def get_active_session(
        self,
        user_id: UUID,
        db_session: AsyncSession
    ) -> Session:
        return await session_repo.get_active_session(
            user_id=user_id,
            db_session=db_session
        )

    async def end_session(
        self,
        session_id: UUID,
        db_session: AsyncSession
    ) -> None:
        await session_repo.end_session(
            session_id=session_id,
            db_session=db_session
        )
        return

session_service = SessionService()
