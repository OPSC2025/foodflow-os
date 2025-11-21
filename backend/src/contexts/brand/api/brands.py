"""
Brand API router for brands.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.brand.application.brand_service import BrandService
from src.contexts.brand.domain.schemas import (
    BrandCreate,
    BrandResponse,
    BrandUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/brands", tags=["Brands"])


@router.post(
    "",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a brand",
)
async def create_brand(
    data: BrandCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new brand."""
    service = BrandService(session, current_user.tenant_id)
    
    try:
        brand = await service.create_brand(data)
        await session.commit()
        return brand
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create brand: {str(e)}",
        )


@router.get(
    "",
    response_model=list[BrandResponse],
    summary="List brands",
)
async def list_brands(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List brands with optional filters."""
    service = BrandService(session, current_user.tenant_id)
    
    try:
        brands, total = await service.list_brands(skip, limit, is_active)
        return brands
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list brands: {str(e)}",
        )


@router.get(
    "/{brand_id}",
    response_model=BrandResponse,
    summary="Get brand details",
)
async def get_brand(
    brand_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific brand."""
    service = BrandService(session, current_user.tenant_id)
    
    brand = await service.get_brand(brand_id)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with ID {brand_id} not found",
        )
    
    return brand


@router.put(
    "/{brand_id}",
    response_model=BrandResponse,
    summary="Update brand",
)
async def update_brand(
    brand_id: uuid.UUID,
    data: BrandUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update brand details."""
    service = BrandService(session, current_user.tenant_id)
    
    try:
        brand = await service.update_brand(brand_id, data)
        await session.commit()
        return brand
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update brand: {str(e)}",
        )

