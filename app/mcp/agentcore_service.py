"""
AgentCore service functions for OAuth authentication.
"""

import asyncio
import logging
import secrets
import time
from collections.abc import Awaitable, Callable

from bedrock_agentcore.services.identity import IdentityClient, TokenPoller

from app.mcp.agentcore_logic import create_agentcore_user_id

# OAuth token polling timeout in seconds
OAUTH_POLLING_TIMEOUT_SECONDS = 300
OAUTH_POLLING_INTERVAL_SECONDS = 5

active_oauth_pollers: dict[str, CancellableTokenPoller] = {}


def create_poller_key(user_id: str, server_name: str) -> str:
    """Create a unique key for tracking pollers by user and server."""
    return f"{user_id}:{server_name}"


class CancellableTokenPoller(TokenPoller):
    """Token poller with cancellation support and custom timeout."""

    def __init__(
        self,
        auth_url: str,
        func: Callable[[], str | None],
        user_id: str,
        server_name: str,
    ):
        """Initialize the cancellable token poller."""
        self.auth_url = auth_url
        self.polling_func = func
        self.user_id = user_id
        self.server_name = server_name
        self.cancelled = False
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            self.logger.addHandler(logging.StreamHandler())

    def cancel(self) -> None:
        """Cancel the token polling."""
        self.cancelled = True

    async def poll_for_token(self) -> str:
        """Poll for a token until it becomes available, timeout occurs, or cancelled."""
        start_time = time.time()
        while (
            not self.cancelled
            and time.time() - start_time < OAUTH_POLLING_TIMEOUT_SECONDS
        ):
            await asyncio.sleep(OAUTH_POLLING_INTERVAL_SECONDS)

            if self.cancelled:
                raise asyncio.CancelledError("Token polling was cancelled")

            resp = self.polling_func()
            if resp is not None:
                self.logger.info("Token is ready")
                return resp

        if self.cancelled:
            raise asyncio.CancelledError("Token polling was cancelled")

        # Timeout occurred - log and raise exception
        self.logger.info(
            "Authorization timed out after %d seconds", OAUTH_POLLING_TIMEOUT_SECONDS
        )
        raise TimeoutError("Authorization timed out")


def shutdown_all_oauth_pollers() -> None:
    """Cancel all active OAuth token pollers."""
    for poller in active_oauth_pollers.values():
        try:
            poller.cancel()
        except Exception:
            logging.debug("Failed to cancel OAuth poller")
    active_oauth_pollers.clear()


def cancel_oauth_polling(user_id: str, server_name: str) -> bool:
    """
    Cancel the OAuth polling for a specific user and server.

    Args:
        user_id (str): User ID.
        server_name (str): Server name.

    Returns:
        bool: True if a poller was cancelled, False otherwise.
    """
    key = create_poller_key(user_id, server_name)
    if key in active_oauth_pollers:
        active_oauth_pollers[key].cancel()
        del active_oauth_pollers[key]
        return True
    return False


def get_oauth_polling_status(user_id: str, server_name: str) -> bool:
    """
    Check if OAuth polling is active (not cancelled) for a specific user and server.

    Args:
        user_id (str): User ID.
        server_name (str): Server name.

    Returns:
        bool: True if polling is active and not cancelled, False otherwise.
    """
    key = create_poller_key(user_id, server_name)
    if key in active_oauth_pollers:
        return not active_oauth_pollers[key].cancelled
    return False


