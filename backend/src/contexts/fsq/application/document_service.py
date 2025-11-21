"""
Document service for FSQ document management.

RAG-ready: Designed for future vector embedding and semantic search integration.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.fsq.domain.models import Document
from src.contexts.fsq.domain.schemas import DocumentCreate, DocumentUpdate
from src.core.logging import logger


class DocumentService:
    """Service for document operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create_document(self, data: DocumentCreate) -> Document:
        """Create a new document record."""
        # Check for duplicate document number
        stmt = select(Document).filter_by(
            tenant_id=self.tenant_id, document_number=data.document_number
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Document number '{data.document_number}' already exists")

        document = Document(**data.model_dump(), tenant_id=self.tenant_id)
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)

        logger.info(
            f"Created document {document.document_number} - Type: {document.document_type}",
            extra={
                "tenant_id": str(self.tenant_id),
                "document_id": str(document.id),
                "document_type": document.document_type,
            },
        )

        # TODO: Queue for RAG indexing (future phase)
        # await self._queue_for_rag_indexing(document)

        return document

    async def get_document(self, document_id: uuid.UUID) -> Optional[Document]:
        """Get a document by ID."""
        stmt = select(Document).filter_by(tenant_id=self.tenant_id, id=document_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_document_by_number(self, document_number: str) -> Optional[Document]:
        """Get a document by document number."""
        stmt = select(Document).filter_by(
            tenant_id=self.tenant_id, document_number=document_number
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        needs_review: bool = False,
    ) -> tuple[list[Document], int]:
        """List documents with pagination and filters."""
        stmt = select(Document).filter_by(tenant_id=self.tenant_id)

        if document_type:
            stmt = stmt.filter_by(document_type=document_type)
        if category:
            stmt = stmt.filter_by(category=category)
        if is_active is not None:
            stmt = stmt.filter_by(is_active=is_active)
        if needs_review:
            now = datetime.utcnow()
            stmt = stmt.filter(
                Document.next_review_date.isnot(None),
                Document.next_review_date <= now,
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Get page
        stmt = stmt.order_by(Document.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        documents = list(result.scalars().all())

        return documents, total

    async def update_document(
        self, document_id: uuid.UUID, data: DocumentUpdate
    ) -> Document:
        """Update a document."""
        document = await self.get_document(document_id)
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(document, field, value)

        await self.session.flush()

        return document

    async def approve_document(
        self, document_id: uuid.UUID, approved_by: str
    ) -> Document:
        """Approve a document."""
        document = await self.get_document(document_id)
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")

        document.approved_by = approved_by
        document.approved_date = datetime.utcnow()

        await self.session.flush()

        logger.info(
            f"Approved document {document.document_number} by {approved_by}",
            extra={"tenant_id": str(self.tenant_id), "document_id": str(document_id)},
        )

        return document

    async def create_new_version(
        self,
        original_document_id: uuid.UUID,
        new_version: str,
        file_path: str,
        file_size: Optional[int] = None,
        content_hash: Optional[str] = None,
        uploaded_by: str = "",
    ) -> Document:
        """Create a new version of an existing document."""
        original = await self.get_document(original_document_id)
        if not original:
            raise ValueError(f"Original document with ID {original_document_id} not found")

        # Mark original as not latest
        original.is_latest_version = False
        await self.session.flush()

        # Create new version
        new_document = Document(
            tenant_id=self.tenant_id,
            document_number=original.document_number,
            title=original.title,
            description=original.description,
            document_type=original.document_type,
            category=original.category,
            file_name=original.file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=original.mime_type,
            content_hash=content_hash,
            version=new_version,
            is_latest_version=True,
            replaces_document_id=original_document_id,
            tags=original.tags,
            uploaded_by=uploaded_by,
        )

        self.session.add(new_document)
        await self.session.flush()
        await self.session.refresh(new_document)

        logger.info(
            f"Created new version {new_version} for document {original.document_number}",
            extra={"tenant_id": str(self.tenant_id), "document_id": str(new_document.id)},
        )

        # TODO: Queue for RAG indexing
        # await self._queue_for_rag_indexing(new_document)

        return new_document

    async def mark_as_indexed(
        self,
        document_id: uuid.UUID,
        embedding_model: str,
        chunk_count: int,
    ) -> Document:
        """
        Mark a document as indexed for RAG.
        
        This will be called by the RAG ingestion service once embeddings are generated.
        """
        document = await self.get_document(document_id)
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")

        document.indexed_at = datetime.utcnow()
        document.embedding_model = embedding_model
        document.chunk_count = chunk_count

        await self.session.flush()

        logger.info(
            f"Marked document {document.document_number} as indexed - {chunk_count} chunks",
            extra={
                "tenant_id": str(self.tenant_id),
                "document_id": str(document_id),
                "embedding_model": embedding_model,
            },
        )

        return document

    async def get_documents_needing_review_count(self) -> int:
        """Get count of documents needing review."""
        now = datetime.utcnow()
        stmt = select(func.count()).select_from(Document).filter(
            Document.tenant_id == self.tenant_id,
            Document.is_active == True,
            Document.next_review_date.isnot(None),
            Document.next_review_date <= now,
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def search_documents(
        self, search_term: str, limit: int = 10
    ) -> list[Document]:
        """
        Basic text search in documents.
        
        TODO: In Phase 4.3, this will be replaced with RAG vector search.
        For now, searches in title, description, and tags.
        """
        search_pattern = f"%{search_term}%"

        stmt = (
            select(Document)
            .filter(
                Document.tenant_id == self.tenant_id,
                Document.is_active == True,
            )
            .filter(
                (Document.title.ilike(search_pattern))
                | (Document.description.ilike(search_pattern))
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        documents = list(result.scalars().all())

        logger.info(
            f"Document search for '{search_term}' returned {len(documents)} results",
            extra={"tenant_id": str(self.tenant_id), "search_term": search_term},
        )

        return documents

    # Future RAG integration (Phase 4.3)
    # async def _queue_for_rag_indexing(self, document: Document) -> None:
    #     """Queue document for RAG ingestion."""
    #     # This will call the RAG ingestion service to:
    #     # 1. Extract text from file
    #     # 2. Chunk the content
    #     # 3. Generate embeddings
    #     # 4. Store in pgvector
    #     pass

