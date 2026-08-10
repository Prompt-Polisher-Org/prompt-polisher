"""
api/v1/prompts.py — Prompt optimisation endpoints with full RAG pipeline.

Task: Week 5-6 / Backend Inference Integration — SSE streaming
Task: Week 7-8 / RAG Integration (task.md lines 406-409)
  [x] Inference endpoint now: retrieve -> augment -> generate
  [x] Pass augmented prompt to model instead of raw prompt
  [x] Log RAG retrieval results for debugging
"""
import json
import hashlib
import logging
from typing import AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from app.db.session import get_db
from app.core.redis import get_redis
from app.core.rate_limit import check_rate_limit
from app.dependencies import get_current_user
from app.models.user import User
from app.models.prompt_history import PromptHistory
from app.models.preference import UserPreference
from app.services.ai_client import ai_client
from app.services.retrieval_service import retrieval_service
from app.rag.augmenter import prompt_augmenter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

class PromptRequest(BaseModel):
    prompt: str = Field(..., description="The original prompt to optimise")
    max_new_tokens: int = Field(512, ge=1, le=2048)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    use_rag: bool = Field(True, description="Whether to apply RAG context augmentation")


class PromptResponse(BaseModel):
    optimized_prompt: str
    cached: bool = False
    latency_ms: float = 0.0
    rag_context_used: bool = False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_cache_key(prompt: str, max_tokens: int, temp: float) -> str:
    """Generate a stable cache key based on inputs."""
    data = f"{prompt}:{max_tokens}:{temp}".encode("utf-8")
    return "prompt_cache:" + hashlib.sha256(data).hexdigest()


async def _get_user_preferences(db: AsyncSession, user_id) -> Optional[dict]:
    """
    Fetch the current user's preferences from Postgres.
    Returns None if no preferences row exists yet.
    """
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()
    if prefs is None:
        return None
    return {
        "tone": prefs.tone,
        "verbosity": prefs.verbosity,
        "target_model": prefs.target_model,
        "domain": prefs.domain,
        "custom_instructions": prefs.custom_instructions,
    }


async def _build_augmented_prompt(
    raw_prompt: str,
    user_id: str,
    user_prefs: Optional[dict],
    use_rag: bool,
) -> tuple[str, bool]:
    """
    Build the full augmented prompt using RAG context.

    Returns:
        (augmented_prompt_string, rag_was_used_bool)
    """
    if not use_rag:
        return raw_prompt, False

    domain = user_prefs.get("domain") if user_prefs else None

    try:
        context = await retrieval_service.retrieve_context_async(
            user_id=user_id,
            query=raw_prompt,
            domain=domain,
        )

        # Log retrieval results for debugging
        logger.info(
            "RAG retrieval complete: prefs=%d, history=%d, patterns=%d",
            len(context.preferences),
            len(context.history),
            len(context.patterns),
        )

        augmented = prompt_augmenter.augment(
            raw_prompt=raw_prompt,
            context=context,
            user_preferences=user_prefs,
        )
        return augmented, True

    except Exception as e:
        # Graceful degradation: if RAG fails, fall back to raw prompt
        logger.warning(f"RAG pipeline failed, falling back to raw prompt: {e}")
        return raw_prompt, False


# ── REST endpoint (sync) ──────────────────────────────────────────────────────

