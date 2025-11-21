"""
Telemetry Analytics API

Provides endpoints for querying AI/Copilot telemetry data and analytics.
These endpoints enable ROI measurement, usage tracking, and system optimization.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.telemetry.service import TelemetryService
from src.core.telemetry.schemas import (
    WorkspaceAnalyticsResponse,
    SuggestionAcceptanceResponse,
    ToolUsageStatsResponse,
    UserEngagementResponse,
    CostAnalyticsResponse,
)


router = APIRouter(prefix="/analytics", tags=["Analytics"])


# Dependency stubs - in production, extract from JWT
async def get_tenant_id() -> UUID:
    """Get current tenant ID from request context."""
    # TODO: Extract from JWT token
    return UUID("00000000-0000-0000-0000-000000000001")


@router.get("/workspace", response_model=WorkspaceAnalyticsResponse)
async def get_workspace_analytics(
    workspace: Optional[str] = Query(None, description="Specific workspace (plantops, fsq, planning, brand, retail) or None for all"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """
    Get Copilot usage analytics for workspace(s).
    
    Returns metrics including:
    - Total interactions
    - Unique users
    - Average response time
    - Token usage
    - Tool usage distribution
    - Feedback scores
    
    Example:
    GET /api/v1/analytics/workspace?workspace=plantops&start_date=2024-11-01
    """
    telemetry = TelemetryService(db)
    
    analytics = await telemetry.get_workspace_analytics(
        tenant_id=tenant_id,
        workspace=workspace,
        start_date=start_date or datetime.utcnow() - timedelta(days=30),
        end_date=end_date or datetime.utcnow(),
    )
    
    return WorkspaceAnalyticsResponse(
        workspace=workspace or "all",
        period_start=start_date or datetime.utcnow() - timedelta(days=30),
        period_end=end_date or datetime.utcnow(),
        **analytics
    )


@router.get("/suggestions/acceptance", response_model=SuggestionAcceptanceResponse)
async def get_suggestion_acceptance_rate(
    suggestion_type: Optional[str] = Query(None, description="Filter by suggestion type"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """
    Get AI suggestion acceptance rate.
    
    This metric is critical for demonstrating ROI:
    - Shows what % of AI suggestions are applied by users
    - Breaks down by suggestion type
    - Tracks actual business impact
    
    Example:
    GET /api/v1/analytics/suggestions/acceptance
    
    Response shows: "80% of AI suggestions were applied"
    """
    telemetry = TelemetryService(db)
    
    acceptance_data = await telemetry.get_suggestion_acceptance_rate(
        tenant_id=tenant_id,
        suggestion_type=suggestion_type,
        start_date=start_date or datetime.utcnow() - timedelta(days=30),
        end_date=end_date or datetime.utcnow(),
    )
    
    return SuggestionAcceptanceResponse(
        period_start=start_date or datetime.utcnow() - timedelta(days=30),
        period_end=end_date or datetime.utcnow(),
        **acceptance_data
    )


@router.get("/tools/usage", response_model=ToolUsageStatsResponse)
async def get_tool_usage_stats(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """
    Get tool usage statistics.
    
    Shows which Copilot tools are most frequently used.
    Helps prioritize which tools to enhance with real ML models.
    
    Returns:
    - Tool usage counts
    - Average execution duration per tool
    - Total tool calls
    
    Example:
    GET /api/v1/analytics/tools/usage
    """
    telemetry = TelemetryService(db)
    
    tool_stats = await telemetry.get_tool_usage_stats(
        tenant_id=tenant_id,
        start_date=start_date or datetime.utcnow() - timedelta(days=30),
        end_date=end_date or datetime.utcnow(),
    )
    
    return ToolUsageStatsResponse(
        period_start=start_date or datetime.utcnow() - timedelta(days=30),
        period_end=end_date or datetime.utcnow(),
        **tool_stats
    )


@router.get("/users/engagement", response_model=UserEngagementResponse)
async def get_user_engagement(
    limit: int = Query(10, ge=1, le=100, description="Number of top users to return"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """
    Get user engagement metrics.
    
    Shows which users are most engaged with Copilot.
    Helps identify:
    - Power users who love the system
    - Users who need training
    - Adoption patterns
    
    Example:
    GET /api/v1/analytics/users/engagement?limit=20
    """
    telemetry = TelemetryService(db)
    
    engagement_data = await telemetry.get_user_engagement(
        tenant_id=tenant_id,
        start_date=start_date or datetime.utcnow() - timedelta(days=30),
        end_date=end_date or datetime.utcnow(),
        limit=limit,
    )
    
    return UserEngagementResponse(**engagement_data)


@router.get("/cost", response_model=CostAnalyticsResponse)
async def get_cost_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """
    Get AI cost analytics.
    
    Calculates estimated costs for AI/LLM usage based on:
    - Token consumption
    - Model pricing (GPT-4, embeddings, etc.)
    - Usage trends
    
    Helps with budgeting and cost optimization.
    
    Example:
    GET /api/v1/analytics/cost?start_date=2024-11-01
    """
    from src.core.telemetry.models import CopilotInteraction
    from sqlalchemy import select, func
    
    # Calculate costs from token usage
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Query for token usage
    query = select(
        func.sum(CopilotInteraction.tokens_used).label("total_tokens"),
        func.count(CopilotInteraction.id).label("total_interactions"),
    ).where(
        CopilotInteraction.tenant_id == tenant_id,
        CopilotInteraction.created_at >= start_date,
        CopilotInteraction.created_at <= end_date,
        CopilotInteraction.tokens_used.isnot(None),
    )
    
    result = await db.execute(query)
    row = result.one_or_none()
    
    if not row or not row.total_tokens:
        return CostAnalyticsResponse(
            period_start=start_date,
            period_end=end_date,
            total_interactions=0,
            total_tokens=0,
            estimated_cost_usd=0.0,
            cost_per_interaction=0.0,
            daily_average_cost=0.0,
        )
    
    total_tokens = row.total_tokens
    total_interactions = row.total_interactions
    
    # Estimate costs (GPT-4 Turbo pricing: ~$0.01/1K input, ~$0.03/1K output)
    # Conservative estimate: assume 40% input, 60% output
    input_tokens = total_tokens * 0.4
    output_tokens = total_tokens * 0.6
    
    input_cost = (input_tokens / 1000) * 0.01
    output_cost = (output_tokens / 1000) * 0.03
    total_cost = input_cost + output_cost
    
    cost_per_interaction = total_cost / total_interactions if total_interactions else 0
    
    # Daily average
    days = (end_date - start_date).days or 1
    daily_average = total_cost / days
    
    return CostAnalyticsResponse(
        period_start=start_date,
        period_end=end_date,
        total_interactions=total_interactions,
        total_tokens=total_tokens,
        estimated_cost_usd=round(total_cost, 2),
        cost_per_interaction=round(cost_per_interaction, 4),
        daily_average_cost=round(daily_average, 2),
    )


@router.get("/overview")
async def get_analytics_overview(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """
    Get comprehensive analytics overview.
    
    Combines all key metrics into a single dashboard response:
    - Workspace usage
    - Top tools
    - Suggestion acceptance
    - Cost estimates
    - Top users
    
    Perfect for executive dashboards and reports.
    
    Example:
    GET /api/v1/analytics/overview
    """
    telemetry = TelemetryService(db)
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # Gather all analytics in parallel
    workspace_analytics = await telemetry.get_workspace_analytics(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    tool_usage = await telemetry.get_tool_usage_stats(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    suggestion_acceptance = await telemetry.get_suggestion_acceptance_rate(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
    )
    
    user_engagement = await telemetry.get_user_engagement(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        limit=5,
    )
    
    # Get top 10 tools
    top_tools = dict(list(tool_usage["tools"].items())[:10])
    
    return {
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "summary": {
            "total_interactions": workspace_analytics["total_interactions"],
            "unique_users": workspace_analytics["unique_users"],
            "avg_feedback_score": workspace_analytics["avg_feedback_score"],
            "suggestion_acceptance_rate": suggestion_acceptance["acceptance_rate"],
        },
        "workspace_breakdown": workspace_analytics,
        "top_tools": top_tools,
        "top_users": user_engagement["top_users"],
        "suggestions": {
            "total": suggestion_acceptance["total_suggestions"],
            "applied": suggestion_acceptance["applied_count"],
            "acceptance_rate": suggestion_acceptance["acceptance_rate"],
        },
    }

