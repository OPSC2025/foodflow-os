"""
Retail API router for POS transactions.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.application.pos_service import POSService
from src.contexts.retail.domain.schemas import (
    POSTransactionBulkCreate,
    POSTransactionCreate,
    POSTransactionResponse,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/pos", tags=["Retail - POS"])


@router.post(
    "/transactions",
    response_model=POSTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create POS transaction",
)
async def create_pos_transaction(
    data: POSTransactionCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a single POS transaction."""
    service = POSService(session, current_user.tenant_id)
    
    try:
        transaction = await service.create_transaction(data)
        await session.commit()
        return transaction
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create POS transaction: {str(e)}",
        )


@router.post(
    "/transactions/bulk",
    response_model=list[POSTransactionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create POS transactions",
)
async def bulk_create_pos_transactions(
    data: POSTransactionBulkCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Bulk create POS transactions (for data loading)."""
    service = POSService(session, current_user.tenant_id)
    
    try:
        transactions = await service.bulk_create_transactions(data.transactions)
        await session.commit()
        return transactions
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create POS transactions: {str(e)}",
        )


@router.get(
    "/transactions",
    response_model=list[POSTransactionResponse],
    summary="List POS transactions",
)
async def list_pos_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    store_id: Optional[uuid.UUID] = Query(None, description="Filter by store ID"),
    sku_id: Optional[uuid.UUID] = Query(None, description="Filter by SKU ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List POS transactions with optional filters."""
    service = POSService(session, current_user.tenant_id)
    
    try:
        transactions, total = await service.list_transactions(
            skip, limit, store_id, sku_id, start_date, end_date
        )
        return transactions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list POS transactions: {str(e)}",
        )


@router.get(
    "/transactions/{transaction_id}",
    response_model=POSTransactionResponse,
    summary="Get POS transaction details",
)
async def get_pos_transaction(
    transaction_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific POS transaction."""
    service = POSService(session, current_user.tenant_id)
    
    transaction = await service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"POS transaction with ID {transaction_id} not found",
        )
    
    return transaction

