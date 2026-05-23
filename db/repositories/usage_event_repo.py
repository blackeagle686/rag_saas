"""Repository for UsageEvent logging and aggregation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.usage_event import UsageEvent, EventType


class UsageEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        tenant_id: uuid.UUID,
        event_type: EventType,
        tokens_used: int = 0,
        query_ms: int | None = None,
        model_used: str | None = None,
    ) -> UsageEvent:
        event = UsageEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            tokens_used=tokens_used,
            query_ms=query_ms,
            model_used=model_used,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def count_events_since(
        self,
        tenant_id: uuid.UUID,
        event_type: EventType,
        since: datetime,
    ) -> int:
        """Count events of a given type since a timestamp. Used for plan limit checks."""
        stmt = select(func.count()).where(
            and_(
                UsageEvent.tenant_id == tenant_id,
                UsageEvent.event_type == event_type,
                UsageEvent.created_at >= since,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def total_tokens_since(
        self,
        tenant_id: uuid.UUID,
        since: datetime,
    ) -> int:
        """Sum tokens used since a timestamp. Used for billing."""
        stmt = select(func.coalesce(func.sum(UsageEvent.tokens_used), 0)).where(
            and_(
                UsageEvent.tenant_id == tenant_id,
                UsageEvent.created_at >= since,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def list_for_tenant(
        self,
        tenant_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[UsageEvent]:
        stmt = (
            select(UsageEvent)
            .where(UsageEvent.tenant_id == tenant_id)
            .order_by(UsageEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
