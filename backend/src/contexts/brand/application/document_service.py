"""
Brand Document service - RAG-ready document management.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.brand.domain.models import BrandDocument
from src.contexts.brand.domain.schemas import (
    BrandDocumentCreate,
    BrandDocumentResponse,
    BrandDocumentUpdate,
)
from src.contexts.brand.infrastructure.repositories import BrandDocumentRepository


class BrandDocumentService:
    """Service for brand document operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = BrandDocumentRepository(session, tenant_id)

    async def create_document(self, data: BrandDocumentCreate) -> BrandDocumentResponse:
        """
        Create a brand document record.
        
        Note: File upload should be handled separately via file storage service.
        This endpoint creates the metadata record after the file is uploaded.
        
        RAG Hook: Document will be queued for indexing in Phase 4.3.
        """
        document = BrandDocument(
            title=data.title,
            description=data.description,
            document_type=data.document_type,
            category=data.category,
            brand_id=data.brand_id,
            product_id=data.product_id,
            copacker_id=data.copacker_id,
            file_path=data.file_path,
            file_size=data.file_size,
            mime_type=data.mime_type,
            content_hash=data.content_hash,
            version=data.version,
            is_latest_version=True,
            parent_document_id=None,
            is_indexed=False,  # Will be set to True by RAG indexing job in Phase 4.3
            indexed_at=None,
            uploaded_by=data.uploaded_by,
            uploaded_at=data.uploaded_at,
            expiry_date=data.expiry_date,
            tags=data.tags,
            is_active=True,
        )

        document = await self.repo.create(document)
        
        # TODO Phase 4.3: Queue for RAG indexing
        # await self.queue_for_indexing(document.id)
        
        return BrandDocumentResponse.model_validate(document)

    async def get_document(
        self, document_id: uuid.UUID
    ) -> Optional[BrandDocumentResponse]:
        """Get document by ID."""
        document = await self.repo.get_by_id(document_id)
        if document:
            return BrandDocumentResponse.model_validate(document)
        return None

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        brand_id: Optional[uuid.UUID] = None,
        product_id: Optional[uuid.UUID] = None,
        copacker_id: Optional[uuid.UUID] = None,
        document_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[BrandDocumentResponse], int]:
        """List documents with filters."""
        documents, total = await self.repo.list(
            skip, limit, brand_id, product_id, copacker_id, document_type, is_active
        )
        return (
            [BrandDocumentResponse.model_validate(d) for d in documents],
            total,
        )

    async def update_document(
        self, document_id: uuid.UUID, data: BrandDocumentUpdate
    ) -> BrandDocumentResponse:
        """Update document metadata."""
        document = await self.repo.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")

        # Update fields
        if data.title is not None:
            document.title = data.title
        if data.description is not None:
            document.description = data.description
        if data.category is not None:
            document.category = data.category
        if data.expiry_date is not None:
            document.expiry_date = data.expiry_date
        if data.tags is not None:
            document.tags = data.tags
        if data.is_active is not None:
            document.is_active = data.is_active

        document = await self.repo.update(document)
        return BrandDocumentResponse.model_validate(document)

    async def search_documents(self, query: str, limit: int = 10) -> list[BrandDocumentResponse]:
        """
        Search documents by title, description, and tags.
        
        Note: This is basic text search. In Phase 4.3, this will be replaced
        with RAG vector search for semantic similarity.
        """
        documents = await self.repo.search_documents(query, limit)
        return [BrandDocumentResponse.model_validate(d) for d in documents]

    async def create_new_version(
        self,
        document_id: uuid.UUID,
        new_version: str,
        file_path: str,
        file_size: Optional[int],
        content_hash: Optional[str],
        uploaded_by: str,
    ) -> BrandDocumentResponse:
        """
        Create a new version of an existing document.
        
        The original document will be marked as not the latest version.
        """
        original = await self.repo.get_by_id(document_id)
        if not original:
            raise ValueError(f"Document with ID {document_id} not found")

        # Mark original as not latest
        original.is_latest_version = False
        await self.repo.update(original)

        # Create new version
        new_document = BrandDocument(
            title=original.title,
            description=original.description,
            document_type=original.document_type,
            category=original.category,
            brand_id=original.brand_id,
            product_id=original.product_id,
            copacker_id=original.copacker_id,
            file_path=file_path,
            file_size=file_size,
            mime_type=original.mime_type,
            content_hash=content_hash,
            version=new_version,
            is_latest_version=True,
            parent_document_id=document_id,
            is_indexed=False,
            indexed_at=None,
            uploaded_by=uploaded_by,
            uploaded_at=datetime.utcnow(),
            expiry_date=original.expiry_date,
            tags=original.tags,
            is_active=True,
        )

        new_document = await self.repo.create(new_document)
        
        # TODO Phase 4.3: Queue for RAG indexing
        # await self.queue_for_indexing(new_document.id)
        
        return BrandDocumentResponse.model_validate(new_document)

    async def approve_document(
        self, document_id: uuid.UUID, approver_email: str
    ) -> BrandDocumentResponse:
        """Approve a document."""
        document = await self.repo.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")

        document.approved_by = approver_email
        document.approved_at = datetime.utcnow()
        document = await self.repo.update(document)
        return BrandDocumentResponse.model_validate(document)

    async def queue_for_indexing(self, document_id: uuid.UUID) -> None:
        """
        Queue document for RAG indexing.
        
        Stub for Phase 4.3 - will trigger background job to:
        1. Extract text from document
        2. Generate embeddings
        3. Store in pgvector
        4. Update is_indexed=True
        """
        # TODO Phase 4.3: Implement RAG indexing queue
        pass

