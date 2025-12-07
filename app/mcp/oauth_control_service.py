"""
Service functions for MCP servers with OAuth authentication.
"""

import asyncio
import concurrent.futures
import time
from typing import Callable

from slack_sdk import WebClient

from app.mcp.agentcore_service import (
    cancel_oauth_polling,
    get_oauth_polling_status,
    initiate_oauth_flow_with_callback,
)
from app.mcp.config_service import (
    get_agentcore_region,
    get_auth_session_duration_minutes,
    get_oauth_callback_url,
    get_oauth_server,
    get_workload_name,
)
from app.mcp.oauth_tools_service import (
    clear_user_oauth_session,
    fetch_mcp_oauth_tools,
    set_user_oauth_session,
)

OAUTH_URL_PROCESSING = "processing"

user_oauth_urls: dict[str, dict[str, str]] = {}
user_oauth_verification_codes: dict[str, dict[str, str]] = {}


def has_running_loop() -> bool:
    """
    Check if there's a running asyncio event loop.

    Returns:
        bool: True if there's a running loop, False otherwise.
    """
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def create_auth_url_callback(
    client: WebClient,
    user_id: str,
    server_name: str,
    on_update: Callable,
):
    """
    Create callback function for handling auth URL.

    Args:
        user_id (str): User ID.
        server_name (str): Server name.
        client: Slack WebClient instance.
        on_update: UI update callback function.

    Returns:
        Callable: Auth URL callback function.
    """

    def on_auth_url_callback(auth_url: str, oauth_verification_code: str):
        # Check if OAuth was cancelled before setting auth URL
        if get_oauth_polling_status(user_id, server_name):
            set_user_oauth_url(
                user_id=user_id,
                server_name=server_name,
                auth_url=auth_url,
            )
            set_user_oauth_oauth_verification_code(
                user_id=user_id,
                server_name=server_name,
                oauth_verification_code=oauth_verification_code,
            )
            on_update(client, user_id)

    return on_auth_url_callback


def create_token_callback(
    client: WebClient,
    user_id: str,
    server_name: str,
    server_url: str,
    on_update: Callable,
):
    """
    Create callback function for handling OAuth token.

    Args:
        user_id (str): User ID.
        server_name (str): Server name.
        server_url (str): Server URL.
        client: Slack WebClient instance.
        on_update: UI update callback function.

    Returns:
        Callable: Token callback function.
    """

    async def on_token_callback(token: str):
        duration_minutes = get_auth_session_duration_minutes()
        expires_at = int(time.time()) + (duration_minutes * 60)

        set_user_oauth_session(
            user_id=user_id,
            server_name=server_name,
            token=token,
            expires_at=expires_at,
        )

        clear_user_oauth_url(user_id, server_name)
        clear_user_oauth_oauth_verification_code(user_id, server_name)
        on_update(client, user_id)

        try:
            await fetch_mcp_oauth_tools(
                user_id=user_id,
                server_name=server_name,
                server_url=server_url,
                token=token,
            )
            on_update(client, user_id)
        except Exception as e:
            # If tool fetching fails, clear the session to return to disabled state
            clear_user_oauth_session(user_id, server_name)
            # Re-raise the exception to maintain error logging and debugging capability
            raise e

    return on_token_callback


def create_timeout_callback(
    client: WebClient,
    user_id: str,
    server_name: str,
    on_update: Callable,
):
    """
    Create callback function for handling OAuth timeout.

    Args:
        client: Slack WebClient instance.
        user_id (str): User ID.
        server_name (str): Server name.
        on_update: UI update callback function.

    Returns:
        Callable: Timeout callback function.
    """

    def on_timeout_callback():
        clear_user_oauth_url(user_id, server_name)
        clear_user_oauth_oauth_verification_code(user_id, server_name)
        on_update(client, user_id)

    return on_timeout_callback


def enable_user_oauth_session(
    client: WebClient,
    user_id: str,
    server_index: int,
    on_update: Callable,
) -> None:
    """
    Enable OAuth session for a user and server.

    Args:
        client: Slack WebClient instance.
        user_id (str): User ID.
        server_index (int): Server index.
        on_update: Callback function to update UI.
    """
    server = get_oauth_server(server_index)
    server_name = server["name"]

    set_user_oauth_url_as_processing(user_id, server_name)
    on_update(client, user_id)

    on_auth_url_callback = create_auth_url_callback(
        client=client,
        user_id=user_id,
        server_name=server_name,
        on_update=on_update,
    )
    on_token_callback = create_token_callback(
        client=client,
        user_id=user_id,
        server_name=server_name,
        server_url=server["url"],
        on_update=on_update,
    )
    on_timeout_callback = create_timeout_callback(
        client=client,
        user_id=user_id,
        server_name=server_name,
        on_update=on_update,
    )

    provider_name = server.get("agentcore_provider")
    if not provider_name:
        raise ValueError(f"Invalid AgentCore provider for server: {server_name}")

    async def run_oauth_flow():
        await initiate_oauth_flow_with_callback(
            region=get_agentcore_region(),
            workload_name=get_workload_name(),
            user_id=user_id,
            server_name=server_name,
            provider_name=provider_name,
            scopes=server.get("scopes", []),
            callback_url=get_oauth_callback_url(),
            on_auth_url_callback=on_auth_url_callback,
            on_token_callback=on_token_callback,
            on_timeout_callback=on_timeout_callback,
        )

    if has_running_loop():
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, run_oauth_flow())
            future.result()
    else:
        asyncio.run(run_oauth_flow())


