"""Planning & Supply workspace tools."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.planning.domain.models import Forecast, ProductionPlan
from src.core.ai_client import get_ai_client
from src.core.logging import logger
from ..core.tool_registry import Tool


async def get_forecast(context: Dict[str, Any], forecast_id: str) -> Dict[str, Any]:
    """
    Retrieve a demand forecast.
    
    Args:
        context: Execution context
        forecast_id: Forecast ID
        
    Returns:
        Forecast details
    """
    db: AsyncSession = context["db"]
    tenant_id: UUID = context["tenant_id"]
    
    try:
        stmt = select(Forecast).where(
            Forecast.id == UUID(forecast_id),
            Forecast.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        forecast = result.scalar_one_or_none()
        
        if not forecast:
            return {"error": f"Forecast {forecast_id} not found"}
        
        return {
            "id": str(forecast.id),
            "name": forecast.name,
            "horizon_weeks": forecast.horizon_weeks,
            "status": forecast.status,
            "created_at": forecast.created_at.isoformat(),
            "forecast_data": forecast.forecast_data,
            "accuracy_metrics": forecast.accuracy_metrics,
        }
    
    except Exception as e:
        logger.error(f"Error fetching forecast: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def get_production_plans(context: Dict[str, Any], limit: int = 10) -> Dict[str, Any]:
    """
    List production plans.
    
    Args:
        context: Execution context
        limit: Maximum number of plans to return
        
    Returns:
        List of production plans
    """
    db: AsyncSession = context["db"]
    tenant_id: UUID = context["tenant_id"]
    
    try:
        stmt = (
            select(ProductionPlan)
            .where(ProductionPlan.tenant_id == tenant_id)
            .order_by(ProductionPlan.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        plans = list(result.scalars().all())
        
        return {
            "plans": [
                {
                    "id": str(plan.id),
                    "name": plan.name,
                    "status": plan.status,
                    "horizon_weeks": plan.horizon_weeks,
                    "start_date": plan.start_date.isoformat() if plan.start_date else None,
                    "end_date": plan.end_date.isoformat() if plan.end_date else None,
                    "created_at": plan.created_at.isoformat(),
                }
                for plan in plans
            ],
            "count": len(plans),
        }
    
    except Exception as e:
        logger.error(f"Error fetching production plans: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def generate_forecast(
    context: Dict[str, Any],
    horizon_weeks: int,
    grouping: str,
    sku_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate AI-powered demand forecast.
    
    Args:
        context: Execution context
        horizon_weeks: Forecast horizon in weeks
        grouping: Grouping level (sku, category, plant)
        sku_ids: Optional list of SKU IDs
        
    Returns:
        Generated forecast
    """
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        result = await ai_client.generate_forecast(
            tenant_id=tenant_id,
            horizon_weeks=horizon_weeks,
            grouping=grouping,
            sku_ids=sku_ids,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating forecast: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def generate_production_plan(
    context: Dict[str, Any],
    forecast_version_id: str,
    horizon_weeks: int,
    plant_ids: List[str],
) -> Dict[str, Any]:
    """
    Generate optimized production plan.
    
    Args:
        context: Execution context
        forecast_version_id: Base forecast ID
        horizon_weeks: Planning horizon
        plant_ids: List of plant IDs to include
        
    Returns:
        Generated production plan
    """
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        result = await ai_client.generate_production_plan(
            tenant_id=tenant_id,
            forecast_version_id=UUID(forecast_version_id),
            horizon_weeks=horizon_weeks,
            plant_ids=[UUID(p) for p in plant_ids],
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error generating production plan: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def recommend_safety_stocks(
    context: Dict[str, Any],
    sku_ids: List[str],
    location_ids: List[str],
) -> Dict[str, Any]:
    """
    Get AI recommendations for safety stock levels.
    
    Args:
        context: Execution context
        sku_ids: List of SKU IDs
        location_ids: List of location IDs
        
    Returns:
        Safety stock recommendations
    """
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        result = await ai_client.recommend_safety_stocks(
            tenant_id=tenant_id,
            sku_ids=sku_ids,
            location_ids=[UUID(l) for l in location_ids],
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error recommending safety stocks: {str(e)}", exc_info=True)
        return {"error": str(e)}


def register_planning_tools(registry):
    """Register Planning tools in the tool registry."""
    
    registry.register(Tool(
        name="get_forecast",
        description="Retrieve a demand forecast with baseline, confidence intervals, and accuracy metrics",
        parameters={
            "type": "object",
            "properties": {
                "forecast_id": {
                    "type": "string",
                    "description": "The forecast ID (UUID format)",
                },
            },
            "required": ["forecast_id"],
        },
        function=get_forecast,
        workspace="planning",
    ))
    
    registry.register(Tool(
        name="get_production_plans",
        description="List recent production plans with status, dates, and horizon",
        parameters={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of plans to return",
                    "default": 10,
                },
            },
        },
        function=get_production_plans,
        workspace="planning",
    ))
    
    registry.register(Tool(
        name="generate_forecast",
        description="Generate AI-powered demand forecast for specified horizon and grouping level",
        parameters={
            "type": "object",
            "properties": {
                "horizon_weeks": {
                    "type": "integer",
                    "description": "Forecast horizon in weeks",
                },
                "grouping": {
                    "type": "string",
                    "enum": ["sku", "category", "plant"],
                    "description": "Forecast grouping level",
                },
                "sku_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of specific SKU IDs",
                },
            },
            "required": ["horizon_weeks", "grouping"],
        },
        function=generate_forecast,
        workspace="planning",
    ))
    
    registry.register(Tool(
        name="generate_production_plan",
        description="Generate optimized production plan from forecast using AI-powered scheduling and capacity optimization",
        parameters={
            "type": "object",
            "properties": {
                "forecast_version_id": {
                    "type": "string",
                    "description": "Base forecast ID (UUID format)",
                },
                "horizon_weeks": {
                    "type": "integer",
                    "description": "Planning horizon in weeks",
                },
                "plant_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of plant IDs to include in plan",
                },
            },
            "required": ["forecast_version_id", "horizon_weeks", "plant_ids"],
        },
        function=generate_production_plan,
        workspace="planning",
    ))
    
    registry.register(Tool(
        name="recommend_safety_stocks",
        description="Get AI-powered safety stock recommendations based on demand variability and lead times",
        parameters={
            "type": "object",
            "properties": {
                "sku_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of SKU IDs",
                },
                "location_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of location IDs (UUIDs)",
                },
            },
            "required": ["sku_ids", "location_ids"],
        },
        function=recommend_safety_stocks,
        workspace="planning",
    ))
    
    logger.info("Registered 5 Planning tools")

