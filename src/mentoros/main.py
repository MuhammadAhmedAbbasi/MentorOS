"""MentorOS FastAPI application entry point.

Create the app with create_app(), then run with:
    uvicorn mentoros.main:app --reload
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from mentoros import __version__
from mentoros.api.routes import api_router
from mentoros.core.config import get_settings
from mentoros.core.exceptions import register_exception_handlers
from mentoros.core.logging import configure_logging, get_logger, set_request_id

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("MentorOS starting up", extra={"version": __version__, "env": settings.app_env})
    yield
    logger.info("MentorOS shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    application = FastAPI(
        title="MentorOS",
        description="Agentic AI-powered personalized learning operating system",
        version=__version__,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # CORS — open in development, locked down in production via env config.
    if not settings.is_production:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Request ID middleware — attaches a UUID to every request for tracing.
    @application.middleware("http")
    async def attach_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        set_request_id(request_id)
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

    register_exception_handlers(application)
    application.include_router(api_router)

    return application


app = create_app()
