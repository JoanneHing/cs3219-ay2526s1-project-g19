import logging
from confluent_kafka import Producer, Consumer, KafkaError, Message
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
import json
from question_service.kafka.config import REQUEST_TOPIC, RESPONSE_TOPIC, \
    consumer_config, producer_admin_config, schema_registry_conf
from question_service.kafka.schemas.match_found import MatchFound
from question_service.view import QuestionViewSet


logger = logging.getLogger(__name__)

class KafkaClient:
    def __init__(self):
        self.deserializer = AvroDeserializer(
            schema_registry_client=SchemaRegistryClient(schema_registry_conf)
        )
        self.producer = Producer(producer_admin_config)
        self.consumer = Consumer(consumer_config)

    def send_response_message(self, message: dict):
        self.producer.produce(RESPONSE_TOPIC, json.dumps(message).encode("utf-8"))

    def consumer_listen(self, topic, handler):
        self.consumer.subscribe([topic])
        logger.info(f"Kafka consumer started. Subscribed to {topic}")

        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error(f"Kafka error: {msg.error()}")
                    continue
                handler(msg)
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
        finally:
            self.consumer.close()

    def handle_match_found(self, msg: Message):
        key = msg.key().decode()
        payload = self.deserializer(msg.value())
        logger.info(f"Received match id {key}")
        logger.info(f"Received message: {payload}")
        match = MatchFound(**payload)
        logger.info(f"Match object: {match}")

    def match_found_consumer(self):
        self.consumer_listen(
            topic=REQUEST_TOPIC,
            handler=self.handle_match_found
        )
        return

kafka_client = KafkaClient()
