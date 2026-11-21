"""Smoke tests: imports, config loading, and health endpoint."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Ensure each test gets a fresh Settings instance."""
    from mentoros.core.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def set_env(monkeypatch):
    """Apply a minimal valid environment for tests that create the app."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://mentoros:mentoros@localhost:5432/mentoros")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_MODEL", "qwen3.5:9b")
    monkeypatch.setenv("APP_ENV", "development")


@pytest.fixture
def app(set_env):
    from mentoros.main import create_app
    return create_app()


def test_imports():
    """All core modules import without error."""
    import mentoros
    from mentoros.core.config import get_settings  # noqa: F401
    from mentoros.core.exceptions import MentorOSError, StudentNotFoundError  # noqa: F401
    from mentoros.core.logging import get_logger  # noqa: F401
    assert mentoros.__version__ == "0.1.0"


def test_settings_defaults(monkeypatch):
    """Settings load with expected defaults when env is clean."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://mentoros:mentoros@localhost:5432/mentoros")
    from mentoros.core.config import get_settings
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
async def test_health_echoes_request_id(app):
    """Health response echoes a valid X-Request-Id header."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health", headers={"X-Request-Id": "test-abc-123"})
    assert response.headers.get("x-request-id") == "test-abc-123"


@pytest.mark.anyio
async def test_health_generates_request_id_when_absent(app):
    """Health response generates an X-Request-Id when none is supplied."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.headers.get("x-request-id")  # non-empty


@pytest.mark.anyio
async def test_unknown_route_returns_404(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
