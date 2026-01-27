"""
Service functions for MCP OAuth session management.
"""

import time

from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient
from strands.types.exceptions import MCPClientInitializationError

from app.env import LLM_MODEL
from app.mcp.config_service import get_oauth_server, get_oauth_server_index
from app.mcp.oauth_tools_logic import create_bearer_auth_headers, is_session_not_expired
from app.mcp.tools_logic import transform_mcp_spec_to_classic_tool

user_oauth_sessions: dict[str, dict[str, dict]] = {}


def set_user_oauth_session(
    user_id: str,
    server_name: str,
    token: str,
    expires_at: int,
    tools: list[dict] | None = None,
) -> None:
    """
    Set OAuth session for a specific user and server.

    Args:
        user_id (str): The user ID.
        server_name (str): The MCP server name.
        token (str): The OAuth token.
        expires_at (int): Unix timestamp when the token expires.
        tools (list[dict] | None): Tools list to store with session.
    """
    if tools is None:
        tools = []
    if user_id not in user_oauth_sessions:
        user_oauth_sessions[user_id] = {}
    user_oauth_sessions[user_id][server_name] = {
        "token": token,
        "expires_at": expires_at,
        "tools": tools,
    }


def clear_user_oauth_session(user_id: str, server_name: str) -> None:
    """
    Clear OAuth session for a specific user and server.

    Args:
        user_id (str): The user ID.
        server_name (str): The MCP server name.
    """
    if user_id in user_oauth_sessions:
        user_oauth_sessions[user_id].pop(server_name, None)


def get_user_oauth_sessions(user_id: str) -> dict[str, dict]:
    """
    Get all OAuth sessions for a user.

    Args:
        user_id (str): The user ID.

    Returns:
        dict: All server sessions for the user.
    """
    return user_oauth_sessions.get(user_id, {})


def get_all_user_oauth_sessions() -> dict[str, dict[str, dict]]:
    """
    Get all user OAuth sessions.

    Returns:
        dict[str, dict[str, dict]]: All OAuth sessions indexed by user ID and server name.
    """
    return user_oauth_sessions


def expire_old_oauth_sessions(user_id: str) -> None:
    """
    Remove expired OAuth sessions for a user.

    Args:
        user_id (str): The user ID.
    """
    all_sessions = get_user_oauth_sessions(user_id)
    current_time = int(time.time())
    for server_name, session in list(all_sessions.items()):
        if not is_session_not_expired(session, current_time):
            clear_user_oauth_session(user_id, server_name)


def set_user_oauth_mcp_tools(user_id: str, server_name: str, tools: list[dict]) -> None:
    """
    Set MCP tools for a user's OAuth session.

    Args:
        user_id (str): The user ID.
        server_name (str): The MCP server name.
        tools (list[dict]): List of MCP tools to store.
    """
    if user_id in user_oauth_sessions and server_name in user_oauth_sessions[user_id]:
        user_oauth_sessions[user_id][server_name]["tools"] = tools


def get_user_oauth_mcp_tools_for_server(user_id: str, server_name: str) -> list[dict]:
    """
    Get MCP tools for a user's OAuth session.

    Args:
        user_id (str): The user ID.
        server_name (str): The MCP server name.

    Returns:
        list[dict]: List of cached MCP tools, empty list if not found.
    """
    if user_id in user_oauth_sessions and server_name in user_oauth_sessions[user_id]:
        return user_oauth_sessions[user_id][server_name].get("tools", [])
    return []


def get_user_oauth_session_for_server(user_id: str, server_name: str) -> dict:
    """
    Get OAuth session for a specific user and server.

    Args:
        user_id (str): The user ID.
        server_name (str): The MCP server name.

    Returns:
        dict: Session data for the server, empty dict if not found.
    """
    if user_id in user_oauth_sessions and server_name in user_oauth_sessions[user_id]:
        return user_oauth_sessions[user_id][server_name]
    return {}


