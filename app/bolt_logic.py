"""
This module contains logic for handling Slack events and interactions.
"""

from slack_bolt import BoltContext
from slack_bolt.authorization.authorize_result import AuthorizeResult
from slack_bolt.request.payload_utils import is_event
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler


def append_rate_limit_retry_handler(retry_handlers: list, max_retry_count: int) -> None:
    """
    Append a RateLimitErrorRetryHandler to the list of retry handlers.

    Args:
        retry_handlers (list): The list of existing retry handlers.
        max_retry_count (int): The maximum number of retries for rate limit errors.

    Returns:
        None
    """
    retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=max_retry_count))


def should_skip_event(body: dict, payload: dict) -> bool:
    """
    Determine if the event should be skipped based on its type and subtype.

    Args:
        body (dict): The request body.
        payload (dict): The request payload.

    Returns:
        bool: True if the event should be skipped, False otherwise.
    """
    return (
        is_event(body)
        and payload.get("type") == "message"
        and payload.get("subtype") in ["message_changed", "message_deleted"]
    )


def extract_user_id_from_context(context: BoltContext) -> str | None:
    """
    Extract the user ID from a Bolt context object.

    Args:
        context (BoltContext): The Bolt context object.

    Returns:
        Optional[str]: The user ID if available, None otherwise.
    """
    return context.actor_user_id or context.user_id


def is_post_from_bot(payload: dict) -> bool:
    """
    Check if the post is from a bot.

    Args:
        payload (dict): The Slack post payload.

    Returns:
        bool: True if the post is from a bot, False otherwise.
    """
    return payload.get("bot_id") is not None


def is_post_in_dm(payload: dict) -> bool:
    """
    Check if the post is in a direct message (DM) channel.

    Args:
        payload (dict): The Slack post payload.

    Returns:
        bool: True if the post is in a DM channel, False otherwise.
    """
    return payload.get("channel_type") == "im"


def is_post_mentioned(bot_user_id: str | None, post: dict | None) -> bool:
    """
    Checks whether the bot is mentioned in a Slack post.

    Args:
        bot_user_id (Optional[str]): The bot's user ID.
        post (Optional[dict]): The Slack post.
    Returns:
        bool: True if the bot is mentioned, False otherwise.
    """
    return post is not None and f"<@{bot_user_id}>" in post.get("text", "")


def determine_thread_ts_to_reply(payload: dict) -> str | None:
    """
    Determine the thread timestamp (thread_ts) to reply to.

    Args:
        payload (dict): The Slack post payload.

    Returns:
        Optional[str]: The thread timestamp to reply to, or None if not applicable.
    """
    thread_ts = payload.get("thread_ts")
    if thread_ts is None and not is_post_in_dm(payload):
        thread_ts = payload["ts"]
    return thread_ts


def has_read_files_scope(authorize_result: AuthorizeResult | None) -> bool:
    """
    Check if the bot has the "files:read" scope.

    Args:
        authorize_result (Optional[AuthorizeResult]): The authorization result.

    Returns:
        bool: True if the bot has the "files:read" scope, False otherwise.
    """
    return (
        authorize_result is not None
        and authorize_result.bot_scopes is not None
        and "files:read" in authorize_result.bot_scopes
    )
