import logging
import os
from django.core.management.base import BaseCommand
from question_service.kafka_client import create_consumer, send_response_message
from confluent_kafka import KafkaError
from question_service.models import Question
import json
import random

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs Kafka consumer for question service"

    def handle(self, *args, **options):
        consumer = create_consumer()
        consumer.subscribe([os.getenv("TOPIC_QUESTION_FOUND", "question.found")])
        self.stdout.write("Kafka consumer started...")

        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        self.stderr.write(f"Kafka error: {msg.error()}")
                    continue

                # Decode message
                payload = json.loads(msg.value().decode("utf-8"))
                logger.info(payload)
                difficulty = payload.get("difficulty")
                topic = payload.get("topic")

                # Fetch random question
                questions = Question.objects.filter(difficulty=difficulty, topic=topic)
                question = random.choice(list(questions)) if questions.exists() else None

                response = {
                    "request_id": payload.get("request_id"),  # echo request id if you want correlation
                    "question_id": question.id if question else None,
                    "question_text": question.text if question else None,
                }

                # Send response
                send_response_message(response)
                self.stdout.write(f"Processed request: {payload}, sent response.")
        except KeyboardInterrupt:
            self.stdout.write("Stopping consumer...")
        finally:
            consumer.close()
