"""
PlantOps API router for production batches.

Handles HTTP endpoints for production batch operations.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.application.services import ProductionBatchService
from src.contexts.plant_ops.domain.schemas import (
    PaginatedResponse,
    ProductionBatchCreate,
    ProductionBatchResponse,
    ProductionBatchUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/batches", tags=["Production Batches"])


@router.post(
    "",
    response_model=ProductionBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new production batch",
)
async def create_batch(
    data: ProductionBatchCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new production batch.
    
    The batch will be created in PLANNED status.
    """
    service = ProductionBatchService(session, current_user.tenant_id)
    
    try:
        batch = await service.create_batch(data)
        await session.commit()
        return batch
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List production batches",
)
async def list_batches(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    line_id: Optional[uuid.UUID] = Query(None, description="Filter by line ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO format)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List production batches with pagination and optional filters.
    
    Returns a paginated list of production batches for the current tenant.
    """
    service = ProductionBatchService(session, current_user.tenant_id)
    
    skip = (page - 1) * page_size
    batches, total = await service.list_batches(
        skip, page_size, line_id, status, start_date, end_date
    )
    
    import math
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return PaginatedResponse(
        items=[ProductionBatchResponse.model_validate(batch) for batch in batches],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{batch_id}",
    response_model=ProductionBatchResponse,
    summary="Get a production batch by ID",
)
async def get_batch(
    batch_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get a specific production batch by ID.
    
    Returns 404 if the batch doesn't exist or doesn't belong to the current tenant.
    """
    service = ProductionBatchService(session, current_user.tenant_id)
    
    batch = await service.get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production batch with ID {batch_id} not found",
        )
    
    return batch


@router.get(
    "/by-number/{batch_number}",
    response_model=ProductionBatchResponse,
    summary="Get a production batch by batch number",
)
async def get_batch_by_number(
    batch_number: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get a specific production batch by batch number.
    
    Returns 404 if the batch doesn't exist or doesn't belong to the current tenant.
    """
    service = ProductionBatchService(session, current_user.tenant_id)
    
    batch = await service.get_batch_by_number(batch_number)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production batch with number '{batch_number}' not found",
        )
    
    return batch


@router.post(
    "/{batch_id}/start",
    response_model=ProductionBatchResponse,
    summary="Start a production batch",
)
async def start_batch(
    batch_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Start a production batch.
    
    The batch must be in PLANNED status. This will:
    - Change batch status to IN_PROGRESS
    - Set actual_start_time to current time
    - Update the line status to RUNNING
    - Publish a BatchStartedEvent
    """
    service = ProductionBatchService(session, current_user.tenant_id)
    
    try:
        batch = await service.start_batch(batch_id)
        await session.commit()
        return batch
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/{batch_id}/complete",
    response_model=ProductionBatchResponse,
    summary="Complete a production batch",
)
async def complete_batch(
    batch_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Complete a production batch.
    
    The batch must be in IN_PROGRESS status. This will:
    - Change batch status to COMPLETED
    - Set actual_end_time to current time
    - Calculate OEE if not already set
    - Update the line status to IDLE
    - Publish a BatchCompletedEvent
    """
    service = ProductionBatchService(session, current_user.tenant_id)
    
    try:
        batch = await service.complete_batch(batch_id)
        await session.commit()
        return batch
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch(
    "/{batch_id}",
    response_model=ProductionBatchResponse,
    summary="Update a production batch",
)
async def update_batch(
    batch_id: uuid.UUID,
    data: ProductionBatchUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update a production batch.
    
    Only provided fields will be updated. Omitted fields remain unchanged.
    OEE will be recalculated if availability, performance, or quality are updated.
    """
    service = ProductionBatchService(session, current_user.tenant_id)
    
    try:
        batch = await service.update_batch(batch_id, data)
        await session.commit()
        return batch
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
