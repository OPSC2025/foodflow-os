"""
Pydantic schemas for telemetry analytics API.

Defines request and response models for analytics endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class WorkspaceAnalyticsResponse(BaseModel):
    """Analytics for a workspace."""
    
    workspace: str = Field(..., description="Workspace name or 'all'")
    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")
    total_interactions: int = Field(..., description="Total Copilot interactions")
    unique_users: int = Field(..., description="Number of unique users")
    avg_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    avg_tokens_used: float = Field(..., description="Average tokens per interaction")
    tool_usage: Dict[str, int] = Field(..., description="Tool usage counts")
    avg_feedback_score: float = Field(..., description="Average user feedback score (1-5)")
    feedback_count: int = Field(..., description="Number of feedback submissions")


class SuggestionTypeAcceptance(BaseModel):
    """Acceptance rate for a suggestion type."""
    
    total: int = Field(..., description="Total suggestions of this type")
    applied: int = Field(..., description="Number applied")
    acceptance_rate: float = Field(..., description="Acceptance rate percentage")


class SuggestionAcceptanceResponse(BaseModel):
    """AI suggestion acceptance rate analytics."""
    
    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")
    total_suggestions: int = Field(..., description="Total suggestions made")
    applied_count: int = Field(..., description="Number of suggestions applied")
    acceptance_rate: float = Field(..., description="Overall acceptance rate percentage")
    by_type: Dict[str, SuggestionTypeAcceptance] = Field(..., description="Breakdown by suggestion type")


class ToolStats(BaseModel):
    """Statistics for a single tool."""
    
    usage_count: int = Field(..., description="Number of times tool was called")
    avg_duration_ms: float = Field(..., description="Average execution duration")


class ToolUsageStatsResponse(BaseModel):
    """Tool usage statistics."""
    
    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")
    tools: Dict[str, ToolStats] = Field(..., description="Tool statistics by tool name")
    total_tool_calls: int = Field(..., description="Total number of tool calls")


class TopUser(BaseModel):
    """Top user engagement metrics."""
    
    user_id: str = Field(..., description="User ID")
    interaction_count: int = Field(..., description="Number of interactions")
    avg_duration_ms: float = Field(..., description="Average interaction duration")
    avg_feedback_score: float = Field(..., description="Average feedback score")


class UserEngagementResponse(BaseModel):
    """User engagement metrics."""
    
    top_users: List[TopUser] = Field(..., description="Top users by interaction count")
    period_start: str = Field(..., description="Analysis period start (ISO format)")
    period_end: str = Field(..., description="Analysis period end (ISO format)")


class CostAnalyticsResponse(BaseModel):
    """AI cost analytics."""
    
    period_start: datetime = Field(..., description="Analysis period start")
    period_end: datetime = Field(..., description="Analysis period end")
    total_interactions: int = Field(..., description="Total interactions")
    total_tokens: int = Field(..., description="Total tokens consumed")
    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")
    cost_per_interaction: float = Field(..., description="Average cost per interaction")
    daily_average_cost: float = Field(..., description="Average daily cost")


class AnalyticsOverviewResponse(BaseModel):
    """Comprehensive analytics overview."""
    
    period_start: str = Field(..., description="Analysis period start")
    period_end: str = Field(..., description="Analysis period end")
    summary: Dict[str, any] = Field(..., description="Summary metrics")
    workspace_breakdown: Dict[str, any] = Field(..., description="Workspace analytics")
    top_tools: Dict[str, ToolStats] = Field(..., description="Top 10 tools")
    top_users: List[TopUser] = Field(..., description="Top 5 users")
    suggestions: Dict[str, any] = Field(..., description="Suggestion metrics")

