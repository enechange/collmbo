"""
This module provides pure logic functions for MCP configuration.
"""

DEFAULT_AUTH_SESSION_DURATION_MINUTES = 30
DEFAULT_WORKLOAD_NAME = "Collmbo"
DEFAULT_AGENTCORE_REGION = "us-west-2"


def get_oauth_servers_from_config(mcp_config: dict) -> list[dict]:
    """
    Extract servers requiring authentication from configuration.

    Args:
        mcp_config (dict): MCP configuration dictionary.

    Returns:
        list[dict]: List of servers requiring authentication.
    """
    oauth_servers = []
    for server in mcp_config.get("servers", []):
        auth_type = server.get("auth_type")
        if auth_type and auth_type != "none":
            oauth_servers.append(server)
    return oauth_servers


def get_oauth_server_from_config(mcp_config: dict, server_index: int) -> dict:
    """
    Get OAuth server configuration by index from config.

    Args:
        mcp_config (dict): MCP configuration dictionary.
        server_index (int): Server index.

    Returns:
        dict: Server configuration, or empty dict if index out of range.
    """
    oauth_servers = get_oauth_servers_from_config(mcp_config)
    if 0 <= server_index < len(oauth_servers):
        return oauth_servers[server_index]
    return {}


def get_oauth_server_index_from_config(
    mcp_config: dict,
    server_name: str,
) -> int | None:
    """
    Get OAuth server index by name from config.

    Args:
        mcp_config (dict): MCP configuration dictionary.
        server_name (str): Server name.

    Returns:
        Optional[int]: Server index, or None if not found.
    """
    oauth_servers = get_oauth_servers_from_config(mcp_config)
    for i, server in enumerate(oauth_servers):
        if server.get("name") == server_name:
            return i
    return None


def get_no_auth_servers_from_config(mcp_config: dict) -> list[dict[str, str]]:
    """
    Get servers with auth_type="none" from configuration.

    Args:
        mcp_config (dict): MCP configuration dictionary.

    Returns:
        list[dict[str, str]]: List of no-auth servers with 'name' and 'url' keys.
    """
    servers = []
    for server in mcp_config.get("servers", []):
        if server.get("auth_type") == "none":
            servers.append({"name": server["name"], "url": server["url"]})
    return servers


def normalize_mcp_config(raw_mcp_config: dict | None) -> dict:
    """
    Normalize MCP configuration data with default values.

    Args:
        raw_mcp_config (Optional[dict]): Raw configuration data from YAML, or None.

    Returns:
        dict: Normalized configuration with required keys and default values.
    """
    if raw_mcp_config is None:
        raw_mcp_config = {}
    return {
        "servers": raw_mcp_config.get("servers", []),
        "auth_session_duration_minutes": raw_mcp_config.get(
            "auth_session_duration_minutes", DEFAULT_AUTH_SESSION_DURATION_MINUTES
        ),
        "workload_name": raw_mcp_config.get("workload_name", DEFAULT_WORKLOAD_NAME),
        "agentcore_region": raw_mcp_config.get(
            "agentcore_region", DEFAULT_AGENTCORE_REGION
        ),
        "oauth_callback_url": raw_mcp_config.get("oauth_callback_url", ""),
    }
