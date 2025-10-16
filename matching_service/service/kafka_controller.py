from confluent_kafka import Producer

class KafkaController:
    def __init__(self):
        config = {
            "bootstrap.servers": "peerprep_kafka:9092"
        }
        self.producer = Producer(config)

    def pub_match_found(self):
        self.producer.produce(
            topic="match.found",
            key="1",
            value="2"
        )
        return


kafka_controller = KafkaController()
