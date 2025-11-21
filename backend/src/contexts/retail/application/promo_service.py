"""
Promo service - business logic for promotions.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.domain.models import Promo, PromoStatus
from src.contexts.retail.domain.schemas import (
    PromoCreate,
    PromoResponse,
    PromoUpdate,
)
from src.contexts.retail.infrastructure.repositories import PromoRepository


class PromoService:
    """Service for promo operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = PromoRepository(session, tenant_id)

    async def create_promo(self, data: PromoCreate) -> PromoResponse:
        """Create a new promo."""
        promo = Promo(
            promo_name=data.promo_name,
            promo_code=data.promo_code,
            description=data.description,
            promo_type=data.promo_type,
            start_date=data.start_date,
            end_date=data.end_date,
            banner_ids=data.banner_ids,
            store_ids=data.store_ids,
            product_ids=data.product_ids,
            sku_ids=data.sku_ids,
            discount_percentage=data.discount_percentage,
            discount_amount=data.discount_amount,
            promo_mechanics=data.promo_mechanics,
            budget=data.budget,
            target_units=data.target_units,
            target_revenue=data.target_revenue,
            suggested_by_ai=data.suggested_by_ai,
            ai_confidence=data.ai_confidence,
            status=PromoStatus.PLANNED,
        )

        promo = await self.repo.create(promo)
        return PromoResponse.model_validate(promo)

    async def get_promo(self, promo_id: uuid.UUID) -> Optional[PromoResponse]:
        """Get promo by ID."""
        promo = await self.repo.get_by_id(promo_id)
        if promo:
            return PromoResponse.model_validate(promo)
        return None

    async def list_promos(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        active_only: bool = False,
    ) -> tuple[list[PromoResponse], int]:
        """List promos with filters."""
        promos, total = await self.repo.list(skip, limit, status, active_only)
        return (
            [PromoResponse.model_validate(p) for p in promos],
            total,
        )

    async def update_promo(self, promo_id: uuid.UUID, data: PromoUpdate) -> PromoResponse:
        """Update a promo."""
        promo = await self.repo.get_by_id(promo_id)
        if not promo:
            raise ValueError(f"Promo with ID {promo_id} not found")

        # Update fields
        if data.promo_name is not None:
            promo.promo_name = data.promo_name
        if data.description is not None:
            promo.description = data.description
        if data.end_date is not None:
            promo.end_date = data.end_date
        if data.discount_percentage is not None:
            promo.discount_percentage = data.discount_percentage
        if data.discount_amount is not None:
            promo.discount_amount = data.discount_amount
        if data.budget is not None:
            promo.budget = data.budget
        if data.target_units is not None:
            promo.target_units = data.target_units
        if data.target_revenue is not None:
            promo.target_revenue = data.target_revenue
        if data.actual_units_sold is not None:
            promo.actual_units_sold = data.actual_units_sold
        if data.actual_revenue is not None:
            promo.actual_revenue = data.actual_revenue
        if data.actual_discount_given is not None:
            promo.actual_discount_given = data.actual_discount_given
        if data.roi is not None:
            promo.roi = data.roi
        if data.status is not None:
            promo.status = data.status

        promo = await self.repo.update(promo)
        return PromoResponse.model_validate(promo)

    async def activate_promo(self, promo_id: uuid.UUID) -> PromoResponse:
        """Activate a promo."""
        promo = await self.repo.get_by_id(promo_id)
        if not promo:
            raise ValueError(f"Promo with ID {promo_id} not found")

        if promo.status != PromoStatus.PLANNED:
            raise ValueError("Only planned promos can be activated")

        # Check if start date has passed
        now = datetime.utcnow()
        if promo.start_date > now:
            raise ValueError("Cannot activate promo before start date")

        promo.status = PromoStatus.ACTIVE
        promo = await self.repo.update(promo)
        return PromoResponse.model_validate(promo)

    async def calculate_promo_roi(self, promo_id: uuid.UUID) -> PromoResponse:
        """
        Calculate promo ROI.
        
        ROI = (Actual Revenue - Actual Discount Given) / Budget
        """
        promo = await self.repo.get_by_id(promo_id)
        if not promo:
            raise ValueError(f"Promo with ID {promo_id} not found")

        if promo.actual_revenue and promo.actual_discount_given and promo.budget:
            net_gain = promo.actual_revenue - promo.actual_discount_given
            promo.roi = (net_gain / promo.budget) * 100 if promo.budget > 0 else 0.0

        promo = await self.repo.update(promo)
        return PromoResponse.model_validate(promo)

