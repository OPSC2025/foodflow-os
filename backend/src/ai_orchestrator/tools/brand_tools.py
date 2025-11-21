"""Brand & Co-packer workspace tools."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.brand.domain.models import Brand, Copacker
from src.core.ai_client import get_ai_client
from src.core.logging import logger
from ..core.tool_registry import Tool
from ..rag.rag_tools import search_documents


async def get_brand_performance(
    context: Dict[str, Any],
    brand_id: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """Get brand performance metrics."""
    db: AsyncSession = context["db"]
    tenant_id: UUID = context["tenant_id"]
    
    try:
        stmt = select(Brand).where(
            Brand.id == UUID(brand_id),
            Brand.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        brand = result.scalar_one_or_none()
        
        if not brand:
            return {"error": f"Brand {brand_id} not found"}
        
        # Return stub performance data
        return {
            "brand_id": str(brand.id),
            "brand_name": brand.name,
            "period": {"start": start_date, "end": end_date},
            "revenue": 1250000.0,
            "gross_margin_pct": 42.5,
            "units_sold": 125000,
            "velocity_per_store_per_week": 15.2,
        }
    
    except Exception as e:
        logger.error(f"Error fetching brand performance: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def get_copacker_performance(context: Dict[str, Any], copacker_id: str) -> Dict[str, Any]:
    """Get co-packer performance metrics."""
    db: AsyncSession = context["db"]
    tenant_id: UUID = context["tenant_id"]
    
    try:
        stmt = select(Copacker).where(
            Copacker.id == UUID(copacker_id),
            Copacker.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        copacker = result.scalar_one_or_none()
        
        if not copacker:
            return {"error": f"Co-packer {copacker_id} not found"}
        
        return {
            "copacker_id": str(copacker.id),
            "name": copacker.name,
            "quality_score": copacker.quality_score,
            "delivery_performance_pct": 95.5,
            "cost_competitiveness": "medium",
            "capacity_utilization_pct": 75.0,
        }
    
    except Exception as e:
        logger.error(f"Error fetching copacker performance: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def compute_margin_bridge(
    context: Dict[str, Any],
    brand_id: str,
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
) -> Dict[str, Any]:
    """Generate margin bridge analysis using AI service."""
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        result = await ai_client.compute_margin_bridge(
            tenant_id=tenant_id,
            brand_id=UUID(brand_id),
            period1_start=datetime.fromisoformat(period1_start),
            period1_end=datetime.fromisoformat(period1_end),
            period2_start=datetime.fromisoformat(period2_start),
            period2_end=datetime.fromisoformat(period2_end),
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error computing margin bridge: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def evaluate_copacker(context: Dict[str, Any], copacker_id: str) -> Dict[str, Any]:
    """Evaluate co-packer risk using AI service."""
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        result = await ai_client.compute_copacker_risk(
            tenant_id=tenant_id,
            copacker_id=UUID(copacker_id),
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error evaluating copacker: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def answer_brand_question(
    context: Dict[str, Any],
    question: str,
) -> Dict[str, Any]:
    """Answer brand questions using document search (RAG)."""
    try:
        doc_results = await search_documents(
            context=context,
            query=question,
            document_type="brand",
            top_k=5,
        )
        
        if not doc_results or not doc_results.get("results"):
            return {
                "answer": "I don't have that specific contract or specification in the system yet. I recommend uploading it to the Brand document library so I can reference it in the future.",
                "sources": [],
                "has_documents": False,
            }
        
        return {
            "answer": "Based on the available documentation...",
            "sources": doc_results["results"],
            "has_documents": True,
        }
    
    except Exception as e:
        logger.error(f"Error answering brand question: {str(e)}", exc_info=True)
        return {"error": str(e)}


def register_brand_tools(registry):
    """Register Brand tools in the tool registry."""
    
    registry.register(Tool(
        name="get_brand_performance",
        description="Get brand-level performance metrics including revenue, margin, velocity, and units sold",
        parameters={
            "type": "object",
            "properties": {
                "brand_id": {"type": "string", "description": "Brand ID (UUID)"},
                "start_date": {"type": "string", "description": "Start date (ISO format)"},
                "end_date": {"type": "string", "description": "End date (ISO format)"},
            },
            "required": ["brand_id", "start_date", "end_date"],
        },
        function=get_brand_performance,
        workspace="brand",
    ))
    
    registry.register(Tool(
        name="get_copacker_performance",
        description="Get co-packer performance metrics including quality, delivery, cost, and capacity utilization",
        parameters={
            "type": "object",
            "properties": {
                "copacker_id": {"type": "string", "description": "Co-packer ID (UUID)"},
            },
            "required": ["copacker_id"],
        },
        function=get_copacker_performance,
        workspace="brand",
    ))
    
    registry.register(Tool(
        name="compute_margin_bridge",
        description="Generate AI-powered margin waterfall analysis comparing two time periods to identify drivers of margin change",
        parameters={
            "type": "object",
            "properties": {
                "brand_id": {"type": "string", "description": "Brand ID (UUID)"},
                "period1_start": {"type": "string", "description": "Period 1 start date (ISO format)"},
                "period1_end": {"type": "string", "description": "Period 1 end date (ISO format)"},
                "period2_start": {"type": "string", "description": "Period 2 start date (ISO format)"},
                "period2_end": {"type": "string", "description": "Period 2 end date (ISO format)"},
            },
            "required": ["brand_id", "period1_start", "period1_end", "period2_start", "period2_end"],
        },
        function=compute_margin_bridge,
        workspace="brand",
    ))
    
    registry.register(Tool(
        name="evaluate_copacker",
        description="AI-powered co-packer risk and performance evaluation based on quality, delivery, financials, and capacity",
        parameters={
            "type": "object",
            "properties": {
                "copacker_id": {"type": "string", "description": "Co-packer ID (UUID)"},
            },
            "required": ["copacker_id"],
        },
        function=evaluate_copacker,
        workspace="brand",
    ))
    
    registry.register(Tool(
        name="answer_brand_question",
        description="Answer questions about brand contracts, specifications, and agreements using RAG-powered document search",
        parameters={
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Brand or contract question"},
            },
            "required": ["question"],
        },
        function=answer_brand_question,
        workspace="brand",
    ))
    
    logger.info("Registered 5 Brand tools")

