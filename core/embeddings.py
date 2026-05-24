"""
Thin convenience wrappers around the EmbeddingService singleton.

Kept for backward compatibility — prefer using EmbeddingService directly.
"""

from __future__ import annotations

from core.embedding_service import EmbeddingService
from core.logging import get_logger

logger = get_logger("local_embeddings")


def get_local_embedding_model():
    """Get the singleton EmbeddingService, initializing if needed."""
    service = EmbeddingService()
    if not service.is_initialized:
        logger.info("lazy_initializing_embedding_model")
        service.initialize()
    return service.model


def embed_text_locally(text: str, is_query: bool = False) -> list[float]:
    """Embed a single piece of text using the local Qwen model."""
    service = EmbeddingService()
    if not service.is_initialized:
        logger.info("lazy_initializing_embedding_model")
        service.initialize()
    return service.embed_text(text, is_query=is_query)


def embed_batch_locally(texts: list[str], is_query: bool = False) -> list[list[float]]:
    """Embed a list of texts using the local Qwen model in one batch."""
    if not texts:
        return []
    service = EmbeddingService()
    if not service.is_initialized:
        logger.info("lazy_initializing_embedding_model")
        service.initialize()
    return service.embed_batch(texts, is_query=is_query)
