"""
PlantOps API router for money leak tracking and analysis.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.application.money_leak_service import MoneyLeakService
from src.contexts.plant_ops.domain.schemas import (
    MoneyLeakCreate,
    MoneyLeakResponse,
    MoneyLeakOverview,
    MoneyLeakSummary,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/money-leaks", tags=["Money Leaks"])


@router.post(
    "",
    response_model=MoneyLeakResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a money leak record",
)
async def create_money_leak(
    data: MoneyLeakCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new money leak record.
    
    Tracks financial losses from various sources like scrap, downtime, speed loss,
    yield loss, quality issues, changeover, and startup inefficiencies.
    """
    service = MoneyLeakService(session, current_user.tenant_id)
    
    try:
        money_leak = await service.create_money_leak(data)
        await session.commit()
        return money_leak
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create money leak: {str(e)}",
        )


@router.get(
    "",
    response_model=list[MoneyLeakResponse],
    summary="List money leak records",
)
async def list_money_leaks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    line_id: Optional[uuid.UUID] = Query(None, description="Filter by line ID"),
    plant_id: Optional[uuid.UUID] = Query(None, description="Filter by plant ID"),
    category: Optional[str] = Query(None, description="Filter by category (scrap_loss, downtime_loss, etc.)"),
    start_time: Optional[datetime] = Query(None, description="Filter by period start (>=)"),
    end_time: Optional[datetime] = Query(None, description="Filter by period start (<=)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List money leak records with optional filters.
    
    Returns a list of money leak records with various filtering options.
    """
    service = MoneyLeakService(session, current_user.tenant_id)
    
    try:
        money_leaks, total = await service.list_money_leaks(
            skip, limit, line_id, plant_id, category, start_time, end_time
        )
        return money_leaks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list money leaks: {str(e)}",
        )


@router.get(
    "/overview",
    response_model=MoneyLeakOverview,
    summary="Get money leak overview",
)
async def get_money_leak_overview(
    start_time: datetime = Query(..., description="Start of the period"),
    end_time: datetime = Query(..., description="End of the period"),
    plant_id: Optional[uuid.UUID] = Query(None, description="Filter by plant ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get comprehensive money leak overview for a period.
    
    Returns:
    - Total amount lost
    - Breakdown by category with percentages
    - Top lines by money leaks
    
    This is the main endpoint for money leak analysis and visualization.
    """
    service = MoneyLeakService(session, current_user.tenant_id)
    
    try:
        overview = await service.get_money_leak_overview(start_time, end_time, plant_id)
        return overview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch money leak overview: {str(e)}",
        )


@router.get(
    "/by-category",
    response_model=list[MoneyLeakSummary],
    summary="Get money leaks grouped by category",
)
async def get_money_leaks_by_category(
    start_time: datetime = Query(..., description="Start of the period"),
    end_time: datetime = Query(..., description="End of the period"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get money leaks grouped and summarized by category.
    
    Returns a list of categories with totals, counts, averages, and percentages.
    Useful for understanding which types of losses are most significant.
    """
    service = MoneyLeakService(session, current_user.tenant_id)
    
    try:
        summaries = await service.get_money_leaks_by_category(start_time, end_time)
        return summaries
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch money leaks by category: {str(e)}",
        )


@router.get(
    "/{money_leak_id}",
    response_model=MoneyLeakResponse,
    summary="Get money leak details",
)
async def get_money_leak(
    money_leak_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information about a specific money leak record.
    """
    service = MoneyLeakService(session, current_user.tenant_id)
    
    money_leak = await service.get_money_leak(money_leak_id)
    if not money_leak:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Money leak with ID {money_leak_id} not found",
        )
    
    return money_leak

