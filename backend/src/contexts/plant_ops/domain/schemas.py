"""
PlantOps context Pydantic schemas for API validation and serialization.

These schemas define the structure of data for API requests and responses.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# Production Line Schemas

class ProductionLineBase(BaseModel):
    """Base schema for production line."""
    
    line_number: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    plant_id: Optional[uuid.UUID] = None
    plant_name: Optional[str] = None
    location: Optional[str] = None
    design_speed: Optional[float] = Field(None, gt=0)
    max_speed: Optional[float] = Field(None, gt=0)
    min_speed: Optional[float] = Field(None, gt=0)


class ProductionLineCreate(ProductionLineBase):
    """Schema for creating a production line."""
    pass


class ProductionLineUpdate(BaseModel):
    """Schema for updating a production line."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    current_speed: Optional[float] = Field(None, ge=0)
    design_speed: Optional[float] = Field(None, gt=0)
    max_speed: Optional[float] = Field(None, gt=0)
    min_speed: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None


class ProductionLineResponse(ProductionLineBase):
    """Schema for production line response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    current_speed: Optional[float] = None
    current_batch_id: Optional[uuid.UUID] = None
    is_active: bool
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Production Batch Schemas

class ProductionBatchBase(BaseModel):
    """Base schema for production batch."""
    
    batch_number: str = Field(..., min_length=1, max_length=100)
    work_order_number: Optional[str] = Field(None, max_length=100)
    product_id: Optional[uuid.UUID] = None
    product_code: str = Field(..., min_length=1, max_length=100)
    product_name: str = Field(..., min_length=1, max_length=255)
    line_id: uuid.UUID
    target_quantity: float = Field(..., gt=0)
    target_speed: Optional[float] = Field(None, gt=0)
    planned_start_time: Optional[datetime] = None
    planned_end_time: Optional[datetime] = None
    operator_id: Optional[uuid.UUID] = None
    operator_name: Optional[str] = None
    shift: Optional[str] = None


class ProductionBatchCreate(ProductionBatchBase):
    """Schema for creating a production batch."""
    pass


class ProductionBatchUpdate(BaseModel):
    """Schema for updating a production batch."""
    
    status: Optional[str] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    produced_quantity: Optional[float] = Field(None, ge=0)
    good_quantity: Optional[float] = Field(None, ge=0)
    scrap_quantity: Optional[float] = Field(None, ge=0)
    average_speed: Optional[float] = Field(None, ge=0)
    availability: Optional[float] = Field(None, ge=0, le=100)
    performance: Optional[float] = Field(None, ge=0, le=100)
    quality: Optional[float] = Field(None, ge=0, le=100)
    oee: Optional[float] = Field(None, ge=0, le=100)
    planned_downtime_minutes: Optional[float] = Field(None, ge=0)
    unplanned_downtime_minutes: Optional[float] = Field(None, ge=0)
    labor_cost: Optional[float] = Field(None, ge=0)
    material_cost: Optional[float] = Field(None, ge=0)
    scrap_cost: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class ProductionBatchResponse(ProductionBatchBase):
    """Schema for production batch response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    produced_quantity: float
    good_quantity: float
    scrap_quantity: float
    average_speed: Optional[float] = None
    availability: Optional[float] = None
    performance: Optional[float] = None
    quality: Optional[float] = None
    oee: Optional[float] = None
    planned_downtime_minutes: float
    unplanned_downtime_minutes: float
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    scrap_cost: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    scrap_rate: float
    yield_rate: float
    duration_minutes: Optional[float] = None
    
    model_config = {"from_attributes": True}


# Line Event Schemas

class LineEventBase(BaseModel):
    """Base schema for line event."""
    
    line_id: uuid.UUID
    batch_id: Optional[uuid.UUID] = None
    event_type: str = Field(..., min_length=1, max_length=50)
    event_time: datetime
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    downtime_reason: Optional[str] = None
    downtime_duration_minutes: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None
    operator_id: Optional[uuid.UUID] = None
    operator_name: Optional[str] = None


class LineEventCreate(LineEventBase):
    """Schema for creating a line event."""
    pass


