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
