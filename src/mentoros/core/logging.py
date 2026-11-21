"""Structured JSON logging with request and session trace IDs.

Produces one JSON object per log line, suitable for ingestion into any log
aggregator. In development the lines are still human-readable because each
field is a stable key.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context vars for trace IDs — set per request by middleware.
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)


class JsonFormatter(logging.Formatter):
    """Format every record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        # Build a timezone-aware UTC timestamp with microseconds.
        ts = datetime.fromtimestamp(record.created, tz=UTC).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        ) + "Z"
        payload: dict[str, Any] = {
            "timestamp": ts,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach trace IDs when present in the current context.
        if request_id_var.get() is not None:
            payload["request_id"] = request_id_var.get()
        if session_id_var.get() is not None:
            payload["session_id"] = session_id_var.get()

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Extra fields added via logger.info("...", extra={...}).
        for key, value in record.__dict__.items():
            if key in payload or key.startswith("_"):
                continue
            if key in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "taskName",
            }:
                continue
            payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    """Configure root logging to emit JSON to stdout. Idempotent."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(log_level)

    # Clear handlers from previous configuration (e.g. uvicorn's).
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # Quiet noisy third-party loggers; keep our app at the configured level.
    for noisy in ("uvicorn.access", "httpx", "httpcore", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def set_request_id(request_id: str) -> None:
    request_id_var.set(request_id)


def set_session_id(session_id: str | None) -> None:
    session_id_var.set(session_id)


def reset_request_context() -> None:
    """Clear request-scoped context vars. Called at the end of each request."""
    request_id_var.set(None)
    session_id_var.set(None)


def get_logger(name: str = "mentoros") -> logging.Logger:
    return logging.getLogger(name)
