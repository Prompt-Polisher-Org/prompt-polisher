import time
from fastapi import HTTPException
from redis.asyncio import Redis

async def check_rate_limit(redis_client: Redis, user_id: str, limit: int = 20, period_seconds: int = 3600):
    """
    Simple fixed window rate limiter using Redis.
    Limits a user to `limit` requests per `period_seconds` (default: 20 per hour).
    """
    current_time = int(time.time())
    window = current_time // period_seconds
    
    key = f"rate_limit:{user_id}:{window}"
    
    # Increment the counter for this window
    requests = await redis_client.incr(key)
    
    # Set expiration on the first request in the window
    if requests == 1:
        await redis_client.expire(key, period_seconds)
        
    if requests > limit:
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded. Maximum {limit} optimizations per {period_seconds//60} minutes."
        )
