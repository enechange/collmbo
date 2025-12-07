"""
Logic functions for OAuth session management.
"""

from typing import Optional

from app.mcp.tools_logic import (
    AUTH_TYPE_ABBREVIATIONS,
    MCP_TOOL_NAME_SEPARATOR,
    MCP_TOOL_NAME_SEPARATOR_FOR_GEMINI,
)


def is_session_not_expired(session: Optional[dict], timestamp: int) -> bool:
    """
    Check if authentication session has not expired.

    Args:
        session (Optional[dict]): Session data.
        timestamp (int): Unix timestamp to compare against expiration.

    Returns:
        bool: True if session exists and has not expired, False otherwise.
    """
    if not session or "expires_at" not in session:
        return False
    return timestamp < session["expires_at"]


def create_bearer_auth_headers(
    token: str,
    additional_headers: Optional[dict[str, str]] = None,
) -> dict[str, str]:
    """
    Create authorization headers for Bearer token authentication.

    Args:
        token (str): OAuth access token.
        additional_headers (Optional[dict[str, str]]): Additional headers from server config.

    Returns:
        dict[str, str]: HTTP headers with Bearer authorization and additional headers.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Add additional headers if provided
    if additional_headers:
        headers.update(additional_headers)

    return headers


def parse_mcp_tool_name(tool_name: str) -> tuple[str, str, int]:
    """
    Parse a classic MCP tool name to extract its components.

    Args:
        tool_name (str): Classic tool name in format:
        - Gemini: "{auth_abbrev}.{server_index}.{spec_name}"
        - Others: "{auth_abbrev}-{server_index}-{spec_name}"

    Returns:
        tuple[str, str, int]: Original spec name, auth type, and server index.
        Returns ("", "", -1) if tool name format is invalid.
    """
    # Try dot-separated format first (Gemini)
    if MCP_TOOL_NAME_SEPARATOR_FOR_GEMINI in tool_name:
        parts = tool_name.split(MCP_TOOL_NAME_SEPARATOR_FOR_GEMINI)
        if len(parts) >= 3:
            # First part is auth abbreviation
            auth_abbrev = parts[0]
            abbreviation_to_auth_type = {
                v: k for k, v in AUTH_TYPE_ABBREVIATIONS.items()
            }
            auth_type = abbreviation_to_auth_type.get(auth_abbrev)
            if auth_type:
                # Second part is server index
                try:
                    server_index = int(parts[1])
                    # Everything after server index is the original spec name
                    spec_name = MCP_TOOL_NAME_SEPARATOR_FOR_GEMINI.join(parts[2:])
                    return spec_name, auth_type, server_index
                except ValueError:
                    pass

    # Try hyphen-separated format (GPT and others)
    if MCP_TOOL_NAME_SEPARATOR in tool_name:
        parts = tool_name.split(MCP_TOOL_NAME_SEPARATOR)
        if len(parts) >= 3:
            # First part is auth abbreviation
            auth_abbrev = parts[0]
            abbreviation_to_auth_type = {
                v: k for k, v in AUTH_TYPE_ABBREVIATIONS.items()
            }
            auth_type = abbreviation_to_auth_type.get(auth_abbrev)
            if auth_type:
                # Second part is server index
                try:
                    server_index = int(parts[1])
                    # Everything after server index is the original spec name
                    spec_name = MCP_TOOL_NAME_SEPARATOR.join(parts[2:])
                    return spec_name, auth_type, server_index
                except ValueError:
                    pass

    return "", "", -1
