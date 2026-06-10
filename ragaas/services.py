import uuid
import os
from .models import Namespace, Document, UsageEvent, ApiKey, Tenant
from core.embedding_service import EmbeddingService
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class KeyService:
    @staticmethod
    def create_key(tenant, label, role="admin", namespace_name=None):
        import secrets
        import hashlib
        from core.security import generate_api_key
        raw_key, key_hash, prefix = generate_api_key("rgs_live_")
        
        ns = None
        if namespace_name:
            ns = Namespace.objects.get(tenant=tenant, name=namespace_name)
            
        api_key = ApiKey.objects.create(
            tenant=tenant,
            key_hash=key_hash,
            prefix=prefix,
            label=label,
            role=role,
            namespace=ns
        )
        return raw_key, api_key

class NamespaceService:
    @staticmethod
    def create_namespace(tenant, data):
        from phoenix.framework.rag.config import RAGConfig, CAGConfig, AgenticRAGConfig, MultiModalRAGConfig
        import dataclasses
        
        rag_type = data.get('rag_type', 'standard')
        
        if rag_type == 'cag':
            phx_cfg = dataclasses.asdict(CAGConfig())
        elif rag_type == 'agentic':
            phx_cfg = dataclasses.asdict(AgenticRAGConfig())
        elif rag_type == 'multimodal':
            phx_cfg = dataclasses.asdict(MultiModalRAGConfig())
        else:
            phx_cfg = dataclasses.asdict(RAGConfig())
            
        # Merge any provided config overrides
        provided_config = data.get('config', {})
        if isinstance(provided_config, dict):
            phx_cfg.update(provided_config)
            
        ns, created = Namespace.objects.get_or_create(
            tenant=tenant, 
            name=data.get('name'),
            defaults={
                'rag_type': rag_type,
                'config': phx_cfg,
                'llm_provider': data.get('llm_provider', 'openai'),
                'llm_model': data.get('llm_model', 'gpt-4o-mini'),
                'llm_api_key': data.get('llm_api_key'),
                'llm_base_url': data.get('llm_base_url'),
                'embedding_provider': data.get('embedding_provider', 'dashscope'),
                'embedding_model': data.get('embedding_model', 'text-embedding-v4'),
                'embedding_api_key': data.get('embedding_api_key'),
                'embedding_base_url': data.get('embedding_base_url'),
            }
        )
        return ns, created

    @staticmethod
    def delete_namespace(tenant, name):
        ns = Namespace.objects.filter(tenant=tenant, name=name).first()
        if ns:
            # Delete Qdrant and S3 logic goes here
            ns.delete()
            return True
        return False

class PhoenixEmbeddingAdapter:
    """Adapter to make core.embedding_service compatible with Phoenix BaseEmbeddings."""
    def __init__(self, provider, model, api_key, base_url):
        self.service = EmbeddingService(provider, model, api_key, base_url)

    def embed_documents(self, texts):
        return self.service.embed_batch(texts)

    def embed_query(self, text):
        return self.service.embed_text(text, is_query=True)

class QdrantVectorDBAdapter:
    """Adapter to use Qdrant for retrieval in Phoenix RAG."""
    def __init__(self, collection_name: str, embedding_service: PhoenixEmbeddingAdapter, namespace_id: str = None):
        self.collection_name = collection_name
        self.embedding_service = embedding_service
        self.namespace_id = namespace_id
        self.client = None

    async def init(self):
        from qdrant_client import QdrantClient
        if hasattr(settings, 'QDRANT_API_KEY') and settings.QDRANT_API_KEY:
            self.client = QdrantClient(
                url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
                api_key=settings.QDRANT_API_KEY,
            )
        else:
            self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

    async def search(self, query: str, limit: int = 5, where: dict = None) -> list:
        if not self.client:
            await self.init()
            
        vector = self.embedding_service.embed_query(query)
        from qdrant_client.http import models as qdrant_models
        
        query_filter = None
        if self.namespace_id:
            query_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="namespace_id",
                        match=qdrant_models.MatchValue(value=self.namespace_id)
                    )
                ]
            )
            
        import asyncio
        def _do_search():
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                query_filter=query_filter,
                limit=limit
            )
            
        results = await asyncio.to_thread(_do_search)
        
        docs = []
        for point in results:
            docs.append({
                "content": point.payload.get("text", ""),
                "metadata": point.payload,
                "id": str(point.id),
                "distance": point.score
            })
        return docs

