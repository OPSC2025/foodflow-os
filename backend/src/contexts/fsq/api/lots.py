"""
FSQ API router for lots and traceability.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.fsq.application.lot_service import LotService
from src.contexts.fsq.domain.schemas import (
    LotCreate,
    LotResponse,
    LotUpdate,
    LotTraceResult,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/lots", tags=["Lots & Traceability"])


@router.post(
    "",
    response_model=LotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lot",
)
async def create_lot(
    data: LotCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new lot for ingredient or finished product.
    
    Critical for traceability: each lot must have a unique lot number.
    """
    service = LotService(session, current_user.tenant_id)
    
    try:
        lot = await service.create_lot(data)
        await session.commit()
        return lot
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lot: {str(e)}",
        )


@router.get(
    "",
    response_model=list[LotResponse],
    summary="List lots",
)
async def list_lots(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    supplier_id: Optional[uuid.UUID] = Query(None, description="Filter by supplier"),
    ingredient_id: Optional[uuid.UUID] = Query(None, description="Filter by ingredient"),
    is_on_hold: Optional[bool] = Query(None, description="Filter by hold status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List lots with optional filters.
    """
    service = LotService(session, current_user.tenant_id)
    
    try:
        lots, total = await service.list_lots(skip, limit, status, supplier_id, ingredient_id, is_on_hold)
        return lots
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list lots: {str(e)}",
        )


@router.get(
    "/{lot_id}",
    response_model=LotResponse,
    summary="Get lot details",
)
async def get_lot(
    lot_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information about a specific lot.
    """
    service = LotService(session, current_user.tenant_id)
    
    lot = await service.get_lot(lot_id)
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lot with ID {lot_id} not found",
        )
    
    return lot


@router.get(
    "/{lot_id}/trace/forward",
    response_model=LotTraceResult,
    summary="⭐ Forward trace - Where did this lot go?",
)
async def trace_forward(
    lot_id: uuid.UUID,
    max_depth: int = Query(10, ge=1, le=50, description="Maximum trace depth"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    **CRITICAL FOR RECALLS**: Forward trace to find where a lot was used.
    
    Recursively traces child lots to identify all downstream usage.
    Essential for:
    - Mock recall simulations
    - Impact assessment
    - Regulatory compliance (FDA, FSMA)
    """
    service = LotService(session, current_user.tenant_id)
    
    try:
        trace_result = await service.trace_forward(lot_id, max_depth)
        return trace_result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trace forward: {str(e)}",
        )


@router.get(
    "/{lot_id}/trace/backward",
    response_model=LotTraceResult,
    summary="⭐ Backward trace - Where did this lot come from?",
)
async def trace_backward(
    lot_id: uuid.UUID,
    max_depth: int = Query(10, ge=1, le=50, description="Maximum trace depth"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    **CRITICAL FOR ROOT CAUSE**: Backward trace to find lot origins.
    
    Recursively traces parent lots to identify all upstream sources.
    Essential for:
    - Root cause investigation
    - Supplier quality issues
    - Contamination source identification
    """
    service = LotService(session, current_user.tenant_id)
    
    try:
        trace_result = await service.trace_backward(lot_id, max_depth)
        return trace_result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trace backward: {str(e)}",
        )


@router.put(
    "/{lot_id}/hold",
    response_model=LotResponse,
    summary="Put lot on hold (quarantine)",
)
async def put_lot_on_hold(
    lot_id: uuid.UUID,
    reason: str = Query(..., min_length=1, description="Reason for hold"),
    held_by: Optional[str] = Query(None, description="Who put the lot on hold"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Put a lot on hold (quarantine) due to quality or safety concerns.
    
    Prevents the lot from being used in production until released.
    """
    service = LotService(session, current_user.tenant_id)
    
    try:
        lot = await service.put_on_hold(lot_id, reason, held_by or current_user.email)
        await session.commit()
        return lot
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to put lot on hold: {str(e)}",
        )


@router.put(
    "/{lot_id}/release",
    response_model=LotResponse,
    summary="Release lot from hold",
)
async def release_lot(
    lot_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Release a lot from hold after review/approval.
    
    Allows the lot to be used in production again.
    """
    service = LotService(session, current_user.tenant_id)
    
    try:
        lot = await service.release_lot(lot_id, current_user.email)
        await session.commit()
        return lot
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to release lot: {str(e)}",
        )


@router.put(
    "/{lot_id}",
    response_model=LotResponse,
    summary="Update lot details",
)
async def update_lot(
    lot_id: uuid.UUID,
    data: LotUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update lot details such as status, test results, quality score, etc.
    """
    service = LotService(session, current_user.tenant_id)
    
    try:
        lot = await service.update_lot(lot_id, data)
        await session.commit()
        return lot
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lot: {str(e)}",
        )


@router.post(
    "/{parent_lot_id}/link/{child_lot_id}",
    response_model=dict,
    summary="Link lots for traceability",
)
async def link_lots(
    parent_lot_id: uuid.UUID,
    child_lot_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create parent-child relationship between lots for traceability.
    
    Example: Link ingredient lot to finished product lot.
    """
    service = LotService(session, current_user.tenant_id)
    
    try:
        parent, child = await service.link_lots(parent_lot_id, child_lot_id)
        await session.commit()
        return {
            "message": "Lots linked successfully",
            "parent_lot_number": parent.lot_number,
            "child_lot_number": child.lot_number,
        }
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link lots: {str(e)}",
        )

