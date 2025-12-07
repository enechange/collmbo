"""
This module contains middleware functions for the Slack Bolt app.
"""

import logging
from collections.abc import Callable

from slack_bolt import BoltContext, BoltResponse
from slack_sdk.web import WebClient

from app.bolt_logic import extract_user_id_from_context, should_skip_event


def before_authorize(
    body: dict,
    payload: dict,
    next_: Callable[[], None],
) -> BoltResponse | None:
    """
    Skip message changed/deleted events to reduce unnecessary workload.

    Especially, "message_changed" events can be triggered many times when the app rapidly updates
    its reply.

    Args:
        body (dict): The request body.
        payload (dict): The request payload.
        next_ (Callable[[], None]): The next middleware function to call.

    Returns:
        Optional[BoltResponse]: A BoltResponse object if the event is skipped, None otherwise.
    """
    if should_skip_event(body, payload):
        logging.debug(
            "Skipped the following middleware and listeners "
            f"for this message event (subtype: {payload.get('subtype')})"
        )
        return BoltResponse(status=200, body="")
    next_()
    return None


def set_locale(
    context: BoltContext,
    client: WebClient,
    next_: Callable[[], None],
) -> None:
    """
    Set the locale for the user based on their Slack profile.

    Args:
        context (BoltContext): The Bolt context object.
        client (WebClient): The Slack WebClient instance.
        next_ (Callable[[], None]): The next middleware function to call.

    Returns:
        None
    """
    if user_id := extract_user_id_from_context(context):
        user_info = client.users_info(user=user_id, include_locale=True)
        user: dict = user_info.get("user", {})
        context["locale"] = user.get("locale")
    else:
        context["locale"] = None
    next_()
