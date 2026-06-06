"""Schemas for namespace management endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from core.security import validate_namespace_name


class CreateNamespaceRequest(BaseModel):
    """Request body for creating a namespace."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Namespace name (alphanumeric, hyphens, underscores)",
        examples=["my-docs"],
    )
    llm_provider: str = Field(default="openai", description="LLM provider")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    llm_api_key: str | None = Field(None, description="LLM API key")
    llm_base_url: str | None = Field(None, description="LLM Base URL (optional)")

    embedding_provider: str = Field(default="dashscope", description="Embedding provider")
    embedding_model: str = Field(default="text-embedding-v4", description="Embedding model name")
    embedding_api_key: str | None = Field(None, description="Embedding API key")
    embedding_base_url: str | None = Field(None, description="Embedding Base URL (optional)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not validate_namespace_name(v):
            raise ValueError(
                "Namespace name must be alphanumeric (hyphens and underscores allowed), "
                "start with a letter or number, and be 1-64 characters."
            )
        return v


class NamespaceInfo(BaseModel):
    """Namespace details."""

    id: uuid.UUID
    name: str
    doc_count: int
    token_count: int
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    created_at: datetime


class NamespaceListResponse(BaseModel):
    """Response for listing namespaces."""

    namespaces: list[NamespaceInfo]


class DeleteNamespaceRequest(BaseModel):
    """Request body for deleting a namespace (requires confirmation)."""

    confirm: bool = Field(
        ...,
        description="Must be true to confirm deletion. This is irreversible.",
    )


class DocumentInfo(BaseModel):
    """Document details shown in listings."""

    id: uuid.UUID
    filename: str
    file_type: str
    status: str
    chunk_count: int
    created_at: datetime
    error_message: str | None = None


class DocumentListResponse(BaseModel):
    """Response for listing documents in a namespace."""

    documents: list[DocumentInfo]
    total: int
