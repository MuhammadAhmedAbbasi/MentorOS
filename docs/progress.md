# MentorOS — Development Progress

## Current Status

**Day:** 3
**Task:** Complete
**Date:** 2026-11-22

---

## Day 1 — Requirements and Architecture Planning ✓

### Decisions Made

| # | Decision | Recorded in |
|---|---|---|
| 1 | Technology stack finalized | ADR-001 |
| 2 | LLM provider abstraction (Ollama now, Anthropic later via factory) | ADR-002 |
| 3 | Stub auth (UUID header) for v0.1 | requirements.md |
| 4 | 10 seeded mathematics topics | requirements.md |
| 5 | pgvector prepared in schema but unused in v0.1 | database-schema.md |
| 6 | LangGraph DAG per turn, no intra-turn cycles | ai-workflow.md |
| 7 | Mastery heuristic: delta formula with difficulty + recency weights | ai-workflow.md |
| 8 | Misconceptions confidence-gated (evidence_count ≥ 2 to surface) | database-schema.md |
| 9 | expected_answer never checkpointed, always fetched from DB | ai-workflow.md |
| 10 | API-only v0.1, no frontend | requirements.md |
| 11 | LLM model: qwen3.5:9b (Ollama); embeddings: qwen3-embedding:0.6b | ADR-001 |

### Files Created

- `docs/requirements.md`
- `docs/roadmap.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/database-schema.md`
- `docs/architecture/ai-workflow.md`
- `docs/decisions/ADR-001-technology-stack.md`
- `docs/decisions/ADR-002-llm-provider-abstraction.md`
- `pyproject.toml`
- `.env.example`
- `.gitignore`

---

## Day 2 — Project Foundation ✓

### Verification Results

| Check | Result |
|---|---|
| `pip install -e ".[dev]"` | ✓ All dependencies installed |
| `ruff check src tests` | ✓ All checks passed (0 errors) |
| `pytest -q` | ✓ 6 passed, 0 warnings |
| `GET /api/v1/health` | ✓ `{"status":"ok","version":"0.1.0"}` |
| `docker-compose.yml` YAML | ✓ Valid |
| Git commit + push | ✓ a7cfe2c pushed to origin/main |

### Fixes Applied

- **Dockerfile**: Copy `pyproject.toml`, `README.md`, `src/` before `pip install`; runtime deps only (no `[dev]` in image)
- **CI**: Added `.github/workflows/ci.yml` — Python 3.12, pip install, ruff check, pytest on push/PR
- **logging.py**: Fixed timestamp to use `datetime.fromtimestamp(tz=UTC)` (proper microsecond UTC ISO-8601); added `reset_request_context()` function
- **main.py**: Request ID middleware validates + truncates header, resets context vars in `finally` block; import block sorted
- **tests/test_smoke.py**: Replaced `os.environ.setdefault` with `monkeypatch.setenv`; `autouse` fixture clears `get_settings` cache between tests; added `test_health_generates_request_id_when_absent`
- **README.md**: Full professional documentation — prerequisites, install, env config, Docker, running API, tests, project structure
- **pyproject.toml**: Added `asyncio_default_fixture_loop_scope = "function"` to silence pytest-asyncio warning

### Files Created/Modified

- `src/mentoros/__init__.py`
- `src/mentoros/main.py`
- `src/mentoros/core/config.py`
- `src/mentoros/core/logging.py`
- `src/mentoros/core/exceptions.py`
- `src/mentoros/api/routes/__init__.py`
- `src/mentoros/api/routes/health.py`
- `src/mentoros/domains/` (all `__init__.py` placeholders)
- `src/mentoros/infrastructure/` (all `__init__.py` placeholders)
- `tests/test_smoke.py`
- `tests/__init__.py`
- `tests/conftest.py`
- `Dockerfile`
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `README.md`
- `pyproject.toml`

---

## Day 3 — Database and Curriculum Foundation ✓

### Verification Results

| Check | Result |
|---|---|
| `docker compose ps` | ✓ `mentoros_db` healthy, pgvector 0.8.7 available |
| `alembic upgrade head` | ✓ 13 tables created |
| `alembic downgrade base` → `upgrade head` | ✓ Round-trips cleanly |
| `alembic check` | ✓ No drift between models and migration |
| `python scripts/seed_curriculum.py` (run twice) | ✓ 10 topics, 11 prerequisite edges, no duplicates |
| `pytest -q` | ✓ 15 passed (6 smoke, 9 database), 0 warnings |
| `ruff check src tests scripts migrations` | ✓ Clean |

### Decisions Made

| # | Decision | Reason |
|---|---|---|
| 1 | Docker Postgres on host port **5433** | A native PostgreSQL service (`postgresql-x64-19`) holds 5432 on this machine; connections to 5432 were reaching it, not Docker |
| 2 | Models live in each domain's `models.py`; `mentoros/models.py` is the registry | Keeps domain ownership; Alembic needs one import that sees every table |
| 3 | Engine created lazily (`get_engine()`), not at import | Importing the app never opens a connection; tests can set the URL first |
| 4 | `student_memories` (pgvector) deferred to its own v0.2 migration | An unused table is cost with no benefit; image already has pgvector |
| 5 | Added `learning_events.idempotency_key` (unique, nullable) | Requirement: idempotent learning events |
| 6 | CHECK constraints instead of PG ENUM types | Easier to evolve in migrations |
| 7 | Separate `mentoros_test` database; each test rolls back | Tests never touch dev data or each other |

### Files Created/Modified

- `src/mentoros/infrastructure/database/engine.py`, `mixins.py`
- `src/mentoros/domains/{students,curriculum,assessment,memory}/models.py`
- `src/mentoros/models.py`
- `src/mentoros/domains/curriculum/seed.py`, `data/mathematics.py`
- `scripts/seed_curriculum.py`
- `alembic.ini`, `migrations/env.py`, `migrations/versions/050886459566_initial_schema.py`
- `tests/test_database.py`
- `docker-compose.yml`, `.env.example`, `core/config.py` (port 5433)
- `main.py` (dispose engine on shutdown)
- `.github/workflows/ci.yml` (Postgres service, migrations, seed)
- `README.md`, `docs/architecture/database-schema.md`

### Outstanding Issues

- Docker CLI is not on the default PATH in new terminals; add `C:\Users\Administrator\AppData\Local\Programs\DockerDesktop\resources\bin` to the user PATH.
- Two native PostgreSQL services are installed (16 stopped, 19 running). They are not used by MentorOS and can be uninstalled.
- CI changes are untested until the first push runs on GitHub.

---

## Upcoming

See [roadmap.md](roadmap.md) for the full 12-day plan.

