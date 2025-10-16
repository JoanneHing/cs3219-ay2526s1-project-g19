import logging
import os
import time
import json
import random
from django.core.management.base import BaseCommand
from confluent_kafka import KafkaError
from confluent_kafka.admin import AdminClient
from question_service.kafka_client import create_consumer, send_response_message
from question_service.models import Question

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "peerprep_kafka:9092")
TOPICS = [
    os.getenv("TOPIC_MATCH_FOUND", "match.found"),
    os.getenv("TOPIC_QUESTION_FOUND", "question.found"),
]

def wait_for_kafka_topics(timeout=60):
    """Wait until Kafka is reachable and all required topics exist."""
    admin = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            md = admin.list_topics(timeout=5)
            existing_topics = md.topics.keys()
            if all(topic in existing_topics for topic in TOPICS):
                logger.info(f"All topics ready: {TOPICS}")
                return
        except Exception as e:
            logger.warning(f"Kafka not ready yet: {e}")
        time.sleep(2)
    raise TimeoutError(f"Topics {TOPICS} not available after {timeout} seconds")

class Command(BaseCommand):
    help = "Runs Kafka consumer for question service"

    def handle(self, *args, **options):
        self.stdout.write("Waiting for Kafka topics to be ready...")
        wait_for_kafka_topics()
        self.stdout.write("Kafka topics ready. Starting consumer...")

        consumer = create_consumer()
        consumer.subscribe([os.getenv("TOPIC_MATCH_FOUND", "match.found")])
        self.stdout.write("Kafka consumer started...")

        try:
            while True:
                msg = consumer.poll(1.0)
                logger.info("Waiting for message...")
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        self.stderr.write(f"Kafka error: {msg.error()}")
                    continue

                # Decode message
                payload = json.loads(msg.value().decode("utf-8"))
                logger.info(f"Received message: {payload}")
                # difficulty = payload.get("difficulty")
                # topic = payload.get("topic")

                # # Fetch random question
                # questions = Question.objects.filter(difficulty=difficulty, topic=topic)
                # question = random.choice(list(questions)) if questions.exists() else None

                # response = {
                #     "request_id": payload.get("request_id"),
                #     "question_id": question.id if question else None,
                #     "question_text": question.text if question else None,
                # }

                # # Send response
                # send_response_message(response)
                # self.stdout.write(f"Processed request: {payload}, sent response.")
        except KeyboardInterrupt:
            self.stdout.write("Stopping consumer...")
        finally:
            consumer.close()
