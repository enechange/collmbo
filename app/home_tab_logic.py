"""
Logic functions for building home tab blocks.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from slack_sdk.models.blocks import (
    ActionsBlock,
    Block,
    ButtonElement,
    HeaderBlock,
    SectionBlock,
)
from slack_sdk.models.blocks.basic_components import MarkdownTextObject, PlainTextObject
from slack_sdk.models.views import View

from app.mcp.config_logic import (
    get_no_auth_servers_from_config,
    get_oauth_servers_from_config,
)
from app.mcp.oauth_control_service import OAUTH_URL_PROCESSING

ENABLE_MCP_OAUTH_ACTION_PREFIX = "enable_mcp_oauth_"
DISABLE_MCP_OAUTH_ACTION_PREFIX = "disable_mcp_oauth_"
CANCEL_MCP_OAUTH_ACTION_PREFIX = "cancel_mcp_oauth_"


def extract_server_index_from_action_id(action_id: str, action_prefix: str) -> int:
    """
    Extract server index from action ID.

    Args:
        action_id (str): Action ID from Slack button.
        action_prefix (str): Action prefix to remove (e.g., "enable_mcp_oauth_", "disable_mcp_oauth_").

    Returns:
        int: Server index.
    """
    return int(action_id.replace(action_prefix, ""))


def extract_enable_server_index(action_id: str) -> int:
    """
    Extract server index from enable OAuth action ID.

    Args:
        action_id (str): Action ID from Slack button.

    Returns:
        int: Server index.
    """
    return extract_server_index_from_action_id(
        action_id, ENABLE_MCP_OAUTH_ACTION_PREFIX
    )


def extract_disable_server_index(action_id: str) -> int:
    """
    Extract server index from disable OAuth action ID.

    Args:
        action_id (str): Action ID from Slack button.

    Returns:
        int: Server index.
    """
    return extract_server_index_from_action_id(
        action_id, DISABLE_MCP_OAUTH_ACTION_PREFIX
    )


def extract_cancel_server_index(action_id: str) -> int:
    """
    Extract server index from cancel OAuth action ID.

    Args:
        action_id (str): Action ID from Slack button.

    Returns:
        int: Server index.
    """
    return extract_server_index_from_action_id(
        action_id, CANCEL_MCP_OAUTH_ACTION_PREFIX
    )


def format_timestamp(timestamp: int, user_tz: str) -> str:
    """
    Format timestamp to readable time.

    Args:
        timestamp (int): Unix timestamp to format.
        user_tz (str): User's timezone string.

    Returns:
        str: Formatted time string.
    """
    try:
        dt = datetime.fromtimestamp(timestamp, tz=UTC)
        try:
            user_timezone = ZoneInfo(user_tz)
        except ZoneInfoNotFoundError, AttributeError:
            user_timezone = UTC
        dt = dt.astimezone(user_timezone)
        return dt.strftime("%H:%M:%S")
    except ValueError, TypeError, OSError:
        return ""


def format_server_display(
    server_name: str,
    is_enabled: bool,
    expires_at: int | None = None,
    user_tz: str = "UTC",
) -> str:
    """
    Format server name for display in Home tab.

    Args:
        server_name (str): The server name.
        is_enabled (bool): Whether the server is enabled/authenticated.
        expires_at (Optional[int]): Unix timestamp when the session expires.
        user_tz (str): User's timezone string.

    Returns:
        str: Formatted server display string with bold if enabled and expiry time if available.
    """
    if not is_enabled:
        return server_name

    # Enabled servers are shown in bold
    if expires_at:
        expiry_time = format_timestamp(expires_at, user_tz)
        return f"*{server_name}* (expires at {expiry_time})"
    return f"*{server_name}*"


def build_home_tab_blocks(
    mcp_config: dict,
    user_oauth_urls: dict[str, str],
    user_oauth_verification_codes: dict[str, str],
    user_oauth_sessions: dict[str, dict],
    user_oauth_tools: dict[str, list[dict]],
    user_tz: str,
    error_message: str | None = None,
) -> list[Block]:
    """
    Build home tab blocks from configuration and user data.

    Args:
        mcp_config (dict): MCP configuration.
        user_oauth_urls (dict): OAuth URLs indexed by server name for the user.
        user_oauth_verification_codes (dict): OAuth verification codes indexed by server name for the user.
        user_oauth_sessions (dict): User OAuth sessions indexed by server name.
        user_oauth_tools (dict): User OAuth tools indexed by server name.
        user_tz (str): User's timezone string.
        error_message (str, optional): Error message to display.

    Returns:
        List[Block]: List of Block Kit blocks.
    """
    blocks: list[Block] = []

    if error_message:
        blocks.append(
            SectionBlock(
                text=MarkdownTextObject(text=f":warning: *Error:* {error_message}")
            )
        )
        return blocks

    no_auth_servers = get_no_auth_servers_from_config(mcp_config)
    blocks.extend(build_no_auth_servers_section(no_auth_servers))

    mcp_servers = []
    oauth_servers = get_oauth_servers_from_config(mcp_config)

    for index, server in enumerate(oauth_servers):
        server_name = server["name"]
        auth_url = user_oauth_urls.get(server_name)
        oauth_verification_code = user_oauth_verification_codes.get(server_name)
        session_data = user_oauth_sessions.get(server_name)
        has_valid_session = server_name in user_oauth_sessions
        has_cached_tools = user_oauth_tools.get(server_name) is not None

        mcp_servers.append(
            {
                "index": index,
                "server": server,
                "auth_url": auth_url,
                "oauth_verification_code": oauth_verification_code,
                "session_data": session_data,
                "has_valid_session": has_valid_session,
                "has_cached_tools": has_cached_tools,
            }
        )

    if mcp_servers:
        blocks.extend(build_oauth_servers_section(mcp_servers, user_tz))

    return blocks


def build_no_auth_servers_section(mcp_servers: list[dict[str, str]]) -> list[Block]:
    """
    Build section for servers without authentication.

    Args:
        mcp_servers (list[dict[str, str]]): List of no-auth MCP server info.

    Returns:
        List[Block]: Block Kit blocks for no-auth servers.
    """
    blocks: list[Block] = []

    blocks.append(
        HeaderBlock(text=PlainTextObject(text="🌐 MCP Servers without Authentication"))
    )

    if not mcp_servers:
        blocks.append(
            SectionBlock(text=MarkdownTextObject(text="No servers configured."))
        )
        return blocks

    for server in mcp_servers:
        # No-auth servers are always active, so they're always enabled
        server_display = format_server_display(
            server_name=server["name"],
            is_enabled=True,
            expires_at=None,
            user_tz="UTC",  # timezone doesn't matter since no expiry
        )
        blocks.append(SectionBlock(text=MarkdownTextObject(text=server_display)))

    return blocks


def build_oauth_servers_section(mcp_servers: list[dict], user_tz: str) -> list[Block]:
    """
    Build section for servers requiring authentication.

    Args:
        mcp_servers (List[dict]): List of server data with authentication status.
        user_tz (str): User's timezone string.

    Returns:
        List[Block]: Block Kit blocks for auth servers.
    """
    blocks: list[Block] = []

    if not mcp_servers:
        return blocks

    blocks.append(
        HeaderBlock(text=PlainTextObject(text="🔒 MCP Servers with Authentication"))
    )

    for data in mcp_servers:
        index = data["index"]
        server = data["server"]
        auth_url = data["auth_url"]
        oauth_verification_code = data["oauth_verification_code"]
        session_data = data["session_data"]
        has_valid_session = data["has_valid_session"]
        has_cached_tools = data["has_cached_tools"]
        is_fetching_tools = has_valid_session and not has_cached_tools

        server_name = server["name"]

        # Use format_server_display for consistent formatting
        expires_at = session_data.get("expires_at") if session_data else None
        is_enabled = has_valid_session and has_cached_tools
        server_display = format_server_display(
            server_name=server_name,
            is_enabled=is_enabled,
            expires_at=expires_at,
            user_tz=user_tz,
        )

        blocks.append(SectionBlock(text=MarkdownTextObject(text=server_display)))

        if has_valid_session and has_cached_tools:
            blocks.append(
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="Disable"),
                            action_id=f"{DISABLE_MCP_OAUTH_ACTION_PREFIX}{index}",
                        )
                    ]
                )
            )
        elif is_fetching_tools:
            blocks.append(
                SectionBlock(text=MarkdownTextObject(text="⏳ Fetching tools..."))
            )
        elif auth_url and auth_url != OAUTH_URL_PROCESSING:
            oauth_verification_code_display = oauth_verification_code or ""
            auth_text = f"🔗 <{auth_url}|Click to authorize> / Code: `{oauth_verification_code_display}`"
            blocks.append(SectionBlock(text=MarkdownTextObject(text=auth_text)))
            blocks.append(
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="Cancel"),
                            action_id=f"{CANCEL_MCP_OAUTH_ACTION_PREFIX}{index}",
                        )
                    ]
                )
            )
        elif auth_url == OAUTH_URL_PROCESSING:
            blocks.append(
                SectionBlock(text=MarkdownTextObject(text="⏳ Please wait..."))
            )
            blocks.append(
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="Cancel"),
                            action_id=f"{CANCEL_MCP_OAUTH_ACTION_PREFIX}{index}",
                        )
                    ]
                )
            )
        else:
            blocks.append(
                ActionsBlock(
                    elements=[
                        ButtonElement(
                            text=PlainTextObject(text="Enable"),
                            action_id=f"{ENABLE_MCP_OAUTH_ACTION_PREFIX}{index}",
                            style="primary",
                        )
                    ]
                )
            )

    return blocks


def build_home_tab_view(
    mcp_config: dict,
    user_oauth_urls: dict[str, str],
    user_oauth_verification_codes: dict[str, str],
    user_oauth_sessions: dict[str, dict],
    user_oauth_tools: dict[str, list[dict]],
    user_tz: str,
    error_message: str | None = None,
) -> View:
    """
    Build complete home tab view with all blocks.

    Args:
        mcp_config (dict): MCP configuration.
        user_oauth_urls (dict): OAuth URLs indexed by server name for the user.
        user_oauth_verification_codes (dict): OAuth verification codes indexed by server name for the user.
        user_oauth_sessions (dict): User OAuth sessions indexed by server name.
        user_oauth_tools (dict): User OAuth tools indexed by server name.
        user_tz (str): User's timezone string.
        error_message (str, optional): Error message to display.

    Returns:
        View: Complete home tab view.
    """
    blocks = build_home_tab_blocks(
        mcp_config,
        user_oauth_urls,
        user_oauth_verification_codes,
        user_oauth_sessions,
        user_oauth_tools,
        user_tz,
        error_message,
    )
    return View(type="home", blocks=blocks)
