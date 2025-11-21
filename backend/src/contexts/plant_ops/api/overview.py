"""
PlantOps API router for workspace overview and dashboard.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.application.overview_service import OverviewService
from src.contexts.plant_ops.domain.schemas import PlantOpsOverview
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/overview", tags=["PlantOps Overview"])


@router.get(
    "",
    response_model=PlantOpsOverview,
    summary="Get PlantOps workspace overview",
)
async def get_overview(
    start_time: Optional[datetime] = Query(None, description="Start time for the period (default: 24 hours ago)"),
    end_time: Optional[datetime] = Query(None, description="End time for the period (default: now)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get comprehensive PlantOps workspace overview including:
    - Key performance indicators (KPIs)
    - Money leaks breakdown
    - Active alerts
    - Active trials count
    - Recent scrap events
    
    This is the main dashboard endpoint for the PlantOps workspace.
    """
    service = OverviewService(session, current_user.tenant_id)
    
    try:
        overview = await service.get_overview(start_time, end_time)
        return overview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch overview: {str(e)}",
        )

