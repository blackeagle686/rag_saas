"""
Ingestion service — handles file upload validation and dispatching to Celery.

The actual processing (text extraction, chunking, embedding) happens
in the Celery worker task. This service handles the API-side logic:
validation, record creation, and task dispatch.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import Settings, get_settings
from api.schemas.ingest import IngestRequest, IngestResponse, IngestStatusResponse
from api.schemas.ingest import SUPPORTED_FILE_TYPES
from core.exceptions import (
    FileTooLargeError,
    NotFoundError,
    UnsupportedFileTypeError,
)
from core.logging import get_logger
from core.security import sanitize_filename
from db.models.document import DocumentStatus
from db.models.tenant import Tenant
from db.repositories.document_repo import DocumentRepository
from db.repositories.namespace_repo import NamespaceRepository

logger = get_logger("ingest_service")


class IngestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ns_repo = NamespaceRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.settings = get_settings()

    async def ingest_file(
        self,
        tenant: Tenant,
        request: IngestRequest,
        file: UploadFile | None = None,
    ) -> IngestResponse:
        """
        Start ingesting a document.

        Validates the file, creates DB records, saves to storage,
        and dispatches a Celery task for async processing.
        """
        # 1. Resolve namespace (auto-create if needed)
        ns = await self.ns_repo.get_by_name(tenant.id, request.namespace)
        if not ns:
            ns = await self.ns_repo.create(tenant.id, request.namespace)

        # 2. Determine filename and type
        if file:
            filename = sanitize_filename(file.filename or "uploaded_file")
            file_ext = Path(filename).suffix.lower()
        elif request.file_url:
            url_path = str(request.file_url).split("?")[0]  # Strip query params
            filename = sanitize_filename(url_path.split("/")[-1])
            file_ext = Path(filename).suffix.lower()
        else:
            raise UnsupportedFileTypeError(
                detail="Either a file upload or file_url must be provided."
            )

        # 3. Validate file type
        if file_ext not in SUPPORTED_FILE_TYPES:
            raise UnsupportedFileTypeError(
                detail=f"File type '{file_ext}' is not supported. "
                f"Supported types: {', '.join(sorted(SUPPORTED_FILE_TYPES))}"
            )

        # 4. Validate file size (for uploads)
        if file:
            # Read file to check size
            content = await file.read()
            if len(content) > self.settings.max_file_size_bytes:
                raise FileTooLargeError(
                    detail=f"File size exceeds the maximum of {self.settings.max_file_size_mb}MB."
                )
            await file.seek(0)  # Reset for later reading

        # 5. Create document record
        doc = await self.doc_repo.create(
            namespace_id=ns.id,
            filename=filename,
            file_type=file_ext,
        )

        # 6. Save file to local storage (or S3)
        storage_key = f"{tenant.id}/{ns.id}/{doc.id}{file_ext}"
        if file:
            await self._save_file_locally(storage_key, content)
        doc.s3_key = storage_key
        await self.db.flush()

        # 7. Dispatch Celery task
        try:
            from workers.tasks.ingest_task import process_document

            process_document.delay(
                document_id=str(doc.id),
                tenant_id=str(tenant.id),
                namespace_id=str(ns.id),
                storage_key=storage_key,
                file_type=file_ext,
                metadata=request.metadata or {},
            )
        except Exception as e:
            logger.error("celery_dispatch_failed", error=str(e), document_id=str(doc.id))
            # Update status to failed if Celery is unavailable
            await self.doc_repo.update_status(
                doc.id,
                DocumentStatus.FAILED,
                error_message=f"Failed to dispatch processing task: {e}",
            )

        # 8. Update status to processing
        await self.doc_repo.update_status(doc.id, DocumentStatus.PROCESSING)

        logger.info(
            "ingestion_started",
            tenant_id=str(tenant.id),
            document_id=str(doc.id),
            filename=filename,
        )

        return IngestResponse(
            document_id=doc.id,
            status="processing",
            estimated_seconds=15,
        )

    async def get_status(
        self, tenant: Tenant, document_id: uuid.UUID
    ) -> IngestStatusResponse:
        """Check the ingestion status of a document."""
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise NotFoundError(detail=f"Document {document_id} not found.")

        # Verify tenant owns this document
        ns = await self.ns_repo.get_by_id(doc.namespace_id, tenant.id)
        if not ns:
            raise NotFoundError(detail=f"Document {document_id} not found.")

        return IngestStatusResponse(
            document_id=doc.id,
            status=doc.status,
            filename=doc.filename,
            chunk_count=doc.chunk_count,
            error_message=doc.error_message,
        )

    async def _save_file_locally(self, storage_key: str, content: bytes) -> None:
        """Save file to local filesystem storage."""
        storage_path = Path(self.settings.local_storage_path)
        file_path = storage_path / storage_key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(content)
