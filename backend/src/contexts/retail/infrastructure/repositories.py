"""
Retail repositories.

Data access layer for Retail context models.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.domain.models import (
    Banner,
    Category,
    OSAEvent,
    POSTransaction,
    Promo,
    Store,
    Waste,
)


class BannerRepository:
    """Repository for Banner operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, banner: Banner) -> Banner:
        """Create a new banner."""
        banner.tenant_id = self.tenant_id
        self.session.add(banner)
        await self.session.flush()
        return banner

    async def get_by_id(self, banner_id: uuid.UUID) -> Optional[Banner]:
        """Get banner by ID."""
        result = await self.session.execute(
            select(Banner).where(and_(Banner.id == banner_id, Banner.tenant_id == self.tenant_id))
        )
        return result.scalars().first()

    async def list(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> tuple[list[Banner], int]:
        """List banners with filters."""
        conditions = [Banner.tenant_id == self.tenant_id]

        if is_active is not None:
            conditions.append(Banner.is_active == is_active)

        count_result = await self.session.execute(select(Banner).where(and_(*conditions)))
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(Banner)
            .where(and_(*conditions))
            .order_by(desc(Banner.created_at))
            .offset(skip)
            .limit(limit)
        )
        banners = result.scalars().all()

        return list(banners), total

    async def update(self, banner: Banner) -> Banner:
        """Update a banner."""
        await self.session.flush()
        return banner


class StoreRepository:
    """Repository for Store operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, store: Store) -> Store:
        """Create a new store."""
        store.tenant_id = self.tenant_id
        self.session.add(store)
        await self.session.flush()
        return store

    async def get_by_id(self, store_id: uuid.UUID) -> Optional[Store]:
        """Get store by ID."""
        result = await self.session.execute(
            select(Store).where(and_(Store.id == store_id, Store.tenant_id == self.tenant_id))
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        banner_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Store], int]:
        """List stores with filters."""
        conditions = [Store.tenant_id == self.tenant_id]

        if banner_id:
            conditions.append(Store.banner_id == banner_id)
        if is_active is not None:
            conditions.append(Store.is_active == is_active)

        count_result = await self.session.execute(select(Store).where(and_(*conditions)))
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(Store)
            .where(and_(*conditions))
            .order_by(desc(Store.created_at))
            .offset(skip)
            .limit(limit)
        )
        stores = result.scalars().all()

        return list(stores), total

    async def update(self, store: Store) -> Store:
        """Update a store."""
        await self.session.flush()
        return store


class CategoryRepository:
    """Repository for Category operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, category: Category) -> Category:
        """Create a new category."""
        category.tenant_id = self.tenant_id
        self.session.add(category)
        await self.session.flush()
        return category

    async def get_by_id(self, category_id: uuid.UUID) -> Optional[Category]:
        """Get category by ID."""
        result = await self.session.execute(
            select(Category).where(
                and_(Category.id == category_id, Category.tenant_id == self.tenant_id)
            )
        )
        return result.scalars().first()

    async def list(
        self, skip: int = 0, limit: int = 100, parent_id: Optional[uuid.UUID] = None
    ) -> tuple[list[Category], int]:
        """List categories with filters."""
        conditions = [Category.tenant_id == self.tenant_id]

        if parent_id is not None:
            conditions.append(Category.parent_category_id == parent_id)

        count_result = await self.session.execute(select(Category).where(and_(*conditions)))
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(Category)
            .where(and_(*conditions))
            .order_by(desc(Category.created_at))
            .offset(skip)
            .limit(limit)
        )
        categories = result.scalars().all()

        return list(categories), total

    async def update(self, category: Category) -> Category:
        """Update a category."""
        await self.session.flush()
        return category


