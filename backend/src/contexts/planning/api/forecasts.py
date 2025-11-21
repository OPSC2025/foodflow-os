"""
Planning API router for forecasts.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.application.forecast_service import ForecastService
from src.contexts.planning.domain.schemas import (
    ForecastCreate,
    ForecastResponse,
    ForecastUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


@router.post(
    "",
    response_model=ForecastResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a forecast",
)
async def create_forecast(
    data: ForecastCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new demand forecast.
    
    Forecasts can be AI-generated or manually entered.
    """
    service = ForecastService(session, current_user.tenant_id)
    
    try:
        forecast = await service.create_forecast(data)
        await session.commit()
        return forecast
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create forecast: {str(e)}",
        )


@router.get(
    "",
    response_model=list[ForecastResponse],
    summary="List forecasts",
)
async def list_forecasts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    product_id: Optional[uuid.UUID] = Query(None, description="Filter by product ID"),
    sku_id: Optional[uuid.UUID] = Query(None, description="Filter by SKU ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List forecasts with optional filters.
    """
    service = ForecastService(session, current_user.tenant_id)
    
    try:
        forecasts, total = await service.list_forecasts(skip, limit, product_id, sku_id, status)
        return forecasts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list forecasts: {str(e)}",
        )


@router.get(
    "/{forecast_id}",
    response_model=ForecastResponse,
    summary="Get forecast details",
)
async def get_forecast(
    forecast_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information about a specific forecast.
    """
    service = ForecastService(session, current_user.tenant_id)
    
    forecast = await service.get_forecast(forecast_id)
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast with ID {forecast_id} not found",
        )
    
    return forecast


@router.put(
    "/{forecast_id}",
    response_model=ForecastResponse,
    summary="Update forecast",
)
async def update_forecast(
    forecast_id: uuid.UUID,
    data: ForecastUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update forecast details.
    """
    service = ForecastService(session, current_user.tenant_id)
    
    try:
        forecast = await service.update_forecast(forecast_id, data)
        await session.commit()
        return forecast
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update forecast: {str(e)}",
        )


@router.put(
    "/{forecast_id}/activate",
    response_model=ForecastResponse,
    summary="Activate forecast",
)
async def activate_forecast(
    forecast_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Activate a forecast.
    
    Supersedes any existing active forecast for the same product/SKU.
    """
    service = ForecastService(session, current_user.tenant_id)
    
    try:
        forecast = await service.activate_forecast(forecast_id, current_user.email)
        await session.commit()
        return forecast
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate forecast: {str(e)}",
        )


@router.post(
    "/{forecast_id}/new-version",
    response_model=ForecastResponse,
    summary="Create new forecast version",
)
async def create_forecast_version(
    forecast_id: uuid.UUID,
    new_version: str = Query(..., description="New version number"),
    forecast_data: dict = Query(..., description="Updated forecast data"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new version of an existing forecast.
    
    The new version starts as a draft.
    """
    service = ForecastService(session, current_user.tenant_id)
    
    try:
        forecast = await service.create_forecast_version(
            forecast_id, new_version, forecast_data, current_user.email
        )
        await session.commit()
        return forecast
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create forecast version: {str(e)}",
        )


@router.delete(
    "/{forecast_id}/archive",
    response_model=ForecastResponse,
    summary="Archive forecast",
)
async def archive_forecast(
    forecast_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Archive a forecast.
    """
    service = ForecastService(session, current_user.tenant_id)
    
    try:
        forecast = await service.archive_forecast(forecast_id)
        await session.commit()
        return forecast
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive forecast: {str(e)}",
        )