def disable_user_oauth_session(
    client: WebClient,
    user_id: str,
    server_index: int,
    on_update: Callable,
) -> None:
    """
    Disable OAuth session for a user and server.

    Args:
        client: Slack WebClient instance.
        user_id (str): User ID.
        server_index (int): Server index.
        on_update: Callback function to update UI.
    """
    server = get_oauth_server(server_index)
    clear_user_oauth_session(user_id, server["name"])
    clear_user_oauth_url(user_id, server["name"])
    clear_user_oauth_oauth_verification_code(user_id, server["name"])
    on_update(client, user_id)


def cancel_user_oauth_polling(
    client: WebClient,
    user_id: str,
    server_index: int,
    on_update: Callable,
) -> None:
    """
    Cancel OAuth polling for a user and server.

    Args:
        client: Slack WebClient instance.
        user_id (str): User ID.
        server_index (int): Server index.
        on_update: Callback function to update UI.
    """
    server = get_oauth_server(server_index)
    server_name = server["name"]

    # Cancel the polling if it exists
    cancel_oauth_polling(user_id, server_name)

    # Clear the OAuth URL and oauth_verification_code to reset the UI state
    clear_user_oauth_url(user_id, server_name)
    clear_user_oauth_oauth_verification_code(user_id, server_name)

    # Update the UI
    on_update(client, user_id)


def set_user_oauth_url(user_id: str, server_name: str, auth_url: str) -> None:
    """
    Set OAuth authorization URL for a user and server.

    Args:
        user_id (str): User ID.
        server_name (str): Server name.
        auth_url (str): Authorization URL.
    """
    if user_id not in user_oauth_urls:
        user_oauth_urls[user_id] = {}
    user_oauth_urls[user_id][server_name] = auth_url


def set_user_oauth_url_as_processing(user_id: str, server_name: str) -> None:
    """
    Set OAuth URL as processing state for a user and server.

    Args:
        user_id (str): User ID.
        server_name (str): Server name.
    """
    set_user_oauth_url(user_id, server_name, OAUTH_URL_PROCESSING)


def clear_user_oauth_url(user_id: str, server_name: str) -> None:
    """
    Clear OAuth authorization URL for a user and server.

    Args:
        user_id (str): User ID.
        server_name (str): Server name.
    """
    if user_id in user_oauth_urls:
        user_oauth_urls[user_id].pop(server_name, None)


def get_user_oauth_urls(user_id: str) -> dict[str, str]:
    """
    Get OAuth URLs for a specific user.

    Args:
        user_id (str): User ID.

    Returns:
        dict[str, str]: OAuth URLs indexed by server name for the user.
    """
    return user_oauth_urls.get(user_id, {})


def get_all_user_oauth_urls() -> dict[str, dict[str, str]]:
    """
    Get all user OAuth URLs.

    Returns:
        dict[str, dict[str, str]]: All OAuth URLs indexed by user ID and server name.
    """
    return user_oauth_urls


def set_user_oauth_oauth_verification_code(
    user_id: str, server_name: str, oauth_verification_code: str
) -> None:
    """
    Set OAuth oauth_verification_code for a user and server.

    Args:
        user_id (str): User ID.
        server_name (str): Server name.
        oauth_verification_code (str): Random oauth_verification_code used in AgentCore user ID.
    """
    if user_id not in user_oauth_verification_codes:
        user_oauth_verification_codes[user_id] = {}
    user_oauth_verification_codes[user_id][server_name] = oauth_verification_code


def clear_user_oauth_oauth_verification_code(user_id: str, server_name: str) -> None:
    """
    Clear OAuth oauth_verification_code for a user and server.

    Args:
        user_id (str): User ID.
        server_name (str): Server name.
    """
    if user_id in user_oauth_verification_codes:
        user_oauth_verification_codes[user_id].pop(server_name, None)


def get_user_oauth_verification_codes(user_id: str) -> dict[str, str]:
    """
    Get OAuth verification codes for a specific user.

    Args:
        user_id (str): User ID.

    Returns:
        dict[str, str]: OAuth verification codes indexed by server name for the user.
    """
    return user_oauth_verification_codes.get(user_id, {})
