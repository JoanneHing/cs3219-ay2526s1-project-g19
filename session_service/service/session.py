from datetime import datetime
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from kafka.kafka_client import kafka_client
from pg_db.core import engine
from crud.session import session_repo, session_user_repo
from models.session import Session, SessionUser
from schemas.events import SessionCreated, SessionEnd
from confluent_kafka.schema_registry.avro import AvroSerializer

from schemas.session import ActiveSessionSchema


logger = logging.getLogger(__name__)


class SessionService:
    def __init__(self):
        pass

    async def start_new_session(
        self,
        session_id: UUID,
        session_created: SessionCreated,
        started_at: datetime
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
                started_at=started_at,
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
            logger.info(f"Creating new session {session_created.session_id}")
            await session_repo.insert(
                obj=session,
                db_session=db_session
            )
        return

    async def get_active_session(
        self,
        user_id: UUID,
        db_session: AsyncSession
    ) -> ActiveSessionSchema | None:
        session = await session_repo.get_active_session(
            user_id=user_id,
            db_session=db_session
        )
        if not session:
            logger.info(f"No active session found for user {user_id}")
            return
        user_id_list = await session_user_repo.get_by_session_id(
            session_id=session.id,
            db_session=db_session
        )
        if len(user_id_list) == 0:
            logger.info(f"No users found in this session {session.id}")
            return
        user_id_list = [id for id in user_id_list if id != user_id]
        if len(user_id_list) != 1:
            logger.info(f"No matched user found in this session {session.id} for user {user_id}")
            return
        return ActiveSessionSchema(
            id=session.id,
            started_at=session.started_at,
            ended_at=session.ended_at,
            question_id=session.question_id,
            language=session.language,
            matched_user_id=user_id_list[0]
        )

    async def end_session(
        self,
        session_id: UUID,
        db_session: AsyncSession
    ) -> None:
        session = await session_repo.end_session(
            session_id=session_id,
            db_session=db_session
        )
        # publish session end event to kafka
        with open("kafka/schemas/session_end.avsc") as f:
            session_end_schema = f.read()
        serializer = AvroSerializer(
            kafka_client.schema_registry_client,
            session_end_schema
        )
        session_end = SessionEnd(
            session_id=session.id,
            ended_at=session.ended_at,
            timestamp=datetime.now()
        )
        kafka_client.produce(
            topic=settings.topic_session_end,
            key=str(session_id),
            value=session_end.model_dump(mode="json"),
            serializer=serializer
        )
        return


session_service = SessionService()
