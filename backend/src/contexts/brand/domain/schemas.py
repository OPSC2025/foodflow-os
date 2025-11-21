"""
Brand & Co-packer Pydantic schemas.

Request/response models for API validation and serialization.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Brand Schemas
# ============================================================================

class BrandBase(BaseModel):
    """Base schema for Brand."""

    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    company_name: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    target_market: Optional[str] = Field(None, max_length=255)
    channels: Optional[list[str]] = None


class BrandCreate(BrandBase):
    """Schema for creating a brand."""

    pass


class BrandUpdate(BaseModel):
    """Schema for updating a brand."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    company_name: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    target_market: Optional[str] = Field(None, max_length=255)
    channels: Optional[list[str]] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class BrandResponse(BrandBase):
    """Schema for brand response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Product Schemas
# ============================================================================

class ProductBase(BaseModel):
    """Base schema for Product."""

    brand_id: uuid.UUID
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    attributes: Optional[dict[str, Any]] = None
    allergens: Optional[list[str]] = None
    launch_date: Optional[datetime] = None


class ProductCreate(ProductBase):
    """Schema for creating a product."""

    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    attributes: Optional[dict[str, Any]] = None
    allergens: Optional[list[str]] = None
    status: Optional[str] = None
    discontinuation_date: Optional[datetime] = None


class ProductResponse(ProductBase):
    """Schema for product response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    discontinuation_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# SKU Schemas
# ============================================================================

class SKUBase(BaseModel):
    """Base schema for SKU."""

    product_id: uuid.UUID
    sku_code: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    variant_attributes: Optional[dict[str, Any]] = None
    package_size: Optional[float] = None
    package_unit: Optional[str] = Field(None, max_length=50)
    units_per_case: Optional[int] = None
    suggested_retail_price: Optional[float] = None
    wholesale_price: Optional[float] = None
    cost_per_unit: Optional[float] = None
    upc: Optional[str] = Field(None, max_length=50)
    gtin: Optional[str] = Field(None, max_length=50)


class SKUCreate(SKUBase):
    """Schema for creating a SKU."""

    pass


class SKUUpdate(BaseModel):
    """Schema for updating a SKU."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    variant_attributes: Optional[dict[str, Any]] = None
    package_size: Optional[float] = None
    package_unit: Optional[str] = Field(None, max_length=50)
    units_per_case: Optional[int] = None
    suggested_retail_price: Optional[float] = None
    wholesale_price: Optional[float] = None
    cost_per_unit: Optional[float] = None
    upc: Optional[str] = Field(None, max_length=50)
    gtin: Optional[str] = Field(None, max_length=50)
    status: Optional[str] = None
    is_active: Optional[bool] = None


class SKUResponse(SKUBase):
    """Schema for SKU response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Copacker Schemas
# ============================================================================

class CopackerBase(BaseModel):
    """Base schema for Copacker."""

    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    capabilities: Optional[list[str]] = None
    certifications: Optional[dict[str, Any]] = None


class CopackerCreate(CopackerBase):
    """Schema for creating a co-packer."""

    pass


class CopackerUpdate(BaseModel):
    """Schema for updating a co-packer."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    capabilities: Optional[list[str]] = None
    certifications: Optional[dict[str, Any]] = None
    performance_score: Optional[float] = Field(None, ge=0, le=100)
    on_time_delivery_rate: Optional[float] = Field(None, ge=0, le=1)
    quality_rating: Optional[float] = Field(None, ge=0, le=5)
    status: Optional[str] = None
    is_active: Optional[bool] = None


class CopackerResponse(CopackerBase):
    """Schema for co-packer response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    performance_score: Optional[float] = None
    on_time_delivery_rate: Optional[float] = None
    quality_rating: Optional[float] = None
    status: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Copacker Contract Schemas
# ============================================================================

class CopackerContractBase(BaseModel):
    """Base schema for CopackerContract."""

    brand_id: uuid.UUID
    copacker_id: uuid.UUID
    product_ids: Optional[list[str]] = None
    contract_number: str = Field(..., max_length=100)
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    renewal_terms: Optional[str] = None
    pricing_model: Optional[str] = Field(None, max_length=100)
    pricing_details: Optional[dict[str, Any]] = None
    slas: Optional[dict[str, Any]] = None
    document_id: Optional[uuid.UUID] = None


