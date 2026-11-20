# MentorOS v0.1 — AI Tutoring Workflow

## Overview

A single stateful LangGraph workflow. One graph instance per tutoring turn; session continuity is maintained via LangGraph checkpointing keyed on `(student_id, session_id)`.

The graph distinguishes two entry paths:
- **Conversation turn**: student sends a message.
- **Answer submission**: student submits an answer to an exercise.

Both paths share the same state and traverse overlapping nodes; they diverge at the `route_intent` conditional edge.

---

## Typed Graph State

```python
class TutoringState(TypedDict):
    # Identity
    student_id: str
    session_id: str
    subject_code: str           # "math" in v0.1

    # Input
    student_message: str
    intent: str                 # "question" | "answer" | "clarification"

    # Loaded context (populated by load_context node)
    student_profile: dict       # name, created_at
    topic_mastery: dict         # {topic_code: float}  — only relevant topics
    recent_misconceptions: list # [{code, topic, confidence, evidence_count}]
    recent_messages: list       # last N messages [{role, content}]

    # Curriculum context
    current_topic_code: str | None
    current_topic_id: str | None
    prerequisite_gap: str | None  # topic_code of an unmet prerequisite, if any

    # Active exercise (populated when asking a practice question)
    active_exercise_id: str | None
    active_exercise_text: str | None
    expected_answer: str | None   # kept server-side only; never sent to student

    # Diagnosis and planning
    diagnostic_signal: str      # "unknown" | "low" | "medium" | "high"
    selected_action: str        # see Teaching Actions below

    # Evaluation result (populated on answer submission path)
    evaluation_result: str | None   # "correct" | "incorrect" | "ambiguous"
    evaluation_detail: str | None   # brief rationale for incorrect/ambiguous
    attempt_id: str | None

    # Output
    assistant_response: str
    mastery_updated: bool
```

**Design rules:**
- State holds IDs and scalars, not full ORM objects.
- Nodes load data themselves from the database via service interfaces.
- No field stores data that would exceed ~1KB (no raw exercise banks, no full prompt text).

---

## Teaching Actions

The `selected_action` field takes one of these values. The `generate_response` node uses it to select the right prompt template.

| action | meaning |
|---|---|
| `explain` | Explain the concept at the student's level |
| `diagnose` | Ask a targeted diagnostic question |
| `practice` | Present a practice question |
| `hint` | Provide a hint for the current exercise |
| `review_prerequisite` | Redirect to an unmet prerequisite topic |
| `worked_example` | Walk through a fully solved example |
| `advance` | Acknowledge mastery; introduce the next concept |
| `fallback` | Generic helpful response (LLM recovery path) |

---

## Nodes

### 1. `load_context`
**Type:** Deterministic (DB calls, no LLM)

Loads everything needed to reason about the student before any LLM call runs.

Reads:
- Student profile from `students`.
- Mastery scores for the current topic and its direct prerequisites from `student_topic_mastery`.
- Recent misconceptions (evidence_count ≥ 1) for the current topic from `student_misconceptions`.
- Last 6 messages from `messages` for this session.
- Resolves `current_topic_code` from recent messages or the student's message (simple keyword/intent heuristic — no LLM needed here).

Populates: `student_profile`, `topic_mastery`, `recent_misconceptions`, `recent_messages`, `current_topic_code`, `current_topic_id`.

Failure mode: if student or session not found, raises `StudentNotFoundError` — handled at the FastAPI layer, not inside the graph.

---

### 2. `route_intent`
**Type:** Conditional edge (no separate node)

Reads `student_message` and `active_exercise_id`. Branches:
- If `active_exercise_id` is set and the message looks like a numeric/algebraic answer → `evaluate_answer`.
- Otherwise → `diagnose_state`.

This is a simple heuristic (regex + context check), not an LLM call. Keeps the happy path fast.

---

### 3. `diagnose_state`
**Type:** Deterministic first; LLM-assisted only when necessary

Determines the diagnostic signal:
- If `topic_mastery[current_topic]` is unknown → `"unknown"`.
- If mastery < 0.3 → `"low"`.
- If mastery < 0.65 → `"medium"`.
- Otherwise → `"high"`.

Checks prerequisites: if a required prerequisite has mastery < 0.4, sets `prerequisite_gap`.

No LLM call in this node. The mastery signal drives action selection deterministically first.

Populates: `diagnostic_signal`, `prerequisite_gap`.

---

### 4. `select_action`
**Type:** Deterministic rules; LLM consulted only for ambiguous cases

Rule table (evaluated top-to-bottom, first match wins):

