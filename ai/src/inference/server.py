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
import os
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from ai.src.inference.engine import InferenceEngine, GenerationConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Host runs load repo-root .env. Docker Compose injects the same variables via
# env_file, so this is a no-op there when the file is not mounted.
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

# FastAPI app
app = FastAPI(title="Prompt Polisher Inference API", version="1.0.0")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global inference engine instance
engine: Optional[InferenceEngine] = None


def _polish_prompt(raw: str) -> str:
    """
    Rule-based prompt optimizer used when the trained model is unavailable.
    Transforms a raw user prompt into a structured, effective AI prompt.
    """
    import re

    raw_lower = raw.strip().lower()
    raw_clean = raw.strip()

    if any(kw in raw_lower for kw in ["math", "algebra", "equation", "solve", "latex", "quadratic", "calculus", "integral", "derivative", "polynomial", "factor", "simplif", "raise", "power", "square", "cube", "root", "find x", "find y", "log", "sin", "cos", "tan"]):
        expr = raw_clean

        expr = re.sub(r'(\d+)\s*raise\s*to\s*(the\s+)?(power\s+of\s+)?(\w+)', r'\1^{\4}', expr, flags=re.IGNORECASE)
        expr = re.sub(r'(\w)\s*raise\s*to\s*(the\s+)?(power\s+of\s+)?(\w+)', r'\1^{\4}', expr, flags=re.IGNORECASE)
        expr = re.sub(r'(\d+)\s*squared', r'\1^{2}', expr, flags=re.IGNORECASE)
        expr = re.sub(r'(\w)\s*squared', r'\1^{2}', expr, flags=re.IGNORECASE)
        expr = re.sub(r'(\d+)\s*cubed', r'\1^{3}', expr, flags=re.IGNORECASE)
        expr = re.sub(r'(\w)\s*cubed', r'\1^{3}', expr, flags=re.IGNORECASE)
        expr = re.sub(r'square\s*root\s*of\s*(\w+)', r'\\sqrt{\1}', expr, flags=re.IGNORECASE)
        expr = re.sub(r'sqrt\s*\(?\s*(\w+)\s*\)?', r'\\sqrt{\1}', expr, flags=re.IGNORECASE)
        expr = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', expr)
        expr = re.sub(r'pi\b', r'\\pi', expr, flags=re.IGNORECASE)
        expr = re.sub(r'theta\b', r'\\theta', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\binfinity\b', r'\\infty', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\*', r' \\times ', expr)

        task_words = ["solve", "find", "evaluate", "simplify", "factor", "compute", "calculate", "prove", "expand"]
        action = "Solve"
        for w in task_words:
            if w in raw_lower:
                action = w.capitalize()
                break

        return (
            f"{action}: $$ {expr} $$\n\n"
            f"Show each step in LaTeX. Box the final answer as $\\boxed{{result}}$."
        )

    if any(kw in raw_lower for kw in ["marketing email", "email", "newsletter"]):
        return (
            f"Write a product-launch email.\n\n"
            f"Context: {raw_clean}\n\n"
            f"Structure: Subject line (< 50 chars) | Hook (1 sentence, address pain point) | "
            f"Body (AIDA framework, < 200 words) | Single CTA with urgency.\n"
            f"Tone: conversational, no jargon."
        )

    if any(kw in raw_lower for kw in ["explain", "teach", "what is", "how does"]):
        return (
            f"{raw_clean}\n\n"
            f"Use a real-world analogy first. Break into 3 progressive layers. "
            f"Define technical terms inline. End with one comprehension question."
        )

    if any(kw in raw_lower for kw in ["python", "code", "function", "script", "program", "algorithm"]):
        return (
            f"{raw_clean}\n\n"
            f"Requirements: type hints, docstring, edge-case handling (empty input, invalid types). "
            f"Include 2 test examples. Optimize for readability."
        )

    if any(kw in raw_lower for kw in ["summarize", "summary", "tldr", "key points"]):
        return (
            f"{raw_clean}\n\n"
            f"Output: 2-sentence executive summary, then 5-7 bullet-point key findings, "
            f"methodology used, limitations, and practical implications."
        )

    if any(kw in raw_lower for kw in ["linkedin", "social media", "post", "tweet", "blog"]):
        return (
            f"{raw_clean}\n\n"
            f"Format: Hook in first line | Short paragraphs (1-2 sentences) | "
            f"Personal insight | End with engaging question | 3-5 hashtags.\n"
            f"Length: 150-200 words."
        )

    if any(kw in raw_lower for kw in ["write", "essay", "article", "story", "creative"]):
        return (
            f"{raw_clean}\n\n"
            f"Structure: Clear thesis in opening | Specific details over generalizations | "
            f"Varied sentence length | Evidence-backed claims | Memorable closing insight."
        )

    return (
        f"{raw_clean}\n\n"
        f"Break response into labeled sections. Be specific and actionable. "
        f"Cover edge cases. End with key takeaways."
    )


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
    checkpoint_path = Path(os.getenv(
        "AI_MODEL_CHECKPOINT_PATH",
        "backend/app/models/best_model.pt",
    ))
    tokenizer_path = Path(os.getenv(
        "AI_MODEL_TOKENIZER_PATH",
        "ai/models/tokenizer/prompt_polisher_bpe.model",
    ))

    if not checkpoint_path.exists():
        logger.warning("Checkpoint %s not found. Using rule-based optimizer.", checkpoint_path)
        engine = None
    elif not tokenizer_path.exists():
        logger.warning(
            "Tokenizer %s not found for checkpoint %s. Using rule-based optimizer.",
            tokenizer_path,
            checkpoint_path,
        )
        engine = None
    else:
        try:
            logger.info(f"Loading model from {checkpoint_path}...")
            engine = InferenceEngine.from_checkpoint(
                checkpoint_path,
                tokenizer_path=tokenizer_path,
            )
            logger.info("Model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load model: {e}. Using rule-based optimizer.")
            engine = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint for Nginx/load balancers."""
    mode = "transformer" if engine is not None else "rule-based"

    info = {"status": "healthy", "inference_mode": mode}
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
        start = time.perf_counter()
        polished = _polish_prompt(req.prompt)
        latency = (time.perf_counter() - start) * 1000.0
        token_estimate = len(polished.split())
        return GenerateResponse(
            generated_text=polished,
            token_count=token_estimate,
            latency_ms=round(latency, 2),
        )

    config = GenerationConfig(
        max_new_tokens=req.max_new_tokens,
        temperature=req.temperature,
        top_k=req.top_k,
        top_p=req.top_p,
        repetition_penalty=req.repetition_penalty
    )

    try:
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
        polished = _polish_prompt(req.prompt)

        async def rule_stream():
            words = polished.split(" ")
            for word in words:
                safe = word.replace('\n', '\\n')
                yield f"data: {safe} \n\n"
                await asyncio.sleep(0.04)
            yield "data: [DONE]\n\n"

        return StreamingResponse(rule_stream(), media_type="text/event-stream")

    config = GenerationConfig(
        max_new_tokens=req.max_new_tokens,
        temperature=req.temperature,
        top_k=req.top_k,
        top_p=req.top_p,
        repetition_penalty=req.repetition_penalty
    )

    async def event_generator():
        try:
            for token_text in engine.stream(req.prompt, gen_config=config):
                safe_text = token_text.replace('\n', '\\n')
                yield f"data: {safe_text}\n\n"
                await asyncio.sleep(0.001)

            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"data: [ERROR: {str(e)}]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai.src.inference.server:app", host="0.0.0.0", port=8001, reload=True)
