# ADR-001 — Technology Stack

**Date:** 2026-11-20
**Status:** Accepted

## Context

MentorOS v0.1 needs a foundation that supports a stateful agentic tutoring loop, deterministic math verification, persistent student memory, and clean subject-agnostic domain separation. Choices here are hard to reverse once code exists.

## Decisions

### Python 3.12+
Mature async support, strong typing, the only ecosystem with LangGraph, SymPy, SQLAlchemy, and Pydantic all at production quality simultaneously.

### FastAPI
Async-native, Pydantic-integrated, excellent OpenAPI generation. DRF/Flask considered; both lack native async ergonomics needed for LangGraph invocation.

### LLM Provider (Ollama) + Model
v0.1 uses local Ollama with **qwen3.5:9b** for all tutoring nodes. Anthropic Claude is added later behind the provider abstraction (ADR-002). Embeddings use **qwen3-embedding:0.6b** via Ollama, prepared for v0.2 pgvector semantic memory; no embedding calls run in v0.1. Running locally keeps cost at zero during development and avoids network latency; the provider abstraction means swapping to Anthropic later is an env-var change.

### LangGraph (not LangChain LCEL alone, not raw LLM calls)
The tutoring loop is a stateful conditional graph, not a chain. LangGraph gives typed state, conditional edges, checkpointing, and testability with mocked nodes. The tradeoff is added dependency weight; accepted because the graph structure is a genuine requirement.

### SQLAlchemy 2.x (async) + asyncpg + Alembic
Industry standard for structured persistence. Async from the start avoids a painful retrofit. Alembic gives version-controlled schema migrations. Tortoise ORM and Beanie considered; both have smaller ecosystems and fewer production references.

### Pydantic v2
Used for LangGraph state typing and API schemas both. One validation system, not two. v2 is 5-10x faster than v1 and the langchain-core integration requires it.

### SymPy 1.13+
Only mature Python library for symbolic math verification. Deterministic where possible; LLM-assisted evaluation used only as fallback. Known risk: some expressions are slow; we add explicit timeouts.

### Ruff + mypy
Ruff replaces flake8 + isort + black in one fast binary. mypy for type checking. Both run in CI.

### Docker Compose
PostgreSQL + pgvector local via `pgvector/pgvector` image. No other infrastructure in v0.1 (no Redis, no message queue).

## Rejected Options
- **Django**: Too much ORM magic, session middleware coupling; overkill for an API-only service.
- **SQLite**: Not suitable for async concurrent writes; PostgreSQL from day one avoids migration later.
- **Redis**: No concrete justification in v0.1. Added if session caching becomes a measured bottleneck.
- **Celery**: No background task requirement yet.
