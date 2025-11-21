"""
Downtime service for tracking and managing line downtime.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.domain.models import Downtime, ProductionLine, ProductionBatch
from src.contexts.plant_ops.domain.schemas import DowntimeCreate, DowntimeUpdate
from src.core.logging import logger


class DowntimeService:
    """Service for downtime operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create_downtime(self, data: DowntimeCreate) -> Downtime:
        """Create a new downtime record."""
        # Verify line exists
        stmt = select(ProductionLine).filter_by(tenant_id=self.tenant_id, id=data.line_id)
        result = await self.session.execute(stmt)
        line = result.scalar_one_or_none()

        if not line:
            raise ValueError(f"Line with ID {data.line_id} not found")

        # Verify batch exists if provided
        if data.batch_id:
            stmt = select(ProductionBatch).filter_by(tenant_id=self.tenant_id, id=data.batch_id)
            result = await self.session.execute(stmt)
            batch = result.scalar_one_or_none()
            if not batch:
                raise ValueError(f"Batch with ID {data.batch_id} not found")

        downtime = Downtime(**data.model_dump(), tenant_id=self.tenant_id)
        self.session.add(downtime)
        await self.session.flush()
        await self.session.refresh(downtime)

        logger.info(
            f"Created downtime record for line {line.line_number} - Reason: {downtime.reason_category}",
            extra={
                "tenant_id": str(self.tenant_id),
                "downtime_id": str(downtime.id),
                "line_id": str(data.line_id),
            },
        )

        return downtime

    async def get_downtime(self, downtime_id: uuid.UUID) -> Optional[Downtime]:
        """Get a downtime record by ID."""
        stmt = select(Downtime).filter_by(tenant_id=self.tenant_id, id=downtime_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_downtimes(
        self,
        skip: int = 0,
        limit: int = 100,
        line_id: Optional[uuid.UUID] = None,
        is_planned: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> tuple[list[Downtime], int]:
        """List downtime records with pagination."""
        stmt = select(Downtime).filter_by(tenant_id=self.tenant_id)

        if line_id:
            stmt = stmt.filter_by(line_id=line_id)
        if is_planned is not None:
            stmt = stmt.filter_by(is_planned=is_planned)
        if start_time:
            stmt = stmt.filter(Downtime.start_time >= start_time)
        if end_time:
            stmt = stmt.filter(Downtime.start_time <= end_time)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Get page
        stmt = stmt.order_by(Downtime.start_time.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        downtimes = list(result.scalars().all())

        return downtimes, total

    async def end_downtime(self, downtime_id: uuid.UUID, data: DowntimeUpdate) -> Downtime:
        """End a downtime period and update details."""
        downtime = await self.get_downtime(downtime_id)
        if not downtime:
            raise ValueError(f"Downtime with ID {downtime_id} not found")

        if downtime.end_time:
            raise ValueError("Downtime period has already ended")

        # Set end time if not provided
        if not data.end_time:
            data.end_time = datetime.utcnow()

        # Calculate duration if not provided
        if data.end_time and not data.duration_minutes:
            delta = data.end_time - downtime.start_time
            data.duration_minutes = delta.total_seconds() / 60

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(downtime, field, value)

        await self.session.flush()

        logger.info(
            f"Ended downtime record {downtime_id} - Duration: {downtime.duration_minutes} min",
            extra={
                "tenant_id": str(self.tenant_id),
                "downtime_id": str(downtime_id),
                "duration_minutes": downtime.duration_minutes,
            },
        )

        return downtime

    async def update_downtime(self, downtime_id: uuid.UUID, data: DowntimeUpdate) -> Downtime:
        """Update a downtime record."""
        downtime = await self.get_downtime(downtime_id)
        if not downtime:
            raise ValueError(f"Downtime with ID {downtime_id} not found")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)

        # Recalculate duration if end_time changed
        if "end_time" in update_data and update_data["end_time"]:
            if downtime.start_time:
                delta = update_data["end_time"] - downtime.start_time
                downtime.duration_minutes = delta.total_seconds() / 60

        for field, value in update_data.items():
            setattr(downtime, field, value)

        await self.session.flush()

        return downtime

    async def get_total_downtime_today(self) -> float:
        """Get total downtime in minutes for today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        stmt = select(func.sum(Downtime.duration_minutes)).filter(
            Downtime.tenant_id == self.tenant_id,
            Downtime.start_time >= today_start,
            Downtime.duration_minutes.isnot(None)
        )

        result = await self.session.execute(stmt)
        total = result.scalar()

        return float(total) if total else 0.0

    async def get_downtime_by_reason(
        self, start_time: datetime, end_time: datetime
    ) -> dict[str, float]:
        """Get downtime breakdown by reason category."""
        stmt = select(
            Downtime.reason_category,
            func.sum(Downtime.duration_minutes).label("total_minutes")
        ).filter(
            Downtime.tenant_id == self.tenant_id,
            Downtime.start_time >= start_time,
            Downtime.start_time <= end_time,
            Downtime.duration_minutes.isnot(None)
        ).group_by(Downtime.reason_category)

        result = await self.session.execute(stmt)
        rows = result.all()

        return {row.reason_category: float(row.total_minutes or 0) for row in rows}

