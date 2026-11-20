# MentorOS — Development Progress

## Current Status

**Day:** 1
**Task:** Complete
**Date:** 2026-11-20

---

## Day 1 — Requirements and Architecture Planning

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

### Files Created

- `docs/requirements.md`
- `docs/roadmap.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/database-schema.md`
- `docs/architecture/ai-workflow.md`
- `docs/decisions/ADR-001-technology-stack.md`
- `docs/decisions/ADR-002-llm-provider-abstraction.md`
- `pyproject.toml`

### Tests Performed

None yet — Day 1 is planning only.

### Outstanding Issues

None blocking Day 2.

---

## Day 2 — Project Foundation

**Status:** Not started

---

## Upcoming

See [roadmap.md](roadmap.md) for the full 12-day plan.
