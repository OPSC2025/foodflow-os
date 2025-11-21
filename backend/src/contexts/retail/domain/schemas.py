"""
Retail Pydantic schemas.

Request/response models for API validation and serialization.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Banner Schemas
# ============================================================================

class BannerBase(BaseModel):
    """Base schema for Banner."""

    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    parent_company: Optional[str] = Field(None, max_length=255)


class BannerCreate(BannerBase):
    """Schema for creating a banner."""

    pass


class BannerUpdate(BaseModel):
    """Schema for updating a banner."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    parent_company: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class BannerResponse(BannerBase):
    """Schema for banner response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Store Schemas
# ============================================================================

class StoreBase(BaseModel):
    """Base schema for Store."""

    banner_id: uuid.UUID
    store_number: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    store_format: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    square_footage: Optional[int] = None
    opening_date: Optional[datetime] = None
    phone: Optional[str] = Field(None, max_length=50)
    manager_name: Optional[str] = Field(None, max_length=255)
    manager_email: Optional[str] = Field(None, max_length=255)


class StoreCreate(StoreBase):
    """Schema for creating a store."""

    pass


class StoreUpdate(BaseModel):
    """Schema for updating a store."""

    name: Optional[str] = Field(None, max_length=255)
    store_format: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=50)
    manager_name: Optional[str] = Field(None, max_length=255)
    manager_email: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    """Schema for store response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Category Schemas
# ============================================================================

class CategoryBase(BaseModel):
    """Base schema for Category."""

    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    parent_category_id: Optional[uuid.UUID] = None


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    parent_category_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# POS Transaction Schemas
# ============================================================================

class POSTransactionBase(BaseModel):
    """Base schema for POSTransaction."""

    store_id: uuid.UUID
    transaction_id: str = Field(..., max_length=100)
    transaction_date: datetime
    sku_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    upc: Optional[str] = Field(None, max_length=50)
    external_sku_id: Optional[str] = Field(None, max_length=100)
    product_name: Optional[str] = Field(None, max_length=255)
    quantity_sold: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    total_amount: float = Field(..., gt=0)
    discount_amount: Optional[float] = Field(None, ge=0)
    net_amount: float = Field(..., gt=0)
    promo_id: Optional[uuid.UUID] = None
    metadata: Optional[dict[str, Any]] = None


class POSTransactionCreate(POSTransactionBase):
    """Schema for creating a POS transaction."""

    pass


class POSTransactionBulkCreate(BaseModel):
    """Schema for bulk creating POS transactions."""

    transactions: list[POSTransactionCreate] = Field(..., min_length=1)


class POSTransactionResponse(POSTransactionBase):
    """Schema for POS transaction response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Waste Schemas
# ============================================================================

class WasteBase(BaseModel):
    """Base schema for Waste."""

    store_id: uuid.UUID
    recorded_date: datetime
    sku_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    product_name: Optional[str] = Field(None, max_length=255)
    quantity_wasted: float = Field(..., gt=0)
    unit: str = Field(default="units", max_length=50)
    estimated_value: Optional[float] = Field(None, ge=0)
    reason: str = Field(..., max_length=50)
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    recorded_by: Optional[str] = Field(None, max_length=255)


class WasteCreate(WasteBase):
    """Schema for creating a waste record."""

    pass


class WasteUpdate(BaseModel):
    """Schema for updating a waste record."""

    quantity_wasted: Optional[float] = Field(None, gt=0)
    estimated_value: Optional[float] = Field(None, ge=0)
    reason: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class WasteResponse(WasteBase):
    """Schema for waste response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# OSA Event Schemas
# ============================================================================

class OSAEventBase(BaseModel):
    """Base schema for OSAEvent."""

    store_id: uuid.UUID
    detected_date: datetime
    sku_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    product_name: Optional[str] = Field(None, max_length=255)
    osa_status: str = Field(..., max_length=50)
    issue_type: str = Field(..., max_length=50)
    on_hand_quantity: Optional[int] = Field(None, ge=0)
    backroom_quantity: Optional[int] = Field(None, ge=0)
    shelf_capacity: Optional[int] = Field(None, ge=0)
    estimated_lost_sales: Optional[float] = Field(None, ge=0)
    duration_hours: Optional[float] = Field(None, ge=0)
    detected_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class OSAEventCreate(OSAEventBase):
    """Schema for creating an OSA event."""

    pass


