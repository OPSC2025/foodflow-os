"""
Pydantic schemas for Copilot API.

Defines request and response structures for Copilot endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CopilotRequest(BaseModel):
    """Request for Copilot chat endpoint."""
    
    workspace: str = Field(..., description="Workspace context (plantops, fsq, planning, brand, retail)")
    message: str = Field(..., min_length=1, max_length=4000, description="User's message/question")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context (IDs, filters, etc.)")
    conversation_id: Optional[UUID] = Field(None, description="Existing conversation ID for multi-turn chat")


class ActionLink(BaseModel):
    """Suggested action link for UI."""
    
    label: str = Field(..., description="Action button label")
    url: str = Field(..., description="URL or route path")
    icon: Optional[str] = Field(None, description="Optional icon name")


class Source(BaseModel):
    """Source document reference for RAG-powered responses."""
    
    document_id: UUID = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    excerpt: str = Field(..., description="Relevant excerpt")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Relevance confidence score")


class CopilotResponse(BaseModel):
    """Response from Copilot chat endpoint."""
    
    conversation_id: UUID = Field(..., description="Conversation ID for follow-ups")
    answer: str = Field(..., description="Copilot's natural language response")
    actions: List[ActionLink] = Field(default_factory=list, description="Suggested UI actions")
    tools_used: List[str] = Field(default_factory=list, description="Tools called during processing")
    tokens_used: int = Field(..., description="Total tokens consumed")
    duration_ms: float = Field(..., description="Processing time in milliseconds")
    sources: Optional[List[Source]] = Field(None, description="Source documents (for RAG responses)")


class FeedbackRequest(BaseModel):
    """Feedback on a Copilot response."""
    
    conversation_id: UUID = Field(..., description="Conversation ID")
    message_id: Optional[UUID] = Field(None, description="Specific message ID")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    feedback: Optional[str] = Field(None, max_length=1000, description="Optional feedback text")


class ConversationStats(BaseModel):
    """Statistics for a conversation."""
    
    conversation_id: UUID
    message_count: int
    total_tokens: int
    tool_calls: List[str]
    unique_tools: List[str]
    created_at: datetime
    updated_at: datetime

