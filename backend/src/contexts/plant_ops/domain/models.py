"""
PlantOps context domain models.

Handles production batches, lines, equipment, sensors, and operational metrics.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


class LineStatus(str, Enum):
    """Production line status enum."""
    
    IDLE = "idle"
    RUNNING = "running"
    CHANGEOVER = "changeover"
    DOWNTIME = "downtime"
    MAINTENANCE = "maintenance"


class BatchStatus(str, Enum):
    """Production batch status enum."""
    
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class DowntimeReason(str, Enum):
    """Downtime reason categories."""
    
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    CHANGEOVER = "changeover"
    NO_MATERIAL = "no_material"
    NO_OPERATOR = "no_operator"
    QUALITY_ISSUE = "quality_issue"
    PLANNED_MAINTENANCE = "planned_maintenance"
    OTHER = "other"


class ProductionLine(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    Production line model representing a manufacturing line.
    
    A line is a physical production line with equipment, sensors, and operators.
    """
    
    __tablename__ = "production_lines"
    
    # Line identification
    line_number: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Location
    plant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    plant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Line specifications
    design_speed: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)  # units per minute
    max_speed: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    min_speed: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)    
    
    # Current status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=LineStatus.IDLE, index=True)
    current_speed: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    current_batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    
    # Operational data
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_maintenance_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_maintenance_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON stored as text
    
    # Relationships
    batches = relationship("ProductionBatch", back_populates="line", foreign_keys="ProductionBatch.line_id")
    events = relationship("LineEvent", back_populates="line", cascade="all, delete-orphan")
    sensors = relationship("Sensor", back_populates="line", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_production_lines_tenant_line_number", "tenant_id", "line_number", unique=True),
        Index("ix_production_lines_status", "tenant_id", "status"),
    )
    
    def __repr__(self) -> str:
        return f"<ProductionLine(id={self.id}, line_number='{self.line_number}', status='{self.status}')>"


