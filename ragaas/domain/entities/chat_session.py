from dataclasses import dataclass, field
from typing import List
import uuid
from datetime import datetime
from ragaas.domain.value_objects import MessageRole, SourceReference

@dataclass
class ChatMessage:
    """A single message within a chat session."""
    id: uuid.UUID
    session_id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime
    tokens_used: int = 0
    sources: List[SourceReference] = field(default_factory=list)

@dataclass
class ChatSession:
    """
    Represents an ongoing conversation between an EndUser and a specific Namespace.
    Maintains the state and history of the conversation for multi-turn RAG.
    """
    id: uuid.UUID
    end_user_id: uuid.UUID
    namespace_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessage] = field(default_factory=list)

    def add_message(self, message: ChatMessage):
        """Add a new message to the session and update the timestamp."""
        self.messages.append(message)
        self.updated_at = message.created_at

    def get_conversation_history(self, limit: int = 10) -> List[ChatMessage]:
        """
        Return the most recent messages to be used as context for the LLM.
        Assumes messages are ordered chronologically.
        """
        return self.messages[-limit:] if limit > 0 else []