| condition | selected_action |
|---|---|
| `prerequisite_gap` is set | `review_prerequisite` |
| `diagnostic_signal == "unknown"` and no recent messages on topic | `diagnose` |
| `diagnostic_signal == "low"` | `explain` or `worked_example` (alternating) |
| `diagnostic_signal == "medium"` and student asked a question | `explain` |
| `diagnostic_signal == "medium"` and no question asked | `practice` |
| `diagnostic_signal == "high"` | `practice` or `advance` |
| student message contains "hint" | `hint` |
| else | LLM decides from {explain, diagnose, practice} |

The LLM branch uses a small structured prompt with the student message, mastery, and misconceptions. Output is validated against the allowed action enum; if invalid, falls back to `explain`.

Populates: `selected_action`.

---

### 5. `generate_response`
**Type:** LLM call

The main teaching response. Uses the subject's prompt template for `selected_action`.

Context passed to the LLM:
- Student name (if set).
- Current topic name and difficulty.
- Mastery signal (not the raw score — a qualitative label: "new to this", "developing", "solid").
- Up to 3 recent misconceptions (descriptions only, not raw DB records).
- Last 6 messages (conversation context).
- Instructional objective derived from `selected_action`.

If `selected_action == "practice"`: the node also selects an exercise from `exercises` for the current topic (by difficulty matched to mastery), saves `active_exercise_id` and `active_exercise_text` to state, and includes the question in the response. `expected_answer` is saved to state but never included in the response text.

Output: `assistant_response` (plain text, the student reads this).

Retry: up to 2 retries on timeout or malformed output; `fallback` action used on second failure.

---

### 6. `evaluate_answer`
**Type:** Deterministic (SymPy) first; LLM-assisted fallback

Entered from the `route_intent` conditional edge when the student submits an answer.

Steps:
1. Loads `active_exercise_id` → fetches `expected_answer` from DB (not from state to prevent tampering).
2. Normalizes `student_message` via the assessment service (strips whitespace, handles "x=3" and "3" equivalence, etc.).
3. Runs SymPy `simplify(student_expr - expected_expr) == 0`.
4. If SymPy raises (unparseable input) → result is `"ambiguous"`.
5. If result is `"incorrect"`: runs a small LLM call to identify whether a known misconception pattern matches. Result recorded with low confidence (0.4); evidence_count incremented if already exists.

Records an `exercise_attempt` row. Populates: `evaluation_result`, `evaluation_detail`, `attempt_id`.

---

### 7. `update_memory`
**Type:** Deterministic (DB writes only)

Runs after both paths (conversation turn and answer submission).

Writes:
- The assistant message to `messages`.
- If `attempt_id` is set: updates `student_topic_mastery` via the mastery heuristic (see below), inserts a `mastery_updates` audit row, sets `mastery_updated = True`. The unique constraint on `mastery_updates.attempt_id` makes this idempotent.
- If a misconception was identified: upserts `student_misconceptions`.
- Appends a `learning_events` row.

The mastery heuristic:
```
delta = base_delta(result) * difficulty_weight * recency_weight
new_score = clamp(old_score + delta, 0.0, 1.0)
```
Where:
- `base_delta`: +0.08 correct, -0.04 incorrect, 0 ambiguous.
- `difficulty_weight`: scales delta down for easy questions (difficulty 1-3), up slightly for hard ones (difficulty 8-10).
- `recency_weight`: slight boost when last attempt was > 7 days ago (spaced repetition signal).

One correct answer on a difficulty-5 question from a 0.0 baseline yields mastery ≈ 0.08. Reaching 0.65 ("solid") requires consistent correct performance.

---

### 8. `compose_final_response`
**Type:** Deterministic

Packages `assistant_response` with any metadata the API layer needs (session_id, updated mastery for the topic, next recommended action hint). No LLM call.

This is a thin node — the response text was already generated in `generate_response`; this just prepares the structured API output.

---

## Graph Edges

```
load_context
    → route_intent (conditional)
        → diagnose_state → select_action → generate_response → update_memory → compose_final_response
        → evaluate_answer → update_memory → compose_final_response
```

`update_memory` and `compose_final_response` are shared by both paths.

---

## Checkpointing Strategy

LangGraph's built-in Postgres checkpointer keyed on `thread_id = f"{student_id}:{session_id}"`.

What is checkpointed: the full `TutoringState` at the end of each turn (after `compose_final_response`). This means `active_exercise_id` and `active_exercise_text` survive across turns within a session, so the student can submit an answer on a later message.

What is NOT checkpointed: `expected_answer` (fetched from DB each evaluation, never persisted in checkpoint). The checkpoint contains no sensitive answer material.

---

## Loop Prevention

The graph has no cycles. It is a DAG per turn. Stateful continuity is managed by checkpointing between turns, not by looping within a turn. This eliminates runaway execution risk.

---

## Testability

Every node function takes `TutoringState` and a `services` container (injected). Tests pass a pre-populated state dict and a mock services container. No real DB or LLM calls needed in unit tests.

The LLM abstraction means swapping `ChatOllama` for a deterministic mock is a one-line change in the services container.
