import pytest

from app.translation_logic import (
    build_translation_messages,
    get_cache_key,
    get_cached_translation,
    get_lang_from_locale,
    set_cached_translation,
)

TEST_LOCALE_TO_LANG = {
    "ja-JP": "Japanese",
    "en-US": "English",
    "de-DE": "German",
}


@pytest.mark.parametrize(
    "locale,expected",
    [
        ("ja-JP", "Japanese"),
        ("en-US", "English"),
        ("de-DE", "German"),
        ("xx-XX", None),  # Key not in dict
        (None, None),
    ],
)
def test_get_lang_from_locale(locale, expected):
    result = get_lang_from_locale(locale, TEST_LOCALE_TO_LANG)

    assert result == expected


@pytest.mark.parametrize(
    "lang,text,expected",
    [
        ("Japanese", "Hello", "Japanese:Hello"),
        ("English", "Slack bot", "English:Slack bot"),
    ],
)
def test_get_cache_key(lang, text, expected):
    result = get_cache_key(lang, text)

    assert result == expected


@pytest.mark.parametrize(
    "cache, lang, original, expected",
    [
        ({"Japanese:Hello": "こんにちは"}, "Japanese", "Hello", "こんにちは"),
        ({"English:Hello": "Hello"}, "English", "Hello", "Hello"),
        ({"Japanese:Hi": "やあ"}, "Japanese", "Hello", None),
        ({}, "Japanese", "Hello", None),
    ],
)
def test_get_cached_translation(cache, lang, original, expected):
    result = get_cached_translation(
        cache=cache,
        lang=lang,
        original=original,
    )

    assert result == expected


@pytest.mark.parametrize(
    "lang, original, translated, expected_cache",
    [
        ("Japanese", "Hello", "こんにちは", {"Japanese:Hello": "こんにちは"}),
        ("English", "Slack bot", "Slack bot", {"English:Slack bot": "Slack bot"}),
        (
            "German",
            "Good morning",
            "Guten Morgen",
            {"German:Good morning": "Guten Morgen"},
        ),
    ],
)
def test_set_cached_translation(lang, original, translated, expected_cache):
    cache = {}

    set_cached_translation(
        cache=cache,
        lang=lang,
        original=original,
        translated=translated,
    )

    assert cache == expected_cache


@pytest.mark.parametrize(
    "lang, original, expected",
    [
        (
            "Japanese",
            "Hello",
            [
                {
                    "role": "system",
                    "content": (
                        "You're the AI model that primarily focuses on the quality of language translation. "
                        "You always respond with the only the translated text in a format suitable for Slack "
                        "user interface. Slack's emoji (e.g., :hourglass_flowing_sand:) and mention parts must "
                        "be kept as-is. You don't change the meaning of sentences when translating them into a "
                        "different language. When the given text is a single verb/noun, its translated text "
                        "must be a norm/verb form too. When the given text is in markdown format, the format "
                        "must be kept as much as possible."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Can you translate the following text into Japanese in a professional tone? Your "
                        "response must omit any English version / pronunciation guide for the result. Again, "
                        "no need to append any English notes and guides about the result. Just return the "
                        "translation result. Here is the original sentence you need to translate:\nHello"
                    ),
                },
            ],
        ),
        (
            "German",
            "Good morning",
            [
                {
                    "role": "system",
                    "content": (
                        "You're the AI model that primarily focuses on the quality of language translation. "
                        "You always respond with the only the translated text in a format suitable for Slack "
                        "user interface. Slack's emoji (e.g., :hourglass_flowing_sand:) and mention parts must "
                        "be kept as-is. You don't change the meaning of sentences when translating them into a "
                        "different language. When the given text is a single verb/noun, its translated text "
                        "must be a norm/verb form too. When the given text is in markdown format, the format "
                        "must be kept as much as possible."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Can you translate the following text into German in a professional tone? Your "
                        "response must omit any English version / pronunciation guide for the result. Again, "
                        "no need to append any English notes and guides about the result. Just return the "
                        "translation result. Here is the original sentence you need to translate:\nGood morning"
                    ),
                },
            ],
        ),
    ],
)
def test_build_translation_messages(lang, original, expected):
    result = build_translation_messages(lang, original)

    assert result == expected
