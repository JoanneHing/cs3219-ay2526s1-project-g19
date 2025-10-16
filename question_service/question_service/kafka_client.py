from confluent_kafka import Producer, Consumer, KafkaError
import json
import os

KAFKA_BOOTSTRAP_SERVERS = "peerprep_kafka:9092"
REQUEST_TOPIC = os.getenv("TOPIC_MATCH_FOUND", "match.found")
RESPONSE_TOPIC = os.getenv("TOPIC_QUESTION_FOUND", "question.found")
GROUP_ID = "question-service-group"

producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})

def send_response_message(message: dict):
    producer.produce(RESPONSE_TOPIC, json.dumps(message).encode("utf-8"))

def create_consumer():
    return Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
    })
