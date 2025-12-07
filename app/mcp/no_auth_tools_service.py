"""
Service functions for no-auth MCP tools integration.
"""

import logging
import threading
import time
from functools import partial

from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

from app.env import LITELLM_MODEL
from app.mcp.config_service import get_no_auth_servers
from app.mcp.tools_logic import transform_mcp_spec_to_classic_tool

REFRESH_INTERVAL_SECONDS = 3600

no_auth_mcp_tools: list[dict] = []


def load_no_auth_mcp_tools() -> None:
    """
    Loads no-auth MCP tools from the MCP server and updates the cache.
    """
    global no_auth_mcp_tools
    result: list[dict] = []
    no_auth_servers = get_no_auth_servers()
    for idx, server in enumerate(no_auth_servers):
        url = server["url"]
        try:
            client = MCPClient(partial(streamablehttp_client, url))
            with client:  # ty: ignore[invalid-context-manager]
                tools = client.list_tools_sync()
            result.extend(
                transform_mcp_spec_to_classic_tool(
                    mcp_spec=tool.tool_spec,
                    auth_type="none",
                    server_index=idx,
                    model=LITELLM_MODEL,
                )
                for tool in tools
            )
        except Exception as exc:
            logging.warning("Failed to load MCP tools from %s: %s", url, exc)
    no_auth_mcp_tools = result


def get_no_auth_mcp_tools() -> list[dict]:
    """
    Get the cached list of no-auth MCP tools.

    Returns:
        list[dict]: Cached no-auth MCP tools in classic format.
    """
    return no_auth_mcp_tools


def start_no_auth_mcp_tools_refresh_loop() -> None:
    """
    Start background thread to periodically refresh no-auth MCP tools.
    Performs initial load before starting the refresh loop.
    """
    load_no_auth_mcp_tools()

    def refresh_loop():
        """Background refresh loop for no-auth MCP tools."""
        while True:
            time.sleep(REFRESH_INTERVAL_SECONDS)
            load_no_auth_mcp_tools()
            logging.info(f"No-auth MCP tools refreshed: {len(no_auth_mcp_tools)} tools")

    threading.Thread(
        target=refresh_loop,
        daemon=True,
        name="no-auth-mcp-tools-refresh",
    ).start()


def process_no_auth_mcp_tool_call(
    *,
    server_url: str,
    tool_call_id: str,
    tool_name: str,
    arguments: dict,
) -> str:
    """
    Processes a no-auth MCP tool call by creating an MCP client.

    Args:
        server_url (str): The URL of the MCP server.
        tool_call_id (str): The ID of the tool call.
        tool_name (str): The name of the tool to call.
        arguments (dict): The arguments to pass to the function.

    Returns:
        str: The response from the tool call.
    """
    mcp_client = MCPClient(lambda: streamablehttp_client(server_url))
    with mcp_client:  # ty: ignore[invalid-context-manager]
        result = mcp_client.call_tool_sync(
            tool_use_id=tool_call_id,
            name=tool_name,
            arguments=arguments,
        )
    content = result["content"][0]
    return content.get("text", "")
