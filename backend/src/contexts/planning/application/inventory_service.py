"""
Inventory Level service - business logic for inventory tracking.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.domain.models import InventoryLevel
from src.contexts.planning.domain.schemas import (
    InventoryLevelCreate,
    InventoryLevelResponse,
    InventoryLevelUpdate,
)
from src.contexts.planning.infrastructure.repositories import InventoryLevelRepository


class InventoryLevelService:
    """Service for inventory level operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = InventoryLevelRepository(session, tenant_id)

    async def create_inventory_level(
        self, data: InventoryLevelCreate
    ) -> InventoryLevelResponse:
        """Create a new inventory level record."""
        inventory_level = InventoryLevel(
            product_id=data.product_id,
            sku_id=data.sku_id,
            ingredient_id=data.ingredient_id,
            plant_id=data.plant_id,
            warehouse_location=data.warehouse_location,
            on_hand_quantity=data.on_hand_quantity,
            available_quantity=data.available_quantity,
            allocated_quantity=data.allocated_quantity,
            in_transit_quantity=data.in_transit_quantity,
            unit=data.unit,
            is_below_safety_stock=data.is_below_safety_stock,
            is_stockout=data.is_stockout,
            days_of_supply=data.days_of_supply,
            last_movement_type=data.last_movement_type,
            last_movement_date=data.last_movement_date,
            last_movement_quantity=data.last_movement_quantity,
            as_of_date=data.as_of_date,
        )

        inventory_level = await self.repo.create(inventory_level)
        return InventoryLevelResponse.model_validate(inventory_level)

    async def get_inventory_level(
        self, inventory_level_id: uuid.UUID
    ) -> Optional[InventoryLevelResponse]:
        """Get inventory level by ID."""
        inventory_level = await self.repo.get_by_id(inventory_level_id)
        if inventory_level:
            return InventoryLevelResponse.model_validate(inventory_level)
        return None

    async def list_inventory_levels(
        self,
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[uuid.UUID] = None,
        sku_id: Optional[uuid.UUID] = None,
        ingredient_id: Optional[uuid.UUID] = None,
        plant_id: Optional[uuid.UUID] = None,
        is_below_safety_stock: Optional[bool] = None,
        is_stockout: Optional[bool] = None,
    ) -> tuple[list[InventoryLevelResponse], int]:
        """List inventory levels with filters."""
        inventory_levels, total = await self.repo.list(
            skip,
            limit,
            product_id,
            sku_id,
            ingredient_id,
            plant_id,
            is_below_safety_stock,
            is_stockout,
        )
        return (
            [InventoryLevelResponse.model_validate(il) for il in inventory_levels],
            total,
        )

    async def update_inventory_level(
        self, inventory_level_id: uuid.UUID, data: InventoryLevelUpdate
    ) -> InventoryLevelResponse:
        """Update an inventory level record."""
        inventory_level = await self.repo.get_by_id(inventory_level_id)
        if not inventory_level:
            raise ValueError(f"Inventory level with ID {inventory_level_id} not found")

        # Update fields
        if data.on_hand_quantity is not None:
            inventory_level.on_hand_quantity = data.on_hand_quantity
        if data.available_quantity is not None:
            inventory_level.available_quantity = data.available_quantity
        if data.allocated_quantity is not None:
            inventory_level.allocated_quantity = data.allocated_quantity
        if data.in_transit_quantity is not None:
            inventory_level.in_transit_quantity = data.in_transit_quantity
        if data.is_below_safety_stock is not None:
            inventory_level.is_below_safety_stock = data.is_below_safety_stock
        if data.is_stockout is not None:
            inventory_level.is_stockout = data.is_stockout
        if data.days_of_supply is not None:
            inventory_level.days_of_supply = data.days_of_supply
        if data.last_movement_type is not None:
            inventory_level.last_movement_type = data.last_movement_type
        if data.last_movement_date is not None:
            inventory_level.last_movement_date = data.last_movement_date
        if data.last_movement_quantity is not None:
            inventory_level.last_movement_quantity = data.last_movement_quantity

        inventory_level = await self.repo.update(inventory_level)
        return InventoryLevelResponse.model_validate(inventory_level)

    async def record_movement(
        self,
        inventory_level_id: uuid.UUID,
        movement_type: str,
        quantity: float,
    ) -> InventoryLevelResponse:
        """
        Record an inventory movement.
        
        Movement types: receipt, consumption, adjustment, transfer
        """
        inventory_level = await self.repo.get_by_id(inventory_level_id)
        if not inventory_level:
            raise ValueError(f"Inventory level with ID {inventory_level_id} not found")

        # Update quantities based on movement type
        if movement_type == "receipt":
            inventory_level.on_hand_quantity += quantity
            inventory_level.available_quantity += quantity
        elif movement_type == "consumption":
            inventory_level.on_hand_quantity -= quantity
            inventory_level.available_quantity -= quantity
        elif movement_type == "adjustment":
            inventory_level.on_hand_quantity += quantity
            inventory_level.available_quantity += quantity
        elif movement_type == "transfer":
            # Transfer out (negative quantity means transfer out)
            inventory_level.on_hand_quantity += quantity
            inventory_level.available_quantity += quantity

        # Update movement metadata
        inventory_level.last_movement_type = movement_type
        inventory_level.last_movement_date = datetime.utcnow()
        inventory_level.last_movement_quantity = quantity

        # Check for stockout
        if inventory_level.on_hand_quantity <= 0:
            inventory_level.is_stockout = True

        inventory_level = await self.repo.update(inventory_level)
        return InventoryLevelResponse.model_validate(inventory_level)

    async def get_latest_by_product(
        self, product_id: uuid.UUID, plant_id: Optional[uuid.UUID] = None
    ) -> Optional[InventoryLevelResponse]:
        """Get the latest inventory level for a product."""
        inventory_level = await self.repo.get_latest_by_product(product_id, plant_id)
        if inventory_level:
            return InventoryLevelResponse.model_validate(inventory_level)
        return None

