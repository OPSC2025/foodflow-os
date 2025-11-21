"""Retail API layer - REST endpoints."""

from fastapi import APIRouter

from . import osa, pos, promos, stores, waste

# Main Retail router
router = APIRouter(prefix="/api/v1/retail", tags=["Retail"])

# Include all sub-routers
router.include_router(stores.router)
router.include_router(pos.router)
router.include_router(waste.router)
router.include_router(osa.router)
router.include_router(promos.router)

__all__ = ["router"]

