"""
Authentication service for user management and authentication.
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from src.contexts.identity.domain.models import RefreshToken, Role, User


class AuthenticationService:
    """Service for user authentication and management."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize authentication service.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def register_user(
        self,
        tenant_id: uuid.UUID,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        role_names: Optional[list[str]] = None,
    ) -> User:
        """
        Register a new user.
        
        Args:
            tenant_id: Tenant ID
            email: User email
            password: Plain text password
            full_name: User's full name
            role_names: List of role names to assign
            
        Returns:
            Created user instance
            
        Raises:
            ValueError: If email already exists for tenant
        """
        # Check if user already exists
        existing = await self.get_user_by_email(tenant_id, email)
        if existing:
            raise ValueError(f"User with email {email} already exists")
        
        # Hash password
        hashed_pw = hash_password(password)
        
        # Create user
        user = User(
            tenant_id=tenant_id,
            email=email,
            hashed_password=hashed_pw,
            full_name=full_name,
            is_active=True,
            is_verified=False,
        )
        
        self.session.add(user)
        await self.session.flush()
        
        # Assign roles if provided
        if role_names:
            await self._assign_roles(user, role_names)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def authenticate_user(
        self,
        tenant_id: uuid.UUID,
        email: str,
        password: str,
    ) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            tenant_id: Tenant ID
            email: User email
            password: Plain text password
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        user = await self.get_user_by_email(tenant_id, email)
        
        if not user:
            return None
        
        # Check if user is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            return None
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts for 15 minutes
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
            
            await self.session.commit()
            return None
        
        # Successful login - reset failed attempts and update last login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def create_tokens(
        self,
        user: User,
        tenant_schema: str,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> dict:
        """
        Create access and refresh tokens for user.
        
        Args:
            user: User instance
            tenant_schema: Tenant schema name
            device_info: Device information
            ip_address: IP address
            
        Returns:
            Dictionary with access_token, refresh_token, and metadata
        """
        # Determine user's primary role
        role = user.roles[0].name if user.roles else "user"
        
        # Create access token
        access_token = create_access_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id),
            tenant_schema=tenant_schema,
            email=user.email,
            role=role,
        )
        
        # Create refresh token
        refresh_token_str = create_refresh_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id),
        )
        
        # Store refresh token in database
        refresh_token = RefreshToken(
            user_id=user.id,
            token=refresh_token_str,
            expires_at=datetime.utcnow() + timedelta(days=30),
            device_info=device_info,
            ip_address=ip_address,
        )
        
        self.session.add(refresh_token)
        await self.session.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_str,
            "token_type": "bearer",
            "expires_in": 900,  # 15 minutes
        }
    
    async def get_user_by_id(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            User instance or None
        """
        result = await self.session.execute(
            select(User).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(
        self,
        tenant_id: uuid.UUID,
        email: str,
    ) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            tenant_id: Tenant ID
            email: User email
            
        Returns:
            User instance or None
        """
        result = await self.session.execute(
            select(User).where(
                User.email == email,
                User.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def list_users(
        self,
        tenant_id: uuid.UUID,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[User]:
        """
        List users for a tenant.
        
        Args:
            tenant_id: Tenant ID
            active_only: If True, only return active users
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of user instances
        """
        query = select(User).where(User.tenant_id == tenant_id)
        
        if active_only:
            query = query.where(User.is_active == True)
        
        query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update_user(
        self,
        user: User,
        **kwargs,
    ) -> User:
        """
        Update user fields.
        
        Args:
            user: User instance
            **kwargs: Fields to update
            
        Returns:
            Updated user instance
        """
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def change_password(
        self,
        user: User,
        new_password: str,
    ) -> User:
        """
        Change user password.
        
        Args:
            user: User instance
            new_password: New plain text password
            
        Returns:
            Updated user instance
        """
        user.hashed_password = hash_password(new_password)
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def initiate_password_reset(
        self,
        user: User,
    ) -> str:
        """
        Initiate password reset flow.
        
        Args:
            user: User instance
            
        Returns:
            Reset token
        """
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        
        user.reset_token = reset_token
        user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=1)
        
        await self.session.commit()
        
        return reset_token
    
    async def reset_password(
        self,
        tenant_id: uuid.UUID,
        reset_token: str,
        new_password: str,
    ) -> Optional[User]:
        """
        Reset password using reset token.
        
        Args:
            tenant_id: Tenant ID
            reset_token: Reset token
            new_password: New plain text password
            
        Returns:
            User instance if reset successful, None otherwise
        """
        result = await self.session.execute(
            select(User).where(
                User.tenant_id == tenant_id,
                User.reset_token == reset_token,
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Check if token is expired
        if user.reset_token_expires_at < datetime.utcnow():
            return None
        
        # Reset password
        user.hashed_password = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires_at = None
        
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def _assign_roles(
        self,
        user: User,
        role_names: list[str],
    ) -> None:
        """
        Assign roles to user.
        
        Args:
            user: User instance
            role_names: List of role names
        """
        # Get roles
        result = await self.session.execute(
            select(Role).where(
                Role.tenant_id == user.tenant_id,
                Role.name.in_(role_names),
            )
        )
        roles = list(result.scalars().all())
        
        # Assign roles
        user.roles = roles


class RoleService:
    """Service for role and permission management."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize role service.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def create_role(
        self,
        tenant_id: uuid.UUID,
        name: str,
        description: Optional[str] = None,
        permission_names: Optional[list[str]] = None,
        is_system: bool = False,
    ) -> Role:
        """
        Create a new role.
        
        Args:
            tenant_id: Tenant ID
            name: Role name
            description: Role description
            permission_names: List of permission names
            is_system: Whether this is a system role
            
        Returns:
            Created role instance
            
        Raises:
            ValueError: If role name already exists for tenant
        """
        # Check if role already exists
        existing = await self.get_role_by_name(tenant_id, name)
        if existing:
            raise ValueError(f"Role with name {name} already exists")
        
        # Create role
        role = Role(
            tenant_id=tenant_id,
            name=name,
            description=description,
            is_system=is_system,
        )
        
        self.session.add(role)
        await self.session.flush()
        
        # Assign permissions if provided
        if permission_names:
            await self._assign_permissions(role, permission_names)
        
        await self.session.commit()
        await self.session.refresh(role)
        
        return role
    
    async def get_role_by_name(
        self,
        tenant_id: uuid.UUID,
        name: str,
    ) -> Optional[Role]:
        """
        Get role by name.
        
        Args:
            tenant_id: Tenant ID
            name: Role name
            
        Returns:
            Role instance or None
        """
        result = await self.session.execute(
            select(Role).where(
                Role.tenant_id == tenant_id,
                Role.name == name,
            )
        )
        return result.scalar_one_or_none()
    
    async def list_roles(
        self,
        tenant_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Role]:
        """
        List roles for a tenant.
        
        Args:
            tenant_id: Tenant ID
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of role instances
        """
        query = (
            select(Role)
            .where(Role.tenant_id == tenant_id)
            .order_by(Role.name)
            .limit(limit)
            .offset(offset)
        )
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def _assign_permissions(
        self,
        role: Role,
        permission_names: list[str],
    ) -> None:
        """
        Assign permissions to role.
        
        Args:
            role: Role instance
            permission_names: List of permission names
        """
        from src.contexts.identity.domain.models import Permission
        
        # Get permissions
        result = await self.session.execute(
            select(Permission).where(Permission.name.in_(permission_names))
        )
        permissions = list(result.scalars().all())
        
        # Assign permissions
        role.permissions = permissions

