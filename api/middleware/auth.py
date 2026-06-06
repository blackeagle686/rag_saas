"""
Authentication middleware.

Extracts the API key or JWT from the Authorization header,
verifies it, and attaches the tenant to the request state.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.config import Settings, get_settings
from core.exceptions import InvalidAPIKeyError, MissingAPIKeyError, TenantSuspendedError
from core.security import verify_api_key, decode_access_token
from db.engine import get_db_session
from db.models.tenant import Tenant, TenantStatus
from db.models.api_key import ApiKey
from db.repositories.api_key_repo import ApiKeyRepository
from db.repositories.tenant_repo import TenantRepository


async def get_current_tenant(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> Tenant:
    """
    FastAPI dependency that authenticates the request via API key OR JWT.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise MissingAPIKeyError(detail="Missing Authorization header")

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise MissingAPIKeyError(detail="Authorization header must be: Bearer <token>")

    token = parts[1].strip()
    if not token:
        raise MissingAPIKeyError()

    tenant_repo = TenantRepository(db)

    # 1. Check if JWT (usually much longer than API keys and starts with eyJ)
    if token.startswith("eyJ"):
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(status_code=401, detail="Invalid or expired JWT token")
        
        tenant_id = uuid.UUID(payload["sub"])
        tenant = await tenant_repo.get_by_id(tenant_id)
        
        if not tenant:
            raise HTTPException(status_code=401, detail="User not found")
        if tenant.status == TenantStatus.SUSPENDED:
            raise TenantSuspendedError()
        if tenant.status == TenantStatus.CANCELLED:
            raise HTTPException(status_code=401, detail="Account cancelled")
            
        request.state.tenant = tenant
        request.state.tenant_id = tenant.id
        request.state.api_key = None
        return tenant

    # 2. Otherwise treat as API Key
    prefix = settings.api_key_prefix
    if not token.startswith(prefix):
        raise InvalidAPIKeyError(detail="API key must start with the correct prefix.")

    key_repo = ApiKeyRepository(db)
    candidates = await key_repo.get_active_keys_by_prefix(prefix)

    matched_key = None
    for candidate in candidates:
        if verify_api_key(token, candidate.key_hash):
            matched_key = candidate
            break

    if matched_key is None:
        raise InvalidAPIKeyError()

    tenant = await tenant_repo.get_by_id(matched_key.tenant_id)

    if tenant is None:
        raise InvalidAPIKeyError(detail="Tenant associated with this key no longer exists.")

    if tenant.status == TenantStatus.SUSPENDED:
        raise TenantSuspendedError()

    if tenant.status == TenantStatus.CANCELLED:
        raise InvalidAPIKeyError(detail="This account has been cancelled.")

    # Enforce Role-Based Access
    # If the key is 'chat_only', it cannot hit /ingest endpoints
    if matched_key.role == "chat_only" and "ingest" in request.url.path:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This API key does not have permission to ingest documents."
        )

    # Update last_used
    await key_repo.update_last_used(matched_key.id)

    # Attach to request state
    request.state.tenant = tenant
    request.state.tenant_id = tenant.id
    request.state.api_key = matched_key

    return tenant
