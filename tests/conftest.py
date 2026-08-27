"""Pytest configuration and shared test fixtures."""

import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set testing environment variables before importing app
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from apps.api.dependencies import get_db_session, get_redis
from apps.api.main import create_app
from packages.persistence.base import Base


class MockRedisClient:
    """In-memory mock for async Redis client in unit/integration tests."""

    def __init__(self) -> None:
        self.store: dict = {}
        self.is_connected = True

    async def ping(self) -> bool:
        if not self.is_connected:
            raise ConnectionError("Mock Redis disconnected")
        return True

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.store[key] = value
        return True

    async def delete(self, key: str):
        self.store.pop(key, None)
        return True

    async def aclose(self) -> None:
        self.is_connected = False


@pytest_asyncio.fixture(scope="function")
async def async_db_engine():
    """Creates an isolated in-memory SQLite database engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_db_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yields a database session bound to the test in-memory database."""
    session_factory = async_sessionmaker(
        bind=async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def mock_redis() -> MockRedisClient:
    """Yields a clean mock Redis client."""
    return MockRedisClient()


@pytest_asyncio.fixture(scope="function")
async def async_client(
    async_db_session: AsyncSession, mock_redis: MockRedisClient
) -> AsyncGenerator[AsyncClient, None]:
    """Provides an async HTTP client configured with test dependency overrides."""
    app = create_app()

    async def override_get_db():
        yield async_db_session

    async def override_get_redis():
        yield mock_redis

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
