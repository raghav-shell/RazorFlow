"""FastAPI Dependency Injection providers for database sessions and Redis clients."""

from typing import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import Settings, get_settings
from packages.persistence.database import get_sessionmaker

_redis_pool: aioredis.Redis | None = None


async def get_db_session(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[AsyncSession, None]:
    """Yields an async database session within a transaction context."""
    session_factory = get_sessionmaker(settings.DATABASE_URL)
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_redis(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[aioredis.Redis, None]:
    """Yields singleton async Redis client pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    yield _redis_pool


async def close_redis() -> None:
    """Closes Redis client connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None
