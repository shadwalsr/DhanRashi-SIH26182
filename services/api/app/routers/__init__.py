from app.routers.audit import router as audit_router
from app.routers.auth import router as auth_router
from app.routers.cases import router as cases_router
from app.routers.health import router as health_router
from app.routers.investigations import router as investigations_router
from app.routers.reports import router as reports_router
from app.routers.sahyog import router as sahyog_router
from app.routers.vasps import router as vasps_router

__all__ = [
    "audit_router",
    "auth_router",
    "cases_router",
    "health_router",
    "investigations_router",
    "reports_router",
    "sahyog_router",
    "vasps_router",
]
