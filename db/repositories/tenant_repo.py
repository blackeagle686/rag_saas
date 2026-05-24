"""Repository for Tenant CRUD operations."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tenant import Tenant, TenantPlan, TenantStatus


class TenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        name: str,
        email: str,
        plan: TenantPlan = TenantPlan.STARTER,
    ) -> Tenant:
        tenant = Tenant(name=name, email=email, plan=plan)
        self.session.add(tenant)
        await self.session.flush()
        return tenant

    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        return await self.session.get(Tenant, tenant_id)

    async def get_by_email(self, email: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_plan(
        self, tenant_id: uuid.UUID, plan: TenantPlan
    ) -> Tenant | None:
        tenant = await self.get_by_id(tenant_id)
        if tenant:
            tenant.plan = plan
            await self.session.flush()
        return tenant

    async def update_status(
        self, tenant_id: uuid.UUID, status: TenantStatus
    ) -> Tenant | None:
        tenant = await self.get_by_id(tenant_id)
        if tenant:
            tenant.status = status
            await self.session.flush()
        return tenant

    async def list_all(
        self, limit: int = 100, offset: int = 0
    ) -> list[Tenant]:
        stmt = select(Tenant).order_by(Tenant.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_llm_settings(
        self,
        tenant_id: uuid.UUID,
        llm_provider: str,
        llm_model: str,
        llm_api_key: str,
        llm_base_url: str,
    ) -> Tenant | None:
        tenant = await self.get_by_id(tenant_id)
        if tenant:
            tenant.llm_provider = llm_provider
            tenant.llm_model = llm_model
            tenant.llm_api_key = llm_api_key
            tenant.llm_base_url = llm_base_url
            await self.session.flush()
        return tenant
