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
        import os
        self.provider = provider.lower()
        self.model = model
        
        if not api_key:
            if self.provider == "dashscope":
                api_key = os.environ.get("DASHSCOPE_API_KEY")
            elif self.provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY")
                
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
            return self._embed_openai(texts)
        elif self.provider == "local":
            return self._embed_local(texts)
        elif self.provider == "gemini":
            return self._embed_gemini(texts)
        elif self.provider == "cohere":
            return self._embed_cohere(texts)
        elif self.provider == "voyage":
            return self._embed_voyage(texts)
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

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        from sentence_transformers import SentenceTransformer
        import torch
        
        # Cache models globally by model name to support different namespaces using different local models
        if not hasattr(EmbeddingService, "_local_models"):
            EmbeddingService._local_models = {}
            
        if self.model not in EmbeddingService._local_models:
            logger.info(f"Loading local embedding model {self.model} on CPU (Optimized)...")
            
            # Ensure optimal CPU thread configuration
            torch.set_num_threads(max(1, torch.get_num_threads()))
            
            # Load model onto CPU and forcefully set to evaluation mode (disables dropout, etc.)
            model = SentenceTransformer(self.model, device='cpu')
            model.eval()
            EmbeddingService._local_models[self.model] = model
            
        # Optimization:
        # - normalize_embeddings=True: Critically improves accuracy for Cosine Similarity/Dot Product DB searches
        # - batch_size=32: Prevents CPU cache thrashing on large text arrays
        # - convert_to_numpy=True: Fastest extraction path before tolist()
        embeddings = EmbeddingService._local_models[self.model].encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False
        )
        return embeddings.tolist()
        
    def _embed_gemini(self, texts: list[str]) -> list[list[float]]:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        
        # Gemini can take a list of strings
        result = genai.embed_content(
            model=f"models/{self.model}",
            content=texts,
            task_type="retrieval_document"
        )
        return result['embedding']
        
    def _embed_cohere(self, texts: list[str]) -> list[list[float]]:
        import cohere
        co = cohere.Client(self.api_key)
        response = co.embed(
            texts=texts,
            model=self.model,
            input_type="search_document"
        )
        return response.embeddings
        
    def _embed_voyage(self, texts: list[str]) -> list[list[float]]:
        import voyageai
        vo = voyageai.Client(api_key=self.api_key)
        result = vo.embed(texts, model=self.model)
        return result.embeddings
