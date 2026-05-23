"""Repository for Namespace CRUD with tenant isolation."""

from __future__ import annotations

import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.namespace import Namespace


class NamespaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        tenant_id: uuid.UUID,
        name: str,
    ) -> Namespace:
        ns = Namespace(tenant_id=tenant_id, name=name)
        self.session.add(ns)
        await self.session.flush()
        return ns

    async def get_by_name(
        self, tenant_id: uuid.UUID, name: str
    ) -> Namespace | None:
        """Get a namespace by name — scoped to tenant."""
        stmt = select(Namespace).where(
            and_(Namespace.tenant_id == tenant_id, Namespace.name == name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(
        self, namespace_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Namespace | None:
        stmt = select(Namespace).where(
            and_(Namespace.id == namespace_id, Namespace.tenant_id == tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_tenant(
        self, tenant_id: uuid.UUID
    ) -> list[Namespace]:
        stmt = (
            select(Namespace)
            .where(Namespace.tenant_id == tenant_id)
            .order_by(Namespace.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_counts(
        self,
        namespace_id: uuid.UUID,
        doc_count_delta: int = 0,
        token_count_delta: int = 0,
    ) -> None:
        """Increment doc_count and token_count atomically."""
        ns = await self.session.get(Namespace, namespace_id)
        if ns:
            ns.doc_count = ns.doc_count + doc_count_delta
            ns.token_count = ns.token_count + token_count_delta
            await self.session.flush()

    async def delete(
        self, tenant_id: uuid.UUID, name: str
    ) -> bool:
        """Delete a namespace and cascade to documents. Returns True if found."""
        ns = await self.get_by_name(tenant_id, name)
        if ns:
            await self.session.delete(ns)
            await self.session.flush()
            return True
        return False
