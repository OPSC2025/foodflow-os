"""
Brand API router for documents (RAG-ready).
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.brand.application.document_service import BrandDocumentService
from src.contexts.brand.domain.schemas import (
    BrandDocumentCreate,
    BrandDocumentResponse,
    BrandDocumentUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/documents", tags=["Brand Documents"])


@router.post(
    "",
    response_model=BrandDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create document record",
)
async def create_document(
    data: BrandDocumentCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a brand document record.
    
    Note: File upload should be handled separately via file storage service (S3/MinIO).
    This endpoint creates the metadata record after the file is uploaded.
    
    RAG Hook: Document will be queued for indexing in Phase 4.3.
    """
    service = BrandDocumentService(session, current_user.tenant_id)
    
    try:
        document = await service.create_document(data)
        await session.commit()
        return document
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}",
        )


@router.get(
    "",
    response_model=list[BrandDocumentResponse],
    summary="List documents",
)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    brand_id: Optional[uuid.UUID] = Query(None, description="Filter by brand ID"),
    product_id: Optional[uuid.UUID] = Query(None, description="Filter by product ID"),
    copacker_id: Optional[uuid.UUID] = Query(None, description="Filter by co-packer ID"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List brand documents with optional filters."""
    service = BrandDocumentService(session, current_user.tenant_id)
    
    try:
        documents, total = await service.list_documents(
            skip, limit, brand_id, product_id, copacker_id, document_type, is_active
        )
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        )


@router.get(
    "/search",
    response_model=list[BrandDocumentResponse],
    summary="Search documents",
)
async def search_documents(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Search documents by title, description, and tags.
    
    Note: This is basic text search. In Phase 4.3, this will be replaced
    with RAG vector search for semantic similarity.
    """
    service = BrandDocumentService(session, current_user.tenant_id)
    
    try:
        documents = await service.search_documents(query, limit)
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search documents: {str(e)}",
        )


@router.get(
    "/{document_id}",
    response_model=BrandDocumentResponse,
    summary="Get document details",
)
async def get_document(
    document_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific document."""
    service = BrandDocumentService(session, current_user.tenant_id)
    
    document = await service.get_document(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found",
        )
    
    return document


@router.put(
    "/{document_id}",
    response_model=BrandDocumentResponse,
    summary="Update document",
)
async def update_document(
    document_id: uuid.UUID,
    data: BrandDocumentUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update document metadata."""
    service = BrandDocumentService(session, current_user.tenant_id)
    
    try:
        document = await service.update_document(document_id, data)
        await session.commit()
        return document
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}",
        )


@router.put(
    "/{document_id}/approve",
    response_model=BrandDocumentResponse,
    summary="Approve document",
)
async def approve_document(
    document_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Approve a document for use."""
    service = BrandDocumentService(session, current_user.tenant_id)
    
    try:
        document = await service.approve_document(document_id, current_user.email)
        await session.commit()
        return document
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve document: {str(e)}",
        )


@router.post(
    "/{document_id}/new-version",
    response_model=BrandDocumentResponse,
    summary="Create new document version",
)
async def create_new_document_version(
    document_id: uuid.UUID,
    new_version: str = Query(..., description="New version number (e.g., '2.0')"),
    file_path: str = Query(..., description="Path to new file in storage"),
    file_size: Optional[int] = Query(None, description="File size in bytes"),
    content_hash: Optional[str] = Query(None, description="SHA-256 hash of file"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new version of an existing document.
    
    The original document will be marked as not the latest version.
    RAG Hook: New version will be queued for indexing in Phase 4.3.
    """
    service = BrandDocumentService(session, current_user.tenant_id)
    
    try:
        document = await service.create_new_version(
            document_id, new_version, file_path, file_size, content_hash, current_user.email
        )
        await session.commit()
        return document
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create new version: {str(e)}",
        )

