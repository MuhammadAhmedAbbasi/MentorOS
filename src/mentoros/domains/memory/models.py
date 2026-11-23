"""Learning memory: sessions, messages, mastery, misconceptions, events.

Every table here is student-owned and carries `student_id` so queries can be
scoped to one student without joins. Deleting a student cascades here.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from mentoros.infrastructure.database.engine import Base
from mentoros.infrastructure.database.mixins import created_at, uuid_pk

SCORE = Numeric(4, 3)  # 0.000 - 1.000


class TutoringSession(Base):
    __tablename__ = "tutoring_sessions"
    __table_args__ = (
        # Needed so Message and ExerciseAttempt can reference (student_id, id) as a compound FK,
        # preventing a message from referencing a session owned by a different student.
        UniqueConstraint("student_id", "id", name="uq_tutoring_sessions_student_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    started_at: Mapped[datetime] = created_at()
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('student', 'assistant')", name="role_values"),
        # Compound FK: session_id must belong to this message's student.
        # Prevents a message referencing a session owned by a different student.
        ForeignKeyConstraint(
            ["student_id", "session_id"],
            ["tutoring_sessions.student_id", "tutoring_sessions.id"],
            ondelete="CASCADE",
            name="fk_messages_student_session",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at()


class StudentTopicMastery(Base):
    """Current mastery estimate. Derived from `mastery_updates`."""

    __tablename__ = "student_topic_mastery"
    __table_args__ = (
        CheckConstraint("mastery_score BETWEEN 0 AND 1", name="score_range"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), primary_key=True
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    mastery_score: Mapped[Decimal] = mapped_column(SCORE, default=Decimal(0))
    attempts_count: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MasteryUpdate(Base):
    """Append-only audit log. One row per attempt, enforced by unique attempt_id."""

    __tablename__ = "mastery_updates"

    id: Mapped[uuid.UUID] = uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercise_attempts.id", ondelete="CASCADE"), unique=True
    )
    previous_score: Mapped[Decimal] = mapped_column(SCORE)
    new_score: Mapped[Decimal] = mapped_column(SCORE)
    created_at: Mapped[datetime] = created_at()


class StudentMisconception(Base):
    """A misconception observed in a student. Surfaced only when evidence_count >= 2."""

    __tablename__ = "student_misconceptions"
    __table_args__ = (
        UniqueConstraint("student_id", "misconception_id"),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="confidence_range"),
        CheckConstraint("evidence_count >= 1", name="evidence_positive"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    misconception_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("misconceptions.id", ondelete="CASCADE")
    )
    confidence: Mapped[Decimal] = mapped_column(SCORE)
    evidence_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = created_at()
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class LearningEvent(Base):
    """Append-only event log for observability and replay. Not authoritative state."""

    __tablename__ = "learning_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tutoring_sessions.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(Text)
    # Caller-supplied key so retried writes do not create duplicate events.
    idempotency_key: Mapped[str | None] = mapped_column(Text, unique=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = created_at()
