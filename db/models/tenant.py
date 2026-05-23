"""Tenant model — represents a customer account."""

from __future__ import annotations

import enum

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.base import Base, TimestampMixin


class TenantPlan(str, enum.Enum):
    STARTER = "starter"
    GROWTH = "growth"
    SCALE = "scale"
    ENTERPRISE = "enterprise"


class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    plan: Mapped[TenantPlan] = mapped_column(
        String(20),
        default=TenantPlan.STARTER,
        nullable=False,
    )
    status: Mapped[TenantStatus] = mapped_column(
        String(20),
        default=TenantStatus.ACTIVE,
        nullable=False,
    )

    # Relationships
    api_keys = relationship("ApiKey", back_populates="tenant", cascade="all, delete-orphan")
    namespaces = relationship("Namespace", back_populates="tenant", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Tenant {self.name} ({self.email}) plan={self.plan}>"
