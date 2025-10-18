import os

schema_registry_conf = {
    "url": os.getenv("SCHEMA_REGISTRY_URL"),
    "basic.auth.user.info": f"{os.getenv('SCHEMA_REGISTRY_KEY')}:{os.getenv('SCHEMA_REGISTRY_SECRET')}"
}
producer_admin_config = {
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    "sasl.username": os.getenv("SASL_USERNAME"),
    "sasl.password": os.getenv("SASL_PASSWORD"),
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN"
}
consumer_config = {
        'bootstrap.servers': os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        'group.id': 'question-service-group',
        'session.timeout.ms': 6000,
        'auto.offset.reset': 'earliest',
        "security.protocol": "SASL_SSL",
        'sasl.mechanisms': 'PLAIN',
        "sasl.username": os.getenv("SASL_USERNAME"),
        "sasl.password": os.getenv("SASL_PASSWORD")
    }

REQUEST_TOPIC = os.getenv("TOPIC_MATCH_FOUND", "match.found")
RESPONSE_TOPIC = os.getenv("TOPIC_QUESTION_CHOSEN", "question.chosen")
