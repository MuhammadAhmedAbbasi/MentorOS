"""Curriculum: subjects, topics, prerequisite graph, misconception catalog.

Curriculum data is shared across students and contains no student data.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from mentoros.infrastructure.database.engine import Base
from mentoros.infrastructure.database.mixins import uuid_pk


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text, unique=True)


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 10", name="difficulty_range"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    subject_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subjects.id", ondelete="RESTRICT"), index=True
    )
    code: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    description: Mapped[str] = mapped_column(Text, default="")


class TopicPrerequisite(Base):
    """Directed edge: `topic_id` requires `prerequisite_id`.

    Acyclicity is validated in the seed loader, not by the database.
    """

    __tablename__ = "topic_prerequisites"
    __table_args__ = (
        CheckConstraint("topic_id <> prerequisite_id", name="no_self_reference"),
    )

    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    prerequisite_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )


class Misconception(Base):
    """Catalog of known misconception types for a topic. Not student-specific."""

    __tablename__ = "misconceptions"
    __table_args__ = (UniqueConstraint("topic_id", "code"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
