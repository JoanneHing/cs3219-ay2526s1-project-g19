from uuid import UUID
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import SerializationContext, MessageField
from config import settings
from schemas.message import MatchedCriteriaSchema
from confluent_kafka.schema_registry.avro import AvroSerializer
from kafka.kafka_config import schema_registry_conf, producer_config

class KafkaController:
    def __init__(self):
        with open("kafka/schemas/match_found.avsc") as f:
            avro_schema_str = f.read()
        self.schema_registry_client = SchemaRegistryClient(schema_registry_conf)
        self.serializer = AvroSerializer(self.schema_registry_client, avro_schema_str)
        self.producer = Producer(producer_config)

    def pub_match_found(
        self,
        user1: UUID,
        user2: UUID,
        criteria: MatchedCriteriaSchema
    ):
        match = {
            "user_id_list": [user1, user2],
            "topic": criteria.topic,
            "difficulty": criteria.difficulty
        }
        key = "-".join(sorted([user1, user2]))
        self.producer.produce(
            topic=settings.topic_match_found,
            key=key,
            value=self.serializer(
                match,
                SerializationContext(settings.topic_match_found, MessageField.VALUE)
            )
        )
        return


kafka_controller = KafkaController()
