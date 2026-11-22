"""Application configuration loaded from environment variables.

All settings come from environment variables (or .env). No secrets in code.
Pydantic-settings handles parsing, type coercion, and default values.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Loaded once, cached via get_settings()."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_env: str = Field(default="development", description="development | production")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO", description="DEBUG | INFO | WARNING | ERROR")

    # ── Database ─────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://mentoros:mentoros@localhost:5433/mentoros"
    )
    database_pool_size: int = Field(default=10)
    database_max_overflow: int = Field(default=20)

    # ── LLM Provider ──────────────────────────────────────────────
    llm_provider: str = Field(default="ollama", description="ollama | anthropic")
    llm_model: str = Field(default="qwen3.5:9b")
    llm_timeout_seconds: int = Field(default=60)
    llm_max_retries: int = Field(default=2)

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434")

    # Anthropic (added in later iteration)
    anthropic_api_key: str = Field(default="")

    # Embeddings (prepared for v0.2; unused in v0.1)
    embedding_model: str = Field(default="qwen3-embedding:0.6b")
    embedding_dimensions: int = Field(default=1024)

    # ── Stub Auth ────────────────────────────────────────────────
    student_id_header: str = Field(default="X-Student-Id")

    # ── Assessment ───────────────────────────────────────────────
    sympy_timeout_seconds: int = Field(default=5)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings. Cleared only on explicit reload."""
    return Settings()
