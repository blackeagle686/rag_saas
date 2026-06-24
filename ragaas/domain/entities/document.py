from dataclasses import dataclass
from typing import Optional
import uuid
from datetime import datetime
from ragaas.domain.value_objects import DocumentStatus

@dataclass
class Document:
    id: uuid.UUID
    namespace_id: uuid.UUID
    filename: str
    file_type: str
    status: DocumentStatus
    chunk_count: int
    images_inside: bool
    created_at: datetime
    updated_at: datetime
    s3_key: Optional[str] = None
    error_message: Optional[str] = None

    def mark_processing(self):
        """Transition document to processing state."""
        self.status = DocumentStatus.PROCESSING

    def mark_ready(self, chunk_count: int):
        """Transition document to ready state with final chunk count."""
        self.status = DocumentStatus.READY
        self.chunk_count = chunk_count
        self.error_message = None

    def mark_failed(self, error_message: str):
        """Transition document to failed state with an error message."""
        self.status = DocumentStatus.FAILED
        self.error_message = error_message
