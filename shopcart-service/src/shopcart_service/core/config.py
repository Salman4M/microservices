import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    DB_HOST: str = ""
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "shopcart_db"
    DB_PORT: int = 5432
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEBUG: bool = False
    CLOUD_SQL_CONNECTION_NAME: str = ""

    model_config = SettingsConfigDict(
        env_file=(
            ".env.prod" if os.getenv("ENV") == "production" else ".env"
        ),
        case_sensitive=False,
        extra="ignore"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
