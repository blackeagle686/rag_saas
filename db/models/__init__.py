"""
Models package — exports all SQLAlchemy models.

Import this module to ensure all models are registered
with the Base metadata before running Alembic.
"""

from db.models.api_key import ApiKey
from db.models.base import Base
from db.models.document import Document, DocumentStatus
from db.models.namespace import Namespace
from db.models.tenant import Tenant, TenantPlan, TenantStatus
from db.models.usage_event import EventType, UsageEvent

__all__ = [
    "Base",
    "Tenant",
    "TenantPlan",
    "TenantStatus",
    "ApiKey",
    "Namespace",
    "Document",
    "DocumentStatus",
    "UsageEvent",
    "EventType",
]
