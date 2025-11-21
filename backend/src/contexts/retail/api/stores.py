"""
Retail API router for stores and banners.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.application.store_service import BannerService, StoreService
from src.contexts.retail.domain.schemas import (
    BannerCreate,
    BannerResponse,
    BannerUpdate,
    StoreCreate,
    StoreResponse,
    StoreUpdate,
)
from src.core.database import get_db_session
from src.core.security import CurrentUser, get_current_active_user

router = APIRouter(tags=["Retail - Stores"])


# Banner endpoints
@router.post(
    "/banners",
    response_model=BannerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a banner",
)
async def create_banner(
    data: BannerCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new retail banner/chain."""
    service = BannerService(session, current_user.tenant_id)
    
    try:
        banner = await service.create_banner(data)
        await session.commit()
        return banner
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create banner: {str(e)}",
        )


@router.get(
    "/banners",
    response_model=list[BannerResponse],
    summary="List banners",
)
async def list_banners(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List banners with optional filters."""
    service = BannerService(session, current_user.tenant_id)
    
    try:
        banners, total = await service.list_banners(skip, limit, is_active)
        return banners
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list banners: {str(e)}",
        )


@router.get(
    "/banners/{banner_id}",
    response_model=BannerResponse,
    summary="Get banner details",
)
async def get_banner(
    banner_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific banner."""
    service = BannerService(session, current_user.tenant_id)
    
    banner = await service.get_banner(banner_id)
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Banner with ID {banner_id} not found",
        )
    
    return banner


@router.put(
    "/banners/{banner_id}",
    response_model=BannerResponse,
    summary="Update banner",
)
async def update_banner(
    banner_id: uuid.UUID,
    data: BannerUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update banner details."""
    service = BannerService(session, current_user.tenant_id)
    
    try:
        banner = await service.update_banner(banner_id, data)
        await session.commit()
        return banner
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update banner: {str(e)}",
        )


# Store endpoints
@router.post(
    "/stores",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a store",
)
async def create_store(
    data: StoreCreate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Create a new retail store."""
    service = StoreService(session, current_user.tenant_id)
    
    try:
        store = await service.create_store(data)
        await session.commit()
        return store
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create store: {str(e)}",
        )


@router.get(
    "/stores",
    response_model=list[StoreResponse],
    summary="List stores",
)
async def list_stores(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    banner_id: Optional[uuid.UUID] = Query(None, description="Filter by banner ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """List stores with optional filters."""
    service = StoreService(session, current_user.tenant_id)
    
    try:
        stores, total = await service.list_stores(skip, limit, banner_id, is_active)
        return stores
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list stores: {str(e)}",
        )


@router.get(
    "/stores/{store_id}",
    response_model=StoreResponse,
    summary="Get store details",
)
async def get_store(
    store_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Get detailed information about a specific store."""
    service = StoreService(session, current_user.tenant_id)
    
    store = await service.get_store(store_id)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store with ID {store_id} not found",
        )
    
    return store


@router.put(
    "/stores/{store_id}",
    response_model=StoreResponse,
    summary="Update store",
)
async def update_store(
    store_id: uuid.UUID,
    data: StoreUpdate,
    current_user: CurrentUser = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Update store details."""
    service = StoreService(session, current_user.tenant_id)
    
    try:
        store = await service.update_store(store_id, data)
        await session.commit()
        return store
    except ValueError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update store: {str(e)}",
        )

