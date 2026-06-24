from dataclasses import dataclass
from typing import Optional
import uuid
from datetime import datetime

@dataclass
class APIKey:
    id: uuid.UUID
    tenant_id: uuid.UUID
    key_hash: str
    prefix: str
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime
    label: Optional[str] = None
    last_used: Optional[datetime] = None
    namespace_id: Optional[uuid.UUID] = None

    def revoke(self):
        """Revoke the API key making it permanently inactive."""
        self.is_active = False

    def record_usage(self, timestamp: datetime):
        """Update the last used timestamp of the API key."""
        self.last_used = timestamp
