"""
POS service - business logic for point-of-sale transactions.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.domain.models import POSTransaction
from src.contexts.retail.domain.schemas import (
    POSTransactionCreate,
    POSTransactionResponse,
)
from src.contexts.retail.infrastructure.repositories import POSTransactionRepository


class POSService:
    """Service for POS transaction operations."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = POSTransactionRepository(session, tenant_id)

    async def create_transaction(
        self, data: POSTransactionCreate
    ) -> POSTransactionResponse:
        """Create a single POS transaction."""
        transaction = POSTransaction(
            store_id=data.store_id,
            transaction_id=data.transaction_id,
            transaction_date=data.transaction_date,
            sku_id=data.sku_id,
            product_id=data.product_id,
            upc=data.upc,
            external_sku_id=data.external_sku_id,
            product_name=data.product_name,
            quantity_sold=data.quantity_sold,
            unit_price=data.unit_price,
            total_amount=data.total_amount,
            discount_amount=data.discount_amount or 0.0,
            net_amount=data.net_amount,
            promo_id=data.promo_id,
            metadata=data.metadata,
        )

        transaction = await self.repo.create(transaction)
        return POSTransactionResponse.model_validate(transaction)

    async def bulk_create_transactions(
        self, transactions_data: list[POSTransactionCreate]
    ) -> list[POSTransactionResponse]:
        """Bulk create POS transactions (for data loading)."""
        transactions = [
            POSTransaction(
                store_id=data.store_id,
                transaction_id=data.transaction_id,
                transaction_date=data.transaction_date,
                sku_id=data.sku_id,
                product_id=data.product_id,
                upc=data.upc,
                external_sku_id=data.external_sku_id,
                product_name=data.product_name,
                quantity_sold=data.quantity_sold,
                unit_price=data.unit_price,
                total_amount=data.total_amount,
                discount_amount=data.discount_amount or 0.0,
                net_amount=data.net_amount,
                promo_id=data.promo_id,
                metadata=data.metadata,
            )
            for data in transactions_data
        ]

        transactions = await self.repo.bulk_create(transactions)
        return [POSTransactionResponse.model_validate(t) for t in transactions]

    async def get_transaction(
        self, transaction_id: uuid.UUID
    ) -> Optional[POSTransactionResponse]:
        """Get POS transaction by ID."""
        transaction = await self.repo.get_by_id(transaction_id)
        if transaction:
            return POSTransactionResponse.model_validate(transaction)
        return None

    async def list_transactions(
        self,
        skip: int = 0,
        limit: int = 100,
        store_id: Optional[uuid.UUID] = None,
        sku_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[list[POSTransactionResponse], int]:
        """List POS transactions with filters."""
        transactions, total = await self.repo.list(
            skip, limit, store_id, sku_id, start_date, end_date
        )
        return (
            [POSTransactionResponse.model_validate(t) for t in transactions],
            total,
        )

