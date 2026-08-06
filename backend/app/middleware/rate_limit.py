"""
middleware/rate_limit.py — Redis-based rate limiting middleware.

Task: Week 3-4 / User & Preferences API (task.md line 164)
  [x] Implement Redis rate limiting middleware (50 req/min/user)

Strategy:
  - For authenticated requests: rate-limit by user ID (from JWT)
  - For unauthenticated requests: rate-limit by IP address
  - Uses a sliding window counter stored in Redis with a 60-second TTL
  - Adds standard rate-limit headers to every response
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import JWTError, jwt

from app.core.config import settings

RATE_LIMIT = 50          # max requests
WINDOW_SECONDS = 60      # per this many seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter using Redis.
    Falls back gracefully if Redis is unavailable (logs warning, allows request).
    """

    async def dispatch(self, request: Request, call_next):
        # ── Identify the requester ────────────────────────────────────────────
        client_key = self._get_client_key(request)

        # ── Try to check Redis ────────────────────────────────────────────────
        try:
            redis = request.app.state.redis
            if redis is not None:
                current, is_limited = await self._check_rate_limit(redis, client_key)
                if is_limited:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": "Too many requests. Limit: 50 per minute.",
                            "retry_after": WINDOW_SECONDS,
                        },
                        headers={
                            "Retry-After": str(WINDOW_SECONDS),
                            "X-RateLimit-Limit": str(RATE_LIMIT),
                            "X-RateLimit-Remaining": "0",
                        },
                    )

                response: Response = await call_next(request)
                remaining = max(0, RATE_LIMIT - current)
                response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
                return response

        except Exception:
            # Redis unavailable — fail open (allow request, don't crash the app)
            pass

        return await call_next(request)

    def _get_client_key(self, request: Request) -> str:
        """
        Try to extract user ID from the Authorization JWT so authenticated users
        are rate-limited by account (not IP, which can be shared).
        Falls back to IP address for unauthenticated requests.
        """
        auth: str | None = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth.removeprefix("Bearer ").strip()
            try:
                payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
                )
                user_id = payload.get("sub")
                if user_id:
                    return f"rate_limit:user:{user_id}"
            except JWTError:
                pass

        # Fall back to client IP
        ip = request.client.host if request.client else "unknown"
        return f"rate_limit:ip:{ip}"

    async def _check_rate_limit(self, redis, key: str) -> tuple[int, bool]:
        """
        Increment the request counter in Redis. Returns (current_count, is_over_limit).
        Uses INCR + EXPIRE so the window resets automatically every 60 seconds.
        """
        count = await redis.incr(key)
        if count == 1:
            # First request in this window — set the expiry
            await redis.expire(key, WINDOW_SECONDS)
        return count, count > RATE_LIMIT