class QueryService:
    def __init__(self):
        pass

    def query(self, tenant, namespace_name, query_text, top_k=3, custom_model=None):
        import time
        from asgiref.sync import async_to_sync
        from phoenix.framework.rag import RAG, CAG, AgenticRAG, MultiModalRAG
        from phoenix.framework.rag.config import RAGConfig, CAGConfig, AgenticRAGConfig, MultiModalRAGConfig
        from phoenix.services.llm.openai import OpenAILLM

        import os

        start_time = time.time()
        ns = Namespace.objects.get(tenant=tenant, name=namespace_name)
        
        # 1. Setup Embeddings Adapter
        embeddings = PhoenixEmbeddingAdapter(
            provider=ns.embedding_provider,
            model=ns.embedding_model,
            api_key=ns.embedding_api_key,
            base_url=ns.embedding_base_url,
        )

        # 2. Setup Vector DB (Qdrant adapter matching tasks.py collection format)
        collection_name = f"tenant_{tenant.id.hex}"
        vector_db = QdrantVectorDBAdapter(collection_name=collection_name, embedding_service=embeddings, namespace_id=str(ns.id))
        
        # 3. Setup LLM
        llm_model = custom_model or ns.llm_model
        
        if ns.llm_provider == "openai":
            # Temporary override env vars for OpenAILLM since it uses config/env internally
            old_key = os.environ.get("OPENAI_API_KEY")
            old_url = os.environ.get("OPENAI_API_BASE")
            if ns.llm_api_key:
                os.environ["OPENAI_API_KEY"] = ns.llm_api_key
            if ns.llm_base_url:
                os.environ["OPENAI_API_BASE"] = ns.llm_base_url
                
            llm = OpenAILLM()
            llm.model = llm_model
            llm.api_key = ns.llm_api_key or os.environ.get("OPENAI_API_KEY")
            llm.base_url = ns.llm_base_url or os.environ.get("OPENAI_API_BASE")
        else:
            # Fallback to a mock LLM for unsupported providers in this refactor
            class MockLLM:
                async def init(self): pass
                async def generate(self, prompt, **kwargs): return f"Mock answer for {ns.llm_provider}"
            llm = MockLLM()
            
        # 4. Instantiate Phoenix RAG Framework based on rag_type
        rag_type = ns.rag_type.lower()
        cfg_dict = ns.config or {}
        cfg_dict["top_k"] = top_k
        
        if rag_type == 'cag':
            config = CAGConfig(**cfg_dict)
            rag = CAG(config=config, llm=llm, vector_db=vector_db, embeddings=embeddings)
        elif rag_type == 'agentic':
            config = AgenticRAGConfig(**cfg_dict)
            rag = AgenticRAG(config=config, llm=llm, vector_db=vector_db, embeddings=embeddings)
        elif rag_type == 'multimodal':
            config = MultiModalRAGConfig(**cfg_dict)
            rag = MultiModalRAG(config=config, llm=llm, vector_db=vector_db, embeddings=embeddings)
        else:
            config = RAGConfig(**cfg_dict)
            rag = RAG(config=config, llm=llm, vector_db=vector_db, embeddings=embeddings)
            
        # 5. Run the query synchronously
        async def run_query():
            await vector_db.init()
            if hasattr(llm, 'init'):
                await llm.init()
            # If the user asks to "query with sources" we can get the chunks
            if hasattr(rag, 'query_with_sources'):
                return await rag.query_with_sources(query_text)
            else:
                answer = await rag.query(query_text)
                return {"answer": answer, "sources": []}
                
        try:
            result = async_to_sync(run_query)()
            answer = result.get("answer", "")
            sources = result.get("sources", [])
        finally:
            if ns.llm_provider == "openai":
                if old_key is not None: os.environ["OPENAI_API_KEY"] = old_key
                else: os.environ.pop("OPENAI_API_KEY", None)
                if old_url is not None: os.environ["OPENAI_API_BASE"] = old_url
                else: os.environ.pop("OPENAI_API_BASE", None)

        query_ms = int((time.time() - start_time) * 1000)
        tokens_used = 0 # Phoenix might not expose tokens natively yet
        
        UsageEvent.objects.create(
            tenant=tenant,
            event_type='query',
            tokens_used=tokens_used,
            query_ms=query_ms,
            model_used=llm_model
        )
        
        return {
            "answer": answer,
            "context_chunks": [
                {
                    "text": str(s.get("text", "")),
                    "score": s.get("score", 0.0),
                    "metadata": s.get("metadata", {})
                } for s in sources
            ] if isinstance(sources, list) else [],
            "usage": {
                "tokens": tokens_used,
                "latency_ms": query_ms,
                "model": llm_model
            }
        }
