"""Application configuration management with Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly typed application configuration loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App Info
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    APP_NAME: str = Field(default="RazorFlow-API")

    # API Server
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    API_V1_PREFIX: str = Field(default="/api/v1")

    # Security
    SECRET_KEY: str = Field(default="dev-insecure-secret-key-32chars-min!!")
    ENCRYPTION_KEY: str = Field(default="dev-insecure-encryption-key-32ch!")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://razorflow:razorflow_dev_password@localhost:5432/razorflow_db"
    )
    DATABASE_SYNC_URL: Optional[str] = Field(
        default="postgresql://razorflow:razorflow_dev_password@localhost:5432/razorflow_db"
    )

    # Redis & Celery
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns cached singleton application settings."""
    return Settings()
