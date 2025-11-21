"""
AI Orchestrator - Copilot LLM Integration

This module implements the Copilot orchestration layer that serves as the
intelligent interface to FoodFlow OS. It provides:

- LLM-powered natural language interface
- Workspace-specific tool calling
- Conversation history management
- Integration with AI services
- Telemetry logging
"""

from .api import router

__all__ = ["router"]

