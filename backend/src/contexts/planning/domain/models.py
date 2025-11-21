"""
Planning & Supply domain models.

Core models for demand forecasting, production planning, and inventory management.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


# Enums
class ForecastStatus(str, enum.Enum):
    """Status of a forecast."""

    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ForecastMethod(str, enum.Enum):
    """Method used to generate forecast."""

    AI_ML = "ai_ml"  # LLM/ML generated
    STATISTICAL = "statistical"  # Time series analysis
    MANUAL = "manual"  # User-entered
    HYBRID = "hybrid"  # Combination


class ProductionPlanStatus(str, enum.Enum):
    """Status of a production plan."""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SafetyStockPolicy(str, enum.Enum):
    """Safety stock calculation policy."""

    FIXED_QUANTITY = "fixed_quantity"
    FIXED_DAYS = "fixed_days"
    SERVICE_LEVEL = "service_level"
    AI_OPTIMIZED = "ai_optimized"


# Models
class Forecast(Base):
    """
    Demand forecast for a product or SKU.
    
    Supports versioning and AI-generated forecasts.
    """

    __tablename__ = "forecasts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Forecast metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "v1.0", "2024-Q1"

    # What is being forecasted
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # FK to products (from Brand context)
    sku_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # FK to SKUs (from Brand context)

    # Time period
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Forecast method
    method: Mapped[str] = mapped_column(String(50), nullable=False, default=ForecastMethod.AI_ML)

    # Forecast data (flexible JSONB for weekly/monthly/daily data)
    # Example: {"periods": [{"date": "2024-01-01", "quantity": 1000, "confidence": 0.85}, ...]}
    forecast_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Accuracy metrics (if comparing to actuals)
    # Example: {"mape": 12.5, "mae": 150.3, "rmse": 200.1}
    accuracy_metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ForecastStatus.DRAFT)

    # AI metadata
    generated_by_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_model_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_suggestion_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # FK to ai_suggestions

    # Versioning (link to previous forecast)
    parent_forecast_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("forecasts.id", ondelete="SET NULL"), nullable=True
    )

    # Ownership
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    child_forecasts: Mapped[list["Forecast"]] = relationship(
        "Forecast", back_populates="parent_forecast", remote_side=[parent_forecast_id]
    )
    parent_forecast: Mapped[Optional["Forecast"]] = relationship(
        "Forecast", back_populates="child_forecasts", remote_side=[id]
    )


class ProductionPlan(Base):
    """
    Production plan for manufacturing.
    
    Links forecasts to production schedules and capacity.
    """

    __tablename__ = "production_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Plan metadata
    plan_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Planning period
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Linked forecast
    forecast_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("forecasts.id", ondelete="SET NULL"), nullable=True
    )

    # Production lines included
    line_ids: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)  # List of line UUIDs

    # Plan details (flexible JSONB for weekly/daily schedules)
    # Example: {"schedules": [{"date": "2024-01-01", "line_id": "...", "product_id": "...", "quantity": 500}, ...]}
    plan_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Capacity analysis
    # Example: {"total_capacity": 10000, "planned_utilization": 8500, "utilization_pct": 85}
    capacity_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Constraints & conflicts
    # Example: {"constraints": ["line-1-downtime-2024-01-05"], "conflicts": []}
    constraints: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ProductionPlanStatus.DRAFT, index=True
    )

    # AI metadata
    generated_by_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_optimizations: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # AI suggestions for the plan

    # Ownership & approval
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Execution tracking
    execution_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    execution_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    forecast: Mapped[Optional["Forecast"]] = relationship("Forecast", foreign_keys=[forecast_id])


class SafetyStock(Base):
    """
    Safety stock recommendations for products/SKUs.
    
    Can be calculated using various policies including AI optimization.
    """

    __tablename__ = "safety_stocks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # What product/SKU
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    sku_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    ingredient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # Safety stock for raw materials

    # Location (optional)
    plant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    warehouse_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Safety stock calculation
    policy: Mapped[str] = mapped_column(
        String(50), nullable=False, default=SafetyStockPolicy.SERVICE_LEVEL
    )
    
    # Calculated safety stock
    safety_stock_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="units")

    # Service level (if using service level policy)
    target_service_level: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # e.g., 0.95 for 95%

    # Lead times
    lead_time_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Demand variability
    demand_std_dev: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    demand_mean: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Reorder point
    reorder_point: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Calculation metadata
    # Example: {"z_score": 1.65, "demand_during_lead_time": 500, "variability_factor": 1.2}
    calculation_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # AI metadata
    calculated_by_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_reviewed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )


class InventoryLevel(Base):
    """
    Current inventory levels for products, SKUs, or ingredients.
    
    Tracks real-time inventory for planning purposes.
    """

    __tablename__ = "inventory_levels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # What item
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    sku_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    ingredient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Location
    plant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    warehouse_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Inventory quantities
    on_hand_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    available_quantity: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )  # On-hand - allocated
    allocated_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    in_transit_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="units")

    # Stock status
    is_below_safety_stock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_stockout: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    days_of_supply: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Last movement
    last_movement_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # receipt, consumption, adjustment
    last_movement_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_movement_quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    as_of_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )  # Snapshot date
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

