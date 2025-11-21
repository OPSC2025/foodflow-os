"""
Retail API router for waste tracking.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.application.waste_service import WasteService
from src.contexts.retail.domain.schemas import (
    WasteCreate,
    WasteResponse,
    WasteUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/waste", tags=["Retail - Waste"])


@router.post(
    "",
    response_model=WasteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record waste",
)
async def create_waste(
    data: WasteCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Record a waste event."""
    service = WasteService(session, current_user.tenant_id)
    
    try:
        waste = await service.create_waste(data)
        await session.commit()
        return waste
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create waste record: {str(e)}",
        )


@router.get(
    "",
    response_model=list[WasteResponse],
    summary="List waste records",
)
async def list_waste(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    store_id: Optional[uuid.UUID] = Query(None, description="Filter by store ID"),
    reason: Optional[str] = Query(None, description="Filter by waste reason"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List waste records with optional filters."""
    service = WasteService(session, current_user.tenant_id)
    
    try:
        waste_records, total = await service.list_waste(
            skip, limit, store_id, reason, start_date, end_date
        )
        return waste_records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list waste records: {str(e)}",
        )


@router.get(
    "/{waste_id}",
    response_model=WasteResponse,
    summary="Get waste record details",
)
async def get_waste(
    waste_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific waste record."""
    service = WasteService(session, current_user.tenant_id)
    
    waste = await service.get_waste(waste_id)
    if not waste:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Waste record with ID {waste_id} not found",
        )
    
    return waste


@router.put(
    "/{waste_id}",
    response_model=WasteResponse,
    summary="Update waste record",
)
async def update_waste(
    waste_id: uuid.UUID,
    data: WasteUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update a waste record."""
    service = WasteService(session, current_user.tenant_id)
    
    try:
        waste = await service.update_waste(waste_id, data)
        await session.commit()
        return waste
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update waste record: {str(e)}",
        )

