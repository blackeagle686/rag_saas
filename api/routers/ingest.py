"""
Document ingestion endpoint.

Accepts file uploads or URLs and dispatches
async processing via Celery workers.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_tenant
from api.middleware.rate_limiter import check_rate_limit
from api.schemas.ingest import IngestRequest, IngestResponse, IngestStatusResponse
from api.services.ingest_service import IngestService
from db.engine import get_db_session
from db.models.tenant import Tenant
from core.exceptions import ValidationError
router = APIRouter(prefix="/v1", tags=["Ingestion"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=202,
    summary="Ingest a document",
    description=(
        "Upload a document for ingestion. The document will be processed asynchronously: "
        "text extracted, chunked, embedded, and indexed for search. "
        "Supported formats: PDF, DOCX, TXT, MD, HTML. Max size: 50MB."
    ),
)
async def ingest_document(
    namespace: str = Form(..., description="Target namespace"),
    file: UploadFile | None = File(None, description="File to upload"),
    file_url: str | None = Form(None, description="URL to download file from"),
    metadata: str | None = Form(None, description="JSON metadata string"),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> IngestResponse:
    import json

    # Parse metadata if provided
    parsed_metadata = None
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            

            raise ValidationError(detail="'metadata' must be valid JSON.")

    # Build request object
    request = IngestRequest(
        namespace=namespace,
        file_url=file_url,
        metadata=parsed_metadata,
    )

    service = IngestService(db)
    return await service.ingest_file(tenant, request, file=file)


@router.get(
    "/ingest/{document_id}",
    response_model=IngestStatusResponse,
    summary="Check ingestion status",
    description="Check the processing status of a previously submitted document.",
)
async def get_ingest_status(
    document_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> IngestStatusResponse:
    service = IngestService(db)
    return await service.get_status(tenant, document_id)
