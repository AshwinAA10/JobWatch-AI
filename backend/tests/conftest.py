"""Pytest configuration and fixtures for backend tests."""

import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models import Base

settings = get_settings()


@pytest.fixture(scope="session")
def test_engine() -> Engine:
    """Create a persistent test database engine for the test suite."""
    test_db_url = settings.TEST_DATABASE_URL
    is_postgres_reachable = False

    # Check if a dedicated or standard PostgreSQL DB is reachable
    target_url = test_db_url or settings.DATABASE_URL
    if target_url and target_url.startswith("postgresql"):
        try:
            probe_engine = create_engine(target_url, pool_pre_ping=True)
            with probe_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            is_postgres_reachable = True
            engine = probe_engine
        except Exception:
            is_postgres_reachable = False

    if not is_postgres_reachable:
        # Fallback to an in-memory SQLite database with foreign keys enabled
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Create all schema tables
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Provide a transactional database session for each test.
    
    Rolls back any changes at the end of each test for absolute isolation.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    session = session_factory()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a TestClient with database session dependency overridden."""
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
