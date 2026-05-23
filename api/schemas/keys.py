"""Schemas for API key management endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateKeyRequest(BaseModel):
    """Request body for creating a new API key."""

    label: str | None = Field(
        None,
        max_length=100,
        description="Optional label for this key (e.g. 'production', 'staging')",
        examples=["production-server"],
    )


class CreateKeyResponse(BaseModel):
    """
    Response when a new API key is created.

    WARNING: The raw `key` is shown ONCE. It cannot be retrieved again.
    """

    id: uuid.UUID
    key: str = Field(
        ...,
        description="The full API key. Store it securely — it will not be shown again.",
        examples=["rgs_live_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456"],
    )
    prefix: str = Field(
        ...,
        description="Shortened display prefix",
        examples=["rgs_live_aBcDeFgH..."],
    )
    label: str | None
    created_at: datetime


class KeyInfo(BaseModel):
    """API key info shown in listings (never includes the full key)."""

    id: uuid.UUID
    prefix: str
    label: str | None
    is_active: bool
    created_at: datetime
    last_used: datetime | None


class KeyListResponse(BaseModel):
    """Response for listing API keys."""

    keys: list[KeyInfo]


class RotateKeyRequest(BaseModel):
    """Request body for key rotation."""

    old_key_id: uuid.UUID = Field(..., description="ID of the key to rotate (deactivate)")
    label: str | None = Field(None, max_length=100, description="Label for the new key")


class RotateKeyResponse(BaseModel):
    """Response after rotating a key."""

    deactivated_key_id: uuid.UUID
    new_key: CreateKeyResponse
