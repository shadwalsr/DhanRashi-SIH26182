import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import (
    VaspTraceException,
    generic_http_exception_handler,
    vasp_trace_exception_handler,
)
from app.core.logging import setup_logging
from app.routers import (
    audit_router,
    auth_router,
    cases_router,
    health_router,
    investigations_router,
    reports_router,
    sahyog_router,
    vasps_router,
)

logger = logging.getLogger("vasp_trace")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting %s in %s mode (DEMO_MODE=%s)", settings.PROJECT_NAME, settings.ENVIRONMENT, settings.DEMO_MODE)
    yield
    # Shutdown
    logger.info("Shutting down %s", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Automated Attribution of Unknown Cryptocurrency Wallets to Nearest VASPs",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(VaspTraceException, vasp_trace_exception_handler)
app.add_exception_handler(HTTPException, generic_http_exception_handler)

# Root level health checks (e.g. /health/live, /health/ready)
app.include_router(health_router)
app.include_router(health_router, prefix=settings.API_V1_PREFIX)

# Versioned API routes
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(cases_router, prefix=settings.API_V1_PREFIX)
app.include_router(investigations_router, prefix=settings.API_V1_PREFIX)
app.include_router(vasps_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)
app.include_router(sahyog_router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": "0.1.0",
        "demo_mode": settings.DEMO_MODE,
        "docs_url": "/docs",
    }
