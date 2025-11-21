"""Planning API layer - REST endpoints."""

from fastapi import APIRouter

from . import forecasts, inventory, overview, production_plans, safety_stocks

# Main Planning router
router = APIRouter(prefix="/api/v1/planning", tags=["Planning"])

# Include all sub-routers
router.include_router(overview.router)
router.include_router(forecasts.router)
router.include_router(production_plans.router)
router.include_router(safety_stocks.router)
router.include_router(inventory.router)

__all__ = ["router"]

