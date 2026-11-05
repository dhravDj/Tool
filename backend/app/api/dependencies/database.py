"""FastAPI database session dependency injection."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an active asynchronous database session."""
    async for session in get_db_session():
        yield session
