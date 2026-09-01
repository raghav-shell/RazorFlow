"""Async SQLAlchemy engine, session maker, and healthcheck utilities."""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def normalize_database_url(url: str) -> str:
    """Normalizes database URLs to asyncpg format."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def get_engine(database_url: str) -> AsyncEngine:
    """Returns singleton AsyncEngine with connection pooling and Supabase/PgBouncer compatibility."""
    global _engine
    if _engine is None:
        normalized_url = normalize_database_url(database_url)
        is_sqlite = normalized_url.startswith("sqlite")
        pool_kwargs: dict = {}
        connect_args: dict = {}

        if not is_sqlite:
            pool_kwargs = {
                "pool_size": 20,
                "max_overflow": 10,
                "pool_recycle": 3600,
                "pool_pre_ping": True,
            }
            # statement_cache_size=0 enables zero-conflict compatibility with Supabase transaction poolers / PgBouncer
            if "asyncpg" in normalized_url:
                connect_args["statement_cache_size"] = 0

        _engine = create_async_engine(
            normalized_url,
            echo=False,
            future=True,
            connect_args=connect_args,
            **pool_kwargs,
        )
    return _engine


def get_sessionmaker(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Returns singleton async_sessionmaker bound to the engine."""
    global _sessionmaker
    if _sessionmaker is None:
        engine = get_engine(database_url)
        _sessionmaker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _sessionmaker


async def check_database_health(session: AsyncSession) -> bool:
    """Executes a lightweight query (SELECT 1) to verify database connectivity."""
    try:
        result = await session.execute(text("SELECT 1"))
        return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database healthcheck failed: {e}")
        return False


async def close_engine() -> None:
    """Closes the async database engine pool on application shutdown."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
        logger.info("Database engine connection pool closed.")
