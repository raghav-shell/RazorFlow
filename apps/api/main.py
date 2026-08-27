"""FastAPI main application entrypoint and lifespan coordinator."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.config import get_settings
from apps.api.dependencies import close_redis
from apps.api.logging_config import setup_logging
from apps.api.middleware import RequestTracingMiddleware
from apps.api.routes.health import router as health_router
from apps.api.routes.v1.api_router import v1_router
from packages.persistence.database import close_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing database and Redis connection pooling."""
    settings = get_settings()
    setup_logging(log_level=settings.LOG_LEVEL, environment=settings.ENVIRONMENT)

    yield

    # Gracefully dispose of connection pools on shutdown
    await close_engine()
    await close_redis()


def create_app() -> FastAPI:
    """Factory function for FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="Institutional-Grade Revenue Recovery Orchestration Platform for Razorpay.",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG or settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.DEBUG or settings.ENVIRONMENT == "development" else None,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.ENVIRONMENT == "development" else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and tracing middleware
    app.add_middleware(RequestTracingMiddleware)

    # Include health and v1 routers
    app.include_router(health_router)
    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
