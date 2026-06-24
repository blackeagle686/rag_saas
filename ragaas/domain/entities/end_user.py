from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
from ragaas.domain.value_objects import Platform

@dataclass
class EndUser:
    """
    Represents an employee, customer, or individual user belonging to a Tenant.
    This is the person actually asking the questions to the RAG system.
    """
    id: uuid.UUID
    tenant_id: uuid.UUID
    platform: Platform          # How they are accessing the system (e.g., Slack, Web Widget)
    created_at: datetime
    is_active: bool = True
    external_id: Optional[str] = None  # e.g. "U123456" from Slack or "john@company.com"
    name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict) # Any custom data the tenant wants to store

    def deactivate(self):
        """Block this end-user from accessing the tenant's RAG system."""
        self.is_active = False

    def activate(self):
        """Re-allow this end-user to access the tenant's RAG system."""
        self.is_active = True
