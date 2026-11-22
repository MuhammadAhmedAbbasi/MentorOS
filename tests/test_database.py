"""Database integration tests against a real PostgreSQL (TEST_DATABASE_URL).

Each test runs inside a transaction that is rolled back, so tests never see
each other's data and the test database stays clean.
"""

from __future__ import annotations

import os
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from mentoros.domains.curriculum.data.mathematics import MATHEMATICS
from mentoros.domains.curriculum.seed import (
    CurriculumValidationError,
    SubjectSpec,
    TopicSpec,
    seed_subject,
    validate,
)
from mentoros.models import (
    Base,
    Exercise,
    ExerciseAttempt,
    MasteryUpdate,
    Message,
    Student,
    StudentTopicMastery,
    Subject,
    Topic,
    TopicPrerequisite,
    TutoringSession,
)

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://mentoros:mentoros@localhost:5433/mentoros_test"
)



@pytest.fixture
async def session():
    engine = create_async_engine(TEST_DATABASE_URL)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except OSError as exc:  # connection refused / reset
        await engine.dispose()
        pytest.skip(f"test database unavailable: {exc}")

    async with engine.connect() as conn:
        trans = await conn.begin()
        # Savepoints let a test hit an IntegrityError and keep going.
        s = AsyncSession(bind=conn, join_transaction_mode="create_savepoint")
        try:
            yield s
        finally:
            await s.close()
            await trans.rollback()
    await engine.dispose()


async def _seeded(session: AsyncSession) -> dict[str, uuid.UUID]:
    await seed_subject(session, MATHEMATICS)
    rows = await session.execute(select(Topic.code, Topic.id))
    return dict(rows.all())


async def _student_session(session: AsyncSession) -> tuple[Student, TutoringSession]:
    subject_id = await session.scalar(select(Subject.id).where(Subject.code == "math"))
    student = Student(display_name="Test Student")
    session.add(student)
    await session.flush()
    tutoring = TutoringSession(student_id=student.id, subject_id=subject_id)
    session.add(tutoring)
    await session.flush()
    return student, tutoring


# ── Curriculum validation (no database needed) ─────────────────────────────


def test_v01_curriculum_is_valid():
    validate(MATHEMATICS)
    assert len(MATHEMATICS.topics) == 10


def test_validate_rejects_cycle():
    spec = SubjectSpec("x", "X", [
        TopicSpec("a", "A", 1, prerequisites=["b"]),
        TopicSpec("b", "B", 1, prerequisites=["a"]),
    ])
    with pytest.raises(CurriculumValidationError, match="cycle"):
        validate(spec)


def test_validate_rejects_unknown_prerequisite():
    spec = SubjectSpec("x", "X", [TopicSpec("a", "A", 1, prerequisites=["missing"])])
    with pytest.raises(CurriculumValidationError, match="unknown prerequisite"):
        validate(spec)


# ── Seeding ─────────────────────────────────────────────────────────────────


async def test_seed_creates_topics_and_edges(session):
    ids = await _seeded(session)
    assert len(ids) == 10
    edges = await session.scalar(select(func.count()).select_from(TopicPrerequisite))
    assert edges == 11

    quad_prereqs = await session.scalars(
        select(Topic.code)
        .join(TopicPrerequisite, TopicPrerequisite.prerequisite_id == Topic.id)
        .where(TopicPrerequisite.topic_id == ids["quadratic_equations"])
    )
    assert sorted(quad_prereqs) == ["factoring", "linear_equations"]


async def test_seed_is_idempotent(session):
    await _seeded(session)
    await _seeded(session)
    assert await session.scalar(select(func.count()).select_from(Topic)) == 10
    assert await session.scalar(select(func.count()).select_from(TopicPrerequisite)) == 11


# ── Constraints ─────────────────────────────────────────────────────────────


async def test_one_mastery_update_per_attempt(session):
    """The unique attempt_id makes duplicate mastery writes impossible."""
    ids = await _seeded(session)
    student, tutoring = await _student_session(session)
    exercise = Exercise(
        topic_id=ids["linear_equations"], question_text="Solve 2x + 4 = 10",
        answer_expression="3", difficulty=4,
    )
    session.add(exercise)
    await session.flush()
    attempt = ExerciseAttempt(
        exercise_id=exercise.id, student_id=student.id, session_id=tutoring.id,
        student_answer="x = 3", result="correct",
    )
    session.add(attempt)
    await session.flush()

    def update() -> MasteryUpdate:
        return MasteryUpdate(
            student_id=student.id, topic_id=ids["linear_equations"], attempt_id=attempt.id,
            previous_score=Decimal(0), new_score=Decimal("0.08"),
        )

    session.add(update())
    await session.flush()
    session.add(update())
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_mastery_score_must_be_between_0_and_1(session):
    ids = await _seeded(session)
    student, _ = await _student_session(session)
    session.add(StudentTopicMastery(
        student_id=student.id, topic_id=ids["fractions"], mastery_score=Decimal("1.5"),
    ))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_message_role_is_constrained(session):
    await _seeded(session)
    student, tutoring = await _student_session(session)
    session.add(Message(
        session_id=tutoring.id, student_id=student.id, role="system", content="x",
    ))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_deleting_student_cascades_to_their_data(session):
    """Supports data deletion requests: removing a student removes their records."""
    await _seeded(session)
    student, tutoring = await _student_session(session)
    session.add(Message(
        session_id=tutoring.id, student_id=student.id, role="student", content="hi",
    ))
    await session.flush()

    await session.execute(text("DELETE FROM students WHERE id = :id"), {"id": student.id})
    remaining = await session.scalar(
        select(func.count()).select_from(Message).where(Message.student_id == student.id)
    )
    assert remaining == 0
