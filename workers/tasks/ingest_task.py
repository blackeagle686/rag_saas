"""
Document ingestion Celery task.

Full pipeline:
1. Read file from storage
2. Extract text (PDF, DOCX, TXT, MD, HTML)
3. Clean text
4. Chunk text (recursive character splitter)
5. Generate embeddings (OpenAI)
6. Upsert to Qdrant
7. Update DB records
8. Log usage event
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from celery import shared_task

from core.logging import get_logger

logger = get_logger("ingest_task")


@shared_task(
    bind=True,
    name="workers.tasks.ingest_task.process_document",
    max_retries=3,
    default_retry_delay=30,
    acks_late=True,
)
def process_document(
    self,  # type: ignore[no-untyped-def]
    document_id: str,
    tenant_id: str,
    namespace_id: str,
    storage_key: str,
    file_type: str,
    metadata: dict,
) -> dict:
    """
    Process a document through the full ingestion pipeline.

    This is a synchronous Celery task that uses the sync
    versions of DB and external service calls.
    """
    from api.config import get_settings

    settings = get_settings()

    logger.info(
        "ingestion_started",
        document_id=document_id,
        tenant_id=tenant_id,
        file_type=file_type,
    )

    try:
        # 1. Read file from storage
        file_content = _read_file(storage_key, settings)

        # 2. Extract text
        text = _extract_text(file_content, file_type)

        # 3. Clean text
        text = _clean_text(text)

        if not text.strip():
            _update_document_status_sync(
                document_id, "failed", error_message="No text content extracted from file."
            )
            return {"status": "failed", "reason": "no_text_content"}

        # 4. Chunk text
        chunks = _chunk_text(
            text,
            chunk_size=settings.chunk_size_tokens,
            overlap=settings.chunk_overlap_tokens,
        )

        # 5. Generate embeddings
        embeddings = _generate_embeddings(
            chunks,
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            batch_size=settings.embedding_batch_size,
            mock=settings.mock_llm,
        )

        # 6. Upsert to Qdrant
        _upsert_to_qdrant(
            tenant_id=tenant_id,
            namespace_id=namespace_id,
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
            metadata=metadata,
            filename=Path(storage_key).name,
            settings=settings,
        )

        # 7. Update DB records
        _update_document_status_sync(document_id, "ready", chunk_count=len(chunks))
        _update_namespace_counts_sync(namespace_id, doc_count_delta=1, token_count_delta=len(text))
        _log_usage_event_sync(tenant_id, "ingest", tokens_used=len(text))

        logger.info(
            "ingestion_completed",
            document_id=document_id,
            chunks=len(chunks),
            text_length=len(text),
        )

        return {
            "status": "ready",
            "document_id": document_id,
            "chunks": len(chunks),
        }

    except Exception as exc:
        logger.error(
            "ingestion_failed",
            document_id=document_id,
            error=str(exc),
        )
        _update_document_status_sync(
            document_id, "failed", error_message=str(exc)[:500]
        )

        # Retry on transient errors
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        return {"status": "failed", "error": str(exc)}


# == Text Extraction ==


def _read_file(storage_key: str, settings) -> bytes:  # type: ignore[no-untyped-def]
    """Read file from local storage or S3."""
    if settings.storage_backend == "local":
        file_path = Path(settings.local_storage_path) / storage_key
        return file_path.read_bytes()
    else:
        import boto3

        s3 = boto3.client(
            "s3",
            region_name=settings.s3_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        response = s3.get_object(Bucket=settings.s3_bucket_name, Key=storage_key)
        return response["Body"].read()


def _extract_text(content: bytes, file_type: str) -> str:
    """Extract text from file based on file type."""
    extractors = {
        ".pdf": _extract_pdf,
        ".docx": _extract_docx,
        ".txt": _extract_txt,
        ".md": _extract_txt,
        ".html": _extract_html,
    }

    extractor = extractors.get(file_type)
    if not extractor:
        raise ValueError(f"Unsupported file type: {file_type}")

    return extractor(content)


def _extract_pdf(content: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    import io

    import pdfplumber

    text_parts = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return "\n\n".join(text_parts)


def _extract_docx(content: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    import io

    from docx import Document

    doc = Document(io.BytesIO(content))
    return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())


def _extract_txt(content: bytes) -> str:
    """Extract text from plain text / markdown files."""
    # Try UTF-8 first, then fall back to latin-1
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="replace")


def _extract_html(content: bytes) -> str:
    """Extract text from HTML using BeautifulSoup."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(content, "html.parser")

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    return soup.get_text(separator="\n", strip=True)


