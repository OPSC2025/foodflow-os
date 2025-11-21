"""
Planning & Supply repositories.

Data access layer for Planning context models.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.domain.models import (
    Forecast,
    InventoryLevel,
    ProductionPlan,
    SafetyStock,
)


class ForecastRepository:
    """Repository for Forecast operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, forecast: Forecast) -> Forecast:
        """Create a new forecast."""
        forecast.tenant_id = self.tenant_id
        self.session.add(forecast)
        await self.session.flush()
        return forecast

    async def get_by_id(self, forecast_id: uuid.UUID) -> Optional[Forecast]:
        """Get forecast by ID."""
        result = await self.session.execute(
            select(Forecast).where(
                and_(Forecast.id == forecast_id, Forecast.tenant_id == self.tenant_id)
            )
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[uuid.UUID] = None,
        sku_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Forecast], int]:
        """List forecasts with filters."""
        conditions = [Forecast.tenant_id == self.tenant_id]

        if product_id:
            conditions.append(Forecast.product_id == product_id)
        if sku_id:
            conditions.append(Forecast.sku_id == sku_id)
        if status:
            conditions.append(Forecast.status == status)

        # Get total count
        count_result = await self.session.execute(
            select(Forecast).where(and_(*conditions))
        )
        total = len(count_result.scalars().all())

        # Get paginated results
        result = await self.session.execute(
            select(Forecast)
            .where(and_(*conditions))
            .order_by(desc(Forecast.created_at))
            .offset(skip)
            .limit(limit)
        )
        forecasts = result.scalars().all()

        return list(forecasts), total

    async def update(self, forecast: Forecast) -> Forecast:
        """Update a forecast."""
        await self.session.flush()
        return forecast

    async def get_latest_by_product(self, product_id: uuid.UUID) -> Optional[Forecast]:
        """Get the latest active forecast for a product."""
        result = await self.session.execute(
            select(Forecast)
            .where(
                and_(
                    Forecast.tenant_id == self.tenant_id,
                    Forecast.product_id == product_id,
                    Forecast.status == "active",
                )
            )
            .order_by(desc(Forecast.created_at))
            .limit(1)
        )
        return result.scalars().first()


class ProductionPlanRepository:
    """Repository for ProductionPlan operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, plan: ProductionPlan) -> ProductionPlan:
        """Create a new production plan."""
        plan.tenant_id = self.tenant_id
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def get_by_id(self, plan_id: uuid.UUID) -> Optional[ProductionPlan]:
        """Get production plan by ID."""
        result = await self.session.execute(
            select(ProductionPlan).where(
                and_(ProductionPlan.id == plan_id, ProductionPlan.tenant_id == self.tenant_id)
            )
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        forecast_id: Optional[uuid.UUID] = None,
    ) -> tuple[list[ProductionPlan], int]:
        """List production plans with filters."""
        conditions = [ProductionPlan.tenant_id == self.tenant_id]

        if status:
            conditions.append(ProductionPlan.status == status)
        if forecast_id:
            conditions.append(ProductionPlan.forecast_id == forecast_id)

        # Get total count
        count_result = await self.session.execute(
            select(ProductionPlan).where(and_(*conditions))
        )
        total = len(count_result.scalars().all())

        # Get paginated results
        result = await self.session.execute(
            select(ProductionPlan)
            .where(and_(*conditions))
            .order_by(desc(ProductionPlan.created_at))
            .offset(skip)
            .limit(limit)
        )
        plans = result.scalars().all()

        return list(plans), total

    async def update(self, plan: ProductionPlan) -> ProductionPlan:
        """Update a production plan."""
        await self.session.flush()
        return plan

    async def list_pending_approval(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[ProductionPlan], int]:
        """List plans pending approval."""
        return await self.list(skip, limit, status="pending_approval")


class SafetyStockRepository:
    """Repository for SafetyStock operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, safety_stock: SafetyStock) -> SafetyStock:
        """Create a new safety stock recommendation."""
        safety_stock.tenant_id = self.tenant_id
        self.session.add(safety_stock)
        await self.session.flush()
        return safety_stock

    async def get_by_id(self, safety_stock_id: uuid.UUID) -> Optional[SafetyStock]:
        """Get safety stock by ID."""
        result = await self.session.execute(
            select(SafetyStock).where(
                and_(SafetyStock.id == safety_stock_id, SafetyStock.tenant_id == self.tenant_id)
            )
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[uuid.UUID] = None,
        sku_id: Optional[uuid.UUID] = None,
        ingredient_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[SafetyStock], int]:
        """List safety stocks with filters."""
        conditions = [SafetyStock.tenant_id == self.tenant_id]

        if product_id:
            conditions.append(SafetyStock.product_id == product_id)
        if sku_id:
            conditions.append(SafetyStock.sku_id == sku_id)
        if ingredient_id:
            conditions.append(SafetyStock.ingredient_id == ingredient_id)
        if is_active is not None:
            conditions.append(SafetyStock.is_active == is_active)

        # Get total count
        count_result = await self.session.execute(
            select(SafetyStock).where(and_(*conditions))
        )
        total = len(count_result.scalars().all())

        # Get paginated results
        result = await self.session.execute(
            select(SafetyStock)
            .where(and_(*conditions))
            .order_by(desc(SafetyStock.created_at))
            .offset(skip)
            .limit(limit)
        )
        safety_stocks = result.scalars().all()

        return list(safety_stocks), total

    async def update(self, safety_stock: SafetyStock) -> SafetyStock:
        """Update a safety stock recommendation."""
        await self.session.flush()
        return safety_stock

    async def get_by_product(
        self, product_id: uuid.UUID, plant_id: Optional[uuid.UUID] = None
    ) -> Optional[SafetyStock]:
        """Get active safety stock for a product."""
        conditions = [
            SafetyStock.tenant_id == self.tenant_id,
            SafetyStock.product_id == product_id,
            SafetyStock.is_active == True,
        ]

        if plant_id:
            conditions.append(SafetyStock.plant_id == plant_id)

        result = await self.session.execute(
            select(SafetyStock).where(and_(*conditions)).order_by(desc(SafetyStock.created_at)).limit(1)
        )
        return result.scalars().first()


