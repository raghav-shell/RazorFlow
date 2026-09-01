"""Integration tests for FastAPI health and readiness endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_healthz_liveness_endpoint(async_client: AsyncClient):
    response = await async_client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "razorflow-api"
    assert "X-Request-ID" in response.headers
    assert "X-Response-Time-MS" in response.headers


@pytest.mark.asyncio
async def test_livez_liveness_alias(async_client: AsyncClient):
    response = await async_client.get("/livez")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_readyz_readiness_healthy(async_client: AsyncClient):
    response = await async_client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] == "healthy"
    assert data["checks"]["redis"] == "healthy"


@pytest.mark.asyncio
async def test_api_v1_version_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/version")
    assert response.status_code == 200
    data = response.json()
    assert data["api_version"] == "v1"
    assert data["status"] == "operational"
