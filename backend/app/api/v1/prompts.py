import json
import hashlib
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.db.session import get_db
from app.core.redis import get_redis
from app.core.rate_limit import check_rate_limit
from app.dependencies import get_current_user
from app.models.user import User
from app.models.prompt_history import PromptHistory
from app.services.ai_client import ai_client
from pydantic import BaseModel, Field

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str = Field(..., description="The original prompt to optimize")
    max_new_tokens: int = Field(512, ge=1, le=2048)
    temperature: float = Field(0.7, ge=0.0, le=2.0)

class PromptResponse(BaseModel):
    optimized_prompt: str
    cached: bool = False
    latency_ms: float = 0.0

def _get_cache_key(prompt: str, max_tokens: int, temp: float) -> str:
    """Generate a stable cache key based on inputs."""
    data = f"{prompt}:{max_tokens}:{temp}".encode("utf-8")
    return "prompt_cache:" + hashlib.sha256(data).hexdigest()

@router.post("/optimize", response_model=PromptResponse)
async def optimize_prompt(
    request: PromptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    """
    Synchronous prompt optimization.
    Applies rate limiting, checks Redis cache, calls AI server, and logs history.
    """
    # 1. Check Rate Limit (20 per hour)
    await check_rate_limit(redis_client, str(current_user.id), limit=20, period_seconds=3600)
    
    # 2. Check Cache
    cache_key = _get_cache_key(request.prompt, request.max_new_tokens, request.temperature)
    cached_result = await redis_client.get(cache_key)
    
    if cached_result:
        # Save cache hit to history (fast)
        history = PromptHistory(
            user_id=current_user.id,
            original_prompt=request.prompt,
            optimized_prompt=cached_result,
            latency_ms=0.0,
            tokens_generated=0
        )
        db.add(history)
        await db.commit()
        return PromptResponse(optimized_prompt=cached_result, cached=True)

    # 3. Call AI Inference Server
    try:
        ai_response = await ai_client.generate_sync(
            prompt=request.prompt,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail="AI Inference server is currently unavailable")

    optimized = ai_response["generated_text"]
    latency = ai_response["latency_ms"]
    tokens = ai_response["token_count"]

    # 4. Save to Cache (expire in 24 hours)
    await redis_client.setex(cache_key, 86400, optimized)

    # 5. Log History to Postgres
    history = PromptHistory(
        user_id=current_user.id,
        original_prompt=request.prompt,
        optimized_prompt=optimized,
        latency_ms=latency,
        tokens_generated=tokens
    )
    db.add(history)
    await db.commit()

    return PromptResponse(
        optimized_prompt=optimized,
        cached=False,
        latency_ms=latency
    )

@router.post("/optimize/stream")
async def optimize_prompt_stream(
    request: PromptRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    """
    SSE stream for prompt optimization. 
    Yields tokens directly from the inference server.
    """
    # 1. Check Rate Limit
    await check_rate_limit(redis_client, str(current_user.id), limit=20, period_seconds=3600)
    
    # 2. Cache Check - for stream, if we have cache, we just yield it entirely at once 
    # (or simulate stream if desired). We'll yield in small chunks to simulate streaming.
    cache_key = _get_cache_key(request.prompt, request.max_new_tokens, request.temperature)
    cached_result = await redis_client.get(cache_key)
    
    if cached_result:
        async def cached_stream():
            words = cached_result.split(" ")
            for word in words:
                if await req.is_disconnected():
                    break
                import asyncio
                await asyncio.sleep(0.01) # Simulate token generation speed
                yield f"data: {word} \n\n"
            yield "data: [DONE]\n\n"
            
            # Save history
            history = PromptHistory(
                user_id=current_user.id,
                original_prompt=request.prompt,
                optimized_prompt=cached_result,
                latency_ms=0.0,
                tokens_generated=0
            )
            db.add(history)
            await db.commit()
            
        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    # 3. Stream from AI Server
    async def ai_stream():
        generated_text = ""
        try:
            async for token in ai_client.generate_stream(
                prompt=request.prompt,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature
            ):
                if await req.is_disconnected():
                    break
                generated_text += token
                # Make safe for SSE
                safe_token = token.replace("\n", "\\n")
                yield f"data: {safe_token}\n\n"
            
            yield "data: [DONE]\n\n"
            
            # Once stream is complete, cache and log
            if generated_text:
                await redis_client.setex(cache_key, 86400, generated_text)
                
                history = PromptHistory(
                    user_id=current_user.id,
                    original_prompt=request.prompt,
                    optimized_prompt=generated_text,
                    latency_ms=0.0, # Not tracked in stream currently
                    tokens_generated=len(generated_text) // 4 # rough estimate
                )
                db.add(history)
                await db.commit()

        except Exception as e:
            yield f"data: [ERROR: AI inference failed]\n\n"

    return StreamingResponse(ai_stream(), media_type="text/event-stream")
