"""
Query service — RAG query pipeline.

Handles the full retrieval-augmented generation flow:
embed query → search Qdrant → build context → call LLM → return answer.
"""

from __future__ import annotations

import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from api.config import Settings, get_settings
from api.schemas.query import QueryRequest, QueryResponse, SourceChunk
from core.exceptions import ExternalServiceError, NotFoundError
from core.logging import get_logger
from db.models.tenant import Tenant
from db.models.usage_event import EventType
from db.repositories.namespace_repo import NamespaceRepository
from db.repositories.usage_event_repo import UsageEventRepository

logger = get_logger("query_service")


class QueryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ns_repo = NamespaceRepository(db)
        self.usage_repo = UsageEventRepository(db)
        self.settings = get_settings()

    async def query(
        self, tenant: Tenant, request: QueryRequest
    ) -> QueryResponse:
        """
        Execute a RAG query pipeline:
        1. Validate namespace exists
        2. Embed the query
        3. Search Qdrant for relevant chunks
        4. Build context from retrieved chunks
        5. Call LLM with context
        6. Log usage event
        7. Return answer with sources
        """
        start_time = time.perf_counter()

        # 1. Validate namespace
        ns = await self.ns_repo.get_by_name(tenant.id, request.namespace)
        if not ns:
            raise NotFoundError(detail=f"Namespace '{request.namespace}' not found.")

        # 2. Embed the query
        query_embedding = await self._embed_query(request.query)

        # 3. Search Qdrant
        search_results = await self._search_qdrant(
            tenant_id=tenant.id,
            namespace_id=ns.id,
            embedding=query_embedding,
            top_k=request.top_k,
            filters=request.filters,
        )

        # 4. Build context
        context, sources = self._build_context(search_results)

        # 5. Call LLM
        model_used = request.model or self._get_default_model(tenant)
        answer, tokens_used = await self._call_llm(
            query=request.query,
            context=context,
            model=model_used,
            tenant=tenant,
        )

        # 6. Calculate timing
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # 7. Log usage event
        await self.usage_repo.create(
            tenant_id=tenant.id,
            event_type=EventType.QUERY,
            tokens_used=tokens_used,
            query_ms=latency_ms,
            model_used=model_used,
        )

        logger.info(
            "query_completed",
            tenant_id=str(tenant.id),
            namespace=request.namespace,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            sources_count=len(sources),
        )

        return QueryResponse(
            answer=answer,
            sources=sources,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
        )

    async def _embed_query(self, query: str) -> list[float]:
        """Embed the query using OpenAI or local embeddings."""
        if self.settings.mock_llm:
            # Return mock embedding for testing
            return [0.0] * self.settings.embedding_dimensions

        if self.settings.app_env == "development":
            try:
                from core.embeddings import embed_text_locally
                return embed_text_locally(query, is_query=True)
            except Exception as e:
                logger.error("local_embedding_failed", error=str(e))
                raise ExternalServiceError(detail=f"Local embedding service error: {e}")

        try:
            import openai

            client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
            response = await client.embeddings.create(
                model=self.settings.embedding_model,
                input=query,
                dimensions=self.settings.embedding_dimensions,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("embedding_failed", error=str(e))
            raise ExternalServiceError(detail=f"Embedding service error: {e}")

    async def _search_qdrant(
        self,
        tenant_id: uuid.UUID,
        namespace_id: uuid.UUID,
        embedding: list[float],
        top_k: int,
        filters: dict | None,
    ) -> list[dict]:
        """Search Qdrant for relevant chunks."""
        if self.settings.mock_llm:
            # Return mock results for testing
            return [
                {
                    "document_id": str(uuid.uuid4()),
                    "filename": "mock-document.txt",
                    "chunk_text": "This is a mock search result for testing purposes.",
                    "score": 0.95,
                    "chunk_index": 0,
                }
            ]

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            client = QdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port,
                api_key=self.settings.qdrant_api_key or None,
            )

            # Build collection name scoped to tenant
            collection_name = f"tenant_{tenant_id}"

            # Build filter conditions
            must_conditions = [
                FieldCondition(
                    key="namespace_id",
                    match=MatchValue(value=str(namespace_id)),
                )
            ]

            if filters:
                for key, value in filters.items():
                    must_conditions.append(
                        FieldCondition(key=f"metadata.{key}", match=MatchValue(value=value))
                    )

            results = client.search(
                collection_name=collection_name,
                query_vector=embedding,
                query_filter=Filter(must=must_conditions),
                limit=top_k,
                with_payload=True,
            )

            return [
                {
                    "document_id": hit.payload.get("document_id", ""),
                    "filename": hit.payload.get("filename", ""),
                    "chunk_text": hit.payload.get("chunk_text", ""),
                    "score": hit.score,
                    "chunk_index": hit.payload.get("chunk_index", 0),
                }
                for hit in results
            ]

        except Exception as e:
            logger.error("qdrant_search_failed", error=str(e))
            raise ExternalServiceError(detail=f"Vector search error: {e}")

    def _build_context(
        self, search_results: list[dict]
    ) -> tuple[str, list[SourceChunk]]:
        """Build LLM context and source references from search results."""
        context_parts = []
        sources = []

        for i, result in enumerate(search_results):
            chunk_text = result.get("chunk_text", "")
            filename = result.get("filename", "unknown")

            context_parts.append(
                f"[Source {i + 1}: {filename}]\n{chunk_text}"
            )

            sources.append(
                SourceChunk(
                    document_id=uuid.UUID(result["document_id"])
                    if result.get("document_id")
                    else uuid.uuid4(),
                    filename=filename,
                    chunk=chunk_text[:500],  # Truncate for response
                    score=round(result.get("score", 0.0), 4),
                )
            )

        context = "\n\n---\n\n".join(context_parts)
        return context, sources

    def _get_default_model(self, tenant: Tenant) -> str:
        """Get the default LLM model based on settings."""
        return tenant.llm_model or self.settings.openai_llm_model

    async def _call_llm(
        self, query: str, context: str, model: str, tenant: Tenant
    ) -> tuple[str, int]:
        """
        Call the LLM to generate an answer.

        Returns (answer_text, tokens_used).
        """
        if self.settings.mock_llm:
            return (
                f"[MOCK] Based on the provided context, here is a mock answer to: {query}",
                100,
            )

        system_prompt = (
            "You are a helpful assistant that answers questions based ONLY on the "
            "provided context. If the context does not contain enough information "
            "to answer the question, say 'I don't have enough information to answer "
            "this question based on the available documents.' Never make up information."
        )

        user_message = f"Context:\n{context}\n\nQuestion: {query}"

        try:
            if "claude" in model.lower() or tenant.llm_provider == "anthropic":
                return await self._call_anthropic(system_prompt, user_message, model, tenant)
            else:
                return await self._call_openai(system_prompt, user_message, model, tenant)
        except Exception as e:
            logger.error("llm_call_failed", error=str(e), model=model)
            raise ExternalServiceError(detail=f"LLM service error: {e}")

    async def _call_openai(
        self, system_prompt: str, user_message: str, model: str, tenant: Tenant
    ) -> tuple[str, int]:
        """Call OpenAI chat completion."""
        import openai

        api_key = tenant.llm_api_key or self.settings.openai_api_key
        base_url = tenant.llm_base_url or None

        client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            max_tokens=1500,
        )

        answer = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return answer, tokens

    async def _call_anthropic(
        self, system_prompt: str, user_message: str, model: str, tenant: Tenant
    ) -> tuple[str, int]:
        """Call Anthropic Claude."""
        import anthropic

        api_key = tenant.llm_api_key or self.settings.anthropic_api_key
        base_url = tenant.llm_base_url or None

        client_args = {"api_key": api_key}
        if base_url:
            client_args["base_url"] = base_url

        client = anthropic.AsyncAnthropic(**client_args)
        response = await client.messages.create(
            model=model,
            max_tokens=1500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        answer = response.content[0].text if response.content else ""
        tokens = (response.usage.input_tokens + response.usage.output_tokens)
        return answer, tokens
