from datetime import datetime
import logging
from uuid import UUID, uuid4
from confluent_kafka import Producer, Message
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import SerializationContext, MessageField
from config import settings
from schemas.events import MatchFoundSchema
from schemas.message import MatchedCriteriaSchema
from confluent_kafka.schema_registry.avro import AvroSerializer
from kafka.kafka_config import schema_registry_conf, producer_config

logger = logging.getLogger(__name__)


class KafkaController:
    def __init__(self):
        self.schema_registry_client = SchemaRegistryClient(schema_registry_conf)
        self.producer = Producer(producer_config)

    def delivery_report(self, err: Exception | None, msg: Message):
        if err is not None:
            logger.error(f"Delivery failed for record {msg.key().decode()}: {err}")
        else:
            logger.info(f"Record {msg.key().decode()} successfully produced to {msg.topic()} [{msg.partition()}]")

    def pub_match_found(
        self,
        user_id_list: list[UUID],
        criteria: MatchedCriteriaSchema
    ):
        with open("kafka/schemas/match_found.avsc") as f:
            avro_schema_str = f.read()
        serializer = AvroSerializer(self.schema_registry_client, avro_schema_str)
        match_id = uuid4()
        match = MatchFoundSchema(
            match_id=match_id,
            user_id_list=user_id_list,
            topic=criteria.topic,
            difficulty=criteria.difficulty,
            timestamp=datetime.now()
        )
        self.producer.produce(
            topic=settings.topic_match_found,
            key=str(match_id),
            value=serializer(
                match.model_dump(mode="json"),
                SerializationContext(settings.topic_match_found, MessageField.VALUE)
            ),
            on_delivery=self.delivery_report
        )
        return

    def shutdown(self):
        self.producer.flush()
        return


kafka_controller = KafkaController()
