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

# Install PyTorch (CPU by default; override for GPU)
RUN pip install --no-cache-dir --prefix=/install \
    torch \
    sentencepiece \
    fastapi \
    uvicorn[standard] \
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

# Copy application code
COPY src/ ./src/
COPY models/ ./models/

# Switch to non-root user
USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["python", "-m", "src.inference.server", \
     "--checkpoint", "models/checkpoints/best_model.pt", \
     "--port", "8001"]
