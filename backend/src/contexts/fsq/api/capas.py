"""
FSQ API router for CAPAs (Corrective and Preventive Actions).
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.fsq.application.capa_service import CAPAService
from src.contexts.fsq.domain.schemas import (
    CAPACreate,
    CAPAResponse,
    CAPAUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/capas", tags=["CAPAs"])


@router.post(
    "",
    response_model=CAPAResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a CAPA",
)
async def create_capa(
    data: CAPACreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a Corrective and Preventive Action (CAPA).
    
    Used to address root causes and prevent recurrence of problems.
    """
    service = CAPAService(session, current_user.tenant_id)
    
    try:
        capa = await service.create_capa(data)
        await session.commit()
        return capa
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create CAPA: {str(e)}",
        )


@router.get(
    "",
    response_model=list[CAPAResponse],
    summary="List CAPAs",
)
async def list_capas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
    owner: Optional[str] = Query(None, description="Filter by owner"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List CAPAs with optional filters.
    """
    service = CAPAService(session, current_user.tenant_id)
    
    try:
        capas, total = await service.list_capas(skip, limit, status, owner)
        return capas
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list CAPAs: {str(e)}",
        )


@router.get(
    "/{capa_id}",
    response_model=CAPAResponse,
    summary="Get CAPA details",
)
async def get_capa(
    capa_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information about a specific CAPA.
    """
    service = CAPAService(session, current_user.tenant_id)
    
    capa = await service.get_capa(capa_id)
    if not capa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CAPA with ID {capa_id} not found",
        )
    
    return capa


@router.put(
    "/{capa_id}",
    response_model=CAPAResponse,
    summary="Update CAPA",
)
async def update_capa(
    capa_id: uuid.UUID,
    data: CAPAUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update CAPA details including actions, status, etc.
    """
    service = CAPAService(session, current_user.tenant_id)
    
    try:
        capa = await service.update_capa(capa_id, data)
        await session.commit()
        return capa
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update CAPA: {str(e)}",
        )


@router.put(
    "/{capa_id}/complete",
    response_model=CAPAResponse,
    summary="Complete CAPA",
)
async def complete_capa(
    capa_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Mark CAPA as completed and ready for verification.
    """
    service = CAPAService(session, current_user.tenant_id)
    
    try:
        capa = await service.complete_capa(capa_id)
        await session.commit()
        return capa
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete CAPA: {str(e)}",
        )


@router.put(
    "/{capa_id}/verify",
    response_model=CAPAResponse,
    summary="Verify CAPA effectiveness",
)
async def verify_capa(
    capa_id: uuid.UUID,
    is_effective: bool = Query(..., description="Is the CAPA effective?"),
    notes: Optional[str] = Query(None, description="Verification notes"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Verify CAPA effectiveness after completion.
    """
    service = CAPAService(session, current_user.tenant_id)
    
    try:
        capa = await service.verify_capa(capa_id, current_user.email, is_effective, notes)
        await session.commit()
        return capa
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify CAPA: {str(e)}",
        )


@router.put(
    "/{capa_id}/close",
    response_model=CAPAResponse,
    summary="Close CAPA",
)
async def close_capa(
    capa_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Close a verified CAPA.
    
    CAPA must be verified as effective before closing.
    """
    service = CAPAService(session, current_user.tenant_id)
    
    try:
        capa = await service.close_capa(capa_id)
        await session.commit()
        return capa
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close CAPA: {str(e)}",
        )