class ProductionBatch(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    Production batch model representing a batch of products.
    
    A batch is a specific production run of a product on a line.
    """
    
    __tablename__ = "production_batches"
    
    # Batch identification
    batch_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    work_order_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Product information
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Line assignment
    line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_lines.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    # Batch status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=BatchStatus.PLANNED, index=True)
    
    # Timing
    planned_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    actual_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Quantities
    target_quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    produced_quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    good_quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    scrap_quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    
    # Performance metrics
    target_speed: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)  # units per minute
    average_speed: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # OEE components
    availability: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)  # percentage
    performance: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)  # percentage
    quality: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)  # percentage
    oee: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)  # percentage
    
    # Downtime tracking
    planned_downtime_minutes: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    unplanned_downtime_minutes: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    
    # Cost tracking
    labor_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    material_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    scrap_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    
    # Operator information
    operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    operator_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    shift: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Notes and metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON stored as text
    
    # Relationships
    line = relationship("ProductionLine", back_populates="batches", foreign_keys=[line_id])
    scrap_events = relationship("ScrapEvent", back_populates="batch", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_production_batches_tenant_batch_number", "tenant_id", "batch_number", unique=True),
        Index("ix_production_batches_status_start", "tenant_id", "status", "actual_start_time"),
        Index("ix_production_batches_line_status", "line_id", "status"),
    )
    
    @property
    def scrap_rate(self) -> float:
        """Calculate scrap rate as percentage."""
        if float(self.produced_quantity) == 0:
            return 0.0
        return (float(self.scrap_quantity) / float(self.produced_quantity)) * 100
    
    @property
    def yield_rate(self) -> float:
        """Calculate yield rate as percentage."""
        if float(self.produced_quantity) == 0:
            return 0.0
        return (float(self.good_quantity) / float(self.produced_quantity)) * 100
    
    @property
    def duration_minutes(self) -> Optional[float]:
        """Calculate batch duration in minutes."""
        if self.actual_start_time and self.actual_end_time:
            delta = self.actual_end_time - self.actual_start_time
            return delta.total_seconds() / 60
        return None
    
    def __repr__(self) -> str:
        return f"<ProductionBatch(id={self.id}, batch_number='{self.batch_number}', status='{self.status}')>"


class LineEvent(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    Line event model for tracking significant events on production lines.
    
    Events include starts, stops, changeovers, downtime, and state changes.
    """
    
    __tablename__ = "line_events"
    
    # Line reference
    line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Batch reference (optional, may not be associated with a batch)
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Event details
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Event data
    previous_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Downtime tracking
    downtime_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    downtime_duration_minutes: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Additional context
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    operator_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Metadata
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON stored as text
    
    # Relationships
    line = relationship("ProductionLine", back_populates="events")
    
    __table_args__ = (
        Index("ix_line_events_tenant_line_time", "tenant_id", "line_id", "event_time"),
        Index("ix_line_events_type_time", "event_type", "event_time"),
    )
    
    def __repr__(self) -> str:
        return f"<LineEvent(id={self.id}, type='{self.event_type}', time='{self.event_time}')>"


class ScrapEvent(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    Scrap event model for tracking scrap occurrences.
    
    Records when scrap is detected, the reason, and the quantity.
    """
    
    __tablename__ = "scrap_events"
    
    # Batch reference
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Scrap details
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Scrap classification
    scrap_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    scrap_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # low, medium, high, critical
    
    # Root cause analysis
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Cost
    estimated_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    
    # Detection
    detected_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # operator, sensor, AI
    operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    operator_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Image reference (if captured)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Metadata
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON stored as text
    
    # Relationships
    batch = relationship("ProductionBatch", back_populates="scrap_events")
    
    __table_args__ = (
        Index("ix_scrap_events_tenant_batch_time", "tenant_id", "batch_id", "event_time"),
        Index("ix_scrap_events_type_time", "scrap_type", "event_time"),
    )
    
    def __repr__(self) -> str:
        return f"<ScrapEvent(id={self.id}, type='{self.scrap_type}', quantity={self.quantity})>"


class Sensor(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    Sensor model representing a physical sensor on a production line.
    
    Sensors monitor temperature, pressure, speed, weight, etc.
    """
    
    __tablename__ = "sensors"
    
    # Line reference
    line_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_lines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Sensor identification
    sensor_code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sensor_type: Mapped[str] = mapped_column(String(100), nullable=False)  # temperature, pressure, speed, weight, etc.
    
    # Location
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Specifications
    unit_of_measure: Mapped[str] = mapped_column(String(50), nullable=False)
    min_value: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    max_value: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    target_value: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    tolerance: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_reading_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_reading_value: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    
    # Calibration
    last_calibration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_calibration_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    calibration_offset: Mapped[Optional[float]] = mapped_column(Numeric(12, 6), nullable=True)
    
    # Configuration
    settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON stored as text
    
    # Relationships
    line = relationship("ProductionLine", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_sensors_tenant_sensor_code", "tenant_id", "sensor_code", unique=True),
        Index("ix_sensors_line_type", "line_id", "sensor_type"),
    )
    
    def __repr__(self) -> str:
        return f"<Sensor(id={self.id}, code='{self.sensor_code}', type='{self.sensor_type}')>"


class SensorReading(Base, UUIDPrimaryKeyMixin, TenantMixin):
    """
    Sensor reading model for time-series sensor data.
    
    Stores individual sensor readings with timestamps.
    This table will grow large and should be partitioned by time.
    """
    
    __tablename__ = "sensor_readings"
    
    # Sensor reference
    sensor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sensors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Batch reference (optional)
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("production_batches.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Reading data
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    
    # Quality flags
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Metadata
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON stored as text
    
    # Relationships
    sensor = relationship("Sensor", back_populates="readings")
    
    __table_args__ = (
        Index("ix_sensor_readings_tenant_sensor_time", "tenant_id", "sensor_id", "timestamp"),
        Index("ix_sensor_readings_batch_time", "batch_id", "timestamp"),
        # Note: In production, this table should be partitioned by timestamp
        # using PostgreSQL table partitioning or TimescaleDB hypertables
    )
    
    def __repr__(self) -> str:
        return f"<SensorReading(id={self.id}, sensor_id={self.sensor_id}, value={self.value})>"
