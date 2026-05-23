"""
Namespace management endpoints.

Handles namespace CRUD, document listing,
and document deletion.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_tenant
from api.middleware.rate_limiter import check_rate_limit
from api.schemas.common import MessageResponse
from api.schemas.namespaces import (
    CreateNamespaceRequest,
    DeleteNamespaceRequest,
    DocumentListResponse,
    NamespaceInfo,
    NamespaceListResponse,
)
from api.services.namespace_service import NamespaceService
from db.engine import get_db_session
from db.models.tenant import Tenant

router = APIRouter(prefix="/v1/namespaces", tags=["Namespaces"])


@router.post(
    "",
    response_model=NamespaceInfo,
    status_code=201,
    summary="Create a namespace",
    description="Create a new namespace for organizing documents.",
)
async def create_namespace(
    request: CreateNamespaceRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> NamespaceInfo:
    service = NamespaceService(db)
    return await service.create_namespace(tenant, request)


@router.get(
    "",
    response_model=NamespaceListResponse,
    summary="List namespaces",
    description="List all namespaces for your account with document and token counts.",
)
async def list_namespaces(
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> NamespaceListResponse:
    service = NamespaceService(db)
    return await service.list_namespaces(tenant)


@router.get(
    "/{name}",
    response_model=NamespaceInfo,
    summary="Get namespace details",
    description="Get detailed stats for a specific namespace.",
)
async def get_namespace(
    name: str,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> NamespaceInfo:
    service = NamespaceService(db)
    return await service.get_namespace(tenant, name)


@router.delete(
    "/{name}",
    response_model=MessageResponse,
    summary="Delete a namespace",
    description=(
        "Permanently delete a namespace and ALL its documents, vectors, and files. "
        "**This is irreversible.** You must set `confirm: true` in the request body."
    ),
)
async def delete_namespace(
    name: str,
    request: DeleteNamespaceRequest,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> MessageResponse:
    service = NamespaceService(db)
    await service.delete_namespace(tenant, name, request)
    return MessageResponse(message=f"Namespace '{name}' and all its data have been deleted.")


@router.get(
    "/{name}/docs",
    response_model=DocumentListResponse,
    summary="List documents in namespace",
    description="List all documents in a namespace with their processing status.",
)
async def list_documents(
    name: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> DocumentListResponse:
    service = NamespaceService(db)
    return await service.list_documents(tenant, name, limit=limit, offset=offset)


# Document deletion (at /v1/documents/ level for convenience)
documents_router = APIRouter(prefix="/v1/documents", tags=["Documents"])


@documents_router.delete(
    "/{doc_id}",
    response_model=MessageResponse,
    summary="Delete a document",
    description="Delete a specific document, its vectors, and stored file.",
)
async def delete_document(
    doc_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(check_rate_limit),
) -> MessageResponse:
    service = NamespaceService(db)
    await service.delete_document(tenant, doc_id)
    return MessageResponse(message=f"Document {doc_id} has been deleted.")
