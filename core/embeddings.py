"""
Local Embedding Service wrapper.

Uses sentence-transformers to run Qwen/Qwen3-Embedding-0.6B locally for
development environments without external API dependency.
"""

from __future__ import annotations

import torch
from core.logging import get_logger

logger = get_logger("local_embeddings")

_model_instance = None


def get_local_embedding_model():
    """Lazily loads and caches the SentenceTransformer model."""
    global _model_instance
    if _model_instance is None:
        logger.info("loading_local_embedding_model", model="Qwen/Qwen3-Embedding-0.6B")
        from sentence_transformers import SentenceTransformer
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("local_embedding_model_device", device=device)
        
        # Load the model
        _model_instance = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", device=device)
        logger.info("local_embedding_model_loaded")
        
    return _model_instance


def embed_text_locally(text: str, is_query: bool = False) -> list[float]:
    """Embed a single piece of text using the local Qwen model."""
    model = get_local_embedding_model()
    
    # Queries benefit from using a prompt name
    prompt_name = "query" if is_query else None
    
    # Encode single text
    embedding = model.encode(text, prompt_name=prompt_name)
    return embedding.tolist()


def embed_batch_locally(texts: list[str], is_query: bool = False) -> list[list[float]]:
    """Embed a list of texts using the local Qwen model in one batch."""
    if not texts:
        return []
        
    model = get_local_embedding_model()
    prompt_name = "query" if is_query else None
    
    embeddings = model.encode(texts, prompt_name=prompt_name)
    return embeddings.tolist()
