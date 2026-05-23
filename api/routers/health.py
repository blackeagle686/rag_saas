"""
Health check endpoints.

Unauthenticated — used for liveness probes and readiness checks.
"""

from __future__ import annotations

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import Settings, get_settings
from api.schemas.common import HealthResponse, ReadyResponse
from db.engine import get_db_session

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description="Basic health check — returns OK if the API is running.",
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")


@router.get(
    "/health/ready",
    response_model=ReadyResponse,
    summary="Readiness check",
    description="Checks connectivity to PostgreSQL, Redis, and Qdrant.",
)
async def health_ready(
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ReadyResponse:
    checks: dict[str, str] = {}

    # Check PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Check Redis
    try:
        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        await client.ping()
        await client.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    # Check Qdrant
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key or None,
            timeout=3,
        )
        client.get_collections()
        checks["qdrant"] = "ok"
    except Exception as e:
        checks["qdrant"] = f"error: {e}"

    # Overall status
    all_ok = all(v == "ok" for v in checks.values())
    status = "ok" if all_ok else "degraded"

    return ReadyResponse(status=status, checks=checks)
