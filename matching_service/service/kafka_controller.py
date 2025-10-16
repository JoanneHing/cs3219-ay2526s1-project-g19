import json
from uuid import UUID
from confluent_kafka import Producer
from config import settings
from schemas.message import MatchedCriteriaSchema

class KafkaController:
    def __init__(self):
        config = {
            "bootstrap.servers": "peerprep_kafka:9092"
        }
        self.producer = Producer(config)

    def pub_match_found(
        self,
        user1: UUID,
        user2: UUID,
        criteria: MatchedCriteriaSchema
    ):
        match = {
            "user1_id": user1,
            "user2_id": user2,
            "difficulty": criteria.difficulty,
            "topic": criteria.topic,
            "language": criteria.language
        }
        key = "-".join(sorted([user1, user2]))
        self.producer.produce(
            topic=settings.topic_match_found,
            key=key,
            value=json.dumps(match)
        )
        return


kafka_controller = KafkaController()
