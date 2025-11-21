"""
Tenant management API endpoints.

Provides REST API for tenant administration.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_user, get_current_superuser
from src.core.tenancy import Tenant, TenantProvisioningService


router = APIRouter()


# Schemas

class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly slug", pattern="^[a-z0-9-]+$")
    contact_email: Optional[str] = Field(None, description="Primary contact email")
    contact_name: Optional[str] = Field(None, description="Primary contact name")
    settings: Optional[dict] = Field(default_factory=dict, description="Tenant-specific settings")


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    settings: Optional[dict] = None


class TenantResponse(BaseModel):
    """Schema for tenant response."""
    
    id: UUID
    name: str
    slug: str
    schema_name: str
    is_active: bool
    contact_email: Optional[str]
    contact_name: Optional[str]
    settings: Optional[dict]
    subscription_tier: Optional[str]
    
    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Schema for listing tenants."""
    
    tenants: list[TenantResponse]
    total: int
    limit: int
    offset: int


# Endpoints

@router.post("/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(get_current_superuser),  # Only superusers can create tenants
) -> Tenant:
    """
    Create a new tenant with isolated schema.
    
    **Permissions**: Superuser only
    
    This endpoint:
    1. Creates a tenant record in the public schema
    2. Creates a dedicated PostgreSQL schema for the tenant
    3. Sets up initial permissions
    
    After creation, migrations should be run for the tenant schema.
    """
    service = TenantProvisioningService(db)
    
    # Check if slug already exists
    existing = await service.get_tenant_by_slug(payload.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with slug '{payload.slug}' already exists"
        )
    
    try:
        tenant = await service.create_tenant(
            name=payload.name,
            slug=payload.slug,
            contact_email=payload.contact_email,
            contact_name=payload.contact_name,
            settings=payload.settings,
        )
        return tenant
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}"
        )


@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants(
    active_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(get_current_superuser),
) -> TenantListResponse:
    """
    List all tenants.
    
    **Permissions**: Superuser only
    """
    service = TenantProvisioningService(db)
    tenants = await service.list_tenants(
        active_only=active_only,
        limit=limit,
        offset=offset
    )
    
    # Count total (simplified - in production, run a separate count query)
    total = len(tenants)
    
    return TenantListResponse(
        tenants=tenants,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> Tenant:
    """
    Get tenant by ID.
    
    **Permissions**: Users can only see their own tenant, superusers can see all.
    """
    service = TenantProvisioningService(db)
    tenant = await service.get_tenant_by_id(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Check permissions: users can only see their own tenant
    if not current_user.is_superuser and current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to this tenant is not allowed"
        )
    
    return tenant


@router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(get_current_superuser),
) -> Tenant:
    """
    Update tenant information.
    
    **Permissions**: Superuser only
    """
    service = TenantProvisioningService(db)
    tenant = await service.get_tenant_by_id(tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Update fields
    if payload.name is not None:
        tenant.name = payload.name
    if payload.contact_email is not None:
        tenant.contact_email = payload.contact_email
    if payload.contact_name is not None:
        tenant.contact_name = payload.contact_name
    if payload.settings is not None:
        tenant.settings = payload.settings
    
    await db.commit()
    await db.refresh(tenant)
    
    return tenant


@router.post("/tenants/{tenant_id}/activate", response_model=TenantResponse)
async def activate_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(get_current_superuser),
) -> Tenant:
    """
    Activate a tenant.
    
    **Permissions**: Superuser only
    """
    service = TenantProvisioningService(db)
    
    try:
        tenant = await service.activate_tenant(tenant_id)
        return tenant
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )


@router.post("/tenants/{tenant_id}/deactivate", response_model=TenantResponse)
async def deactivate_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _: CurrentUser = Depends(get_current_superuser),
) -> Tenant:
    """
    Deactivate a tenant.
    
    **Permissions**: Superuser only
    
    Deactivating a tenant prevents users from logging in and accessing the system.
    """
    service = TenantProvisioningService(db)
    
    try:
        tenant = await service.deactivate_tenant(tenant_id)
        return tenant
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )


@router.get("/tenants/me", response_model=TenantResponse)
async def get_my_tenant(
    db: AsyncSession = Depends(get_db_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> Tenant:
    """
    Get current user's tenant information.
    
    **Permissions**: Any authenticated user
    """
    service = TenantProvisioningService(db)
    tenant = await service.get_tenant_by_id(current_user.tenant_id)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return tenant

