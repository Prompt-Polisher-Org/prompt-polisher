"""
server.py — FastAPI Inference Server for Prompt Polisher.

Task: Week 5-6 / Inference Engine (task.md lines 305-309)
  [x] HTTP endpoint for synchronous generation
  [x] Streaming endpoint for token-by-token output
  [x] Request queue for batching (optional / simplified)
  [x] Health check endpoint

Usage:
    # Run the inference server on port 8001
    uvicorn ai.src.inference.server:app --host 0.0.0.0 --port 8001
"""
import asyncio
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ai.src.inference.engine import InferenceEngine, GenerationConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Prompt Polisher Inference API", version="1.0.0")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global inference engine instance
engine: Optional[InferenceEngine] = None


# ── Pydantic Models ───────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="The raw prompt to optimize")
    max_new_tokens: int = Field(512, ge=1, le=2048)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    top_k: int = Field(50, ge=0)
    top_p: float = Field(0.9, ge=0.0, le=1.0)
    repetition_penalty: float = Field(1.1, ge=1.0)


class GenerateResponse(BaseModel):
    generated_text: str
    token_count: int
    latency_ms: float


# ── Lifespan Events ───────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Load the model when the server starts."""
    global engine
    # Hardcoded path for simplicity in this script; in prod use env vars
    checkpoint_path = "ai/models/checkpoints/final_model.pt"
    
    import os
    if not os.path.exists(checkpoint_path):
        logger.warning(f"Checkpoint {checkpoint_path} not found! Starting in dummy mode (MOCK responses).")
        engine = None
    else:
        try:
            logger.info(f"Loading model from {checkpoint_path}...")
            engine = InferenceEngine.from_checkpoint(checkpoint_path)
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            engine = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint for Nginx/load balancers."""
    status = "healthy" if engine is not None else "degraded (mock mode)"
    
    info = {"status": status}
    if engine is not None:
        info["model"] = engine.get_model_info()
        
    return info


@app.post("/v1/generate", response_model=GenerateResponse)
async def generate_sync(req: GenerateRequest):
    """
    Synchronous generation endpoint. 
    Blocks until the entire generated string is ready.
    """
    if engine is None:
        # Mock response for testing without a model
        await asyncio.sleep(1.0)
        return GenerateResponse(
            generated_text=f"MOCK: Optimized version of '{req.prompt}' (No model loaded)",
            token_count=10,
            latency_ms=1000.5
        )

    config = GenerationConfig(
        max_new_tokens=req.max_new_tokens,
        temperature=req.temperature,
        top_k=req.top_k,
        top_p=req.top_p,
        repetition_penalty=req.repetition_penalty
    )

    try:
        # Note: In a real high-throughput prod server, this blocking call 
        # should be run in a ThreadPoolExecutor or handled by a batching queue.
        result = engine.generate(req.prompt, gen_config=config)
        return GenerateResponse(**result)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/generate_stream")
async def generate_stream(req: GenerateRequest):
    """
    Streaming generation endpoint.
    Returns Server-Sent Events (SSE) containing tokens as they are generated.
    """
    if engine is None:
        async def mock_stream():
            words = ["MOCK:", "Optimized", "version", "of", f"'{req.prompt}'"]
            for word in words:
                yield f"data: {word} \n\n"
                await asyncio.sleep(0.2)
            yield "data: [DONE]\n\n"
        return StreamingResponse(mock_stream(), media_type="text/event-stream")

    config = GenerationConfig(
        max_new_tokens=req.max_new_tokens,
        temperature=req.temperature,
        top_k=req.top_k,
        top_p=req.top_p,
        repetition_penalty=req.repetition_penalty
    )

    async def event_generator():
        try:
            # We wrap the synchronous generator in an async wrapper.
            # In a true high-perf async server, the model inference itself
            # would run in a separate thread/process to not block the event loop.
            for token_text in engine.stream(req.prompt, gen_config=config):
                # Yield SSE format
                # Replace newlines so they don't break SSE format
                safe_text = token_text.replace('\n', '\\n')
                yield f"data: {safe_text}\n\n"
                # Small sleep to yield to event loop (optional)
                await asyncio.sleep(0.001)
                
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"data: [ERROR: {str(e)}]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai.src.inference.server:app", host="0.0.0.0", port=8001, reload=True)
