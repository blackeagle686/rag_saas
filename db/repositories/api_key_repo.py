"""Repository for API Key CRUD operations with tenant isolation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.api_key import ApiKey


class ApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        tenant_id: uuid.UUID,
        key_hash: str,
        prefix: str,
        label: str | None = None,
        namespace_id: uuid.UUID | None = None,
        role: str = "admin",
    ) -> ApiKey:
        api_key = ApiKey(
            tenant_id=tenant_id,
            key_hash=key_hash,
            prefix=prefix,
            label=label,
            namespace_id=namespace_id,
            role=role,
        )
        self.session.add(api_key)
        await self.session.flush()
        return api_key

    async def get_by_id(
        self, key_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> ApiKey | None:
        """Get a key by ID — scoped to tenant for isolation."""
        stmt = select(ApiKey).where(
            and_(ApiKey.id == key_id, ApiKey.tenant_id == tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_keys_by_prefix(self, prefix_start: str) -> list[ApiKey]:
        """
        Get all active API keys whose prefix starts with the given string.
        Used during authentication to narrow down candidates before bcrypt check.
        """
        stmt = select(ApiKey).where(
            and_(
                ApiKey.prefix.startswith(prefix_start),
                ApiKey.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_active(self) -> list[ApiKey]:
        """Get all active API keys (for auth lookup)."""
        stmt = select(ApiKey).where(ApiKey.is_active.is_(True))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_tenant(
        self, tenant_id: uuid.UUID
    ) -> list[ApiKey]:
        """List all keys for a tenant (active and inactive)."""
        stmt = (
            select(ApiKey)
            .where(ApiKey.tenant_id == tenant_id)
            .order_by(ApiKey.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_last_used(self, key_id: uuid.UUID) -> None:
        """Update the last_used timestamp for a key."""
        api_key = await self.session.get(ApiKey, key_id)
        if api_key:
            api_key.last_used = datetime.now(timezone.utc)
            await self.session.flush()

    async def deactivate(
        self, key_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> bool:
        """Deactivate (revoke) a key. Returns True if found and deactivated."""
        api_key = await self.get_by_id(key_id, tenant_id)
        if api_key:
            api_key.is_active = False
            await self.session.flush()
            return True
        return False
