"""
Brand & Co-packer repositories.

Data access layer for Brand context models.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.brand.domain.models import (
    Brand,
    BrandDocument,
    BrandPerformance,
    Copacker,
    CopackerContract,
    Product,
    SKU,
)


class BrandRepository:
    """Repository for Brand operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, brand: Brand) -> Brand:
        """Create a new brand."""
        brand.tenant_id = self.tenant_id
        self.session.add(brand)
        await self.session.flush()
        return brand

    async def get_by_id(self, brand_id: uuid.UUID) -> Optional[Brand]:
        """Get brand by ID."""
        result = await self.session.execute(
            select(Brand).where(and_(Brand.id == brand_id, Brand.tenant_id == self.tenant_id))
        )
        return result.scalars().first()

    async def list(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> tuple[list[Brand], int]:
        """List brands with filters."""
        conditions = [Brand.tenant_id == self.tenant_id]

        if is_active is not None:
            conditions.append(Brand.is_active == is_active)

        count_result = await self.session.execute(select(Brand).where(and_(*conditions)))
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(Brand)
            .where(and_(*conditions))
            .order_by(desc(Brand.created_at))
            .offset(skip)
            .limit(limit)
        )
        brands = result.scalars().all()

        return list(brands), total

    async def update(self, brand: Brand) -> Brand:
        """Update a brand."""
        await self.session.flush()
        return brand


class ProductRepository:
    """Repository for Product operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, product: Product) -> Product:
        """Create a new product."""
        product.tenant_id = self.tenant_id
        self.session.add(product)
        await self.session.flush()
        return product

    async def get_by_id(self, product_id: uuid.UUID) -> Optional[Product]:
        """Get product by ID."""
        result = await self.session.execute(
            select(Product).where(
                and_(Product.id == product_id, Product.tenant_id == self.tenant_id)
            )
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        brand_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Product], int]:
        """List products with filters."""
        conditions = [Product.tenant_id == self.tenant_id]

        if brand_id:
            conditions.append(Product.brand_id == brand_id)
        if status:
            conditions.append(Product.status == status)

        count_result = await self.session.execute(select(Product).where(and_(*conditions)))
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(Product)
            .where(and_(*conditions))
            .order_by(desc(Product.created_at))
            .offset(skip)
            .limit(limit)
        )
        products = result.scalars().all()

        return list(products), total

    async def update(self, product: Product) -> Product:
        """Update a product."""
        await self.session.flush()
        return product


class SKURepository:
    """Repository for SKU operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, sku: SKU) -> SKU:
        """Create a new SKU."""
        sku.tenant_id = self.tenant_id
        self.session.add(sku)
        await self.session.flush()
        return sku

    async def get_by_id(self, sku_id: uuid.UUID) -> Optional[SKU]:
        """Get SKU by ID."""
        result = await self.session.execute(
            select(SKU).where(and_(SKU.id == sku_id, SKU.tenant_id == self.tenant_id))
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        product_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[SKU], int]:
        """List SKUs with filters."""
        conditions = [SKU.tenant_id == self.tenant_id]

        if product_id:
            conditions.append(SKU.product_id == product_id)
        if is_active is not None:
            conditions.append(SKU.is_active == is_active)

        count_result = await self.session.execute(select(SKU).where(and_(*conditions)))
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(SKU)
            .where(and_(*conditions))
            .order_by(desc(SKU.created_at))
            .offset(skip)
            .limit(limit)
        )
        skus = result.scalars().all()

        return list(skus), total

    async def update(self, sku: SKU) -> SKU:
        """Update a SKU."""
        await self.session.flush()
        return sku


