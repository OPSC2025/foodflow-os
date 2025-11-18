"""
PlantOps API router for production lines.

Handles HTTP endpoints for production line operations.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.application.services import ProductionLineService
from src.contexts.plant_ops.domain.schemas import (
    PaginatedResponse,
    ProductionLineCreate,
    ProductionLineResponse,
    ProductionLineUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/lines", tags=["Production Lines"])


@router.post(
    "",
    response_model=ProductionLineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new production line",
)
async def create_line(
    data: ProductionLineCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new production line.
    
    Requires authentication and appropriate permissions.
    """
    service = ProductionLineService(session, current_user.tenant_id)
    
    try:
        line = await service.create_line(data)
        await session.commit()
        return line
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List production lines",
)
async def list_lines(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List production lines with pagination and optional filters.
    
    Returns a paginated list of production lines for the current tenant.
    """
    service = ProductionLineService(session, current_user.tenant_id)
    
    skip = (page - 1) * page_size
    lines, total = await service.list_lines(skip, page_size, status, is_active)
    
    import math
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return PaginatedResponse(
        items=[ProductionLineResponse.model_validate(line) for line in lines],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{line_id}",
    response_model=ProductionLineResponse,
    summary="Get a production line by ID",
)
async def get_line(
    line_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get a specific production line by ID.
    
    Returns 404 if the line doesn't exist or doesn't belong to the current tenant.
    """
    service = ProductionLineService(session, current_user.tenant_id)
    
    line = await service.get_line(line_id)
    if not line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production line with ID {line_id} not found",
        )
    
    return line


@router.get(
    "/by-number/{line_number}",
    response_model=ProductionLineResponse,
    summary="Get a production line by line number",
)
async def get_line_by_number(
    line_number: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get a specific production line by line number.
    
    Returns 404 if the line doesn't exist or doesn't belong to the current tenant.
    """
    service = ProductionLineService(session, current_user.tenant_id)
    
    line = await service.get_line_by_number(line_number)
    if not line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production line with number '{line_number}' not found",
        )
    
    return line


@router.patch(
    "/{line_id}",
    response_model=ProductionLineResponse,
    summary="Update a production line",
)
async def update_line(
    line_id: uuid.UUID,
    data: ProductionLineUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update a production line.
    
    Only provided fields will be updated. Omitted fields remain unchanged.
    """
    service = ProductionLineService(session, current_user.tenant_id)
    
    try:
        line = await service.update_line(line_id, data)
        await session.commit()
        return line
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/{line_id}/status",
    response_model=ProductionLineResponse,
    summary="Update production line status",
)
async def update_line_status(
    line_id: uuid.UUID,
    new_status: str = Query(..., description="New status for the line"),
    reason: Optional[str] = Query(None, description="Reason for status change"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update the status of a production line.
    
    Creates a line event to track the status change.
    """
    service = ProductionLineService(session, current_user.tenant_id)
    
    try:
        line = await service.update_line_status(line_id, new_status, reason)
        await session.commit()
        return line
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete(
    "/{line_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a production line",
)
async def delete_line(
    line_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Delete a production line.
    
    This will also delete all associated sensors and events.
    Use with caution as this operation cannot be undone.
    """
    service = ProductionLineService(session, current_user.tenant_id)
    
    try:
        deleted = await service.delete_line(line_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Production line with ID {line_id} not found",
            )
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
