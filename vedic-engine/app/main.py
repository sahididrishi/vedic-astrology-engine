import time
import uuid
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Vedic Astrology Engine")
    try:
        app.state.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await app.state.redis.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        app.state.redis = None

    yield

    # Shutdown — finish in-flight requests handled by uvicorn; close connections
    if app.state.redis:
        await app.state.redis.close()
    logger.info("Vedic Astrology Engine stopped")


app = FastAPI(
    title="Vedic Astrology Predictive Engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    """Add request ID and timing to every request."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    request.state.start_time = time.time()

    response = await call_next(request)

    duration_ms = int((time.time() - request.state.start_time) * 1000)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Processing-Time-Ms"] = str(duration_ms)

    logger.info(
        f"{request.method} {request.url.path} {response.status_code} {duration_ms}ms",
        extra={"request_id": request_id, "method": request.method,
               "path": request.url.path, "status": response.status_code,
               "duration_ms": duration_ms},
    )

    return response


@app.get("/api/v1/health")
async def health_check(request: Request):
    redis_ok = False
    if hasattr(request.app.state, "redis") and request.app.state.redis:
        try:
            await request.app.state.redis.ping()
            redis_ok = True
        except Exception:
            pass

    status = "ok" if redis_ok else "degraded"
    status_code = 200 if redis_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "redis": "connected" if redis_ok else "unavailable",
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled error: {exc}", exc_info=True,
                 extra={"request_id": request_id})
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "suggestion": "Please retry. If this persists, contact support.",
            "request_id": request_id,
        },
    )


# Import and include routers after app is created
from app.api.v1 import reading, chart, admin  # noqa: E402

app.include_router(reading.router)
app.include_router(chart.router)
app.include_router(admin.router)
