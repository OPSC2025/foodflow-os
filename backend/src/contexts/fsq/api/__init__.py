"""FSQ API layer - REST endpoints."""

from fastapi import APIRouter

from . import capas, deviations, documents, lots, suppliers

# Main FSQ router
router = APIRouter(prefix="/api/v1/fsq", tags=["FSQ"])

# Include all sub-routers
router.include_router(lots.router)
router.include_router(suppliers.router)
router.include_router(deviations.router)
router.include_router(capas.router)
router.include_router(documents.router)

__all__ = ["router"]
