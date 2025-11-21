"""
Brand API router for SKUs (standalone).
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.brand.application.product_service import SKUService
from src.contexts.brand.domain.schemas import (
    SKUResponse,
    SKUUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/skus", tags=["SKUs"])


@router.get(
    "",
    response_model=list[SKUResponse],
    summary="List all SKUs",
)
async def list_skus(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    product_id: Optional[uuid.UUID] = Query(None, description="Filter by product ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List all SKUs with optional filters."""
    service = SKUService(session, current_user.tenant_id)
    
    try:
        skus, total = await service.list_skus(skip, limit, product_id, is_active)
        return skus
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list SKUs: {str(e)}",
        )


@router.get(
    "/{sku_id}",
    response_model=SKUResponse,
    summary="Get SKU details",
)
async def get_sku(
    sku_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific SKU."""
    service = SKUService(session, current_user.tenant_id)
    
    sku = await service.get_sku(sku_id)
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU with ID {sku_id} not found",
        )
    
    return sku


@router.put(
    "/{sku_id}",
    response_model=SKUResponse,
    summary="Update SKU",
)
async def update_sku(
    sku_id: uuid.UUID,
    data: SKUUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update SKU details."""
    service = SKUService(session, current_user.tenant_id)
    
    try:
        sku = await service.update_sku(sku_id, data)
        await session.commit()
        return sku
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update SKU: {str(e)}",
        )

