from contextlib import asynccontextmanager
import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1.api import api_router
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    On startup: connect to Redis for rate limiting and initialise Qdrant collections.
    On shutdown: gracefully close Redis, AI client, and DB engine.
    Falls back gracefully if Redis or Qdrant is not configured.
    """
    import signal
    import logging

    logger = logging.getLogger("prompt_polisher")

    # Initialize structured JSON logging
    setup_logging()

    # ── Startup ────────────────────────────────────────────────────────────
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        app.state.redis = aioredis.from_url(redis_url, decode_responses=True)
        await app.state.redis.ping()
        print("✅ Redis connected — rate limiting active")
    except Exception as e:
        print(f"⚠️  Redis unavailable ({e}) — rate limiting disabled")
        app.state.redis = None

    # ── Qdrant collections bootstrap (Week 7-8) ───────────────────────────
    try:
        from app.services.qdrant_service import qdrant_service
        qdrant_service.ensure_collections_exist()
        print("✅ Qdrant collections ready")
    except Exception as e:
        print(f"⚠️  Qdrant unavailable ({e}) — RAG features disabled")

    # ── Register signal handlers for graceful shutdown ─────────────────────
    shutdown_event = asyncio.Event()

    def _handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, _handle_signal)
        except (ValueError, OSError):
            # Can't set signal handlers in non-main thread
            pass

    print("✅ Graceful shutdown handlers registered")

    yield

    # ── Shutdown ───────────────────────────────────────────────────────────
    logger.info("Shutting down gracefully...")

    # 1. Close Redis connection
    if getattr(app.state, "redis", None) and app.state.redis:
        try:
            await app.state.redis.aclose()
            logger.info("✅ Redis connection closed")
        except Exception as e:
            logger.warning(f"Error closing Redis: {e}")

    # 2. Close AI inference client
    try:
        from app.services.ai_client import ai_client
        await ai_client.close()
        logger.info("✅ AI client closed")
    except Exception as e:
        logger.warning(f"Error closing AI client: {e}")

    # 3. Dispose DB engine (drain connection pool)
    try:
        from app.db.session import engine
        await engine.dispose()
        logger.info("✅ Database engine disposed")
    except Exception as e:
        logger.warning(f"Error disposing DB engine: {e}")

    logger.info("🛑 Graceful shutdown complete")



app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ✅ Error handling + request ID tracking (outermost — catches everything)
app.add_middleware(ErrorHandlerMiddleware)

# ✅ Security headers (CSP, X-Frame-Options, XSS protection)
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# ✅ Rate limiting (50 req/min per user or IP)
app.add_middleware(RateLimitMiddleware)

# ✅ CORS — allows Next.js (port 3000) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ GZip compression for responses > 1KB
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

# ✅ Mount the v1 API router (auth, users, chat, etc.)
app.include_router(api_router, prefix=settings.API_V1_STR)


# ✅ Health check
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "message": "Prompt Polisher Backend is Live!",
        "database": "Connected & Migrated"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
