"""
This module provides service functions for MCP configuration.
"""

from pathlib import Path

import yaml

from app.mcp.config_logic import (
    DEFAULT_AGENTCORE_REGION,
    DEFAULT_WORKLOAD_NAME,
    get_no_auth_servers_from_config,
    get_oauth_server_from_config,
    get_oauth_server_index_from_config,
    get_oauth_servers_from_config,
    normalize_mcp_config,
)

CONFIG_FILE_PATH = "config/mcp.yml"

mcp_config: dict | None = None


def load_mcp_config() -> dict:
    """
    Load MCP configuration from YAML file.

    Returns:
        dict: Normalized configuration with default values.
    """
    config_data = None
    path = Path(CONFIG_FILE_PATH)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
    return normalize_mcp_config(config_data)


def get_mcp_config() -> dict:
    """
    Get the cached MCP configuration, loading it if necessary.

    Returns:
        dict: The MCP configuration.
    """
    global mcp_config
    if mcp_config is None:
        mcp_config = load_mcp_config()
    return mcp_config


def get_no_auth_servers() -> list[dict]:
    """
    Get no-auth MCP servers from configuration.

    Returns:
        list[dict]: List of no-auth server configurations.
    """
    config = get_mcp_config()
    return get_no_auth_servers_from_config(config)


def get_oauth_servers() -> list[dict]:
    """
    Get OAuth MCP servers from configuration.

    Returns:
        list[dict]: List of OAuth server configurations.
    """
    config = get_mcp_config()
    return get_oauth_servers_from_config(config)


def get_oauth_server(server_index: int) -> dict:
    """
    Get OAuth server configuration by index.

    Args:
        server_index (int): Server index.

    Returns:
        dict: Server configuration, or empty dict if index out of range.
    """
    config = get_mcp_config()
    return get_oauth_server_from_config(config, server_index)


def get_oauth_server_index(server_name: str) -> int | None:
    """
    Get OAuth server index by name.

    Args:
        server_name (str): Server name.

    Returns:
        Optional[int]: Server index, or None if not found.
    """
    config = get_mcp_config()
    return get_oauth_server_index_from_config(config, server_name)


def get_workload_name() -> str:
    """
    Get workload name from configuration.

    Returns:
        str: Workload name, defaults to DEFAULT_WORKLOAD_NAME if not set.
    """
    config = get_mcp_config()
    return config.get("workload_name", DEFAULT_WORKLOAD_NAME)


def get_agentcore_region() -> str:
    """
    Get AgentCore region from global configuration.

    Returns:
        str: AgentCore region for OAuth MCP servers.
    """
    config = get_mcp_config()
    return config.get("agentcore_region", DEFAULT_AGENTCORE_REGION)


def get_auth_session_duration_minutes() -> int:
    """
    Get auth session duration in minutes from configuration.

    Returns:
        int: Auth session duration in minutes.
    """
    config = get_mcp_config()
    return config["auth_session_duration_minutes"]


def get_oauth_callback_url() -> str:
    """
    Get OAuth callback URL from configuration.

    Returns:
        str: OAuth callback URL for AgentCore Identity.
    """
    config = get_mcp_config()
    return config.get("oauth_callback_url", "")
