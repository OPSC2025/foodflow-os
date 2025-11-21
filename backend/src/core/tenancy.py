"""
Core tenancy module for multi-tenant support.

Provides tenant provisioning, schema management, and tenant isolation utilities.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tenant model for multi-tenancy.
    
    Each tenant gets its own PostgreSQL schema for data isolation.
    """
    
    __tablename__ = "tenants"
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    schema_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Settings (JSON blob for tenant-specific configuration)
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Subscription info
    subscription_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Contact info
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name='{self.name}', slug='{self.slug}', schema='{self.schema_name}')>"


class TenantProvisioningService:
    """
    Service for provisioning and managing tenants.
    
    Handles:
    - Creating new tenants with isolated schemas
    - Running migrations for tenant schemas
    - Activating/deactivating tenants
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize tenant provisioning service.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def create_tenant(
        self,
        name: str,
        slug: str,
        contact_email: Optional[str] = None,
        contact_name: Optional[str] = None,
        settings: Optional[dict] = None,
    ) -> Tenant:
        """
        Create a new tenant with isolated schema.
        
        Args:
            name: Tenant name
            slug: URL-friendly slug (must be unique)
            contact_email: Primary contact email
            contact_name: Primary contact name
            settings: Optional tenant-specific settings
            
        Returns:
            Created tenant instance
            
        Raises:
            ValueError: If slug is invalid or already exists
        """
        # Generate schema name from slug
        schema_name = f"tenant_{slug}"
        
        # Create tenant record
        tenant = Tenant(
            name=name,
            slug=slug,
            schema_name=schema_name,
            contact_email=contact_email,
            contact_name=contact_name,
            settings=settings or {},
            is_active=True,
        )
        
        self.session.add(tenant)
        await self.session.flush()  # Get the ID without committing
        
        # Create schema in database
        await self._create_schema(schema_name)
        
        # Commit the transaction
        await self.session.commit()
        await self.session.refresh(tenant)
        
        return tenant
    
    async def _create_schema(self, schema_name: str) -> None:
        """
        Create a PostgreSQL schema for tenant isolation.
        
        Args:
            schema_name: Name of the schema to create
        """
        # Create schema
        await self.session.execute(
            text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        )
        
        # Grant usage on schema
        await self.session.execute(
            text(f"GRANT USAGE ON SCHEMA {schema_name} TO CURRENT_USER")
        )
        
        # Grant create on schema (for migrations)
        await self.session.execute(
            text(f"GRANT CREATE ON SCHEMA {schema_name} TO CURRENT_USER")
        )
    
    async def run_migrations_for_tenant(self, tenant_id: uuid.UUID) -> None:
        """
        Run database migrations for a specific tenant schema.
        
        This should be called after tenant creation to set up tables.
        
        Args:
            tenant_id: ID of the tenant
            
        Note:
            In practice, this would call Alembic programmatically to run
            migrations against the tenant's schema. For now, this is a stub.
        """
        # TODO: Implement Alembic migration execution
        # This will be implemented when we set up Alembic properly
        pass
    
    async def activate_tenant(self, tenant_id: uuid.UUID) -> Tenant:
        """
        Activate a tenant.
        
        Args:
            tenant_id: ID of the tenant to activate
            
        Returns:
            Updated tenant instance
        """
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one()
        
        tenant.is_active = True
        await self.session.commit()
        await self.session.refresh(tenant)
        
        return tenant
    
    async def deactivate_tenant(self, tenant_id: uuid.UUID) -> Tenant:
        """
        Deactivate a tenant.
        
        Args:
            tenant_id: ID of the tenant to deactivate
            
        Returns:
            Updated tenant instance
        """
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one()
        
        tenant.is_active = False
        await self.session.commit()
        await self.session.refresh(tenant)
        
        return tenant
    
    async def update_tenant_settings(
        self, 
        tenant_id: uuid.UUID, 
        settings: dict
    ) -> Tenant:
        """
        Update tenant settings.
        
        Args:
            tenant_id: ID of the tenant
            settings: New settings dictionary
            
        Returns:
            Updated tenant instance
        """
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one()
        
        tenant.settings = settings
        await self.session.commit()
        await self.session.refresh(tenant)
        
        return tenant
    
    async def get_tenant_by_id(self, tenant_id: uuid.UUID) -> Optional[Tenant]:
        """
        Get tenant by ID.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tenant instance or None
        """
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """
        Get tenant by slug.
        
        Args:
            slug: Tenant slug
            
        Returns:
            Tenant instance or None
        """
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Tenant).where(Tenant.slug == slug)
        )
        return result.scalar_one_or_none()
    
    async def list_tenants(
        self, 
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> list[Tenant]:
        """
        List all tenants.
        
        Args:
            active_only: If True, only return active tenants
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of tenant instances
        """
        from sqlalchemy import select
        
        query = select(Tenant)
        
        if active_only:
            query = query.where(Tenant.is_active == True)
        
        query = query.order_by(Tenant.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


async def set_tenant_context(session: AsyncSession, tenant_schema: str) -> None:
    """
    Set the search_path for the current session to isolate tenant data.
    
    This should be called at the beginning of each request to ensure
    all queries are scoped to the correct tenant.
    
    Args:
        session: Database session
        tenant_schema: Tenant's schema name (e.g., "tenant_acme")
    """
    await session.execute(
        text(f"SET search_path TO {tenant_schema}, public")
    )


async def get_tenant_from_token(token_payload: dict) -> str:
    """
    Extract tenant schema name from JWT token payload.
    
    Args:
        token_payload: Decoded JWT token payload
        
    Returns:
        Tenant schema name
        
    Raises:
        ValueError: If tenant information is missing from token
    """
    tenant_schema = token_payload.get("tenant_schema")
    if not tenant_schema:
        raise ValueError("Token missing tenant_schema claim")
    
    return tenant_schema

