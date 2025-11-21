"""
Brand API router for co-packers and contracts.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.brand.application.copacker_service import (
    CopackerContractService,
    CopackerService,
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
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/copackers", tags=["Copackers"])


@router.post(
    "",
    response_model=CopackerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a co-packer",
)
async def create_copacker(
    data: CopackerCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new co-packer."""
    service = CopackerService(session, current_user.tenant_id)
    
    try:
        copacker = await service.create_copacker(data)
        await session.commit()
        return copacker
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create co-packer: {str(e)}",
        )


@router.get(
    "",
    response_model=list[CopackerResponse],
    summary="List co-packers",
)
async def list_copackers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List co-packers with optional filters."""
    service = CopackerService(session, current_user.tenant_id)
    
    try:
        copackers, total = await service.list_copackers(skip, limit, is_active, status)
        return copackers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list co-packers: {str(e)}",
        )


@router.get(
    "/{copacker_id}",
    response_model=CopackerResponse,
    summary="Get co-packer details",
)
async def get_copacker(
    copacker_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific co-packer."""
    service = CopackerService(session, current_user.tenant_id)
    
    copacker = await service.get_copacker(copacker_id)
    if not copacker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Co-packer with ID {copacker_id} not found",
        )
    
    return copacker


@router.put(
    "/{copacker_id}",
    response_model=CopackerResponse,
    summary="Update co-packer",
)
async def update_copacker(
    copacker_id: uuid.UUID,
    data: CopackerUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update co-packer details."""
    service = CopackerService(session, current_user.tenant_id)
    
    try:
        copacker = await service.update_copacker(copacker_id, data)
        await session.commit()
        return copacker
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update co-packer: {str(e)}",
        )


@router.put(
    "/{copacker_id}/approve",
    response_model=CopackerResponse,
    summary="Approve co-packer",
)
async def approve_copacker(
    copacker_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Approve a co-packer for use."""
    service = CopackerService(session, current_user.tenant_id)
    
    try:
        copacker = await service.approve_copacker(copacker_id)
        await session.commit()
        return copacker
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve co-packer: {str(e)}",
        )


@router.get(
    "/{copacker_id}/performance",
    response_model=CopackerPerformanceResponse,
    summary="Get co-packer performance",
)
async def get_copacker_performance(
    copacker_id: uuid.UUID,
    period_start: datetime = Query(..., description="Performance period start date"),
    period_end: datetime = Query(..., description="Performance period end date"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get co-packer performance metrics for a time period."""
    service = CopackerService(session, current_user.tenant_id)
    
    try:
        performance = await service.get_copacker_performance(copacker_id, period_start, period_end)
        return performance
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get co-packer performance: {str(e)}",
        )


# Contract endpoints
@router.post(
    "/{copacker_id}/contracts",
    response_model=CopackerContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a contract",
)
async def create_contract(
    copacker_id: uuid.UUID,
    data: CopackerContractCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new co-packer contract."""
    # Ensure copacker_id matches
    if data.copacker_id != copacker_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Co-packer ID in path must match copacker_id in body",
        )
    
    service = CopackerContractService(session, current_user.tenant_id)
    
    try:
        contract = await service.create_contract(data)
        await session.commit()
        return contract
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contract: {str(e)}",
        )


@router.get(
    "/{copacker_id}/contracts",
    response_model=list[CopackerContractResponse],
    summary="List contracts for co-packer",
)
async def list_contracts_for_copacker(
    copacker_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List contracts for a specific co-packer."""
    service = CopackerContractService(session, current_user.tenant_id)
    
    try:
        contracts, total = await service.list_contracts(skip, limit, copacker_id, None, status)
        return contracts
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list contracts: {str(e)}",
        )


@router.get(
    "/contracts/{contract_id}",
    response_model=CopackerContractResponse,
    summary="Get contract details",
)
async def get_contract(
    contract_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific contract."""
    service = CopackerContractService(session, current_user.tenant_id)
    
    contract = await service.get_contract(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found",
        )
    
    return contract


@router.put(
    "/contracts/{contract_id}",
    response_model=CopackerContractResponse,
    summary="Update contract",
)
async def update_contract(
    contract_id: uuid.UUID,
    data: CopackerContractUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update contract details."""
    service = CopackerContractService(session, current_user.tenant_id)
    
    try:
        contract = await service.update_contract(contract_id, data)
        await session.commit()
        return contract
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contract: {str(e)}",
        )


@router.put(
    "/contracts/{contract_id}/activate",
    response_model=CopackerContractResponse,
    summary="Activate contract",
)
async def activate_contract(
    contract_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Activate a contract."""
    service = CopackerContractService(session, current_user.tenant_id)
    
    try:
        contract = await service.activate_contract(contract_id)
        await session.commit()
        return contract
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate contract: {str(e)}",
        )

