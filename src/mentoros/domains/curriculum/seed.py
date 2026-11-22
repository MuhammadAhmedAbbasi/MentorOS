"""Curriculum seed loader: validates a subject spec and upserts it.

Idempotent: running it twice leaves the database unchanged. Topics are matched
by `code`, so re-running after editing a description updates it in place.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from mentoros.domains.curriculum.models import Subject, Topic, TopicPrerequisite


@dataclass(frozen=True)
class TopicSpec:
    code: str
    name: str
    difficulty: int
    description: str = ""
    prerequisites: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SubjectSpec:
    code: str
    name: str
    topics: list[TopicSpec]


class CurriculumValidationError(ValueError):
    """The curriculum spec is internally inconsistent."""


def validate(spec: SubjectSpec) -> None:
    """Check unique codes, known prerequisites, difficulty range, and no cycles."""
    codes = [t.code for t in spec.topics]
    if len(codes) != len(set(codes)):
        raise CurriculumValidationError(f"duplicate topic codes in {spec.code}")

    known = set(codes)
    for topic in spec.topics:
        if not 1 <= topic.difficulty <= 10:
            raise CurriculumValidationError(f"{topic.code}: difficulty must be 1-10")
        for prereq in topic.prerequisites:
            if prereq not in known:
                raise CurriculumValidationError(f"{topic.code}: unknown prerequisite {prereq}")
            if prereq == topic.code:
                raise CurriculumValidationError(f"{topic.code}: cannot require itself")

    _check_acyclic({t.code: t.prerequisites for t in spec.topics})


def _check_acyclic(graph: dict[str, list[str]]) -> None:
    """Depth-first search; raises on the first cycle found."""
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in done:
            return
        if node in visiting:
            cycle = " -> ".join([*path[path.index(node):], node])
            raise CurriculumValidationError(f"prerequisite cycle: {cycle}")
        visiting.add(node)
        for prereq in graph[node]:
            visit(prereq, [*path, node])
        visiting.remove(node)
        done.add(node)

    for node in graph:
        visit(node, [])


async def seed_subject(session: AsyncSession, spec: SubjectSpec) -> dict[str, int]:
    """Validate and upsert one subject with its topics and prerequisite edges.

    The caller owns the transaction (commit/rollback).
    """
    validate(spec)

    subject_id = await session.scalar(
        insert(Subject)
        .values(code=spec.code, name=spec.name)
        .on_conflict_do_update(index_elements=[Subject.code], set_={"name": spec.name})
        .returning(Subject.id)
    )

    for t in spec.topics:
        await session.execute(
            insert(Topic)
            .values(
                subject_id=subject_id,
                code=t.code,
                name=t.name,
                difficulty=t.difficulty,
                description=t.description,
            )
            .on_conflict_do_update(
                index_elements=[Topic.code],
                set_={"name": t.name, "difficulty": t.difficulty, "description": t.description},
            )
        )

    rows = await session.execute(select(Topic.code, Topic.id).where(Topic.subject_id == subject_id))
    ids = dict(rows.all())

    # Replace this subject's edges so removed prerequisites disappear too.
    await session.execute(
        delete(TopicPrerequisite).where(TopicPrerequisite.topic_id.in_(ids.values()))
    )
    edges = [
        {"topic_id": ids[t.code], "prerequisite_id": ids[p]}
        for t in spec.topics
        for p in t.prerequisites
    ]
    if edges:
        await session.execute(insert(TopicPrerequisite), edges)

    return {"topics": len(spec.topics), "prerequisites": len(edges)}
