"""
Shared FastAPI dependencies.

Centralized dependency factories used across routers.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_tenant
from api.middleware.rate_limiter import check_rate_limit
from db.engine import get_db_session
from db.models.tenant import Tenant


async def get_authenticated_tenant(
    tenant: Tenant = Depends(get_current_tenant),
    _rate_limit: None = Depends(check_rate_limit),
) -> Tenant:
    """
    Combined dependency that:
    1. Authenticates the tenant via API key
    2. Checks rate limits

    Use this when you want both in one dependency.
    """
    return tenant
