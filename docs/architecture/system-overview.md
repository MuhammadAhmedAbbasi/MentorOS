# MentorOS v0.1 — System Overview

## High-Level Architecture

```
Student / HTTP Client
        |
        v
FastAPI (api/routes, dependencies)
        |
        v
Tutoring Application Service
        |
        v
LangGraph Tutoring Workflow
        |
        +---- Students domain (profile, identity)
        +---- Curriculum domain (topics, prerequisites)
        +---- Memory domain (sessions, history, mastery, misconceptions)
        +---- Assessment domain (math questions, SymPy verification)
        v
Response Generation
        |
        v
Student
```

## Domain Boundaries

### `domains/tutoring/` — Orchestration
Owns the LangGraph workflow and the teaching strategy logic. The only domain that calls the LLM for tutoring responses. Depends on the other four domains through service interfaces, never by importing their ORM models directly.

- `graph/` — LangGraph state, nodes, edges.
- `services/` — Teaching strategy selection, diagnostic reasoning.
- `schemas/` — Pydantic models for structured LLM outputs.
- `prompts/` — Versioned prompt templates (math-specific prompts live here in v0.1, behind a subject interface so Physics can plug in later).

### `domains/students/` — Student identity and profile
Owns student records and their current profile state. Stub-auth compatible: a student is created on first reference if absent.

### `domains/curriculum/` — Subject knowledge
Owns subjects, topics, prerequisites, learning objectives, and question templates. The only domain that holds math-specific content in v0.1; everything else is subject-agnostic. A `SubjectContext` interface lets the tutoring graph load subject-specific prompts and tools without hardcoding "math" into orchestration.

### `domains/memory/` — Learning memory
Owns sessions, messages, learning events, mastery, and misconceptions. Authoritative record of what a student has done and what the system believes they know. All queries scoped by `student_id`.

### `domains/assessment/` — Evaluation
Owns math question representation, answer normalization, SymPy verification, and attempt scoring. Deterministic by default; LLM-assisted only as a fallback for ambiguous open-ended answers.

## Dependency Rules

- `api/` depends on application services, not on domain internals.
- `tutoring/` depends on the other four domains through service interfaces.
- The other four domains do not depend on `tutoring/` or on each other where avoidable.
- No domain imports another domain's ORM models; it calls the owning domain's service.
- `infrastructure/` (database, llm, vector_store) is depended on by domains, never the reverse.

## Cross-Cutting

- `core/config.py` — settings loaded from environment.
- `core/logging.py` — structured logging with request/session IDs.
- `core/exceptions.py` — domain error hierarchy and FastAPI exception handlers.

## Subject Agnosticism

v0.1 ships Mathematics only, but the tutoring graph never branches on `if subject == "math"`. Instead it asks `curriculum/` for the active `SubjectContext`, which provides prompts and points to the right evaluation tool. Adding Physics later means a new `SubjectContext` implementation, not graph surgery.
