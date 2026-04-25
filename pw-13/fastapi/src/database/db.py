"""
Database session management for async SQLAlchemy.
Provides a session manager and FastAPI dependency (`get_db`)
with commit/rollback behavior per request.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import SQLAlchemyError

from src.config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    """Creates async engine/session factory and manages session lifecycle."""

    def __init__(self, db_url: str):
        self._engine: AsyncEngine | None = create_async_engine(db_url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @asynccontextmanager
    async def get_session(self):
        if self._session_maker is None:
            raise Exception("Session is not initialized")
        session = self._session_maker()
        try:
            yield session
            # await session.commit()
        except SQLAlchemyError:
            await session.rollback()
            logger.exception("Database transaction failed")
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped async DB session."""
    async with sessionmanager.get_session() as session:
        yield session