class LineEventResponse(LineEventBase):
    """Schema for line event response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Scrap Event Schemas

class ScrapEventBase(BaseModel):
    """Base schema for scrap event."""
    
    batch_id: uuid.UUID
    event_time: datetime
    quantity: float = Field(..., gt=0)
    scrap_type: str = Field(..., min_length=1, max_length=100)
    scrap_reason: Optional[str] = None
    severity: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    estimated_cost: Optional[float] = Field(None, ge=0)
    detected_by: Optional[str] = None
    operator_id: Optional[uuid.UUID] = None
    operator_name: Optional[str] = None
    image_url: Optional[str] = None


class ScrapEventCreate(ScrapEventBase):
    """Schema for creating a scrap event."""
    pass


class ScrapEventResponse(ScrapEventBase):
    """Schema for scrap event response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Sensor Schemas

class SensorBase(BaseModel):
    """Base schema for sensor."""
    
    line_id: uuid.UUID
    sensor_code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    sensor_type: str = Field(..., min_length=1, max_length=100)
    location: Optional[str] = None
    position: Optional[str] = None
    unit_of_measure: str = Field(..., min_length=1, max_length=50)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    target_value: Optional[float] = None
    tolerance: Optional[float] = Field(None, gt=0)


class SensorCreate(SensorBase):
    """Schema for creating a sensor."""
    pass


class SensorUpdate(BaseModel):
    """Schema for updating a sensor."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = None
    position: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    target_value: Optional[float] = None
    tolerance: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None
    last_calibration_date: Optional[datetime] = None
    next_calibration_date: Optional[datetime] = None
    calibration_offset: Optional[float] = None


class SensorResponse(SensorBase):
    """Schema for sensor response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    last_reading_time: Optional[datetime] = None
    last_reading_value: Optional[float] = None
    last_calibration_date: Optional[datetime] = None
    next_calibration_date: Optional[datetime] = None
    calibration_offset: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Sensor Reading Schemas

class SensorReadingBase(BaseModel):
    """Base schema for sensor reading."""
    
    sensor_id: uuid.UUID
    batch_id: Optional[uuid.UUID] = None
    timestamp: datetime
    value: float
    is_valid: bool = True
    is_anomaly: bool = False


class SensorReadingCreate(SensorReadingBase):
    """Schema for creating a sensor reading."""
    pass


class SensorReadingBulkCreate(BaseModel):
    """Schema for bulk creating sensor readings."""
    
    readings: list[SensorReadingCreate] = Field(..., min_length=1, max_length=1000)


class SensorReadingResponse(SensorReadingBase):
    """Schema for sensor reading response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    
    model_config = {"from_attributes": True}


# Analytics and Metrics Schemas

class LineMetrics(BaseModel):
    """Schema for line performance metrics."""
    
    line_id: uuid.UUID
    line_number: str
    period_start: datetime
    period_end: datetime
    total_batches: int
    total_produced: float
    total_good: float
    total_scrap: float
    average_oee: float
    average_availability: float
    average_performance: float
    average_quality: float
    total_downtime_minutes: float
    scrap_rate: float
    yield_rate: float


class BatchMetrics(BaseModel):
    """Schema for batch performance metrics."""
    
    batch_id: uuid.UUID
    batch_number: str
    line_number: str
    product_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    target_quantity: float
    produced_quantity: float
    good_quantity: float
    scrap_quantity: float
    scrap_rate: float
    yield_rate: float
    oee: Optional[float] = None
    total_cost: Optional[float] = None


class ScrapAnalysis(BaseModel):
    """Schema for scrap analysis."""
    
    period_start: datetime
    period_end: datetime
    total_scrap_quantity: float
    total_scrap_cost: float
    scrap_by_type: dict[str, float]
    scrap_by_line: dict[str, float]
    top_reasons: list[dict[str, any]]
    trend: list[dict[str, any]]


class RealTimeMetrics(BaseModel):
    """Schema for real-time dashboard metrics."""
    
    line_id: uuid.UUID
    line_number: str
    status: str
    current_batch_id: Optional[uuid.UUID] = None
    current_batch_number: Optional[str] = None
    current_speed: Optional[float] = None
    target_speed: Optional[float] = None
    produced_today: float
    scrap_today: float
    scrap_rate_today: float
    current_oee: Optional[float] = None
    last_updated: datetime


# Pagination

class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=1000)


class PaginatedResponse(BaseModel):
    """Generic schema for paginated responses."""
    
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
    
    @field_validator("total_pages", mode="before")
    @classmethod
    def calculate_total_pages(cls, v, info):
        """Calculate total pages from total and page_size."""
        if "total" in info.data and "page_size" in info.data:
            import math
            return math.ceil(info.data["total"] / info.data["page_size"])
        return v
