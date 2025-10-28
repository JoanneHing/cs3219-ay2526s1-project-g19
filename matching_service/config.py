from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "prd"
    redis_host: str = Field(alias="MATCHING_REDIS_HOST")
    redis_port: str = Field(alias="MATCHING_REDIS_PORT")
    user_service_url: str
    question_service_url: str

    # Kafka
    group_id: str = Field(alias="MATCHING_GROUP_ID")
    kafka_bootstrap_servers: str
    topic_match_found: str
    topic_session_created: str
    schema_registry_url: str
    schema_registry_key: str
    schema_registry_secret: str
    sasl_username: str
    sasl_password: str


settings = Settings()
