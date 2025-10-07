"""
This module contains the logic for responding to new Slack posts.
"""

import logging
import time
from typing import Optional

from litellm.exceptions import ContextWindowExceededError, Timeout
from slack_bolt import BoltContext
from slack_sdk.web import SlackResponse, WebClient

from app.bolt_logic import (
    determine_thread_ts_to_reply,
    extract_user_id_from_context,
    has_read_files_scope,
    is_post_from_bot,
    is_post_in_dm,
    is_post_mentioned,
)
from app.env import (
    IMAGE_FILE_ACCESS_ENABLED,
    LITELLM_TIMEOUT_SECONDS,
    PDF_FILE_ACCESS_ENABLED,
    PROMPT_CACHING_ENABLED,
    REDACT_CREDIT_CARD_PATTERN,
    REDACT_EMAIL_PATTERN,
    REDACT_PHONE_PATTERN,
    REDACT_SSN_PATTERN,
    REDACT_USER_DEFINED_PATTERN,
    REDACTION_ENABLED,
    SYSTEM_TEXT,
    TRANSLATE_MARKDOWN,
)
from app.home_tab_logic import (
    extract_cancel_server_index,
    extract_disable_server_index,
    extract_enable_server_index,
)
from app.home_tab_service import update_home_tab
from app.litellm_service import reply_to_slack_with_litellm
from app.mcp.oauth_control_service import (
    cancel_user_oauth_polling,
    disable_user_oauth_session,
    enable_user_oauth_session,
)
from app.mcp.oauth_tools_service import expire_old_oauth_sessions
from app.message_logic import (
    build_assistant_message,
    build_slack_user_prefixed_text,
    build_system_message,
    build_user_message,
    filter_replies_after_last_marker,
    maybe_redact_string,
    maybe_set_cache_points,
    maybe_slack_to_markdown,
    remove_bot_mention,
    unescape_slack_formatting,
)
from app.slack_image_service import build_image_url_items_from_slack_files
from app.slack_pdf_service import build_pdf_file_items_from_slack_files
from app.translation_service import translate

LOADING_TEXT = ":hourglass_flowing_sand: Wait a second, please ..."
TIMEOUT_ERROR_MESSAGE = (
    f":warning: Apologies! It seems that the AI didn't respond within the "
    f"{LITELLM_TIMEOUT_SECONDS}-second timeframe. Please try your request again later. "
    "If you wish to extend the timeout limit, you may consider deploying this app with "
    "customized settings on your infrastructure. :bow:"
)
CONTEXT_WINDOW_EXCEEDED_ERROR_MESSAGE = (
    ":warning: The conversation has grown too long for the AI to process. "
    "To continue, only your upcoming messages will be used and previous ones will be ignored."
)

REDACT_PATTERNS = [
    (REDACT_EMAIL_PATTERN, "[EMAIL]"),
    (REDACT_CREDIT_CARD_PATTERN, "[CREDIT CARD]"),
    (REDACT_PHONE_PATTERN, "[PHONE]"),
    (REDACT_SSN_PATTERN, "[SSN]"),
    (REDACT_USER_DEFINED_PATTERN, "[REDACTED]"),
]
MAX_PDF_SLOTS = 5


def respond_to_new_post(
    context: BoltContext,
    payload: dict,
    client: WebClient,
) -> None:
    """
    Responds to a new Slack post.

    This function filters irrelevant posts, posts a loading reply,
    builds the conversation history, and sends a response using a language model.

    Args:
        context (BoltContext): The Bolt context object.
        payload (dict): The payload of the incoming Slack post.
        client (WebClient): The Slack WebClient instance.

    Returns:
        None
    """
    if context.channel_id is None:
        raise ValueError("context.channel_id cannot be None")
    user_id = extract_user_id_from_context(context)
    if user_id is None:
        raise ValueError("User ID could not be determined from context")

    if is_post_from_bot(payload):
        return

    wip_reply = None
    try:
        if not (
            is_post_mentioned(context.bot_user_id, payload)
            or is_post_in_dm(payload)
            or has_parent_post_mentioned(context, payload, client)
        ):
            return
        loading_text = translate(context.get("locale"), LOADING_TEXT)
        reply_thread_ts, wip_reply = post_loading_reply(
            client=client,
            channel_id=context.channel_id,
            payload=payload,
            loading_text=loading_text,
        )
        messages = build_messages(
            client=client,
            context=context,
            payload=payload,
            channel_id=context.channel_id,
            user_id=user_id,
        )
        reply_to_slack_with_litellm(
            client=client,
            channel=context.channel_id,
            user_id=user_id,
            thread_ts=reply_thread_ts,
            messages=messages,
            loading_text=loading_text,
            wip_reply=wip_reply,
            timeout_seconds=LITELLM_TIMEOUT_SECONDS,
        )
    except (Timeout, TimeoutError):
        handle_timeout_error(
            client=client,
            channel_id=context.channel_id,
            locale=context.get("locale"),
            wip_reply=wip_reply,
        )
    except ContextWindowExceededError as e:
        handle_context_window_exceeded_error(
            client=client,
            channel_id=context.channel_id,
            e=e,
            wip_reply=wip_reply,
        )
    except Exception as e:
        handle_exception(
            client=client,
            channel_id=context.channel_id,
            e=e,
            wip_reply=wip_reply,
        )


