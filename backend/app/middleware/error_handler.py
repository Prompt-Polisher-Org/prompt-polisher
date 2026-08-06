"""
middleware/error_handler.py — Global exception handler & request ID tracking.

Task: Week 9-10 / Backend Hardening (task.md lines 524-527)
  [x] Global exception handler
  [x] Structured error response format
  [x] Request ID tracking for debugging

Every request gets a unique X-Request-ID header. If the client sends one,
we preserve it; otherwise we generate a UUID. The request ID appears in:
  - Response headers (X-Request-ID)
  - Error response bodies (request_id field)
  - Log output (for tracing through logs)
"""
import uuid
import time
import logging
import traceback

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("prompt_polisher")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Catches all unhandled exceptions and returns a structured JSON error.
    Also attaches a request ID to every request/response for traceability.
    """

    async def dispatch(self, request: Request, call_next):
        # ── Generate or preserve request ID ───────────────────────────────
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Attach request ID and timing to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms}ms"

            # Log the request
            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            return response

        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Log the full traceback for debugging
            logger.error(
                "unhandled_exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                    "duration_ms": duration_ms,
                },
            )

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal server error occurred.",
                    "request_id": request_id,
                },
                headers={
                    "X-Request-ID": request_id,
                    "X-Response-Time": f"{duration_ms}ms",
                },
            )
