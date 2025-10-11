from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "prd"
    redis_host: str
    redis_port: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
