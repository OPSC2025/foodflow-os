"""
Retail API router for promotions.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.application.promo_service import PromoService
from src.contexts.retail.domain.schemas import (
    PromoCreate,
    PromoResponse,
    PromoUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/promos", tags=["Retail - Promos"])


@router.post(
    "",
    response_model=PromoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a promo",
)
async def create_promo(
    data: PromoCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new promotion."""
    service = PromoService(session, current_user.tenant_id)
    
    try:
        promo = await service.create_promo(data)
        await session.commit()
        return promo
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create promo: {str(e)}",
        )


@router.get(
    "",
    response_model=list[PromoResponse],
    summary="List promos",
)
async def list_promos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
    active_only: bool = Query(False, description="Show only currently active promos"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List promos with optional filters."""
    service = PromoService(session, current_user.tenant_id)
    
    try:
        promos, total = await service.list_promos(skip, limit, status, active_only)
        return promos
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list promos: {str(e)}",
        )


@router.get(
    "/{promo_id}",
    response_model=PromoResponse,
    summary="Get promo details",
)
async def get_promo(
    promo_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific promo."""
    service = PromoService(session, current_user.tenant_id)
    
    promo = await service.get_promo(promo_id)
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Promo with ID {promo_id} not found",
        )
    
    return promo


@router.put(
    "/{promo_id}",
    response_model=PromoResponse,
    summary="Update promo",
)
async def update_promo(
    promo_id: uuid.UUID,
    data: PromoUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update promo details."""
    service = PromoService(session, current_user.tenant_id)
    
    try:
        promo = await service.update_promo(promo_id, data)
        await session.commit()
        return promo
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update promo: {str(e)}",
        )


@router.put(
    "/{promo_id}/activate",
    response_model=PromoResponse,
    summary="Activate promo",
)
async def activate_promo(
    promo_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Activate a promotion."""
    service = PromoService(session, current_user.tenant_id)
    
    try:
        promo = await service.activate_promo(promo_id)
        await session.commit()
        return promo
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate promo: {str(e)}",
        )


@router.post(
    "/{promo_id}/calculate-roi",
    response_model=PromoResponse,
    summary="Calculate promo ROI",
)
async def calculate_promo_roi(
    promo_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Calculate and update promo ROI."""
    service = PromoService(session, current_user.tenant_id)
    
    try:
        promo = await service.calculate_promo_roi(promo_id)
        await session.commit()
        return promo
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate promo ROI: {str(e)}",
        )

