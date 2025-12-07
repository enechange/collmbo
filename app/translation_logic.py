"""
Provides logic for handling translations.
"""


def get_lang_from_locale(
    locale: str | None, locale_to_lang: dict[str, str]
) -> str | None:
    """
    Get the language from the locale string.

    Args:
        locale (Optional[str]): The locale string (e.g., "en-US").
        locale_to_lang (dict[str, str]): A dictionary mapping locale strings to language names.

    Returns:
        Optional[str]: The language name if found, None otherwise.
    """
    return None if locale is None else locale_to_lang.get(locale)


def get_cache_key(lang: str, text: str) -> str:
    """
    Generate a cache key for the translation.

    Args:
        lang (str): The language name.
        text (str): The text to be translated.

    Returns:
        str: The cache key in the format "lang:text".
    """
    return f"{lang}:{text}"


def get_cached_translation(
    *,
    cache: dict[str, str],
    lang: str,
    original: str,
) -> str | None:
    """
    Get the cached translation for the given language and original text.

    Args:
        cache (dict[str, str]): The cache dictionary.
        lang (str): The language name.
        original (str): The original text.

    Returns:
        Optional[str]: The cached translation if found, None otherwise.
    """
    return cache.get(get_cache_key(lang, original))


def set_cached_translation(
    *,
    cache: dict[str, str],
    lang: str,
    original: str,
    translated: str,
) -> None:
    """
    Set the cached translation for the given language and original text.

    Args:
        cache (dict[str, str]): The cache dictionary.
        lang (str): The language name.
        original (str): The original text.
        translated (str): The translated text.

    Returns:
        None
    """
    cache[get_cache_key(lang, original)] = translated


def build_translation_messages(lang: str, original: str) -> list[dict[str, str]]:
    """
    Build the messages for translation.

    Args:
        lang (str): The target language for translation.
        original (str): The original text to be translated.

    Returns:
        list[dict[str, str]]: A list of messages for translation.
    """
    system_text = (
        "You're the AI model that primarily focuses on the quality of language translation. "
        "You always respond with the only the translated text in a format suitable for Slack user "
        "interface. Slack's emoji (e.g., :hourglass_flowing_sand:) and mention parts must be kept "
        "as-is. You don't change the meaning of sentences when translating them into a different "
        "language. When the given text is a single verb/noun, its translated text must be a norm/"
        "verb form too. When the given text is in markdown format, the format must be kept as much "
        "as possible."
    )
    user_text = (
        f"Can you translate the following text into {lang} in a professional tone? "
        "Your response must omit any English version / pronunciation guide for the result. "
        "Again, no need to append any English notes and guides about the result. "
        "Just return the translation result. "
        f"Here is the original sentence you need to translate:\n{original}"
    )
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]
