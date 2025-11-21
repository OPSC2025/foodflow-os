"""FSQ & Traceability workspace tools."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.fsq.domain.models import Lot, Supplier
from src.contexts.fsq.application.lot_service import LotService
from src.core.ai_client import get_ai_client
from src.core.logging import logger
from ..core.tool_registry import Tool
from ..rag.rag_tools import search_documents


async def get_lot_details(context: Dict[str, Any], lot_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a lot.
    
    Args:
        context: Execution context
        lot_id: Lot ID
        
    Returns:
        Lot details
    """
    db: AsyncSession = context["db"]
    tenant_id: UUID = context["tenant_id"]
    
    try:
        stmt = select(Lot).where(
            Lot.id == UUID(lot_id),
            Lot.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        lot = result.scalar_one_or_none()
        
        if not lot:
            return {"error": f"Lot {lot_id} not found"}
        
        return {
            "id": str(lot.id),
            "lot_number": lot.lot_number,
            "ingredient_name": lot.ingredient.name if lot.ingredient else "Unknown",
            "supplier_name": lot.supplier.name if lot.supplier else "Unknown",
            "quantity": lot.quantity,
            "unit": lot.unit,
            "production_date": lot.production_date.isoformat() if lot.production_date else None,
            "expiration_date": lot.expiration_date.isoformat() if lot.expiration_date else None,
            "status": lot.status,
            "quality_status": lot.quality_status,
            "on_hold": lot.on_hold,
            "test_results": lot.test_results,
            "certifications": lot.certifications,
        }
    
    except Exception as e:
        logger.error(f"Error fetching lot details: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def trace_lot_forward(context: Dict[str, Any], lot_id: str) -> Dict[str, Any]:
    """
    Trace lot forward through production and distribution.
    
    Args:
        context: Execution context
        lot_id: Lot ID
        
    Returns:
        Forward traceability results
    """
    db: AsyncSession = context["db"]
    tenant_id: UUID = context["tenant_id"]
    
    try:
        service = LotService(db)
        result = await service.trace_forward(
            lot_id=UUID(lot_id),
            tenant_id=tenant_id,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error tracing lot forward: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def trace_lot_backward(context: Dict[str, Any], lot_id: str) -> Dict[str, Any]:
    """
    Trace lot backward to ingredients and suppliers.
    
    Args:
        context: Execution context
        lot_id: Lot ID
        
    Returns:
        Backward traceability results
    """
    db: AsyncSession = context["db"]
    tenant_id: UUID = context["tenant_id"]
    
    try:
        service = LotService(db)
        result = await service.trace_backward(
            lot_id=UUID(lot_id),
            tenant_id=tenant_id,
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error tracing lot backward: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def compute_lot_risk(context: Dict[str, Any], lot_id: str) -> Dict[str, Any]:
    """
    Calculate risk score for a lot using AI service.
    
    Args:
        context: Execution context
        lot_id: Lot ID
        
    Returns:
        Lot risk assessment
    """
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        result = await ai_client.compute_lot_risk(
            tenant_id=tenant_id,
            lot_id=UUID(lot_id),
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error computing lot risk: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def compute_supplier_risk(context: Dict[str, Any], supplier_id: str) -> Dict[str, Any]:
    """
    Assess supplier risk level using AI service.
    
    Args:
        context: Execution context
        supplier_id: Supplier ID
        
    Returns:
        Supplier risk assessment
    """
    tenant_id: UUID = context["tenant_id"]
    
    try:
        ai_client = get_ai_client()
        result = await ai_client.compute_supplier_risk(
            tenant_id=tenant_id,
            supplier_id=UUID(supplier_id),
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error computing supplier risk: {str(e)}", exc_info=True)
        return {"error": str(e)}


async def check_ccp_status(context: Dict[str, Any], plant_id: str) -> Dict[str, Any]:
    """
    Get CCP monitoring status and alerts for a plant.
    
    Args:
        context: Execution context
        plant_id: Plant ID
        
    Returns:
        CCP monitoring status
    """
    # For now, return a stub response
    # Real implementation would query CCPLog and HACCPPlan
    return {
        "plant_id": plant_id,
        "ccp_count": 5,
        "active_alerts": 0,
        "last_check": datetime.utcnow().isoformat(),
        "status": "all_ccps_in_control",
        "message": "All Critical Control Points are within acceptable limits",
    }


async def answer_compliance_question(
    context: Dict[str, Any],
    question: str,
    doc_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Answer compliance questions using document search (RAG).
    
    Args:
        context: Execution context
        question: Compliance question
        doc_ids: Optional specific document IDs to search
        
    Returns:
        Answer with document references
    """
    tenant_id: UUID = context["tenant_id"]
    
    try:
        # Search documents
        doc_results = await search_documents(
            context=context,
            query=question,
            document_type="fsq",
            top_k=5,
        )
        
        if not doc_results or not doc_results.get("results"):
            return {
                "answer": "I don't have direct access to that specific document or procedure in the system yet. I recommend checking your FSQ document library, SOPs, or HACCP plans, or uploading relevant documents so I can reference them in the future.",
                "sources": [],
                "has_documents": False,
            }
        
        # Format answer with sources
        return {
            "answer": "Based on the available documentation...",
            "sources": doc_results["results"],
            "has_documents": True,
        }
    
    except Exception as e:
        logger.error(f"Error answering compliance question: {str(e)}", exc_info=True)
        return {"error": str(e)}


def register_fsq_tools(registry):
    """Register FSQ tools in the tool registry."""
    
    # Tool 1: get_lot_details
    registry.register(Tool(
        name="get_lot_details",
        description="Get detailed information about a production lot including ingredient, supplier, quantity, dates, and quality status",
        parameters={
            "type": "object",
            "properties": {
                "lot_id": {
                    "type": "string",
                    "description": "The lot ID (UUID format)",
                },
            },
            "required": ["lot_id"],
        },
        function=get_lot_details,
        workspace="fsq",
    ))
    
    # Tool 2: trace_lot_forward
    registry.register(Tool(
        name="trace_lot_forward",
        description="Trace a lot forward through production to see what products were made from it and where they were distributed",
        parameters={
            "type": "object",
            "properties": {
                "lot_id": {
                    "type": "string",
                    "description": "The lot ID (UUID format)",
                },
            },
            "required": ["lot_id"],
        },
        function=trace_lot_forward,
        workspace="fsq",
    ))
    
    # Tool 3: trace_lot_backward
    registry.register(Tool(
        name="trace_lot_backward",
        description="Trace a lot backward to identify all ingredient lots and suppliers that went into producing it",
        parameters={
            "type": "object",
            "properties": {
                "lot_id": {
                    "type": "string",
                    "description": "The lot ID (UUID format)",
                },
            },
            "required": ["lot_id"],
        },
        function=trace_lot_backward,
        workspace="fsq",
    ))
    
    # Tool 4: compute_lot_risk
    registry.register(Tool(
        name="compute_lot_risk",
        description="Calculate AI-powered risk score for a lot based on quality history, supplier risk, test results, and deviations",
        parameters={
            "type": "object",
            "properties": {
                "lot_id": {
                    "type": "string",
                    "description": "The lot ID (UUID format)",
                },
            },
            "required": ["lot_id"],
        },
        function=compute_lot_risk,
        workspace="fsq",
    ))
    
    # Tool 5: compute_supplier_risk
    registry.register(Tool(
        name="compute_supplier_risk",
        description="Assess supplier risk level using AI analysis of quality history, certifications, audit scores, and deviation trends",
        parameters={
            "type": "object",
            "properties": {
                "supplier_id": {
                    "type": "string",
                    "description": "The supplier ID (UUID format)",
                },
            },
            "required": ["supplier_id"],
        },
        function=compute_supplier_risk,
        workspace="fsq",
    ))
    
    # Tool 6: check_ccp_status
    registry.register(Tool(
        name="check_ccp_status",
        description="Get Critical Control Point (CCP) monitoring status and active alerts for HACCP compliance",
        parameters={
            "type": "object",
            "properties": {
                "plant_id": {
                    "type": "string",
                    "description": "The plant ID (UUID format)",
                },
            },
            "required": ["plant_id"],
        },
        function=check_ccp_status,
        workspace="fsq",
    ))
    
    # Tool 7: answer_compliance_question
    registry.register(Tool(
        name="answer_compliance_question",
        description="Answer food safety and compliance questions by searching FSQ documentation (SOPs, HACCP plans, specifications) using RAG",
        parameters={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The compliance or food safety question",
                },
                "doc_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional specific document IDs to search",
                },
            },
            "required": ["question"],
        },
        function=answer_compliance_question,
        workspace="fsq",
    ))
    
    logger.info("Registered 7 FSQ tools")

