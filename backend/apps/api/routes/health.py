"""Health and readiness probe endpoints."""

import logging
from typing import Any, Dict

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import Settings, get_settings
from apps.api.dependencies import get_db_session, get_redis
from packages.persistence.database import check_database_health

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health & Probes"])


@router.get("/healthz", summary="Liveness Probe")
async def healthz() -> Dict[str, Any]:
    """Basic liveness probe indicating process is running."""
    return {"status": "ok", "service": "razorflow-api"}


@router.get("/livez", summary="Liveness Probe Alias")
async def livez() -> Dict[str, Any]:
    """Liveness probe alias for Kubernetes/container healthchecks."""
    return {"status": "ok", "service": "razorflow-api"}


@router.get("/readyz", summary="Readiness Probe")
async def readyz(
    db: AsyncSession = Depends(get_db_session),
    redis: aioredis.Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """
    Readiness probe verifying PostgreSQL and Redis connectivity.
    Returns HTTP 200 if all services are healthy, 503 Service Unavailable otherwise.
    """
    checks: Dict[str, str] = {}
    is_ready = True

    # 1. Check Database connectivity
    db_ok = await check_database_health(db)
    checks["database"] = "healthy" if db_ok else "unhealthy"
    if not db_ok:
        is_ready = False

    # 2. Check Redis connectivity
    try:
        redis_ok = await redis.ping()
        checks["redis"] = "healthy" if redis_ok else "unhealthy"
        if not redis_ok:
            is_ready = False
    except Exception as e:
        logger.error(f"Redis healthcheck failed: {e}")
        checks["redis"] = "unhealthy"
        is_ready = False

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    response_payload = {
        "status": "ready" if is_ready else "degraded",
        "environment": settings.ENVIRONMENT,
        "checks": checks,
    }
    return JSONResponse(status_code=status_code, content=response_payload)
