"""
Retail API router for OSA (On-Shelf Availability).
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.application.osa_service import OSAService
from src.contexts.retail.domain.schemas import (
    OSAEventCreate,
    OSAEventResponse,
    OSAEventUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/osa", tags=["Retail - OSA"])


@router.post(
    "/events",
    response_model=OSAEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create OSA event",
)
async def create_osa_event(
    data: OSAEventCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Record an on-shelf availability (OSA) event."""
    service = OSAService(session, current_user.tenant_id)
    
    try:
        osa_event = await service.create_osa_event(data)
        await session.commit()
        return osa_event
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create OSA event: {str(e)}",
        )


@router.get(
    "/events",
    response_model=list[OSAEventResponse],
    summary="List OSA events",
)
async def list_osa_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    store_id: Optional[uuid.UUID] = Query(None, description="Filter by store ID"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List OSA events with optional filters."""
    service = OSAService(session, current_user.tenant_id)
    
    try:
        osa_events, total = await service.list_osa_events(
            skip, limit, store_id, resolved, start_date, end_date
        )
        return osa_events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list OSA events: {str(e)}",
        )


@router.get(
    "/events/{osa_event_id}",
    response_model=OSAEventResponse,
    summary="Get OSA event details",
)
async def get_osa_event(
    osa_event_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific OSA event."""
    service = OSAService(session, current_user.tenant_id)
    
    osa_event = await service.get_osa_event(osa_event_id)
    if not osa_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OSA event with ID {osa_event_id} not found",
        )
    
    return osa_event


@router.put(
    "/events/{osa_event_id}",
    response_model=OSAEventResponse,
    summary="Update OSA event",
)
async def update_osa_event(
    osa_event_id: uuid.UUID,
    data: OSAEventUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update an OSA event."""
    service = OSAService(session, current_user.tenant_id)
    
    try:
        osa_event = await service.update_osa_event(osa_event_id, data)
        await session.commit()
        return osa_event
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update OSA event: {str(e)}",
        )


@router.put(
    "/events/{osa_event_id}/resolve",
    response_model=OSAEventResponse,
    summary="Resolve OSA event",
)
async def resolve_osa_event(
    osa_event_id: uuid.UUID,
    resolution_notes: Optional[str] = Query(None, description="Resolution notes"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Mark an OSA event as resolved."""
    service = OSAService(session, current_user.tenant_id)
    
    try:
        osa_event = await service.resolve_osa_event(osa_event_id, resolution_notes)
        await session.commit()
        return osa_event
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve OSA event: {str(e)}",
        )

