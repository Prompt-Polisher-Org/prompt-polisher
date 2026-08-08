"""
core/logging_config.py — Structured JSON logging configuration.

Task: Week 9-10 / Backend Hardening (task.md line 532)
  [x] Add structured logging (JSON format)

All log output is JSON-formatted for easy parsing by log aggregators
(ELK stack, Datadog, CloudWatch, etc). Includes timestamp, level,
message, and any extra fields passed via the `extra` dict.
"""
import logging
import json
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include any extra fields passed to the logger
        # e.g., logger.info("msg", extra={"request_id": "abc", "duration_ms": 42})
        standard_attrs = {
            "name", "msg", "args", "created", "relativeCreated", "exc_info",
            "exc_text", "stack_info", "lineno", "funcName", "pathname",
            "filename", "module", "levelname", "levelno", "msecs",
            "thread", "threadName", "process", "processName", "message",
            "taskName",
        }
        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                log_entry[key] = value

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure the root logger and the app logger to use JSON format.
    Call this once at application startup (in main.py's lifespan).
    """
    json_formatter = JSONFormatter()

    # Console handler with JSON output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)

    # Configure the app logger
    app_logger = logging.getLogger("prompt_polisher")
    app_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    app_logger.handlers.clear()
    app_logger.addHandler(console_handler)
    app_logger.propagate = False

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
