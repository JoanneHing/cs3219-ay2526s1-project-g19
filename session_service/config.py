from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = "prd"


settings = Settings()
