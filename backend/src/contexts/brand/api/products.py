"""
Brand API router for products and SKUs.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.brand.application.product_service import ProductService, SKUService
from src.contexts.brand.domain.schemas import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    SKUCreate,
    SKUResponse,
    SKUUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
async def create_product(
    data: ProductCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new product."""
    service = ProductService(session, current_user.tenant_id)
    
    try:
        product = await service.create_product(data)
        await session.commit()
        return product
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create product: {str(e)}",
        )


@router.get(
    "",
    response_model=list[ProductResponse],
    summary="List products",
)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    brand_id: Optional[uuid.UUID] = Query(None, description="Filter by brand ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List products with optional filters."""
    service = ProductService(session, current_user.tenant_id)
    
    try:
        products, total = await service.list_products(skip, limit, brand_id, status)
        return products
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list products: {str(e)}",
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product details",
)
async def get_product(
    product_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific product."""
    service = ProductService(session, current_user.tenant_id)
    
    product = await service.get_product(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )
    
    return product


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product",
)
async def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update product details."""
    service = ProductService(session, current_user.tenant_id)
    
    try:
        product = await service.update_product(product_id, data)
        await session.commit()
        return product
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update product: {str(e)}",
        )


@router.put(
    "/{product_id}/launch",
    response_model=ProductResponse,
    summary="Launch product",
)
async def launch_product(
    product_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Launch a product (move from development to active)."""
    service = ProductService(session, current_user.tenant_id)
    
    try:
        product = await service.launch_product(product_id)
        await session.commit()
        return product
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to launch product: {str(e)}",
        )


# SKU endpoints
@router.post(
    "/{product_id}/skus",
    response_model=SKUResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a SKU",
)
async def create_sku(
    product_id: uuid.UUID,
    data: SKUCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new SKU for a product."""
    # Ensure product_id matches
    if data.product_id != product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product ID in path must match product_id in body",
        )
    
    service = SKUService(session, current_user.tenant_id)
    
    try:
        sku = await service.create_sku(data)
        await session.commit()
        return sku
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create SKU: {str(e)}",
        )


@router.get(
    "/{product_id}/skus",
    response_model=list[SKUResponse],
    summary="List SKUs for product",
)
async def list_skus_for_product(
    product_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List SKUs for a specific product."""
    service = SKUService(session, current_user.tenant_id)
    
    try:
        skus, total = await service.list_skus(skip, limit, product_id, is_active)
        return skus
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list SKUs: {str(e)}",
        )

