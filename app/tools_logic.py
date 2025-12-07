"""
This module provides logical functions for tools.
"""

from importlib import import_module

from app.mcp.tools_logic import (
    AUTH_TYPE_ABBREVIATIONS,
    MCP_TOOL_NAME_SEPARATOR,
    MCP_TOOL_NAME_SEPARATOR_FOR_GEMINI,
)

ABBREVIATION_TO_AUTH_TYPE = {v: k for k, v in AUTH_TYPE_ABBREVIATIONS.items()}


def is_mcp_tool_name(name: str) -> bool:
    """
    Check if a tool name indicates it is an MCP tool.

    Args:
        name (str): The name of the tool.

    Returns:
        bool: True if the tool is an MCP tool, False otherwise.
    """
    # Check for both dot-separated (Gemini) and hyphen-separated (GPT) formats
    return MCP_TOOL_NAME_SEPARATOR_FOR_GEMINI in name or MCP_TOOL_NAME_SEPARATOR in name


def load_classic_tools(module_name: str | None) -> list[dict]:
    """
    Load tools from a module.

    Args:
        module_name (Optional[str]): The name of the module to load tools from.

    Returns:
        list[dict]: The loaded tools, or an empty list if none.
    """
    return import_module(module_name).tools if module_name is not None else []
