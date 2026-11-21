"""Health endpoint. Used for liveness checks and as the Day 2 smoke test."""

from __future__ import annotations

from fastapi import APIRouter

from mentoros import __version__

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe. Does not touch the database."""
    return {"status": "ok", "version": __version__}