def create_workload_identity_token(
    client: IdentityClient,
    workload_name: str,
    agentcore_user_id: str,
    callback_urls: list[str],
) -> str:
    """
    Get workload identity token from AgentCore.

    Args:
        client (IdentityClient): AgentCore Identity client.
        workload_name (str): Workload name for AgentCore.
        agentcore_user_id (str): Salted user identifier for AgentCore.
        callback_urls (list[str]): List of allowed OAuth callback URLs.

    Returns:
        str: Workload identity token.

    Raises:
        Exception: If token creation fails.
    """
    try:
        workload_identity = client.create_workload_identity(
            name=workload_name,
            allowed_resource_oauth_2_return_urls=callback_urls,
        )
        workload_identity_name = workload_identity["name"]
    except Exception as e:
        if "already exists" in str(e):
            workload_identity_name = workload_name
            # Update existing workload with callback URLs
            if callback_urls:
                client.update_workload_identity(
                    name=workload_name,
                    allowed_resource_oauth_2_return_urls=callback_urls,
                )
        else:
            raise e
    token_response = client.get_workload_access_token(
        workload_identity_name,
        user_id=agentcore_user_id,
    )
    return token_response["workloadAccessToken"]


async def initiate_oauth_flow_with_callback(
    region: str,
    workload_name: str,
    user_id: str,
    server_name: str,
    provider_name: str,
    scopes: list[str],
    callback_url: str,
    on_auth_url_callback: Callable[[str, str], None],
    on_token_callback: Callable[[str], Awaitable[None]],
    on_timeout_callback: Callable[[], None] | None = None,
) -> None:
    """
    Initiate OAuth flow using callbacks for auth URL and token.

    Args:
        region (str): AWS region.
        workload_name (str): Workload name for AgentCore.
        user_id (str): User ID.
        server_name (str): MCP server name.
        provider_name (str): OAuth provider name.
        scopes (list[str]): OAuth scopes.
        callback_url (str): OAuth callback URL for AgentCore Identity.
        on_auth_url_callback: Callback function to handle auth URL display (receives auth_url and oauth_verification_code).
        on_token_callback: Callback function to handle token receipt.

    Returns:
        None: Results are delivered via callbacks.

    Raises:
        Exception: If the flow initiation fails.
    """
    # Generate a new random suffix each time to avoid AgentCore token caching
    random_suffix = secrets.token_hex()
    agentcore_user_id = create_agentcore_user_id(user_id, random_suffix)
    client = IdentityClient(region=region)

    # Create or update workload identity with callback URL
    callback_urls = [callback_url] if callback_url else []
    identity_token = create_workload_identity_token(
        client=client,
        workload_name=workload_name,
        agentcore_user_id=agentcore_user_id,
        callback_urls=callback_urls,
    )

    # Extract verification code (last 8 chars) and prefix for session binding
    oauth_verification_code = random_suffix[-8:]
    agentcore_user_id_without_last8 = agentcore_user_id[:-8]

    # Create cancellable token poller with custom_state for session binding
    poller = CancellableTokenPoller(
        auth_url="pending",  # Will be updated in the callback
        func=lambda: client.dp_client.get_resource_oauth2_token(
            resourceCredentialProviderName=provider_name,
            scopes=scopes,
            oauth2Flow="USER_FEDERATION",
            workloadIdentityToken=identity_token,
            customState=agentcore_user_id_without_last8,
            resourceOauth2ReturnUrl=callback_url,
        ).get("accessToken", None),
        user_id=user_id,
        server_name=server_name,
    )
    key = create_poller_key(user_id, server_name)
    active_oauth_pollers[key] = poller

    try:
        # Check if cancelled before starting token retrieval
        if poller.cancelled:
            return

        token = await client.get_token(
            provider_name=provider_name,
            scopes=scopes,
            agent_identity_token=identity_token,
            on_auth_url=lambda auth_url: on_auth_url_callback(
                auth_url, oauth_verification_code
            ),
            auth_flow="USER_FEDERATION",
            callback_url=callback_url,
            custom_state=agentcore_user_id_without_last8,
            token_poller=poller,
        )

        # Check if cancelled before processing token
        if poller.cancelled:
            return

        if token:
            await on_token_callback(token)
    except TimeoutError:
        # Timeout occurred - reset UI state
        if on_timeout_callback:
            on_timeout_callback()
    finally:
        # Remove poller from active list
        if key in active_oauth_pollers:
            del active_oauth_pollers[key]
