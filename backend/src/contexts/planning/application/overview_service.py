"""
Planning Overview service - aggregated analytics for dashboard.
"""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.domain.schemas import PlanningOverviewResponse
from src.contexts.planning.infrastructure.repositories import (
    ForecastRepository,
    InventoryLevelRepository,
    ProductionPlanRepository,
)


class PlanningOverviewService:
    """Service for planning dashboard overview."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.forecast_repo = ForecastRepository(session, tenant_id)
        self.plan_repo = ProductionPlanRepository(session, tenant_id)
        self.inventory_repo = InventoryLevelRepository(session, tenant_id)

    async def get_planning_overview(self) -> PlanningOverviewResponse:
        """
        Get aggregated planning metrics for dashboard.
        
        Returns:
        - Active forecasts count
        - Active plans count
        - Plans pending approval
        - Low stock items count
        - Stockout items count
        - Average forecast accuracy (if available)
        """
        # Count active forecasts
        active_forecasts, _ = await self.forecast_repo.list(status="active", limit=1000)
        active_forecasts_count = len(active_forecasts)

        # Count active plans (approved or in progress)
        approved_plans, _ = await self.plan_repo.list(status="approved", limit=1000)
        in_progress_plans, _ = await self.plan_repo.list(status="in_progress", limit=1000)
        active_plans_count = len(approved_plans) + len(in_progress_plans)

        # Count plans pending approval
        pending_plans, _ = await self.plan_repo.list(status="pending_approval", limit=1000)
        plans_pending_approval = len(pending_plans)

        # Count low stock items
        low_stock_items, _ = await self.inventory_repo.list(
            is_below_safety_stock=True, limit=1000
        )
        low_stock_items_count = len(low_stock_items)

        # Count stockout items
        stockout_items, _ = await self.inventory_repo.list(is_stockout=True, limit=1000)
        stockout_items_count = len(stockout_items)

        # Calculate average forecast accuracy (MAPE)
        avg_forecast_accuracy = None
        if active_forecasts:
            mape_values = []
            for forecast in active_forecasts:
                if forecast.accuracy_metrics and "mape" in forecast.accuracy_metrics:
                    mape_values.append(forecast.accuracy_metrics["mape"])

            if mape_values:
                avg_forecast_accuracy = sum(mape_values) / len(mape_values)

        return PlanningOverviewResponse(
            active_forecasts_count=active_forecasts_count,
            active_plans_count=active_plans_count,
            plans_pending_approval=plans_pending_approval,
            low_stock_items_count=low_stock_items_count,
            stockout_items_count=stockout_items_count,
            avg_forecast_accuracy=avg_forecast_accuracy,
            total_inventory_value=None,  # TODO: Calculate if cost data available
            last_updated=datetime.utcnow(),
        )

