"""v1 API Router grouping all version 1 endpoints."""

from fastapi import APIRouter

from apps.api.routes.v1.cases import router as cases_router
from apps.api.routes.v1.webhooks import router as webhooks_router

v1_router = APIRouter()

v1_router.include_router(webhooks_router)
v1_router.include_router(cases_router)


@v1_router.get("/version", tags=["System"])
async def get_api_version() -> dict:
    """Returns the current API platform version and status."""
    return {
        "api_version": "v1",
        "platform": "RazorFlow Revenue Recovery Orchestrator",
        "phase": "Phase 1 - Webhook Ingestion & Case Lifecycle",
        "status": "operational",
    }
