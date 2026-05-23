"""Schemas for the query endpoint."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request body for RAG query."""

    namespace: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Namespace to query",
        examples=["my-docs"],
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The question to answer",
        examples=["What is our refund policy?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of relevant chunks to retrieve",
    )
    filters: dict[str, str | int | float | bool] | None = Field(
        None,
        description="Metadata filters to narrow search scope",
        examples=[{"source": "legal-team"}],
    )
    stream: bool = Field(
        default=False,
        description="If true, stream the response via SSE",
    )
    model: str | None = Field(
        None,
        description="LLM model to use (defaults to server config)",
        examples=["claude-sonnet", "gpt-4o"],
    )


class SourceChunk(BaseModel):
    """A source chunk returned with the query answer."""

    document_id: uuid.UUID
    filename: str
    chunk: str = Field(..., description="The relevant text chunk")
    score: float = Field(..., description="Similarity score (0-1)")


class QueryResponse(BaseModel):
    """Response from the query endpoint."""

    answer: str = Field(..., description="The generated answer based on retrieved context")
    sources: list[SourceChunk] = Field(
        ...,
        description="Source chunks used to generate the answer",
    )
    latency_ms: int = Field(..., description="Total processing time in milliseconds")
    tokens_used: int = Field(..., description="Total tokens consumed (embedding + LLM)")
