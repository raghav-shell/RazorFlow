import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.config import get_settings
from apps.api.dependencies import close_redis
from apps.api.logging_config import setup_logging
from apps.api.middleware import RequestTracingMiddleware, SecurityHeadersMiddleware
from apps.api.routes.health import router as health_router
from apps.api.routes.v1.api_router import v1_router
from packages.common.context import get_request_id
from packages.persistence.database import close_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan managing database and Redis connection pooling."""
    settings = get_settings()
    setup_logging(log_level=settings.LOG_LEVEL, environment=settings.ENVIRONMENT)
    settings.validate_production_safety()

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
    if settings.ENVIRONMENT == "development" and not settings.CORS_ALLOWED_ORIGINS:
        allowed_origins = ["*"]
    else:
        allowed_origins = [
            origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()
        ]
        if not allowed_origins:
            allowed_origins = ["http://localhost:3000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # OWASP Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # Request ID and tracing middleware
    app.add_middleware(RequestTracingMiddleware)

    # Global unhandled exception handler to prevent internal trace / secret leaks
    @app.exception_handler(Exception)
    async def global_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = get_request_id() or "unknown"
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path} (request_id={req_id}): {exc}",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred while processing your request.",
                "request_id": req_id,
                "status_code": 500,
            },
        )

    # Include health and v1 routers
    app.include_router(health_router)
    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
