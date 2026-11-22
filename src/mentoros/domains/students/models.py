"""Student identity. Stub auth in v0.1: no credentials stored."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from mentoros.infrastructure.database.engine import Base
from mentoros.infrastructure.database.mixins import created_at, uuid_pk


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = uuid_pk()
    display_name: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at()
