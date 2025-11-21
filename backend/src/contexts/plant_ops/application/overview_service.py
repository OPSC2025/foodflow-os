"""
Overview service for PlantOps workspace dashboard and KPIs.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.domain.models import (
    ProductionLine,
    ProductionBatch,
    BatchStatus,
    LineStatus,
    ScrapEvent,
    Trial,
    TrialStatus,
)
from src.contexts.plant_ops.domain.schemas import (
    PlantOpsOverview,
    PlantOpsKPI,
    PlantOpsAlert,
)
from src.contexts.plant_ops.application.money_leak_service import MoneyLeakService
from src.contexts.plant_ops.application.downtime_service import DowntimeService
from src.contexts.plant_ops.application.trial_service import TrialService
from src.core.logging import logger


class OverviewService:
    """Service for PlantOps workspace overview and dashboard."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.money_leak_service = MoneyLeakService(session, tenant_id)
        self.downtime_service = DowntimeService(session, tenant_id)
        self.trial_service = TrialService(session, tenant_id)

    async def get_overview(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> PlantOpsOverview:
        """Get comprehensive PlantOps overview for dashboard."""
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=1)  # Default to last 24 hours

        logger.info(
            f"Fetching PlantOps overview for period {start_time} to {end_time}",
            extra={
                "tenant_id": str(self.tenant_id),
                "period_start": start_time.isoformat(),
                "period_end": end_time.isoformat(),
            },
        )

        # Fetch KPIs
        kpis = await self._get_kpis(start_time, end_time)

        # Fetch money leaks
        money_leaks = await self.money_leak_service.get_money_leak_overview(
            start_time, end_time
        )

        # Fetch alerts
        alerts = await self._get_alerts()

        # Get active trials count
        active_trials = await self.trial_service.get_active_trials_count()

        # Get recent scrap events count
        recent_scrap_count = await self._get_recent_scrap_count(start_time)

        return PlantOpsOverview(
            period_start=start_time,
            period_end=end_time,
            kpis=kpis,
            money_leaks=money_leaks,
            alerts=alerts,
            active_trials=active_trials,
            recent_scrap_events=recent_scrap_count,
        )

    async def _get_kpis(self, start_time: datetime, end_time: datetime) -> PlantOpsKPI:
        """Calculate key performance indicators."""
        # Total lines
        stmt = select(func.count()).select_from(ProductionLine).filter_by(
            tenant_id=self.tenant_id
        )
        total_lines = (await self.session.execute(stmt)).scalar() or 0

        # Active lines
        stmt = select(func.count()).select_from(ProductionLine).filter_by(
            tenant_id=self.tenant_id, is_active=True
        )
        active_lines = (await self.session.execute(stmt)).scalar() or 0

        # Running batches
        stmt = select(func.count()).select_from(ProductionBatch).filter_by(
            tenant_id=self.tenant_id, status=BatchStatus.IN_PROGRESS
        )
        running_batches = (await self.session.execute(stmt)).scalar() or 0

        # Average OEE for completed batches in period
        stmt = select(func.avg(ProductionBatch.oee)).filter(
            ProductionBatch.tenant_id == self.tenant_id,
            ProductionBatch.status == BatchStatus.COMPLETED,
            ProductionBatch.actual_end_time >= start_time,
            ProductionBatch.actual_end_time <= end_time,
            ProductionBatch.oee.isnot(None),
        )
        avg_oee = (await self.session.execute(stmt)).scalar()
        average_oee = float(avg_oee) if avg_oee else 0.0

        # Total scrap cost today
        total_scrap_cost = await self.money_leak_service.get_total_scrap_cost_today()

        # Total downtime minutes today
        total_downtime = await self.downtime_service.get_total_downtime_today()

        return PlantOpsKPI(
            total_lines=total_lines,
            active_lines=active_lines,
            running_batches=running_batches,
            average_oee=average_oee,
            total_scrap_cost_today=total_scrap_cost,
            total_downtime_minutes_today=total_downtime,
        )

    async def _get_alerts(self) -> list[PlantOpsAlert]:
        """Generate alerts based on current conditions."""
        alerts = []

        # Check for lines in downtime
        stmt = select(ProductionLine).filter_by(
            tenant_id=self.tenant_id, status=LineStatus.DOWNTIME
        )
        result = await self.session.execute(stmt)
        downtime_lines = list(result.scalars().all())

        for line in downtime_lines:
            alerts.append(
                PlantOpsAlert(
                    id=uuid.uuid4(),  # Temporary ID for alerts
                    severity="high",
                    type="downtime",
                    title=f"Line {line.line_number} is down",
                    description="Production line experiencing downtime",
                    line_id=line.id,
                    line_number=line.line_number,
                    timestamp=datetime.utcnow(),
                    is_acknowledged=False,
                )
            )

        # Check for recent high scrap events (last 2 hours)
        two_hours_ago = datetime.utcnow() - timedelta(hours=2)
        stmt = select(ScrapEvent).filter(
            ScrapEvent.tenant_id == self.tenant_id,
            ScrapEvent.event_time >= two_hours_ago,
            ScrapEvent.severity.in_(["high", "critical"]),
        ).order_by(ScrapEvent.event_time.desc()).limit(5)

        result = await self.session.execute(stmt)
        recent_scrap = list(result.scalars().all())

        for scrap in recent_scrap:
            # Get batch info
            if scrap.batch_id:
                stmt = select(ProductionBatch).filter_by(id=scrap.batch_id)
                batch_result = await self.session.execute(stmt)
                batch = batch_result.scalar_one_or_none()

                alerts.append(
                    PlantOpsAlert(
                        id=scrap.id,
                        severity=scrap.severity or "medium",
                        type="scrap_spike",
                        title=f"High scrap detected: {scrap.scrap_type}",
                        description=f"Scrap quantity: {scrap.quantity} units",
                        line_id=batch.line_id if batch else None,
                        timestamp=scrap.event_time,
                        is_acknowledged=False,
                    )
                )

        # Sort alerts by severity and timestamp
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda a: (severity_order.get(a.severity, 3), a.timestamp), reverse=True)

        return alerts[:10]  # Return top 10 alerts

    async def _get_recent_scrap_count(self, since: datetime) -> int:
        """Get count of scrap events since a given time."""
        stmt = select(func.count()).select_from(ScrapEvent).filter(
            ScrapEvent.tenant_id == self.tenant_id,
            ScrapEvent.event_time >= since,
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

