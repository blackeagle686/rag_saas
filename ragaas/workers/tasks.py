from celery import shared_task
from ragaas.models import Document, Namespace
from core.embedding_service import EmbeddingService
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from django.conf import settings
import uuid

@shared_task(queue='bulk_ingestion')
def process_document(document_id):
    try:
        doc = Document.objects.get(id=document_id)
        doc.status = 'processing'
        doc.save()
        
        # 1. Read file
        with open(doc.s3_key, 'rb') as f:
            content_bytes = f.read()
            
        text = ""
        if doc.file_type == 'db':
            import json
            import sqlite3
            with open(doc.s3_key, 'r') as f:
                db_config = json.load(f)
                
            db_type = db_config.get('type')
            query = db_config.get('query')
            rows = []
            
            if db_type == 'postgresql':
                import psycopg2
                conn = psycopg2.connect(
                    host=db_config.get('host'),
                    port=db_config.get('port') or 5432,
                    user=db_config.get('user'),
                    password=db_config.get('password'),
                    dbname=db_config.get('database')
                )
                cur = conn.cursor()
                cur.execute(query)
                while True:
                    batch_rows = cur.fetchmany(1000)
                    if not batch_rows: break
                    text += "\n\n".join([str(item) for row in batch_rows for item in row if item]) + "\n\n"
                conn.close()
            elif db_type == 'mysql':
                import pymysql
                conn = pymysql.connect(
                    host=db_config.get('host'),
                    port=int(db_config.get('port') or 3306),
                    user=db_config.get('user'),
                    password=db_config.get('password'),
                    database=db_config.get('database')
                )
                cur = conn.cursor()
                cur.execute(query)
                while True:
                    batch_rows = cur.fetchmany(1000)
                    if not batch_rows: break
                    text += "\n\n".join([str(item) for row in batch_rows for item in row if item]) + "\n\n"
                conn.close()
            elif db_type == 'sqlite':
                conn = sqlite3.connect(db_config.get('database'))
                cur = conn.cursor()
                cur.execute(query)
                while True:
                    batch_rows = cur.fetchmany(1000)
                    if not batch_rows: break
                    text += "\n\n".join([str(item) for row in batch_rows for item in row if item]) + "\n\n"
                conn.close()
            
        elif doc.file_type in ('txt', 'md'):
            text = content_bytes.decode('utf-8', errors='ignore')
        elif doc.file_type == 'pdf':
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        else:
            text = content_bytes.decode('utf-8', errors='ignore')
            
        if not text.strip():
            doc.status = 'failed'
            doc.error_message = "No text could be extracted"
            doc.save()
            return
            
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        
        chunk_size = 512
        overlap = 50
        chunks = []
        for i in range(0, len(tokens), chunk_size - overlap):
            chunk_tokens = tokens[i:i + chunk_size]
            chunks.append(enc.decode(chunk_tokens))
            
        doc.chunk_count = len(chunks)
        doc.save()
        
        ns = doc.namespace
        embedder = EmbeddingService(
            provider=ns.embedding_provider,
            model=ns.embedding_model,
            api_key=ns.embedding_api_key or ns.tenant.embedding_api_key,
            base_url=ns.embedding_base_url or ns.tenant.embedding_base_url
        )
        
        from qdrant_client import QdrantClient
        from qdrant_client.http import models as qdrant_models
        import os
        
        qdrant_url = getattr(settings, 'QDRANT_URL', 'http://localhost:6333')
        qdrant_client = QdrantClient(url=qdrant_url)
        collection_name = "ragaas_vectors"
        
        vectors = embedder.embed_batch(chunks) if hasattr(embedder, 'embed_batch') else [embedder.embed_query(c) for c in chunks]
        
        try:
            qdrant_client.get_collection(collection_name)
        except Exception:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=len(vectors[0]),
                    distance=qdrant_models.Distance.COSINE
                )
            )
        
        points = []
        for i, chunk in enumerate(chunks):
            points.append(
                qdrant_models.PointStruct(
                    id=uuid.uuid4().hex,
                    vector=vectors[i],
                    payload={
                        "document_id": str(doc.id),
                        "namespace_id": str(ns.id),
                        "tenant_id": str(ns.tenant.id),
                        "filename": doc.filename,
                        "text": chunk,
                        "chunk_index": i
                    }
                )
            )
            
        batch_size = 100
        for i in range(0, len(points), batch_size):
            qdrant_client.upsert(
                collection_name=collection_name,
                points=points[i:i + batch_size]
            )
            
        doc.status = 'ready'
        doc.save()
        
        ns.doc_count += 1
        ns.token_count += len(tokens)
        ns.save()
        
    except Exception as e:
        doc.status = 'failed'
        doc.error_message = str(e)
        doc.save()
        raise e

@shared_task(queue='realtime')
def log_query_metrics_task(tenant_id, query_text, answer, sources, query_ms, llm_model):
    try:
        from ragaas.models import Tenant, UsageEvent
        import tiktoken
        tenant = Tenant.objects.get(id=tenant_id)
        enc = tiktoken.get_encoding("cl100k_base")
        context_text = " ".join([str(s.get("content", s.get("text", ""))) for s in sources]) if isinstance(sources, list) else ""
        input_text = query_text + context_text
        tokens_used = len(enc.encode(input_text)) + len(enc.encode(answer))
        
        UsageEvent.objects.create(
            tenant=tenant, event_type='query', tokens_used=tokens_used, query_ms=query_ms, model_used=llm_model
        )
    except Exception as e:
        print(f"Error logging metrics: {e}")

@shared_task(queue='realtime')
def delete_namespace_data_task(tenant_id, namespace_name):
    try:
        from ragaas.models import Namespace
        import chromadb
        import os
        from django.conf import settings
        
        ns = Namespace.objects.filter(tenant_id=tenant_id, name=namespace_name).first()
        if not ns: return
        
        # Clean Qdrant vectors
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models as qdrant_models
            
            qdrant_url = getattr(settings, 'QDRANT_URL', 'http://localhost:6333')
            qdrant_client = QdrantClient(url=qdrant_url)
            
            qdrant_client.delete(
                collection_name="ragaas_vectors",
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="namespace_id",
                                match=qdrant_models.MatchValue(value=str(ns.id))
                            )
                        ]
                    )
                )
            )
        except Exception:
            pass # Collection might not exist or be empty
            
        # The database cascade deletes documents and API keys
        ns.delete()
    except Exception as e:
        print(f"Error deleting namespace: {e}")
