from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "prd"
    redis_host: str
    redis_port: str
    user_service_url: str
    question_service_url: str

    # Kafka
    group_id: str
    kafka_bootstrap_servers: str
    topic_match_found: str
    topic_session_created: str
    topic_topics_updated: str = "topics.updated"
    topic_difficulties_updated: str = "difficulties.updated"
    schema_registry_url: str
    schema_registry_key: str
    schema_registry_secret: str
    sasl_username: str
    sasl_password: str


settings = Settings()
