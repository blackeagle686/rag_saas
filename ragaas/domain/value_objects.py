from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
import uuid

class PlanTier(str, Enum):
    FREE = 'free'
    START = 'start'
    MID = 'mid'
    PRIME = 'prime'
    ENTERPRISE = 'enterprise'

class DocumentStatus(str, Enum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    READY = 'ready'
    FAILED = 'failed'

class EventType(str, Enum):
    QUERY = 'query'
    INGEST = 'ingest'

@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int

@dataclass(frozen=True)
class Embedding:
    vector: List[float]

@dataclass(frozen=True)
class SourceReference:
    document_id: uuid.UUID
    filename: str
    chunk_text: str
    score: float

@dataclass(frozen=True)
class LLMResponse:
    answer: str
    latency_ms: int
    tokens_used: TokenUsage
    sources: List[SourceReference]

@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None

@dataclass(frozen=True)
class EmbeddingConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None

class MessageRole(str, Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'

class Platform(str, Enum):
    WEB_WIDGET = 'web_widget'
    SLACK = 'slack'
    TEAMS = 'teams'
    API = 'api'
