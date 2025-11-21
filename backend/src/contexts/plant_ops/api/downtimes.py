"""
PlantOps API router for downtime tracking.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.application.downtime_service import DowntimeService
from src.contexts.plant_ops.domain.schemas import (
    DowntimeCreate,
    DowntimeResponse,
    DowntimeUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/downtimes", tags=["Downtimes"])


@router.post(
    "",
    response_model=DowntimeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a downtime record",
)
async def create_downtime(
    data: DowntimeCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new downtime record.
    
    Records when a line is not producing due to various reasons like
    mechanical issues, electrical problems, changeover, lack of materials, etc.
    """
    service = DowntimeService(session, current_user.tenant_id)
    
    try:
        downtime = await service.create_downtime(data)
        await session.commit()
        return downtime
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create downtime: {str(e)}",
        )


@router.get(
    "",
    response_model=list[DowntimeResponse],
    summary="List downtime records",
)
async def list_downtimes(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    line_id: Optional[uuid.UUID] = Query(None, description="Filter by line ID"),
    is_planned: Optional[bool] = Query(None, description="Filter by planned vs unplanned downtime"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time (>=)"),
    end_time: Optional[datetime] = Query(None, description="Filter by start time (<=)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List downtime records with optional filters.
    
    Returns a list of downtime records, optionally filtered by line, time period, and planned/unplanned status.
    """
    service = DowntimeService(session, current_user.tenant_id)
    
    try:
        downtimes, total = await service.list_downtimes(
            skip, limit, line_id, is_planned, start_time, end_time
        )
        return downtimes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list downtimes: {str(e)}",
        )


@router.get(
    "/{downtime_id}",
    response_model=DowntimeResponse,
    summary="Get downtime details",
)
async def get_downtime(
    downtime_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information about a specific downtime record.
    """
    service = DowntimeService(session, current_user.tenant_id)
    
    downtime = await service.get_downtime(downtime_id)
    if not downtime:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Downtime with ID {downtime_id} not found",
        )
    
    return downtime


@router.put(
    "/{downtime_id}/end",
    response_model=DowntimeResponse,
    summary="End a downtime period",
)
async def end_downtime(
    downtime_id: uuid.UUID,
    data: DowntimeUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    End a downtime period and update resolution details.
    
    Calculates duration, records resolution, and can include:
    - end_time: when downtime ended (defaults to now)
    - resolution: how the issue was resolved
    - preventive_action: actions to prevent recurrence
    - resolved_by: who resolved the issue
    - cost_impact: financial impact of the downtime
    """
    service = DowntimeService(session, current_user.tenant_id)
    
    try:
        downtime = await service.end_downtime(downtime_id, data)
        await session.commit()
        return downtime
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end downtime: {str(e)}",
        )


@router.put(
    "/{downtime_id}",
    response_model=DowntimeResponse,
    summary="Update downtime details",
)
async def update_downtime(
    downtime_id: uuid.UUID,
    data: DowntimeUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update downtime record details.
    
    Can update reason, root cause, resolution, preventive actions, etc.
    """
    service = DowntimeService(session, current_user.tenant_id)
    
    try:
        downtime = await service.update_downtime(downtime_id, data)
        await session.commit()
        return downtime
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update downtime: {str(e)}",
        )

