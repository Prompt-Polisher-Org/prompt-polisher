from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.api import api_router
from app.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    On startup: try to connect to Redis for rate limiting.
    On shutdown: close the Redis connection.
    Falls back gracefully if Redis is not configured.
    """
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        app.state.redis = aioredis.from_url(redis_url, decode_responses=True)
        await app.state.redis.ping()
        print("✅ Redis connected — rate limiting active")
    except Exception as e:
        print(f"⚠️  Redis unavailable ({e}) — rate limiting disabled")
        app.state.redis = None
    yield
    if app.state.redis:
        await app.state.redis.aclose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

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
