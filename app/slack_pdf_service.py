"""
This module provides functionality to handle PDFs from Slack files.
"""

import logging

from app.message_logic import build_pdf_file_item
from app.slack_file_service import get_slack_file_content


def build_pdf_file_items_from_slack_files(
    *,
    bot_token: str,
    files: list[dict] | None,
    pdf_slots: int = 5,
    used_pdf_slots: int = 0,
) -> list[dict]:
    """
    Build PDF file items from Slack files.

    Args:
        - bot_token (str): The bot token for Slack API.
        - files (Optional[list[dict]]): The list of files from Slack.
        - pdf_slots (int): The number of PDF slots available.
        - used_pdf_slots (int): The number of PDF slots already used.

    Returns:
        - list[dict]: A list of dictionaries containing PDF file content.
    """
    pdf_file_items: list[dict] = []
    if not files:
        return pdf_file_items

    for file in files:
        if len(pdf_file_items) >= (pdf_slots - used_pdf_slots):
            break
        if file.get("mimetype") != "application/pdf":
            continue
        file_url = file.get("url_private")
        if file_url is None:
            logging.warning("Skipped a PDF file due to missing 'url_private'")
            continue

        pdf_bytes = get_slack_file_content(
            url=file_url,
            token=bot_token,
            expected_content_types=["application/pdf", "binary/octet-stream"],
        )
        if not pdf_bytes.startswith(b"%PDF-"):
            logging.warning(f"Skipped invalid PDF (url: {file_url})")
            continue

        file_item = build_pdf_file_item(file.get("name"), pdf_bytes)
        pdf_file_items.append(file_item)

    return pdf_file_items
