"""
Database models for Copilot conversations.

Stores conversation history for context management and analytics.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class CopilotConversation(Base):
    """
    Copilot conversation.
    
    Represents a conversation thread between a user and Copilot
    within a specific workspace context.
    """
    __tablename__ = "copilot_conversations"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    workspace: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages: Mapped[List["CopilotMessage"]] = relationship(
        "CopilotMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
    
    __table_args__ = (
        Index("ix_copilot_conversations_tenant_user", "tenant_id", "user_id"),
        Index("ix_copilot_conversations_tenant_workspace", "tenant_id", "workspace"),
    )


class CopilotMessage(Base):
    """
    Message in a Copilot conversation.
    
    Stores individual messages including user queries, assistant responses,
    system prompts, and function calls.
    """
    __tablename__ = "copilot_messages"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("copilot_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system, function
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tools_used: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    function_call: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    
    # Relationships
    conversation: Mapped["CopilotConversation"] = relationship("CopilotConversation", back_populates="messages")
    
    __table_args__ = (
        Index("ix_copilot_messages_conversation_created", "conversation_id", "created_at"),
    )

