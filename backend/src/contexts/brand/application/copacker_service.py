"""
Co-packer service - business logic for co-packer management.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.brand.domain.models import (
    Copacker,
    CopackerContract,
    CopackerStatus,
    ContractStatus,
)
from src.contexts.brand.domain.schemas import (
    CopackerContractCreate,
    CopackerContractResponse,
    CopackerContractUpdate,
    CopackerCreate,
    CopackerPerformanceResponse,
    CopackerResponse,
    CopackerUpdate,
)
from src.contexts.brand.infrastructure.repositories import (
    CopackerContractRepository,
    CopackerRepository,
)


class CopackerService:
    """Service for co-packer operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = CopackerRepository(session, tenant_id)

    async def create_copacker(self, data: CopackerCreate) -> CopackerResponse:
        """Create a new co-packer."""
        copacker = Copacker(
            name=data.name,
            code=data.code,
            description=data.description,
            contact_person=data.contact_person,
            email=data.email,
            phone=data.phone,
            website=data.website,
            address=data.address,
            city=data.city,
            state=data.state,
            country=data.country,
            postal_code=data.postal_code,
            capabilities=data.capabilities,
            certifications=data.certifications,
            status=CopackerStatus.PENDING,
            is_active=True,
        )

        copacker = await self.repo.create(copacker)
        return CopackerResponse.model_validate(copacker)

    async def get_copacker(self, copacker_id: uuid.UUID) -> Optional[CopackerResponse]:
        """Get co-packer by ID."""
        copacker = await self.repo.get_by_id(copacker_id)
        if copacker:
            return CopackerResponse.model_validate(copacker)
        return None

    async def list_copackers(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        status: Optional[str] = None,
    ) -> tuple[list[CopackerResponse], int]:
        """List co-packers with filters."""
        copackers, total = await self.repo.list(skip, limit, is_active, status)
        return (
            [CopackerResponse.model_validate(c) for c in copackers],
            total,
        )

    async def update_copacker(
        self, copacker_id: uuid.UUID, data: CopackerUpdate
    ) -> CopackerResponse:
        """Update a co-packer."""
        copacker = await self.repo.get_by_id(copacker_id)
        if not copacker:
            raise ValueError(f"Co-packer with ID {copacker_id} not found")

        # Update fields
        if data.name is not None:
            copacker.name = data.name
        if data.description is not None:
            copacker.description = data.description
        if data.contact_person is not None:
            copacker.contact_person = data.contact_person
        if data.email is not None:
            copacker.email = data.email
        if data.phone is not None:
            copacker.phone = data.phone
        if data.website is not None:
            copacker.website = data.website
        if data.address is not None:
            copacker.address = data.address
        if data.city is not None:
            copacker.city = data.city
        if data.state is not None:
            copacker.state = data.state
        if data.country is not None:
            copacker.country = data.country
        if data.postal_code is not None:
            copacker.postal_code = data.postal_code
        if data.capabilities is not None:
            copacker.capabilities = data.capabilities
        if data.certifications is not None:
            copacker.certifications = data.certifications
        if data.performance_score is not None:
            copacker.performance_score = data.performance_score
        if data.on_time_delivery_rate is not None:
            copacker.on_time_delivery_rate = data.on_time_delivery_rate
        if data.quality_rating is not None:
            copacker.quality_rating = data.quality_rating
        if data.status is not None:
            copacker.status = data.status
        if data.is_active is not None:
            copacker.is_active = data.is_active

        copacker = await self.repo.update(copacker)
        return CopackerResponse.model_validate(copacker)

    async def approve_copacker(self, copacker_id: uuid.UUID) -> CopackerResponse:
        """Approve a co-packer for use."""
        copacker = await self.repo.get_by_id(copacker_id)
        if not copacker:
            raise ValueError(f"Co-packer with ID {copacker_id} not found")

        if copacker.status != CopackerStatus.PENDING:
            raise ValueError("Only pending co-packers can be approved")

        copacker.status = CopackerStatus.APPROVED
        copacker = await self.repo.update(copacker)
        return CopackerResponse.model_validate(copacker)

    async def get_copacker_performance(
        self,
        copacker_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
    ) -> CopackerPerformanceResponse:
        """
        Get co-packer performance metrics.
        
        TODO: In Phase 4, this will aggregate actual data from production batches.
        For now, returns current performance scores.
        """
        copacker = await self.repo.get_by_id(copacker_id)
        if not copacker:
            raise ValueError(f"Co-packer with ID {copacker_id} not found")

        # For now, return current metrics
        # In Phase 4, this would aggregate from actual batch data
        return CopackerPerformanceResponse(
            copacker_id=copacker.id,
            copacker_name=copacker.name,
            period_start=period_start,
            period_end=period_end,
            performance_score=copacker.performance_score or 0.0,
            on_time_delivery_rate=copacker.on_time_delivery_rate or 0.0,
            quality_rating=copacker.quality_rating or 0.0,
            total_orders=0,  # TODO: Calculate from batches
            defect_rate=None,
            average_lead_time_days=None,
            issues_summary=None,
        )


