"""Schemas for the ingestion endpoint."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, HttpUrl


# Supported file extensions
SUPPORTED_FILE_TYPES = {".pdf", ".docx", ".txt", ".md", ".html"}


class IngestRequest(BaseModel):
    """Request body for document ingestion."""

    namespace: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Target namespace for this document",
        examples=["my-docs"],
    )
    file_url: HttpUrl | None = Field(
        None,
        description="URL to download the file from (alternative to multipart upload)",
        examples=["https://example.com/document.pdf"],
    )
    metadata: dict[str, str | int | float | bool] | None = Field(
        None,
        description="Custom metadata to attach to the document for filtering",
        examples=[{"source": "legal-team", "year": 2025}],
    )


class IngestResponse(BaseModel):
    """Response after starting document ingestion."""

    document_id: uuid.UUID
    status: str = Field(
        ...,
        description="Current processing status",
        examples=["processing"],
    )
    estimated_seconds: int = Field(
        default=15,
        description="Estimated processing time in seconds",
    )


class IngestStatusResponse(BaseModel):
    """Response for checking ingestion status."""

    document_id: uuid.UUID
    status: str
    filename: str
    chunk_count: int
    error_message: str | None = None
