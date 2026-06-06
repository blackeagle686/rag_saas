"""
Embedding Service — factory for managing remote embedding models dynamically.
"""

from __future__ import annotations

import dashscope
from http import HTTPStatus
from core.logging import get_logger

logger = get_logger("embedding_service")


class EmbeddingService:
    """Service for generating embeddings using namespace-specific configuration."""

    def __init__(self, provider: str, model: str, api_key: str | None, base_url: str | None = None):
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def embed_text(self, text: str, is_query: bool = False) -> list[float]:
        """Embed a single piece of text."""
        return self.embed_batch([text], is_query=is_query)[0]

    def embed_batch(self, texts: list[str], is_query: bool = False) -> list[list[float]]:
        """Embed a list of texts using the configured provider."""
        if not texts:
            return []

        if self.provider == "dashscope":
            return self._embed_dashscope(texts)
        elif self.provider == "openai":
            # For synchronous calling, we can use the synchronous OpenAI client
            # But the service is often called from Celery (sync) and FastAPI (async).
            # Wait, this is called from Celery process_document (sync), so sync is better here.
            return self._embed_openai(texts)
        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

    def _embed_dashscope(self, texts: list[str]) -> list[list[float]]:
        resp = dashscope.TextEmbedding.call(
            model=self.model,
            input=texts,
            api_key=self.api_key
        )
        
        if resp.status_code == HTTPStatus.OK:
            embeddings = [None] * len(texts)
            for emb in resp.output["embeddings"]:
                embeddings[emb["text_index"]] = emb["embedding"]
            return embeddings  # type: ignore[return-value]
        else:
            error_msg = f"DashScope API Error: {resp.message} (Code: {resp.code})"
            logger.error("dashscope_embed_batch_error", error=error_msg, response=resp)
            raise Exception(error_msg)

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        import openai
        
        client_args = {"api_key": self.api_key}
        if self.base_url:
            client_args["base_url"] = self.base_url
            
        client = openai.OpenAI(**client_args)
        response = client.embeddings.create(
            model=self.model,
            input=texts
        )
        
        # Responses come back in order
        return [data.embedding for data in response.data]
