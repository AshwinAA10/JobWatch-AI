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
    DB_CONNECT_TIMEOUT: int = 10
    DB_ECHO: bool = False

    # Reliability & Production Hardening (Phase 11)
    RATE_LIMIT_ENABLED: bool = False
    AUTH_RATE_LIMIT_PER_MINUTE: int = 15
    API_RATE_LIMIT_PER_MINUTE: int = 120

    # Monitoring Engine Configuration (Phase 3)
    MONITORING_ENABLED: bool = False
    MONITORING_INTERVAL_SECONDS: int = 900
    MONITORING_MAX_CONCURRENCY: int = 5
    MONITORING_MAX_RETRIES: int = 2
    MONITORING_RETRY_BACKOFF_SECONDS: float = 5.0
    MONITORING_SOURCE_TIMEOUT_SECONDS: float = 120.0

    # Deduplication & Job Identity Configuration (Phase 4)
    DEDUP_ENABLED: bool = True
    DEDUP_HIGH_THRESHOLD: float = 0.90
    DEDUP_MEDIUM_THRESHOLD: float = 0.75
    DEDUP_MAX_CANDIDATES: int = 100
    DEDUP_LOOKBACK_DAYS: int = 90

    # Authentication & User Security Configuration (Phase 5)
    AUTH_ENABLED: bool = True
    JWT_SECRET: str = "dev-insecure-jwt-secret-key-change-in-production-min32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # AI Intelligence & Semantic Matching Configuration (Phase 7)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSION: int = 1536
    OPENAI_TIMEOUT: float = 30.0
    OPENAI_MAX_RETRIES: int = 2

    # AI Feature Flags (Independent Subsystem Control)
    AI_EXTRACTION_ENABLED: bool = True
    AI_EMBEDDING_ENABLED: bool = True
    AI_HYBRID_MATCHING_ENABLED: bool = True
    AI_EXPLANATIONS_ENABLED: bool = True

    # Hybrid Scoring Weights (must sum to 1.0)
    HYBRID_DETERMINISTIC_WEIGHT: float = 0.70
    HYBRID_SEMANTIC_WEIGHT: float = 0.30

    # Phase 8: Notification & Alerting Settings
    NOTIFICATIONS_ENABLED: bool = True
    EMAIL_NOTIFICATIONS_ENABLED: bool = False
    EMAIL_PROVIDER: str = "smtp"
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "alerts@jobwatch.ai"
    SMTP_FROM_NAME: str = "JobWatch AI"
    SMTP_USE_TLS: bool = True
    SMTP_TIMEOUT_SECONDS: float = 10.0
    EMAIL_REQUIRE_VERIFIED: bool = False
    WEBHOOK_NOTIFICATIONS_ENABLED: bool = False
    WEBHOOK_TIMEOUT_SECONDS: float = 10.0
    NOTIFICATION_MAX_RETRIES: int = 4
    NOTIFICATION_PROCESSING_TIMEOUT_SECONDS: int = 600
    NOTIFICATION_HOURLY_RATE_LIMIT: int = 10
    NOTIFICATION_DEFAULT_MIN_SCORE: float = 75.0

    @field_validator("DEDUP_HIGH_THRESHOLD")
    @classmethod
    def validate_high_threshold(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("DEDUP_HIGH_THRESHOLD must be between 0.0 and 1.0")
        return v

    @field_validator("DEDUP_MEDIUM_THRESHOLD")
    @classmethod
    def validate_medium_threshold(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("DEDUP_MEDIUM_THRESHOLD must be between 0.0 and 1.0")
        return v

    @field_validator("DEDUP_MAX_CANDIDATES")
    @classmethod
    def validate_max_candidates(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("DEDUP_MAX_CANDIDATES must be greater than 0")
        return v

    @field_validator("DEDUP_LOOKBACK_DAYS")
    @classmethod
    def validate_lookback_days(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("DEDUP_LOOKBACK_DAYS must be greater than 0")
        return v

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

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_access_token_expire(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be greater than 0")
        return v

    @field_validator("JWT_SECRET")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or len(v.strip()) < 8:
            raise ValueError("JWT_SECRET must be at least 8 characters long")
        return v

    @field_validator("HYBRID_DETERMINISTIC_WEIGHT", "HYBRID_SEMANTIC_WEIGHT")
    @classmethod
    def validate_hybrid_weights(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Hybrid weights must be between 0.0 and 1.0")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    def validate_production_configuration(self) -> None:
        """Fail fast if critical security or infrastructure settings are invalid in production."""
        if self.APP_ENV.lower() not in ("production", "prod"):
            return

        errors: List[str] = []

        # 1. DEBUG must be False
        if self.DEBUG:
            errors.append("DEBUG mode must be disabled in production.")

        # 2. Secret key strength & non-default check
        insecure_keys = [
            "dev-insecure-jwt-secret-key-change-in-production-min32chars",
            "change_this_to_a_secure_random_string_in_production",
            "secret",
            "changeme",
        ]
        if self.JWT_SECRET in insecure_keys or len(self.JWT_SECRET) < 32:
            errors.append(
                "JWT_SECRET must be at least 32 characters and cannot use default/insecure development keys in production."
            )

        # 3. Database URL must not use default dev credentials
        if "jobwatch:jobwatch_dev" in self.DATABASE_URL:
            errors.append("DATABASE_URL must not use default development credentials (jobwatch_dev) in production.")

        # 4. CORS Origins must not contain wildcard or empty list in production
        if not self.CORS_ORIGINS or "*" in self.CORS_ORIGINS:
            errors.append("CORS_ORIGINS must be explicitly configured and cannot be empty or contain '*' in production.")

        if errors:
            raise RuntimeError(
                f"Production configuration validation failed ({len(errors)} errors):\n - "
                + "\n - ".join(errors)
            )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    return Settings()