def has_parent_post_mentioned(
    context: BoltContext,
    payload: dict,
    client: WebClient,
) -> bool:
    """
    Checks whether the Slack post should be ignored based on certain conditions.

    Args:
        context (BoltContext): The Bolt context object.
        payload (dict): The payload of the incoming Slack post.
        client (WebClient): The Slack WebClient instance.

    Returns:
        bool: True if the post should be ignored, False otherwise.
    """
    parent_post = find_parent_post(
        client=client,
        channel_id=context.channel_id,
        thread_ts=payload.get("thread_ts"),
    )
    return is_post_mentioned(context.bot_user_id, parent_post)


def find_parent_post(
    client: WebClient, channel_id: Optional[str], thread_ts: Optional[str]
) -> Optional[dict]:
    """
    Finds the parent post of a thread in Slack.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (Optional[str]): The ID of the channel containing the thread.
        thread_ts (Optional[str]): The timestamp of the thread.

    Returns:
        Optional[dict]: The parent post if found, None otherwise.
    """
    if channel_id is None or thread_ts is None:
        return None
    posts: list[dict] = client.conversations_history(
        channel=channel_id,
        latest=thread_ts,
        limit=1,
        inclusive=True,
    ).get("messages", [])
    return posts[0] if posts else None


def post_loading_reply(
    *,
    client: WebClient,
    channel_id: str,
    payload: dict,
    loading_text: str,
) -> tuple[Optional[str], SlackResponse]:
    """
    Posts a loading reply to a Slack post in a channel or thread.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (str): The ID of the channel to reply to.
        payload (dict): The payload of the incoming Slack post.
        loading_text (str): The loading text to display.

    Returns:
        tuple[Optional[str], SlackResponse]: Thread timestamp and Slack API response.
    """
    thread_ts = determine_thread_ts_to_reply(payload)
    wip_reply = client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        text=loading_text,
    )
    return thread_ts, wip_reply


def build_messages(
    *,
    client: WebClient,
    context: BoltContext,
    payload: dict,
    channel_id: str,
    user_id: str,
) -> list[dict]:
    """
    Builds the conversation history for the Slack post.

    Args:
        client (WebClient): The Slack WebClient instance.
        context (BoltContext): The Bolt context object.
        payload (dict): The payload of the incoming Slack post.
        channel_id (str): The ID of the channel where the post was made.
        user_id (str): The ID of the user who made the post.

    Returns:
        list[dict]: A list of messages representing the conversation history.
    """
    system_message = build_system_message(
        system_text_template=SYSTEM_TEXT,
        bot_user_id=context.bot_user_id,
        translate_markdown=TRANSLATE_MARKDOWN,
        prompt_caching_enabled=PROMPT_CACHING_ENABLED,
    )
    replies = get_replies(
        client=client,
        payload=payload,
        channel_id=channel_id,
        user_id=user_id,
    )
    filtered_replies = filter_replies_after_last_marker(
        replies=replies,
        bot_user_id=context.bot_user_id,
        marker_text=CONTEXT_WINDOW_EXCEEDED_ERROR_MESSAGE,
    )
    messages = [system_message] + convert_replies_to_messages(filtered_replies, context)
    maybe_set_cache_points(
        messages=messages,
        prompt_caching_enabled=PROMPT_CACHING_ENABLED,
    )
    return messages


def get_replies(
    *,
    client: WebClient,
    payload: dict,
    channel_id: str,
    user_id: str,
) -> list[dict]:
    """
    Retrieves replies to be used as conversation history based on the context of the incoming Slack
    post.

    Args:
        client (WebClient): The Slack WebClient instance.
        payload (dict): The payload of the incoming Slack post.
        channel_id (str): The ID of the channel where the post was made.
        user_id (str): The ID of the user who made the post.

    Returns:
        list[dict]: A list of replies based on the post context.
    """
    thread_ts = payload.get("thread_ts")
    # In a DM with the bot (not part of a thread)
    if payload.get("channel_type") == "im" and thread_ts is None:
        return get_dm_replies(client, channel_id)
    # In a thread
    if thread_ts is not None:
        return get_thread_replies(client, channel_id, thread_ts)
    # In a channel (not in a thread), with a mention to the bot
    return [
        {
            "text": payload["text"],
            "user": user_id,
            "bot_id": payload.get("bot_id"),
            "files": payload.get("files"),
        }
    ]


