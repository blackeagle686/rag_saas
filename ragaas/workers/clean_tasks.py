from celery import shared_task
import uuid
import logging

from ragaas.application.use_cases.ingestion_use_cases import ProcessDocumentIngestionUseCase
from ragaas.infrastructure.database.repositories import DjangoDocumentRepository, DjangoNamespaceRepository

# NOTE: In a fully implemented architecture, these below would be actual classes in the infrastructure layer.
# We mock them here to demonstrate the wiring.
class DummyStorage:
    def download_file(self, *args, **kwargs): pass
class DummyParser:
    def extract_text(self, *args, **kwargs): return "Extracted text"
class DummyChunker:
    def chunk_text(self, *args, **kwargs): return ["Chunk 1", "Chunk 2"]
class DummyLLM:
    def generate_embedding(self, *args, **kwargs): return [0.1, 0.2, 0.3]
    def generate_answer(self, *args, **kwargs):
        from ragaas.domain.value_objects import LLMResponse, TokenUsage
        return LLMResponse(answer="This is a simulated AI response. The clean architecture pipeline is working correctly from start to finish!", latency_ms=450, tokens_used=TokenUsage(prompt_tokens=10, completion_tokens=15, total_tokens=25), sources=[])

class DummyVectorStore:
    def upsert_chunks(self, *args, **kwargs): pass
    def search_similar(self, *args, **kwargs):
        from ragaas.domain.value_objects import SourceReference
        return [SourceReference(document_id=uuid.uuid4(), chunk_text="Dummy context chunk from vector db.", score=0.95, filename="sample.pdf")]
class DummyBilling:
    def report_usage(self, *args, **kwargs): pass

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_document_clean_task(self, document_id: str):
    """
    Clean Architecture approach: The Celery task acts as an Interface Adapter (Controller).
    It has NO business logic. It only instantiates the dependencies and calls the Use Case.
    """
    logger.info(f"Starting clean ingestion task for document: {document_id}")
    
    try:
        # 1. Dependency Injection setup
        # We inject the Django ORM repositories (Infrastructure) into the Use Case
        doc_repo = DjangoDocumentRepository()
        namespace_repo = DjangoNamespaceRepository()
        
        # Inject other infrastructure adapters
        storage = DummyStorage()
        parser = DummyParser()
        chunker = DummyChunker()
        llm = DummyLLM()
        vector_store = DummyVectorStore()
        billing = DummyBilling()

        # Instantiate the Application Use Case
        use_case = ProcessDocumentIngestionUseCase(
            doc_repo=doc_repo, namespace_repo=namespace_repo,
            storage=storage, parser=parser, chunker=chunker,
            llm_service=llm, vector_store=vector_store, billing_service=billing
        )
        
        # 2. Execute Business Logic entirely decoupled from Celery
        use_case.execute(uuid.UUID(document_id))
        
        logger.info(f"Successfully processed document: {document_id}")
        
    except Exception as exc:
        logger.error(f"Failed to process document {document_id}: {str(exc)}")
        self.retry(exc=exc, countdown=60)
