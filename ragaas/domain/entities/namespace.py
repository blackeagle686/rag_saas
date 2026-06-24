from dataclasses import dataclass
from typing import Dict, Any
import uuid
from datetime import datetime
from ragaas.domain.value_objects import LLMConfig, EmbeddingConfig

@dataclass
class Namespace:
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    doc_count: int
    token_count: int
    rag_type: str
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    llm_config: LLMConfig
    embedding_config: EmbeddingConfig

    def add_document(self, tokens: int):
        """Update metrics when a document is successfully ingested."""
        self.doc_count += 1
        self.token_count += tokens

    def remove_document(self, tokens: int):
        """Update metrics when a document is deleted."""
        self.doc_count = max(0, self.doc_count - 1)
        self.token_count = max(0, self.token_count - tokens)
