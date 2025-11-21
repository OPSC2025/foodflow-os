"""
Production Plan service - business logic for production planning.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.domain.models import ProductionPlan, ProductionPlanStatus
from src.contexts.planning.domain.schemas import (
    ProductionPlanCreate,
    ProductionPlanResponse,
    ProductionPlanUpdate,
)
from src.contexts.planning.infrastructure.repositories import ProductionPlanRepository


class ProductionPlanService:
    """Service for production plan operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = ProductionPlanRepository(session, tenant_id)

    async def create_plan(self, data: ProductionPlanCreate) -> ProductionPlanResponse:
        """Create a new production plan."""
        plan = ProductionPlan(
            plan_name=data.plan_name,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            forecast_id=data.forecast_id,
            line_ids=data.line_ids,
            plan_data=data.plan_data,
            capacity_analysis=data.capacity_analysis,
            constraints=data.constraints,
            generated_by_ai=data.generated_by_ai,
            ai_optimizations=data.ai_optimizations,
            status=ProductionPlanStatus.DRAFT,
            created_by=data.created_by,
        )

        plan = await self.repo.create(plan)
        return ProductionPlanResponse.model_validate(plan)

    async def get_plan(self, plan_id: uuid.UUID) -> Optional[ProductionPlanResponse]:
        """Get production plan by ID."""
        plan = await self.repo.get_by_id(plan_id)
        if plan:
            return ProductionPlanResponse.model_validate(plan)
        return None

    async def list_plans(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        forecast_id: Optional[uuid.UUID] = None,
    ) -> tuple[list[ProductionPlanResponse], int]:
        """List production plans with filters."""
        plans, total = await self.repo.list(skip, limit, status, forecast_id)
        return (
            [ProductionPlanResponse.model_validate(p) for p in plans],
            total,
        )

    async def update_plan(
        self, plan_id: uuid.UUID, data: ProductionPlanUpdate
    ) -> ProductionPlanResponse:
        """Update a production plan."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise ValueError(f"Production plan with ID {plan_id} not found")

        # Only allow updates for draft or pending approval plans
        if plan.status not in [ProductionPlanStatus.DRAFT, ProductionPlanStatus.PENDING_APPROVAL]:
            raise ValueError(f"Cannot update plan with status: {plan.status}")

        # Update fields
        if data.plan_name is not None:
            plan.plan_name = data.plan_name
        if data.description is not None:
            plan.description = data.description
        if data.plan_data is not None:
            plan.plan_data = data.plan_data
        if data.capacity_analysis is not None:
            plan.capacity_analysis = data.capacity_analysis
        if data.constraints is not None:
            plan.constraints = data.constraints
        if data.status is not None:
            plan.status = data.status
        if data.completion_percentage is not None:
            plan.completion_percentage = data.completion_percentage

        plan = await self.repo.update(plan)
        return ProductionPlanResponse.model_validate(plan)

    async def submit_for_approval(
        self, plan_id: uuid.UUID
    ) -> ProductionPlanResponse:
        """Submit a plan for approval."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise ValueError(f"Production plan with ID {plan_id} not found")

        if plan.status != ProductionPlanStatus.DRAFT:
            raise ValueError(f"Only draft plans can be submitted for approval")

        plan.status = ProductionPlanStatus.PENDING_APPROVAL
        plan = await self.repo.update(plan)
        return ProductionPlanResponse.model_validate(plan)

    async def approve_plan(
        self, plan_id: uuid.UUID, user_email: str
    ) -> ProductionPlanResponse:
        """Approve a production plan."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise ValueError(f"Production plan with ID {plan_id} not found")

        if plan.status != ProductionPlanStatus.PENDING_APPROVAL:
            raise ValueError(f"Only pending plans can be approved")

        plan.status = ProductionPlanStatus.APPROVED
        plan.approved_by = user_email
        plan.approved_at = datetime.utcnow()

        plan = await self.repo.update(plan)
        return ProductionPlanResponse.model_validate(plan)

    async def start_execution(
        self, plan_id: uuid.UUID
    ) -> ProductionPlanResponse:
        """Start executing an approved plan."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise ValueError(f"Production plan with ID {plan_id} not found")

        if plan.status != ProductionPlanStatus.APPROVED:
            raise ValueError(f"Only approved plans can be executed")

        plan.status = ProductionPlanStatus.IN_PROGRESS
        plan.execution_start = datetime.utcnow()
        plan.completion_percentage = 0.0

        plan = await self.repo.update(plan)
        return ProductionPlanResponse.model_validate(plan)

    async def complete_plan(
        self, plan_id: uuid.UUID
    ) -> ProductionPlanResponse:
        """Mark a plan as completed."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise ValueError(f"Production plan with ID {plan_id} not found")

        if plan.status != ProductionPlanStatus.IN_PROGRESS:
            raise ValueError(f"Only in-progress plans can be completed")

        plan.status = ProductionPlanStatus.COMPLETED
        plan.execution_end = datetime.utcnow()
        plan.completion_percentage = 100.0

        plan = await self.repo.update(plan)
        return ProductionPlanResponse.model_validate(plan)

    async def cancel_plan(
        self, plan_id: uuid.UUID
    ) -> ProductionPlanResponse:
        """Cancel a production plan."""
        plan = await self.repo.get_by_id(plan_id)
        if not plan:
            raise ValueError(f"Production plan with ID {plan_id} not found")

        if plan.status == ProductionPlanStatus.COMPLETED:
            raise ValueError(f"Cannot cancel completed plans")

        plan.status = ProductionPlanStatus.CANCELLED
        plan = await self.repo.update(plan)
        return ProductionPlanResponse.model_validate(plan)

    async def list_pending_approval(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[ProductionPlanResponse], int]:
        """List plans pending approval."""
        plans, total = await self.repo.list_pending_approval(skip, limit)
        return (
            [ProductionPlanResponse.model_validate(p) for p in plans],
            total,
        )

