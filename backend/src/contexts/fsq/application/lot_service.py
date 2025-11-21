"""
Lot service for managing lot traceability.

Critical for food safety: forward and backward tracing.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.fsq.domain.models import Lot, LotStatus, Supplier, Ingredient
from src.contexts.fsq.domain.schemas import LotCreate, LotUpdate, LotResponse, LotTraceResult
from src.core.logging import logger


class LotService:
    """Service for lot operations and traceability."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create_lot(self, data: LotCreate) -> Lot:
        """Create a new lot."""
        # Check for duplicate lot number
        stmt = select(Lot).filter_by(tenant_id=self.tenant_id, lot_number=data.lot_number)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Lot number '{data.lot_number}' already exists")

        # Verify supplier if provided
        if data.supplier_id:
            stmt = select(Supplier).filter_by(tenant_id=self.tenant_id, id=data.supplier_id)
            result = await self.session.execute(stmt)
            supplier = result.scalar_one_or_none()
            if not supplier:
                raise ValueError(f"Supplier with ID {data.supplier_id} not found")

        # Verify ingredient if provided
        if data.ingredient_id:
            stmt = select(Ingredient).filter_by(tenant_id=self.tenant_id, id=data.ingredient_id)
            result = await self.session.execute(stmt)
            ingredient = result.scalar_one_or_none()
            if not ingredient:
                raise ValueError(f"Ingredient with ID {data.ingredient_id} not found")

        # Create lot
        lot_data = data.model_dump()
        # Set quantity_remaining to quantity if not provided
        if lot_data.get("quantity_remaining") is None:
            lot_data["quantity_remaining"] = lot_data["quantity"]

        lot = Lot(**lot_data, tenant_id=self.tenant_id)
        self.session.add(lot)
        await self.session.flush()
        await self.session.refresh(lot)

        logger.info(
            f"Created lot {lot.lot_number}",
            extra={"tenant_id": str(self.tenant_id), "lot_id": str(lot.id)},
        )

        return lot

    async def get_lot(self, lot_id: uuid.UUID) -> Optional[Lot]:
        """Get a lot by ID."""
        stmt = select(Lot).filter_by(tenant_id=self.tenant_id, id=lot_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_lot_by_number(self, lot_number: str) -> Optional[Lot]:
        """Get a lot by lot number."""
        stmt = select(Lot).filter_by(tenant_id=self.tenant_id, lot_number=lot_number)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_lots(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        supplier_id: Optional[uuid.UUID] = None,
        ingredient_id: Optional[uuid.UUID] = None,
        is_on_hold: Optional[bool] = None,
    ) -> tuple[list[Lot], int]:
        """List lots with pagination and filters."""
        stmt = select(Lot).filter_by(tenant_id=self.tenant_id)

        if status:
            stmt = stmt.filter_by(status=status)
        if supplier_id:
            stmt = stmt.filter_by(supplier_id=supplier_id)
        if ingredient_id:
            stmt = stmt.filter_by(ingredient_id=ingredient_id)
        if is_on_hold is not None:
            stmt = stmt.filter_by(is_on_hold=is_on_hold)

        # Count total
        from sqlalchemy import func

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Get page
        stmt = stmt.order_by(Lot.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        lots = list(result.scalars().all())

        return lots, total

    async def update_lot(self, lot_id: uuid.UUID, data: LotUpdate) -> Lot:
        """Update a lot."""
        lot = await self.get_lot(lot_id)
        if not lot:
            raise ValueError(f"Lot with ID {lot_id} not found")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lot, field, value)

        await self.session.flush()

        return lot

    async def put_on_hold(
        self, lot_id: uuid.UUID, reason: str, held_by: Optional[str] = None
    ) -> Lot:
        """Put a lot on hold (quarantine)."""
        lot = await self.get_lot(lot_id)
        if not lot:
            raise ValueError(f"Lot with ID {lot_id} not found")

        lot.is_on_hold = True
        lot.hold_reason = reason
        lot.hold_date = datetime.utcnow()
        lot.status = LotStatus.QUARANTINE

        await self.session.flush()

        logger.warning(
            f"Lot {lot.lot_number} put on hold - Reason: {reason}",
            extra={"tenant_id": str(self.tenant_id), "lot_id": str(lot_id)},
        )

        return lot

    async def release_lot(
        self, lot_id: uuid.UUID, released_by: str
    ) -> Lot:
        """Release a lot from hold."""
        lot = await self.get_lot(lot_id)
        if not lot:
            raise ValueError(f"Lot with ID {lot_id} not found")

        if not lot.is_on_hold:
            raise ValueError(f"Lot {lot.lot_number} is not on hold")

        lot.is_on_hold = False
        lot.released_date = datetime.utcnow()
        lot.released_by = released_by
        lot.status = LotStatus.RELEASED

        await self.session.flush()

        logger.info(
            f"Lot {lot.lot_number} released by {released_by}",
            extra={"tenant_id": str(self.tenant_id), "lot_id": str(lot_id)},
        )

        return lot

    async def trace_forward(
        self, lot_id: uuid.UUID, max_depth: int = 10
    ) -> LotTraceResult:
        """
        Forward trace: Where did this lot go?
        
        Traces child lots recursively.
        """
        origin_lot = await self.get_lot(lot_id)
        if not origin_lot:
            raise ValueError(f"Lot with ID {lot_id} not found")

        traced_lots = []
        await self._trace_forward_recursive(origin_lot, traced_lots, 0, max_depth)

        logger.info(
            f"Forward trace for lot {origin_lot.lot_number} - Found {len(traced_lots)} related lots",
            extra={"tenant_id": str(self.tenant_id), "lot_id": str(lot_id)},
        )

        return LotTraceResult(
            direction="forward",
            origin_lot_id=origin_lot.id,
            origin_lot_number=origin_lot.lot_number,
            traced_lots=[LotResponse.model_validate(lot) for lot in traced_lots],
            trace_depth=max_depth,
            total_lots=len(traced_lots),
        )

    async def _trace_forward_recursive(
        self, lot: Lot, traced_lots: list[Lot], current_depth: int, max_depth: int
    ) -> None:
        """Recursively trace forward through child lots."""
        if current_depth >= max_depth or not lot.child_lots:
            return

        for child_lot_number in lot.child_lots:
            child_lot = await self.get_lot_by_number(child_lot_number)
            if child_lot and child_lot not in traced_lots:
                traced_lots.append(child_lot)
                await self._trace_forward_recursive(
                    child_lot, traced_lots, current_depth + 1, max_depth
                )

    async def trace_backward(
        self, lot_id: uuid.UUID, max_depth: int = 10
    ) -> LotTraceResult:
        """
        Backward trace: Where did this lot come from?
        
        Traces parent lots recursively.
        """
        origin_lot = await self.get_lot(lot_id)
        if not origin_lot:
            raise ValueError(f"Lot with ID {lot_id} not found")

        traced_lots = []
        await self._trace_backward_recursive(origin_lot, traced_lots, 0, max_depth)

        logger.info(
            f"Backward trace for lot {origin_lot.lot_number} - Found {len(traced_lots)} related lots",
            extra={"tenant_id": str(self.tenant_id), "lot_id": str(lot_id)},
        )

        return LotTraceResult(
            direction="backward",
            origin_lot_id=origin_lot.id,
            origin_lot_number=origin_lot.lot_number,
            traced_lots=[LotResponse.model_validate(lot) for lot in traced_lots],
            trace_depth=max_depth,
            total_lots=len(traced_lots),
        )

    async def _trace_backward_recursive(
        self, lot: Lot, traced_lots: list[Lot], current_depth: int, max_depth: int
    ) -> None:
        """Recursively trace backward through parent lots."""
        if current_depth >= max_depth or not lot.parent_lots:
            return

        for parent_lot_number in lot.parent_lots:
            parent_lot = await self.get_lot_by_number(parent_lot_number)
            if parent_lot and parent_lot not in traced_lots:
                traced_lots.append(parent_lot)
                await self._trace_backward_recursive(
                    parent_lot, traced_lots, current_depth + 1, max_depth
                )

    async def link_lots(
        self, parent_lot_id: uuid.UUID, child_lot_id: uuid.UUID
    ) -> tuple[Lot, Lot]:
        """
        Link two lots for traceability.
        
        Creates parent-child relationship.
        """
        parent_lot = await self.get_lot(parent_lot_id)
        child_lot = await self.get_lot(child_lot_id)

        if not parent_lot:
            raise ValueError(f"Parent lot with ID {parent_lot_id} not found")
        if not child_lot:
            raise ValueError(f"Child lot with ID {child_lot_id} not found")

        # Add child to parent's child_lots
        if parent_lot.child_lots is None:
            parent_lot.child_lots = []
        if child_lot.lot_number not in parent_lot.child_lots:
            parent_lot.child_lots.append(child_lot.lot_number)

        # Add parent to child's parent_lots
        if child_lot.parent_lots is None:
            child_lot.parent_lots = []
        if parent_lot.lot_number not in child_lot.parent_lots:
            child_lot.parent_lots.append(parent_lot.lot_number)

        await self.session.flush()

        logger.info(
            f"Linked lots: {parent_lot.lot_number} → {child_lot.lot_number}",
            extra={"tenant_id": str(self.tenant_id)},
        )

        return parent_lot, child_lot

    async def get_lots_on_hold_count(self) -> int:
        """Get count of lots currently on hold."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(Lot).filter_by(
            tenant_id=self.tenant_id, is_on_hold=True
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

