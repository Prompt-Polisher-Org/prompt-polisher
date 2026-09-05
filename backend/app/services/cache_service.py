"""
cache_service.py — Redis-based response caching for AI inference.

Task: Week 11-12 / Performance Optimization (task.md lines 613-617)
  [x] Cache generated prompts with hash of input as key
  [x] TTL: 1 hour for cached results
  [x] Cache invalidation on preference change
  [x] Track cache hit rate

Caching strategy:
  - Key: SHA-256 hash of (prompt + temperature + max_tokens)
  - Value: JSON-serialized AI response
  - TTL: 3600 seconds (1 hour)
  - Metrics: hit_count and miss_count stored in Redis for monitoring
"""

import hashlib
import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Cache Configuration ───────────────────────────────────────────────────────

CACHE_TTL_SECONDS = 3600  # 1 hour
CACHE_KEY_PREFIX = "pp:inference:"
CACHE_METRICS_KEY = "pp:cache_metrics"


class CacheService:
    """
    Redis-based caching layer for AI inference responses.

    Sits between the API endpoint and the AI client to prevent
    redundant model calls for identical prompts.
    """

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Establish Redis connection for caching."""
        try:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
            await self._redis.ping()
            logger.info("✅ Cache service connected to Redis")
        except Exception as e:
            logger.warning(f"⚠️  Cache service unavailable ({e}) — caching disabled")
            self._redis = None

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    @property
    def is_available(self) -> bool:
        return self._redis is not None

    # ── Key Generation ─────────────────────────────────────────────────────

    @staticmethod
    def _make_cache_key(
        prompt: str,
        temperature: float = 0.7,
        max_new_tokens: int = 512,
    ) -> str:
        """
        Generate a deterministic cache key from the inference parameters.

        Uses SHA-256 to keep keys a fixed length and avoid special characters.
        """
        raw = f"{prompt}|temp={temperature}|tokens={max_new_tokens}"
        hash_digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return f"{CACHE_KEY_PREFIX}{hash_digest}"

    # ── Core Operations ────────────────────────────────────────────────────

    async def get_cached_response(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_new_tokens: int = 512,
    ) -> Optional[dict]:
        """
        Look up a cached inference response.

        Returns:
            The cached response dict if found, or None on cache miss.
        """
        if not self.is_available:
            return None

        key = self._make_cache_key(prompt, temperature, max_new_tokens)

        try:
            cached = await self._redis.get(key)

            if cached is not None:
                await self._increment_metric("hits")
                logger.debug(f"Cache HIT for key {key[:20]}...")
                return json.loads(cached)
            else:
                await self._increment_metric("misses")
                logger.debug(f"Cache MISS for key {key[:20]}...")
                return None

        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    async def set_cached_response(
        self,
        prompt: str,
        response: dict,
        temperature: float = 0.7,
        max_new_tokens: int = 512,
        ttl: int = CACHE_TTL_SECONDS,
    ) -> bool:
        """
        Store an inference response in cache.

        Returns:
            True if successfully cached, False otherwise.
        """
        if not self.is_available:
            return False

        key = self._make_cache_key(prompt, temperature, max_new_tokens)

        try:
            serialized = json.dumps(response, ensure_ascii=False)
            await self._redis.setex(key, ttl, serialized)
            logger.debug(f"Cached response for key {key[:20]}... (TTL={ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
            return False

    # ── Cache Invalidation ─────────────────────────────────────────────────

    async def invalidate_for_prompt(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_new_tokens: int = 512,
    ) -> bool:
        """Invalidate the cache for a specific prompt."""
        if not self.is_available:
            return False

        key = self._make_cache_key(prompt, temperature, max_new_tokens)
        try:
            deleted = await self._redis.delete(key)
            return deleted > 0
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")
            return False

    async def invalidate_all(self) -> int:
        """
        Invalidate ALL cached inference responses.

        Called when user preferences change (e.g., different model version)
        to ensure fresh responses.

        Returns the number of keys deleted.
        """
        if not self.is_available:
            return 0

        try:
            cursor = 0
            deleted_count = 0
            while True:
                cursor, keys = await self._redis.scan(
                    cursor=cursor,
                    match=f"{CACHE_KEY_PREFIX}*",
                    count=100,
                )
                if keys:
                    deleted_count += await self._redis.delete(*keys)
                if cursor == 0:
                    break

            logger.info(f"Invalidated {deleted_count} cached responses")
            return deleted_count
        except Exception as e:
            logger.warning(f"Cache bulk invalidation error: {e}")
            return 0

    # ── Metrics ────────────────────────────────────────────────────────────

    async def _increment_metric(self, field: str):
        """Increment a cache metric counter (hits or misses)."""
        try:
            await self._redis.hincrby(CACHE_METRICS_KEY, field, 1)
        except Exception:
            pass  # Metrics are best-effort

    async def get_cache_stats(self) -> dict:
        """
        Get cache hit/miss statistics.

        Returns:
            {"hits": int, "misses": int, "hit_rate": float}
        """
        if not self.is_available:
            return {"hits": 0, "misses": 0, "hit_rate": 0.0, "status": "unavailable"}

        try:
            stats = await self._redis.hgetall(CACHE_METRICS_KEY)
            hits = int(stats.get("hits", 0))
            misses = int(stats.get("misses", 0))
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0.0

            return {
                "hits": hits,
                "misses": misses,
                "total": total,
                "hit_rate": round(hit_rate, 2),
                "status": "active",
            }
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {"hits": 0, "misses": 0, "hit_rate": 0.0, "status": "error"}


# ── Singleton instance ─────────────────────────────────────────────────────────
cache_service = CacheService()