# == Text Processing ==


def _clean_text(text: str) -> str:
    """Clean extracted text."""
    # Remove null bytes
    text = text.replace("\x00", "")

    # Normalize whitespace (but preserve paragraph breaks)
    text = re.sub(r"[^\S\n]+", " ", text)

    # Collapse multiple newlines to max 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def _chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
) -> list[str]:
    """
    Split text into overlapping chunks using recursive character splitting.

    Uses tiktoken for accurate token counting with approximate character-based
    chunking. Splits on paragraph → sentence → word boundaries.
    """
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")

        def count_tokens(t: str) -> int:
            return len(enc.encode(t))
    except ImportError:
        # Fallback: approximate 1 token ≈ 4 chars
        def count_tokens(t: str) -> int:
            return len(t) // 4

    # Separators in priority order
    separators = ["\n\n", "\n", ". ", " ", ""]

    chunks: list[str] = []
    _recursive_split(text, separators, chunk_size, overlap, count_tokens, chunks)

    return chunks


def _recursive_split(
    text: str,
    separators: list[str],
    chunk_size: int,
    overlap: int,
    count_tokens,  # type: ignore[no-untyped-def]
    result: list[str],
) -> None:
    """Recursively split text on the best available separator."""
    if count_tokens(text) <= chunk_size:
        if text.strip():
            result.append(text.strip())
        return

    # Try each separator
    sep = separators[0] if separators else ""
    remaining_separators = separators[1:] if len(separators) > 1 else [""]

    if sep:
        parts = text.split(sep)
    else:
        # Last resort: split by characters
        chars_per_chunk = chunk_size * 4  # Approximate
        parts = [text[i : i + chars_per_chunk] for i in range(0, len(text), chars_per_chunk)]

    current_chunk = ""

    for part in parts:
        candidate = f"{current_chunk}{sep}{part}" if current_chunk else part

        if count_tokens(candidate) <= chunk_size:
            current_chunk = candidate
        else:
            # Save current chunk
            if current_chunk.strip():
                result.append(current_chunk.strip())

            # Check if this part alone exceeds chunk_size
            if count_tokens(part) > chunk_size:
                _recursive_split(part, remaining_separators, chunk_size, overlap, count_tokens, result)
                current_chunk = ""
            else:
                # Start new chunk with overlap
                if overlap > 0 and current_chunk:
                    overlap_text = _get_overlap(current_chunk, overlap, count_tokens)
                    current_chunk = f"{overlap_text}{sep}{part}" if overlap_text else part
                else:
                    current_chunk = part

    # Don't forget the last chunk
    if current_chunk.strip():
        result.append(current_chunk.strip())


def _get_overlap(text: str, overlap_tokens: int, count_tokens) -> str:  # type: ignore[no-untyped-def]
    """Get the last N tokens of text for overlap."""
    words = text.split()
    overlap_text = ""

    for word in reversed(words):
        candidate = f"{word} {overlap_text}" if overlap_text else word
        if count_tokens(candidate) > overlap_tokens:
            break
        overlap_text = candidate

    return overlap_text.strip()


# == Embedding ==


