"""
Identity context domain models.

Handles tenants, users, roles, and authentication.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TenantStatus(str, Enum):
    """Tenant status enum."""
    
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class TenantPlan(str, Enum):
    """Tenant subscription plan."""
    
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class UserRole(str, Enum):
    """User role enum."""
    
    SUPERUSER = "superuser"  # Platform admin
    ADMIN = "admin"  # Tenant admin
    MANAGER = "manager"  # Plant manager, FSQ manager
    OPERATOR = "operator"  # Line operator, QA technician
    VIEWER = "viewer"  # Read-only access


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tenant model representing an organization in the system.
    
    Each tenant has its own isolated schema in the database for data isolation.
    """
    
    __tablename__ = "tenants"
    
    # Organization details
    org_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    
    # Database schema for multi-tenancy
    schema_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    
    # Subscription
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default=TenantPlan.STARTER)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=TenantStatus.PROVISIONING, index=True)
    
    # Contact information
    primary_contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Settings
    settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON stored as text
    
    # Timestamps for subscription
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    subscription_starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    subscription_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, org_name='{self.org_name}', status='{self.status}')>"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    User model representing a user within a tenant.
    
    Users belong to a single tenant and have a role that determines their permissions.
    """
    
    __tablename__ = "users"
    
    # Tenant relationship
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # User identity
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Role and permissions
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=UserRole.VIEWER, index=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Authentication
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Email verification
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Password reset
    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Preferences
    preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON stored as text
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    
    __table_args__ = (
        Index("ix_users_tenant_email", "tenant_id", "email", unique=True),
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class ApiKey(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    API key model for programmatic access.
    
    Allows users to authenticate via API keys instead of username/password.
    """
    
    __tablename__ = "api_keys"
    
    # Owner
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Key details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    prefix: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_count: Mapped[int] = mapped_column(String(20), default="0", nullable=False)
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Scopes/permissions (JSON)
    scopes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name='{self.name}', prefix='{self.prefix}')>"


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Audit log for tracking user actions.
    
    Records all significant actions for compliance and security.
    """
    
    __tablename__ = "audit_logs"
    
    # Who
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # What
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON of before/after
    
    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Timestamp is from TimestampMixin
    
    __table_args__ = (
        Index("ix_audit_logs_tenant_action_created", "tenant_id", "action", "created_at"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', resource='{self.resource_type}')>"
