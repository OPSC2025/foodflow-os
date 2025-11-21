"""
Authentication API endpoints.

Provides REST API for authentication (login, register, password reset, etc.).
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_user
from src.core.tenancy import TenantProvisioningService
from src.contexts.identity.application.auth_service import AuthenticationService
from src.contexts.identity.domain.models import User


router = APIRouter()


# Schemas

class RegisterRequest(BaseModel):
    """Schema for user registration."""
    
    tenant_slug: str = Field(..., description="Tenant slug (for finding tenant)")
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: Optional[str] = Field(None, description="Full name")
    role_names: Optional[list[str]] = Field(default_factory=lambda: ["viewer"], description="Role names to assign")


class LoginRequest(BaseModel):
    """Schema for login."""
    
    tenant_slug: str = Field(..., description="Tenant slug")
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Schema for token response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Schema for user response."""
    
    id: UUID
    tenant_id: UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    roles: list[str]
    
    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    """Schema for initiating password reset."""
    
    tenant_slug: str = Field(..., description="Tenant slug")
    email: EmailStr = Field(..., description="User email")


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset."""
    
    tenant_slug: str = Field(..., description="Tenant slug")
    reset_token: str = Field(..., description="Reset token from email")
    new_password: str = Field(..., min_length=8, description="New password")


class PasswordChangeRequest(BaseModel):
    """Schema for changing password (authenticated)."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


# Endpoints

@router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Register a new user.
    
    Creates a user account for an existing tenant.
    """
    # Get tenant by slug
    tenant_service = TenantProvisioningService(db)
    tenant = await tenant_service.get_tenant_by_slug(payload.tenant_slug)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with slug '{payload.tenant_slug}' not found"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is not active"
        )
    
    # Register user
    auth_service = AuthenticationService(db)
    
    try:
        user = await auth_service.register_user(
            tenant_id=tenant.id,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role_names=payload.role_names,
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """
    Login with email and password.
    
    Returns JWT access and refresh tokens on successful authentication.
    """
    # Get tenant by slug
    tenant_service = TenantProvisioningService(db)
    tenant = await tenant_service.get_tenant_by_slug(payload.tenant_slug)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is not active"
        )
    
    # Authenticate user
    auth_service = AuthenticationService(db)
    user = await auth_service.authenticate_user(
        tenant_id=tenant.id,
        email=payload.email,
        password=payload.password,
    )
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create tokens
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    tokens = await auth_service.create_tokens(
        user=user,
        tenant_schema=tenant.schema_name,
        device_info=user_agent,
        ip_address=client_ip,
    )
    
    return TokenResponse(**tokens)


@router.post("/auth/logout")
async def logout(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Logout current user.
    
    In a JWT-based system, logout is typically handled on the client side
    by discarding the tokens. This endpoint can be used to revoke refresh tokens.
    """
    # TODO: Revoke refresh tokens for this user
    return {"message": "Logged out successfully"}


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get current authenticated user's information.
    """
    auth_service = AuthenticationService(db)
    user = await auth_service.get_user_by_id(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/auth/password-reset/initiate")
async def initiate_password_reset(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Initiate password reset flow.
    
    Generates a reset token and sends it via email (stub for now).
    """
    # Get tenant
    tenant_service = TenantProvisioningService(db)
    tenant = await tenant_service.get_tenant_by_slug(payload.tenant_slug)
    
    if not tenant:
        # Don't reveal if tenant exists
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Get user
    auth_service = AuthenticationService(db)
    user = await auth_service.get_user_by_email(
        tenant_id=tenant.id,
        email=payload.email,
    )
    
    if user:
        # Generate reset token
        reset_token = await auth_service.initiate_password_reset(user)
        
        # TODO: Send email with reset token
        # For now, log it (in production, this would send an email)
        print(f"Password reset token for {user.email}: {reset_token}")
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/auth/password-reset/confirm")
async def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Confirm password reset with token.
    
    Resets the user's password using the reset token.
    """
    # Get tenant
    tenant_service = TenantProvisioningService(db)
    tenant = await tenant_service.get_tenant_by_slug(payload.tenant_slug)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    # Reset password
    auth_service = AuthenticationService(db)
    user = await auth_service.reset_password(
        tenant_id=tenant.id,
        reset_token=payload.reset_token,
        new_password=payload.new_password,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Password reset successfully"}


@router.post("/auth/password-change")
async def change_password(
    payload: PasswordChangeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Change password for authenticated user.
    
    Requires current password for verification.
    """
    auth_service = AuthenticationService(db)
    
    # Get user
    user = await auth_service.get_user_by_id(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    from src.core.security import verify_password
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Change password
    await auth_service.change_password(user, payload.new_password)
    
    return {"message": "Password changed successfully"}


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    active_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> list[User]:
    """
    List users in current tenant.
    
    **Permissions**: Requires admin.user.read permission
    """
    # TODO: Check permissions
    
    auth_service = AuthenticationService(db)
    users = await auth_service.list_users(
        tenant_id=current_user.tenant_id,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get user by ID.
    
    **Permissions**: Requires admin.user.read permission or viewing own profile
    """
    auth_service = AuthenticationService(db)
    user = await auth_service.get_user_by_id(
        tenant_id=current_user.tenant_id,
        user_id=user_id,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Users can view their own profile, admins can view any
    if user.id != current_user.id and not current_user.is_superuser:
        # TODO: Check admin.user.read permission
        pass
    
    return user

