"""
Copilot API Endpoints

Main orchestration layer for LLM-powered AI assistance.
Handles tool calling, conversation management, and response synthesis.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.logging import logger
from src.core.telemetry.service import TelemetryService
from .core.llm_client import get_llm_client
from .core.tool_registry import get_tool_registry
from .core.conversation import ConversationManager
from .prompts import get_system_prompt
from .domain.schemas import (
    CopilotRequest,
    CopilotResponse,
    ActionLink,
    FeedbackRequest,
)
from .tools import register_all_tools


# Initialize router
router = APIRouter(prefix="/copilot", tags=["Copilot"])

# Global tool registry (initialized on startup)
_tools_registered = False


def ensure_tools_registered():
    """Ensure tools are registered (call once on startup)."""
    global _tools_registered
    if not _tools_registered:
        registry = get_tool_registry()
        register_all_tools(registry)
        _tools_registered = True
        logger.info(f"Registered {registry.tool_count()} total tools across {len(registry.list_workspaces())} workspaces")


# Dependency to get current tenant (stub for now)
async def get_tenant_id() -> UUID:
    """Get current tenant ID from request context."""
    # TODO: Extract from JWT token
    return UUID("00000000-0000-0000-0000-000000000001")


# Dependency to get current user (stub for now)
async def get_current_user_id() -> UUID:
    """Get current user ID from request context."""
    # TODO: Extract from JWT token
    return UUID("00000000-0000-0000-0000-000000000002")


@router.post("", response_model=CopilotResponse)
async def copilot_chat(
    request: CopilotRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id),
) -> CopilotResponse:
    """
    Main Copilot endpoint for natural language interactions.
    
    This endpoint:
    1. Validates workspace and retrieves system prompt
    2. Creates or retrieves conversation
    3. Calls LLM with workspace-specific tools
    4. Executes any requested tools
    5. Synthesizes final response
    6. Logs interaction to telemetry
    
    Args:
        request: Copilot request with workspace, message, and context
        db: Database session
        tenant_id: Current tenant ID
        user_id: Current user ID
        
    Returns:
        Copilot response with answer, actions, and metadata
    """
    ensure_tools_registered()
    
    start_time = datetime.utcnow()
    tools_used = []
    
    try:
        # Validate workspace
        registry = get_tool_registry()
        if request.workspace not in registry.list_workspaces():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid workspace '{request.workspace}'. Valid options: {', '.join(registry.list_workspaces())}"
            )
        
        # Get system prompt for workspace
        system_prompt = get_system_prompt(request.workspace)
        
        # Initialize services
        conv_manager = ConversationManager(db)
        llm_client = get_llm_client()
        
        # Create or get conversation
        if request.conversation_id:
            conversation = await conv_manager.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            conversation = await conv_manager.create_conversation(
                tenant_id=tenant_id,
                user_id=user_id,
                workspace=request.workspace,
            )
        
        # Add user message
        await conv_manager.add_message(
            conversation_id=conversation.id,
            role="user",
            content=request.message,
        )
        
        # Build conversation context
        messages = await conv_manager.build_context(
            conversation_id=conversation.id,
            system_prompt=system_prompt,
        )
        
        # Get tools for this workspace
        functions = registry.get_workspace_functions(request.workspace)
        
        # Execute LLM with tool calling loop
        max_iterations = 5
        iteration = 0
        total_tokens = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Call LLM
            llm_response = await llm_client.chat_completion(
                messages=messages,
                functions=functions if functions else None,
                function_call="auto" if functions else "none",
            )
            
            total_tokens += llm_response["usage"]["total_tokens"]
            
            # Check if LLM wants to call a tool
            if llm_response.get("finish_reason") == "function_call" and llm_response.get("function_call"):
                function_call = llm_response["function_call"]
                tool_name = function_call["name"]
                tool_args = function_call["arguments"]
                
                logger.info(f"LLM calling tool: {tool_name}", extra={"args": tool_args})
                tools_used.append(tool_name)
                
                # Execute tool
                tool_context = {
                    "db": db,
                    "tenant_id": tenant_id,
                    "user_id": user_id,
                    "workspace": request.workspace,
                    "request_context": request.context or {},
                }
                
                tool_result = await registry.execute_tool(
                    tool_name=tool_name,
                    arguments=tool_args,
                    context=tool_context,
                )
                
                # Add function call and result to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": tool_name,
                        "arguments": str(tool_args),
                    }
                })
                
                messages.append({
                    "role": "function",
                    "name": tool_name,
                    "content": str(tool_result),
                })
                
                # Add to conversation history
                await conv_manager.add_message(
                    conversation_id=conversation.id,
                    role="function",
                    content=str(tool_result),
                    tools_used=[tool_name],
                )
                
                # Continue loop to get LLM's next response
                continue
            
            # LLM provided final answer
            answer = llm_response["message"]["content"]
            
            # Add assistant's final message
            await conv_manager.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
                tools_used=tools_used,
                tokens_used=total_tokens,
            )
            
            # Calculate duration
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Log to telemetry
            telemetry = TelemetryService(db)
            await telemetry.log_copilot_interaction(
                tenant_id=tenant_id,
                user_id=user_id,
                workspace=request.workspace,
                question=request.message,
                answer=answer,
                tools_used=tools_used,
                tokens_used=total_tokens,
                duration_ms=duration_ms,
                conversation_id=conversation.id,
            )
            
            # Generate action links (workspace-specific)
            actions = generate_action_links(request.workspace, tools_used, request.context)
            
            # Build response
            return CopilotResponse(
                conversation_id=conversation.id,
                answer=answer,
                actions=actions,
                tools_used=tools_used,
                tokens_used=total_tokens,
                duration_ms=duration_ms,
            )
        
        # Max iterations reached
        logger.warning(f"Max iterations reached for conversation {conversation.id}")
        
        answer = "I apologize, but I've reached the maximum number of steps for this request. Please try rephrasing your question or breaking it into smaller parts."
        
        await conv_manager.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            tools_used=tools_used,
        )
        
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return CopilotResponse(
            conversation_id=conversation.id,
            answer=answer,
            actions=[],
            tools_used=tools_used,
            tokens_used=total_tokens,
            duration_ms=duration_ms,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Copilot error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Copilot error: {str(e)}")


@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
) -> Dict[str, Any]:
    """
    Submit feedback on a Copilot response.
    
    Args:
        feedback: Feedback with rating and optional comment
        db: Database session
        tenant_id: Current tenant ID
        
    Returns:
        Confirmation message
    """
    try:
        telemetry = TelemetryService(db)
        
        await telemetry.record_copilot_feedback(
            conversation_id=feedback.conversation_id,
            rating=feedback.rating,
            feedback_text=feedback.feedback,
        )
        
        logger.info(
            f"Copilot feedback recorded",
            extra={
                "conversation_id": str(feedback.conversation_id),
                "rating": feedback.rating,
            }
        )
        
        return {
            "status": "success",
            "message": "Feedback recorded successfully",
        }
    
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}")


def generate_action_links(workspace: str, tools_used: list, context: Dict[str, Any]) -> list:
    """
    Generate workspace-specific action links for the UI.
    
    Args:
        workspace: Workspace name
        tools_used: Tools that were called
        context: Request context
        
    Returns:
        List of action links
    """
    actions = []
    
    if workspace == "plantops":
        if "get_line_status" in tools_used:
            actions.append(ActionLink(
                label="View Line Details",
                url=f"/plant-ops/lines/{context.get('line_id', '')}",
                icon="line-chart"
            ))
        if "analyze_scrap" in tools_used:
            actions.append(ActionLink(
                label="View Scrap Log",
                url=f"/plant-ops/scrap?line_id={context.get('line_id', '')}",
                icon="alert-triangle"
            ))
        if "get_money_leaks" in tools_used:
            actions.append(ActionLink(
                label="View Money Leaks Dashboard",
                url="/plant-ops/money-leaks",
                icon="dollar-sign"
            ))
    
    elif workspace == "fsq":
        if "trace_lot_backward" in tools_used or "trace_lot_forward" in tools_used:
            actions.append(ActionLink(
                label="View Lot Details",
                url=f"/fsq/lots/{context.get('lot_id', '')}",
                icon="package"
            ))
        if "compute_lot_risk" in tools_used:
            actions.append(ActionLink(
                label="View Risk Assessment",
                url=f"/fsq/risk/{context.get('lot_id', '')}",
                icon="shield"
            ))
    
    elif workspace == "planning":
        if "generate_forecast" in tools_used:
            actions.append(ActionLink(
                label="View Forecast",
                url="/planning/forecasts",
                icon="trending-up"
            ))
        if "generate_production_plan" in tools_used:
            actions.append(ActionLink(
                label="View Production Plan",
                url="/planning/plans",
                icon="calendar"
            ))
    
    elif workspace == "brand":
        if "compute_margin_bridge" in tools_used:
            actions.append(ActionLink(
                label="View Margin Analysis",
                url=f"/brand/margin/{context.get('brand_id', '')}",
                icon="bar-chart"
            ))
        if "evaluate_copacker" in tools_used:
            actions.append(ActionLink(
                label="View Co-packer Details",
                url=f"/brand/copackers/{context.get('copacker_id', '')}",
                icon="building"
            ))
    
    elif workspace == "retail":
        if "detect_osa_issues" in tools_used:
            actions.append(ActionLink(
                label="View OSA Dashboard",
                url="/retail/osa",
                icon="alert-circle"
            ))
        if "evaluate_promo" in tools_used:
            actions.append(ActionLink(
                label="View Promo Details",
                url=f"/retail/promos/{context.get('promo_id', '')}",
                icon="tag"
            ))
    
    return actions

