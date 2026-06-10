import time
import os
import asyncio
from asgiref.sync import async_to_sync
from django.conf import settings
from ragaas.models import Namespace, UsageEvent
from core.embedding_service import EmbeddingService
from phoenix.framework.rag import RAG, CAG, AgenticRAG, MultiModalRAG
from phoenix.framework.rag.config import RAGConfig, CAGConfig, AgenticRAGConfig, MultiModalRAGConfig
from phoenix.services.llm.openai import OpenAILLM

class PhoenixEmbeddingAdapter:
    def __init__(self, provider, model, api_key, base_url):
        self.service = EmbeddingService(provider, model, api_key, base_url)
    def embed_documents(self, texts):
        return self.service.embed_batch(texts)
    def embed_query(self, text):
        return self.service.embed_text(text, is_query=True)

class QdrantVectorDBAdapter:
    def __init__(self, collection_name: str, embedding_service: PhoenixEmbeddingAdapter, namespace_id: str = None):
        self.collection_name = collection_name
        self.embedding_service = embedding_service
        self.namespace_id = namespace_id
        self.client = None
    async def init(self):
        from qdrant_client import QdrantClient
        if hasattr(settings, 'QDRANT_API_KEY') and settings.QDRANT_API_KEY:
            self.client = QdrantClient(url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}", api_key=settings.QDRANT_API_KEY, check_compatibility=False)
        else:
            self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, check_compatibility=False)
    async def search(self, query: str, limit: int = 5, where: dict = None) -> list:
        if not self.client: await self.init()
        vector = self.embedding_service.embed_query(query)
        from qdrant_client.http import models as qdrant_models
        query_filter = None
        if self.namespace_id:
            query_filter = qdrant_models.Filter(must=[qdrant_models.FieldCondition(key="namespace_id", match=qdrant_models.MatchValue(value=self.namespace_id))])
        def _do_search():
            return self.client.search(collection_name=self.collection_name, query_vector=vector, query_filter=query_filter, limit=limit)
        results = await asyncio.to_thread(_do_search)
        return [{"content": p.payload.get("text", ""), "metadata": p.payload, "id": str(p.id), "distance": p.score} for p in results]

class QueryService:
    def query(self, tenant, namespace_name, query_text, top_k=3, custom_model=None):
        start_time = time.time()
        ns = Namespace.objects.get(tenant=tenant, name=namespace_name)
        embeddings = PhoenixEmbeddingAdapter(
            provider=ns.embedding_provider, model=ns.embedding_model,
            api_key=ns.embedding_api_key or tenant.embedding_api_key, base_url=ns.embedding_base_url or tenant.embedding_base_url,
        )
        collection_name = f"tenant_{tenant.id.hex}"
        vector_db = QdrantVectorDBAdapter(collection_name=collection_name, embedding_service=embeddings, namespace_id=str(ns.id))
        llm_model = custom_model or ns.llm_model
        
        if ns.llm_provider in ("openai", "longcat2-preview"):
            resolved_api_key = ns.llm_api_key or tenant.llm_api_key or os.environ.get("OPENAI_API_KEY")
            resolved_base_url = ns.llm_base_url or tenant.llm_base_url or os.environ.get("OPENAI_API_BASE")
            # CRITICAL SECURITY FIX: Do not mutate os.environ globally as it causes cross-tenant race conditions.
            # Phoenix / OpenAI clients must be configured via instance properties.
            llm = OpenAILLM()
            llm.model = llm_model
            if resolved_api_key:
                llm.api_key = resolved_api_key
            if resolved_base_url:
                llm.base_url = resolved_base_url
        else:
            class MockLLM:
                async def init(self): pass
                async def generate(self, prompt, **kwargs): return f"Mock answer for {ns.llm_provider}"
            llm = MockLLM()
            
        rag_type = ns.rag_type.lower()
        cfg_dict = ns.config or {}
        cfg_dict["top_k"] = top_k
        
        if rag_type == 'cag': rag = CAG(config=CAGConfig(**cfg_dict), llm=llm, vector_db=vector_db, embeddings=embeddings)
        elif rag_type == 'agentic': rag = AgenticRAG(config=AgenticRAGConfig(**cfg_dict), llm=llm, vector_db=vector_db, embeddings=embeddings)
        elif rag_type == 'multimodal': rag = MultiModalRAG(config=MultiModalRAGConfig(**cfg_dict), llm=llm, vector_db=vector_db, embeddings=embeddings)
        else: rag = RAG(config=RAGConfig(**cfg_dict), llm=llm, vector_db=vector_db, embeddings=embeddings)
            
        async def run_query():
            await vector_db.init()
            if hasattr(llm, 'init'): await llm.init()
            if hasattr(rag, 'query_with_sources'): return await rag.query_with_sources(query_text)
            else: return {"answer": await rag.query(query_text), "sources": []}
                
        try:
            result = async_to_sync(run_query)()
            answer = result.get("answer", "")
            sources = result.get("sources", [])
        finally:
            pass # Removed os.environ restore logic since we no longer mutate it

        query_ms = int((time.time() - start_time) * 1000)
        
        # Calculate accurate token usage for billing using tiktoken
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            context_text = " ".join([str(s.get("content", s.get("text", ""))) for s in sources]) if isinstance(sources, list) else ""
            input_text = query_text + context_text
            tokens_used = len(enc.encode(input_text)) + len(enc.encode(answer))
        except Exception:
            tokens_used = 0 
        
        UsageEvent.objects.create(
            tenant=tenant, event_type='query', tokens_used=tokens_used, query_ms=query_ms, model_used=llm_model
        )
        
        return {
            "answer": answer,
            "context_chunks": [{"text": str(s.get("text", "")), "score": s.get("score", 0.0), "metadata": s.get("metadata", {})} for s in sources] if isinstance(sources, list) else [],
            "usage": {"tokens": tokens_used, "latency_ms": query_ms, "model": llm_model}
        }
