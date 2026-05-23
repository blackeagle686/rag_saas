"""
API key management endpoints.

All endpoints require authentication (except initial key creation
which would happen via a separate onboarding flow).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_tenant
from api.middleware.rate_limiter import check_rate_limit
from api.schemas.common import MessageResponse
from api.schemas.keys import (
    CreateKeyRequest,
    CreateKeyResponse,
    KeyListResponse,
    RotateKeyRequest,
    RotateKeyResponse,
)
from api.services.key_service import KeyService
from db.engine import get_db_session
from db.models.tenant import Tenant

router = APIRouter(prefix="/v1/keys", tags=["API Keys"])


@router.post(
    "",
    response_model=CreateKeyResponse,
    status_code=201,
    summary="Create a new API key",
    description=(
        "Generate a new API key for your account. "
        "**The full key is returned ONCE in this response.** "
        "Store it securely — it cannot be retrieved again."
    ),
)
async def create_key(
    request: CreateKeyRequest = CreateKeyRequest(),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> CreateKeyResponse:
    service = KeyService(db)
    return await service.create_key(tenant, request)


@router.get(
    "",
    response_model=KeyListResponse,
    summary="List API keys",
    description="List all API keys for your account. Shows prefix and metadata — never the full key.",
)
async def list_keys(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> KeyListResponse:
    service = KeyService(db)
    return await service.list_keys(tenant)


@router.post(
    "/rotate",
    response_model=RotateKeyResponse,
    summary="Rotate an API key",
    description=(
        "Deactivate an existing key and create a new one atomically. "
        "The old key stops working immediately."
    ),
)
async def rotate_key(
    request: RotateKeyRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> RotateKeyResponse:
    service = KeyService(db)
    return await service.rotate_key(tenant, request)


@router.delete(
    "/{key_id}",
    response_model=MessageResponse,
    summary="Revoke an API key",
    description="Permanently deactivate an API key. This cannot be undone.",
)
async def revoke_key(
    key_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> MessageResponse:
    service = KeyService(db)
    await service.revoke_key(tenant, key_id)
    return MessageResponse(message=f"API key {key_id} has been revoked.")
