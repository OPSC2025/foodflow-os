"""
PlantOps API router initialization.

Aggregates all PlantOps-related API endpoints.
"""

from fastapi import APIRouter

from . import batches, downtimes, lines, money_leaks, overview, sensors, trials

# Create main PlantOps router
router = APIRouter()

# Include all sub-routers
router.include_router(overview.router)
router.include_router(lines.router)
router.include_router(batches.router)
router.include_router(trials.router)
router.include_router(downtimes.router)
router.include_router(money_leaks.router)
router.include_router(sensors.router)

__all__ = ["router"]

