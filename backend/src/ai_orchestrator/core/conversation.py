"""
Conversation Manager

Handles conversation history storage and retrieval for Copilot.
Stores conversations in PostgreSQL for persistence and analytics.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import logger
from ..domain.models import CopilotConversation, CopilotMessage


class ConversationManager:
    """
    Manages Copilot conversation history.
    
    Provides:
    - Conversation creation and retrieval
    - Message storage and formatting
    - History trimming for token limits
    - Conversation context building
    """
    
    def __init__(self, db: AsyncSession, max_history: int = 10):
        """
        Initialize conversation manager.
        
        Args:
            db: Database session
            max_history: Maximum number of messages to keep in context
        """
        self.db = db
        self.max_history = max_history
    
    async def create_conversation(
        self,
        tenant_id: UUID,
        user_id: UUID,
        workspace: str,
    ) -> CopilotConversation:
        """
        Create a new conversation.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            workspace: Workspace name
            
        Returns:
            Created conversation
        """
        conversation = CopilotConversation(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            workspace=workspace,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        
        logger.info(
            f"Created conversation: {conversation.id}",
            extra={
                "tenant_id": str(tenant_id),
                "user_id": str(user_id),
                "workspace": workspace,
            }
        )
        
        return conversation
    
    async def get_conversation(self, conversation_id: UUID) -> Optional[CopilotConversation]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation or None
        """
        stmt = select(CopilotConversation).where(CopilotConversation.id == conversation_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: Optional[str],
        tools_used: Optional[List[str]] = None,
        tokens_used: int = 0,
        function_call: Optional[Dict[str, Any]] = None,
    ) -> CopilotMessage:
        """
        Add a message to the conversation.
        
        Args:
            conversation_id: Conversation ID
            role: Message role ('user', 'assistant', 'system', 'function')
            content: Message content
            tools_used: List of tools called
            tokens_used: Number of tokens used
            function_call: Optional function call details
            
        Returns:
            Created message
        """
        message = CopilotMessage(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            tools_used=tools_used or [],
            tokens_used=tokens_used,
            function_call=function_call,
            created_at=datetime.utcnow(),
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        # Update conversation updated_at
        conversation = await self.get_conversation(conversation_id)
        if conversation:
            conversation.updated_at = datetime.utcnow()
            await self.db.commit()
        
        return message
    
    async def get_messages(
        self,
        conversation_id: UUID,
        limit: Optional[int] = None,
    ) -> List[CopilotMessage]:
        """
        Get messages for a conversation.
        
        Args:
            conversation_id: Conversation ID
            limit: Optional limit on number of messages
            
        Returns:
            List of messages (ordered by creation time)
        """
        stmt = (
            select(CopilotMessage)
            .where(CopilotMessage.conversation_id == conversation_id)
            .order_by(CopilotMessage.created_at.asc())
        )
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_recent_messages(
        self,
        conversation_id: UUID,
        count: Optional[int] = None,
    ) -> List[CopilotMessage]:
        """
        Get recent messages for a conversation.
        
        Args:
            conversation_id: Conversation ID
            count: Number of recent messages (default from max_history)
            
        Returns:
            List of recent messages (ordered chronologically)
        """
        limit = count or self.max_history
        
        stmt = (
            select(CopilotMessage)
            .where(CopilotMessage.conversation_id == conversation_id)
            .order_by(CopilotMessage.created_at.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        messages = list(result.scalars().all())
        
        # Reverse to get chronological order
        return list(reversed(messages))
    
    def format_messages_for_llm(self, messages: List[CopilotMessage]) -> List[Dict[str, str]]:
        """
        Format messages for LLM API.
        
        Args:
            messages: List of messages
            
        Returns:
            List of message dicts for OpenAI API
        """
        formatted = []
        
        for msg in messages:
            message_dict = {
                "role": msg.role,
                "content": msg.content or "",
            }
            
            # Add function call if present
            if msg.function_call:
                message_dict["function_call"] = msg.function_call
            
            formatted.append(message_dict)
        
        return formatted
    
    async def build_context(
        self,
        conversation_id: UUID,
        system_prompt: str,
    ) -> List[Dict[str, str]]:
        """
        Build full conversation context for LLM.
        
        Args:
            conversation_id: Conversation ID
            system_prompt: System prompt for workspace
            
        Returns:
            Full message list starting with system prompt
        """
        # Get recent messages
        messages = await self.get_recent_messages(conversation_id)
        
        # Format for LLM
        formatted_messages = self.format_messages_for_llm(messages)
        
        # Prepend system prompt
        context = [
            {"role": "system", "content": system_prompt}
        ] + formatted_messages
        
        return context
    
    async def get_conversation_stats(self, conversation_id: UUID) -> Dict[str, Any]:
        """
        Get statistics for a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Dict with conversation statistics
        """
        messages = await self.get_messages(conversation_id)
        
        total_tokens = sum(msg.tokens_used for msg in messages)
        tool_calls = []
        
        for msg in messages:
            if msg.tools_used:
                tool_calls.extend(msg.tools_used)
        
        return {
            "message_count": len(messages),
            "total_tokens": total_tokens,
            "tool_calls": tool_calls,
            "unique_tools": list(set(tool_calls)),
        }

