"""Model registry: imports every ORM model so `Base.metadata` is complete.

Alembic and test fixtures import this module. It lives at the package root
because it depends on every domain; infrastructure must not import domains.
"""

from mentoros.domains.assessment.models import Exercise, ExerciseAttempt
from mentoros.domains.curriculum.models import Misconception, Subject, Topic, TopicPrerequisite
from mentoros.domains.memory.models import (
    LearningEvent,
    MasteryUpdate,
    Message,
    StudentMisconception,
    StudentTopicMastery,
    TutoringSession,
)
from mentoros.domains.students.models import Student
from mentoros.infrastructure.database.engine import Base

__all__ = [
    "Base",
    "Exercise",
    "ExerciseAttempt",
    "LearningEvent",
    "MasteryUpdate",
    "Message",
    "Misconception",
    "Student",
    "StudentMisconception",
    "StudentTopicMastery",
    "Subject",
    "Topic",
    "TopicPrerequisite",
    "TutoringSession",
]
