"""Tests for application and database configuration."""

from app.core.config import Settings, get_settings


def test_database_settings_defaults():
    """Verify that default database configuration settings are loaded properly."""
    settings = get_settings()

    assert settings.DATABASE_URL is not None
    assert "postgresql" in settings.DATABASE_URL or "sqlite" in settings.DATABASE_URL
    assert settings.DB_POOL_SIZE >= 1
    assert settings.DB_MAX_OVERFLOW >= 0
    assert settings.DB_POOL_TIMEOUT > 0
    assert settings.DB_POOL_RECYCLE > 0


def test_settings_custom_values():
    """Verify that settings can be instantiated with custom values."""
    custom = Settings(
        DATABASE_URL="postgresql+psycopg://custom_user:custom_pass@localhost:5432/custom_db",
        DB_POOL_SIZE=10,
        DB_MAX_OVERFLOW=20,
        DB_ECHO=True,
    )
    assert custom.DATABASE_URL == "postgresql+psycopg://custom_user:custom_pass@localhost:5432/custom_db"
    assert custom.DB_POOL_SIZE == 10
    assert custom.DB_MAX_OVERFLOW == 20
    assert custom.DB_ECHO is True


def test_monitoring_settings_defaults():
    """Verify default monitoring configuration values."""
    settings = get_settings()

    assert settings.MONITORING_ENABLED is False
    assert settings.MONITORING_INTERVAL_SECONDS == 900
    assert settings.MONITORING_MAX_CONCURRENCY == 5
    assert settings.MONITORING_MAX_RETRIES == 2
    assert settings.MONITORING_RETRY_BACKOFF_SECONDS == 5.0
    assert settings.MONITORING_SOURCE_TIMEOUT_SECONDS == 120.0


def test_monitoring_settings_validation():
    """Verify that invalid monitoring parameters raise validation errors."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(MONITORING_INTERVAL_SECONDS=0)

    with pytest.raises(ValidationError):
        Settings(MONITORING_MAX_CONCURRENCY=0)

    with pytest.raises(ValidationError):
        Settings(MONITORING_MAX_RETRIES=-1)

    with pytest.raises(ValidationError):
        Settings(MONITORING_RETRY_BACKOFF_SECONDS=-1.0)

    with pytest.raises(ValidationError):
        Settings(MONITORING_SOURCE_TIMEOUT_SECONDS=0)


def test_dedup_settings_defaults():
    """Verify default deduplication configuration values."""
    settings = get_settings()

    assert settings.DEDUP_ENABLED is True
    assert settings.DEDUP_HIGH_THRESHOLD == 0.90
    assert settings.DEDUP_MEDIUM_THRESHOLD == 0.75
    assert settings.DEDUP_MAX_CANDIDATES == 100
    assert settings.DEDUP_LOOKBACK_DAYS == 90


def test_dedup_settings_validation():
    """Verify that invalid deduplication parameters raise validation errors."""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(DEDUP_HIGH_THRESHOLD=1.5)

    with pytest.raises(ValidationError):
        Settings(DEDUP_HIGH_THRESHOLD=-0.1)

    with pytest.raises(ValidationError):
        Settings(DEDUP_MEDIUM_THRESHOLD=-0.1)

    with pytest.raises(ValidationError):
        Settings(DEDUP_MAX_CANDIDATES=0)

    with pytest.raises(ValidationError):
        Settings(DEDUP_LOOKBACK_DAYS=0)


