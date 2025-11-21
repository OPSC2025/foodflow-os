"""
Planning API router for production plans.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.application.production_plan_service import ProductionPlanService
from src.contexts.planning.domain.schemas import (
    ProductionPlanCreate,
    ProductionPlanResponse,
    ProductionPlanUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/production-plans", tags=["Production Plans"])


@router.post(
    "",
    response_model=ProductionPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a production plan",
)
async def create_production_plan(
    data: ProductionPlanCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new production plan.
    
    Plans can be AI-generated or manually created.
    """
    service = ProductionPlanService(session, current_user.tenant_id)
    
    try:
        plan = await service.create_plan(data)
        await session.commit()
        return plan
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create production plan: {str(e)}",
        )


@router.get(
    "",
    response_model=list[ProductionPlanResponse],
    summary="List production plans",
)
async def list_production_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
    forecast_id: Optional[uuid.UUID] = Query(None, description="Filter by forecast ID"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List production plans with optional filters.
    """
    service = ProductionPlanService(session, current_user.tenant_id)
    
    try:
        plans, total = await service.list_plans(skip, limit, status, forecast_id)
        return plans
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list production plans: {str(e)}",
        )


@router.get(
    "/{plan_id}",
    response_model=ProductionPlanResponse,
    summary="Get production plan details",
)
async def get_production_plan(
    plan_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information about a specific production plan.
    """
    service = ProductionPlanService(session, current_user.tenant_id)
    
    plan = await service.get_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Production plan with ID {plan_id} not found",
        )
    
    return plan


@router.put(
    "/{plan_id}",
    response_model=ProductionPlanResponse,
    summary="Update production plan",
)
async def update_production_plan(
    plan_id: uuid.UUID,
    data: ProductionPlanUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update production plan details.
    """
    service = ProductionPlanService(session, current_user.tenant_id)
    
    try:
        plan = await service.update_plan(plan_id, data)
        await session.commit()
        return plan
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update production plan: {str(e)}",
        )


@router.put(
    "/{plan_id}/submit",
    response_model=ProductionPlanResponse,
    summary="Submit plan for approval",
)
async def submit_for_approval(
    plan_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Submit a production plan for approval.
    """
    service = ProductionPlanService(session, current_user.tenant_id)
    
    try:
        plan = await service.submit_for_approval(plan_id)
        await session.commit()
        return plan
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit plan for approval: {str(e)}",
        )


@router.put(
    "/{plan_id}/approve",
    response_model=ProductionPlanResponse,
    summary="Approve production plan",
)
async def approve_production_plan(
    plan_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Approve a production plan.
    """
    service = ProductionPlanService(session, current_user.tenant_id)
    
    try:
        plan = await service.approve_plan(plan_id, current_user.email)
        await session.commit()
        return plan
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve production plan: {str(e)}",
        )


@router.put(
    "/{plan_id}/execute",
    response_model=ProductionPlanResponse,
    summary="Start plan execution",
)
async def start_execution(
    plan_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Start executing an approved production plan.
    """
    service = ProductionPlanService(session, current_user.tenant_id)
    
    try:
        plan = await service.start_execution(plan_id)
        await session.commit()
        return plan
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start plan execution: {str(e)}",
        )


@router.put(
    "/{plan_id}/complete",
    response_model=ProductionPlanResponse,
    summary="Complete production plan",
)
async def complete_production_plan(
    plan_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Mark a production plan as completed.
    """
    service = ProductionPlanService(session, current_user.tenant_id)
    
    try:
        plan = await service.complete_plan(plan_id)
        await session.commit()
        return plan
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete production plan: {str(e)}",
        )


@router.delete(
    "/{plan_id}/cancel",
    response_model=ProductionPlanResponse,
    summary="Cancel production plan",
)
async def cancel_production_plan(
    plan_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Cancel a production plan.
    """
    service = ProductionPlanService(session, current_user.tenant_id)
    
    try:
        plan = await service.cancel_plan(plan_id)
        await session.commit()
        return plan
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel production plan: {str(e)}",
        )

