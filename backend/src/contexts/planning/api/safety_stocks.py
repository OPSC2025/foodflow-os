"""
Planning API router for safety stocks.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.application.safety_stock_service import SafetyStockService
from src.contexts.planning.domain.schemas import (
    SafetyStockCreate,
    SafetyStockResponse,
    SafetyStockUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/safety-stocks", tags=["Safety Stocks"])


@router.post(
    "",
    response_model=SafetyStockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create safety stock recommendation",
)
async def create_safety_stock(
    data: SafetyStockCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new safety stock recommendation.
    
    Can be AI-calculated or manually set.
    """
    service = SafetyStockService(session, current_user.tenant_id)
    
    try:
        safety_stock = await service.create_safety_stock(data)
        await session.commit()
        return safety_stock
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create safety stock: {str(e)}",
        )


@router.get(
    "",
    response_model=list[SafetyStockResponse],
    summary="List safety stocks",
)
async def list_safety_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    product_id: Optional[uuid.UUID] = Query(None, description="Filter by product ID"),
    sku_id: Optional[uuid.UUID] = Query(None, description="Filter by SKU ID"),
    ingredient_id: Optional[uuid.UUID] = Query(None, description="Filter by ingredient ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List safety stock recommendations with optional filters.
    """
    service = SafetyStockService(session, current_user.tenant_id)
    
    try:
        safety_stocks, total = await service.list_safety_stocks(
            skip, limit, product_id, sku_id, ingredient_id, is_active
        )
        return safety_stocks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list safety stocks: {str(e)}",
        )


@router.get(
    "/{safety_stock_id}",
    response_model=SafetyStockResponse,
    summary="Get safety stock details",
)
async def get_safety_stock(
    safety_stock_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information about a specific safety stock recommendation.
    """
    service = SafetyStockService(session, current_user.tenant_id)
    
    safety_stock = await service.get_safety_stock(safety_stock_id)
    if not safety_stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safety stock with ID {safety_stock_id} not found",
        )
    
    return safety_stock


@router.put(
    "/{safety_stock_id}",
    response_model=SafetyStockResponse,
    summary="Update safety stock",
)
async def update_safety_stock(
    safety_stock_id: uuid.UUID,
    data: SafetyStockUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update a safety stock recommendation.
    """
    service = SafetyStockService(session, current_user.tenant_id)
    
    try:
        safety_stock = await service.update_safety_stock(safety_stock_id, data)
        await session.commit()
        return safety_stock
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update safety stock: {str(e)}",
        )


@router.post(
    "/calculate",
    response_model=dict,
    summary="Calculate safety stock",
)
async def calculate_safety_stock(
    demand_mean: float = Query(..., gt=0, description="Mean daily demand"),
    demand_std_dev: float = Query(..., gt=0, description="Standard deviation of daily demand"),
    lead_time_days: float = Query(..., gt=0, description="Lead time in days"),
    target_service_level: float = Query(0.95, ge=0, le=1, description="Target service level (0-1)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Calculate safety stock using service level policy.
    
    Returns calculated safety stock quantity and reorder point.
    """
    service = SafetyStockService(session, current_user.tenant_id)
    
    try:
        result = await service.calculate_service_level_safety_stock(
            demand_mean, demand_std_dev, lead_time_days, target_service_level
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate safety stock: {str(e)}",
        )

