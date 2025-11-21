"""
PlantOps API router for trials.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.application.trial_service import TrialService
from src.contexts.plant_ops.domain.schemas import (
    PaginatedResponse,
    TrialCreate,
    TrialResponse,
    TrialUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/trials", tags=["Trials"])


@router.post(
    "",
    response_model=TrialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new trial",
)
async def create_trial(
    data: TrialCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new line trial.
    
    A trial is an experiment to test new parameters, products, or configurations on a line.
    Can be suggested by AI or manually created.
    """
    service = TrialService(session, current_user.tenant_id)
    
    try:
        trial = await service.create_trial(data)
        await session.commit()
        return trial
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create trial: {str(e)}",
        )


@router.get(
    "",
    response_model=list[TrialResponse],
    summary="List trials",
)
async def list_trials(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    line_id: Optional[uuid.UUID] = Query(None, description="Filter by line ID"),
    status: Optional[str] = Query(None, description="Filter by status (planned, in_progress, completed, cancelled)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List trials with optional filters.
    
    Returns a list of trials, optionally filtered by line and status.
    """
    service = TrialService(session, current_user.tenant_id)
    
    try:
        trials, total = await service.list_trials(skip, limit, line_id, status)
        return trials
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list trials: {str(e)}",
        )


@router.get(
    "/{trial_id}",
    response_model=TrialResponse,
    summary="Get trial details",
)
async def get_trial(
    trial_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information about a specific trial.
    """
    service = TrialService(session, current_user.tenant_id)
    
    trial = await service.get_trial(trial_id)
    if not trial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trial with ID {trial_id} not found",
        )
    
    return trial


@router.put(
    "/{trial_id}/start",
    response_model=TrialResponse,
    summary="Start a trial",
)
async def start_trial(
    trial_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Start a planned trial.
    
    Changes trial status from PLANNED to IN_PROGRESS and records the actual start time.
    """
    service = TrialService(session, current_user.tenant_id)
    
    try:
        trial = await service.start_trial(trial_id)
        await session.commit()
        return trial
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start trial: {str(e)}",
        )


@router.put(
    "/{trial_id}/complete",
    response_model=TrialResponse,
    summary="Complete a trial",
)
async def complete_trial(
    trial_id: uuid.UUID,
    data: TrialUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Complete a trial with results.
    
    Changes trial status to COMPLETED, records results, observations, and learnings.
    Should include:
    - results: actual outcomes (e.g., {actual_oee: 87, actual_scrap: 1.5})
    - was_successful: whether the trial met success criteria
    - observations: what was observed during the trial
    - learnings: key takeaways
    - recommendations: next steps or recommendations
    """
    service = TrialService(session, current_user.tenant_id)
    
    try:
        trial = await service.complete_trial(trial_id, data)
        await session.commit()
        return trial
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete trial: {str(e)}",
        )


@router.put(
    "/{trial_id}",
    response_model=TrialResponse,
    summary="Update a trial",
)
async def update_trial(
    trial_id: uuid.UUID,
    data: TrialUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update trial details.
    
    Can update parameters, observations, learnings, or other trial details.
    """
    service = TrialService(session, current_user.tenant_id)
    
    try:
        trial = await service.update_trial(trial_id, data)
        await session.commit()
        return trial
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update trial: {str(e)}",
        )


@router.delete(
    "/{trial_id}/cancel",
    response_model=TrialResponse,
    summary="Cancel a trial",
)
async def cancel_trial(
    trial_id: uuid.UUID,
    reason: Optional[str] = Query(None, description="Reason for cancellation"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Cancel a trial.
    
    Changes trial status to CANCELLED. Cannot cancel completed trials.
    """
    service = TrialService(session, current_user.tenant_id)
    
    try:
        trial = await service.cancel_trial(trial_id, reason)
        await session.commit()
        return trial
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel trial: {str(e)}",
        )

