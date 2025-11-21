"""
AI Telemetry Service for logging and analyzing Copilot interactions.

This service provides APIs for:
- Logging Copilot interactions
- Recording AI suggestions and their outcomes
- Capturing user feedback
- Generating analytics and insights
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AIFeedback, AISuggestion, CopilotInteraction, WorkspaceAnalytics


class TelemetryService:
    """Service for AI telemetry logging and analytics."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize telemetry service.
        
        Args:
            session: Database session
        """
        self.session = session
    
    async def log_copilot_interaction(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        workspace: str,
        question: str,
        answer: str,
        tools_used: Optional[list[str]] = None,
        tokens_used: Optional[int] = None,
        duration_ms: Optional[int] = None,
        metadata: Optional[dict] = None,
    ) -> CopilotInteraction:
        """
        Log a Copilot interaction.
        
        This should be called for EVERY Copilot interaction to ensure
        we have complete data for analysis.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            workspace: Workspace name (plantops, fsq, planning, brand, retail)
            question: User's question/prompt
            answer: Copilot's response
            tools_used: List of tools called during interaction
            tokens_used: Number of LLM tokens consumed
            duration_ms: Duration of interaction in milliseconds
            metadata: Additional context (optional)
            
        Returns:
            Created interaction record
        """
        interaction = CopilotInteraction(
            tenant_id=tenant_id,
            user_id=user_id,
            workspace=workspace,
            question=question,
            answer=answer,
            tools_used=tools_used or [],
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
        
        self.session.add(interaction)
        await self.session.commit()
        await self.session.refresh(interaction)
        
        return interaction
    
    async def log_ai_suggestion(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        suggestion_type: str,
        suggestion_text: str,
        payload: dict,
        interaction_id: Optional[uuid.UUID] = None,
        estimated_impact: Optional[dict] = None,
    ) -> AISuggestion:
        """
        Log an AI-generated suggestion.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            suggestion_type: Type of suggestion (e.g., "line_adjustment", "safety_stock")
            suggestion_text: Human-readable suggestion text
            payload: Actionable data (parameters, values)
            interaction_id: Related Copilot interaction ID (optional)
            estimated_impact: AI's prediction of impact (optional)
            
        Returns:
            Created suggestion record
        """
        suggestion = AISuggestion(
            tenant_id=tenant_id,
            user_id=user_id,
            suggestion_type=suggestion_type,
            suggestion_text=suggestion_text,
            payload=payload,
            interaction_id=interaction_id,
            estimated_impact=estimated_impact,
            applied_flag=False,
        )
        
        self.session.add(suggestion)
        await self.session.commit()
        await self.session.refresh(suggestion)
        
        return suggestion
    
    async def record_suggestion_outcome(
        self,
        suggestion_id: uuid.UUID,
        applied_by: uuid.UUID,
        before_metrics: Optional[dict] = None,
        after_metrics: Optional[dict] = None,
    ) -> AISuggestion:
        """
        Record that a suggestion was applied and track its outcome.
        
        This is CRITICAL for ROI measurement. When we can show that:
        - AI suggested X
        - User applied X
        - Metric Y improved from A to B
        
        We have concrete proof of value.
        
        Args:
            suggestion_id: Suggestion ID
            applied_by: User ID who applied the suggestion
            before_metrics: Metrics before applying (optional)
            after_metrics: Metrics after applying (optional)
            
        Returns:
            Updated suggestion record
        """
        result = await self.session.execute(
            select(AISuggestion).where(AISuggestion.id == suggestion_id)
        )
        suggestion = result.scalar_one()
        
        suggestion.applied_flag = True
        suggestion.applied_at = datetime.utcnow()
        suggestion.applied_by = applied_by
        suggestion.before_metrics = before_metrics
        suggestion.after_metrics = after_metrics
        
        await self.session.commit()
        await self.session.refresh(suggestion)
        
        return suggestion
    
    async def record_feedback(
        self,
        interaction_id: uuid.UUID,
        rating: int,
        comment: Optional[str] = None,
        is_accurate: Optional[bool] = None,
        is_helpful: Optional[bool] = None,
        is_timely: Optional[bool] = None,
    ) -> AIFeedback:
        """
        Record user feedback on a Copilot interaction.
        
        Args:
            interaction_id: Interaction ID
            rating: Rating 1-5 (1 = poor, 5 = excellent)
            comment: Optional feedback comment
            is_accurate: Was the response accurate?
            is_helpful: Was the response helpful?
            is_timely: Was the response timely?
            
        Returns:
            Created feedback record
        """
        # Also update the interaction record with feedback
        result = await self.session.execute(
            select(CopilotInteraction).where(CopilotInteraction.id == interaction_id)
        )
        interaction = result.scalar_one()
        
        interaction.feedback_score = rating
        interaction.feedback_comment = comment
        interaction.feedback_at = datetime.utcnow()
        
        # Create feedback record
        feedback = AIFeedback(
            interaction_id=interaction_id,
            rating=rating,
            comment=comment,
            is_accurate=is_accurate,
            is_helpful=is_helpful,
            is_timely=is_timely,
        )
        
        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)
        
        return feedback
    
    async def get_workspace_analytics(
        self,
        tenant_id: uuid.UUID,
        workspace: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Get analytics for workspace(s).
        
        Returns metrics like:
        - Total interactions
        - Unique users
        - Average response time
        - Tool usage distribution
        - Feedback scores
        
        Args:
            tenant_id: Tenant ID
            workspace: Specific workspace (or None for all)
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            
        Returns:
            Analytics dictionary
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Build query
        query = select(CopilotInteraction).where(
            CopilotInteraction.tenant_id == tenant_id,
            CopilotInteraction.created_at >= start_date,
            CopilotInteraction.created_at <= end_date,
        )
        
        if workspace:
            query = query.where(CopilotInteraction.workspace == workspace)
        
        result = await self.session.execute(query)
        interactions = list(result.scalars().all())
        
        if not interactions:
            return {
                "total_interactions": 0,
                "unique_users": 0,
                "avg_response_time_ms": 0,
                "avg_tokens_used": 0,
                "tool_usage": {},
                "avg_feedback_score": 0,
                "feedback_count": 0,
            }
        
        # Calculate metrics
        total_interactions = len(interactions)
        unique_users = len(set(i.user_id for i in interactions if i.user_id))
        
        # Average response time
        response_times = [i.duration_ms for i in interactions if i.duration_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Average tokens
        token_counts = [i.tokens_used for i in interactions if i.tokens_used]
        avg_tokens = sum(token_counts) / len(token_counts) if token_counts else 0
        
        # Tool usage distribution
        tool_usage = {}
        for interaction in interactions:
            if interaction.tools_used:
                for tool in interaction.tools_used:
                    tool_usage[tool] = tool_usage.get(tool, 0) + 1
        
        # Feedback metrics
        feedback_scores = [i.feedback_score for i in interactions if i.feedback_score]
        avg_feedback = sum(feedback_scores) / len(feedback_scores) if feedback_scores else 0
        
        return {
            "total_interactions": total_interactions,
            "unique_users": unique_users,
            "avg_response_time_ms": round(avg_response_time, 2),
            "avg_tokens_used": round(avg_tokens, 2),
            "tool_usage": tool_usage,
            "avg_feedback_score": round(avg_feedback, 2),
            "feedback_count": len(feedback_scores),
        }
    
    async def get_suggestion_acceptance_rate(
        self,
        tenant_id: uuid.UUID,
        suggestion_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Calculate suggestion acceptance rate.
        
        This metric is GOLD for demonstrating ROI:
        - "80% of AI suggestions were applied by users"
        - "Suggestions saved an estimated $XX,XXX"
        
        Args:
            tenant_id: Tenant ID
            suggestion_type: Filter by suggestion type (optional)
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            
        Returns:
            Acceptance metrics dictionary
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Build query
        query = select(AISuggestion).where(
            AISuggestion.tenant_id == tenant_id,
            AISuggestion.created_at >= start_date,
            AISuggestion.created_at <= end_date,
        )
        
        if suggestion_type:
            query = query.where(AISuggestion.suggestion_type == suggestion_type)
        
        result = await self.session.execute(query)
        suggestions = list(result.scalars().all())
        
        if not suggestions:
            return {
                "total_suggestions": 0,
                "applied_count": 0,
                "acceptance_rate": 0.0,
                "by_type": {},
            }
        
        total = len(suggestions)
        applied = sum(1 for s in suggestions if s.applied_flag)
        acceptance_rate = (applied / total * 100) if total > 0 else 0.0
        
        # Break down by type
        by_type = {}
        types = set(s.suggestion_type for s in suggestions)
        for stype in types:
            type_suggestions = [s for s in suggestions if s.suggestion_type == stype]
            type_applied = sum(1 for s in type_suggestions if s.applied_flag)
            by_type[stype] = {
                "total": len(type_suggestions),
                "applied": type_applied,
                "acceptance_rate": (type_applied / len(type_suggestions) * 100) if type_suggestions else 0.0,
            }
        
        return {
            "total_suggestions": total,
            "applied_count": applied,
            "acceptance_rate": round(acceptance_rate, 2),
            "by_type": by_type,
        }
    
    async def get_tool_usage_stats(
        self,
        tenant_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """
        Get tool usage statistics.
        
        Shows which Copilot tools are most used, helping prioritize
        which tools to invest in for real ML implementation.
        
        Args:
            tenant_id: Tenant ID
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            
        Returns:
            Tool usage statistics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Get all interactions
        query = select(CopilotInteraction).where(
            CopilotInteraction.tenant_id == tenant_id,
            CopilotInteraction.created_at >= start_date,
            CopilotInteraction.created_at <= end_date,
        )
        
        result = await self.session.execute(query)
        interactions = list(result.scalars().all())
        
        # Count tool usage
        tool_counts = {}
        tool_avg_duration = {}
        
        for interaction in interactions:
            if interaction.tools_used:
                for tool in interaction.tools_used:
                    tool_counts[tool] = tool_counts.get(tool, 0) + 1
                    
                    # Track duration for this tool
                    if interaction.duration_ms:
                        if tool not in tool_avg_duration:
                            tool_avg_duration[tool] = []
                        tool_avg_duration[tool].append(interaction.duration_ms)
        
        # Calculate averages
        tool_stats = {}
        for tool, count in tool_counts.items():
            avg_duration = 0
            if tool in tool_avg_duration:
                durations = tool_avg_duration[tool]
                avg_duration = sum(durations) / len(durations)
            
            tool_stats[tool] = {
                "usage_count": count,
                "avg_duration_ms": round(avg_duration, 2),
            }
        
        # Sort by usage count
        sorted_stats = dict(sorted(tool_stats.items(), key=lambda x: x[1]["usage_count"], reverse=True))
        
        return {
            "tools": sorted_stats,
            "total_tool_calls": sum(tool_counts.values()),
        }
    
    async def get_user_engagement(
        self,
        tenant_id: uuid.UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
    ) -> dict:
        """
        Get user engagement metrics.
        
        Shows which users are most engaged with Copilot,
        helping identify power users and those who need training.
        
        Args:
            tenant_id: Tenant ID
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            limit: Number of top users to return
            
        Returns:
            User engagement statistics
        """
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        # Query for user engagement
        query = (
            select(
                CopilotInteraction.user_id,
                func.count(CopilotInteraction.id).label("interaction_count"),
                func.avg(CopilotInteraction.duration_ms).label("avg_duration_ms"),
                func.avg(CopilotInteraction.feedback_score).label("avg_feedback_score"),
            )
            .where(
                CopilotInteraction.tenant_id == tenant_id,
                CopilotInteraction.created_at >= start_date,
                CopilotInteraction.created_at <= end_date,
                CopilotInteraction.user_id.isnot(None),
            )
            .group_by(CopilotInteraction.user_id)
            .order_by(func.count(CopilotInteraction.id).desc())
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        top_users = []
        for row in rows:
            top_users.append({
                "user_id": str(row.user_id),
                "interaction_count": row.interaction_count,
                "avg_duration_ms": round(row.avg_duration_ms, 2) if row.avg_duration_ms else 0,
                "avg_feedback_score": round(row.avg_feedback_score, 2) if row.avg_feedback_score else 0,
            })
        
        return {
            "top_users": top_users,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
        }

