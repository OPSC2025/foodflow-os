"""
OSA service - business logic for on-shelf availability.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.domain.models import OSAEvent
from src.contexts.retail.domain.schemas import (
    OSAEventCreate,
    OSAEventResponse,
    OSAEventUpdate,
)
from src.contexts.retail.infrastructure.repositories import OSAEventRepository


class OSAService:
    """Service for OSA (On-Shelf Availability) operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = OSAEventRepository(session, tenant_id)

    async def create_osa_event(self, data: OSAEventCreate) -> OSAEventResponse:
        """Create an OSA event."""
        osa_event = OSAEvent(
            store_id=data.store_id,
            detected_date=data.detected_date,
            sku_id=data.sku_id,
            product_id=data.product_id,
            product_name=data.product_name,
            osa_status=data.osa_status,
            issue_type=data.issue_type,
            on_hand_quantity=data.on_hand_quantity,
            backroom_quantity=data.backroom_quantity,
            shelf_capacity=data.shelf_capacity,
            estimated_lost_sales=data.estimated_lost_sales,
            duration_hours=data.duration_hours,
            detected_by=data.detected_by,
            notes=data.notes,
            resolved=False,
        )

        osa_event = await self.repo.create(osa_event)
        return OSAEventResponse.model_validate(osa_event)

    async def get_osa_event(self, osa_event_id: uuid.UUID) -> Optional[OSAEventResponse]:
        """Get OSA event by ID."""
        osa_event = await self.repo.get_by_id(osa_event_id)
        if osa_event:
            return OSAEventResponse.model_validate(osa_event)
        return None

    async def list_osa_events(
        self,
        skip: int = 0,
        limit: int = 100,
        store_id: Optional[uuid.UUID] = None,
        resolved: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[list[OSAEventResponse], int]:
        """List OSA events with filters."""
        osa_events, total = await self.repo.list(
            skip, limit, store_id, resolved, start_date, end_date
        )
        return (
            [OSAEventResponse.model_validate(e) for e in osa_events],
            total,
        )

    async def update_osa_event(
        self, osa_event_id: uuid.UUID, data: OSAEventUpdate
    ) -> OSAEventResponse:
        """Update an OSA event."""
        osa_event = await self.repo.get_by_id(osa_event_id)
        if not osa_event:
            raise ValueError(f"OSA event with ID {osa_event_id} not found")

        if data.resolved is not None:
            osa_event.resolved = data.resolved
        if data.resolved_date is not None:
            osa_event.resolved_date = data.resolved_date
        if data.resolution_notes is not None:
            osa_event.resolution_notes = data.resolution_notes
        if data.estimated_lost_sales is not None:
            osa_event.estimated_lost_sales = data.estimated_lost_sales
        if data.duration_hours is not None:
            osa_event.duration_hours = data.duration_hours

        osa_event = await self.repo.update(osa_event)
        return OSAEventResponse.model_validate(osa_event)

    async def resolve_osa_event(
        self, osa_event_id: uuid.UUID, resolution_notes: Optional[str] = None
    ) -> OSAEventResponse:
        """Mark an OSA event as resolved."""
        osa_event = await self.repo.get_by_id(osa_event_id)
        if not osa_event:
            raise ValueError(f"OSA event with ID {osa_event_id} not found")

        osa_event.resolved = True
        osa_event.resolved_date = datetime.utcnow()
        if resolution_notes:
            osa_event.resolution_notes = resolution_notes

        osa_event = await self.repo.update(osa_event)
        return OSAEventResponse.model_validate(osa_event)

