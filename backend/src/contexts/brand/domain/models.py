"""
Brand & Co-packer domain models.

Core models for brand management, products, SKUs, and co-packer relationships.
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
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


# Enums
class BrandStatus(str, enum.Enum):
    """Status of a brand."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ProductStatus(str, enum.Enum):
    """Status of a product."""

    DEVELOPMENT = "development"
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    ARCHIVED = "archived"


class SKUStatus(str, enum.Enum):
    """Status of a SKU."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"


class CopackerStatus(str, enum.Enum):
    """Status of a co-packer."""

    APPROVED = "approved"
    PENDING = "pending"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class ContractStatus(str, enum.Enum):
    """Status of a co-packer contract."""

    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class DocumentType(str, enum.Enum):
    """Type of brand document."""

    CONTRACT = "contract"
    SPECIFICATION = "specification"
    CERTIFICATE = "certificate"
    REPORT = "report"
    OTHER = "other"


# Models
class Brand(Base):
    """
    Brand entity.
    
    Represents a food brand that may produce multiple products.
    """

    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Brand information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Company details
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Business metrics
    target_market: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    channels: Mapped[Optional[list]] = mapped_column(
        ARRAY(String()), nullable=True
    )  # e.g., ["retail", "foodservice", "ecommerce"]

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=BrandStatus.ACTIVE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    products: Mapped[list["Product"]] = relationship("Product", back_populates="brand")


class Product(Base):
    """
    Product entity.
    
    Represents a product line within a brand (e.g., "Organic Granola Bar").
    Can have multiple SKUs (different sizes/flavors).
    """

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Product information
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Product classification
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Attributes (JSONB for flexibility)
    # Example: {"organic": true, "gluten_free": true, "vegan": false}
    attributes: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Allergen information
    allergens: Mapped[Optional[list]] = mapped_column(
        ARRAY(String()), nullable=True
    )  # e.g., ["milk", "soy", "nuts"]

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ProductStatus.ACTIVE)
    launch_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discontinuation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", back_populates="products")
    skus: Mapped[list["SKU"]] = relationship("SKU", back_populates="product")


class SKU(Base):
    """
    SKU (Stock Keeping Unit) entity.
    
    Represents a specific variant of a product (e.g., "Organic Granola Bar - Chocolate Chip - 12oz").
    """

    __tablename__ = "skus"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # SKU information
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Variant details
    variant_attributes: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # e.g., {"flavor": "Chocolate Chip", "size": "12oz"}

    # Packaging
    package_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    package_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # oz, lb, g, kg
    units_per_case: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Pricing
    suggested_retail_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wholesale_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_per_unit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Barcodes
    upc: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    gtin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=SKUStatus.ACTIVE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="skus")


class Copacker(Base):
    """
    Co-packer (Contract Manufacturer) entity.
    
    Represents a third-party manufacturer that produces products for brands.
    """

    __tablename__ = "copackers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Co-packer information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Contact information
    contact_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Location
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Capabilities
    capabilities: Mapped[Optional[list]] = mapped_column(
        ARRAY(String()), nullable=True
    )  # e.g., ["baking", "packaging", "cold_storage"]
    certifications: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # e.g., {"sqs": true, "organic": true, "kosher": false}

    # Performance metrics
    performance_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # 0-100 score
    on_time_delivery_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # 0-1 (percentage)
    quality_rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-5 stars

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=CopackerStatus.APPROVED)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    contracts: Mapped[list["CopackerContract"]] = relationship(
        "CopackerContract", back_populates="copacker"
    )


class CopackerContract(Base):
    """
    Co-packer contract entity.
    
    Represents a contract between a brand and a co-packer for producing specific products.
    """

    __tablename__ = "copacker_contracts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Contract parties
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    copacker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copackers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_ids: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True
    )  # List of product UUIDs covered by contract

    # Contract details
    contract_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Terms
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    renewal_terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pricing
    pricing_model: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # e.g., "per_unit", "per_batch", "monthly_retainer"
    pricing_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # SLAs (Service Level Agreements)
    slas: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # e.g., {"lead_time_days": 14, "min_order_qty": 1000}

    # Document reference (link to BrandDocument)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brand_documents.id", ondelete="SET NULL"), nullable=True
    )

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ContractStatus.ACTIVE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    copacker: Mapped["Copacker"] = relationship("Copacker", back_populates="contracts")
    document: Mapped[Optional["BrandDocument"]] = relationship("BrandDocument", foreign_keys=[document_id])


class BrandPerformance(Base):
    """
    Brand performance metrics.
    
    Tracks financial and operational performance for brands and products.
    """

    __tablename__ = "brand_performance"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Scope
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True
    )
    sku_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skus.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Time period
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "daily", "weekly", "monthly", "quarterly"

    # Sales metrics
    units_sold: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gross_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    net_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost_of_goods_sold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross_margin: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    gross_margin_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Additional metrics (flexible JSONB)
    # Example: {"market_share": 0.15, "velocity": 2.5, "customer_retention": 0.82}
    additional_metrics: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )


class BrandDocument(Base):
    """
    Brand document entity (RAG-ready).
    
    Stores brand-related documents (contracts, specifications, reports).
    Designed for future RAG (Retrieval Augmented Generation) integration.
    """

    __tablename__ = "brand_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Document metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # contract, specification, etc.
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    # Relationships
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=True, index=True
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True
    )
    copacker_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("copackers.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # File information
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # bytes
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )  # SHA-256

    # Version control
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="1.0")
    is_latest_version: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parent_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brand_documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    # RAG indexing (for Phase 4.3)
    is_indexed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )  # RAG indexed?
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Document lifecycle
    uploaded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Tagging
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String()), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    child_documents: Mapped[list["BrandDocument"]] = relationship(
        "BrandDocument", back_populates="parent_document", remote_side=[parent_document_id]
    )
    parent_document: Mapped[Optional["BrandDocument"]] = relationship(
        "BrandDocument", back_populates="child_documents", remote_side=[id]
    )

