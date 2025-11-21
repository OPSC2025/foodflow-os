"""
Tool Registry for Copilot

Manages workspace-specific tools and their execution.
Tools are functions that the LLM can call to interact with the system.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from src.core.logging import logger


@dataclass
class Tool:
    """
    Represents a tool that can be called by the LLM.
    
    Attributes:
        name: Unique tool name
        description: Human-readable description for LLM
        parameters: JSON schema defining parameters
        function: Async function to execute
        workspace: Workspace this tool belongs to
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    workspace: str
    
    def to_openai_function(self) -> Dict[str, Any]:
        """
        Convert tool to OpenAI function calling format.
        
        Returns:
            Function definition for OpenAI API
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """
    Registry for managing and executing Copilot tools.
    
    Tools are organized by workspace and can be dynamically
    registered, retrieved, and executed.
    """
    
    def __init__(self):
        """Initialize empty tool registry."""
        self._tools: Dict[str, Tool] = {}
        self._workspace_tools: Dict[str, List[str]] = {}
    
    def register(self, tool: Tool):
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool to register
        """
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} already registered, overwriting")
        
        self._tools[tool.name] = tool
        
        # Track workspace association
        if tool.workspace not in self._workspace_tools:
            self._workspace_tools[tool.workspace] = []
        
        if tool.name not in self._workspace_tools[tool.workspace]:
            self._workspace_tools[tool.workspace].append(tool.name)
        
        logger.info(f"Registered tool: {tool.name} for workspace: {tool.workspace}")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool or None if not found
        """
        return self._tools.get(name)
    
    def get_workspace_tools(self, workspace: str) -> List[Tool]:
        """
        Get all tools for a workspace.
        
        Args:
            workspace: Workspace name
            
        Returns:
            List of tools
        """
        tool_names = self._workspace_tools.get(workspace, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_workspace_functions(self, workspace: str) -> List[Dict[str, Any]]:
        """
        Get OpenAI function definitions for a workspace.
        
        Args:
            workspace: Workspace name
            
        Returns:
            List of function definitions for OpenAI API
        """
        tools = self.get_workspace_tools(workspace)
        return [tool.to_openai_function() for tool in tools]
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a tool with given arguments.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments from LLM
            context: Execution context (tenant_id, user_id, db session, etc.)
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)
        
        if not tool:
            logger.error(f"Tool not found: {tool_name}")
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
            }
        
        try:
            logger.info(f"Executing tool: {tool_name}", extra={"arguments": arguments})
            
            # Execute tool function
            result = await tool.function(context=context, **arguments)
            
            logger.info(f"Tool executed successfully: {tool_name}")
            
            return {
                "success": True,
                "result": result,
            }
        
        except Exception as e:
            logger.error(
                f"Tool execution failed: {tool_name}",
                extra={
                    "error": str(e),
                    "arguments": arguments,
                },
                exc_info=True,
            )
            
            return {
                "success": False,
                "error": str(e),
            }
    
    def list_workspaces(self) -> List[str]:
        """
        List all registered workspaces.
        
        Returns:
            List of workspace names
        """
        return list(self._workspace_tools.keys())
    
    def tool_count(self, workspace: Optional[str] = None) -> int:
        """
        Count tools in registry.
        
        Args:
            workspace: Optional workspace filter
            
        Returns:
            Number of tools
        """
        if workspace:
            return len(self._workspace_tools.get(workspace, []))
        return len(self._tools)


# Singleton instance
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get singleton tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry

