"""Centralized SQLAlchemy engine, session management, and database connectivity."""

import time
from typing import Generator, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def create_db_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine configured with connection pooling."""
    connect_args = {}
    is_sqlite = database_url.startswith("sqlite")
    if is_sqlite:
        connect_args["check_same_thread"] = False

    pool_kwargs = {
        "pool_pre_ping": True,
        "echo": settings.DB_ECHO,
        "connect_args": connect_args,
    }

    # SQLite memory/file does not support standard QueuePool pool_size/max_overflow
    if not is_sqlite:
        pool_kwargs["pool_size"] = settings.DB_POOL_SIZE
        pool_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
        pool_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT
        pool_kwargs["pool_recycle"] = settings.DB_POOL_RECYCLE

    return create_engine(database_url, **pool_kwargs)


# Centralized application engine and session factory
engine = create_db_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session lifecycle management.
    
    Yields an active database session, automatically rolling back on uncaught
    exceptions and guaranteeing session closure upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_health() -> Tuple[bool, float, Optional[str]]:
    """Perform a lightweight database readiness probe using SELECT 1.
    
    Returns:
        Tuple of (is_healthy, latency_ms, error_message)
    """
    start_time = time.perf_counter()
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return True, round(latency_ms, 2), None
    except Exception as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        # Return generic error summary without exposing credentials or internal paths
        return False, round(latency_ms, 2), "Database connection failed"
