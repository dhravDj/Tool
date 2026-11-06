"""Asynchronous database session lifecycle and health verification."""

import time
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.logging import logger

# Construct async SQLAlchemy engine
# Use pool_pre_ping to automatically recover from dropped connections
# Use pool_recycle and pool_timeout to prevent connection pool exhaustion and stale sockets
engine: AsyncEngine = create_async_engine(
    settings.async_database_uri,
    echo=settings.DEBUG and False,  # Keep false by default to prevent leaking data to logs
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_timeout=settings.DB_POOL_TIMEOUT,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connectivity() -> tuple[bool, float, str]:
    """Test database connectivity with SELECT 1 and return (is_healthy, latency_ms, message)."""
    start = time.perf_counter()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start) * 1000
        return True, round(latency, 2), "Database connection active and responsive."
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        logger.warning(f"Database health check failed: {e}")
        return False, round(latency, 2), str(e)
