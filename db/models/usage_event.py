"""Usage event model — tracks API usage for billing and analytics."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin


class EventType(str, enum.Enum):
    QUERY = "query"
    INGEST = "ingest"


class UsageEvent(TimestampMixin, Base):
    __tablename__ = "usage_events"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[EventType] = mapped_column(
        String(20),
        nullable=False,
        index=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    query_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="usage_events")

    def __repr__(self) -> str:
        return f"<UsageEvent {self.event_type} tokens={self.tokens_used}>"
