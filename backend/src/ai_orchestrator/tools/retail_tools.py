"""Retail workspace tools."""

from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.retail.domain.models import Store
from src.core.ai_client import get_ai_client
from src.core.logging import logger
from ..core.tool_registry import Tool


async def get_store_performance(
    context: Dict[str, Any],
    store_id: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """Get store performance metrics."""
    db: AsyncSession = context["db"]
    tenant_id: UUID = context["tenant_id"]
    
    try:
        stmt = select(Store).where(
            Store.id == UUID(store_id),
            Store.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        store = result.scalar_one_or_none()
        
        if not store:
            return {"error": f"Store {store_id} not found"}
        
        # Return stub performance data
        return {
            "store_id": str(store.id),
            "store_number": store.store_number,
            "name": store.name,
            "period": {"start": start_date, "end": end_date},
            "sales_units": 1250,
            "velocity_per_week": 42.5,
            "osa_pct": 94.2,
            "waste_pct": 3.1,
        }
    
    except Exception as e:
        logger.error(f"Error fetching store performance: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def forecast_retail_demand(
    context: Dict[str, Any],
    banner_id: str,
    store_ids: List[str],
    sku_ids: List[str],
    horizon_weeks: int,
) -> Dict[str, Any]:
    """Generate store-level demand forecast using AI service."""
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        result = await ai_client.forecast_retail_demand(
            tenant_id=tenant_id,
            banner_id=UUID(banner_id),
            store_ids=[UUID(s) for s in store_ids],
            sku_ids=sku_ids,
            horizon_weeks=horizon_weeks,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error forecasting retail demand: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def recommend_replenishment(
    context: Dict[str, Any],
    banner_id: str,
    store_ids: List[str],
    sku_ids: List[str],
) -> Dict[str, Any]:
    """Get optimal replenishment recommendations using AI service."""
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        result = await ai_client.recommend_replenishment(
            tenant_id=tenant_id,
            banner_id=UUID(banner_id),
            store_ids=[UUID(s) for s in store_ids] if store_ids else None,
            sku_ids=sku_ids if sku_ids else None,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error recommending replenishment: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def detect_osa_issues(
    context: Dict[str, Any],
    category_id: str = None,
    banner_id: str = None,
    min_severity: str = "medium",
) -> Dict[str, Any]:
    """Detect on-shelf availability issues using AI service."""
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        result = await ai_client.detect_osa_issues(
            tenant_id=tenant_id,
            category_id=category_id,
            banner_id=UUID(banner_id) if banner_id else None,
            min_severity=min_severity,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error detecting OSA issues: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def evaluate_promo(context: Dict[str, Any], promo_id: str) -> Dict[str, Any]:
    """Evaluate promotion effectiveness using AI service."""
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        result = await ai_client.evaluate_promo(
            tenant_id=tenant_id,
            promo_id=UUID(promo_id),
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error evaluating promo: {str(e)}", exc_info=True)
        return {"error": str(e)}


def register_retail_tools(registry):
    """Register Retail tools in the tool registry."""
    
    registry.register(Tool(
        name="get_store_performance",
        description="Get store-level performance metrics including sales, velocity, OSA%, and waste%",
        parameters={
            "type": "object",
            "properties": {
                "store_id": {"type": "string", "description": "Store ID (UUID)"},
                "start_date": {"type": "string", "description": "Start date (ISO format)"},
                "end_date": {"type": "string", "description": "End date (ISO format)"},
            },
            "required": ["store_id", "start_date", "end_date"],
        },
        function=get_store_performance,
        workspace="retail",
    ))
    
    registry.register(Tool(
        name="forecast_retail_demand",
        description="Generate AI-powered store-level demand forecast accounting for local trends and promotions",
        parameters={
            "type": "object",
            "properties": {
                "banner_id": {"type": "string", "description": "Banner/chain ID (UUID)"},
                "store_ids": {"type": "array", "items": {"type": "string"}, "description": "List of store IDs"},
                "sku_ids": {"type": "array", "items": {"type": "string"}, "description": "List of SKU IDs"},
                "horizon_weeks": {"type": "integer", "description": "Forecast horizon in weeks"},
            },
            "required": ["banner_id", "store_ids", "sku_ids", "horizon_weeks"],
        },
        function=forecast_retail_demand,
        workspace="retail",
    ))
    
    registry.register(Tool(
        name="recommend_replenishment",
        description="Get AI-powered replenishment recommendations balancing availability with freshness and waste",
        parameters={
            "type": "object",
            "properties": {
                "banner_id": {"type": "string", "description": "Banner/chain ID (UUID)"},
                "store_ids": {"type": "array", "items": {"type": "string"}, "description": "Optional store IDs"},
                "sku_ids": {"type": "array", "items": {"type": "string"}, "description": "Optional SKU IDs"},
            },
            "required": ["banner_id", "store_ids", "sku_ids"],
        },
        function=recommend_replenishment,
        workspace="retail",
    ))
    
    registry.register(Tool(
        name="detect_osa_issues",
        description="Detect on-shelf availability problems using AI pattern recognition across stores",
        parameters={
            "type": "object",
            "properties": {
                "category_id": {"type": "string", "description": "Optional category ID filter"},
                "banner_id": {"type": "string", "description": "Optional banner ID filter (UUID)"},
                "min_severity": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Minimum severity level",
                    "default": "medium",
                },
            },
        },
        function=detect_osa_issues,
        workspace="retail",
    ))
    
    registry.register(Tool(
        name="evaluate_promo",
        description="Evaluate promotion effectiveness calculating lift, ROI, cannibalization, and post-promo dip",
        parameters={
            "type": "object",
            "properties": {
                "promo_id": {"type": "string", "description": "Promotion ID (UUID)"},
            },
            "required": ["promo_id"],
        },
        function=evaluate_promo,
        workspace="retail",
    ))
    
    logger.info("Registered 5 Retail tools")

