from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import uuid

@dataclass
class DocumentChunk:
    id: uuid.UUID
    document_id: uuid.UUID
    namespace_id: uuid.UUID
    text: str
    index: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def set_embedding(self, embedding_vector: List[float]):
        """Attach an embedding vector to this chunk."""
        self.embedding = embedding_vector
