"""
FSQ context repository layer for database operations.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.fsq.domain.models import (
    CAPA,
    CCPLog,
    Deviation,
    Document,
    HACCPPlan,
    Ingredient,
    Lot,
    Supplier,
)


# Lot Repository

class LotRepository:
    """Repository for Lot operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, lot: Lot) -> Lot:
        """Create a new lot."""
        lot.tenant_id = self.tenant_id
        self.session.add(lot)
        await self.session.flush()
        await self.session.refresh(lot)
        return lot

    async def get_by_id(self, lot_id: uuid.UUID) -> Optional[Lot]:
        """Get a lot by ID."""
        stmt = select(Lot).where(and_(Lot.id == lot_id, Lot.tenant_id == self.tenant_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_lot_number(self, lot_number: str) -> Optional[Lot]:
        """Get a lot by lot number."""
        stmt = select(Lot).where(
            and_(Lot.lot_number == lot_number, Lot.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        supplier_id: Optional[uuid.UUID] = None,
        ingredient_id: Optional[uuid.UUID] = None,
    ) -> list[Lot]:
        """List lots with pagination and filters."""
        stmt = select(Lot).where(Lot.tenant_id == self.tenant_id)

        if status:
            stmt = stmt.where(Lot.status == status)
        if supplier_id:
            stmt = stmt.where(Lot.supplier_id == supplier_id)
        if ingredient_id:
            stmt = stmt.where(Lot.ingredient_id == ingredient_id)

        stmt = stmt.order_by(desc(Lot.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        status: Optional[str] = None,
        supplier_id: Optional[uuid.UUID] = None,
        ingredient_id: Optional[uuid.UUID] = None,
    ) -> int:
        """Count lots matching filters."""
        stmt = select(func.count()).select_from(Lot).where(Lot.tenant_id == self.tenant_id)

        if status:
            stmt = stmt.where(Lot.status == status)
        if supplier_id:
            stmt = stmt.where(Lot.supplier_id == supplier_id)
        if ingredient_id:
            stmt = stmt.where(Lot.ingredient_id == ingredient_id)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update(self, lot: Lot) -> Lot:
        """Update a lot."""
        await self.session.flush()
        await self.session.refresh(lot)
        return lot


# Supplier Repository

class SupplierRepository:
    """Repository for Supplier operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, supplier: Supplier) -> Supplier:
        """Create a new supplier."""
        supplier.tenant_id = self.tenant_id
        self.session.add(supplier)
        await self.session.flush()
        await self.session.refresh(supplier)
        return supplier

    async def get_by_id(self, supplier_id: uuid.UUID) -> Optional[Supplier]:
        """Get a supplier by ID."""
        stmt = select(Supplier).where(
            and_(Supplier.id == supplier_id, Supplier.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> list[Supplier]:
        """List suppliers with pagination."""
        stmt = select(Supplier).where(Supplier.tenant_id == self.tenant_id)

        if is_active is not None:
            stmt = stmt.where(Supplier.is_active == is_active)

        stmt = stmt.order_by(Supplier.name).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, is_active: Optional[bool] = None) -> int:
        """Count suppliers matching filters."""
        stmt = select(func.count()).select_from(Supplier).where(
            Supplier.tenant_id == self.tenant_id
        )

        if is_active is not None:
            stmt = stmt.where(Supplier.is_active == is_active)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update(self, supplier: Supplier) -> Supplier:
        """Update a supplier."""
        await self.session.flush()
        await self.session.refresh(supplier)
        return supplier


# Ingredient Repository

class IngredientRepository:
    """Repository for Ingredient operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, ingredient: Ingredient) -> Ingredient:
        """Create a new ingredient."""
        ingredient.tenant_id = self.tenant_id
        self.session.add(ingredient)
        await self.session.flush()
        await self.session.refresh(ingredient)
        return ingredient

    async def get_by_id(self, ingredient_id: uuid.UUID) -> Optional[Ingredient]:
        """Get an ingredient by ID."""
        stmt = select(Ingredient).where(
            and_(Ingredient.id == ingredient_id, Ingredient.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self, skip: int = 0, limit: int = 100, category: Optional[str] = None
    ) -> list[Ingredient]:
        """List ingredients with pagination."""
        stmt = select(Ingredient).where(Ingredient.tenant_id == self.tenant_id)

        if category:
            stmt = stmt.where(Ingredient.category == category)

        stmt = stmt.order_by(Ingredient.name).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, category: Optional[str] = None) -> int:
        """Count ingredients matching filters."""
        stmt = select(func.count()).select_from(Ingredient).where(
            Ingredient.tenant_id == self.tenant_id
        )

        if category:
            stmt = stmt.where(Ingredient.category == category)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update(self, ingredient: Ingredient) -> Ingredient:
        """Update an ingredient."""
        await self.session.flush()
        await self.session.refresh(ingredient)
        return ingredient


# Deviation Repository

class DeviationRepository:
    """Repository for Deviation operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, deviation: Deviation) -> Deviation:
        """Create a new deviation."""
        deviation.tenant_id = self.tenant_id
        self.session.add(deviation)
        await self.session.flush()
        await self.session.refresh(deviation)
        return deviation

    async def get_by_id(self, deviation_id: uuid.UUID) -> Optional[Deviation]:
        """Get a deviation by ID."""
        stmt = select(Deviation).where(
            and_(Deviation.id == deviation_id, Deviation.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[Deviation]:
        """List deviations with pagination and filters."""
        stmt = select(Deviation).where(Deviation.tenant_id == self.tenant_id)

        if status:
            stmt = stmt.where(Deviation.status == status)
        if severity:
            stmt = stmt.where(Deviation.severity == severity)
        if category:
            stmt = stmt.where(Deviation.category == category)
        if start_date:
            stmt = stmt.where(Deviation.occurred_at >= start_date)
        if end_date:
            stmt = stmt.where(Deviation.occurred_at <= end_date)

        stmt = stmt.order_by(desc(Deviation.occurred_at)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count deviations matching filters."""
        stmt = select(func.count()).select_from(Deviation).where(
            Deviation.tenant_id == self.tenant_id
        )

        if status:
            stmt = stmt.where(Deviation.status == status)
        if severity:
            stmt = stmt.where(Deviation.severity == severity)
        if category:
            stmt = stmt.where(Deviation.category == category)
        if start_date:
            stmt = stmt.where(Deviation.occurred_at >= start_date)
        if end_date:
            stmt = stmt.where(Deviation.occurred_at <= end_date)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update(self, deviation: Deviation) -> Deviation:
        """Update a deviation."""
        await self.session.flush()
        await self.session.refresh(deviation)
        return deviation


# CAPA Repository

class CAPARepository:
    """Repository for CAPA operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, capa: CAPA) -> CAPA:
        """Create a new CAPA."""
        capa.tenant_id = self.tenant_id
        self.session.add(capa)
        await self.session.flush()
        await self.session.refresh(capa)
        return capa

    async def get_by_id(self, capa_id: uuid.UUID) -> Optional[CAPA]:
        """Get a CAPA by ID."""
        stmt = select(CAPA).where(and_(CAPA.id == capa_id, CAPA.tenant_id == self.tenant_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> list[CAPA]:
        """List CAPAs with pagination and filters."""
        stmt = select(CAPA).where(CAPA.tenant_id == self.tenant_id)

        if status:
            stmt = stmt.where(CAPA.status == status)
        if owner:
            stmt = stmt.where(CAPA.owner == owner)

        stmt = stmt.order_by(desc(CAPA.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, status: Optional[str] = None, owner: Optional[str] = None) -> int:
        """Count CAPAs matching filters."""
        stmt = select(func.count()).select_from(CAPA).where(CAPA.tenant_id == self.tenant_id)

        if status:
            stmt = stmt.where(CAPA.status == status)
        if owner:
            stmt = stmt.where(CAPA.owner == owner)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update(self, capa: CAPA) -> CAPA:
        """Update a CAPA."""
        await self.session.flush()
        await self.session.refresh(capa)
        return capa


# HACCP Plan Repository

class HACCPPlanRepository:
    """Repository for HACCP Plan operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, plan: HACCPPlan) -> HACCPPlan:
        """Create a new HACCP plan."""
        plan.tenant_id = self.tenant_id
        self.session.add(plan)
        await self.session.flush()
        await self.session.refresh(plan)
        return plan

    async def get_by_id(self, plan_id: uuid.UUID) -> Optional[HACCPPlan]:
        """Get a HACCP plan by ID."""
        stmt = select(HACCPPlan).where(
            and_(HACCPPlan.id == plan_id, HACCPPlan.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None
    ) -> list[HACCPPlan]:
        """List HACCP plans with pagination."""
        stmt = select(HACCPPlan).where(HACCPPlan.tenant_id == self.tenant_id)

        if is_active is not None:
            stmt = stmt.where(HACCPPlan.is_active == is_active)

        stmt = stmt.order_by(HACCPPlan.name).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, is_active: Optional[bool] = None) -> int:
        """Count HACCP plans matching filters."""
        stmt = select(func.count()).select_from(HACCPPlan).where(
            HACCPPlan.tenant_id == self.tenant_id
        )

        if is_active is not None:
            stmt = stmt.where(HACCPPlan.is_active == is_active)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update(self, plan: HACCPPlan) -> HACCPPlan:
        """Update a HACCP plan."""
        await self.session.flush()
        await self.session.refresh(plan)
        return plan


# CCP Log Repository

class CCPLogRepository:
    """Repository for CCP Log operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, log: CCPLog) -> CCPLog:
        """Create a new CCP log."""
        log.tenant_id = self.tenant_id
        self.session.add(log)
        await self.session.flush()
        await self.session.refresh(log)
        return log

    async def get_by_id(self, log_id: uuid.UUID) -> Optional[CCPLog]:
        """Get a CCP log by ID."""
        stmt = select(CCPLog).where(
            and_(CCPLog.id == log_id, CCPLog.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        haccp_plan_id: Optional[uuid.UUID] = None,
        ccp_code: Optional[str] = None,
        is_deviation: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[CCPLog]:
        """List CCP logs with pagination and filters."""
        stmt = select(CCPLog).where(CCPLog.tenant_id == self.tenant_id)

        if haccp_plan_id:
            stmt = stmt.where(CCPLog.haccp_plan_id == haccp_plan_id)
        if ccp_code:
            stmt = stmt.where(CCPLog.ccp_code == ccp_code)
        if is_deviation is not None:
            stmt = stmt.where(CCPLog.is_deviation == is_deviation)
        if start_time:
            stmt = stmt.where(CCPLog.log_time >= start_time)
        if end_time:
            stmt = stmt.where(CCPLog.log_time <= end_time)

        stmt = stmt.order_by(desc(CCPLog.log_time)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        haccp_plan_id: Optional[uuid.UUID] = None,
        ccp_code: Optional[str] = None,
        is_deviation: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """Count CCP logs matching filters."""
        stmt = select(func.count()).select_from(CCPLog).where(CCPLog.tenant_id == self.tenant_id)

        if haccp_plan_id:
            stmt = stmt.where(CCPLog.haccp_plan_id == haccp_plan_id)
        if ccp_code:
            stmt = stmt.where(CCPLog.ccp_code == ccp_code)
        if is_deviation is not None:
            stmt = stmt.where(CCPLog.is_deviation == is_deviation)
        if start_time:
            stmt = stmt.where(CCPLog.log_time >= start_time)
        if end_time:
            stmt = stmt.where(CCPLog.log_time <= end_time)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update(self, log: CCPLog) -> CCPLog:
        """Update a CCP log."""
        await self.session.flush()
        await self.session.refresh(log)
        return log


# Document Repository

class DocumentRepository:
    """Repository for Document operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, document: Document) -> Document:
        """Create a new document."""
        document.tenant_id = self.tenant_id
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        """Get a document by ID."""
        stmt = select(Document).where(
            and_(Document.id == document_id, Document.tenant_id == self.tenant_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[Document]:
        """List documents with pagination and filters."""
        stmt = select(Document).where(Document.tenant_id == self.tenant_id)

        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        if category:
            stmt = stmt.where(Document.category == category)
        if is_active is not None:
            stmt = stmt.where(Document.is_active == is_active)

        stmt = stmt.order_by(desc(Document.created_at)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(
        self,
        document_type: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """Count documents matching filters."""
        stmt = select(func.count()).select_from(Document).where(
            Document.tenant_id == self.tenant_id
        )

        if document_type:
            stmt = stmt.where(Document.document_type == document_type)
        if category:
            stmt = stmt.where(Document.category == category)
        if is_active is not None:
            stmt = stmt.where(Document.is_active == is_active)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def update(self, document: Document) -> Document:
        """Update a document."""
        await self.session.flush()
        await self.session.refresh(document)
        return document

