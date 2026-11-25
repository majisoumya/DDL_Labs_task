"""Database Session Lifecycle and Initialization."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base
from app.database.connection import engine as default_engine
# Import models to ensure they are registered with Base.metadata
import app.database.models  # noqa: F401

SessionLocal = sessionmaker(
    bind=default_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped database session.

    Ensures the session is cleanly closed upon request completion or error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_context(custom_sessionmaker: Optional[sessionmaker] = None) -> Generator[Session, None, None]:
    """Context manager for standalone scripts, background workers, and tasks."""
    maker = custom_sessionmaker or SessionLocal
    session: Session = maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(engine_instance: Optional[Engine] = None) -> None:
    """Initializes the database schema by creating all defined tables."""
    target_engine = engine_instance or default_engine
    Base.metadata.create_all(bind=target_engine)


def drop_db(engine_instance: Optional[Engine] = None) -> None:
    """Drops all tables registered in Base.metadata (used for testing resets)."""
    target_engine = engine_instance or default_engine
    Base.metadata.drop_all(bind=target_engine)
