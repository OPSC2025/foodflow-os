"""
Core security module for authentication and authorization.

Provides:
- JWT token generation and validation
- Password hashing and verification
- Multi-tenant access control
- Security utilities
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from .config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security_scheme = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """JWT token payload structure."""
    
    sub: str  # Subject (user ID)
    tenant_id: str
    tenant_schema: str
    email: str
    role: str
    exp: datetime
    iat: datetime
    jti: str = Field(default_factory=lambda: str(uuid.uuid4()))  # JWT ID for revocation


class TokenResponse(BaseModel):
    """Token response model."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUser(BaseModel):
    """Current authenticated user model."""
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    tenant_schema: str
    email: str
    role: str
    is_active: bool = True
    is_superuser: bool = False


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    tenant_id: str,
    tenant_schema: str,
    email: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: User ID (sub claim)
        tenant_id: Tenant ID
        tenant_schema: Tenant schema name
        email: User email
        role: User role
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "tenant_schema": tenant_schema,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
    }
    
    encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(
    subject: str,
    tenant_id: str,
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: User ID
        tenant_id: Tenant ID
        
    Returns:
        Encoded JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    payload = {
        "sub": subject,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    
    encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenPayload with decoded claims
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        
        # Validate required fields
        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )
        
        return TokenPayload(**payload)
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> CurrentUser:
    """
    Get the current authenticated user from JWT token.
    
    This is a FastAPI dependency that extracts and validates the JWT token,
    then returns the current user information.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        
    Returns:
        CurrentUser instance
        
    Raises:
        HTTPException: If authentication fails
        
    Example:
        @app.get("/protected")
        async def protected_route(user: CurrentUser = Depends(get_current_user)):
            return {"user_id": user.id, "tenant": user.tenant_schema}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_payload = decode_token(credentials.credentials)
    
    # Create CurrentUser from token payload
    current_user = CurrentUser(
        id=uuid.UUID(token_payload.sub),
        tenant_id=uuid.UUID(token_payload.tenant_id),
        tenant_schema=token_payload.tenant_schema,
        email=token_payload.email,
        role=token_payload.role,
    )
    
    # Store user in request state for access in other parts of the request lifecycle
    request.state.user = current_user
    request.state.tenant_schema = current_user.tenant_schema
    
    return current_user


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Get the current active user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        CurrentUser if active
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Get the current user if they are a superuser.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        CurrentUser if superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


def check_role(allowed_roles: List[str]):
    """
    Create a dependency that checks if user has one of the allowed roles.
    
    Args:
        allowed_roles: List of role names that are allowed
        
    Returns:
        Dependency function
        
    Example:
        @app.get("/admin", dependencies=[Depends(check_role(["admin", "superuser"]))])
        async def admin_route():
            return {"message": "Admin access"}
    """
    async def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized. Required: {allowed_roles}",
            )
        return current_user
    
    return role_checker


def check_tenant_access(tenant_id: uuid.UUID):
    """
    Create a dependency that checks if user has access to a specific tenant.
    
    Args:
        tenant_id: Tenant ID to check access for
        
    Returns:
        Dependency function
    """
    async def tenant_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.tenant_id != tenant_id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to this tenant is not allowed",
            )
        return current_user
    
    return tenant_checker


class TenantIsolationMiddleware:
    """
    Middleware to enforce tenant isolation at the request level.
    
    This middleware ensures that every request is associated with a valid tenant
    and sets the appropriate database schema for the request.
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Process request with tenant isolation."""
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Extract tenant from token if present
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    token_payload = decode_token(token)
                    scope["state"]["tenant_schema"] = token_payload.tenant_schema
                    scope["state"]["tenant_id"] = token_payload.tenant_id
                except HTTPException:
                    pass  # Let the route handler deal with invalid tokens
        
        await self.app(scope, receive, send)


def generate_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        API key string
    """
    import secrets
    return f"ffos_{secrets.token_urlsafe(32)}"


def validate_api_key(api_key: str) -> bool:
    """
    Validate an API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        True if valid format, False otherwise
    """
    return api_key.startswith("ffos_") and len(api_key) > 40