class POSTransactionRepository:
    """Repository for POSTransaction operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, transaction: POSTransaction) -> POSTransaction:
        """Create a new POS transaction."""
        transaction.tenant_id = self.tenant_id
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def bulk_create(self, transactions: list[POSTransaction]) -> list[POSTransaction]:
        """Bulk create POS transactions."""
        for txn in transactions:
            txn.tenant_id = self.tenant_id
        self.session.add_all(transactions)
        await self.session.flush()
        return transactions

    async def get_by_id(self, transaction_id: uuid.UUID) -> Optional[POSTransaction]:
        """Get POS transaction by ID."""
        result = await self.session.execute(
            select(POSTransaction).where(
                and_(
                    POSTransaction.id == transaction_id,
                    POSTransaction.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        store_id: Optional[uuid.UUID] = None,
        sku_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[list[POSTransaction], int]:
        """List POS transactions with filters."""
        conditions = [POSTransaction.tenant_id == self.tenant_id]

        if store_id:
            conditions.append(POSTransaction.store_id == store_id)
        if sku_id:
            conditions.append(POSTransaction.sku_id == sku_id)
        if start_date:
            conditions.append(POSTransaction.transaction_date >= start_date)
        if end_date:
            conditions.append(POSTransaction.transaction_date <= end_date)

        count_result = await self.session.execute(
            select(POSTransaction).where(and_(*conditions))
        )
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(POSTransaction)
            .where(and_(*conditions))
            .order_by(desc(POSTransaction.transaction_date))
            .offset(skip)
            .limit(limit)
        )
        transactions = result.scalars().all()

        return list(transactions), total


class WasteRepository:
    """Repository for Waste operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, waste: Waste) -> Waste:
        """Create a new waste record."""
        waste.tenant_id = self.tenant_id
        self.session.add(waste)
        await self.session.flush()
        return waste

    async def get_by_id(self, waste_id: uuid.UUID) -> Optional[Waste]:
        """Get waste record by ID."""
        result = await self.session.execute(
            select(Waste).where(and_(Waste.id == waste_id, Waste.tenant_id == self.tenant_id))
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        store_id: Optional[uuid.UUID] = None,
        reason: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[list[Waste], int]:
        """List waste records with filters."""
        conditions = [Waste.tenant_id == self.tenant_id]

        if store_id:
            conditions.append(Waste.store_id == store_id)
        if reason:
            conditions.append(Waste.reason == reason)
        if start_date:
            conditions.append(Waste.recorded_date >= start_date)
        if end_date:
            conditions.append(Waste.recorded_date <= end_date)

        count_result = await self.session.execute(select(Waste).where(and_(*conditions)))
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(Waste)
            .where(and_(*conditions))
            .order_by(desc(Waste.recorded_date))
            .offset(skip)
            .limit(limit)
        )
        waste_records = result.scalars().all()

        return list(waste_records), total

    async def update(self, waste: Waste) -> Waste:
        """Update a waste record."""
        await self.session.flush()
        return waste


class OSAEventRepository:
    """Repository for OSAEvent operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, osa_event: OSAEvent) -> OSAEvent:
        """Create a new OSA event."""
        osa_event.tenant_id = self.tenant_id
        self.session.add(osa_event)
        await self.session.flush()
        return osa_event

    async def get_by_id(self, osa_event_id: uuid.UUID) -> Optional[OSAEvent]:
        """Get OSA event by ID."""
        result = await self.session.execute(
            select(OSAEvent).where(
                and_(OSAEvent.id == osa_event_id, OSAEvent.tenant_id == self.tenant_id)
            )
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        store_id: Optional[uuid.UUID] = None,
        resolved: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[list[OSAEvent], int]:
        """List OSA events with filters."""
        conditions = [OSAEvent.tenant_id == self.tenant_id]

        if store_id:
            conditions.append(OSAEvent.store_id == store_id)
        if resolved is not None:
            conditions.append(OSAEvent.resolved == resolved)
        if start_date:
            conditions.append(OSAEvent.detected_date >= start_date)
        if end_date:
            conditions.append(OSAEvent.detected_date <= end_date)

        count_result = await self.session.execute(select(OSAEvent).where(and_(*conditions)))
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(OSAEvent)
            .where(and_(*conditions))
            .order_by(desc(OSAEvent.detected_date))
            .offset(skip)
            .limit(limit)
        )
        osa_events = result.scalars().all()

        return list(osa_events), total

    async def update(self, osa_event: OSAEvent) -> OSAEvent:
        """Update an OSA event."""
        await self.session.flush()
        return osa_event


class PromoRepository:
    """Repository for Promo operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, promo: Promo) -> Promo:
        """Create a new promo."""
        promo.tenant_id = self.tenant_id
        self.session.add(promo)
        await self.session.flush()
        return promo

    async def get_by_id(self, promo_id: uuid.UUID) -> Optional[Promo]:
        """Get promo by ID."""
        result = await self.session.execute(
            select(Promo).where(and_(Promo.id == promo_id, Promo.tenant_id == self.tenant_id))
        )
        return result.scalars().first()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        active_only: bool = False,
    ) -> tuple[list[Promo], int]:
        """List promos with filters."""
        conditions = [Promo.tenant_id == self.tenant_id]

        if status:
            conditions.append(Promo.status == status)
        if active_only:
            now = datetime.utcnow()
            conditions.append(Promo.start_date <= now)
            conditions.append(Promo.end_date >= now)
            conditions.append(Promo.status == "active")

        count_result = await self.session.execute(select(Promo).where(and_(*conditions)))
        total = len(count_result.scalars().all())

        result = await self.session.execute(
            select(Promo)
            .where(and_(*conditions))
            .order_by(desc(Promo.created_at))
            .offset(skip)
            .limit(limit)
        )
        promos = result.scalars().all()

        return list(promos), total

    async def update(self, promo: Promo) -> Promo:
        """Update a promo."""
        await self.session.flush()
        return promo

