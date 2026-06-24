from dataclasses import dataclass
from typing import Optional
import uuid
from datetime import datetime
from ragaas.domain.value_objects import EventType

@dataclass
class UsageEvent:
    id: uuid.UUID
    tenant_id: uuid.UUID
    event_type: EventType
    tokens_used: int
    created_at: datetime
    updated_at: datetime
    query_ms: Optional[int] = None
    model_used: Optional[str] = None
