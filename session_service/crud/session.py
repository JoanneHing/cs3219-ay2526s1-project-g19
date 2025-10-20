from models.session import Session
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


session_repo = SessionRepo()
