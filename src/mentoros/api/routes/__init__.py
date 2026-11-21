"""API router aggregation. All route modules are registered here."""

from __future__ import annotations

from fastapi import APIRouter

from . import health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
