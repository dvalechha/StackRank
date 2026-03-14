"""Health check endpoint."""

from fastapi import APIRouter

from stackrank.api.models.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return API status. Used by Railway for health checks."""
    return HealthResponse(status="ok", version="0.1.0")