def get_user_oauth_mcp_tools(user_id: str) -> dict[str, list[dict]]:
    """
    Get all OAuth MCP tools for a user across all servers.

    Args:
        user_id (str): The user ID.

    Returns:
        dict: Tools grouped by server name.
    """
    sessions = get_user_oauth_sessions(user_id)
    return {
        server_name: session.get("tools", [])
        for server_name, session in sessions.items()
    }


def get_flattened_user_oauth_mcp_tools(user_id: str) -> list[dict]:
    """
    Get flattened OAuth MCP tools for a user.
    This function is only called for DM conversations.

    Args:
        user_id (str): User ID for authenticated tools.

    Returns:
        list[dict]: List of OAuth MCP tools in classic format.
    """
    result: list[dict] = []
    oauth_tools_map = get_user_oauth_mcp_tools(user_id)
    for tools in oauth_tools_map.values():
        result.extend(tools)
    return result


async def fetch_mcp_oauth_tools(
    user_id: str,
    server_name: str,
    server_url: str,
    token: str,
) -> list[dict]:
    """
    Fetch tools from OAuth-authenticated MCP server.

    Args:
        user_id (str): User ID for caching.
        server_name (str): Server name for caching.
        server_url (str): MCP server URL.
        token (str): OAuth access token.

    Returns:
        list[dict]: List of available tools.
    """
    cached_tools = get_user_oauth_mcp_tools_for_server(user_id, server_name)
    if cached_tools:
        return cached_tools

    tools = []

    # Get server configuration for additional headers
    server_index = get_oauth_server_index(server_name)
    if server_index is None:
        return []

    server_config = get_oauth_server(server_index)
    additional_headers = server_config.get("additional_headers", {})
    headers = create_bearer_auth_headers(token, additional_headers)

    client = MCPClient(lambda: streamablehttp_client(server_url, headers=headers))
    with client:  # ty: ignore[invalid-context-manager]
        mcp_tools = client.list_tools_sync()

    for mcp_tool in mcp_tools:
        tool_spec = mcp_tool.tool_spec
        classic_tool = transform_mcp_spec_to_classic_tool(
            mcp_spec=tool_spec,
            auth_type="user_federation",
            server_index=server_index,
            model=LLM_MODEL,
        )
        tools.append(classic_tool)

    set_user_oauth_mcp_tools(user_id=user_id, server_name=server_name, tools=tools)
    return tools


def process_oauth_mcp_tool_call(
    *,
    tool_call_id: str,
    tool_name: str,
    arguments: dict,
    user_id: str,
    server_index: int,
) -> str:
    """
    Processes an OAuth MCP tool call using MCPClient.

    Args:
        tool_call_id (str): The ID of the tool call.
        tool_name (str): The name of the tool to call.
        arguments (dict): The arguments to pass to the function.
        user_id (str): The user ID for authentication.
        server_index (int): The OAuth server index.

    Returns:
        str: The response from the tool call.
    """
    server_config = get_oauth_server(server_index)
    session = get_user_oauth_session_for_server(user_id, server_config["name"])

    additional_headers = server_config.get("additional_headers", {})
    headers = create_bearer_auth_headers(session["token"], additional_headers)
    mcp_client = MCPClient(
        lambda: streamablehttp_client(server_config["url"], headers=headers)
    )

    try:
        with mcp_client:  # ty: ignore[invalid-context-manager]
            result = mcp_client.call_tool_sync(
                tool_use_id=tool_call_id,
                name=tool_name,
                arguments=arguments,
            )
        content = result["content"][0]
        return content.get("text", "")
    except MCPClientInitializationError as err:
        # MCP client failed to initialize, likely due to authentication error
        # Clear the invalid session and cached tools
        clear_user_oauth_session(user_id, server_config["name"])
        raise RuntimeError(
            f"Authentication error for {server_config['name']}. "
            "Please visit the Home tab to re-authorize."
        ) from err
