"""
Retail domain models.

Core models for retail operations, store management, POS data, waste tracking,
on-shelf availability (OSA), and promotions.
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
class StoreStatus(str, enum.Enum):
    """Status of a store."""

    ACTIVE = "active"
    TEMPORARILY_CLOSED = "temporarily_closed"
    PERMANENTLY_CLOSED = "permanently_closed"


class WasteReason(str, enum.Enum):
    """Reason for waste."""

    EXPIRED = "expired"
    DAMAGED = "damaged"
    SPOILED = "spoiled"
    CUSTOMER_RETURN = "customer_return"
    SHRINKAGE = "shrinkage"
    OVERSTOCKED = "overstocked"
    OTHER = "other"


class OSAStatus(str, enum.Enum):
    """On-Shelf Availability status."""

    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    LOW_STOCK = "low_stock"


class OSAIssueType(str, enum.Enum):
    """Type of OSA issue."""

    OUT_OF_STOCK = "out_of_stock"
    LOW_STOCK = "low_stock"
    MISPLACED = "misplaced"
    SHELF_GAP = "shelf_gap"
    BACKROOM_STOCK = "backroom_stock"


class PromoType(str, enum.Enum):
    """Type of promotion."""

    PRICE_DISCOUNT = "price_discount"
    BOGO = "bogo"  # Buy One Get One
    BUNDLE = "bundle"
    LOYALTY_REWARD = "loyalty_reward"
    COUPON = "coupon"
    SEASONAL = "seasonal"
    TPR = "tpr"  # Temporary Price Reduction


class PromoStatus(str, enum.Enum):
    """Status of a promotion."""

    PLANNED = "planned"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# Models
class Banner(Base):
    """
    Banner (Retail Chain) entity.
    
    Represents a retail chain or banner (e.g., Whole Foods, Trader Joe's).
    """

    __tablename__ = "banners"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Banner information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Parent company
    parent_company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

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
    stores: Mapped[list["Store"]] = relationship("Store", back_populates="banner")


class Store(Base):
    """
    Store entity.
    
    Represents a physical retail store location.
    """

    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Store information
    banner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("banners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    store_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    store_format: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # e.g., "supermarket", "convenience", "flagship"

    # Location
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Store details
    square_footage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    opening_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Contact
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    manager_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    manager_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=StoreStatus.ACTIVE)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    banner: Mapped["Banner"] = relationship("Banner", back_populates="stores")


class Category(Base):
    """
    Product category entity for retail.
    
    Represents product categories used in retail (may differ from brand categories).
    """

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Category information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Hierarchy
    parent_category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

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
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent", remote_side=[parent_category_id]
    )
    parent: Mapped[Optional["Category"]] = relationship(
        "Category", back_populates="children", remote_side=[id]
    )


class POSTransaction(Base):
    """
    Point of Sale (POS) transaction entity.
    
    Represents individual POS transactions from retail stores.
    Typically loaded in bulk from POS systems.
    """

    __tablename__ = "pos_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Transaction details
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Product information
    sku_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # FK to SKUs
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )  # FK to Products
    upc: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # External identifiers (from POS system)
    external_sku_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Quantities and pricing
    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    discount_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    net_amount: Mapped[float] = mapped_column(Float, nullable=False)

    # Promo linkage
    promo_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("promos.id", ondelete="SET NULL"), nullable=True
    )
    
    # Additional metadata
    metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # e.g., {"payment_method": "credit", "basket_size": 5}

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    store: Mapped["Store"] = relationship("Store")


class Waste(Base):
    """
    Waste tracking entity.
    
    Tracks product waste at retail stores.
    """

    __tablename__ = "waste"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Waste details
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Product information
    sku_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Waste quantities
    quantity_wasted: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="units")
    estimated_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Reason & category
    reason: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Details
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    store: Mapped["Store"] = relationship("Store")


class OSAEvent(Base):
    """
    On-Shelf Availability (OSA) event entity.
    
    Tracks shelf availability issues and stock-outs.
    """

    __tablename__ = "osa_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Event details
    store_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    detected_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Product information
    sku_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    product_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # OSA status
    osa_status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    issue_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Stock levels
    on_hand_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    backroom_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shelf_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Resolution
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Impact
    estimated_lost_sales: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    duration_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Detection method
    detected_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # "manual", "ai", "system"
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )

    # Relationships
    store: Mapped["Store"] = relationship("Store")


class Promo(Base):
    """
    Promotion entity.
    
    Represents retail promotions and campaigns.
    """

    __tablename__ = "promos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Promo details
    promo_name: Mapped[str] = mapped_column(String(255), nullable=False)
    promo_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    promo_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Timing
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Scope
    banner_ids: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True
    )  # List of banner UUIDs
    store_ids: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True
    )  # List of store UUIDs (if specific stores)
    product_ids: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True
    )  # List of product UUIDs
    sku_ids: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True
    )  # List of SKU UUIDs

    # Promo mechanics
    discount_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    discount_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    promo_mechanics: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # Flexible promo rules

    # Budget & targets
    budget: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_units: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Performance (to be updated as promo runs)
    actual_units_sold: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    actual_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    actual_discount_given: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    roi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=PromoStatus.PLANNED)

    # AI suggestions
    suggested_by_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default="now()", nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True
    )

