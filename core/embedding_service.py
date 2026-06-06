"""
Embedding Service — singleton for managing remote embedding model via DashScope API.
"""

from __future__ import annotations

import os
import dashscope
from http import HTTPStatus
from core.logging import get_logger

logger = get_logger("embedding_service")

# Extract API key directly from user instructions, removing any errant spaces
DEFAULT_API_KEY = "sk-ws-H.HLXLMP.bsb6.MEUCIQDGgGDCO-IC4PgfH3-M_zdsFm3vWz7z9sL9Eb99c4keQIgDgWfWhyQwFh3gYngwdr_P82ItOMgnm_Mz38U2_jgJdQ"
MODEL_NAME = "text-embedding-v4"


class EmbeddingService:
    """Singleton service for the remote DashScope embedding model.

    Uses `text-embedding-v4` via the dashscope Python SDK.
    """

    _instance: EmbeddingService | None = None
    _is_initialized: bool = False

    def __new__(cls) -> EmbeddingService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        """Initialize the API client configuration."""
        if self._is_initialized:
            logger.info("embedding_model_already_initialized")
            return

        # Use environment variable or fallback to the provided default key
        api_key = os.environ.get("DASHSCOPE_API_KEY", DEFAULT_API_KEY)
        dashscope.api_key = api_key
        
        # Optional: Set base URL if needed based on user preferences.
        # However, the native DashScope SDK handles the correct endpoint for `TextEmbedding.call`.
        # If using OpenAI-compatible mode, we would use the `openai` SDK instead.
        # Since the example used `dashscope.TextEmbedding.call`, we stick to the native SDK here.

        self._is_initialized = True
        logger.info("embedding_model_initialized", model=MODEL_NAME)

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    def embed_text(self, text: str, is_query: bool = False) -> list[float]:
        """Embed a single piece of text using DashScope."""
        if not self.is_initialized:
            raise RuntimeError(
                "EmbeddingService not initialized. "
                "Call EmbeddingService().initialize() first."
            )

        resp = dashscope.TextEmbedding.call(
            model=MODEL_NAME,
            input=text
        )
        
        if resp.status_code == HTTPStatus.OK:
            return resp.output["embeddings"][0]["embedding"]
        else:
            error_msg = f"DashScope API Error: {resp.message} (Code: {resp.code})"
            logger.error("dashscope_embed_error", error=error_msg, response=resp)
            raise Exception(error_msg)

    def embed_batch(
        self, texts: list[str], is_query: bool = False
    ) -> list[list[float]]:
        """Embed a list of texts using DashScope."""
        if not self.is_initialized:
            raise RuntimeError(
                "EmbeddingService not initialized. "
                "Call EmbeddingService().initialize() first."
            )
        
        if not texts:
            return []

        # dashscope TextEmbedding.call accepts `input` as str or list[str]
        # Max limit depends on the API documentation, typically handles reasonable batches.
        resp = dashscope.TextEmbedding.call(
            model=MODEL_NAME,
            input=texts
        )
        
        if resp.status_code == HTTPStatus.OK:
            # We sort the results based on text_index to ensure the output matches the input list order
            embeddings = [None] * len(texts)
            for emb in resp.output["embeddings"]:
                embeddings[emb["text_index"]] = emb["embedding"]
            return embeddings  # type: ignore[return-value]
        else:
            error_msg = f"DashScope API Error: {resp.message} (Code: {resp.code})"
            logger.error("dashscope_embed_batch_error", error=error_msg, response=resp)
            raise Exception(error_msg)
