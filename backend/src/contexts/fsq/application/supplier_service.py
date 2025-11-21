"""
Supplier service for managing suppliers and risk assessment.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.fsq.domain.models import Supplier
from src.contexts.fsq.domain.schemas import SupplierCreate, SupplierUpdate
from src.core.logging import logger


class SupplierService:
    """Service for supplier operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create_supplier(self, data: SupplierCreate) -> Supplier:
        """Create a new supplier."""
        # Check for duplicate supplier code
        stmt = select(Supplier).filter_by(
            tenant_id=self.tenant_id, supplier_code=data.supplier_code
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Supplier code '{data.supplier_code}' already exists")

        supplier = Supplier(**data.model_dump(), tenant_id=self.tenant_id)
        self.session.add(supplier)
        await self.session.flush()
        await self.session.refresh(supplier)

        logger.info(
            f"Created supplier {supplier.supplier_code} - {supplier.name}",
            extra={"tenant_id": str(self.tenant_id), "supplier_id": str(supplier.id)},
        )

        return supplier

    async def get_supplier(self, supplier_id: uuid.UUID) -> Optional[Supplier]:
        """Get a supplier by ID."""
        stmt = select(Supplier).filter_by(tenant_id=self.tenant_id, id=supplier_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_suppliers(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_approved: Optional[bool] = None,
    ) -> tuple[list[Supplier], int]:
        """List suppliers with pagination and filters."""
        stmt = select(Supplier).filter_by(tenant_id=self.tenant_id)

        if is_active is not None:
            stmt = stmt.filter_by(is_active=is_active)
        if is_approved is not None:
            stmt = stmt.filter_by(is_approved=is_approved)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Get page
        stmt = stmt.order_by(Supplier.name).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        suppliers = list(result.scalars().all())

        return suppliers, total

    async def update_supplier(
        self, supplier_id: uuid.UUID, data: SupplierUpdate
    ) -> Supplier:
        """Update a supplier."""
        supplier = await self.get_supplier(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with ID {supplier_id} not found")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(supplier, field, value)

        await self.session.flush()

        return supplier

    async def approve_supplier(
        self, supplier_id: uuid.UUID, approved_by: Optional[str] = None
    ) -> Supplier:
        """Approve a supplier."""
        supplier = await self.get_supplier(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with ID {supplier_id} not found")

        supplier.is_approved = True
        supplier.approval_date = datetime.utcnow()

        await self.session.flush()

        logger.info(
            f"Approved supplier {supplier.supplier_code}",
            extra={"tenant_id": str(self.tenant_id), "supplier_id": str(supplier_id)},
        )

        return supplier

    async def update_risk_score(
        self, supplier_id: uuid.UUID, risk_score: float
    ) -> Supplier:
        """Update supplier risk score."""
        supplier = await self.get_supplier(supplier_id)
        if not supplier:
            raise ValueError(f"Supplier with ID {supplier_id} not found")

        if risk_score < 0 or risk_score > 100:
            raise ValueError("Risk score must be between 0 and 100")

        supplier.risk_score = risk_score

        await self.session.flush()

        logger.info(
            f"Updated risk score for supplier {supplier.supplier_code} to {risk_score}",
            extra={"tenant_id": str(self.tenant_id), "supplier_id": str(supplier_id)},
        )

        return supplier

    async def get_average_supplier_risk(self) -> float:
        """Get average risk score across all active suppliers."""
        stmt = select(func.avg(Supplier.risk_score)).filter(
            Supplier.tenant_id == self.tenant_id,
            Supplier.is_active == True,
            Supplier.risk_score.isnot(None),
        )
        result = await self.session.execute(stmt)
        avg = result.scalar()

        return float(avg) if avg else 0.0

    async def get_high_risk_suppliers_count(self, threshold: float = 70.0) -> int:
        """Get count of high-risk suppliers."""
        stmt = select(func.count()).select_from(Supplier).filter(
            Supplier.tenant_id == self.tenant_id,
            Supplier.is_active == True,
            Supplier.risk_score >= threshold,
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