class OSAEventUpdate(BaseModel):
    """Schema for updating an OSA event."""

    resolved: Optional[bool] = None
    resolved_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    estimated_lost_sales: Optional[float] = Field(None, ge=0)
    duration_hours: Optional[float] = Field(None, ge=0)


class OSAEventResponse(OSAEventBase):
    """Schema for OSA event response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    resolved: bool
    resolved_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Promo Schemas
# ============================================================================

class PromoBase(BaseModel):
    """Base schema for Promo."""

    promo_name: str = Field(..., max_length=255)
    promo_code: str = Field(..., max_length=50)
    description: Optional[str] = None
    promo_type: str = Field(..., max_length=50)
    start_date: datetime
    end_date: datetime
    banner_ids: Optional[list[str]] = None
    store_ids: Optional[list[str]] = None
    product_ids: Optional[list[str]] = None
    sku_ids: Optional[list[str]] = None
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    discount_amount: Optional[float] = Field(None, ge=0)
    promo_mechanics: Optional[dict[str, Any]] = None
    budget: Optional[float] = Field(None, ge=0)
    target_units: Optional[int] = Field(None, ge=0)
    target_revenue: Optional[float] = Field(None, ge=0)
    suggested_by_ai: bool = Field(default=False)
    ai_confidence: Optional[float] = Field(None, ge=0, le=1)


class PromoCreate(PromoBase):
    """Schema for creating a promo."""

    pass


class PromoUpdate(BaseModel):
    """Schema for updating a promo."""

    promo_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    end_date: Optional[datetime] = None
    discount_percentage: Optional[float] = Field(None, ge=0, le=100)
    discount_amount: Optional[float] = Field(None, ge=0)
    budget: Optional[float] = Field(None, ge=0)
    target_units: Optional[int] = Field(None, ge=0)
    target_revenue: Optional[float] = Field(None, ge=0)
    actual_units_sold: Optional[int] = Field(None, ge=0)
    actual_revenue: Optional[float] = Field(None, ge=0)
    actual_discount_given: Optional[float] = Field(None, ge=0)
    roi: Optional[float] = None
    status: Optional[str] = None


class PromoResponse(PromoBase):
    """Schema for promo response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    actual_units_sold: Optional[int] = None
    actual_revenue: Optional[float] = None
    actual_discount_given: Optional[float] = None
    roi: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Analytics Schemas
# ============================================================================

class WasteSummaryResponse(BaseModel):
    """Waste summary analytics."""

    store_id: Optional[uuid.UUID]
    period_start: datetime
    period_end: datetime
    total_waste_quantity: float
    total_waste_value: float
    waste_by_reason: dict[str, float]
    top_wasted_products: list[dict[str, Any]]


class OSASummaryResponse(BaseModel):
    """OSA summary analytics."""

    store_id: Optional[uuid.UUID]
    period_start: datetime
    period_end: datetime
    total_osa_events: int
    resolved_events: int
    unresolved_events: int
    avg_resolution_time_hours: Optional[float]
    total_estimated_lost_sales: Optional[float]
    events_by_type: dict[str, int]


class PromoPerformanceResponse(BaseModel):
    """Promo performance analytics."""

    promo_id: uuid.UUID
    promo_name: str
    promo_type: str
    start_date: datetime
    end_date: datetime
    target_units: Optional[int]
    actual_units_sold: Optional[int]
    attainment_pct: Optional[float]
    roi: Optional[float]
    total_discount_given: Optional[float]
    lift_pct: Optional[float]  # Sales lift vs baseline


class StorePerformanceResponse(BaseModel):
    """Store performance summary."""

    store_id: uuid.UUID
    store_name: str
    period_start: datetime
    period_end: datetime
    total_sales: float
    total_transactions: int
    avg_basket_size: Optional[float]
    waste_rate: Optional[float]
    osa_compliance: Optional[float]  # % of time in stock

