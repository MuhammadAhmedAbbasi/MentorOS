# MentorOS — Development Roadmap

## v0.1 — 12-Day Implementation Plan

### Day 1 — Requirements and Architecture Planning ✓
- Requirements document
- Technology stack ADR
- LLM provider abstraction ADR
- System overview and domain boundaries
- Database schema design
- LangGraph node design
- Roadmap and progress tracking

### Day 2 — Project Foundation
- Professional Python package structure under `src/mentoros/`
- `core/config.py` — Pydantic-settings environment config
- `core/logging.py` — structured JSON logging
- `core/exceptions.py` — domain error hierarchy + FastAPI handlers
- FastAPI app bootstrap (`main.py`)
- Health endpoint (`GET /api/v1/health`)
- `.env.example`
- `pyproject.toml` complete with all dependencies
- `docker-compose.yml` — PostgreSQL + pgvector
- `Dockerfile`
- Ruff + mypy config
- Smoke tests (import checks, health endpoint)
- GitHub Actions baseline (lint + test on push)

### Day 3 — Database and Curriculum Foundation
- `infrastructure/database/` — async engine, session factory, base model
- Alembic init + initial migration
- SQLAlchemy models for all v0.1 tables
- `domains/curriculum/` — Subject, Topic, TopicPrerequisite models + seed loader
- 10 seeded mathematics topics with prerequisite graph
- `domains/students/` — Student model + stub-auth resolver
- Database integration tests (models round-trip, FK constraints)

### Day 4 — LangGraph Tutoring Foundation
- `domains/tutoring/graph/state.py` — typed `TutoringState`
- `domains/tutoring/graph/nodes.py` — `load_context`, `route_intent`, `diagnose_state`, `select_action` (no LLM yet)
- `infrastructure/llm/provider.py` — `get_chat_model()` factory
- `infrastructure/llm/base.py` — timeout + retry wrapper
- LangGraph graph definition and compile
- Graph invocation via a stub FastAPI endpoint
- Node unit tests with mocked state and services

### Day 5 — Sessions and Short-Term Memory
- `domains/memory/` — Session, Message SQLAlchemy models
- Session create/resume service
- Recent-message retrieval (last N messages for context window)
- LangGraph Postgres checkpointer wired to session
- Session-aware graph invocation
- Tests: session creation, message persistence, context window retrieval

### Day 6 — Mathematics Assessment Engine
- `domains/assessment/` — Exercise, ExerciseAttempt models
- `domains/assessment/services/evaluator.py` — SymPy normalization + verification
- `domains/assessment/services/parser.py` — raw answer → SymPy expression
- `evaluate_answer` graph node wired to evaluator
- Assessment API endpoint (`POST /api/v1/sessions/{id}/answer`)
- Tests: correct, incorrect, ambiguous, unparseable, slow-expression timeout

### Day 7 — Mastery Tracking
- `student_topic_mastery` and `mastery_updates` SQLAlchemy models
- Mastery heuristic service (delta formula, clamp, idempotency guard)
- `update_memory` graph node — mastery write path
- Mastery retrieval service (used by `load_context`)
- Tests: score updates, one-attempt-one-update invariant, duplicate submission safety

### Day 8 — Misconception Recording and Long-Term Memory
- `Misconception`, `StudentMisconception` models
- Misconception detection in `evaluate_answer` (LLM-assisted, low confidence)
- Upsert in `update_memory`
- Memory retrieval service (recent misconceptions for context window)
- `learning_events` append-only logger
- Student data isolation tests

### Day 9 — Personalized Teaching Decisions
- `generate_response` node wired to real LLM via provider abstraction
- Subject prompt templates (math) for all 8 teaching actions
- Prerequisite-aware action selection (full rule table from ai-workflow.md)
- `compose_final_response` node
- End-to-end single-turn integration test (mocked LLM)

### Day 10 — Complete Tutoring Workflow
- Full graph integration: both paths (conversation + answer)
- Multi-turn session test (diagnose → practice → evaluate → adapt)
- Cross-session continuity test (new session loads saved mastery)
- Next-step recommendation in response metadata
- Personalization observable in logged response differences between students

### Day 11 — Evaluation and Reliability
- Evaluation dataset: 20 math question/answer pairs covering correct, incorrect, ambiguous
- Assessment engine accuracy test (all 20 cases)
- Tutoring behavior tests: low mastery → diagnostic action, prereq gap → redirect
- LLM error handling: timeout, malformed output, retry, fallback
- Structured logging with request + session trace IDs
- Token usage logging per LLM call

### Day 12 — Final Integration and v0.1 Release
- End-to-end demo script (`scripts/demo.py`) executing the 12-step DoD scenario
- `README.md` — setup, running locally, running tests, demo walkthrough
- `docs/progress.md` final update
- Known limitations recorded
- v0.2 backlog
- Release checklist signed off

---

## v0.2 Backlog (not in scope for v0.1)

- Real JWT authentication and user registration
- pgvector semantic memory retrieval
- Multiple subjects (Physics, Chemistry)
- Streaming LLM responses (Server-Sent Events)
- Anthropic Claude provider behind the abstraction
- Advanced knowledge tracing (BKT or IRT)
- Teacher/admin dashboard API
- Rate limiting and cost controls
- Production deployment (cloud, reverse proxy, managed DB)
