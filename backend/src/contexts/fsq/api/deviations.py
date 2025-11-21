"""
FSQ API router for deviations.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.fsq.application.deviation_service import DeviationService
from src.contexts.fsq.domain.schemas import (
    DeviationCreate,
    DeviationResponse,
    DeviationUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/deviations", tags=["Deviations"])


@router.post(
    "",
    response_model=DeviationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a deviation",
)
async def create_deviation(
    data: DeviationCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Report a quality or safety deviation.
    
    A deviation is any non-conformance to specifications, procedures, or standards.
    """
    service = DeviationService(session, current_user.tenant_id)
    
    try:
        deviation = await service.create_deviation(data)
        await session.commit()
        return deviation
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create deviation: {str(e)}",
        )


@router.get(
    "",
    response_model=list[DeviationResponse],
    summary="List deviations",
)
async def list_deviations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[datetime] = Query(None, description="Filter by occurred date (>=)"),
    end_date: Optional[datetime] = Query(None, description="Filter by occurred date (<=)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List deviations with optional filters.
    """
    service = DeviationService(session, current_user.tenant_id)
    
    try:
        deviations, total = await service.list_deviations(
            skip, limit, status, severity, category, start_date, end_date
        )
        return deviations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list deviations: {str(e)}",
        )


@router.get(
    "/{deviation_id}",
    response_model=DeviationResponse,
    summary="Get deviation details",
)
async def get_deviation(
    deviation_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information about a specific deviation.
    """
    service = DeviationService(session, current_user.tenant_id)
    
    deviation = await service.get_deviation(deviation_id)
    if not deviation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deviation with ID {deviation_id} not found",
        )
    
    return deviation


@router.put(
    "/{deviation_id}",
    response_model=DeviationResponse,
    summary="Update deviation",
)
async def update_deviation(
    deviation_id: uuid.UUID,
    data: DeviationUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update deviation details including investigation notes, root cause, etc.
    """
    service = DeviationService(session, current_user.tenant_id)
    
    try:
        deviation = await service.update_deviation(deviation_id, data)
        await session.commit()
        return deviation
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update deviation: {str(e)}",
        )


@router.put(
    "/{deviation_id}/close",
    response_model=DeviationResponse,
    summary="Close a deviation",
)
async def close_deviation(
    deviation_id: uuid.UUID,
    resolution_notes: Optional[str] = Query(None, description="Resolution notes"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Close a deviation after investigation and resolution.
    """
    service = DeviationService(session, current_user.tenant_id)
    
    try:
        deviation = await service.close_deviation(
            deviation_id, current_user.email, resolution_notes
        )
        await session.commit()
        return deviation
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close deviation: {str(e)}",
        )


@router.post(
    "/{deviation_id}/link-capa/{capa_id}",
    response_model=DeviationResponse,
    summary="Link deviation to CAPA",
)
async def link_deviation_to_capa(
    deviation_id: uuid.UUID,
    capa_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Link a deviation to a CAPA (Corrective and Preventive Action).
    """
    service = DeviationService(session, current_user.tenant_id)
    
    try:
        deviation = await service.link_to_capa(deviation_id, capa_id)
        await session.commit()
        return deviation
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link deviation to CAPA: {str(e)}",
        )

