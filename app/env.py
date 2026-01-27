"""
This module loads and exposes environment variables used by the app.
"""

import os
import warnings
from typing import overload

# Mapping of deprecated environment variable names to their new names
DEPRECATED_ENV_VARS: dict[str, str] = {
    "LITELLM_MODEL": "LLM_MODEL",
    "LITELLM_TIMEOUT_SECONDS": "LLM_TIMEOUT_SECONDS",
    "LITELLM_TEMPERATURE": "LLM_TEMPERATURE",
    "LITELLM_MAX_TOKENS": "LLM_MAX_TOKENS",
    "LITELLM_TOOLS_MODULE_NAME": "TOOLS_MODULE_NAME",
    "LITELLM_SYSTEM_TEXT": "SYSTEM_PROMPT_TEMPLATE",
    "USE_SLACK_LANGUAGE": "USE_SLACK_LOCALE",
    "TRANSLATE_MARKDOWN": "SLACK_FORMATTING_ENABLED",
    "IMAGE_FILE_ACCESS_ENABLED": "IMAGE_INPUT_ENABLED",
    "PDF_FILE_ACCESS_ENABLED": "PDF_INPUT_ENABLED",
}


@overload
def get_env(new_name: str, default: str) -> str: ...


@overload
def get_env(new_name: str, default: int) -> int: ...


@overload
def get_env(new_name: str, default: float) -> float: ...


@overload
def get_env(new_name: str, default: None = None) -> str | None: ...


def get_env(
    new_name: str, default: str | int | float | None = None
) -> str | int | float | None:
    """
    Get an environment variable with deprecation warning support.

    If a deprecated name is set and the new name is not, warns and returns the old value.
    Returns the value converted to the same type as the default parameter.
    """

    def convert(value: str) -> str | int | float:
        if isinstance(default, int):
            return int(value)
        if isinstance(default, float):
            return float(value)
        return value

    new_value = os.environ.get(new_name)
    if new_value is not None:
        return convert(new_value)

    for old_name, mapped_new_name in DEPRECATED_ENV_VARS.items():
        if mapped_new_name == new_name:
            old_value = os.environ.get(old_name)
            if old_value is not None:
                warnings.warn(
                    f"{old_name} is deprecated, use {new_name} instead",
                    stacklevel=2,
                )
                return convert(old_value)

    return default


# LLM
DEFAULT_SYSTEM_PROMPT_TEMPLATE = """
You are a bot in a slack chat room. You might receive messages from multiple people.
Format bold text *like this*, italic text _like this_ and strikethrough text ~like this~.
Slack user IDs match the regex `<@U.*?>`.
Your Slack user ID is <@{bot_user_id}>.
Each message has the author's Slack user ID prepended, like the regex `^<@U.*?>: ` followed by the message text.
Only mention users (e.g., `<@U12345>`) when you are explicitly instructed to do so. Otherwise, do not mention users.
"""
SYSTEM_PROMPT_TEMPLATE = get_env(
    "SYSTEM_PROMPT_TEMPLATE", DEFAULT_SYSTEM_PROMPT_TEMPLATE
)
LLM_MODEL = get_env("LLM_MODEL", "gpt-5.2")
LLM_TIMEOUT_SECONDS = get_env("LLM_TIMEOUT_SECONDS", 30)
LLM_TEMPERATURE = get_env("LLM_TEMPERATURE", 1.0)
LLM_MAX_TOKENS = get_env("LLM_MAX_TOKENS", 2048)

# LiteLLM
LITELLM_CALLBACK_MODULE_NAME = get_env("LITELLM_CALLBACK_MODULE_NAME")
LITELLM_DROP_PARAMS = get_env("LITELLM_DROP_PARAMS")

# Slack
SLACK_APP_LOG_LEVEL = get_env("SLACK_APP_LOG_LEVEL", "DEBUG")
SLACK_UPDATE_TEXT_BUFFER_SIZE = get_env("SLACK_UPDATE_TEXT_BUFFER_SIZE", 20)
SLACK_LOADING_CHARACTER = get_env("SLACK_LOADING_CHARACTER", " ... :writing_hand:")
USE_SLACK_LOCALE = get_env("USE_SLACK_LOCALE", "true") == "true"
SLACK_FORMATTING_ENABLED = get_env("SLACK_FORMATTING_ENABLED", "false") == "true"

# Input
IMAGE_INPUT_ENABLED = get_env("IMAGE_INPUT_ENABLED", "false") == "true"
PDF_INPUT_ENABLED = get_env("PDF_INPUT_ENABLED", "false") == "true"

# Tools
TOOLS_MODULE_NAME = get_env("TOOLS_MODULE_NAME")

# Prompt caching
PROMPT_CACHING_ENABLED = get_env("PROMPT_CACHING_ENABLED", "false") == "true"
PROMPT_CACHING_TTL = get_env("PROMPT_CACHING_TTL")

# Redaction
REDACTION_ENABLED = get_env("REDACTION_ENABLED", "false") == "true"
REDACT_EMAIL_PATTERN = get_env(
    "REDACT_EMAIL_PATTERN", r"\b[A-Za-z0-9.*%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
REDACT_PHONE_PATTERN = get_env(
    "REDACT_PHONE_PATTERN", r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
)
REDACT_CREDIT_CARD_PATTERN = get_env(
    "REDACT_CREDIT_CARD_PATTERN", r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"
)
REDACT_SSN_PATTERN = get_env("REDACT_SSN_PATTERN", r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b")
REDACT_USER_DEFINED_PATTERN = get_env("REDACT_USER_DEFINED_PATTERN", r"(?!)")
