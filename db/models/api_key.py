"""API Key model — stores hashed keys for tenant authentication."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin


class ApiKey(TimestampMixin, Base):
    __tablename__ = "api_keys"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    prefix: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Display prefix (e.g. rgs_live_abc12345...)",
    )
    label: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Optional user-provided label for the key",
    )
    last_used: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    namespace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("namespaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="If set, this key is scoped to a specific namespace",
    )
    role: Mapped[str] = mapped_column(
        String(20),
        default="admin",
        nullable=False,
        comment="'admin' or 'chat_only'",
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    namespace = relationship("Namespace")

    def __repr__(self) -> str:
        return f"<ApiKey {self.prefix} active={self.is_active}>"
