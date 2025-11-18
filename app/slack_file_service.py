"""
This module provides a function to download files from Slack.
"""

import httpx
from slack_sdk.errors import SlackApiError


def get_slack_file_content(
    *,
    url: str,
    token: str,
    expected_content_types: list[str],
) -> bytes:
    """
    Get the content of a Slack file.

    Args:
        - url (str): The URL of the Slack file.
        - token (str): The bot token for Slack API.
        - expected_content_types (list[str]): A list of expected content types.

    Returns:
        - bytes: The content of the Slack file.
    """
    response = httpx.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
        follow_redirects=True,
    )
    if response.status_code != 200:
        raise SlackApiError(
            f"Request to {url} failed with status code {response.status_code}", response
        )
    content_type = response.headers.get("Content-Type", "")
    if content_type.startswith("text/html"):
        raise SlackApiError(
            f"You don't have the permission to download this file: {url}", response
        )
    if content_type not in expected_content_types:
        raise SlackApiError(
            f"The responded content-type is not expected: {content_type}", response
        )
    return response.content
