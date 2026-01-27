"""
This module loads and exposes environment variables used by the app.
"""

import os

DEFAULT_SYSTEM_TEXT = """
You are a bot in a slack chat room. You might receive messages from multiple people.
Format bold text *like this*, italic text _like this_ and strikethrough text ~like this~.
Slack user IDs match the regex `<@U.*?>`.
Your Slack user ID is <@{bot_user_id}>.
Each message has the author's Slack user ID prepended, like the regex `^<@U.*?>: ` followed by the message text.
Only mention users (e.g., `<@U12345>`) when you are explicitly instructed to do so. Otherwise, do not mention users.
"""
SYSTEM_TEXT = os.environ.get("LITELLM_SYSTEM_TEXT", DEFAULT_SYSTEM_TEXT)

DEFAULT_LITELLM_TIMEOUT_SECONDS = 30
LITELLM_TIMEOUT_SECONDS = int(
    os.environ.get("LITELLM_TIMEOUT_SECONDS", DEFAULT_LITELLM_TIMEOUT_SECONDS)
)

DEFAULT_LITELLM_MODEL = "gpt-5.2"
LITELLM_MODEL = os.environ.get("LITELLM_MODEL", DEFAULT_LITELLM_MODEL)

DEFAULT_LITELLM_MODEL_TYPE = LITELLM_MODEL
LITELLM_MODEL_TYPE = os.environ.get("LITELLM_MODEL_TYPE", DEFAULT_LITELLM_MODEL_TYPE)

DEFAULT_LITELLM_TEMPERATURE = 1
LITELLM_TEMPERATURE = float(
    os.environ.get("LITELLM_TEMPERATURE", DEFAULT_LITELLM_TEMPERATURE)
)

DEFAULT_LITELLM_MAX_TOKENS = 2048
LITELLM_MAX_TOKENS = int(
    os.environ.get("LITELLM_MAX_TOKENS", DEFAULT_LITELLM_MAX_TOKENS)
)

DEFAULT_LITELLM_TOOLS_MODULE_NAME = None
LITELLM_TOOLS_MODULE_NAME = os.environ.get(
    "LITELLM_TOOLS_MODULE_NAME", DEFAULT_LITELLM_TOOLS_MODULE_NAME
)

DEFAULT_LITELLM_CALLBACK_MODULE_NAME = None
LITELLM_CALLBACK_MODULE_NAME = os.environ.get(
    "LITELLM_CALLBACK_MODULE_NAME", DEFAULT_LITELLM_CALLBACK_MODULE_NAME
)

DEFAULT_LITELLM_DROP_PARAMS = None
LITELLM_DROP_PARAMS = os.environ.get("LITELLM_DROP_PARAMS", DEFAULT_LITELLM_DROP_PARAMS)

DEFAULT_SLACK_UPDATE_TEXT_BUFFER_SIZE = 20
SLACK_UPDATE_TEXT_BUFFER_SIZE = int(
    os.environ.get(
        "SLACK_UPDATE_TEXT_BUFFER_SIZE", DEFAULT_SLACK_UPDATE_TEXT_BUFFER_SIZE
    )
)

DEFAULT_SLACK_LOADING_CHARACTER = " ... :writing_hand:"
SLACK_LOADING_CHARACTER = os.environ.get(
    "SLACK_LOADING_CHARACTER", DEFAULT_SLACK_LOADING_CHARACTER
)

USE_SLACK_LANGUAGE = os.environ.get("USE_SLACK_LANGUAGE", "true") == "true"

SLACK_APP_LOG_LEVEL = os.environ.get("SLACK_APP_LOG_LEVEL", "DEBUG")

TRANSLATE_MARKDOWN = os.environ.get("TRANSLATE_MARKDOWN", "false") == "true"

REDACTION_ENABLED = os.environ.get("REDACTION_ENABLED", "false") == "true"

IMAGE_FILE_ACCESS_ENABLED = (
    os.environ.get("IMAGE_FILE_ACCESS_ENABLED", "false") == "true"
)

PDF_FILE_ACCESS_ENABLED = os.environ.get("PDF_FILE_ACCESS_ENABLED", "false") == "true"

PROMPT_CACHING_ENABLED = os.environ.get("PROMPT_CACHING_ENABLED", "false") == "true"
PROMPT_CACHING_TTL = os.environ.get("PROMPT_CACHING_TTL")

# Redaction patterns
#
REDACT_EMAIL_PATTERN = os.environ.get(
    "REDACT_EMAIL_PATTERN", r"\b[A-Za-z0-9.*%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
REDACT_PHONE_PATTERN = os.environ.get(
    "REDACT_PHONE_PATTERN", r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
REDACT_CREDIT_CARD_PATTERN = os.environ.get(
    "REDACT_CREDIT_CARD_PATTERN", r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"
)
REDACT_SSN_PATTERN = os.environ.get(
    "REDACT_SSN_PATTERN", r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b"
)
# For REDACT_USER_DEFINED_PATTERN, the default will never match anything
REDACT_USER_DEFINED_PATTERN = os.environ.get("REDACT_USER_DEFINED_PATTERN", r"(?!)")
