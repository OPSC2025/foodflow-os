"""Brand API layer - REST endpoints."""

from fastapi import APIRouter

from . import brands, copackers, documents, products, skus

# Main Brand router
router = APIRouter(prefix="/api/v1/brand", tags=["Brand"])

# Include all sub-routers
router.include_router(brands.router)
router.include_router(products.router)
router.include_router(skus.router)
router.include_router(copackers.router)
router.include_router(documents.router)

__all__ = ["router"]

