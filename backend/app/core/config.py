"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings.
    
    Loads configuration from environment variables and .env files.
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Metadata
    APP_NAME: str = "JobWatch AI"
    APP_ENV: str = "development"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Server Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    API_V1_STR: str = "/api/v1"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Database Configuration (Phase 1)
    DATABASE_URL: str = "postgresql+psycopg://jobwatch:jobwatch_dev@localhost:5432/jobwatch"
    TEST_DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    # Monitoring Engine Configuration (Phase 3)
    MONITORING_ENABLED: bool = False
    MONITORING_INTERVAL_SECONDS: int = 900
    MONITORING_MAX_CONCURRENCY: int = 5
    MONITORING_MAX_RETRIES: int = 2
    MONITORING_RETRY_BACKOFF_SECONDS: float = 5.0
    MONITORING_SOURCE_TIMEOUT_SECONDS: float = 120.0

    @field_validator("MONITORING_INTERVAL_SECONDS")
    @classmethod
    def validate_interval(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("MONITORING_INTERVAL_SECONDS must be greater than 0")
        return v

    @field_validator("MONITORING_MAX_CONCURRENCY")
    @classmethod
    def validate_concurrency(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("MONITORING_MAX_CONCURRENCY must be greater than 0")
        return v

    @field_validator("MONITORING_MAX_RETRIES")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        if v < 0:
            raise ValueError("MONITORING_MAX_RETRIES cannot be negative")
        return v

    @field_validator("MONITORING_RETRY_BACKOFF_SECONDS")
    @classmethod
    def validate_retry_backoff(cls, v: float) -> float:
        if v < 0:
            raise ValueError("MONITORING_RETRY_BACKOFF_SECONDS cannot be negative")
        return v

    @field_validator("MONITORING_SOURCE_TIMEOUT_SECONDS")
    @classmethod
    def validate_source_timeout(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("MONITORING_SOURCE_TIMEOUT_SECONDS must be greater than 0")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    return Settings()