def get_thread_replies(
    client: WebClient, channel_id: str, thread_ts: str
) -> list[dict]:
    """
    Retrieves all replies to a Slack thread.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (str): The ID of the channel containing the thread.
        thread_ts (str): The timestamp of the parent post.

    Returns:
        list[dict]: A list of replies in the thread.
    """
    return client.conversations_replies(
        channel=channel_id,
        ts=thread_ts,
        limit=1000,
    ).get("messages", [])


def get_dm_replies(client: WebClient, channel_id: str) -> list[dict]:
    """
    Retrieves recent replies in a direct message (DM) conversation.
    Returns up to 100 messages from the last 24 hours.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (str): The ID of the DM channel.

    Returns:
        list[dict]: A list of replies in the DM conversation.
    """
    cutoff_time = time.time() - 86400  # 24 hours ago
    replies: list[dict] = client.conversations_history(
        channel=channel_id,
        limit=100,
        inclusive=True,
    ).get("messages", [])

    # Filter messages to only include those from the last 24 hours
    recent_replies = [
        message for message in replies if float(message.get("ts", "0")) >= cutoff_time
    ]

    return list(reversed(recent_replies))


def convert_replies_to_messages(
    replies: list[dict],
    context: BoltContext,
) -> list[dict]:
    """
    Converts Slack replies to a list of messages for the language model.

    Args:
        replies (list[dict]): The list of replies to convert.
        context (BoltContext): The Bolt context object.

    Returns:
        list[dict]: A list of messages representing the conversation history.
    """

    # Ignore trailing bot replies (including a loading reply)
    while replies and replies[-1].get("user") == context.bot_user_id:
        replies.pop()

    messages: list[dict] = []
    used_pdf_slots = 0

    # Process replies in reverse order to prioritize recent PDFs and avoid unnecessary downloads
    for reply in reversed(replies):
        text = remove_bot_mention(reply.get("text", ""), context.bot_user_id)
        text = maybe_redact_string(
            input_string=text,
            patterns=REDACT_PATTERNS,
            redaction_enabled=REDACTION_ENABLED,
        )
        text = unescape_slack_formatting(text)
        text = maybe_slack_to_markdown(text, TRANSLATE_MARKDOWN)
        text = build_slack_user_prefixed_text(reply, text)

        if reply["user"] == context.bot_user_id:
            messages.append(build_assistant_message(text))
            continue

        content = [{"type": "text", "text": text}]
        if (
            reply.get("bot_id") is None
            and IMAGE_FILE_ACCESS_ENABLED
            and has_read_files_scope(context.authorize_result)
        ):
            if context.bot_token is None:
                raise ValueError("context.bot_token cannot be None")
            content += build_image_url_items_from_slack_files(
                bot_token=context.bot_token,
                files=reply.get("files"),
            )

        # Only process PDFs if we haven't reached the limit
        if (
            used_pdf_slots < MAX_PDF_SLOTS
            and reply.get("bot_id") is None
            and PDF_FILE_ACCESS_ENABLED
            and has_read_files_scope(context.authorize_result)
        ):
            if context.bot_token is None:
                raise ValueError("context.bot_token cannot be None")
            pdf_file_items = build_pdf_file_items_from_slack_files(
                bot_token=context.bot_token,
                files=reply.get("files"),
                pdf_slots=MAX_PDF_SLOTS,
                used_pdf_slots=used_pdf_slots,
            )

            # Count and add PDFs
            # Note: Prepend PDFs to avoid Bedrock Converse API error
            # (cache control cannot immediately follow document type)
            used_pdf_slots += len(pdf_file_items)
            content = pdf_file_items + content

        messages.append(build_user_message(content))

    # Reverse the messages to restore chronological order
    messages.reverse()
    return messages


def handle_timeout_error(
    *,
    client: WebClient,
    channel_id: str,
    locale: Optional[str],
    wip_reply: Optional[SlackResponse],
):
    """
    Handles timeout errors by updating the loading reply with an error message.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (str): The ID of the channel where the post was made.
        locale (Optional[str]): The locale for translation.
        wip_reply (Optional[SlackResponse]): The loading reply to update.

    Returns:
        None
    """
    if wip_reply is None:
        return
    message_dict: dict = wip_reply.get("message", {})
    text = (
        message_dict.get("text", "") + "\n\n" + translate(locale, TIMEOUT_ERROR_MESSAGE)
    )
    client.chat_update(
        channel=channel_id,
        ts=message_dict.get("ts", ""),
        text=text,
    )


