"""Workspace-specific tools for Copilot."""

from .plantops_tools import register_plantops_tools
from .fsq_tools import register_fsq_tools
from .planning_tools import register_planning_tools
from .brand_tools import register_brand_tools
from .retail_tools import register_retail_tools


def register_all_tools(registry):
    """
    Register all workspace tools in the tool registry.
    
    Args:
        registry: ToolRegistry instance
    """
    register_plantops_tools(registry)
    register_fsq_tools(registry)
    register_planning_tools(registry)
    register_brand_tools(registry)
    register_retail_tools(registry)


__all__ = [
    "register_all_tools",
    "register_plantops_tools",
    "register_fsq_tools",
    "register_planning_tools",
    "register_brand_tools",
    "register_retail_tools",
]

