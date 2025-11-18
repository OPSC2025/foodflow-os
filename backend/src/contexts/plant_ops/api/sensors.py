"""
PlantOps API router for sensors and sensor readings.

Handles HTTP endpoints for sensor management and data ingestion.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.application.services import SensorService
from src.contexts.plant_ops.domain.schemas import (
    PaginatedResponse,
    SensorCreate,
    SensorReadingBulkCreate,
    SensorReadingCreate,
    SensorReadingResponse,
    SensorResponse,
    SensorUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sensor",
)
async def create_sensor(
    data: SensorCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new sensor.
    
    Requires authentication and appropriate permissions.
    """
    service = SensorService(session, current_user.tenant_id)
    
    try:
        sensor = await service.create_sensor(data)
        await session.commit()
        return sensor
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List sensors",
)
async def list_sensors(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    line_id: Optional[uuid.UUID] = Query(None, description="Filter by line ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List sensors with pagination and optional filters.
    
    Returns a paginated list of sensors for the current tenant.
    """
    service = SensorService(session, current_user.tenant_id)
    
    skip = (page - 1) * page_size
    sensors, total = await service.list_sensors(skip, page_size, line_id, sensor_type, is_active)
    
    import math
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return PaginatedResponse(
        items=[SensorResponse.model_validate(sensor) for sensor in sensors],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/{sensor_id}",
    response_model=SensorResponse,
    summary="Get a sensor by ID",
)
async def get_sensor(
    sensor_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get a specific sensor by ID.
    
    Returns 404 if the sensor doesn't exist or doesn't belong to the current tenant.
    """
    service = SensorService(session, current_user.tenant_id)
    
    sensor = await service.get_sensor(sensor_id)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with ID {sensor_id} not found",
        )
    
    return sensor


@router.get(
    "/by-code/{sensor_code}",
    response_model=SensorResponse,
    summary="Get a sensor by sensor code",
)
async def get_sensor_by_code(
    sensor_code: str,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get a specific sensor by sensor code.
    
    Returns 404 if the sensor doesn't exist or doesn't belong to the current tenant.
    """
    service = SensorService(session, current_user.tenant_id)
    
    sensor = await service.get_sensor_by_code(sensor_code)
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor with code '{sensor_code}' not found",
        )
    
    return sensor


@router.patch(
    "/{sensor_id}",
    response_model=SensorResponse,
    summary="Update a sensor",
)
async def update_sensor(
    sensor_id: uuid.UUID,
    data: SensorUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update a sensor.
    
    Only provided fields will be updated. Omitted fields remain unchanged.
    """
    service = SensorService(session, current_user.tenant_id)
    
    try:
        sensor = await service.update_sensor(sensor_id, data)
        await session.commit()
        return sensor
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete(
    "/{sensor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sensor",
)
async def delete_sensor(
    sensor_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Delete a sensor.
    
    This will also delete all associated sensor readings.
    Use with caution as this operation cannot be undone.
    """
    service = SensorService(session, current_user.tenant_id)
    
    try:
        deleted = await service.repo.delete(sensor_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sensor with ID {sensor_id} not found",
            )
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Sensor Readings Endpoints

@router.post(
    "/{sensor_id}/readings",
    response_model=SensorReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a sensor reading",
)
async def record_reading(
    sensor_id: uuid.UUID,
    data: SensorReadingCreate,
    check_anomaly: bool = Query(True, description="Check for anomalies"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Record a sensor reading.
    
    Automatically checks for anomalies based on sensor min/max values.
    Publishes an AnomalyDetectedEvent if an anomaly is found.
    """
    # Ensure sensor_id matches
    if data.sensor_id != sensor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sensor ID in path must match sensor ID in request body",
        )
    
    service = SensorService(session, current_user.tenant_id)
    
    try:
        reading = await service.record_reading(data, check_anomaly)
        await session.commit()
        return reading
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    "/readings/bulk",
    response_model=list[SensorReadingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record multiple sensor readings in bulk",
)
async def record_readings_bulk(
    data: SensorReadingBulkCreate,
    check_anomaly: bool = Query(True, description="Check for anomalies"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Record multiple sensor readings in bulk.
    
    This is optimized for high-throughput sensor data ingestion.
    Maximum 1000 readings per request.
    """
    service = SensorService(session, current_user.tenant_id)
    
    try:
        readings = await service.record_readings_bulk(data.readings, check_anomaly)
        await session.commit()
        return readings
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{sensor_id}/readings",
    response_model=PaginatedResponse,
    summary="Get sensor readings",
)
async def get_sensor_readings(
    sensor_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(1000, ge=1, le=10000, description="Items per page"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time (ISO format)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get sensor readings with pagination and time filters.
    
    Returns a paginated list of sensor readings for the specified sensor.
    """
    service = SensorService(session, current_user.tenant_id)
    
    skip = (page - 1) * page_size
    readings, total = await service.get_sensor_readings(
        sensor_id, skip, page_size, start_time, end_time
    )
    
    import math
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    return PaginatedResponse(
        items=[SensorReadingResponse.model_validate(reading) for reading in readings],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
