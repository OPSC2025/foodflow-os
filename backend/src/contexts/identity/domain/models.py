"""
Identity context domain models.

Handles users, roles, permissions, and authentication.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


# Association tables for many-to-many relationships

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    User model for authentication and authorization.
    
    Users belong to a tenant and can have multiple roles.
    """
    
    __tablename__ = "users"
    
    # Tenant association
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Basic info
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Activity tracking
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Email verification
    verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verification_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
    )
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission through any of their roles."""
        for role in self.roles:
            if any(perm.name == permission_name for perm in role.permissions):
                return True
        return False
    
    def get_all_permissions(self) -> List[str]:
        """Get list of all permission names user has."""
        permissions = set()
        for role in self.roles:
            for perm in role.permissions:
                permissions.add(perm.name)
        return list(permissions)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', tenant_id={self.tenant_id})>"


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Role model for role-based access control (RBAC).
    
    Roles are tenant-specific and contain a set of permissions.
    """
    
    __tablename__ = "roles"
    
    # Tenant association
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Role info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # System roles cannot be deleted
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    users = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles",
    )
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_role_tenant_name"),
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"


class Permission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Permission model for fine-grained access control.
    
    Permissions are global (not tenant-specific) and define what actions
    can be performed in the system.
    """
    
    __tablename__ = "permissions"
    
    # Permission info
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "batch", "line", "lot"
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "create", "read", "update", "delete"
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationships
    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
    )
    
    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name='{self.name}', resource='{self.resource}', action='{self.action}')>"


class RefreshToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Refresh token model for JWT token refresh flow.
    
    Stores refresh tokens for secure token renewal.
    """
    
    __tablename__ = "refresh_tokens"
    
    # User association
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Token info
    token: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Revocation
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Device/session tracking
    device_info: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    def __repr__(self) -> str:
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"


# Standard permissions (to be seeded)
STANDARD_PERMISSIONS = [
    # PlantOps permissions
    {"name": "plantops.plant.read", "resource": "plant", "action": "read", "description": "View plants"},
    {"name": "plantops.plant.create", "resource": "plant", "action": "create", "description": "Create plants"},
    {"name": "plantops.plant.update", "resource": "plant", "action": "update", "description": "Update plants"},
    {"name": "plantops.plant.delete", "resource": "plant", "action": "delete", "description": "Delete plants"},
    
    {"name": "plantops.line.read", "resource": "line", "action": "read", "description": "View production lines"},
    {"name": "plantops.line.create", "resource": "line", "action": "create", "description": "Create production lines"},
    {"name": "plantops.line.update", "resource": "line", "action": "update", "description": "Update production lines"},
    {"name": "plantops.line.delete", "resource": "line", "action": "delete", "description": "Delete production lines"},
    
    {"name": "plantops.batch.read", "resource": "batch", "action": "read", "description": "View batches"},
    {"name": "plantops.batch.create", "resource": "batch", "action": "create", "description": "Create batches"},
    {"name": "plantops.batch.update", "resource": "batch", "action": "update", "description": "Update batches"},
    {"name": "plantops.batch.delete", "resource": "batch", "action": "delete", "description": "Delete batches"},
    {"name": "plantops.batch.start", "resource": "batch", "action": "start", "description": "Start batches"},
    {"name": "plantops.batch.complete", "resource": "batch", "action": "complete", "description": "Complete batches"},
    
    {"name": "plantops.scrap.read", "resource": "scrap", "action": "read", "description": "View scrap events"},
    {"name": "plantops.scrap.create", "resource": "scrap", "action": "create", "description": "Log scrap events"},
    
    # FSQ permissions
    {"name": "fsq.lot.read", "resource": "lot", "action": "read", "description": "View lots"},
    {"name": "fsq.lot.create", "resource": "lot", "action": "create", "description": "Create lots"},
    {"name": "fsq.lot.trace", "resource": "lot", "action": "trace", "description": "Trace lots"},
    
    {"name": "fsq.deviation.read", "resource": "deviation", "action": "read", "description": "View deviations"},
    {"name": "fsq.deviation.create", "resource": "deviation", "action": "create", "description": "Report deviations"},
    {"name": "fsq.deviation.update", "resource": "deviation", "action": "update", "description": "Update deviations"},
    
    {"name": "fsq.capa.read", "resource": "capa", "action": "read", "description": "View CAPAs"},
    {"name": "fsq.capa.create", "resource": "capa", "action": "create", "description": "Create CAPAs"},
    {"name": "fsq.capa.update", "resource": "capa", "action": "update", "description": "Update CAPAs"},
    {"name": "fsq.capa.close", "resource": "capa", "action": "close", "description": "Close CAPAs"},
    
    # Planning permissions
    {"name": "planning.forecast.read", "resource": "forecast", "action": "read", "description": "View forecasts"},
    {"name": "planning.forecast.create", "resource": "forecast", "action": "create", "description": "Generate forecasts"},
    
    {"name": "planning.plan.read", "resource": "plan", "action": "read", "description": "View production plans"},
    {"name": "planning.plan.create", "resource": "plan", "action": "create", "description": "Create production plans"},
    {"name": "planning.plan.approve", "resource": "plan", "action": "approve", "description": "Approve production plans"},
    
    # Brand permissions
    {"name": "brand.brand.read", "resource": "brand", "action": "read", "description": "View brands"},
    {"name": "brand.brand.create", "resource": "brand", "action": "create", "description": "Create brands"},
    {"name": "brand.brand.update", "resource": "brand", "action": "update", "description": "Update brands"},
    
    {"name": "brand.copacker.read", "resource": "copacker", "action": "read", "description": "View co-packers"},
    {"name": "brand.copacker.create", "resource": "copacker", "action": "create", "description": "Create co-packers"},
    {"name": "brand.copacker.update", "resource": "copacker", "action": "update", "description": "Update co-packers"},
    
    # Retail permissions
    {"name": "retail.store.read", "resource": "store", "action": "read", "description": "View stores"},
    {"name": "retail.store.create", "resource": "store", "action": "create", "description": "Create stores"},
    
    {"name": "retail.pos.create", "resource": "pos", "action": "create", "description": "Record POS transactions"},
    {"name": "retail.waste.create", "resource": "waste", "action": "create", "description": "Record waste"},
    
    # Admin permissions
    {"name": "admin.user.read", "resource": "user", "action": "read", "description": "View users"},
    {"name": "admin.user.create", "resource": "user", "action": "create", "description": "Create users"},
    {"name": "admin.user.update", "resource": "user", "action": "update", "description": "Update users"},
    {"name": "admin.user.delete", "resource": "user", "action": "delete", "description": "Delete users"},
    
    {"name": "admin.role.read", "resource": "role", "action": "read", "description": "View roles"},
    {"name": "admin.role.create", "resource": "role", "action": "create", "description": "Create roles"},
    {"name": "admin.role.update", "resource": "role", "action": "update", "description": "Update roles"},
    {"name": "admin.role.delete", "resource": "role", "action": "delete", "description": "Delete roles"},
]


