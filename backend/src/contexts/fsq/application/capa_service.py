"""
CAPA service for managing Corrective and Preventive Actions.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.fsq.domain.models import CAPA, CAPAStatus
from src.contexts.fsq.domain.schemas import CAPACreate, CAPAUpdate
from src.core.logging import logger


class CAPAService:
    """Service for CAPA operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create_capa(self, data: CAPACreate) -> CAPA:
        """Create a new CAPA."""
        # Check for duplicate CAPA number
        stmt = select(CAPA).filter_by(tenant_id=self.tenant_id, capa_number=data.capa_number)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"CAPA number '{data.capa_number}' already exists")

        capa = CAPA(**data.model_dump(), tenant_id=self.tenant_id)
        self.session.add(capa)
        await self.session.flush()
        await self.session.refresh(capa)

        logger.info(
            f"Created CAPA {capa.capa_number} - Owner: {capa.owner}",
            extra={"tenant_id": str(self.tenant_id), "capa_id": str(capa.id)},
        )

        return capa

    async def get_capa(self, capa_id: uuid.UUID) -> Optional[CAPA]:
        """Get a CAPA by ID."""
        stmt = select(CAPA).filter_by(tenant_id=self.tenant_id, id=capa_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_capas(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> tuple[list[CAPA], int]:
        """List CAPAs with pagination and filters."""
        stmt = select(CAPA).filter_by(tenant_id=self.tenant_id)

        if status:
            stmt = stmt.filter_by(status=status)
        if owner:
            stmt = stmt.filter_by(owner=owner)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Get page
        stmt = stmt.order_by(CAPA.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        capas = list(result.scalars().all())

        return capas, total

    async def update_capa(self, capa_id: uuid.UUID, data: CAPAUpdate) -> CAPA:
        """Update a CAPA."""
        capa = await self.get_capa(capa_id)
        if not capa:
            raise ValueError(f"CAPA with ID {capa_id} not found")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(capa, field, value)

        await self.session.flush()

        return capa

    async def complete_capa(self, capa_id: uuid.UUID) -> CAPA:
        """Mark CAPA as completed."""
        capa = await self.get_capa(capa_id)
        if not capa:
            raise ValueError(f"CAPA with ID {capa_id} not found")

        if capa.status == CAPAStatus.CLOSED:
            raise ValueError(f"CAPA {capa.capa_number} is already closed")

        capa.status = CAPAStatus.PENDING_VERIFICATION
        capa.actual_completion_date = datetime.utcnow()

        await self.session.flush()

        logger.info(
            f"Completed CAPA {capa.capa_number}, pending verification",
            extra={"tenant_id": str(self.tenant_id), "capa_id": str(capa_id)},
        )

        return capa

    async def verify_capa(
        self, capa_id: uuid.UUID, verified_by: str, is_effective: bool, notes: Optional[str] = None
    ) -> CAPA:
        """Verify CAPA effectiveness."""
        capa = await self.get_capa(capa_id)
        if not capa:
            raise ValueError(f"CAPA with ID {capa_id} not found")

        if capa.status != CAPAStatus.PENDING_VERIFICATION:
            raise ValueError(f"CAPA {capa.capa_number} is not pending verification")

        capa.status = CAPAStatus.VERIFIED if is_effective else CAPAStatus.IN_PROGRESS
        capa.verification_date = datetime.utcnow()
        capa.verified_by = verified_by
        capa.is_effective = is_effective

        if notes:
            capa.notes = notes

        await self.session.flush()

        logger.info(
            f"Verified CAPA {capa.capa_number} - Effective: {is_effective}",
            extra={"tenant_id": str(self.tenant_id), "capa_id": str(capa_id)},
        )

        return capa

    async def close_capa(self, capa_id: uuid.UUID) -> CAPA:
        """Close a verified CAPA."""
        capa = await self.get_capa(capa_id)
        if not capa:
            raise ValueError(f"CAPA with ID {capa_id} not found")

        if capa.status != CAPAStatus.VERIFIED:
            raise ValueError(f"CAPA {capa.capa_number} must be verified before closing")

        capa.status = CAPAStatus.CLOSED

        await self.session.flush()

        logger.info(
            f"Closed CAPA {capa.capa_number}",
            extra={"tenant_id": str(self.tenant_id), "capa_id": str(capa_id)},
        )

        return capa

    async def get_open_capas_count(self) -> int:
        """Get count of open CAPAs."""
        stmt = select(func.count()).select_from(CAPA).filter(
            CAPA.tenant_id == self.tenant_id,
            CAPA.status.in_([CAPAStatus.OPEN, CAPAStatus.IN_PROGRESS]),
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_overdue_capas_count(self) -> int:
        """Get count of overdue CAPAs."""
        now = datetime.utcnow()
        stmt = select(func.count()).select_from(CAPA).filter(
            CAPA.tenant_id == self.tenant_id,
            CAPA.target_completion_date < now,
            CAPA.status.in_([CAPAStatus.OPEN, CAPAStatus.IN_PROGRESS]),
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