class CopackerContractCreate(CopackerContractBase):
    """Schema for creating a co-packer contract."""

    pass


class CopackerContractUpdate(BaseModel):
    """Schema for updating a co-packer contract."""

    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    end_date: Optional[datetime] = None
    renewal_terms: Optional[str] = None
    pricing_model: Optional[str] = Field(None, max_length=100)
    pricing_details: Optional[dict[str, Any]] = None
    slas: Optional[dict[str, Any]] = None
    document_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class CopackerContractResponse(CopackerContractBase):
    """Schema for co-packer contract response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Brand Performance Schemas
# ============================================================================

class BrandPerformanceBase(BaseModel):
    """Base schema for BrandPerformance."""

    brand_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    sku_id: Optional[uuid.UUID] = None
    period_start: datetime
    period_end: datetime
    period_type: str = Field(..., max_length=50)
    units_sold: Optional[int] = None
    gross_revenue: Optional[float] = None
    net_revenue: Optional[float] = None
    cost_of_goods_sold: Optional[float] = None
    gross_margin: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    additional_metrics: Optional[dict[str, Any]] = None


class BrandPerformanceCreate(BrandPerformanceBase):
    """Schema for creating brand performance record."""

    pass


class BrandPerformanceUpdate(BaseModel):
    """Schema for updating brand performance record."""

    units_sold: Optional[int] = None
    gross_revenue: Optional[float] = None
    net_revenue: Optional[float] = None
    cost_of_goods_sold: Optional[float] = None
    gross_margin: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    additional_metrics: Optional[dict[str, Any]] = None


class BrandPerformanceResponse(BrandPerformanceBase):
    """Schema for brand performance response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Brand Document Schemas (RAG-ready)
# ============================================================================

class BrandDocumentBase(BaseModel):
    """Base schema for BrandDocument."""

    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    document_type: str = Field(..., max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    brand_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    copacker_id: Optional[uuid.UUID] = None
    file_path: str = Field(..., max_length=500)
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)
    content_hash: Optional[str] = Field(None, max_length=64)
    version: str = Field(default="1.0", max_length=50)
    uploaded_by: str = Field(..., max_length=255)
    uploaded_at: datetime
    expiry_date: Optional[datetime] = None
    tags: Optional[list[str]] = None


class BrandDocumentCreate(BrandDocumentBase):
    """Schema for creating a brand document."""

    pass


class BrandDocumentUpdate(BaseModel):
    """Schema for updating a brand document."""

    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None
    tags: Optional[list[str]] = None
    is_active: Optional[bool] = None


class BrandDocumentResponse(BrandDocumentBase):
    """Schema for brand document response."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    is_latest_version: bool
    parent_document_id: Optional[uuid.UUID] = None
    is_indexed: bool
    indexed_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# Analytics Schemas
# ============================================================================

class MarginBridgeRequest(BaseModel):
    """Request schema for margin bridge analysis."""

    product_id: Optional[uuid.UUID] = None
    sku_id: Optional[uuid.UUID] = None
    period_start: datetime
    period_end: datetime


class MarginBridgeResponse(BaseModel):
    """Response schema for margin bridge analysis."""

    product_id: Optional[uuid.UUID]
    sku_id: Optional[uuid.UUID]
    period_start: datetime
    period_end: datetime
    gross_margin_start: float
    gross_margin_end: float
    margin_change: float
    margin_change_pct: float
    drivers: dict[str, Any]  # AI-generated margin drivers
    recommendations: list[str]  # AI-generated recommendations


class CopackerPerformanceResponse(BaseModel):
    """Response schema for co-packer performance."""

    copacker_id: uuid.UUID
    copacker_name: str
    period_start: datetime
    period_end: datetime
    performance_score: float
    on_time_delivery_rate: float
    quality_rating: float
    total_orders: int
    defect_rate: Optional[float] = None
    average_lead_time_days: Optional[float] = None
    issues_summary: Optional[dict[str, Any]] = None

