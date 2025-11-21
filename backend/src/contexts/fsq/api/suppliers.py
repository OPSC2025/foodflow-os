"""
FSQ API router for suppliers.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.fsq.application.supplier_service import SupplierService
from src.contexts.fsq.domain.schemas import (
    SupplierCreate,
    SupplierResponse,
    SupplierUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a supplier",
)
async def create_supplier(
    data: SupplierCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Create a new supplier.
    """
    service = SupplierService(session, current_user.tenant_id)
    
    try:
        supplier = await service.create_supplier(data)
        await session.commit()
        return supplier
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create supplier: {str(e)}",
        )


@router.get(
    "",
    response_model=list[SupplierResponse],
    summary="List suppliers",
)
async def list_suppliers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_approved: Optional[bool] = Query(None, description="Filter by approval status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    List suppliers with optional filters.
    """
    service = SupplierService(session, current_user.tenant_id)
    
    try:
        suppliers, total = await service.list_suppliers(skip, limit, is_active, is_approved)
        return suppliers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list suppliers: {str(e)}",
        )


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Get supplier details",
)
async def get_supplier(
    supplier_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get detailed information about a specific supplier.
    """
    service = SupplierService(session, current_user.tenant_id)
    
    supplier = await service.get_supplier(supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )
    
    return supplier


@router.put(
    "/{supplier_id}",
    response_model=SupplierResponse,
    summary="Update supplier",
)
async def update_supplier(
    supplier_id: uuid.UUID,
    data: SupplierUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update supplier details.
    """
    service = SupplierService(session, current_user.tenant_id)
    
    try:
        supplier = await service.update_supplier(supplier_id, data)
        await session.commit()
        return supplier
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update supplier: {str(e)}",
        )


@router.put(
    "/{supplier_id}/approve",
    response_model=SupplierResponse,
    summary="Approve supplier",
)
async def approve_supplier(
    supplier_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Approve a supplier for use.
    """
    service = SupplierService(session, current_user.tenant_id)
    
    try:
        supplier = await service.approve_supplier(supplier_id, current_user.email)
        await session.commit()
        return supplier
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve supplier: {str(e)}",
        )


@router.put(
    "/{supplier_id}/risk-score",
    response_model=SupplierResponse,
    summary="Update supplier risk score",
)
async def update_supplier_risk_score(
    supplier_id: uuid.UUID,
    risk_score: float = Query(..., ge=0, le=100, description="Risk score (0-100)"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Update supplier risk score.
    
    Risk scores are used for supplier evaluation and monitoring.
    """
    service = SupplierService(session, current_user.tenant_id)
    
    try:
        supplier = await service.update_risk_score(supplier_id, risk_score)
        await session.commit()
        return supplier
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update risk score: {str(e)}",
        )

