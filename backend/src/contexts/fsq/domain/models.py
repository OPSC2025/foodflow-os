"""
FSQ (Food Safety & Quality) context domain models.

Handles lot traceability, deviations, CAPA, HACCP, CCP monitoring,
supplier management, and compliance documentation.
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
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


# Enums

class LotStatus(str, Enum):
    """Lot status enum."""
    
    PENDING = "pending"
    APPROVED = "approved"
    QUARANTINE = "quarantine"
    REJECTED = "rejected"
    RELEASED = "released"
    CONSUMED = "consumed"


class DeviationSeverity(str, Enum):
    """Deviation severity levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DeviationStatus(str, Enum):
    """Deviation status enum."""
    
    OPEN = "open"
    INVESTIGATING = "investigating"
    CAPA_REQUIRED = "capa_required"
    RESOLVED = "resolved"
    CLOSED = "closed"


class CAPAStatus(str, Enum):
    """CAPA status enum."""
    
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DocumentType(str, Enum):
    """FSQ document types."""
    
    SOP = "sop"  # Standard Operating Procedure
    HACCP_PLAN = "haccp_plan"
    QMS_DOC = "qms_doc"  # Quality Management System
    SQF_DOC = "sqf_doc"  # Safe Quality Food
    AUDIT_REPORT = "audit_report"
    CERTIFICATE = "certificate"
    SPECIFICATION = "specification"
    TEST_REPORT = "test_report"
    TRAINING_MATERIAL = "training_material"
    OTHER = "other"


# Models

class Supplier(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    Supplier model for tracking ingredient and material suppliers.
    """
    
    __tablename__ = "suppliers"
    
    # Supplier identification
    supplier_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Contact information
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Status and certification
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Certifications (stored as JSON array of strings)
    certifications: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    
    # Risk assessment
    risk_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)  # 0-100
    last_audit_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_audit_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    ingredients = relationship("Ingredient", back_populates="supplier")
    lots = relationship("Lot", back_populates="supplier")
    
    __table_args__ = (
        Index("ix_suppliers_tenant_code", "tenant_id", "supplier_code", unique=True),
        Index("ix_suppliers_is_active", "tenant_id", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, code='{self.supplier_code}', name='{self.name}')>"


class Ingredient(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    Ingredient model for tracking raw materials and ingredients.
    """
    
    __tablename__ = "ingredients"
    
    # Ingredient identification
    ingredient_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Classification
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    allergens: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    
    # Supplier
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Specifications
    specification: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # e.g., pH, moisture, protein %
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_lot_tracking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="ingredients")
    lots = relationship("Lot", back_populates="ingredient")
    
    __table_args__ = (
        Index("ix_ingredients_tenant_code", "tenant_id", "ingredient_code", unique=True),
        Index("ix_ingredients_category", "tenant_id", "category"),
    )
    
    def __repr__(self) -> str:
        return f"<Ingredient(id={self.id}, code='{self.ingredient_code}', name='{self.name}')>"


