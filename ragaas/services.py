import uuid
import os
from .models import Namespace, Document, UsageEvent, ApiKey, Tenant
from core.embedding_service import EmbeddingService
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

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
        ns, created = Namespace.objects.get_or_create(
            tenant=tenant, 
            name=data.get('name'),
            defaults={
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

class QueryService:
    def __init__(self):
        # Initializing Qdrant client
        if hasattr(settings, 'QDRANT_API_KEY') and settings.QDRANT_API_KEY:
            self.qdrant = QdrantClient(
                url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
                api_key=settings.QDRANT_API_KEY,
            )
        else:
            self.qdrant = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
            )

    def query(self, tenant, namespace_name, query_text, top_k=3, custom_model=None):
        import time
        start_time = time.time()
        
        ns = Namespace.objects.get(tenant=tenant, name=namespace_name)
        
        # 1. Embed query
        embedding_service = EmbeddingService(
            provider=ns.embedding_provider,
            model=ns.embedding_model,
            api_key=ns.embedding_api_key,
            base_url=ns.embedding_base_url,
        )
        query_vector = embedding_service.embed_query(query_text)
        
        # 2. Search Qdrant
        collection_name = f"tenant_{tenant.id.hex}"
        
        try:
            results = self.qdrant.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="namespace_id",
                            match=qdrant_models.MatchValue(value=str(ns.id)),
                        )
                    ]
                ),
            )
        except Exception:
            results = []
            
        context_parts = []
        for i, hit in enumerate(results):
            source = hit.payload.get("filename", "Unknown")
            text = hit.payload.get("text", "")
            context_parts.append(f"[Source {i+1}: {source}]\n{text}")
            
        context = "\n\n".join(context_parts)
        
        # 3. Generate Answer (mocked logic or call LLM)
        llm_model = custom_model or ns.llm_model
        
        if settings.MOCK_LLM:
            answer = f"Mocked answer for query '{query_text}'. Found {len(results)} contexts."
            tokens_used = 100
        else:
            from openai import OpenAI
            import anthropic
            
            # Simple OpenAI usage
            if ns.llm_provider == "openai":
                client = OpenAI(
                    api_key=ns.llm_api_key or os.environ.get("OPENAI_API_KEY"),
                    base_url=ns.llm_base_url
                )
                response = client.chat.completions.create(
                    model=llm_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant. Use the provided context to answer the user's question."},
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query_text}"}
                    ]
                )
                answer = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
            elif ns.llm_provider == "anthropic":
                client = anthropic.Anthropic(
                    api_key=ns.llm_api_key or os.environ.get("ANTHROPIC_API_KEY"),
                    base_url=ns.llm_base_url
                )
                response = client.messages.create(
                    model=llm_model,
                    max_tokens=1000,
                    system="You are a helpful assistant. Use the provided context to answer the user's question.",
                    messages=[
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query_text}"}
                    ]
                )
                answer = response.content[0].text
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
            else:
                answer = f"Unsupported LLM provider: {ns.llm_provider}"
                tokens_used = 0
                
        query_ms = int((time.time() - start_time) * 1000)
        
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
                    "text": h.payload.get("text"),
                    "score": h.score,
                    "metadata": {
                        "filename": h.payload.get("filename"),
                        "page": h.payload.get("page", 1)
                    }
                } for h in results
            ],
            "usage": {
                "tokens": tokens_used,
                "latency_ms": query_ms,
                "model": llm_model
            }
        }
