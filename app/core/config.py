# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str        # async URL, e.g. postgresql+asyncpg://webhook:webhook@localhost:5432/webhook_platform
    SYNC_DATABASE_URL: str   # sync URL for Celery, e.g. postgresql+psycopg2://webhook:webhook@localhost:5432/webhook_platform
    REDIS_URL: str = "redis://localhost:6379/0"
    PLATFORM_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()