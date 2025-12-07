"""
This module provides functionality to handle images from Slack files.
"""

import logging
from io import BytesIO

from PIL import Image

from app.message_logic import build_image_url_item
from app.slack_file_service import get_slack_file_content

SUPPORTED_IMAGE_FORMATS = ["jpeg", "png", "gif", "webp"]
SUPPORTED_IMAGE_MIME_TYPES = [f"image/{fmt}" for fmt in SUPPORTED_IMAGE_FORMATS]


def build_image_url_items_from_slack_files(
    *,
    bot_token: str,
    files: list[dict] | None,
) -> list[dict]:
    """
    Build image URL items from Slack files.

    Args:
        - bot_token (str): The bot token for Slack API.
        - files (Optional[list[dict]]): The list of files from Slack.

    Returns:
        - list[dict]: A list of dictionaries containing image content.
    """
    image_url_items: list[dict] = []
    if not files:
        return image_url_items

    for file in files:
        mime_type = file.get("mimetype")
        if mime_type not in SUPPORTED_IMAGE_MIME_TYPES:
            continue
        file_url = file.get("url_private")
        if file_url is None:
            logging.warning("Skipped an image file due to missing 'url_private'")
            continue

        image_bytes = get_slack_file_content(
            url=file_url,
            token=bot_token,
            expected_content_types=SUPPORTED_IMAGE_MIME_TYPES,
        )
        try:
            image = Image.open(BytesIO(image_bytes))
        except Exception as e:
            raise RuntimeError(f"Failed to open an image data: {e}") from e
        if image.format is None:
            logging.warning(f"Skipped image with unknown format (url: {file_url})")
            continue
        if image.format.lower() not in SUPPORTED_IMAGE_FORMATS:
            logging.info(
                f"Skipped unsupported image (url: {file_url}, format: {image.format})"
            )
            continue

        image_url_item = build_image_url_item(mime_type, image_bytes)
        image_url_items.append(image_url_item)

    return image_url_items
