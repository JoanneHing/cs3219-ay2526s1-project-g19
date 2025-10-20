import json
import logging
import logging.config
from uuid import uuid4
from config import settings
from kafka.kafka_client import kafka_client
from confluent_kafka import Message
from confluent_kafka.schema_registry.avro import AvroSerializer
from schemas.events import QuestionChosen, SessionCreated


with open("log_config.json", "r") as f:
    config = json.load(f)
logging.config.dictConfig(config)
logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)


class QuestionChosenConsumer:
    def __init__(self):
        self.topics = [settings.topic_question_chosen]
        with open("kafka/schemas/session_created.avsc") as f:
            session_created_schema = f.read()
        self.session_created_serializer = AvroSerializer(
            kafka_client.schema_registry_client,
            session_created_schema
        )

    def listen(self):
        kafka_client.consumer_listen(
            topics=self.topics,
            handler=self.handle_question_chosen
        )
        return

    def handle_question_chosen(self, msg: Message):
        key = msg.key().decode()
        value = kafka_client.deserializer(msg.value())
        question_chosen = QuestionChosen(
            **value
        )
        logger.info(f"Received key {key}: value {value}")
        session_id = uuid4()
        session_created = SessionCreated(
            **question_chosen.model_dump(),
            session_id=session_id
        )
        kafka_client.produce(
            topic=settings.topic_session_created,
            key=str(session_id),
            value=session_created.model_dump(mode="json"),
            serializer=self.session_created_serializer
        )
        return


if __name__=="__main__":
    consumer = QuestionChosenConsumer()
    consumer.listen()
    