def _generate_embeddings(
    chunks: list[str],
    api_key: str,
    model: str,
    dimensions: int,
    batch_size: int = 100,
    mock: bool = False,
) -> list[list[float]]:
    """Generate embeddings for all chunks in batches."""
    if mock:
        return [[0.0] * dimensions for _ in chunks]

    from api.config import get_settings
    settings = get_settings()

    if settings.app_env == "development":
        try:
            from core.embeddings import embed_batch_locally
            return embed_batch_locally(chunks, is_query=False)
        except Exception as e:
            logger.error("local_batch_embedding_failed", error=str(e))
            raise

    import openai

    client = openai.OpenAI(api_key=api_key)
    all_embeddings: list[list[float]] = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        response = client.embeddings.create(
            model=model,
            input=batch,
            dimensions=dimensions,
        )
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


# == Qdrant ==


def _upsert_to_qdrant(
    tenant_id: str,
    namespace_id: str,
    document_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
    metadata: dict,
    filename: str,
    settings,  # type: ignore[no-untyped-def]
) -> None:
    """Upsert chunk embeddings to Qdrant."""
    if settings.mock_llm:
        logger.info("mock_qdrant_upsert", chunks=len(chunks))
        return

    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams

    client = QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key or None,
    )

    collection_name = f"tenant_{tenant_id}"

    # Create collection if it doesn't exist
    collections = [c.name for c in client.get_collections().collections]
    if collection_name not in collections:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )

    # Build points
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid.uuid4())
        payload = {
            "namespace_id": namespace_id,
            "document_id": document_id,
            "filename": filename,
            "chunk_text": chunk,
            "chunk_index": i,
            "metadata": metadata,
        }
        points.append(PointStruct(id=point_id, vector=embedding, payload=payload))

    # Upsert in batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=collection_name, points=batch)


# == DB Sync Helpers ==
# These use synchronous SQLAlchemy since Celery tasks are sync


def _update_document_status_sync(
    document_id: str,
    status: str,
    chunk_count: int | None = None,
    error_message: str | None = None,
) -> None:
    """Update document status using sync DB connection."""
    from sqlalchemy import create_engine, text

    from api.config import get_settings

    settings = get_settings()
    # Convert async URL to sync
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2").replace("postgresql+asyncpg", "postgresql")

    engine = create_engine(sync_url)
    with engine.connect() as conn:
        params: dict = {"doc_id": document_id, "status": status}
        set_clauses = ["status = :status", "updated_at = NOW()"]

        if chunk_count is not None:
            set_clauses.append("chunk_count = :chunk_count")
            params["chunk_count"] = chunk_count

        if error_message is not None:
            set_clauses.append("error_message = :error_message")
            params["error_message"] = error_message

        query = f"UPDATE documents SET {', '.join(set_clauses)} WHERE id = :doc_id"
        conn.execute(text(query), params)
        conn.commit()
    engine.dispose()


def _update_namespace_counts_sync(
    namespace_id: str,
    doc_count_delta: int = 0,
    token_count_delta: int = 0,
) -> None:
    """Update namespace counters using sync DB connection."""
    from sqlalchemy import create_engine, text

    from api.config import get_settings

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2").replace("postgresql+asyncpg", "postgresql")

    engine = create_engine(sync_url)
    with engine.connect() as conn:
        conn.execute(
            text(
                "UPDATE namespaces SET "
                "doc_count = doc_count + :doc_delta, "
                "token_count = token_count + :token_delta, "
                "updated_at = NOW() "
                "WHERE id = :ns_id"
            ),
            {"ns_id": namespace_id, "doc_delta": doc_count_delta, "token_delta": token_count_delta},
        )
        conn.commit()
    engine.dispose()


def _log_usage_event_sync(
    tenant_id: str,
    event_type: str,
    tokens_used: int = 0,
) -> None:
    """Log a usage event using sync DB connection."""
    from sqlalchemy import create_engine, text

    from api.config import get_settings

    settings = get_settings()
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2").replace("postgresql+asyncpg", "postgresql")

    engine = create_engine(sync_url)
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO usage_events (id, tenant_id, event_type, tokens_used, created_at, updated_at) "
                "VALUES (:id, :tenant_id, :event_type, :tokens_used, NOW(), NOW())"
            ),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "event_type": event_type,
                "tokens_used": tokens_used,
            },
        )
        conn.commit()
    engine.dispose()
