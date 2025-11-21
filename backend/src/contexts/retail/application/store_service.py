"""
Store service - business logic for store & banner management.
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.domain.models import Banner, Store, StoreStatus
from src.contexts.retail.domain.schemas import (
    BannerCreate,
    BannerResponse,
    BannerUpdate,
    StoreCreate,
    StoreResponse,
    StoreUpdate,
)
from src.contexts.retail.infrastructure.repositories import BannerRepository, StoreRepository


class BannerService:
    """Service for banner operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = BannerRepository(session, tenant_id)

    async def create_banner(self, data: BannerCreate) -> BannerResponse:
        """Create a new banner."""
        banner = Banner(
            name=data.name,
            code=data.code,
            description=data.description,
            logo_url=data.logo_url,
            parent_company=data.parent_company,
            is_active=True,
        )

        banner = await self.repo.create(banner)
        return BannerResponse.model_validate(banner)

    async def get_banner(self, banner_id: uuid.UUID) -> Optional[BannerResponse]:
        """Get banner by ID."""
        banner = await self.repo.get_by_id(banner_id)
        if banner:
            return BannerResponse.model_validate(banner)
        return None

    async def list_banners(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> tuple[list[BannerResponse], int]:
        """List banners with filters."""
        banners, total = await self.repo.list(skip, limit, is_active)
        return (
            [BannerResponse.model_validate(b) for b in banners],
            total,
        )

    async def update_banner(
        self, banner_id: uuid.UUID, data: BannerUpdate
    ) -> BannerResponse:
        """Update a banner."""
        banner = await self.repo.get_by_id(banner_id)
        if not banner:
            raise ValueError(f"Banner with ID {banner_id} not found")

        if data.name is not None:
            banner.name = data.name
        if data.description is not None:
            banner.description = data.description
        if data.logo_url is not None:
            banner.logo_url = data.logo_url
        if data.parent_company is not None:
            banner.parent_company = data.parent_company
        if data.is_active is not None:
            banner.is_active = data.is_active

        banner = await self.repo.update(banner)
        return BannerResponse.model_validate(banner)


class StoreService:
    """Service for store operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = StoreRepository(session, tenant_id)

    async def create_store(self, data: StoreCreate) -> StoreResponse:
        """Create a new store."""
        store = Store(
            banner_id=data.banner_id,
            store_number=data.store_number,
            name=data.name,
            store_format=data.store_format,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            postal_code=data.postal_code,
            latitude=data.latitude,
            longitude=data.longitude,
            square_footage=data.square_footage,
            opening_date=data.opening_date,
            phone=data.phone,
            manager_name=data.manager_name,
            manager_email=data.manager_email,
            status=StoreStatus.ACTIVE,
            is_active=True,
        )

        store = await self.repo.create(store)
        return StoreResponse.model_validate(store)

    async def get_store(self, store_id: uuid.UUID) -> Optional[StoreResponse]:
        """Get store by ID."""
        store = await self.repo.get_by_id(store_id)
        if store:
            return StoreResponse.model_validate(store)
        return None

    async def list_stores(
        self,
        skip: int = 0,
        limit: int = 100,
        banner_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[StoreResponse], int]:
        """List stores with filters."""
        stores, total = await self.repo.list(skip, limit, banner_id, is_active)
        return (
            [StoreResponse.model_validate(s) for s in stores],
            total,
        )

    async def update_store(self, store_id: uuid.UUID, data: StoreUpdate) -> StoreResponse:
        """Update a store."""
        store = await self.repo.get_by_id(store_id)
        if not store:
            raise ValueError(f"Store with ID {store_id} not found")

        if data.name is not None:
            store.name = data.name
        if data.store_format is not None:
            store.store_format = data.store_format
        if data.address is not None:
            store.address = data.address
        if data.city is not None:
            store.city = data.city
        if data.state is not None:
            store.state = data.state
        if data.postal_code is not None:
            store.postal_code = data.postal_code
        if data.phone is not None:
            store.phone = data.phone
        if data.manager_name is not None:
            store.manager_name = data.manager_name
        if data.manager_email is not None:
            store.manager_email = data.manager_email
        if data.status is not None:
            store.status = data.status
        if data.is_active is not None:
            store.is_active = data.is_active

        store = await self.repo.update(store)
        return StoreResponse.model_validate(store)

