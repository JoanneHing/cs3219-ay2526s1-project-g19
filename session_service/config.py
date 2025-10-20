from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "prd"
    session_db_host: str
    session_db_port: int
    session_db_name: str
    session_db_user: str
    session_db_password: str

    # Kafka variables
    topic_question_chosen: str
    topic_session_created: str
    schema_registry_url: str
    schema_registry_key: str
    schema_registry_secret: str
    kafka_bootstrap_servers: str
    sasl_username: str
    sasl_password: str

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def pg_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.session_db_user}:"
            f"{self.session_db_password}@{self.session_db_host}:"
            f"{self.session_db_port}/{self.session_db_name}"
        )


settings = Settings()
