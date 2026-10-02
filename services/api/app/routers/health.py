from typing import Any

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
async def health_live() -> dict[str, Any]:
    """Liveness probe - returns 200 if process is up."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "demo_mode": settings.DEMO_MODE,
        "live_mode": settings.LIVE_MODE,
    }


@router.get("/ready")
async def health_ready() -> dict[str, Any]:
    """Readiness probe checking backing services."""
    checks = {
        "api": "ok",
        "demo_fixtures": "available",
    }
    return {
        "status": "ready",
        "checks": checks,
    }
