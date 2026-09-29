# ──────────────────────────────────────────────────────────────────────────────
# AI Worker Dockerfile — Multi-stage optimized build with model weights
#
# Stage 1 (builder): Installs Python deps including PyTorch
# Stage 2 (runtime): Slim image with only inference dependencies
#
# Build:  docker build -t promptpolisher/ai-worker ./ai
# Run:    docker run -p 8001:8001 --gpus all promptpolisher/ai-worker
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Inference-only dependency set — deliberately narrower than ai/requirements.txt,
# which also carries the training stack (datasets, transformers, trl).
#
# torch comes from the CPU wheel index: the default PyPI wheel drags in ~2.5GB
# of CUDA libraries this image never uses. For a GPU build, drop the
# --index-url line and run the container with --gpus all.
RUN pip install --no-cache-dir --prefix=/install \
        --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install --no-cache-dir --prefix=/install \
        sentencepiece \
        fastapi \
        "uvicorn[standard]" \
        httpx

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code. The modules import each other as `ai.src.*`, so the
# package has to live under an `ai/` directory on the import path.
COPY src/ ./ai/src/
COPY models/ ./ai/models/

# Switch to non-root user
USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# The server loads ai/models/checkpoints/final_model.pt if it is present and
# falls back to mock responses if it is not, so this starts either way.
CMD ["uvicorn", "ai.src.inference.server:app", "--host", "0.0.0.0", "--port", "8001"]
