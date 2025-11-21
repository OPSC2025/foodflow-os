"""
Safety Stock service - business logic for safety stock management.
"""

import math
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.domain.models import SafetyStock, SafetyStockPolicy
from src.contexts.planning.domain.schemas import (
    SafetyStockCreate,
    SafetyStockResponse,
    SafetyStockUpdate,
)
from src.contexts.planning.infrastructure.repositories import SafetyStockRepository


class SafetyStockService:
    """Service for safety stock operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = SafetyStockRepository(session, tenant_id)

    async def create_safety_stock(
        self, data: SafetyStockCreate
    ) -> SafetyStockResponse:
        """Create a new safety stock recommendation."""
        safety_stock = SafetyStock(
            product_id=data.product_id,
            sku_id=data.sku_id,
            ingredient_id=data.ingredient_id,
            plant_id=data.plant_id,
            warehouse_location=data.warehouse_location,
            policy=data.policy,
            safety_stock_quantity=data.safety_stock_quantity,
            unit=data.unit,
            target_service_level=data.target_service_level,
            lead_time_days=data.lead_time_days,
            demand_std_dev=data.demand_std_dev,
            demand_mean=data.demand_mean,
            reorder_point=data.reorder_point,
            calculation_details=data.calculation_details,
            calculated_by_ai=data.calculated_by_ai,
            ai_confidence=data.ai_confidence,
            ai_reasoning=data.ai_reasoning,
            is_active=True,
            next_review_date=datetime.utcnow() + timedelta(days=90),  # Review every 3 months
        )

        safety_stock = await self.repo.create(safety_stock)
        return SafetyStockResponse.model_validate(safety_stock)

    async def get_safety_stock(
        self, safety_stock_id: uuid.UUID
    ) -> Optional[SafetyStockResponse]:
        """Get safety stock by ID."""
        safety_stock = await self.repo.get_by_id(safety_stock_id)
        if safety_stock:
            return SafetyStockResponse.model_validate(safety_stock)
        return None

    async def list_safety_stocks(
        self,
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[uuid.UUID] = None,
        sku_id: Optional[uuid.UUID] = None,
        ingredient_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[SafetyStockResponse], int]:
        """List safety stocks with filters."""
        safety_stocks, total = await self.repo.list(
            skip, limit, product_id, sku_id, ingredient_id, is_active
        )
        return (
            [SafetyStockResponse.model_validate(ss) for ss in safety_stocks],
            total,
        )

    async def update_safety_stock(
        self, safety_stock_id: uuid.UUID, data: SafetyStockUpdate
    ) -> SafetyStockResponse:
        """Update a safety stock recommendation."""
        safety_stock = await self.repo.get_by_id(safety_stock_id)
        if not safety_stock:
            raise ValueError(f"Safety stock with ID {safety_stock_id} not found")

        # Update fields
        if data.safety_stock_quantity is not None:
            safety_stock.safety_stock_quantity = data.safety_stock_quantity
        if data.unit is not None:
            safety_stock.unit = data.unit
        if data.target_service_level is not None:
            safety_stock.target_service_level = data.target_service_level
        if data.lead_time_days is not None:
            safety_stock.lead_time_days = data.lead_time_days
        if data.reorder_point is not None:
            safety_stock.reorder_point = data.reorder_point
        if data.is_active is not None:
            safety_stock.is_active = data.is_active
        if data.last_reviewed is not None:
            safety_stock.last_reviewed = data.last_reviewed
        if data.next_review_date is not None:
            safety_stock.next_review_date = data.next_review_date

        safety_stock = await self.repo.update(safety_stock)
        return SafetyStockResponse.model_validate(safety_stock)

    async def calculate_service_level_safety_stock(
        self,
        demand_mean: float,
        demand_std_dev: float,
        lead_time_days: float,
        target_service_level: float,
    ) -> dict:
        """
        Calculate safety stock using service level policy.
        
        Formula: SS = Z × σ_LT
        Where:
        - Z = Z-score for target service level
        - σ_LT = Standard deviation of demand during lead time
        """
        # Z-scores for common service levels
        z_scores = {
            0.50: 0.00,
            0.84: 1.00,
            0.90: 1.28,
            0.95: 1.65,
            0.97: 1.88,
            0.98: 2.05,
            0.99: 2.33,
            0.995: 2.58,
        }

        # Find closest Z-score
        z_score = z_scores.get(target_service_level, 1.65)  # Default to 95%

        # Calculate demand during lead time
        demand_during_lead_time = demand_mean * lead_time_days

        # Calculate std dev during lead time (assuming independent demand)
        std_dev_during_lead_time = demand_std_dev * math.sqrt(lead_time_days)

        # Calculate safety stock
        safety_stock_quantity = z_score * std_dev_during_lead_time

        # Calculate reorder point
        reorder_point = demand_during_lead_time + safety_stock_quantity

        return {
            "safety_stock_quantity": round(safety_stock_quantity, 2),
            "reorder_point": round(reorder_point, 2),
            "calculation_details": {
                "z_score": z_score,
                "demand_during_lead_time": round(demand_during_lead_time, 2),
                "std_dev_during_lead_time": round(std_dev_during_lead_time, 2),
                "target_service_level": target_service_level,
                "lead_time_days": lead_time_days,
            },
        }

    async def get_by_product(
        self, product_id: uuid.UUID, plant_id: Optional[uuid.UUID] = None
    ) -> Optional[SafetyStockResponse]:
        """Get active safety stock for a product."""
        safety_stock = await self.repo.get_by_product(product_id, plant_id)
        if safety_stock:
            return SafetyStockResponse.model_validate(safety_stock)
        return None

