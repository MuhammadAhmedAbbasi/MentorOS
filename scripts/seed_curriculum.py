"""Seed the v0.1 curriculum into the database configured by DATABASE_URL.

Usage:
    python scripts/seed_curriculum.py

Safe to run repeatedly. Run `alembic upgrade head` first.
"""

from __future__ import annotations

import asyncio

from mentoros.domains.curriculum.data.mathematics import MATHEMATICS
from mentoros.domains.curriculum.seed import seed_subject
from mentoros.infrastructure.database.engine import dispose_engine, get_sessionmaker


async def main() -> None:
    async with get_sessionmaker()() as session, session.begin():
        counts = await seed_subject(session, MATHEMATICS)
    await dispose_engine()
    print(f"Seeded {MATHEMATICS.name}: {counts['topics']} topics, "
          f"{counts['prerequisites']} prerequisite edges")


if __name__ == "__main__":
    asyncio.run(main())
