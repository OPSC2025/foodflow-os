"""
Core database module with async SQLAlchemy setup and multi-tenant support.

This module provides:
- Async database engine and session management
- Multi-tenant schema isolation
- Base models and mixins
- Database utilities
"""

import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, Optional

from sqlalchemy import Column, DateTime, MetaData, String, event, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool

from .config import get_settings

settings = get_settings()


# Naming convention for constraints (helps with migrations)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    
    metadata = metadata
    
    # Type annotation for SQLAlchemy to understand this is a table
    __tablename__: str
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name (snake_case)."""
        import re
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class TenantMixin:
    """Mixin to add tenant_id for multi-tenant models."""
    
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )


class UUIDPrimaryKeyMixin:
    """Mixin to add UUID primary key."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class DatabaseManager:
    """
    Manages database connections and sessions with multi-tenant support.
    
    This class handles:
    - Creating and managing async database engines
    - Session lifecycle management
    - Tenant schema isolation
    - Connection pooling
    """
    
    def __init__(self) -> None:
        """Initialize database manager."""
        self._engines: Dict[str, AsyncEngine] = {}
        self._session_makers: Dict[str, async_sessionmaker[AsyncSession]] = {}
        self._default_engine: Optional[AsyncEngine] = None
        self._default_session_maker: Optional[async_sessionmaker[AsyncSession]] = None
    
    def create_engine(
        self,
        database_url: Optional[str] = None,
        schema: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncEngine:
        """
        Create an async database engine.
        
        Args:
            database_url: Database connection URL (uses settings default if not provided)
            schema: PostgreSQL schema name for multi-tenancy
            **kwargs: Additional engine configuration
            
        Returns:
            AsyncEngine instance
        """
        url = database_url or settings.database_url
        
        # Set schema in search_path if provided
        connect_args: Dict[str, Any] = kwargs.pop("connect_args", {})
        if schema:
            connect_args["server_settings"] = {"search_path": schema}
        
        engine = create_async_engine(
            url,
            echo=settings.database_echo,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_recycle=settings.database_pool_recycle,
            pool_pre_ping=True,  # Verify connections before using
            connect_args=connect_args,
            **kwargs,
        )
        
        return engine
    
    def get_default_engine(self) -> AsyncEngine:
        """
        Get or create the default database engine.
        
        Returns:
            Default AsyncEngine instance
        """
        if self._default_engine is None:
            self._default_engine = self.create_engine()
        return self._default_engine
    
    def get_default_session_maker(self) -> async_sessionmaker[AsyncSession]:
        """
        Get or create the default session maker.
        
        Returns:
            Default session maker
        """
        if self._default_session_maker is None:
            engine = self.get_default_engine()
            self._default_session_maker = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        return self._default_session_maker
    
    def get_tenant_engine(self, tenant_schema: str) -> AsyncEngine:
        """
        Get or create a database engine for a specific tenant.
        
        Args:
            tenant_schema: Tenant's schema name
            
        Returns:
            AsyncEngine configured for the tenant's schema
        """
        if tenant_schema not in self._engines:
            self._engines[tenant_schema] = self.create_engine(schema=tenant_schema)
        return self._engines[tenant_schema]
    
    def get_tenant_session_maker(self, tenant_schema: str) -> async_sessionmaker[AsyncSession]:
        """
        Get or create a session maker for a specific tenant.
        
        Args:
            tenant_schema: Tenant's schema name
            
        Returns:
            Session maker configured for the tenant's schema
        """
        if tenant_schema not in self._session_makers:
            engine = self.get_tenant_engine(tenant_schema)
            self._session_makers[tenant_schema] = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
        return self._session_makers[tenant_schema]
    
    @asynccontextmanager
    async def get_session(
        self,
        tenant_schema: Optional[str] = None,
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session.
        
        Args:
            tenant_schema: Optional tenant schema for multi-tenant isolation
            
        Yields:
            AsyncSession instance
            
        Example:
            async with db_manager.get_session(tenant_schema="tenant_acme") as session:
                result = await session.execute(select(User))
                users = result.scalars().all()
        """
        if tenant_schema:
            session_maker = self.get_tenant_session_maker(tenant_schema)
        else:
            session_maker = self.get_default_session_maker()
        
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def create_schema(self, schema_name: str) -> None:
        """
        Create a new PostgreSQL schema for a tenant.
        
        Args:
            schema_name: Name of the schema to create
        """
        engine = self.get_default_engine()
        async with engine.begin() as conn:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
    
    async def drop_schema(self, schema_name: str, cascade: bool = False) -> None:
        """
        Drop a PostgreSQL schema.
        
        Args:
            schema_name: Name of the schema to drop
            cascade: Whether to cascade drop (delete all objects in schema)
        """
        engine = self.get_default_engine()
        cascade_clause = "CASCADE" if cascade else ""
        async with engine.begin() as conn:
            await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} {cascade_clause}"))
    
    async def create_tables(
        self,
        schema_name: Optional[str] = None,
        tables: Optional[list] = None,
    ) -> None:
        """
        Create database tables.
        
        Args:
            schema_name: Optional schema name for tenant-specific tables
            tables: Optional list of specific tables to create (creates all if None)
        """
        if schema_name:
            engine = self.get_tenant_engine(schema_name)
        else:
            engine = self.get_default_engine()
        
        async with engine.begin() as conn:
            if tables:
                await conn.run_sync(lambda sync_conn: Base.metadata.create_all(
                    sync_conn,
                    tables=tables,
                ))
            else:
                await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(
        self,
        schema_name: Optional[str] = None,
        tables: Optional[list] = None,
    ) -> None:
        """
        Drop database tables.
        
        Args:
            schema_name: Optional schema name for tenant-specific tables
            tables: Optional list of specific tables to drop (drops all if None)
        """
        if schema_name:
            engine = self.get_tenant_engine(schema_name)
        else:
            engine = self.get_default_engine()
        
        async with engine.begin() as conn:
            if tables:
                await conn.run_sync(lambda sync_conn: Base.metadata.drop_all(
                    sync_conn,
                    tables=tables,
                ))
            else:
                await conn.run_sync(Base.metadata.drop_all)
    
    async def close_all(self) -> None:
        """Close all database engines."""
        if self._default_engine:
            await self._default_engine.dispose()
        
        for engine in self._engines.values():
            await engine.dispose()
        
        self._engines.clear()
        self._session_makers.clear()
        self._default_engine = None
        self._default_session_maker = None


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get a database session.
    
    NOTE: This is the base session without tenant isolation.
    For tenant-aware sessions, use get_tenant_db_session().
    
    Use this with FastAPI's Depends():
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db_session)):
            ...
        
    Yields:
        AsyncSession instance
    """
    async with db_manager.get_session() as session:
        yield session


async def get_tenant_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get a tenant-aware database session.
    
    Automatically extracts tenant schema from ContextVar and sets search_path.
    MUST be used in combination with tenant_isolation_middleware.
    
    Use this with FastAPI's Depends():
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_tenant_db_session)):
            ...
        
    Yields:
        AsyncSession instance with tenant search_path set
    """
    from src.core.tenancy import get_tenant_from_context
    
    tenant_schema = get_tenant_from_context()
    
    async with db_manager.get_session() as session:
        # Set search_path for tenant isolation
        if tenant_schema:
            await session.execute(
                text(f"SET search_path TO {tenant_schema}, public")
            )
        
        yield session


async def init_db() -> None:
    """Initialize database (create tables, etc.)."""
    await db_manager.create_tables()


async def close_db() -> None:
    """Close all database connections."""
    await db_manager.close_all()
