"""Workspace-specific system prompts for Copilot."""

from .plantops_prompt import PLANTOPS_SYSTEM_PROMPT
from .fsq_prompt import FSQ_SYSTEM_PROMPT
from .planning_prompt import PLANNING_SYSTEM_PROMPT
from .brand_prompt import BRAND_SYSTEM_PROMPT
from .retail_prompt import RETAIL_SYSTEM_PROMPT

# Mapping of workspace names to system prompts
WORKSPACE_PROMPTS = {
    "plantops": PLANTOPS_SYSTEM_PROMPT,
    "fsq": FSQ_SYSTEM_PROMPT,
    "planning": PLANNING_SYSTEM_PROMPT,
    "brand": BRAND_SYSTEM_PROMPT,
    "retail": RETAIL_SYSTEM_PROMPT,
}


def get_system_prompt(workspace: str) -> str:
    """
    Get system prompt for a workspace.
    
    Args:
        workspace: Workspace name
        
    Returns:
        System prompt string
        
    Raises:
        ValueError: If workspace is not found
    """
    if workspace not in WORKSPACE_PROMPTS:
        raise ValueError(
            f"Invalid workspace: {workspace}. "
            f"Valid workspaces: {', '.join(WORKSPACE_PROMPTS.keys())}"
        )
    
    return WORKSPACE_PROMPTS[workspace]


__all__ = [
    "PLANTOPS_SYSTEM_PROMPT",
    "FSQ_SYSTEM_PROMPT",
    "PLANNING_SYSTEM_PROMPT",
    "BRAND_SYSTEM_PROMPT",
    "RETAIL_SYSTEM_PROMPT",
    "WORKSPACE_PROMPTS",
    "get_system_prompt",
]

