"""
CHC Pro AI — Backend Entry Point
Run: uvicorn main:app --reload --port 8000
"""
import logging, uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.routes.auth         import router as auth_router
from app.routes.registration import router as reg_router
from config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log      = logging.getLogger(__name__)
settings = get_settings()
limiter  = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"CHC Pro AI starting [{settings.APP_ENV}]")

    # Redis warm-up
    try:
        from app.services.otp_service import get_redis
        r = await get_redis()
        await r.ping()
        log.info("Redis: OK")
    except Exception as e:
        log.warning(f"Redis: {e}")

    yield
    log.info("CHC Pro AI shutting down")


app = FastAPI(
    title="Carolin Code Pro AI",
    description="HIPAA-compliant AI medical coding — Layer 1: Auth & Registration",
    version="1.0.0",
    docs_url  ="/docs"  if not settings.is_production else None,
    redoc_url ="/redoc" if not settings.is_production else None,
    lifespan  =lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# ── Trusted hosts (production) ─────────────────────────────────────────────
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["carolincodepro.ai", "*.carolincodepro.ai", "localhost"],
    )

# ── Security headers ───────────────────────────────────────────────────────
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    h = response.headers
    h["X-Content-Type-Options"]  = "nosniff"
    h["X-Frame-Options"]         = "DENY"
    h["X-XSS-Protection"]        = "1; mode=block"
    h["Referrer-Policy"]         = "strict-origin-when-cross-origin"
    h["Permissions-Policy"]      = "geolocation=(), microphone=(), camera=()"
    if settings.is_production:
        h["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response

# ── Request ID ────────────────────────────────────────────────────────────
@app.middleware("http")
async def request_id(request: Request, call_next):
    rid      = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response

# ── Validation error handler ──────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    errors = []
    for e in exc.errors():
        field = " → ".join(str(l) for l in e["loc"] if l != "body")
        errors.append({"field": field, "message": e["msg"]})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors},
    )

# ── Global error handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_error(request: Request, exc: Exception):
    log.error(f"Unhandled error [{request.url}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again or contact support."},
    )

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(reg_router)

# ── Health ─────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "service": "chc-pro-ai-auth"}


@app.get("/health/deep", tags=["System"])
async def deep_health():
    checks = {}
    try:
        from app.services.otp_service import get_redis
        r = await get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    try:
        import boto3
        boto3.client("cognito-idp", region_name=settings.AWS_REGION)
        checks["cognito"] = "ok"
    except Exception as e:
        checks["cognito"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "ok" if all_ok else "degraded", "checks": checks},
    )


@app.get("/", tags=["System"])
async def root():
    return {
        "product": "Carolin Code Pro AI",
        "layer":   "1 — Auth & Registration",
        "version": "1.0.0",
        "docs":    "/docs" if not settings.is_production else "disabled",
    }
