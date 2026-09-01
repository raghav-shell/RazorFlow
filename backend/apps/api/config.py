"""Application configuration management with Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly typed application configuration loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
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
    CORS_ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"
    )

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

    # Razorpay Provider Safety & Environment Configuration
    RAZORPAY_MODE: str = Field(default="test")  # "test" or "live"
    RAZORPAY_PRODUCTION_ENABLED: bool = Field(default=False)  # Explicit fail-closed safety flag
    RAZORPAY_KEY_ID: Optional[str] = Field(default=None)
    RAZORPAY_KEY_SECRET: Optional[str] = Field(default=None)
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = Field(default=None)
    RAZORPAY_BASE_URL: str = Field(default="https://api.razorpay.com/v1")

    # AI & Gemini Configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GEMINI_MODEL: str = Field(default="gemini-3.6-flash")
    AI_TIMEOUT_SECONDS: float = Field(default=15.0)
    AI_ENABLED: bool = Field(default=True)
    AI_PROMPT_VERSION: str = Field(default="v1.0.0")

    # Observability (Non-blocking telemetry)
    LANGFUSE_ENABLED: bool = Field(default=False)
    LANGFUSE_PUBLIC_KEY: Optional[str] = Field(default=None)
    LANGFUSE_SECRET_KEY: Optional[str] = Field(default=None)
    LANGFUSE_HOST: str = Field(default="https://cloud.langfuse.com")

    def validate_production_safety(self) -> None:
        """Validates critical security and safety invariants on startup."""
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY in ("dev-insecure-secret-key-32chars-min!!", ""):
                raise ValueError(
                    "CRITICAL SECURITY ERROR: Default SECRET_KEY detected in production!"
                )
            if self.ENCRYPTION_KEY in ("dev-insecure-encryption-key-32ch!", ""):
                raise ValueError(
                    "CRITICAL SECURITY ERROR: Default ENCRYPTION_KEY detected in production!"
                )
            if "*" in self.CORS_ALLOWED_ORIGINS:
                raise ValueError(
                    "CRITICAL SECURITY ERROR: Wildcard CORS origin is forbidden in production!"
                )
            if not self.DATABASE_URL:
                raise ValueError(
                    "CRITICAL CONFIGURATION ERROR: DATABASE_URL must be configured in production!"
                )
            if not self.CELERY_BROKER_URL:
                raise ValueError(
                    "CRITICAL CONFIGURATION ERROR: CELERY_BROKER_URL must be configured in production!"
                )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns cached singleton application settings."""
    return Settings()
