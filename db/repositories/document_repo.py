"""Repository for Document CRUD with namespace scoping."""

from __future__ import annotations

import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.document import Document, DocumentStatus


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        namespace_id: uuid.UUID,
        filename: str,
        file_type: str,
        s3_key: str | None = None,
    ) -> Document:
        doc = Document(
            namespace_id=namespace_id,
            filename=filename,
            file_type=file_type,
            s3_key=s3_key,
            status=DocumentStatus.PENDING,
        )
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def get_by_id(self, doc_id: uuid.UUID) -> Document | None:
        return await self.session.get(Document, doc_id)

    async def list_for_namespace(
        self,
        namespace_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.namespace_id == namespace_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        doc_id: uuid.UUID,
        status: DocumentStatus,
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> Document | None:
        doc = await self.get_by_id(doc_id)
        if doc:
            doc.status = status
            if chunk_count is not None:
                doc.chunk_count = chunk_count
            if error_message is not None:
                doc.error_message = error_message
            await self.session.flush()
        return doc

    async def delete(self, doc_id: uuid.UUID) -> bool:
        doc = await self.get_by_id(doc_id)
        if doc:
            await self.session.delete(doc)
            await self.session.flush()
            return True
        return False

    async def count_for_namespace(self, namespace_id: uuid.UUID) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).where(Document.namespace_id == namespace_id)
        result = await self.session.execute(stmt)
        return result.scalar_one()
