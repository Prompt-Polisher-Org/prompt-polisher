import redis.asyncio as redis
from typing import AsyncIterator

from app.core.config import settings

# Create a connection pool
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL, 
    decode_responses=True
)

async def get_redis() -> AsyncIterator[redis.Redis]:
    """Dependency to get Redis client."""
    client = redis.Redis.from_pool(redis_pool)
    try:
        yield client
    finally:
        await client.close()
