"""Domain error hierarchy and FastAPI exception handlers.

Errors raised inside the application use these classes. The FastAPI handlers
convert them to consistent JSON responses so no domain logic imports FastAPI.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class MentorOSError(Exception):
    """Base for all application-defined errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class StudentNotFoundError(MentorOSError):
    status_code = 404
    code = "student_not_found"


class SessionNotFoundError(MentorOSError):
    status_code = 404
    code = "session_not_found"


class TopicNotFoundError(MentorOSError):
    status_code = 404
    code = "topic_not_found"


class LLMInvocationError(MentorOSError):
    status_code = 503
    code = "llm_invocation_failed"


class AssessmentError(MentorOSError):
    status_code = 422
    code = "assessment_error"


def _error_payload(error: MentorOSError, request_id: str | None) -> dict:
    return {
        "error": {
            "code": error.code,
            "message": error.message,
            "details": error.details,
            "request_id": request_id,
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Attach JSON error handlers to the FastAPI app."""
    from .logging import request_id_var

    @app.exception_handler(MentorOSError)
    async def handle_mentoros_error(  # type: ignore[unused-variable]
        _request: Request, error: MentorOSError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content=_error_payload(error, request_id_var.get()),
        )
