"""Database Connection and Engine Management for SQLAlchemy 2.x."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

from app.config import settings, PROJECT_ROOT

logger = logging.getLogger("insightiq.database")


def get_engine(db_url: Optional[str] = None, **engine_kwargs: Any) -> Engine:
    """Creates and configures an SQLAlchemy Engine with pooling and query timeouts.

    Supports PostgreSQL connection pooling and statement timeouts in production,
    with adaptive handling for SQLite, and automatic fallback to local SQLite
    when PostgreSQL is unreachable during local host execution.
    """
    url = db_url or settings.DATABASE_URL

    # Detect driver type
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if ":memory:" in url:
            return create_engine(
                url,
                connect_args=connect_args,
                poolclass=StaticPool,
                **engine_kwargs,
            )
        return create_engine(
            url,
            connect_args=connect_args,
            poolclass=NullPool,
            **engine_kwargs,
        )

    # In local development, check if PostgreSQL is reachable. If not, automatically
    # fall back to the pre-seeded SQLite database so developers can run without Docker.
    sqlite_fallback_path = PROJECT_ROOT / "data" / "insightiq.db"
    try:
        quick_test = create_engine(url, connect_args={"connect_timeout": 2}, poolclass=NullPool)
        with quick_test.connect():
            pass
        quick_test.dispose()
    except Exception as exc:
        if sqlite_fallback_path.exists():
            logger.warning(
                "PostgreSQL connection to %s failed (%s). "
                "Automatically falling back to local SQLite database at %s.",
                url, exc, sqlite_fallback_path
            )
            fallback_url = f"sqlite:///{sqlite_fallback_path.as_posix()}"
            return create_engine(
                fallback_url,
                connect_args={"check_same_thread": False},
                poolclass=NullPool,
                **engine_kwargs,
            )
        # If no SQLite database exists, re-raise the connection exception
        raise

    # PostgreSQL / Client Pooling with Timeouts
    connect_args = engine_kwargs.pop("connect_args", {})
    if "connect_timeout" not in connect_args:
        connect_args["connect_timeout"] = settings.DB_CONNECT_TIMEOUT_SECONDS
    if "options" not in connect_args and settings.DB_COMMAND_TIMEOUT_SECONDS > 0:
        connect_args["options"] = f"-c statement_timeout={settings.DB_COMMAND_TIMEOUT_SECONDS * 1000}"

    pool_options: Dict[str, Any] = {
        "poolclass": QueuePool,
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_pre_ping": settings.DB_POOL_PRE_PING,
        "connect_args": connect_args,
    }
    pool_options.update(engine_kwargs)

    return create_engine(url, **pool_options)


# Default engine instance bound to configured DATABASE_URL
engine = get_engine()