@router.post("/optimize", response_model=PromptResponse)
async def optimize_prompt(
    request: PromptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
):
    """
    Synchronous prompt optimisation.
    Flow: rate limit → cache check → RAG retrieve → augment → AI generate → cache + log.
    """
    # 1. Rate limit (20 optimisations/hour/user)
    await check_rate_limit(redis_client, str(current_user.id), limit=20, period_seconds=3600)

    # 2. Check cache (use raw prompt as cache key — RAG personalisation is intentionally not cached)
    cache_key = _get_cache_key(request.prompt, request.max_new_tokens, request.temperature)
    cached_result = await redis_client.get(cache_key)

    if cached_result:
        logger.info("Cache hit for prompt: %s", request.prompt[:40])
        history = PromptHistory(
            user_id=current_user.id,
            original_prompt=request.prompt,
            optimized_prompt=cached_result,
            latency_ms=0.0,
            tokens_generated=0,
        )
        db.add(history)
        await db.commit()
        return PromptResponse(optimized_prompt=cached_result, cached=True)

    # 3. Fetch user preferences for RAG context
    user_prefs = await _get_user_preferences(db, current_user.id)

    # 4. RAG: retrieve context + build augmented prompt
    augmented_prompt, rag_used = await _build_augmented_prompt(
        raw_prompt=request.prompt,
        user_id=str(current_user.id),
        user_prefs=user_prefs,
        use_rag=request.use_rag,
    )

    # 5. Call AI inference server with the augmented prompt
    try:
        ai_response = await ai_client.generate_sync(
            prompt=augmented_prompt,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
        )
    except Exception as e:
        logger.error(f"AI inference failed: {e}")
        raise HTTPException(status_code=503, detail="AI Inference server is currently unavailable")

    optimized = ai_response["generated_text"]
    latency = ai_response["latency_ms"]
    tokens = ai_response["token_count"]

    # 6. Cache the result (24 hour TTL)
    await redis_client.setex(cache_key, 86400, optimized)

    # 7. Log history to Postgres
    history = PromptHistory(
        user_id=current_user.id,
        original_prompt=request.prompt,
        optimized_prompt=optimized,
        latency_ms=latency,
        tokens_generated=tokens,
    )
    db.add(history)
    await db.commit()

    return PromptResponse(
        optimized_prompt=optimized,
        cached=False,
        latency_ms=latency,
        rag_context_used=rag_used,
    )


# ── SSE streaming endpoint ────────────────────────────────────────────────────

@router.post("/optimize/stream")
async def optimize_prompt_stream(
    request: PromptRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
):
    """
    SSE stream for prompt optimisation.
    Flow: rate limit → cache check → RAG retrieve → augment → stream tokens from AI.
    """
    # 1. Rate limit
    await check_rate_limit(redis_client, str(current_user.id), limit=20, period_seconds=3600)

    # 2. Cache check
    cache_key = _get_cache_key(request.prompt, request.max_new_tokens, request.temperature)
    cached_result = await redis_client.get(cache_key)

    if cached_result:
        async def cached_stream():
            import asyncio
            words = cached_result.split(" ")
            for word in words:
                if await req.is_disconnected():
                    break
                await asyncio.sleep(0.01)
                yield f"data: {word} \n\n"
            yield "data: [DONE]\n\n"

            history = PromptHistory(
                user_id=current_user.id,
                original_prompt=request.prompt,
                optimized_prompt=cached_result,
                latency_ms=0.0,
                tokens_generated=0,
            )
            db.add(history)
            await db.commit()

        return StreamingResponse(cached_stream(), media_type="text/event-stream")

    # 3. Fetch user preferences
    user_prefs = await _get_user_preferences(db, current_user.id)

    # 4. RAG: retrieve context + build augmented prompt
    augmented_prompt, rag_used = await _build_augmented_prompt(
        raw_prompt=request.prompt,
        user_id=str(current_user.id),
        user_prefs=user_prefs,
        use_rag=request.use_rag,
    )

    # 5. Stream from AI server using augmented prompt
    async def ai_stream():
        generated_text = ""
        try:
            async for token in ai_client.generate_stream(
                prompt=augmented_prompt,
                max_new_tokens=request.max_new_tokens,
                temperature=request.temperature,
            ):
                if await req.is_disconnected():
                    break
                generated_text += token
                safe_token = token.replace("\n", "\\n")
                yield f"data: {safe_token}\n\n"

            yield "data: [DONE]\n\n"

            # After stream completes — cache result and log history
            if generated_text:
                await redis_client.setex(cache_key, 86400, generated_text)

                history = PromptHistory(
                    user_id=current_user.id,
                    original_prompt=request.prompt,
                    optimized_prompt=generated_text,
                    latency_ms=0.0,  # Not measured per-token yet
                    tokens_generated=len(generated_text) // 4,
                )
                db.add(history)
                await db.commit()

        except Exception as e:
            logger.error(f"AI stream error: {e}")
            yield "data: [ERROR: AI inference failed]\n\n"

    return StreamingResponse(ai_stream(), media_type="text/event-stream")
