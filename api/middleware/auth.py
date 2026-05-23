"""
API Key authentication middleware.

Extracts the API key from the Authorization header,
verifies it against stored bcrypt hashes, and attaches
the tenant to the request state.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import Settings, get_settings
from core.exceptions import InvalidAPIKeyError, MissingAPIKeyError, TenantSuspendedError
from core.security import verify_api_key
from db.engine import get_db_session
from db.models.tenant import Tenant, TenantStatus
from db.repositories.api_key_repo import ApiKeyRepository
from db.repositories.tenant_repo import TenantRepository


async def get_current_tenant(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> Tenant:
    """
    FastAPI dependency that authenticates the request via API key.

    Flow:
    1. Extract key from Authorization: Bearer <key>
    2. Find matching active keys by prefix
    3. Verify bcrypt hash
    4. Check tenant status
    5. Update last_used timestamp
    6. Return tenant

    Raises:
        MissingAPIKeyError: No Authorization header
        InvalidAPIKeyError: Key not found or inactive
        TenantSuspendedError: Tenant account is suspended
    """
    # 1. Extract key from header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise MissingAPIKeyError()

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise MissingAPIKeyError(detail="Authorization header must be: Bearer <api_key>")

    raw_key = parts[1].strip()
    if not raw_key:
        raise MissingAPIKeyError()

    # 2. Extract prefix for faster lookup
    prefix = settings.api_key_prefix
    if not raw_key.startswith(prefix):
        raise InvalidAPIKeyError(detail="API key must start with the correct prefix.")

    # 3. Find candidate keys and verify
    key_repo = ApiKeyRepository(db)
    candidates = await key_repo.get_active_keys_by_prefix(prefix)

    matched_key = None
    for candidate in candidates:
        if verify_api_key(raw_key, candidate.key_hash):
            matched_key = candidate
            break

    if matched_key is None:
        raise InvalidAPIKeyError()

    # 4. Load tenant
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id(matched_key.tenant_id)

    if tenant is None:
        raise InvalidAPIKeyError(detail="Tenant associated with this key no longer exists.")

    if tenant.status == TenantStatus.SUSPENDED:
        raise TenantSuspendedError()

    if tenant.status == TenantStatus.CANCELLED:
        raise InvalidAPIKeyError(detail="This account has been cancelled.")

    # 5. Update last_used (fire and forget — don't block the response)
    await key_repo.update_last_used(matched_key.id)

    # 6. Attach tenant to request state for downstream use
    request.state.tenant = tenant
    request.state.api_key_id = matched_key.id

    return tenant
