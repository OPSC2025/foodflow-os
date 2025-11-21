"""
Product & SKU service - business logic for product management.
"""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.brand.domain.models import Product, ProductStatus, SKU, SKUStatus
from src.contexts.brand.domain.schemas import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    SKUCreate,
    SKUResponse,
    SKUUpdate,
)
from src.contexts.brand.infrastructure.repositories import ProductRepository, SKURepository


class ProductService:
    """Service for product operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = ProductRepository(session, tenant_id)

    async def create_product(self, data: ProductCreate) -> ProductResponse:
        """Create a new product."""
        product = Product(
            brand_id=data.brand_id,
            name=data.name,
            code=data.code,
            description=data.description,
            image_url=data.image_url,
            category=data.category,
            subcategory=data.subcategory,
            attributes=data.attributes,
            allergens=data.allergens,
            status=ProductStatus.DEVELOPMENT,
            launch_date=data.launch_date,
        )

        product = await self.repo.create(product)
        return ProductResponse.model_validate(product)

    async def get_product(self, product_id: uuid.UUID) -> Optional[ProductResponse]:
        """Get product by ID."""
        product = await self.repo.get_by_id(product_id)
        if product:
            return ProductResponse.model_validate(product)
        return None

    async def list_products(
        self,
        skip: int = 0,
        limit: int = 100,
        brand_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> tuple[list[ProductResponse], int]:
        """List products with filters."""
        products, total = await self.repo.list(skip, limit, brand_id, status)
        return (
            [ProductResponse.model_validate(p) for p in products],
            total,
        )

    async def update_product(
        self, product_id: uuid.UUID, data: ProductUpdate
    ) -> ProductResponse:
        """Update a product."""
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")

        # Update fields
        if data.name is not None:
            product.name = data.name
        if data.description is not None:
            product.description = data.description
        if data.image_url is not None:
            product.image_url = data.image_url
        if data.category is not None:
            product.category = data.category
        if data.subcategory is not None:
            product.subcategory = data.subcategory
        if data.attributes is not None:
            product.attributes = data.attributes
        if data.allergens is not None:
            product.allergens = data.allergens
        if data.status is not None:
            product.status = data.status
        if data.discontinuation_date is not None:
            product.discontinuation_date = data.discontinuation_date

        product = await self.repo.update(product)
        return ProductResponse.model_validate(product)

    async def launch_product(self, product_id: uuid.UUID) -> ProductResponse:
        """Launch a product (move from development to active)."""
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")

        if product.status != ProductStatus.DEVELOPMENT:
            raise ValueError("Only products in development can be launched")

        product.status = ProductStatus.ACTIVE
        product = await self.repo.update(product)
        return ProductResponse.model_validate(product)


class SKUService:
    """Service for SKU operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = SKURepository(session, tenant_id)

    async def create_sku(self, data: SKUCreate) -> SKUResponse:
        """Create a new SKU."""
        sku = SKU(
            product_id=data.product_id,
            sku_code=data.sku_code,
            name=data.name,
            description=data.description,
            variant_attributes=data.variant_attributes,
            package_size=data.package_size,
            package_unit=data.package_unit,
            units_per_case=data.units_per_case,
            suggested_retail_price=data.suggested_retail_price,
            wholesale_price=data.wholesale_price,
            cost_per_unit=data.cost_per_unit,
            upc=data.upc,
            gtin=data.gtin,
            status=SKUStatus.ACTIVE,
            is_active=True,
        )

        sku = await self.repo.create(sku)
        return SKUResponse.model_validate(sku)

    async def get_sku(self, sku_id: uuid.UUID) -> Optional[SKUResponse]:
        """Get SKU by ID."""
        sku = await self.repo.get_by_id(sku_id)
        if sku:
            return SKUResponse.model_validate(sku)
        return None

    async def list_skus(
        self,
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[SKUResponse], int]:
        """List SKUs with filters."""
        skus, total = await self.repo.list(skip, limit, product_id, is_active)
        return (
            [SKUResponse.model_validate(s) for s in skus],
            total,
        )

    async def update_sku(self, sku_id: uuid.UUID, data: SKUUpdate) -> SKUResponse:
        """Update a SKU."""
        sku = await self.repo.get_by_id(sku_id)
        if not sku:
            raise ValueError(f"SKU with ID {sku_id} not found")

        # Update fields
        if data.name is not None:
            sku.name = data.name
        if data.description is not None:
            sku.description = data.description
        if data.variant_attributes is not None:
            sku.variant_attributes = data.variant_attributes
        if data.package_size is not None:
            sku.package_size = data.package_size
        if data.package_unit is not None:
            sku.package_unit = data.package_unit
        if data.units_per_case is not None:
            sku.units_per_case = data.units_per_case
        if data.suggested_retail_price is not None:
            sku.suggested_retail_price = data.suggested_retail_price
        if data.wholesale_price is not None:
            sku.wholesale_price = data.wholesale_price
        if data.cost_per_unit is not None:
            sku.cost_per_unit = data.cost_per_unit
        if data.upc is not None:
            sku.upc = data.upc
        if data.gtin is not None:
            sku.gtin = data.gtin
        if data.status is not None:
            sku.status = data.status
        if data.is_active is not None:
            sku.is_active = data.is_active

        sku = await self.repo.update(sku)
        return SKUResponse.model_validate(sku)

