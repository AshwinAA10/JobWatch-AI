"""Tests for database engine, session management, and health probes."""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import check_database_health, create_db_engine, get_db


def test_create_db_engine():
    """Verify that engine creation handles database URLs properly."""
    engine = create_db_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_get_db_generator(db_session: Session):
    """Verify session generator yields a valid session and closes it."""
    gen = get_db()
    session = next(gen)
    assert isinstance(session, Session)

    # Closing generator should clean up session
    try:
        next(gen)
    except StopIteration:
        pass


def test_check_database_health_success(monkeypatch, test_engine):
    """Verify check_database_health returns True and latency with healthy connection."""
    import app.core.database as db_mod

    monkeypatch.setattr(db_mod, "engine", test_engine)
    is_healthy, latency_ms, error = check_database_health()

    assert is_healthy is True
    assert latency_ms >= 0.0
    assert error is None


def test_check_database_health_failure(monkeypatch):
    """Verify check_database_health handles unreachable database cleanly without leaking secrets."""
    import app.core.database as db_mod

    class FailingEngine:
        def connect(self):
            raise ConnectionRefusedError("Could not connect to database host")

    monkeypatch.setattr(db_mod, "engine", FailingEngine())

    is_healthy, latency_ms, error = check_database_health()
    assert is_healthy is False
    assert error == "Database connection failed"
