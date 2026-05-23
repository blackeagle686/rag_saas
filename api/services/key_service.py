"""
API Key service — business logic for key management.

Handles key creation, rotation, revocation, and listing
while enforcing tenant isolation.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from api.config import get_settings
from api.schemas.keys import (
    CreateKeyRequest,
    CreateKeyResponse,
    KeyInfo,
    KeyListResponse,
    RotateKeyRequest,
    RotateKeyResponse,
)
from core.exceptions import NotFoundError
from core.security import generate_api_key
from db.models.tenant import Tenant
from db.repositories.api_key_repo import ApiKeyRepository


class KeyService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ApiKeyRepository(db)
        self.settings = get_settings()

    async def create_key(
        self, tenant: Tenant, request: CreateKeyRequest
    ) -> CreateKeyResponse:
        """Create a new API key for the tenant."""
        raw_key, key_hash, prefix = generate_api_key(self.settings.api_key_prefix)

        api_key = await self.repo.create(
            tenant_id=tenant.id,
            key_hash=key_hash,
            prefix=prefix,
            label=request.label,
        )

        return CreateKeyResponse(
            id=api_key.id,
            key=raw_key,
            prefix=prefix,
            label=api_key.label,
            created_at=api_key.created_at,
        )

    async def list_keys(self, tenant: Tenant) -> KeyListResponse:
        """List all keys for a tenant (never exposes the full key)."""
        keys = await self.repo.list_for_tenant(tenant.id)

        return KeyListResponse(
            keys=[
                KeyInfo(
                    id=k.id,
                    prefix=k.prefix,
                    label=k.label,
                    is_active=k.is_active,
                    created_at=k.created_at,
                    last_used=k.last_used,
                )
                for k in keys
            ]
        )

    async def rotate_key(
        self, tenant: Tenant, request: RotateKeyRequest
    ) -> RotateKeyResponse:
        """
        Rotate a key: deactivate the old one and create a new one.

        This is atomic — both operations happen in the same transaction.
        """
        # Deactivate old key
        success = await self.repo.deactivate(request.old_key_id, tenant.id)
        if not success:
            raise NotFoundError(detail=f"API key {request.old_key_id} not found.")

        # Create new key
        new_key_response = await self.create_key(
            tenant,
            CreateKeyRequest(label=request.label),
        )

        return RotateKeyResponse(
            deactivated_key_id=request.old_key_id,
            new_key=new_key_response,
        )

    async def revoke_key(
        self, tenant: Tenant, key_id: uuid.UUID
    ) -> None:
        """Revoke (deactivate) an API key."""
        success = await self.repo.deactivate(key_id, tenant.id)
        if not success:
            raise NotFoundError(detail=f"API key {key_id} not found.")