class CopackerContractService:
    """Service for co-packer contract operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = CopackerContractRepository(session, tenant_id)

    async def create_contract(
        self, data: CopackerContractCreate
    ) -> CopackerContractResponse:
        """Create a new co-packer contract."""
        contract = CopackerContract(
            brand_id=data.brand_id,
            copacker_id=data.copacker_id,
            product_ids=data.product_ids,
            contract_number=data.contract_number,
            title=data.title,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            renewal_terms=data.renewal_terms,
            pricing_model=data.pricing_model,
            pricing_details=data.pricing_details,
            slas=data.slas,
            document_id=data.document_id,
            status=ContractStatus.DRAFT,
            is_active=False,
        )

        contract = await self.repo.create(contract)
        return CopackerContractResponse.model_validate(contract)

    async def get_contract(
        self, contract_id: uuid.UUID
    ) -> Optional[CopackerContractResponse]:
        """Get contract by ID."""
        contract = await self.repo.get_by_id(contract_id)
        if contract:
            return CopackerContractResponse.model_validate(contract)
        return None

    async def list_contracts(
        self,
        skip: int = 0,
        limit: int = 100,
        copacker_id: Optional[uuid.UUID] = None,
        brand_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> tuple[list[CopackerContractResponse], int]:
        """List contracts with filters."""
        contracts, total = await self.repo.list(skip, limit, copacker_id, brand_id, status)
        return (
            [CopackerContractResponse.model_validate(c) for c in contracts],
            total,
        )

    async def update_contract(
        self, contract_id: uuid.UUID, data: CopackerContractUpdate
    ) -> CopackerContractResponse:
        """Update a contract."""
        contract = await self.repo.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract with ID {contract_id} not found")

        # Update fields
        if data.title is not None:
            contract.title = data.title
        if data.description is not None:
            contract.description = data.description
        if data.end_date is not None:
            contract.end_date = data.end_date
        if data.renewal_terms is not None:
            contract.renewal_terms = data.renewal_terms
        if data.pricing_model is not None:
            contract.pricing_model = data.pricing_model
        if data.pricing_details is not None:
            contract.pricing_details = data.pricing_details
        if data.slas is not None:
            contract.slas = data.slas
        if data.document_id is not None:
            contract.document_id = data.document_id
        if data.status is not None:
            contract.status = data.status
        if data.is_active is not None:
            contract.is_active = data.is_active

        contract = await self.repo.update(contract)
        return CopackerContractResponse.model_validate(contract)

    async def activate_contract(
        self, contract_id: uuid.UUID
    ) -> CopackerContractResponse:
        """Activate a contract."""
        contract = await self.repo.get_by_id(contract_id)
        if not contract:
            raise ValueError(f"Contract with ID {contract_id} not found")

        if contract.status != ContractStatus.DRAFT:
            raise ValueError("Only draft contracts can be activated")

        contract.status = ContractStatus.ACTIVE
        contract.is_active = True
        contract = await self.repo.update(contract)
        return CopackerContractResponse.model_validate(contract)

