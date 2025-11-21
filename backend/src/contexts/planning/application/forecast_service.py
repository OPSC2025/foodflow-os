"""
Forecast service - business logic for demand forecasting.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.domain.models import Forecast, ForecastStatus
from src.contexts.planning.domain.schemas import (
    ForecastCreate,
    ForecastResponse,
    ForecastUpdate,
)
from src.contexts.planning.infrastructure.repositories import ForecastRepository


class ForecastService:
    """Service for forecast operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = ForecastRepository(session, tenant_id)

    async def create_forecast(self, data: ForecastCreate) -> ForecastResponse:
        """Create a new forecast."""
        forecast = Forecast(
            name=data.name,
            description=data.description,
            version=data.version,
            product_id=data.product_id,
            sku_id=data.sku_id,
            start_date=data.start_date,
            end_date=data.end_date,
            method=data.method,
            forecast_data=data.forecast_data,
            accuracy_metrics=data.accuracy_metrics,
            generated_by_ai=data.generated_by_ai,
            ai_model_version=data.ai_model_version,
            status=ForecastStatus.DRAFT,
            created_by=data.created_by,
            parent_forecast_id=data.parent_forecast_id,
        )

        forecast = await self.repo.create(forecast)
        return ForecastResponse.model_validate(forecast)

    async def get_forecast(self, forecast_id: uuid.UUID) -> Optional[ForecastResponse]:
        """Get forecast by ID."""
        forecast = await self.repo.get_by_id(forecast_id)
        if forecast:
            return ForecastResponse.model_validate(forecast)
        return None

    async def list_forecasts(
        self,
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[uuid.UUID] = None,
        sku_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> tuple[list[ForecastResponse], int]:
        """List forecasts with filters."""
        forecasts, total = await self.repo.list(skip, limit, product_id, sku_id, status)
        return (
            [ForecastResponse.model_validate(f) for f in forecasts],
            total,
        )

    async def update_forecast(
        self, forecast_id: uuid.UUID, data: ForecastUpdate
    ) -> ForecastResponse:
        """Update a forecast."""
        forecast = await self.repo.get_by_id(forecast_id)
        if not forecast:
            raise ValueError(f"Forecast with ID {forecast_id} not found")

        # Update fields
        if data.name is not None:
            forecast.name = data.name
        if data.description is not None:
            forecast.description = data.description
        if data.forecast_data is not None:
            forecast.forecast_data = data.forecast_data
        if data.accuracy_metrics is not None:
            forecast.accuracy_metrics = data.accuracy_metrics
        if data.status is not None:
            forecast.status = data.status

        forecast = await self.repo.update(forecast)
        return ForecastResponse.model_validate(forecast)

    async def activate_forecast(
        self, forecast_id: uuid.UUID, user_email: str
    ) -> ForecastResponse:
        """
        Activate a forecast.
        
        Supersedes any existing active forecast for the same product/SKU.
        """
        forecast = await self.repo.get_by_id(forecast_id)
        if not forecast:
            raise ValueError(f"Forecast with ID {forecast_id} not found")

        if forecast.status != ForecastStatus.DRAFT:
            raise ValueError(f"Only draft forecasts can be activated")

        # Supersede existing active forecast for same product/SKU
        if forecast.product_id:
            existing = await self.repo.get_latest_by_product(forecast.product_id)
            if existing and existing.id != forecast_id:
                existing.status = ForecastStatus.SUPERSEDED
                await self.repo.update(existing)

        # Activate the new forecast
        forecast.status = ForecastStatus.ACTIVE
        forecast.approved_by = user_email
        forecast.approved_at = datetime.utcnow()

        forecast = await self.repo.update(forecast)
        return ForecastResponse.model_validate(forecast)

    async def archive_forecast(self, forecast_id: uuid.UUID) -> ForecastResponse:
        """Archive a forecast."""
        forecast = await self.repo.get_by_id(forecast_id)
        if not forecast:
            raise ValueError(f"Forecast with ID {forecast_id} not found")

        forecast.status = ForecastStatus.ARCHIVED
        forecast = await self.repo.update(forecast)
        return ForecastResponse.model_validate(forecast)

    async def create_forecast_version(
        self,
        parent_forecast_id: uuid.UUID,
        new_version: str,
        forecast_data: dict,
        user_email: str,
    ) -> ForecastResponse:
        """
        Create a new version of an existing forecast.
        
        The new version starts as a draft.
        """
        parent = await self.repo.get_by_id(parent_forecast_id)
        if not parent:
            raise ValueError(f"Parent forecast with ID {parent_forecast_id} not found")

        # Create new version
        new_forecast = Forecast(
            name=parent.name,
            description=parent.description,
            version=new_version,
            product_id=parent.product_id,
            sku_id=parent.sku_id,
            start_date=parent.start_date,
            end_date=parent.end_date,
            method=parent.method,
            forecast_data=forecast_data,
            accuracy_metrics=None,  # Reset metrics for new version
            generated_by_ai=parent.generated_by_ai,
            ai_model_version=parent.ai_model_version,
            status=ForecastStatus.DRAFT,
            created_by=user_email,
            parent_forecast_id=parent_forecast_id,
        )

        new_forecast = await self.repo.create(new_forecast)
        return ForecastResponse.model_validate(new_forecast)

    async def update_accuracy_metrics(
        self, forecast_id: uuid.UUID, accuracy_metrics: dict
    ) -> ForecastResponse:
        """
        Update forecast accuracy metrics.
        
        Used when comparing forecast to actuals.
        """
        forecast = await self.repo.get_by_id(forecast_id)
        if not forecast:
            raise ValueError(f"Forecast with ID {forecast_id} not found")

        forecast.accuracy_metrics = accuracy_metrics
        forecast = await self.repo.update(forecast)
        return ForecastResponse.model_validate(forecast)

