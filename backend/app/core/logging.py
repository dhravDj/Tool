"""Structured logging configuration for DocuMind AI."""

import contextvars
import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

# Context variable for request correlation ID
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")


class StructuredJsonFormatter(logging.Formatter):
    """Custom logging formatter that outputs JSON objects with contextual fields."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        req_id = request_id_ctx.get()
        if req_id:
            log_data["request_id"] = req_id

        if record.exc_info and record.exc_text:
            log_data["exception"] = record.exc_text

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)

        return json.dumps(log_data)


def setup_logging(debug: bool = False) -> None:
    """Initialize application-wide logging handlers."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove existing handlers to avoid duplicate log lines
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = StructuredJsonFormatter()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Suppress overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


logger = logging.getLogger("documind")