# Standard roles (to be created per tenant)
STANDARD_ROLES = {
    "admin": {
        "description": "Full access to all features within tenant",
        "permissions": [
            # All plantops
            "plantops.plant.*", "plantops.line.*", "plantops.batch.*", "plantops.scrap.*",
            # All fsq
            "fsq.lot.*", "fsq.deviation.*", "fsq.capa.*",
            # All planning
            "planning.forecast.*", "planning.plan.*",
            # All brand
            "brand.brand.*", "brand.copacker.*",
            # All retail
            "retail.store.*", "retail.pos.*", "retail.waste.*",
            # All admin
            "admin.user.*", "admin.role.*",
        ],
    },
    "operator": {
        "description": "Plant floor operator - can manage batches and record data",
        "permissions": [
            "plantops.plant.read", "plantops.line.read",
            "plantops.batch.read", "plantops.batch.create", "plantops.batch.update",
            "plantops.batch.start", "plantops.batch.complete",
            "plantops.scrap.read", "plantops.scrap.create",
        ],
    },
    "fsq_manager": {
        "description": "Food safety & quality manager - manages deviations, CAPAs, lots",
        "permissions": [
            "fsq.lot.read", "fsq.lot.create", "fsq.lot.trace",
            "fsq.deviation.read", "fsq.deviation.create", "fsq.deviation.update",
            "fsq.capa.read", "fsq.capa.create", "fsq.capa.update", "fsq.capa.close",
            "plantops.batch.read",  # Need to see production context
        ],
    },
    "planner": {
        "description": "Production planner - creates forecasts and production plans",
        "permissions": [
            "planning.forecast.read", "planning.forecast.create",
            "planning.plan.read", "planning.plan.create", "planning.plan.approve",
            "plantops.plant.read", "plantops.line.read", "plantops.batch.read",
        ],
    },
    "viewer": {
        "description": "Read-only access to all data",
        "permissions": [
            "plantops.plant.read", "plantops.line.read", "plantops.batch.read", "plantops.scrap.read",
            "fsq.lot.read", "fsq.deviation.read", "fsq.capa.read",
            "planning.forecast.read", "planning.plan.read",
            "brand.brand.read", "brand.copacker.read",
            "retail.store.read",
        ],
    },
}
