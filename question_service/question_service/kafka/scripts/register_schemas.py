import logging
from confluent_kafka.schema_registry import Schema

from question_service.kafka.kafka_client import kafka_client

logger = logging.getLogger(__name__)

def register_schemas():
    # Example schema file
    with open("question_service/kafka/schemas/question_chosen.avsc") as f:
        schema_str = f.read()

    subject = "question.chosen-value"
    schema = Schema(schema_str, "AVRO")

    registered = kafka_client.schema_registry_client.register_schema(subject, schema)
    logger.info(f"Registered schema {subject} with ID {registered}")

if __name__ == "__main__":
    register_schemas()
