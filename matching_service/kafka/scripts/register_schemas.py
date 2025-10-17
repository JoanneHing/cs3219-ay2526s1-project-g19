# scripts/register_schemas.py
import logging
from confluent_kafka.schema_registry import Schema

from kafka.kafka_controller import kafka_controller

logger = logging.getLogger(__name__)

def register_schemas():
    # Example schema file
    with open("kafka/schemas/match_found.avsc") as f:
        schema_str = f.read()

    subject = "match.found-value"
    schema = Schema(schema_str, "AVRO")

    registered = kafka_controller.schema_registry_client.register_schema(subject, schema)
    logger.info(f"Registered schema {subject} with ID {registered}")

if __name__ == "__main__":
    register_schemas()
