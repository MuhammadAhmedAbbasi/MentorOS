# MentorOS

Agentic AI-powered personalized learning operating system. MentorOS provides every student with a persistent AI tutor that understands their learning history, tracks topic mastery, and adapts its teaching strategy across sessions.

## Project Status

**v0.1 — AI backend in active development.** Mathematics subject only. API-only (no frontend). See [docs/roadmap.md](docs/roadmap.md) for the 12-day plan.

---

## Prerequisites

- Python 3.12+
- Docker Desktop (for PostgreSQL)
- [Ollama](https://ollama.com) with `qwen3.5:9b` pulled locally

Pull the model before running:
```bash
ollama pull qwen3.5:9b
```

---

## Installation

```bash
# Clone the repository
git clone https://github.com/MuhammadAhmedAbbasi/MentorOS.git
cd MentorOS

# Create and activate a virtual environment
python -m venv mentorenv
# Windows
mentorenv\Scripts\activate
# macOS / Linux
source mentorenv/bin/activate

# Install the package and all dependencies
pip install -e ".[dev]"
```

---

## Environment Configuration

Copy `.env.example` to `.env` and review the values:

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://mentoros:mentoros@localhost:5433/mentoros` | Async PostgreSQL URL |
| `TEST_DATABASE_URL` | `postgresql+asyncpg://mentoros:mentoros@localhost:5433/mentoros_test` | Database used by `tests/test_database.py` |
| `LLM_PROVIDER` | `ollama` | `ollama` or `anthropic` |
| `LLM_MODEL` | `qwen3.5:9b` | Model name for the chosen provider |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama server |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |

---

## Database (Docker)

Start PostgreSQL with the pgvector extension:

```bash
docker compose up -d
```

Verify it is healthy:
```bash
docker compose ps
```

Stop it:
```bash
docker compose down
```

Data is persisted in the `mentoros_pgdata` Docker volume between restarts.

The container publishes PostgreSQL on host port **5433**, so it does not clash with a natively installed PostgreSQL on 5432. Set `POSTGRES_HOST_PORT` to change it.

### Migrations and seed data

```bash
alembic upgrade head                 # create / update all tables
python scripts/seed_curriculum.py    # load the 10 mathematics topics (safe to re-run)
```

After changing ORM models, generate a migration and review it before applying:
```bash
alembic revision --autogenerate -m "describe the change"
```

---

## Running the API

```bash
uvicorn mentoros.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:
```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","version":"0.1.0"}
```

Interactive API docs: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

---

## Running Tests

Database tests need a separate test database (created once):
```bash
docker exec mentoros_db psql -U mentoros -d mentoros -c "CREATE DATABASE mentoros_test"
```

```bash
pytest -q
```
If the test database is unreachable, the database tests are skipped rather than failing.

Run with verbose output:
```bash
pytest tests/ -v
```

Run linting:
```bash
ruff check src tests
```

---

## Project Structure

```
src/mentoros/
├── api/              # FastAPI routes and dependency providers
├── core/             # Config, logging, exceptions (no domain logic)
├── domains/
│   ├── tutoring/     # LangGraph workflow, teaching strategies, prompts
│   ├── students/     # Student identity and profile
│   ├── curriculum/   # Subjects, topics, prerequisites
│   ├── assessment/   # Math evaluation (SymPy)
│   └── memory/       # Sessions, mastery, misconceptions
├── infrastructure/
│   ├── database/     # SQLAlchemy engine and session factory
│   ├── llm/          # LLM provider abstraction (Ollama / Anthropic)
│   └── vector_store/ # pgvector adapter (prepared for v0.2)
└── main.py           # FastAPI app factory
```

---

## Architecture Decisions

See [docs/decisions/](docs/decisions/) for Architecture Decision Records:
- [ADR-001 — Technology Stack](docs/decisions/ADR-001-technology-stack.md)
- [ADR-002 — LLM Provider Abstraction](docs/decisions/ADR-002-llm-provider-abstraction.md)
