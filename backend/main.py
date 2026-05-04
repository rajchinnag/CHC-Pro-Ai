"""
CHC Pro AI – FastAPI Application Entry Point
Layer 1: Auth & Registration
Layer 2: Upload & Context
"""
import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from app.routes import auth, registration, upload as upload_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"CHC Pro AI starting [{settings.APP_ENV}]")
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        logger.info("Redis: OK")
    except Exception as e:
        logger.warning(f"Redis: Error connecting to {settings.REDIS_URL}. {e}")
    yield
    # Shutdown
    logger.info("CHC Pro AI shutting down")


app = FastAPI(
    title="CHC Pro AI",
    description="HIPAA-compliant AI-assisted medical coding platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(registration.router)
app.include_router(upload_router.router)   # Layer 2


@app.get("/", tags=["System"])
async def root():
    return {"service": "CHC Pro AI", "version": "2.0.0", "status": "operational"}


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok"}


@app.get("/health/deep", tags=["System"])
async def health_deep():
    checks = {}
    try:
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"
    return {"status": "ok" if all(v == "ok" for v in checks.values()) else "degraded", "checks": checks}
