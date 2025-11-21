"""
Planning API router for dashboard overview.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.application.overview_service import PlanningOverviewService
from src.contexts.planning.domain.schemas import PlanningOverviewResponse
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/overview", tags=["Planning Overview"])


@router.get(
    "",
    response_model=PlanningOverviewResponse,
    summary="Get planning dashboard overview",
)
async def get_planning_overview(
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
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
    service = PlanningOverviewService(session, current_user.tenant_id)
    
    try:
        overview = await service.get_planning_overview()
        return overview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get planning overview: {str(e)}",
        )

