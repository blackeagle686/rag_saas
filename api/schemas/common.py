"""Common schema types shared across endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Standard error response body."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: dict | None = Field(None, description="Additional error context")


class ErrorResponse(BaseModel):
    """Wrapper for all error responses."""

    error: ErrorDetail


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    limit: int = Field(default=50, ge=1, le=200, description="Max items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class HealthResponse(BaseModel):
    """Response from /health endpoint."""

    status: str = Field(..., description="Service status", examples=["ok"])
    version: str = Field(..., description="API version")


class ReadyResponse(BaseModel):
    """Response from /health/ready endpoint."""

    status: str
    checks: dict[str, str] = Field(
        ...,
        description="Status of each dependency",
        examples=[{"database": "ok", "redis": "ok", "qdrant": "ok"}],
    )


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str
