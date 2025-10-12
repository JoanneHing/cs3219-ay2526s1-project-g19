from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "prd"
    redis_host: str
    redis_port: str
    user_service_url: str
    question_service_url: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
