"""
Namespace service — business logic for namespace management.

Handles CRUD, document listing, and cascading deletes
(Qdrant vectors + S3 files + DB records).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.namespaces import (
    CreateNamespaceRequest,
    DeleteNamespaceRequest,
    DocumentInfo,
    DocumentListResponse,
    NamespaceInfo,
    NamespaceListResponse,
)
from core.exceptions import ConflictError, NotFoundError, ValidationError
from core.logging import get_logger
from db.models.tenant import Tenant
from db.repositories.document_repo import DocumentRepository
from db.repositories.namespace_repo import NamespaceRepository

logger = get_logger("namespace_service")


class NamespaceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ns_repo = NamespaceRepository(db)
        self.doc_repo = DocumentRepository(db)

    async def create_namespace(
        self, tenant: Tenant, request: CreateNamespaceRequest
    ) -> NamespaceInfo:
        """Create a new namespace for the tenant."""
        # Check for duplicate
        existing = await self.ns_repo.get_by_name(tenant.id, request.name)
        if existing:
            raise ConflictError(detail=f"Namespace '{request.name}' already exists.")

        ns = await self.ns_repo.create(tenant.id, request.name)

        logger.info(
            "namespace_created",
            tenant_id=str(tenant.id),
            namespace=request.name,
        )

        return NamespaceInfo(
            id=ns.id,
            name=ns.name,
            doc_count=ns.doc_count,
            token_count=ns.token_count,
            created_at=ns.created_at,
        )

    async def list_namespaces(self, tenant: Tenant) -> NamespaceListResponse:
        """List all namespaces for the tenant."""
        namespaces = await self.ns_repo.list_for_tenant(tenant.id)

        return NamespaceListResponse(
            namespaces=[
                NamespaceInfo(
                    id=ns.id,
                    name=ns.name,
                    doc_count=ns.doc_count,
                    token_count=ns.token_count,
                    created_at=ns.created_at,
                )
                for ns in namespaces
            ]
        )

    async def get_namespace(
        self, tenant: Tenant, name: str
    ) -> NamespaceInfo:
        """Get stats for a specific namespace."""
        ns = await self.ns_repo.get_by_name(tenant.id, name)
        if not ns:
            raise NotFoundError(detail=f"Namespace '{name}' not found.")

        return NamespaceInfo(
            id=ns.id,
            name=ns.name,
            doc_count=ns.doc_count,
            token_count=ns.token_count,
            created_at=ns.created_at,
        )

    async def delete_namespace(
        self, tenant: Tenant, name: str, request: DeleteNamespaceRequest
    ) -> None:
        """
        Delete a namespace and ALL its data.

        This is irreversible. Deletes:
        1. All Qdrant vectors under this namespace
        2. All S3 files under this namespace
        3. All DB records (cascading via FK)
        """
        if not request.confirm:
            raise ValidationError(
                detail="You must set 'confirm: true' to delete a namespace. This is irreversible."
            )

        ns = await self.ns_repo.get_by_name(tenant.id, name)
        if not ns:
            raise NotFoundError(detail=f"Namespace '{name}' not found.")

        # TODO: Delete Qdrant collection/points for this namespace
        # TODO: Delete S3 files under {tenant_id}/{namespace_id}/

        # Delete DB records (cascades to documents)
        await self.ns_repo.delete(tenant.id, name)

        logger.info(
            "namespace_deleted",
            tenant_id=str(tenant.id),
            namespace=name,
        )

    async def list_documents(
        self, tenant: Tenant, name: str, limit: int = 50, offset: int = 0
    ) -> DocumentListResponse:
        """List documents in a namespace."""
        ns = await self.ns_repo.get_by_name(tenant.id, name)
        if not ns:
            raise NotFoundError(detail=f"Namespace '{name}' not found.")

        docs = await self.doc_repo.list_for_namespace(ns.id, limit=limit, offset=offset)
        total = await self.doc_repo.count_for_namespace(ns.id)

        return DocumentListResponse(
            documents=[
                DocumentInfo(
                    id=d.id,
                    filename=d.filename,
                    file_type=d.file_type,
                    status=d.status,
                    chunk_count=d.chunk_count,
                    created_at=d.created_at,
                    error_message=d.error_message,
                )
                for d in docs
            ],
            total=total,
        )

    async def delete_document(
        self, tenant: Tenant, doc_id: uuid.UUID
    ) -> None:
        """Delete a specific document."""
        doc = await self.doc_repo.get_by_id(doc_id)
        if not doc:
            raise NotFoundError(detail=f"Document {doc_id} not found.")

        # Verify tenant owns this document via namespace
        ns = await self.ns_repo.get_by_id(doc.namespace_id, tenant.id)
        if not ns:
            raise NotFoundError(detail=f"Document {doc_id} not found.")

        # TODO: Delete Qdrant points for this document
        # TODO: Delete S3 file

        await self.doc_repo.delete(doc_id)
        await self.ns_repo.update_counts(ns.id, doc_count_delta=-1)

        logger.info(
            "document_deleted",
            tenant_id=str(tenant.id),
            document_id=str(doc_id),
        )
