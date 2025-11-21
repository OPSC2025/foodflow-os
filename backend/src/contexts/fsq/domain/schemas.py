"""
FSQ context Pydantic schemas for API validation and serialization.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Supplier Schemas

class SupplierBase(BaseModel):
    """Base schema for supplier."""
    
    supplier_code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    certifications: Optional[list[str]] = None


class SupplierCreate(SupplierBase):
    """Schema for creating a supplier."""
    pass


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None
    is_approved: Optional[bool] = None
    certifications: Optional[list[str]] = None
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class SupplierResponse(SupplierBase):
    """Schema for supplier response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    is_approved: bool
    approval_date: Optional[datetime] = None
    risk_score: Optional[float] = None
    last_audit_date: Optional[datetime] = None
    next_audit_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Ingredient Schemas

class IngredientBase(BaseModel):
    """Base schema for ingredient."""
    
    ingredient_code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    allergens: Optional[list[str]] = None
    supplier_id: Optional[uuid.UUID] = None
    specification: Optional[dict] = None


class IngredientCreate(IngredientBase):
    """Schema for creating an ingredient."""
    pass


class IngredientUpdate(BaseModel):
    """Schema for updating an ingredient."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    allergens: Optional[list[str]] = None
    supplier_id: Optional[uuid.UUID] = None
    specification: Optional[dict] = None
    is_active: Optional[bool] = None
    requires_lot_tracking: Optional[bool] = None
    notes: Optional[str] = None


class IngredientResponse(IngredientBase):
    """Schema for ingredient response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    requires_lot_tracking: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Lot Schemas

class LotBase(BaseModel):
    """Base schema for lot."""
    
    lot_number: str = Field(..., min_length=1, max_length=100)
    ingredient_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    supplier_id: Optional[uuid.UUID] = None
    production_batch_id: Optional[uuid.UUID] = None
    received_date: Optional[datetime] = None
    manufactured_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    quantity: float = Field(..., gt=0)
    unit_of_measure: str = Field(..., min_length=1, max_length=50)


class LotCreate(LotBase):
    """Schema for creating a lot."""
    quantity_remaining: Optional[float] = None  # Defaults to quantity if not provided


class LotUpdate(BaseModel):
    """Schema for updating a lot."""
    
    status: Optional[str] = None
    quantity_remaining: Optional[float] = Field(None, ge=0)
    test_results: Optional[dict] = None
    quality_score: Optional[float] = Field(None, ge=0, le=100)
    parent_lots: Optional[list[str]] = None
    child_lots: Optional[list[str]] = None
    is_on_hold: Optional[bool] = None
    hold_reason: Optional[str] = None
    released_by: Optional[str] = None
    notes: Optional[str] = None


class LotResponse(LotBase):
    """Schema for lot response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    quantity_remaining: float
    status: str
    test_results: Optional[dict] = None
    quality_score: Optional[float] = None
    parent_lots: Optional[list[str]] = None
    child_lots: Optional[list[str]] = None
    is_on_hold: bool
    hold_reason: Optional[str] = None
    hold_date: Optional[datetime] = None
    released_date: Optional[datetime] = None
    released_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class LotTraceResult(BaseModel):
    """Schema for lot trace results (forward or backward)."""
    
    direction: str  # "forward" or "backward"
    origin_lot_id: uuid.UUID
    origin_lot_number: str
    traced_lots: list[LotResponse]
    trace_depth: int
    total_lots: int


# Deviation Schemas

class DeviationBase(BaseModel):
    """Base schema for deviation."""
    
    deviation_number: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    severity: str = Field(..., min_length=1, max_length=50)
    lot_id: Optional[uuid.UUID] = None
    production_batch_id: Optional[uuid.UUID] = None
    product_id: Optional[uuid.UUID] = None
    occurred_at: datetime
    location: Optional[str] = None
    reported_by: str = Field(..., min_length=1, max_length=255)


class DeviationCreate(DeviationBase):
    """Schema for creating a deviation."""
    pass


class DeviationUpdate(BaseModel):
    """Schema for updating a deviation."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    root_cause: Optional[str] = None
    investigation_notes: Optional[str] = None
    immediate_action: Optional[str] = None
    requires_capa: Optional[bool] = None
    capa_id: Optional[uuid.UUID] = None
    investigated_by: Optional[str] = None
    closed_by: Optional[str] = None
    affected_quantity: Optional[float] = Field(None, ge=0)
    financial_impact: Optional[float] = Field(None, ge=0)


class DeviationResponse(DeviationBase):
    """Schema for deviation response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    root_cause: Optional[str] = None
    investigation_notes: Optional[str] = None
    immediate_action: Optional[str] = None
    requires_capa: bool
    capa_id: Optional[uuid.UUID] = None
    investigated_by: Optional[str] = None
    closed_by: Optional[str] = None
    closed_at: Optional[datetime] = None
    affected_quantity: Optional[float] = None
    financial_impact: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# CAPA Schemas

class CAPABase(BaseModel):
    """Base schema for CAPA."""
    
    capa_number: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    root_cause: str = Field(..., min_length=1)
    is_corrective: bool = True
    is_preventive: bool = False
    owner: str = Field(..., min_length=1, max_length=255)
    created_by: str = Field(..., min_length=1, max_length=255)
    target_completion_date: Optional[datetime] = None


class CAPACreate(CAPABase):
    """Schema for creating a CAPA."""
    pass


class CAPAUpdate(BaseModel):
    """Schema for updating a CAPA."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    root_cause: Optional[str] = None
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    status: Optional[str] = None
    target_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    verification_method: Optional[str] = None
    verification_date: Optional[datetime] = None
    verified_by: Optional[str] = None
    is_effective: Optional[bool] = None
    notes: Optional[str] = None


