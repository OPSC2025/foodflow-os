"""
Deviation service for managing quality and safety deviations.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.fsq.domain.models import Deviation, DeviationStatus, CAPA, Lot
from src.contexts.fsq.domain.schemas import DeviationCreate, DeviationUpdate
from src.core.logging import logger


class DeviationService:
    """Service for deviation operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create_deviation(self, data: DeviationCreate) -> Deviation:
        """Create a new deviation."""
        # Check for duplicate deviation number
        stmt = select(Deviation).filter_by(
            tenant_id=self.tenant_id, deviation_number=data.deviation_number
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Deviation number '{data.deviation_number}' already exists")

        # Verify lot if provided
        if data.lot_id:
            stmt = select(Lot).filter_by(tenant_id=self.tenant_id, id=data.lot_id)
            result = await self.session.execute(stmt)
            lot = result.scalar_one_or_none()
            if not lot:
                raise ValueError(f"Lot with ID {data.lot_id} not found")

        deviation = Deviation(**data.model_dump(), tenant_id=self.tenant_id)
        self.session.add(deviation)
        await self.session.flush()
        await self.session.refresh(deviation)

        logger.warning(
            f"Created deviation {deviation.deviation_number} - Severity: {deviation.severity}",
            extra={
                "tenant_id": str(self.tenant_id),
                "deviation_id": str(deviation.id),
                "severity": deviation.severity,
            },
        )

        return deviation

    async def get_deviation(self, deviation_id: uuid.UUID) -> Optional[Deviation]:
        """Get a deviation by ID."""
        stmt = select(Deviation).filter_by(tenant_id=self.tenant_id, id=deviation_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_deviations(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[list[Deviation], int]:
        """List deviations with pagination and filters."""
        stmt = select(Deviation).filter_by(tenant_id=self.tenant_id)

        if status:
            stmt = stmt.filter_by(status=status)
        if severity:
            stmt = stmt.filter_by(severity=severity)
        if category:
            stmt = stmt.filter_by(category=category)
        if start_date:
            stmt = stmt.filter(Deviation.occurred_at >= start_date)
        if end_date:
            stmt = stmt.filter(Deviation.occurred_at <= end_date)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Get page
        stmt = stmt.order_by(Deviation.occurred_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        deviations = list(result.scalars().all())

        return deviations, total

    async def update_deviation(
        self, deviation_id: uuid.UUID, data: DeviationUpdate
    ) -> Deviation:
        """Update a deviation."""
        deviation = await self.get_deviation(deviation_id)
        if not deviation:
            raise ValueError(f"Deviation with ID {deviation_id} not found")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(deviation, field, value)

        await self.session.flush()

        return deviation

    async def close_deviation(
        self, deviation_id: uuid.UUID, closed_by: str, resolution_notes: Optional[str] = None
    ) -> Deviation:
        """Close a deviation."""
        deviation = await self.get_deviation(deviation_id)
        if not deviation:
            raise ValueError(f"Deviation with ID {deviation_id} not found")

        if deviation.status == DeviationStatus.CLOSED:
            raise ValueError(f"Deviation {deviation.deviation_number} is already closed")

        deviation.status = DeviationStatus.CLOSED
        deviation.closed_by = closed_by
        deviation.closed_at = datetime.utcnow()

        if resolution_notes:
            if deviation.investigation_notes:
                deviation.investigation_notes += f"\n\nResolution: {resolution_notes}"
            else:
                deviation.investigation_notes = f"Resolution: {resolution_notes}"

        await self.session.flush()

        logger.info(
            f"Closed deviation {deviation.deviation_number}",
            extra={"tenant_id": str(self.tenant_id), "deviation_id": str(deviation_id)},
        )

        return deviation

    async def link_to_capa(self, deviation_id: uuid.UUID, capa_id: uuid.UUID) -> Deviation:
        """Link a deviation to a CAPA."""
        deviation = await self.get_deviation(deviation_id)
        if not deviation:
            raise ValueError(f"Deviation with ID {deviation_id} not found")

        # Verify CAPA exists
        stmt = select(CAPA).filter_by(tenant_id=self.tenant_id, id=capa_id)
        result = await self.session.execute(stmt)
        capa = result.scalar_one_or_none()
        if not capa:
            raise ValueError(f"CAPA with ID {capa_id} not found")

        deviation.capa_id = capa_id
        deviation.requires_capa = True
        deviation.status = DeviationStatus.CAPA_REQUIRED

        await self.session.flush()

        logger.info(
            f"Linked deviation {deviation.deviation_number} to CAPA {capa.capa_number}",
            extra={"tenant_id": str(self.tenant_id)},
        )

        return deviation

    async def get_active_deviations_count(self) -> int:
        """Get count of active (non-closed) deviations."""
        stmt = select(func.count()).select_from(Deviation).filter(
            Deviation.tenant_id == self.tenant_id,
            Deviation.status != DeviationStatus.CLOSED,
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_deviations_by_severity(
        self, start_date: datetime, end_date: datetime
    ) -> dict[str, int]:
        """Get deviation counts grouped by severity."""
        stmt = select(
            Deviation.severity, func.count().label("count")
        ).filter(
            Deviation.tenant_id == self.tenant_id,
            Deviation.occurred_at >= start_date,
            Deviation.occurred_at <= end_date,
        ).group_by(Deviation.severity)

        result = await self.session.execute(stmt)
        rows = result.all()

        return {row.severity: row.count for row in rows}

