"""
LLM Client for OpenAI Integration

Provides async OpenAI client with:
- Function calling support
- Token counting and rate limiting
- Retry logic for API failures
- Configuration from environment
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import openai
from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.core.config import get_settings
from src.core.logging import logger


settings = get_settings()


class LLMClient:
    """
    Client for OpenAI LLM with function calling support.
    
    Handles all interactions with OpenAI API including:
    - Chat completions with function calling
    - Token counting and cost estimation
    - Retry logic for transient failures
    - Request/response logging
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: OpenAI API key (default from settings)
            model: Model name (default from settings)
            temperature: Sampling temperature (default from settings)
            max_tokens: Maximum tokens in response (default from settings)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model
        self.temperature = temperature or settings.openai_temperature
        self.max_tokens = max_tokens or settings.openai_max_tokens
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def close(self):
        """Close OpenAI client."""
        await self.client.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.APITimeoutError, openai.APIConnectionError)),
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = "auto",
    ) -> Dict[str, Any]:
        """
        Create a chat completion with optional function calling.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            functions: Optional list of function definitions
            function_call: 'auto', 'none', or {'name': 'function_name'}
            
        Returns:
            Response dict with:
            - message: Assistant's message
            - function_call: Optional function call details
            - usage: Token usage statistics
            - finish_reason: 'stop', 'function_call', etc.
        """
        start_time = datetime.utcnow()
        
        try:
            # Prepare request parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            
            # Add function calling if provided
            if functions:
                params["functions"] = functions
                params["function_call"] = function_call
            
            # Make API call
            response = await self.client.chat.completions.create(**params)
            
            # Extract response
            choice = response.choices[0]
            usage = response.usage
            
            # Log success
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(
                f"LLM completion successful ({duration_ms:.2f}ms)",
                extra={
                    "model": self.model,
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "finish_reason": choice.finish_reason,
                }
            )
            
            # Format response
            result = {
                "message": {
                    "role": choice.message.role,
                    "content": choice.message.content,
                },
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                },
                "finish_reason": choice.finish_reason,
            }
            
            # Add function call if present
            if choice.message.function_call:
                result["function_call"] = {
                    "name": choice.message.function_call.name,
                    "arguments": json.loads(choice.message.function_call.arguments),
                }
            
            return result
        
        except openai.APIError as e:
            # Log failure
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(
                f"LLM completion failed: {str(e)}",
                extra={
                    "model": self.model,
                    "duration_ms": duration_ms,
                    "error": str(e),
                }
            )
            raise e
    
    async def chat_completion_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        max_iterations: int = 5,
    ) -> Dict[str, Any]:
        """
        Execute chat completion with iterative tool calling.
        
        This method handles the full tool calling loop:
        1. Send messages to LLM
        2. If LLM calls a function, execute it
        3. Add function result to messages
        4. Repeat until LLM provides final answer
        
        Args:
            messages: Initial conversation messages
            tools: List of available tool definitions
            max_iterations: Maximum tool calling iterations
            
        Returns:
            Final response with all tool calls and results
        """
        conversation = messages.copy()
        tool_calls = []
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            
            # Get LLM response
            response = await self.chat_completion(
                messages=conversation,
                functions=tools,
                function_call="auto",
            )
            
            # Check if LLM wants to call a function
            if response["finish_reason"] == "function_call":
                function_call = response["function_call"]
                tool_calls.append(function_call)
                
                # Add assistant's function call to conversation
                conversation.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": function_call["name"],
                        "arguments": json.dumps(function_call["arguments"]),
                    }
                })
                
                # Tool execution will be handled by the orchestrator
                # Return to allow orchestrator to execute the tool
                return {
                    "status": "requires_tool_execution",
                    "function_call": function_call,
                    "conversation": conversation,
                    "tool_calls": tool_calls,
                    "usage": response["usage"],
                }
            
            # LLM provided final answer
            return {
                "status": "complete",
                "message": response["message"]["content"],
                "conversation": conversation,
                "tool_calls": tool_calls,
                "usage": response["usage"],
            }
        
        # Max iterations reached
        return {
            "status": "max_iterations",
            "message": "I apologize, but I've reached the maximum number of tool calls. Please try rephrasing your question.",
            "conversation": conversation,
            "tool_calls": tool_calls,
            "usage": {"total_tokens": 0},
        }
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost of API call based on token usage.
        
        Pricing as of 2024 (update as needed):
        - gpt-4-turbo-preview: $0.01/1K prompt, $0.03/1K completion
        - gpt-3.5-turbo: $0.0005/1K prompt, $0.0015/1K completion
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD
        """
        if "gpt-4" in self.model:
            prompt_cost = (prompt_tokens / 1000) * 0.01
            completion_cost = (completion_tokens / 1000) * 0.03
        else:
            prompt_cost = (prompt_tokens / 1000) * 0.0005
            completion_cost = (completion_tokens / 1000) * 0.0015
        
        return prompt_cost + completion_cost


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


async def close_llm_client():
    """Close LLM client."""
    global _llm_client
    if _llm_client is not None:
        await _llm_client.close()
        _llm_client = None

