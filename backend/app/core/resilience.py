"""
core/resilience.py — Retry logic and Circuit Breaker for external service calls.

Task: Week 9-10 / Backend Hardening (task.md lines 529-530)
  [x] Add retry logic for external service calls (Qdrant, Redis)
  [x] Implement circuit breaker pattern for inference calls

Circuit Breaker States:
  CLOSED  → Normal operation, requests pass through.
  OPEN    → Too many failures, requests fail immediately.
  HALF_OPEN → After a cooldown, allow one test request through.
"""
import asyncio
import functools
import logging
import time
from enum import Enum
from typing import Any, Callable, Optional, Type

logger = logging.getLogger("prompt_polisher")


# ── Retry Decorator ───────────────────────────────────────────────────────────

def retry_async(
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
):
    """
    Async retry decorator with exponential backoff.

    Usage:
        @retry_async(max_retries=3, retryable_exceptions=(ConnectionError, TimeoutError))
        async def call_qdrant():
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exception = exc
                    if attempt == max_retries:
                        logger.error(
                            "retry_exhausted",
                            extra={
                                "function": func.__qualname__,
                                "attempt": attempt,
                                "error": str(exc),
                            },
                        )
                        raise

                    delay = min(base_delay * (backoff_factor ** (attempt - 1)), max_delay)
                    logger.warning(
                        "retry_attempt",
                        extra={
                            "function": func.__qualname__,
                            "attempt": attempt,
                            "max_retries": max_retries,
                            "delay_s": delay,
                            "error": str(exc),
                        },
                    )
                    await asyncio.sleep(delay)
            raise last_exception  # should never reach here
        return wrapper
    return decorator


# ── Circuit Breaker ───────────────────────────────────────────────────────────

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpen(Exception):
    """Raised when a call is attempted while the circuit is OPEN."""
    def __init__(self, service_name: str, retry_after: float):
        self.service_name = service_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker OPEN for '{service_name}'. "
            f"Retry after {retry_after:.1f}s."
        )


class CircuitBreaker:
    """
    Simple async circuit breaker.

    Parameters:
        failure_threshold: Number of consecutive failures before opening the circuit.
        recovery_timeout:  Seconds to wait in OPEN state before moving to HALF_OPEN.
        success_threshold: Consecutive successes in HALF_OPEN before closing again.
    """

    def __init__(
        self,
        service_name: str = "unknown",
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
    ):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if self._last_failure_time and (
                time.monotonic() - self._last_failure_time >= self.recovery_timeout
            ):
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                logger.info(
                    "circuit_half_open",
                    extra={"service": self.service_name},
                )
        return self._state

    def record_success(self):
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info(
                    "circuit_closed",
                    extra={"service": self.service_name},
                )
        else:
            self._failure_count = 0

    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in HALF_OPEN reopens the circuit
            self._state = CircuitState.OPEN
            logger.warning(
                "circuit_reopened",
                extra={"service": self.service_name},
            )
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                "circuit_opened",
                extra={
                    "service": self.service_name,
                    "failures": self._failure_count,
                },
            )

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute `func` through the circuit breaker."""
        current_state = self.state  # triggers OPEN → HALF_OPEN check

        if current_state == CircuitState.OPEN:
            retry_after = self.recovery_timeout - (
                time.monotonic() - (self._last_failure_time or 0)
            )
            raise CircuitBreakerOpen(self.service_name, max(retry_after, 0))

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as exc:
            self.record_failure()
            raise


# ── Pre-configured circuit breakers for key services ──────────────────────────

inference_circuit = CircuitBreaker(
    service_name="ai_inference",
    failure_threshold=5,
    recovery_timeout=30.0,
    success_threshold=2,
)

qdrant_circuit = CircuitBreaker(
    service_name="qdrant",
    failure_threshold=5,
    recovery_timeout=20.0,
    success_threshold=2,
)
