"""
Money leak service for tracking and calculating financial losses.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.domain.models import (
    MoneyLeak,
    MoneyLeakCategory,
    ProductionBatch,
    ProductionLine,
    Downtime,
    ScrapEvent,
)
from src.contexts.plant_ops.domain.schemas import (
    MoneyLeakCreate,
    MoneyLeakSummary,
    MoneyLeakOverview,
)
from src.core.logging import logger


class MoneyLeakService:
    """Service for money leak calculations and tracking."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create_money_leak(self, data: MoneyLeakCreate) -> MoneyLeak:
        """Create a new money leak record."""
        money_leak = MoneyLeak(**data.model_dump(), tenant_id=self.tenant_id)
        self.session.add(money_leak)
        await self.session.flush()
        await self.session.refresh(money_leak)

        logger.info(
            f"Created money leak record - Category: {money_leak.category}, Amount: ${money_leak.amount_usd}",
            extra={
                "tenant_id": str(self.tenant_id),
                "money_leak_id": str(money_leak.id),
                "category": money_leak.category,
                "amount_usd": float(money_leak.amount_usd),
            },
        )

        return money_leak

    async def get_money_leak(self, money_leak_id: uuid.UUID) -> Optional[MoneyLeak]:
        """Get a money leak record by ID."""
        stmt = select(MoneyLeak).filter_by(tenant_id=self.tenant_id, id=money_leak_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_money_leaks(
        self,
        skip: int = 0,
        limit: int = 100,
        line_id: Optional[uuid.UUID] = None,
        plant_id: Optional[uuid.UUID] = None,
        category: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> tuple[list[MoneyLeak], int]:
        """List money leak records with pagination."""
        stmt = select(MoneyLeak).filter_by(tenant_id=self.tenant_id)

        if line_id:
            stmt = stmt.filter_by(line_id=line_id)
        if plant_id:
            stmt = stmt.filter_by(plant_id=plant_id)
        if category:
            stmt = stmt.filter_by(category=category)
        if start_time:
            stmt = stmt.filter(MoneyLeak.period_start >= start_time)
        if end_time:
            stmt = stmt.filter(MoneyLeak.period_start <= end_time)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Get page
        stmt = stmt.order_by(MoneyLeak.period_start.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        money_leaks = list(result.scalars().all())

        return money_leaks, total

    async def calculate_scrap_loss(
        self,
        batch_id: uuid.UUID,
        scrap_quantity: float,
        unit_cost: float,
    ) -> MoneyLeak:
        """Calculate and record scrap loss for a batch."""
        # Get batch info
        stmt = select(ProductionBatch).filter_by(tenant_id=self.tenant_id, id=batch_id)
        result = await self.session.execute(stmt)
        batch = result.scalar_one_or_none()

        if not batch:
            raise ValueError(f"Batch with ID {batch_id} not found")

        amount_usd = scrap_quantity * unit_cost

        money_leak = MoneyLeak(
            tenant_id=self.tenant_id,
            period_start=batch.actual_start_time or datetime.utcnow(),
            period_end=datetime.utcnow(),
            line_id=batch.line_id,
            batch_id=batch_id,
            category=MoneyLeakCategory.SCRAP_LOSS,
            amount_usd=Decimal(str(amount_usd)),
            quantity_lost=Decimal(str(scrap_quantity)),
            unit_cost=Decimal(str(unit_cost)),
            description=f"Scrap loss for batch {batch.batch_number}",
            calculation_method="scrap_quantity * unit_cost",
        )

        self.session.add(money_leak)
        await self.session.flush()

        return money_leak

    async def calculate_downtime_loss(
        self,
        downtime_id: uuid.UUID,
        hourly_cost: float,
    ) -> MoneyLeak:
        """Calculate and record downtime loss."""
        # Get downtime info
        stmt = select(Downtime).filter_by(tenant_id=self.tenant_id, id=downtime_id)
        result = await self.session.execute(stmt)
        downtime = result.scalar_one_or_none()

        if not downtime:
            raise ValueError(f"Downtime with ID {downtime_id} not found")

        if not downtime.duration_minutes:
            raise ValueError("Downtime duration not calculated yet")

        amount_usd = (downtime.duration_minutes / 60) * hourly_cost

        money_leak = MoneyLeak(
            tenant_id=self.tenant_id,
            period_start=downtime.start_time,
            period_end=downtime.end_time or datetime.utcnow(),
            line_id=downtime.line_id,
            batch_id=downtime.batch_id,
            category=MoneyLeakCategory.DOWNTIME_LOSS,
            subcategory=downtime.reason_category,
            amount_usd=Decimal(str(amount_usd)),
            time_lost_minutes=Decimal(str(downtime.duration_minutes)),
            hourly_cost=Decimal(str(hourly_cost)),
            description=f"Downtime loss: {downtime.reason_category}",
            root_cause=downtime.root_cause,
            calculation_method="(duration_minutes / 60) * hourly_cost",
        )

        self.session.add(money_leak)
        await self.session.flush()

        return money_leak

    async def get_total_scrap_cost_today(self) -> float:
        """Get total scrap cost for today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        stmt = select(func.sum(MoneyLeak.amount_usd)).filter(
            MoneyLeak.tenant_id == self.tenant_id,
            MoneyLeak.category == MoneyLeakCategory.SCRAP_LOSS,
            MoneyLeak.period_start >= today_start,
        )

        result = await self.session.execute(stmt)
        total = result.scalar()

        return float(total) if total else 0.0

    async def get_money_leak_overview(
        self, start_time: datetime, end_time: datetime, plant_id: Optional[uuid.UUID] = None
    ) -> MoneyLeakOverview:
        """Get comprehensive money leak overview for a period."""
        stmt = select(MoneyLeak).filter(
            MoneyLeak.tenant_id == self.tenant_id,
            MoneyLeak.period_start >= start_time,
            MoneyLeak.period_start <= end_time,
        )

        if plant_id:
            stmt = stmt.filter_by(plant_id=plant_id)

        result = await self.session.execute(stmt)
        money_leaks = list(result.scalars().all())

        # Calculate total
        total_amount = sum(float(leak.amount_usd) for leak in money_leaks)

        # Group by category
        category_totals: dict[str, dict] = {}
        for leak in money_leaks:
            if leak.category not in category_totals:
                category_totals[leak.category] = {
                    "total": 0.0,
                    "count": 0,
                }
            category_totals[leak.category]["total"] += float(leak.amount_usd)
            category_totals[leak.category]["count"] += 1

        # Build category summaries
        by_category = []
        for category, data in category_totals.items():
            percentage = (data["total"] / total_amount * 100) if total_amount > 0 else 0
            by_category.append(
                MoneyLeakSummary(
                    category=category,
                    total_amount_usd=data["total"],
                    count=data["count"],
                    average_amount_usd=data["total"] / data["count"] if data["count"] > 0 else 0,
                    percentage_of_total=percentage,
                )
            )

        # Sort by total amount descending
        by_category.sort(key=lambda x: x.total_amount_usd, reverse=True)

        # Get top lines
        line_totals: dict[uuid.UUID, float] = {}
        line_numbers: dict[uuid.UUID, str] = {}

        for leak in money_leaks:
            if leak.line_id:
                if leak.line_id not in line_totals:
                    line_totals[leak.line_id] = 0.0
                    # Fetch line number (in practice, would use a join or cache)
                    stmt = select(ProductionLine.line_number).filter_by(
                        tenant_id=self.tenant_id, id=leak.line_id
                    )
                    result = await self.session.execute(stmt)
                    line_number = result.scalar_one_or_none()
                    line_numbers[leak.line_id] = line_number or "Unknown"

                line_totals[leak.line_id] += float(leak.amount_usd)

        top_lines = [
            {
                "line_id": str(line_id),
                "line_number": line_numbers[line_id],
                "total_amount": amount,
            }
            for line_id, amount in sorted(
                line_totals.items(), key=lambda x: x[1], reverse=True
            )[:5]
        ]

        return MoneyLeakOverview(
            period_start=start_time,
            period_end=end_time,
            total_amount_usd=total_amount,
            by_category=by_category,
            top_lines=top_lines,
        )

    async def get_money_leaks_by_category(
        self, start_time: datetime, end_time: datetime
    ) -> list[MoneyLeakSummary]:
        """Get money leaks grouped by category."""
        overview = await self.get_money_leak_overview(start_time, end_time)
        return overview.by_category

