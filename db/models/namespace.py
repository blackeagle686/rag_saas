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

    # LLM Configuration
    llm_provider: Mapped[str] = mapped_column(String(50), default="openai", nullable=False)
    llm_model: Mapped[str] = mapped_column(String(100), default="gpt-4o-mini", nullable=False)
    llm_api_key: Mapped[str] = mapped_column(String(255), nullable=True)
    llm_base_url: Mapped[str] = mapped_column(String(255), nullable=True)

    # Embedding Configuration
    embedding_provider: Mapped[str] = mapped_column(String(50), default="dashscope", nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), default="text-embedding-v4", nullable=False)
    embedding_api_key: Mapped[str] = mapped_column(String(255), nullable=True)
    embedding_base_url: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="namespaces")
    documents = relationship("Document", back_populates="namespace", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Namespace {self.name} docs={self.doc_count}>"
