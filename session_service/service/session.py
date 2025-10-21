from datetime import datetime
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from kafka.kafka_client import kafka_client
from pg_db.core import engine
from crud.session import session_repo
from models.session import Session, SessionUser
from schemas.events import SessionCreated, SessionEnd
from confluent_kafka.schema_registry.avro import AvroSerializer


logger = logging.getLogger(__name__)


class SessionService:
    def __init__(self):
        pass

    async def start_new_session(
        self,
        session_id: UUID,
        session_created: SessionCreated
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
