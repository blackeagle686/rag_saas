from celery import shared_task
from .models import Document, Namespace
from core.embedding_service import EmbeddingService
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from django.conf import settings
import uuid

@shared_task
def process_document(document_id):
    try:
        doc = Document.objects.get(id=document_id)
        doc.status = 'processing'
        doc.save()
        
        # 1. Read file
        with open(doc.s3_key, 'rb') as f:
            content_bytes = f.read()
            
        text = ""
        if doc.file_type in ('txt', 'md'):
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
            api_key=ns.embedding_api_key,
            base_url=ns.embedding_base_url
        )
        
        if hasattr(settings, 'QDRANT_API_KEY') and settings.QDRANT_API_KEY:
            qdrant = QdrantClient(
                url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
                api_key=settings.QDRANT_API_KEY,
            )
        else:
            qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            
        collection_name = f"tenant_{doc.namespace.tenant.id.hex}"
        
        try:
            qdrant.get_collection(collection_name)
        except:
            qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=settings.EMBEDDING_DIMENSIONS, 
                    distance=qdrant_models.Distance.COSINE
                )
            )
            
        points = []
        for i, chunk in enumerate(chunks):
            vector = embedder.embed_query(chunk)
            points.append(
                qdrant_models.PointStruct(
                    id=uuid.uuid4().hex,
                    vector=vector,
                    payload={
                        "text": chunk,
                        "document_id": str(doc.id),
                        "namespace_id": str(ns.id),
                        "filename": doc.filename,
                        "chunk_index": i
                    }
                )
            )
            
        batch_size = 100
        for i in range(0, len(points), batch_size):
            qdrant.upsert(
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
