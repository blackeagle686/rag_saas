import uuid
from datetime import datetime
from typing import BinaryIO
from ragaas.domain.entities.document import Document
from ragaas.domain.entities.chunk import DocumentChunk
from ragaas.domain.value_objects import DocumentStatus, EventType
from ragaas.domain.exceptions import ResourceNotFoundException
from ragaas.application.interfaces.repositories import IDocumentRepository, INamespaceRepository
from ragaas.application.interfaces.services import (
    IFileStorage, IDocumentParser, ITextChunker, ILLMService, IVectorStore, IBackgroundWorker, IBillingService
)

class InitiateDocumentIngestionUseCase:
    """Synchronous Use Case: Handles the API request, saves the file, and queues the background job."""
    def __init__(self, doc_repo: IDocumentRepository, storage: IFileStorage, worker: IBackgroundWorker):
        self.doc_repo = doc_repo
        self.storage = storage
        self.worker = worker

    def execute(self, namespace_id: uuid.UUID, filename: str, file_type: str, file_obj: BinaryIO) -> Document:
        doc = Document(
            id=uuid.uuid4(),
            namespace_id=namespace_id,
            filename=filename,
            file_type=file_type,
            status=DocumentStatus.PENDING,
            chunk_count=0,
            images_inside=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        s3_path = f"{namespace_id}/{doc.id}/{filename}"
        doc.s3_key = self.storage.upload_file(file_obj, s3_path)
        self.doc_repo.save(doc)
        
        self.worker.queue_document_ingestion(doc.id)
        return doc


class ProcessDocumentIngestionUseCase:
    """Asynchronous Use Case: Run by Celery to parse, chunk, embed, and store vectors."""
    def __init__(
        self,
        doc_repo: IDocumentRepository,
        namespace_repo: INamespaceRepository,
        storage: IFileStorage,
        parser: IDocumentParser,
        chunker: ITextChunker,
        llm_service: ILLMService,
        vector_store: IVectorStore,
        billing_service: IBillingService
    ):
        self.doc_repo = doc_repo
        self.namespace_repo = namespace_repo
        self.storage = storage
        self.parser = parser
        self.chunker = chunker
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.billing_service = billing_service

    def execute(self, document_id: uuid.UUID) -> None:
        doc = self.doc_repo.get_by_id(document_id)
        if not doc:
            return

        doc.mark_processing()
        self.doc_repo.save(doc)

        try:
            namespace = self.namespace_repo.get_by_id(doc.namespace_id)
            if not namespace:
                raise ResourceNotFoundException("Namespace not found")

            # 1. Download & Parse
            file_obj = self.storage.download_file(doc.s3_key)
            raw_text = self.parser.extract_text(file_obj, doc.file_type)

            # 2. Chunk
            text_chunks = self.chunker.chunk_text(raw_text, chunk_size=512, chunk_overlap=50)

            # 3. Embed & Vectorize
            domain_chunks = []
            for i, txt in enumerate(text_chunks):
                chunk = DocumentChunk(id=uuid.uuid4(), document_id=doc.id, namespace_id=doc.namespace_id, text=txt, index=i)
                embedding = self.llm_service.generate_embedding(txt, namespace.embedding_config)
                chunk.set_embedding(embedding)
                domain_chunks.append(chunk)

            self.vector_store.upsert_chunks(doc.namespace_id, domain_chunks)

            # 4. Finalize
            doc.mark_ready(len(domain_chunks))
            self.doc_repo.save(doc)

            # Update namespace metrics
            # Estimate tokens based on words just for example logic
            estimated_tokens = sum(len(c.text.split()) for c in domain_chunks)
            namespace.add_document(estimated_tokens)
            self.namespace_repo.save(namespace)

            # Report Usage
            self.billing_service.report_usage(namespace.tenant_id, estimated_tokens, EventType.INGEST)

        except Exception as e:
            doc.mark_failed(str(e))
            self.doc_repo.save(doc)
            raise e
