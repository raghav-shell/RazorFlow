"""v1 API Router grouping all version 1 endpoints."""

from fastapi import APIRouter

v1_router = APIRouter()


@v1_router.get("/version", tags=["System"])
async def get_api_version() -> dict:
    """Returns the current API platform version and status."""
    return {
        "api_version": "v1",
        "platform": "RazorFlow Revenue Recovery Orchestrator",
        "phase": "Phase 0 - Foundation",
        "status": "operational",
    }
