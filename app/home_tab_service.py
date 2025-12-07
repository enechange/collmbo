"""
Service functions for home tab that have side effects or external dependencies.
"""

from slack_sdk import WebClient

from app.home_tab_logic import build_home_tab_view
from app.mcp.config_service import get_mcp_config
from app.mcp.oauth_control_service import (
    get_user_oauth_urls,
    get_user_oauth_verification_codes,
)
from app.mcp.oauth_tools_service import (
    get_user_oauth_mcp_tools,
    get_user_oauth_sessions,
)


def get_user_timezone(client: WebClient, user_id: str) -> str:
    """
    Get user's timezone from Slack API.

    Args:
        client (WebClient): Slack WebClient instance.
        user_id (str): User ID.

    Returns:
        str: User's timezone string (defaults to UTC if unavailable).
    """
    try:
        user_info = client.users_info(user=user_id)
        if user_info.get("ok"):
            user_data = user_info.get("user")
            if user_data and hasattr(user_data, "get"):
                return user_data.get("tz", "UTC")
    except Exception:
        pass
    return "UTC"


def update_home_tab(
    client: WebClient,
    user_id: str,
    error_message: str | None = None,
) -> None:
    """
    Update home tab by fetching all data from mcp_service.

    Args:
        client (WebClient): Slack WebClient instance.
        user_id (str): User ID.
        error_message (str, optional): Error message to display.
    """
    user_tz = get_user_timezone(client, user_id)
    view = build_home_tab_view(
        mcp_config=get_mcp_config(),
        user_oauth_urls=get_user_oauth_urls(user_id),
        user_oauth_verification_codes=get_user_oauth_verification_codes(user_id),
        user_oauth_sessions=get_user_oauth_sessions(user_id),
        user_oauth_tools=get_user_oauth_mcp_tools(user_id),
        user_tz=user_tz,
        error_message=error_message,
    )
    client.views_publish(user_id=user_id, view=view)
