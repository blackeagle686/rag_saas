"""Document model — tracks ingested files and their processing status."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from db.models.base import Base, TimestampMixin


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"

class FileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    HTML = "html"
    MD = "md"
    PPTX = "pptx"

class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    namespace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("namespaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    file_type: Mapped[FileType] = mapped_column(
        String(10),
        nullable=False
    )
    
    status: Mapped[DocumentStatus] = mapped_column(
        String(20),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True,
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        nullable=False
    )
    s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    namespace = relationship("Namespace", back_populates="documents")


    def __repr__(self) -> str:
        return f"<Document {self.filename} status={self.status}>"
