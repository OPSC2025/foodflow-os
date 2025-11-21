"""
Brand service - business logic for brand management.
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.brand.domain.models import Brand, BrandStatus
from src.contexts.brand.domain.schemas import (
    BrandCreate,
    BrandResponse,
    BrandUpdate,
)
from src.contexts.brand.infrastructure.repositories import BrandRepository


class BrandService:
    """Service for brand operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = BrandRepository(session, tenant_id)

    async def create_brand(self, data: BrandCreate) -> BrandResponse:
        """Create a new brand."""
        brand = Brand(
            name=data.name,
            code=data.code,
            description=data.description,
            logo_url=data.logo_url,
            company_name=data.company_name,
            website=data.website,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            target_market=data.target_market,
            channels=data.channels,
            status=BrandStatus.ACTIVE,
            is_active=True,
        )

        brand = await self.repo.create(brand)
        return BrandResponse.model_validate(brand)

    async def get_brand(self, brand_id: uuid.UUID) -> Optional[BrandResponse]:
        """Get brand by ID."""
        brand = await self.repo.get_by_id(brand_id)
        if brand:
            return BrandResponse.model_validate(brand)
        return None

    async def list_brands(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> tuple[list[BrandResponse], int]:
        """List brands with filters."""
        brands, total = await self.repo.list(skip, limit, is_active)
        return (
            [BrandResponse.model_validate(b) for b in brands],
            total,
        )

    async def update_brand(self, brand_id: uuid.UUID, data: BrandUpdate) -> BrandResponse:
        """Update a brand."""
        brand = await self.repo.get_by_id(brand_id)
        if not brand:
            raise ValueError(f"Brand with ID {brand_id} not found")

        # Update fields
        if data.name is not None:
            brand.name = data.name
        if data.description is not None:
            brand.description = data.description
        if data.logo_url is not None:
            brand.logo_url = data.logo_url
        if data.company_name is not None:
            brand.company_name = data.company_name
        if data.website is not None:
            brand.website = data.website
        if data.contact_email is not None:
            brand.contact_email = data.contact_email
        if data.contact_phone is not None:
            brand.contact_phone = data.contact_phone
        if data.target_market is not None:
            brand.target_market = data.target_market
        if data.channels is not None:
            brand.channels = data.channels
        if data.status is not None:
            brand.status = data.status
        if data.is_active is not None:
            brand.is_active = data.is_active

        brand = await self.repo.update(brand)
        return BrandResponse.model_validate(brand)

