import logging
from sqlalchemy.ext.asyncio import AsyncSession
from pg_db.core import engine
from crud.session import session_repo
from models.session import Session


logger = logging.getLogger(__name__)


class SessionService:
    def __init__(self):
        pass

    async def start_new_session(self, session: Session) -> None:
        async with AsyncSession(engine) as db_session:
            logger.info(f"Creating new session {session.id}")
            await session_repo.insert(
                obj=session,
                db_session=db_session
            )
        return


session_service = SessionService()
