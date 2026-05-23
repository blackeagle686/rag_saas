"""Namespace model — logical grouping of documents for a tenant."""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin


class Namespace(TimestampMixin, Base):
    __tablename__ = "namespaces"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_namespace_tenant_name"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    doc_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="namespaces")
    documents = relationship("Document", back_populates="namespace", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Namespace {self.name} docs={self.doc_count}>"