class CopackerRepository:
    """Repository for Copacker operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, copacker: Copacker) -> Copacker:
        """Create a new co-packer."""
        copacker.tenant_id = self.tenant_id
        self.session.add(copacker)
        await self.session.flush()
        return copacker

    async def get_by_id(self, copacker_id: uuid.UUID) -> Optional[Copacker]:
        """Get co-packer by ID."""
        result = await self.session.execute(
            select(Copacker).where(
                and_(Copacker.id == copacker_id, Copacker.tenant_id == self.tenant_id)
            )
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Copacker], int]:
        """List co-packers with filters."""
        conditions = [Copacker.tenant_id == self.tenant_id]

        if is_active is not None:
            conditions.append(Copacker.is_active == is_active)
        if status:
            conditions.append(Copacker.status == status)

        count_result = await self.session.execute(select(Copacker).where(and_(*conditions)))
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(Copacker)
            .where(and_(*conditions))
            .order_by(desc(Copacker.created_at))
            .offset(skip)
            .limit(limit)
        )
        copackers = result.scalars().all()

        return list(copackers), total

    async def update(self, copacker: Copacker) -> Copacker:
        """Update a co-packer."""
        await self.session.flush()
        return copacker


class CopackerContractRepository:
    """Repository for CopackerContract operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, contract: CopackerContract) -> CopackerContract:
        """Create a new contract."""
        contract.tenant_id = self.tenant_id
        self.session.add(contract)
        await self.session.flush()
        return contract

    async def get_by_id(self, contract_id: uuid.UUID) -> Optional[CopackerContract]:
        """Get contract by ID."""
        result = await self.session.execute(
            select(CopackerContract).where(
                and_(
                    CopackerContract.id == contract_id,
                    CopackerContract.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        copacker_id: Optional[uuid.UUID] = None,
        brand_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> tuple[list[CopackerContract], int]:
        """List contracts with filters."""
        conditions = [CopackerContract.tenant_id == self.tenant_id]

        if copacker_id:
            conditions.append(CopackerContract.copacker_id == copacker_id)
        if brand_id:
            conditions.append(CopackerContract.brand_id == brand_id)
        if status:
            conditions.append(CopackerContract.status == status)

        count_result = await self.session.execute(
            select(CopackerContract).where(and_(*conditions))
        )
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(CopackerContract)
            .where(and_(*conditions))
            .order_by(desc(CopackerContract.created_at))
            .offset(skip)
            .limit(limit)
        )
        contracts = result.scalars().all()

        return list(contracts), total

    async def update(self, contract: CopackerContract) -> CopackerContract:
        """Update a contract."""
        await self.session.flush()
        return contract


class BrandPerformanceRepository:
    """Repository for BrandPerformance operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, performance: BrandPerformance) -> BrandPerformance:
        """Create a new performance record."""
        performance.tenant_id = self.tenant_id
        self.session.add(performance)
        await self.session.flush()
        return performance

    async def get_by_id(self, performance_id: uuid.UUID) -> Optional[BrandPerformance]:
        """Get performance record by ID."""
        result = await self.session.execute(
            select(BrandPerformance).where(
                and_(
                    BrandPerformance.id == performance_id,
                    BrandPerformance.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        brand_id: Optional[uuid.UUID] = None,
        product_id: Optional[uuid.UUID] = None,
        sku_id: Optional[uuid.UUID] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> tuple[list[BrandPerformance], int]:
        """List performance records with filters."""
        conditions = [BrandPerformance.tenant_id == self.tenant_id]

        if brand_id:
            conditions.append(BrandPerformance.brand_id == brand_id)
        if product_id:
            conditions.append(BrandPerformance.product_id == product_id)
        if sku_id:
            conditions.append(BrandPerformance.sku_id == sku_id)
        if period_start:
            conditions.append(BrandPerformance.period_start >= period_start)
        if period_end:
            conditions.append(BrandPerformance.period_end <= period_end)

        count_result = await self.session.execute(
            select(BrandPerformance).where(and_(*conditions))
        )
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(BrandPerformance)
            .where(and_(*conditions))
            .order_by(desc(BrandPerformance.period_start))
            .offset(skip)
            .limit(limit)
        )
        performances = result.scalars().all()

        return list(performances), total

    async def update(self, performance: BrandPerformance) -> BrandPerformance:
        """Update a performance record."""
        await self.session.flush()
        return performance


class BrandDocumentRepository:
    """Repository for BrandDocument operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, document: BrandDocument) -> BrandDocument:
        """Create a new brand document."""
        document.tenant_id = self.tenant_id
        self.session.add(document)
        await self.session.flush()
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Optional[BrandDocument]:
        """Get document by ID."""
        result = await self.session.execute(
            select(BrandDocument).where(
                and_(BrandDocument.id == document_id, BrandDocument.tenant_id == self.tenant_id)
            )
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        brand_id: Optional[uuid.UUID] = None,
        product_id: Optional[uuid.UUID] = None,
        copacker_id: Optional[uuid.UUID] = None,
        document_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_indexed: Optional[bool] = None,
    ) -> tuple[list[BrandDocument], int]:
        """List documents with filters."""
        conditions = [BrandDocument.tenant_id == self.tenant_id]

        if brand_id:
            conditions.append(BrandDocument.brand_id == brand_id)
        if product_id:
            conditions.append(BrandDocument.product_id == product_id)
        if copacker_id:
            conditions.append(BrandDocument.copacker_id == copacker_id)
        if document_type:
            conditions.append(BrandDocument.document_type == document_type)
        if is_active is not None:
            conditions.append(BrandDocument.is_active == is_active)
        if is_indexed is not None:
            conditions.append(BrandDocument.is_indexed == is_indexed)

        count_result = await self.session.execute(
            select(BrandDocument).where(and_(*conditions))
        )
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(BrandDocument)
            .where(and_(*conditions))
            .order_by(desc(BrandDocument.created_at))
            .offset(skip)
            .limit(limit)
        )
        documents = result.scalars().all()

        return list(documents), total

    async def update(self, document: BrandDocument) -> BrandDocument:
        """Update a document."""
        await self.session.flush()
        return document

    async def search_documents(self, query: str, limit: int = 10) -> list[BrandDocument]:
        """
        Search documents by title, description, and tags.
        
        Note: This is basic text search. In Phase 4.3, this will be replaced
        with RAG vector search for semantic similarity.
        """
        # Simple case-insensitive search in title and description
        result = await self.session.execute(
            select(BrandDocument)
            .where(
                and_(
                    BrandDocument.tenant_id == self.tenant_id,
                    BrandDocument.is_active == True,
                    # Search in title or description
                    (
                        BrandDocument.title.ilike(f"%{query}%")
                        | BrandDocument.description.ilike(f"%{query}%")
                    ),
                )
            )
            .order_by(desc(BrandDocument.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

