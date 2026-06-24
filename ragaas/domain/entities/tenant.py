from dataclasses import dataclass
from typing import List, Optional
import uuid
from datetime import datetime
from ragaas.domain.value_objects import PlanTier, LLMConfig, EmbeddingConfig

@dataclass
class Tenant:
    id: uuid.UUID
    email: str
    name: str
    plan: PlanTier
    status: str
    is_active: bool
    can_deploy_api: bool
    allowed_vector_dbs: List[str]
    allowed_rag_types: List[str]
    created_at: datetime
    updated_at: datetime
    llm_config: LLMConfig
    embedding_config: EmbeddingConfig
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    billing_cycle_reset: Optional[datetime] = None

    def can_query(self) -> bool:
        """Business rule: only active tenants can perform queries."""
        return self.is_active and self.status == 'active'

    def update_plan(self, new_plan: PlanTier):
        """Update the tenant's billing plan."""
        self.plan = new_plan

    def suspend(self):
        """Suspend the tenant from accessing the platform."""
        self.status = 'suspended'
        self.is_active = False

    def activate(self):
        """Activate or re-activate the tenant."""
        self.status = 'active'
        self.is_active = True
