"""
Trial service for managing line trials and experiments.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.domain.models import ProductionLine, Trial, TrialStatus
from src.contexts.plant_ops.domain.schemas import TrialCreate, TrialUpdate
from src.core.logging import logger


class TrialService:
    """Service for trial operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id

    async def create_trial(self, data: TrialCreate) -> Trial:
        """Create a new trial."""
        # Check for duplicate trial number
        stmt = select(Trial).filter_by(
            tenant_id=self.tenant_id, trial_number=data.trial_number
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Trial number '{data.trial_number}' already exists")

        # Verify line exists
        stmt = select(ProductionLine).filter_by(tenant_id=self.tenant_id, id=data.line_id)
        result = await self.session.execute(stmt)
        line = result.scalar_one_or_none()

        if not line:
            raise ValueError(f"Line with ID {data.line_id} not found")

        # Convert dict fields to JSON strings
        trial_data = data.model_dump()
        if trial_data.get("parameters"):
            trial_data["parameters"] = json.dumps(trial_data["parameters"])
        if trial_data.get("success_criteria"):
            trial_data["success_criteria"] = json.dumps(trial_data["success_criteria"])

        trial = Trial(**trial_data, tenant_id=self.tenant_id)
        self.session.add(trial)
        await self.session.flush()
        await self.session.refresh(trial)

        logger.info(
            f"Created trial {trial.trial_number} for line {line.line_number}",
            extra={"tenant_id": str(self.tenant_id), "trial_id": str(trial.id)},
        )

        return trial

    async def get_trial(self, trial_id: uuid.UUID) -> Optional[Trial]:
        """Get a trial by ID."""
        stmt = select(Trial).filter_by(tenant_id=self.tenant_id, id=trial_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_trial_by_number(self, trial_number: str) -> Optional[Trial]:
        """Get a trial by trial number."""
        stmt = select(Trial).filter_by(tenant_id=self.tenant_id, trial_number=trial_number)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_trials(
        self,
        skip: int = 0,
        limit: int = 100,
        line_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Trial], int]:
        """List trials with pagination."""
        stmt = select(Trial).filter_by(tenant_id=self.tenant_id)

        if line_id:
            stmt = stmt.filter_by(line_id=line_id)
        if status:
            stmt = stmt.filter_by(status=status)

        # Count total
        from sqlalchemy import func

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.session.execute(count_stmt)).scalar() or 0

        # Get page
        stmt = stmt.order_by(Trial.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        trials = list(result.scalars().all())

        return trials, total

    async def start_trial(self, trial_id: uuid.UUID) -> Trial:
        """Start a trial."""
        trial = await self.get_trial(trial_id)
        if not trial:
            raise ValueError(f"Trial with ID {trial_id} not found")

        if trial.status != TrialStatus.PLANNED:
            raise ValueError(
                f"Trial must be in PLANNED status to start (current: {trial.status})"
            )

        trial.status = TrialStatus.IN_PROGRESS
        trial.actual_start_time = datetime.utcnow()
        await self.session.flush()

        logger.info(
            f"Started trial {trial.trial_number}",
            extra={"tenant_id": str(self.tenant_id), "trial_id": str(trial_id)},
        )

        return trial

    async def complete_trial(
        self, trial_id: uuid.UUID, data: TrialUpdate
    ) -> Trial:
        """Complete a trial with results."""
        trial = await self.get_trial(trial_id)
        if not trial:
            raise ValueError(f"Trial with ID {trial_id} not found")

        if trial.status != TrialStatus.IN_PROGRESS:
            raise ValueError(
                f"Trial must be IN_PROGRESS to complete (current: {trial.status})"
            )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)

        # Convert dict fields to JSON strings
        if "results" in update_data and update_data["results"]:
            update_data["results"] = json.dumps(update_data["results"])
        if "parameters" in update_data and update_data["parameters"]:
            update_data["parameters"] = json.dumps(update_data["parameters"])

        for field, value in update_data.items():
            setattr(trial, field, value)

        trial.status = TrialStatus.COMPLETED
        trial.actual_end_time = datetime.utcnow()
        await self.session.flush()

        logger.info(
            f"Completed trial {trial.trial_number} - Success: {trial.was_successful}",
            extra={"tenant_id": str(self.tenant_id), "trial_id": str(trial_id)},
        )

        return trial

    async def update_trial(self, trial_id: uuid.UUID, data: TrialUpdate) -> Trial:
        """Update a trial."""
        trial = await self.get_trial(trial_id)
        if not trial:
            raise ValueError(f"Trial with ID {trial_id} not found")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)

        # Convert dict fields to JSON strings
        if "results" in update_data and update_data["results"]:
            update_data["results"] = json.dumps(update_data["results"])
        if "parameters" in update_data and update_data["parameters"]:
            update_data["parameters"] = json.dumps(update_data["parameters"])

        for field, value in update_data.items():
            setattr(trial, field, value)

        await self.session.flush()

        return trial

    async def cancel_trial(self, trial_id: uuid.UUID, reason: Optional[str] = None) -> Trial:
        """Cancel a trial."""
        trial = await self.get_trial(trial_id)
        if not trial:
            raise ValueError(f"Trial with ID {trial_id} not found")

        if trial.status == TrialStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed trial")

        trial.status = TrialStatus.CANCELLED
        if reason:
            trial.observations = f"Cancelled: {reason}"

        await self.session.flush()

        logger.info(
            f"Cancelled trial {trial.trial_number}",
            extra={"tenant_id": str(self.tenant_id), "trial_id": str(trial_id)},
        )

        return trial

    async def get_active_trials_count(self) -> int:
        """Get count of active (IN_PROGRESS) trials."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(Trial).filter_by(
            tenant_id=self.tenant_id, status=TrialStatus.IN_PROGRESS
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

