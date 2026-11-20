# MentorOS v0.1 — Requirements

## 1. Product Summary

MentorOS is an agentic AI-powered personalized learning system. For v0.1 it provides a persistent, adaptive mathematics tutor: a student converses with an AI teacher that retrieves their learning profile, diagnoses understanding, teaches at the right level, asks practice questions, evaluates answers with deterministic math verification, updates a mastery model, and remembers everything across sessions.

The core loop: **Observe → Diagnose → Plan → Teach → Practice → Evaluate → Update → Adapt**.

## 2. v0.1 Scope

### In scope
- Mathematics subject only.
- 10 seeded topics across two difficulty tiers.
- Student identification via stub auth (UUID in request header).
- Personalized tutoring conversations through a LangGraph workflow.
- Diagnostic questioning when understanding is unclear.
- Practice question generation and SymPy-based answer verification.
- Heuristic mastery tracking with auditable updates.
- Misconception recording with confidence and evidence.
- Structured learning memory in PostgreSQL.
- Cross-session continuity.
- API backend only (no frontend); tested via HTTP client.

### Out of scope
- Other subjects (architecture must not preclude them).
- Real authentication, authorization, or user registration.
- Frontend or UI.
- Video, voice, or document ingestion.
- pgvector semantic retrieval (prepared in schema but unused).
- Advanced knowledge tracing (BKT, IRT, DKT).
- Multi-agent collaboration.
- Analytics dashboards, parent or teacher views.
- Production deployment infrastructure.

## 3. Functional Requirements

### FR-1 — Student Identification
As a student, I want to be identified by a stable ID so the system can retrieve my learning profile.
**Acceptance criteria:**
- A request includes a student ID.
- The system loads the student's profile and current mastery state from PostgreSQL.
- If the student is new, a profile is initialized.

### FR-2 — Session Management
As a student, I want my interactions grouped into a tutoring session I can resume.
**Acceptance criteria:**
- A session can be created and referenced by ID.
- Messages and attempts belong to a session.
- A session can be resumed and its recent context retrieved.

### FR-3 — Personalized Tutoring Conversation
As a student, I want to ask for help with a math topic and receive a response tailored to my level.
**Acceptance criteria:**
- The workflow retrieves my profile, relevant memory, and current topic mastery.
- It selects an instructional action: explain, diagnose, practice, hint, or review prerequisite.
- The response reflects my demonstrated understanding, not a generic explanation.

### FR-4 — Diagnostic Questioning
As a student, when my understanding of a topic is unknown or low, I want the system to ask a diagnostic question before teaching.
**Acceptance criteria:**
- When topic mastery is unknown or below a threshold, the system can ask a targeted diagnostic question.
- The system does not assume a knowledge gap without evidence.

### FR-5 — Practice and Evaluation
As a student, I want to answer practice questions and have my answer evaluated reliably.
**Acceptance criteria:**
- The system presents a math question with a defined correct answer.
- It accepts my answer, normalizes it, and verifies correctness with SymPy.
- It distinguishes correct, incorrect, and ambiguous answers.
- It records the attempt with the question, my answer, and the result.

### FR-6 — Mastery Tracking
As a student, I want my topic mastery to update based on my performance.
**Acceptance criteria:**
- After each evaluated attempt, the mastery score for the relevant topic updates.
- The update uses a transparent heuristic: correctness, difficulty, attempts, hints, recency.
- Updates are auditable via an event history referencing the attempt.
- A single correct answer does not max out mastery.

### FR-7 — Misconception Recording
As a student, when I show a recurring error pattern, I want it recorded so future sessions adapt.
**Acceptance criteria:**
- Misconceptions are recorded with a confidence level and supporting evidence.
- Low-confidence misconceptions are not surfaced to me until confirmed by repeated evidence.

### FR-8 — Learning History Persistence
As a student, I want my learning history saved so it survives restarts.
**Acceptance criteria:**
- Sessions, messages, attempts, mastery updates, and misconceptions persist in PostgreSQL.
- Data survives process restarts.

### FR-9 — Context-Aware Memory Retrieval
As a student, I want the system to use my past learning when responding.
**Acceptance criteria:**
- The tutoring workflow retrieves relevant prior attempts, misconceptions, and mastery before generating a response.
- Retrieval is scoped to my student ID.

### FR-10 — Personalized Next Steps
As a student, I want the system to recommend what to study next based on my state.
**Acceptance criteria:**
- The system can recommend a next topic or action using mastery and prerequisite relationships.

### FR-11 — Cross-Session Continuity
As a student, I want a new session to remember my previous learning.
**Acceptance criteria:**
- A new session loads my persisted mastery, misconceptions, and history.
- The first response in a new session reflects my saved state.

## 4. Non-Functional Requirements

- **NFR-1 Latency:** A tutoring turn (request to first response) targets a soft bound; local LLM latency is hardware-dependent and must be measured, not assumed.
- **NFR-2 Testing:** Unit tests for graph nodes, the math evaluator, and the mastery updater; integration tests for the full loop; graph tests use a mocked LLM so they run without a model.
- **NFR-3 Data isolation:** All student data queries are scoped by student_id; no cross-student access.
- **NFR-4 Reliability:** Every LLM call has a timeout and bounded retries with a defined fallback per node.
- **NFR-5 Observability:** Structured logs with request and session IDs; errors carry context.
- **NFR-6 Configuration:** Secrets and environment-specific values come from environment variables or `.env`; no secrets in code.
- **NFR-7 Maintainability:** Type hints throughout; ruff clean; small focused functions; no hardcoded math logic in core orchestration.
- **NFR-8 Portability:** LLM access goes through a provider abstraction so Ollama (now) and Anthropic (later) plug in behind one interface.

## 5. Constraints and Assumptions

- v0.1 is Mathematics only; core orchestration must not hardcode math-specific logic.
- LLM: local Ollama with a Qwen agentic model for development; Anthropic added later behind the same abstraction.
- Authentication is a stub (UUID in request header) for v0.1.
- Curriculum: 10 seeded mathematics topics with prerequisite relationships.
- No frontend in v0.1; the API is exercised via HTTP client and automated tests.
- pgvector is prepared in schema but no embedding calls run in v0.1.

## 6. Definition of Done for v0.1

The end-to-end demonstration scenario, backed by real persisted data:
1. A student starts a tutoring session.
2. The system retrieves their learning profile.
3. The student asks for help with a math topic.
4. The system identifies an appropriate starting point using prerequisites.
5. The AI teaches or asks a diagnostic question.
6. The student submits an answer.
7. The system evaluates the answer with SymPy.
8. The system records the learning event.
9. Mastery updates appropriately.
10. The AI adapts its next action.
11. The student returns in a later session.
12. The system uses saved history to personalize the new session.
