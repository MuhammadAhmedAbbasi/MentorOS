"""Smoke tests: imports, config loading, and health endpoint."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def app():
    # Override settings so tests run without a real .env file.
    import os
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://mentoros:mentoros@localhost:5432/mentoros")
    os.environ.setdefault("LLM_PROVIDER", "ollama")
    os.environ.setdefault("LLM_MODEL", "qwen3.5:9b")

    from mentoros.main import create_app
    return create_app()


def test_imports():
    """All core modules import without error."""
    import mentoros
    from mentoros.core.config import get_settings
    from mentoros.core.logging import get_logger
    from mentoros.core.exceptions import MentorOSError, StudentNotFoundError
    assert mentoros.__version__ == "0.1.0"


def test_settings_defaults():
    """Settings load with expected defaults."""
    import os
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://mentoros:mentoros@localhost:5432/mentoros")

    # Clear lru_cache so env overrides take effect in tests.
    from mentoros.core.config import get_settings
    get_settings.cache_clear()
    s = get_settings()
    assert s.llm_provider == "ollama"
    assert s.llm_model == "qwen3.5:9b"
    assert s.sympy_timeout_seconds == 5


@pytest.mark.anyio
async def test_health_endpoint(app):
    """GET /api/v1/health returns 200 with status ok."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"


@pytest.mark.anyio
async def test_health_sets_request_id_header(app):
    """Health response echoes or generates an X-Request-Id header."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health", headers={"X-Request-Id": "test-123"})
    assert response.headers.get("x-request-id") == "test-123"


@pytest.mark.anyio
async def test_unknown_route_returns_404(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
