"""PlantOps workspace tools."""

from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.plant_ops.domain.models import ProductionLine, Batch
from src.contexts.plant_ops.application.money_leak_service import MoneyLeakService
from src.core.ai_client import get_ai_client
from src.core.logging import logger
from ..core.tool_registry import Tool


async def get_line_status(context: Dict[str, Any], line_id: str) -> Dict[str, Any]:
    """
    Get current status and metrics for a production line.
    
    Args:
        context: Execution context with db, tenant_id, etc.
        line_id: Production line ID
        
    Returns:
        Line status with current metrics
    """
    db: AsyncSession = context["db"]
    tenant_id: UUID = context["tenant_id"]
    
    try:
        # Fetch line
        stmt = select(ProductionLine).where(
            ProductionLine.id == UUID(line_id),
            ProductionLine.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        line = result.scalar_one_or_none()
        
        if not line:
            return {"error": f"Line {line_id} not found"}
        
        # Get recent batches
        recent_batches_stmt = (
            select(Batch)
            .where(
                Batch.line_id == line.id,
                Batch.tenant_id == tenant_id,
            )
            .order_by(Batch.created_at.desc())
            .limit(5)
        )
        recent_result = await db.execute(recent_batches_stmt)
        recent_batches = list(recent_result.scalars().all())
        
        return {
            "line_id": str(line.id),
            "name": line.name,
            "status": line.status,
            "plant_name": line.plant.name if line.plant else "Unknown",
            "current_efficiency": line.efficiency_pct,
            "target_rate": line.target_rate_per_hour,
            "recent_batches": [
                {
                    "id": str(b.id),
                    "product_code": b.product_code,
                    "status": b.status,
                    "quantity": b.quantity_produced or 0,
                    "started_at": b.start_time.isoformat() if b.start_time else None,
                }
                for b in recent_batches
            ],
        }
    
    except Exception as e:
        logger.error(f"Error fetching line status: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def get_batch_details(context: Dict[str, Any], batch_id: str) -> Dict[str, Any]:
    """
    Retrieve detailed information about a batch.
    
    Args:
        context: Execution context
        batch_id: Batch ID
        
    Returns:
        Detailed batch information
    """
    db: AsyncSession = context["db"]
    tenant_id: UUID = context["tenant_id"]
    
    try:
        stmt = select(Batch).where(
            Batch.id == UUID(batch_id),
            Batch.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        batch = result.scalar_one_or_none()
        
        if not batch:
            return {"error": f"Batch {batch_id} not found"}
        
        return {
            "id": str(batch.id),
            "batch_number": batch.batch_number,
            "product_code": batch.product_code,
            "status": batch.status,
            "line_name": batch.line.name if batch.line else "Unknown",
            "quantity_planned": batch.quantity_planned,
            "quantity_produced": batch.quantity_produced,
            "yield_pct": ((batch.quantity_produced / batch.quantity_planned * 100) 
                          if batch.quantity_planned and batch.quantity_produced else 0),
            "start_time": batch.start_time.isoformat() if batch.start_time else None,
            "end_time": batch.end_time.isoformat() if batch.end_time else None,
            "duration_minutes": (
                (batch.end_time - batch.start_time).total_seconds() / 60
                if batch.start_time and batch.end_time else None
            ),
            "notes": batch.notes,
        }
    
    except Exception as e:
        logger.error(f"Error fetching batch details: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def analyze_scrap(
    context: Dict[str, Any],
    plant_id: str,
    line_id: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """
    Analyze scrap patterns using AI service.
    
    Args:
        context: Execution context
        plant_id: Plant ID
        line_id: Line ID
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        
    Returns:
        Scrap analysis from AI service
    """
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        
        result = await ai_client.analyze_scrap(
            tenant_id=tenant_id,
            plant_id=UUID(plant_id),
            line_id=UUID(line_id),
            start_date=datetime.fromisoformat(start_date),
            end_date=datetime.fromisoformat(end_date),
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing scrap: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def suggest_trial(
    context: Dict[str, Any],
    line_id: str,
    sku_id: str,
    current_parameters: Dict[str, Any],
    optimization_goal: str = "reduce_scrap",
) -> Dict[str, Any]:
    """
    Get trial parameter recommendations from AI service.
    
    Args:
        context: Execution context
        line_id: Line ID
        sku_id: SKU/Product ID
        current_parameters: Current line parameters
        optimization_goal: Goal (reduce_scrap, increase_speed, improve_quality)
        
    Returns:
        Trial suggestions from AI service
    """
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        
        result = await ai_client.suggest_trial(
            tenant_id=tenant_id,
            line_id=UUID(line_id),
            sku_id=sku_id,
            current_parameters=current_parameters,
            optimization_goal=optimization_goal,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error suggesting trial: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def get_money_leaks(
    context: Dict[str, Any],
    plant_id: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """
    Get money leak breakdown by category.
    
    Args:
        context: Execution context
        plant_id: Plant ID
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        
    Returns:
        Money leaks by category
    """
    db: AsyncSession = context["db"]
    tenant_id: UUID = context["tenant_id"]
    
    try:
        service = MoneyLeakService(db)
        
        summary = await service.get_summary(
            tenant_id=tenant_id,
            plant_id=UUID(plant_id),
            start_date=datetime.fromisoformat(start_date),
            end_date=datetime.fromisoformat(end_date),
        )
        
        return summary
    
    except Exception as e:
        logger.error(f"Error fetching money leaks: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def compare_batch(context: Dict[str, Any], batch_id: str) -> Dict[str, Any]:
    """
    Compare batch to similar historical batches using AI service.
    
    Args:
        context: Execution context
        batch_id: Batch ID
        
    Returns:
        Batch comparison from AI service
    """
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        
        result = await ai_client.compare_batch(
            tenant_id=tenant_id,
            batch_id=UUID(batch_id),
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error comparing batch: {str(e)}", exc_info=True)
        return {"error": str(e)}


def register_plantops_tools(registry):
    """Register PlantOps tools in the tool registry."""
    
    # Tool 1: get_line_status
    registry.register(Tool(
        name="get_line_status",
        description="Get current status and real-time metrics for a production line including efficiency, recent batches, and operational state",
        parameters={
            "type": "object",
            "properties": {
                "line_id": {
                    "type": "string",
                    "description": "The production line ID (UUID format)",
                },
            },
            "required": ["line_id"],
        },
        function=get_line_status,
        workspace="plantops",
    ))
    
    # Tool 2: get_batch_details
    registry.register(Tool(
        name="get_batch_details",
        description="Retrieve detailed information about a specific production batch including quantities, yield, timing, and status",
        parameters={
            "type": "object",
            "properties": {
                "batch_id": {
                    "type": "string",
                    "description": "The batch ID (UUID format)",
                },
            },
            "required": ["batch_id"],
        },
        function=get_batch_details,
        workspace="plantops",
    ))
    
    # Tool 3: analyze_scrap
    registry.register(Tool(
        name="analyze_scrap",
        description="Analyze scrap patterns and identify root causes using AI-powered analytics for a production line over a date range",
        parameters={
            "type": "object",
            "properties": {
                "plant_id": {
                    "type": "string",
                    "description": "The plant ID (UUID format)",
                },
                "line_id": {
                    "type": "string",
                    "description": "The production line ID (UUID format)",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO format (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO format (YYYY-MM-DD)",
                },
            },
            "required": ["plant_id", "line_id", "start_date", "end_date"],
        },
        function=analyze_scrap,
        workspace="plantops",
    ))
    
    # Tool 4: suggest_trial
    registry.register(Tool(
        name="suggest_trial",
        description="Get AI-powered trial parameter recommendations to optimize line performance (reduce scrap, increase speed, improve quality)",
        parameters={
            "type": "object",
            "properties": {
                "line_id": {
                    "type": "string",
                    "description": "The production line ID (UUID format)",
                },
                "sku_id": {
                    "type": "string",
                    "description": "The SKU/product code",
                },
                "current_parameters": {
                    "type": "object",
                    "description": "Current line parameters (temperature, speed, pressure, etc.)",
                },
                "optimization_goal": {
                    "type": "string",
                    "enum": ["reduce_scrap", "increase_speed", "improve_quality"],
                    "description": "Optimization objective",
                    "default": "reduce_scrap",
                },
            },
            "required": ["line_id", "sku_id", "current_parameters"],
        },
        function=suggest_trial,
        workspace="plantops",
    ))
    
    # Tool 5: get_money_leaks
    registry.register(Tool(
        name="get_money_leaks",
        description="Get money leak breakdown by category (scrap cost, downtime cost, yield loss) for a plant over a date range",
        parameters={
            "type": "object",
            "properties": {
                "plant_id": {
                    "type": "string",
                    "description": "The plant ID (UUID format)",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in ISO format (YYYY-MM-DD)",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in ISO format (YYYY-MM-DD)",
                },
            },
            "required": ["plant_id", "start_date", "end_date"],
        },
        function=get_money_leaks,
        workspace="plantops",
    ))
    
    # Tool 6: compare_batch
    registry.register(Tool(
        name="compare_batch",
        description="Compare a batch to similar historical batches using AI to identify deviations and insights",
        parameters={
            "type": "object",
            "properties": {
                "batch_id": {
                    "type": "string",
                    "description": "The batch ID (UUID format)",
                },
            },
            "required": ["batch_id"],
        },
        function=compare_batch,
        workspace="plantops",
    ))
    
    logger.info("Registered 6 PlantOps tools")

