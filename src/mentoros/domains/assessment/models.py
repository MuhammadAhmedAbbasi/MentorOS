"""Assessment: exercises and student attempts.

`exercise_attempts` is the authoritative event source for mastery updates.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Integer, SmallInteger, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from mentoros.infrastructure.database.engine import Base
from mentoros.infrastructure.database.mixins import created_at, uuid_pk


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 10", name="difficulty_range"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True
    )
    question_text: Mapped[str] = mapped_column(Text)
    # Canonical answer, SymPy-parseable. Never sent to the student.
    answer_expression: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    # Variable bindings, tolerances, answer format hints.
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"
    __table_args__ = (
        CheckConstraint(
            "result IN ('correct', 'incorrect', 'ambiguous')", name="result_values"
        ),
        CheckConstraint("hints_used >= 0", name="hints_non_negative"),
    )

    # Also the idempotency key for the mastery update this attempt produces.
    id: Mapped[uuid.UUID] = uuid_pk()
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tutoring_sessions.id", ondelete="CASCADE"), index=True
    )
    student_answer: Mapped[str] = mapped_column(Text)
    result: Mapped[str] = mapped_column(Text)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = created_at()