class Lot(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    Lot model for tracking lots/batches of ingredients and finished products.
    
    Critical for traceability: forward trace (where did this lot go?) and
    backward trace (where did this come from?).
    """
    
    __tablename__ = "lots"
    
    # Lot identification
    lot_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # What is this lot?
    ingredient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ingredients.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)  # Link to product catalog
    product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Supplier (for received lots)
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Production (for manufactured lots)
    production_batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)  # Link to PlantOps batch
    
    # Dates
    received_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    manufactured_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Quantities
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity_remaining: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=LotStatus.PENDING, index=True)
    
    # Quality and testing
    test_results: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Traceability links (stored as JSON arrays of UUIDs or lot numbers)
    parent_lots: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)  # Where did this come from?
    child_lots: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)  # Where did this go?
    
    # Hold/release
    is_on_hold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hold_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hold_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    released_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    ingredient = relationship("Ingredient", back_populates="lots")
    supplier = relationship("Supplier", back_populates="lots")
    deviations = relationship("Deviation", back_populates="lot")
    
    __table_args__ = (
        Index("ix_lots_tenant_lot_number", "tenant_id", "lot_number", unique=True),
        Index("ix_lots_status", "tenant_id", "status"),
        Index("ix_lots_supplier", "supplier_id", "received_date"),
        Index("ix_lots_ingredient", "ingredient_id", "received_date"),
    )
    
    def __repr__(self) -> str:
        return f"<Lot(id={self.id}, lot_number='{self.lot_number}', status='{self.status}')>"


class Deviation(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    Deviation model for tracking quality and safety deviations.
    
    A deviation is any non-conformance to specifications, procedures, or standards.
    """
    
    __tablename__ = "deviations"
    
    # Deviation identification
    deviation_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Classification
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., "quality", "safety", "gmp"
    severity: Mapped[str] = mapped_column(String(50), nullable=False, default=DeviationSeverity.MEDIUM, index=True)
    
    # Related entities
    lot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    production_batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # When and where
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Investigation
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    investigation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Resolution
    immediate_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requires_capa: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    capa_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("capas.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Status and workflow
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=DeviationStatus.OPEN, index=True)
    reported_by: Mapped[str] = mapped_column(String(255), nullable=False)
    investigated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    closed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Impact
    affected_quantity: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    financial_impact: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    
    # Notes
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    lot = relationship("Lot", back_populates="deviations")
    capa = relationship("CAPA", back_populates="deviations", foreign_keys=[capa_id])
    
    __table_args__ = (
        Index("ix_deviations_tenant_number", "tenant_id", "deviation_number", unique=True),
        Index("ix_deviations_status_occurred", "tenant_id", "status", "occurred_at"),
        Index("ix_deviations_severity", "tenant_id", "severity", "occurred_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Deviation(id={self.id}, number='{self.deviation_number}', severity='{self.severity}')>"


class CAPA(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    CAPA (Corrective and Preventive Action) model.
    
    Tracks actions taken to correct problems and prevent recurrence.
    """
    
    __tablename__ = "capas"
    
    # CAPA identification
    capa_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Type
    is_corrective: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_preventive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Root cause
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Actions
    corrective_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preventive_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Due dates
    target_completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Verification
    verification_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_effective: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    # Status and ownership
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=CAPAStatus.OPEN, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    deviations = relationship("Deviation", back_populates="capa", foreign_keys="Deviation.capa_id")
    
    __table_args__ = (
        Index("ix_capas_tenant_number", "tenant_id", "capa_number", unique=True),
        Index("ix_capas_status", "tenant_id", "status"),
        Index("ix_capas_owner", "tenant_id", "owner"),
    )
    
    def __repr__(self) -> str:
        return f"<CAPA(id={self.id}, number='{self.capa_number}', status='{self.status}')>"


class HACCPPlan(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    HACCP Plan model for Hazard Analysis and Critical Control Points.
    """
    
    __tablename__ = "haccp_plans"
    
    # Plan identification
    plan_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Product/process
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    product_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    process_line_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # Hazard analysis (stored as JSON)
    hazard_analysis: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Critical Control Points (array of CCP definitions as JSON)
    ccps: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    # Verification and validation
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_review_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    ccp_logs = relationship("CCPLog", back_populates="haccp_plan")
    
    __table_args__ = (
        Index("ix_haccp_plans_tenant_code", "tenant_id", "plan_code", unique=True),
        Index("ix_haccp_plans_is_active", "tenant_id", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<HACCPPlan(id={self.id}, code='{self.plan_code}', name='{self.name}')>"


class CCPLog(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    Critical Control Point (CCP) log for monitoring HACCP compliance.
    
    Records measurements, limits, and deviations at critical control points.
    """
    
    __tablename__ = "ccp_logs"
    
    # CCP identification
    haccp_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("haccp_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ccp_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ccp_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # When and where
    log_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    production_batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    line_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # Measurement
    measurement_value: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Limits
    critical_limit_min: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    critical_limit_max: Mapped[Optional[float]] = mapped_column(Numeric(12, 4), nullable=True)
    
    # Status
    is_within_limits: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_deviation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Corrective action (if deviation)
    corrective_action_taken: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Recorded by
    recorded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    haccp_plan = relationship("HACCPPlan", back_populates="ccp_logs")
    
    __table_args__ = (
        Index("ix_ccp_logs_tenant_ccp_time", "tenant_id", "ccp_code", "log_time"),
        Index("ix_ccp_logs_is_deviation", "tenant_id", "is_deviation", "log_time"),
        Index("ix_ccp_logs_haccp_plan", "haccp_plan_id", "log_time"),
    )
    
    def __repr__(self) -> str:
        return f"<CCPLog(id={self.id}, ccp='{self.ccp_code}', within_limits={self.is_within_limits})>"


class Document(Base, UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin):
    """
    FSQ Document model for storing and managing compliance documents.
    
    Designed for RAG (Retrieval Augmented Generation):
    - Stores document metadata
    - Links to file storage (S3/MinIO)
    - Tracks indexing status for vector embeddings
    - Supports semantic search via pgvector
    """
    
    __tablename__ = "fsq_documents"
    
    # Document identification
    document_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Type and category
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # File storage
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # S3/MinIO path
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256 hash
    
    # Version control
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    is_latest_version: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    replaces_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # Status and approval
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_confidential: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Review cycle
    review_frequency_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_review_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # RAG indexing (for AI-powered search)
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    chunk_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Uploaded by
    uploaded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Tags for categorization
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    __table_args__ = (
        Index("ix_fsq_documents_tenant_number", "tenant_id", "document_number", unique=True),
        Index("ix_fsq_documents_type_category", "tenant_id", "document_type", "category"),
        Index("ix_fsq_documents_indexed", "tenant_id", "indexed_at"),
        Index("ix_fsq_documents_review", "tenant_id", "next_review_date"),
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, number='{self.document_number}', type='{self.document_type}')>"

