# MentorOS v0.1 — Database Schema

PostgreSQL via SQLAlchemy 2.x async. Migrations managed by Alembic. Student data isolated by `student_id` on every student-owned table.

## v0.1 Tables

### `students`
The identity record. Stub-auth: no password column yet.

| column | type | notes |
|---|---|---|
| id | UUID PK | |
| display_name | text | nullable |
| created_at | timestamptz | default now() |

### `subjects`
Mathematics only in v0.1.

| column | type | notes |
|---|---|---|
| id | UUID PK | |
| name | text unique | "Mathematics" |
| code | text unique | "math" |

### `topics`
A topic is a teachable unit within a subject.

| column | type | notes |
|---|---|---|
| id | UUID PK | |
| subject_id | UUID FK → subjects.id | |
| code | text unique | e.g. "linear_equations" |
| name | text | |
| difficulty | smallint | 1-10, used by mastery heuristic |
| description | text | |

### `topic_prerequisites`
Self-referential many-to-many on topics. Acyclic; enforced in application code, not a DB constraint.

| column | type | notes |
|---|---|---|
| topic_id | UUID FK → topics.id | |
| prerequisite_id | UUID FK → topics.id | |
| PK | (topic_id, prerequisite_id) | |

### `tutoring_sessions`
A tutoring conversation. Group of messages.

| column | type | notes |
|---|---|---|
| id | UUID PK | |
| student_id | UUID FK → students.id | indexed |
| subject_id | UUID FK → subjects.id | |
| started_at | timestamptz | default now() |
| ended_at | timestamptz | nullable |

### `messages`
The conversation log. Both student and assistant messages.

| column | type | notes |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → tutoring_sessions.id | indexed |
| student_id | UUID | denormalized for scoped queries; indexed |
| role | text | "student" \| "assistant" |
| content | text | |
| created_at | timestamptz | default now() |

### `exercises`
A practice question derived from a template. Owned by curriculum, not by a student.

| column | type | notes |
|---|---|---|
| id | UUID PK | |
| topic_id | UUID FK → topics.id | |
| question_text | text | rendered question |
| answer_expression | text | canonical correct answer, SymPy-parseable |
| difficulty | smallint | 1-10 |
| metadata | jsonb | variable name bindings, tolerances, etc. |

### `exercise_attempts`
A student's attempt at an exercise. The authoritative event source for mastery updates.

| column | type | notes |
|---|---|---|
| id | UUID PK | also the idempotency key for mastery updates |
| exercise_id | UUID FK → exercises.id | |
| student_id | UUID | denormalized, indexed |
| session_id | UUID FK → tutoring_sessions.id | |
| student_answer | text | raw answer as submitted |
| result | text | "correct" \| "incorrect" \| "ambiguous" |
| hints_used | int | default 0 |
| created_at | timestamptz | default now() |

### `student_topic_mastery`
One row per student per topic. The derived, auditable mastery estimate.

| column | type | notes |
|---|---|---|
| student_id | UUID | composite PK with topic_id |
| topic_id | UUID | |
| mastery_score | numeric(4,3) | 0.000-1.000 |
| attempts_count | int | default 0 |
| last_attempt_at | timestamptz | nullable |
| updated_at | timestamptz | default now() |

### `mastery_updates`
Audit log for every mastery write. Never updated, only inserted.

| column | type | notes |
|---|---|---|
| id | UUID PK | |
| student_id | UUID | indexed |
| topic_id | UUID | |
| attempt_id | UUID FK → exercise_attempts.id | unique; enforces one mastery update per attempt |
| previous_score | numeric(4,3) | |
| new_score | numeric(4,3) | |
| created_at | timestamptz | default now() |

### `misconceptions`
A catalog of known misconception types per topic. Shared, not student-specific.

| column | type | notes |
|---|---|---|
| id | UUID PK | |
| topic_id | UUID FK → topics.id | |
| code | text | e.g. "sign_error", "distributive_vs_exponent" |
| description | text | |

### `student_misconceptions`
A student exhibiting a misconception. Confidence-gated; not surfaced until evidence_count >= 2.

| column | type | notes |
|---|---|---|
| id | UUID PK | |
| student_id | UUID | indexed |
| topic_id | UUID | |
| misconception_id | UUID FK → misconceptions.id | |
| confidence | numeric(4,3) | 0.000-1.000 |
| evidence_count | int | default 1 |
| first_seen_at | timestamptz | default now() |
| last_seen_at | timestamptz | default now() |
| UK | (student_id, misconception_id) | one row per pair |

### `learning_events`
Append-only event log for observability and replay. Not authoritative for state; derived tables are.

| column | type | notes |
|---|---|---|
| id | bigserial PK | |
| student_id | UUID | indexed |
| session_id | UUID | nullable |
| event_type | text | e.g. "attempt", "mastery_update", "misconception_observed" |
| idempotency_key | text unique | nullable; caller-supplied so retried writes don't duplicate events |
| payload | jsonb | event-specific data |
| created_at | timestamptz | default now() |

## Deferred to v0.2

### `student_memories` (pgvector)
Semantic memory table with an `embedding vector(1024)` column (qwen3-embedding:0.6b dimensions). Not created in the v0.1 migration: an unused table adds migration and maintenance cost with no benefit. It will get its own migration, which also runs `CREATE EXTENSION vector`, when semantic retrieval is built. The Docker image already ships pgvector 0.8.

## Implementation Notes (Day 3)

- ORM models live in their owning domain: `domains/<domain>/models.py`. `src/mentoros/models.py` imports all of them so Alembic sees the complete schema.
- Constraint names follow a fixed naming convention (`pk_`, `fk_`, `uq_`, `ck_`, `ix_`) so migrations are stable and reviewable.
- Student-owned tables use `ON DELETE CASCADE` from `students`, so deleting a student removes their learning data. Curriculum references use `RESTRICT` where deleting would orphan history.
- Enum-like text columns (`messages.role`, `exercise_attempts.result`) are guarded by CHECK constraints instead of PostgreSQL ENUM types, which are awkward to change in migrations.

## Invariants

- Every student-owned query filters by `student_id`. Enforced in repository layers, not relied upon from callers.
- One mastery update per attempt: `mastery_updates.attempt_id` is unique.
- Mastery is derived; `student_topic_mastery` holds the current value and is updated in the same transaction as the `mastery_updates` audit row.
- Misconceptions with `evidence_count < 2` are internal-only.
- Prerequisite graph is acyclic; validated in the curriculum seed loader.