class CAPAResponse(CAPABase):
    """Schema for CAPA response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    corrective_action: Optional[str] = None
    preventive_action: Optional[str] = None
    status: str
    actual_completion_date: Optional[datetime] = None
    verification_method: Optional[str] = None
    verification_date: Optional[datetime] = None
    verified_by: Optional[str] = None
    is_effective: Optional[bool] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# HACCP Plan Schemas

class HACCPPlanBase(BaseModel):
    """Base schema for HACCP plan."""
    
    plan_code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    product_id: Optional[uuid.UUID] = None
    product_code: Optional[str] = None
    process_line_id: Optional[uuid.UUID] = None
    hazard_analysis: Optional[dict] = None
    ccps: Optional[list] = None


class HACCPPlanCreate(HACCPPlanBase):
    """Schema for creating a HACCP plan."""
    pass


class HACCPPlanUpdate(BaseModel):
    """Schema for updating a HACCP plan."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    hazard_analysis: Optional[dict] = None
    ccps: Optional[list] = None
    is_active: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    notes: Optional[str] = None


class HACCPPlanResponse(HACCPPlanBase):
    """Schema for HACCP plan response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# CCP Log Schemas

class CCPLogBase(BaseModel):
    """Base schema for CCP log."""
    
    haccp_plan_id: uuid.UUID
    ccp_code: str = Field(..., min_length=1, max_length=100)
    ccp_name: str = Field(..., min_length=1, max_length=255)
    log_time: datetime
    production_batch_id: Optional[uuid.UUID] = None
    line_id: Optional[uuid.UUID] = None
    measurement_value: float
    unit_of_measure: str = Field(..., min_length=1, max_length=50)
    critical_limit_min: Optional[float] = None
    critical_limit_max: Optional[float] = None
    is_within_limits: bool
    recorded_by: str = Field(..., min_length=1, max_length=255)


class CCPLogCreate(CCPLogBase):
    """Schema for creating a CCP log."""
    pass


class CCPLogUpdate(BaseModel):
    """Schema for updating a CCP log."""
    
    is_deviation: Optional[bool] = None
    corrective_action_taken: Optional[str] = None
    verified_by: Optional[str] = None
    notes: Optional[str] = None


class CCPLogResponse(CCPLogBase):
    """Schema for CCP log response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_deviation: bool
    corrective_action_taken: Optional[str] = None
    verified_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Document Schemas

class DocumentBase(BaseModel):
    """Base schema for document."""
    
    document_number: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: str = Field(..., min_length=1, max_length=50)
    category: Optional[str] = None
    file_name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(default="1.0", max_length=50)
    tags: Optional[list[str]] = None


class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    
    file_path: str = Field(..., min_length=1, max_length=500)
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    content_hash: Optional[str] = None
    uploaded_by: str = Field(..., min_length=1, max_length=255)


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    is_confidential: Optional[bool] = None
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    review_frequency_days: Optional[int] = Field(None, gt=0)
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    tags: Optional[list[str]] = None
    notes: Optional[str] = None


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    content_hash: Optional[str] = None
    is_latest_version: bool
    replaces_document_id: Optional[uuid.UUID] = None
    is_active: bool
    is_confidential: bool
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    review_frequency_days: Optional[int] = None
    last_review_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    embedding_model: Optional[str] = None
    chunk_count: Optional[int] = None
    uploaded_by: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class DocumentUploadRequest(BaseModel):
    """Schema for document upload request."""
    
    document_number: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    document_type: str = Field(..., min_length=1, max_length=50)
    category: Optional[str] = None
    version: str = Field(default="1.0", max_length=50)
    tags: Optional[list[str]] = None
    # File will be uploaded separately via multipart/form-data


# Analytics Schemas

class DeviationSummary(BaseModel):
    """Schema for deviation summary analytics."""
    
    category: str
    total_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    open_count: int
    closed_count: int
    avg_resolution_days: Optional[float] = None


class CAPASummary(BaseModel):
    """Schema for CAPA summary analytics."""
    
    status: str
    count: int
    avg_completion_days: Optional[float] = None
    effectiveness_rate: Optional[float] = None


class FSQOverview(BaseModel):
    """Schema for FSQ workspace overview."""
    
    period_start: datetime
    period_end: datetime
    total_lots: int
    lots_on_hold: int
    active_deviations: int
    open_capas: int
    ccp_violations_count: int
    supplier_risk_avg: float
    recent_deviations: list[DeviationResponse]
    upcoming_document_reviews: int

