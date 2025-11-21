"""
Waste service - business logic for waste tracking.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.domain.models import Waste
from src.contexts.retail.domain.schemas import (
    WasteCreate,
    WasteResponse,
    WasteUpdate,
)
from src.contexts.retail.infrastructure.repositories import WasteRepository


class WasteService:
    """Service for waste tracking operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = WasteRepository(session, tenant_id)

    async def create_waste(self, data: WasteCreate) -> WasteResponse:
        """Create a waste record."""
        waste = Waste(
            store_id=data.store_id,
            recorded_date=data.recorded_date,
            sku_id=data.sku_id,
            product_id=data.product_id,
            product_name=data.product_name,
            quantity_wasted=data.quantity_wasted,
            unit=data.unit,
            estimated_value=data.estimated_value,
            reason=data.reason,
            category=data.category,
            notes=data.notes,
            recorded_by=data.recorded_by,
        )

        waste = await self.repo.create(waste)
        return WasteResponse.model_validate(waste)

    async def get_waste(self, waste_id: uuid.UUID) -> Optional[WasteResponse]:
        """Get waste record by ID."""
        waste = await self.repo.get_by_id(waste_id)
        if waste:
            return WasteResponse.model_validate(waste)
        return None

    async def list_waste(
        self,
        skip: int = 0,
        limit: int = 100,
        store_id: Optional[uuid.UUID] = None,
        reason: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[list[WasteResponse], int]:
        """List waste records with filters."""
        waste_records, total = await self.repo.list(
            skip, limit, store_id, reason, start_date, end_date
        )
        return (
            [WasteResponse.model_validate(w) for w in waste_records],
            total,
        )

    async def update_waste(self, waste_id: uuid.UUID, data: WasteUpdate) -> WasteResponse:
        """Update a waste record."""
        waste = await self.repo.get_by_id(waste_id)
        if not waste:
            raise ValueError(f"Waste record with ID {waste_id} not found")

        if data.quantity_wasted is not None:
            waste.quantity_wasted = data.quantity_wasted
        if data.estimated_value is not None:
            waste.estimated_value = data.estimated_value
        if data.reason is not None:
            waste.reason = data.reason
        if data.notes is not None:
            waste.notes = data.notes

        waste = await self.repo.update(waste)
        return WasteResponse.model_validate(waste)