def handle_context_window_exceeded_error(
    *,
    client: WebClient,
    channel_id: str,
    e: ContextWindowExceededError,
    wip_reply: Optional[SlackResponse],
):
    """
    Handles context window exceeded errors by updating the loading reply with an error message.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (str): The ID of the channel where the post was made.
        e (ContextWindowExceededError): The exception that occurred.
        wip_reply (Optional[SlackResponse]): The loading reply to update.

    Returns:
        None
    """
    if wip_reply is None:
        return
    message_dict: dict = wip_reply.get("message", {})
    text = (
        message_dict.get("text", "")
        + "\n\n"
        + CONTEXT_WINDOW_EXCEEDED_ERROR_MESSAGE
        + "\n\n"
        + f"Error: {e}"
    )
    client.chat_update(
        channel=channel_id,
        ts=message_dict.get("ts", ""),
        text=text,
    )


def handle_exception(
    *,
    client: WebClient,
    channel_id: str,
    e: Exception,
    wip_reply: Optional[SlackResponse],
):
    """
    Handles exceptions by updating the loading reply with an error message.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel_id (str): The ID of the channel where the post was made.
        e (Exception): The exception that occurred.
        wip_reply (Optional[SlackResponse]): The loading reply to update.

    Returns:
        None
    """
    message_dict: dict = wip_reply.get("message", {}) if wip_reply else {}
    text = message_dict.get("text", "") + "\n\n" + f":warning: Failed to reply: {e}"
    client.logger.exception(text)
    if wip_reply:
        client.chat_update(
            channel=channel_id,
            ts=message_dict.get("ts", ""),
            text=text,
        )


def handle_app_home_opened(client: WebClient, event: dict) -> None:
    """
    Handle app_home_opened event to display MCP server information.
    Also cleans up expired OAuth sessions.

    Args:
        client (WebClient): Slack WebClient instance.
        event (dict): The app_home_opened event payload.

    Returns:
        None
    """
    user_id = event["user"]
    expire_old_oauth_sessions(user_id)
    try:
        update_home_tab(client=client, user_id=user_id)
    except Exception as e:
        logging.error(f"Failed to update home tab: {e}")
        update_home_tab(
            client=client,
            user_id=user_id,
            error_message="A system error occurred. Please contact your administrator.",
        )


def handle_enable_mcp_oauth_action(body: dict, client: WebClient) -> None:
    """
    Handle enable MCP OAuth action from Slack button.

    Args:
        body (dict): Slack event body.
        client: Slack WebClient instance.

    Returns:
        None
    """
    try:
        server_index = extract_enable_server_index(body["actions"][0]["action_id"])
        enable_user_oauth_session(
            client=client,
            user_id=body["user"]["id"],
            server_index=server_index,
            on_update=update_home_tab,
        )
    except Exception as e:
        logging.error(f"Failed to handle enable auth action: {e}")
        update_home_tab(
            client=client,
            user_id=body["user"]["id"],
            error_message="A system error occurred. Please contact your administrator.",
        )


def handle_disable_mcp_oauth_action(
    body: dict,
    client: WebClient,
) -> None:
    """
    Handle disable authentication action from home tab.

    Args:
        body (dict): Action payload from Slack.
        client (WebClient): Slack WebClient instance.

    Returns:
        None
    """
    try:
        server_index = extract_disable_server_index(body["actions"][0]["action_id"])
        disable_user_oauth_session(
            client=client,
            user_id=body["user"]["id"],
            server_index=server_index,
            on_update=update_home_tab,
        )
    except Exception as e:
        logging.error(f"Failed to handle disable auth action: {e}")
        update_home_tab(
            client=client,
            user_id=body["user"]["id"],
            error_message="A system error occurred. Please contact your administrator.",
        )


def handle_cancel_mcp_oauth_action(
    body: dict,
    client: WebClient,
) -> None:
    """
    Handle cancel OAuth polling action from home tab.

    Args:
        body (dict): Action payload from Slack.
        client (WebClient): Slack WebClient instance.

    Returns:
        None
    """
    try:
        server_index = extract_cancel_server_index(body["actions"][0]["action_id"])
        cancel_user_oauth_polling(
            client=client,
            user_id=body["user"]["id"],
            server_index=server_index,
            on_update=update_home_tab,
        )
    except Exception as e:
        logging.error(f"Failed to handle cancel auth action: {e}")
        update_home_tab(
            client=client,
            user_id=body["user"]["id"],
            error_message="A system error occurred. Please contact your administrator.",
        )
