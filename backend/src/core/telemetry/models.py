"""
AI Telemetry models for tracking Copilot interactions and AI suggestions.

These models are CRITICAL for:
- Measuring ROI (show investors "Copilot saved $XX,XXX")
- Tuning prompts based on real usage
- Identifying which tools are valuable
- Building training datasets for future fine-tuning
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CopilotInteraction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Records every interaction with the Copilot.
    
    This is the primary telemetry table for measuring Copilot usage,
    performance, and user engagement.
    """
    
    __tablename__ = "copilot_interactions"
    
    # Tenant and user context
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Interaction context
    workspace: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        index=True,
        comment="Workspace: plantops, fsq, planning, brand, retail"
    )
    
    # Question and answer
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Tools used (JSON array of tool names)
    tools_used: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    
    # Performance metrics
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Duration in milliseconds")
    
    # Feedback
    feedback_score: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True,
        comment="User feedback: 1 = thumbs down, 5 = thumbs up"
    )
    feedback_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Additional context (can store anything as JSON)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    suggestions = relationship("AISuggestion", back_populates="interaction", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<CopilotInteraction(id={self.id}, workspace='{self.workspace}', user_id={self.user_id})>"


class AISuggestion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Records AI-generated suggestions that users can apply.
    
    Examples:
    - "Adjust line speed to 95 units/min"
    - "Increase safety stock for SKU-123 by 20%"
    - "Close this CAPA as resolved"
    
    Tracking acceptance rate is GOLD for demonstrating ROI.
    """
    
    __tablename__ = "ai_suggestions"
    
    # Link to interaction (optional)
    interaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copilot_interactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Tenant and user context
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Suggestion details
    suggestion_type: Mapped[str] = mapped_column(
        String(100), 
        nullable=False, 
        index=True,
        comment="Type: line_adjustment, safety_stock, production_plan, etc."
    )
    suggestion_text: Mapped[str] = mapped_column(Text, nullable=False, comment="Human-readable suggestion")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, comment="Actionable data (parameters, values)")
    
    # Application tracking
    applied_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Impact tracking (before/after metrics)
    before_metrics: Mapped[Optional[dict]] = mapped_column(
        JSONB, 
        nullable=True,
        comment="Metrics before applying suggestion (e.g., scrap_rate: 5.2%)"
    )
    after_metrics: Mapped[Optional[dict]] = mapped_column(
        JSONB, 
        nullable=True,
        comment="Metrics after applying suggestion (e.g., scrap_rate: 3.8%)"
    )
    
    # Estimated impact (AI's prediction)
    estimated_impact: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="AI's prediction of impact (e.g., cost_savings: $5000)"
    )
    
    # Relationships
    interaction = relationship("CopilotInteraction", back_populates="suggestions")
    
    def __repr__(self) -> str:
        return f"<AISuggestion(id={self.id}, type='{self.suggestion_type}', applied={self.applied_flag})>"


class AIFeedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    User feedback on Copilot interactions.
    
    Allows users to rate responses and provide comments.
    This is merged with CopilotInteraction in the current schema,
    but kept separate for extensibility.
    """
    
    __tablename__ = "ai_feedback"
    
    # Link to interaction
    interaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copilot_interactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Feedback details
    rating: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        comment="1-5 scale: 1 = very poor, 5 = excellent"
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Categories (why was it good/bad?)
    is_accurate: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_helpful: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_timely: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    
    def __repr__(self) -> str:
        return f"<AIFeedback(id={self.id}, interaction_id={self.interaction_id}, rating={self.rating})>"


class WorkspaceAnalytics(Base, UUIDPrimaryKeyMixin):
    """
    Pre-aggregated analytics per workspace per day.
    
    This is updated periodically (e.g., daily job) for fast querying.
    Useful for dashboards and reporting.
    """
    
    __tablename__ = "workspace_analytics"
    
    # Context
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workspace: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    
    # Metrics
    total_interactions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_response_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_tokens_used: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Tool usage (JSON object: {tool_name: count})
    tool_usage: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Feedback metrics
    avg_feedback_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Suggestion metrics
    suggestions_made: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    suggestions_applied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<WorkspaceAnalytics(workspace='{self.workspace}', date={self.date}, interactions={self.total_interactions})>"

