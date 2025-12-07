"""
Provides functionality to translate text based on the user's locale.
"""

from litellm.types.utils import ModelResponse

from app.litellm_service import call_litellm_completion
from app.translation_logic import (
    build_translation_messages,
    get_cached_translation,
    get_lang_from_locale,
    set_cached_translation,
)

# https://slack.com/help/articles/215058658-Manage-your-language-preferences
LOCALE_TO_LANG = {
    "en-US": "English",
    "en-GB": "English",
    "de-DE": "German",
    "es-ES": "Spanish",
    "es-LA": "Spanish",
    "fr-FR": "French",
    "it-IT": "Italian",
    "pt-BR": "Portuguese",
    "ja-JP": "Japanese",
    "zh-CN": "Simplified Chinese",
    "zh-TW": "Traditional Chinese",
    "ko-KR": "Korean",
}


_translation_result_cache: dict[str, str] = {}


def translate(locale: str | None, text: str) -> str:
    """
    Translate the given text into the language specified by the locale.

    Args:
        - locale (Optional[str]): The locale string (e.g., "en-US").
        - text (str): The text to be translated.

    Returns:
        - str: The translated text.
    """
    lang = get_lang_from_locale(locale, LOCALE_TO_LANG)
    if lang is None or lang == "English":
        return text

    cached_result = get_cached_translation(
        cache=_translation_result_cache,
        lang=lang,
        original=text,
    )
    if cached_result is not None:
        return cached_result

    response = call_litellm_completion(
        messages=build_translation_messages(lang, text),
        temperature=1,
        user="system",
    )
    if not isinstance(response, ModelResponse):
        raise TypeError("Expected ModelResponse when streaming is disabled")

    translated = response["choices"][0]["message"].get("content")
    set_cached_translation(
        cache=_translation_result_cache,
        lang=lang,
        original=text,
        translated=translated,
    )
    return translated