class InventoryLevelRepository:
    """Repository for InventoryLevel operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, inventory_level: InventoryLevel) -> InventoryLevel:
        """Create a new inventory level record."""
        inventory_level.tenant_id = self.tenant_id
        self.session.add(inventory_level)
        await self.session.flush()
        return inventory_level

    async def get_by_id(self, inventory_level_id: uuid.UUID) -> Optional[InventoryLevel]:
        """Get inventory level by ID."""
        result = await self.session.execute(
            select(InventoryLevel).where(
                and_(
                    InventoryLevel.id == inventory_level_id,
                    InventoryLevel.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[uuid.UUID] = None,
        sku_id: Optional[uuid.UUID] = None,
        ingredient_id: Optional[uuid.UUID] = None,
        plant_id: Optional[uuid.UUID] = None,
        is_below_safety_stock: Optional[bool] = None,
        is_stockout: Optional[bool] = None,
    ) -> tuple[list[InventoryLevel], int]:
        """List inventory levels with filters."""
        conditions = [InventoryLevel.tenant_id == self.tenant_id]

        if product_id:
            conditions.append(InventoryLevel.product_id == product_id)
        if sku_id:
            conditions.append(InventoryLevel.sku_id == sku_id)
        if ingredient_id:
            conditions.append(InventoryLevel.ingredient_id == ingredient_id)
        if plant_id:
            conditions.append(InventoryLevel.plant_id == plant_id)
        if is_below_safety_stock is not None:
            conditions.append(InventoryLevel.is_below_safety_stock == is_below_safety_stock)
        if is_stockout is not None:
            conditions.append(InventoryLevel.is_stockout == is_stockout)

        # Get total count
        count_result = await self.session.execute(
            select(InventoryLevel).where(and_(*conditions))
        )
        total = len(count_result.scalars().all())

        # Get paginated results
        result = await self.session.execute(
            select(InventoryLevel)
            .where(and_(*conditions))
            .order_by(desc(InventoryLevel.as_of_date))
            .offset(skip)
            .limit(limit)
        )
        inventory_levels = result.scalars().all()

        return list(inventory_levels), total

    async def update(self, inventory_level: InventoryLevel) -> InventoryLevel:
        """Update an inventory level record."""
        await self.session.flush()
        return inventory_level

    async def get_latest_by_product(
        self, product_id: uuid.UUID, plant_id: Optional[uuid.UUID] = None
    ) -> Optional[InventoryLevel]:
        """Get the latest inventory level for a product."""
        conditions = [
            InventoryLevel.tenant_id == self.tenant_id,
            InventoryLevel.product_id == product_id,
        ]

        if plant_id:
            conditions.append(InventoryLevel.plant_id == plant_id)

        result = await self.session.execute(
            select(InventoryLevel)
            .where(and_(*conditions))
            .order_by(desc(InventoryLevel.as_of_date))
            .limit(1)
        )
        return result.scalars().first()

