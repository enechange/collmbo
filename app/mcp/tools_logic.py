"""
This module provides logical functions for MCP tools.
"""

from copy import deepcopy

from strands.types.tools import ToolSpec

MCP_TOOL_NAME_SEPARATOR = "-"
MCP_TOOL_NAME_SEPARATOR_FOR_GEMINI = "."

AUTH_TYPE_ABBREVIATIONS = {"none": "n", "user_federation": "u"}


def build_mcp_tool_name(
    spec_name: str, auth_type: str, server_index: int, model: str
) -> str:
    """
    Build a name for an MCP tool based on its specification name, auth type, and server index.

    Args:
        spec_name (str): The name of the tool specification.
        auth_type (str): The authentication type (none, user_federation, m2m).
        server_index (int): The index of the MCP server.
        model (str): The model name, used to determine separator format.

    Returns:
        str: The constructed tool name. Format depends on model:
        - Gemini: "{auth_abbrev}.{server_index}.{spec_name}"
        - Others: "{auth_abbrev}-{server_index}-{spec_name}"
    """
    auth_abbrev = AUTH_TYPE_ABBREVIATIONS.get(auth_type, auth_type)

    # Use dot separator for Gemini models, hyphen for others
    if model.startswith("gemini/"):
        return MCP_TOOL_NAME_SEPARATOR_FOR_GEMINI.join(
            [auth_abbrev, str(server_index), spec_name]
        )
    else:
        return MCP_TOOL_NAME_SEPARATOR.join([auth_abbrev, str(server_index), spec_name])


def transform_mcp_spec_to_classic_tool(
    *,
    mcp_spec: ToolSpec,
    auth_type: str,
    server_index: int,
    model: str,
) -> dict:
    """
    Transform an MCP tool specification to a classic tool format.

    Args:
        mcp_spec (dict): The MCP tool specification.
        auth_type (str): The authentication type (none, user_federation).
        server_index (int): The index of the MCP server.
        model (str): The model name, used to determine if specific properties should be removed.

    Returns:
        dict: The transformed tool in classic format.
    """
    parameters = deepcopy(mcp_spec["inputSchema"]["json"])

    # Ensure parameters has required fields for OpenAI API
    if "type" not in parameters:
        parameters["type"] = "object"
    if "properties" not in parameters:
        parameters["properties"] = {}

    # Remove invalid "format" property for Gemini models
    if model.startswith("gemini/"):
        for prop in parameters.get("properties", {}).values():
            if "format" in prop and prop["format"] not in ("date-time", "enum"):
                prop.pop("format")

    return {
        "type": "function",
        "function": {
            "name": build_mcp_tool_name(
                mcp_spec["name"], auth_type, server_index, model
            ),
            "description": mcp_spec["description"],
            "parameters": parameters,
        },
    }
