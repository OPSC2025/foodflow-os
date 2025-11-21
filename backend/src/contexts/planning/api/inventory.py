"""
Planning API router for inventory levels.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.application.inventory_service import InventoryLevelService
from src.contexts.planning.domain.schemas import (
    InventoryLevelCreate,
    InventoryLevelResponse,
    InventoryLevelUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.post(
    "",
    response_model=InventoryLevelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create inventory level record",
)
async def create_inventory_level(
    data: InventoryLevelCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new inventory level snapshot.
    """
    service = InventoryLevelService(session, current_user.tenant_id)
    
    try:
        inventory_level = await service.create_inventory_level(data)
        await session.commit()
        return inventory_level
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create inventory level: {str(e)}",
        )


@router.get(
    "",
    response_model=list[InventoryLevelResponse],
    summary="List inventory levels",
)
async def list_inventory_levels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    product_id: Optional[uuid.UUID] = Query(None, description="Filter by product ID"),
    sku_id: Optional[uuid.UUID] = Query(None, description="Filter by SKU ID"),
    ingredient_id: Optional[uuid.UUID] = Query(None, description="Filter by ingredient ID"),
    plant_id: Optional[uuid.UUID] = Query(None, description="Filter by plant ID"),
    is_below_safety_stock: Optional[bool] = Query(None, description="Filter by low stock status"),
    is_stockout: Optional[bool] = Query(None, description="Filter by stockout status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List inventory levels with optional filters.
    """
    service = InventoryLevelService(session, current_user.tenant_id)
    
    try:
        inventory_levels, total = await service.list_inventory_levels(
            skip, limit, product_id, sku_id, ingredient_id, plant_id, is_below_safety_stock, is_stockout
        )
        return inventory_levels
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list inventory levels: {str(e)}",
        )


@router.get(
    "/{inventory_level_id}",
    response_model=InventoryLevelResponse,
    summary="Get inventory level details",
)
async def get_inventory_level(
    inventory_level_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information about a specific inventory level record.
    """
    service = InventoryLevelService(session, current_user.tenant_id)
    
    inventory_level = await service.get_inventory_level(inventory_level_id)
    if not inventory_level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory level with ID {inventory_level_id} not found",
        )
    
    return inventory_level


@router.put(
    "/{inventory_level_id}",
    response_model=InventoryLevelResponse,
    summary="Update inventory level",
)
async def update_inventory_level(
    inventory_level_id: uuid.UUID,
    data: InventoryLevelUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update an inventory level record.
    """
    service = InventoryLevelService(session, current_user.tenant_id)
    
    try:
        inventory_level = await service.update_inventory_level(inventory_level_id, data)
        await session.commit()
        return inventory_level
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update inventory level: {str(e)}",
        )


@router.post(
    "/{inventory_level_id}/movement",
    response_model=InventoryLevelResponse,
    summary="Record inventory movement",
)
async def record_inventory_movement(
    inventory_level_id: uuid.UUID,
    movement_type: str = Query(..., description="Movement type: receipt, consumption, adjustment, transfer"),
    quantity: float = Query(..., description="Movement quantity (negative for reductions)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Record an inventory movement.
    
    Movement types:
    - receipt: Incoming inventory
    - consumption: Outgoing inventory (production usage)
    - adjustment: Inventory adjustment (cycle count)
    - transfer: Transfer between locations
    """
    service = InventoryLevelService(session, current_user.tenant_id)
    
    try:
        inventory_level = await service.record_movement(
            inventory_level_id, movement_type, quantity
        )
        await session.commit()
        return inventory_level
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record movement: {str(e)}",
        )

