"""
This module contains functions to handle message logic.
"""

import base64
import re
import unicodedata


def is_last_marker_reply(
    *,
    reply: dict,
    bot_user_id: str | None,
    marker_text: str,
) -> bool:
    """
    Check if the reply is the last marker reply.

    Args:
        - reply (dict): The reply dictionary.
        - bot_user_id (Optional[str]): The bot's user ID.
        - marker_text (str): The marker text to check.

    Returns:
        - bool: True if the reply is the last marker reply, False otherwise.
    """
    return reply.get("user") == bot_user_id and marker_text in reply.get("text", "")


def filter_replies_after_last_marker(
    *,
    replies: list[dict],
    bot_user_id: str | None,
    marker_text: str,
) -> list[dict]:
    """
    Filter replies to only include those after the last marker reply.

    Args:
        - replies (list[dict]): The list of replies.
        - bot_user_id (Optional[str]): The bot's user ID.
        - marker_text (str): The marker text to check.

    Returns:
        - list[dict]: The filtered list of replies.
    """
    for i, reply in enumerate(reversed(replies)):
        if is_last_marker_reply(
            reply=reply,
            bot_user_id=bot_user_id,
            marker_text=marker_text,
        ):
            new_start = len(replies) - i
            return replies[new_start:]
    return replies


def build_system_message(
    system_prompt_template: str,
    bot_user_id: str | None,
    slack_formatting_enabled: bool,
    prompt_caching_enabled: bool,
    prompt_caching_ttl: str | None = None,
) -> dict:
    """
    Build the system message for the bot.

    Args:
        - system_prompt_template (str): The template for the system prompt.
        - bot_user_id (Optional[str]): The bot's user ID.
        - slack_formatting_enabled (bool): Flag indicating whether to convert Slack mrkdwn to Markdown.
        - prompt_caching_enabled (bool): Flag indicating if prompt caching is enabled.
        - prompt_caching_ttl (Optional[str]): TTL for prompt caching (e.g., "5m", "1h").

    Returns:
        - dict: The system message as a dictionary with "role" and "content" keys.
    """
    system_text = system_prompt_template.format(bot_user_id=bot_user_id)
    system_text = maybe_slack_to_markdown(system_text, slack_formatting_enabled)
    content: list[dict[str, str | dict]] = [
        {
            "type": "text",
            "text": system_text,
        }
    ]
    if prompt_caching_enabled:
        cache_control: dict[str, str] = {"type": "ephemeral"}
        if prompt_caching_ttl:
            cache_control["ttl"] = prompt_caching_ttl
        content[0]["cache_control"] = cache_control
    return {
        "role": "system",
        "content": content,
    }


def build_assistant_message(text: str = "") -> dict:
    """
    Build the assistant message for the bot.

    Args:
        - text (str): The text message from the assistant.

    Returns:
        - dict: The assistant message as a dictionary with "role" and "content" keys.
    """
    return {"role": "assistant", "content": text}


def build_user_message(content: list[dict]) -> dict:
    """
    Build the user message.

    Args:
        - content (list[dict]): The content of the user message.

    Returns:
        - dict: The user message as a dictionary with "role" and "content" keys.
    """
    return {"role": "user", "content": content}


def build_tool_message(*, tool_call_id: str, name: str, content: str) -> dict:
    """
    Build the tool message.

    Args:
        - tool_call_id (str): The ID of the tool call.
        - name (str): The name of the tool.
        - content (str): The content of the tool message.

    Returns:
        - dict: The tool message with "tool_call_id", "role", "name", and "content".
    """
    return {
        "tool_call_id": tool_call_id,
        "role": "tool",
        "name": name,
        "content": content,
    }


def build_image_url_item(mime_type: str, image_bytes: bytes) -> dict:
    """
    Build an image URL item for the bot.

    Args:
        - mime_type (str): The MIME type of the image.
        - image_bytes (bytes): The image data in bytes.

    Returns:
        - dict: The image URL content as a dictionary with "type" and "image_url".
    """
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"},
    }


def build_pdf_file_item(filename: str | None, pdf_bytes: bytes) -> dict:
    """
    Build a PDF file item for the bot.

    Args:
        - filename (Optional[str]): The name of the PDF file.
        - pdf_bytes (bytes): The PDF data in bytes.

    Returns:
        - dict: The PDF file content as a dictionary with "type" and "file".
    """
    encoded_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    return {
        "type": "file",
        "file": {
            "filename": filename or "unnamed.pdf",
            "file_data": f"data:application/pdf;base64,{encoded_pdf}",
        },
    }


def remove_bot_mention(text: str, bot_user_id: str | None) -> str:
    """
    Remove the bot mention from the text.

    Args:
        - text (str): The input text containing the bot mention.
        - bot_user_id (Optional[str]): The bot's user ID.

    Returns:
        - str: The text with the bot mention removed.
    """
    return re.sub(rf"<@{bot_user_id}>\s*", "", text) if bot_user_id else text


def maybe_redact_string(
    *,
    input_string: str,
    patterns: list[tuple[str, str]],
    redaction_enabled: bool,
) -> str:
    """
    Optionally redact sensitive information from a string (inspired by @quangnhut123)

    Args:
        - input_string (str): The string to potentially redact
        - patterns (list[tuple]): A list of (regex pattern, replacement string)
        - redaction_enabled (bool): Whether redaction should be applied

    Returns:
        - str: The redacted string (or original if disabled)
    """
    if not redaction_enabled:
        return input_string
    output_string = input_string
    for pattern, replacement in patterns:
        output_string = re.sub(pattern, replacement, output_string)
    return output_string


def unescape_slack_formatting(content: str) -> str:
    """
    Unescape Slack formatting characters.

    Unescape &, < and >, since Slack replaces these with their HTML equivalents.
    See also: https://api.slack.com/reference/surfaces/formatting#escaping

    Args:
        content (str): The input string containing Slack formatting.

    Returns:
        str: The unescaped string.
    """
    return content.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")


def maybe_slack_to_markdown(content: str, slack_formatting_enabled: bool) -> str:
    """
    Convert Slack mrkdwn to Markdown format.

    See also: https://api.slack.com/reference/surfaces/formatting#basics

    Args:
        content (str): The input string in Slack mrkdwn format.
        slack_formatting_enabled (bool): Flag indicating whether to perform the conversion.

    Returns:
        str: The converted string in Markdown format.
    """
    if not slack_formatting_enabled:
        return content

    # Split the input string into parts based on code blocks and inline code
    parts = re.split(r"(?s)(```.+?```|`[^`\n]+?`)", content)

    # Apply the bold, italic, and strikethrough formatting to text not within code
    result = ""
    for part in parts:
        if not part.startswith("```") and not part.startswith("`"):
            for o, n in [
                (r"\*(?!\s)([^\*\n]+?)(?<!\s)\*", r"**\1**"),  # *bold* to **bold**
                (r"_(?!\s)([^_\n]+?)(?<!\s)_", r"*\1*"),  # _italic_ to *italic*
                (r"~(?!\s)([^~\n]+?)(?<!\s)~", r"~~\1~~"),  # ~strike~ to ~~strike~~
            ]:
                part = re.sub(o, n, part)
        result += part
    return result


def build_slack_user_prefixed_text(reply: dict, text: str) -> str:
    """
    Build a Slack user-prefixed text message.

    Args:
        reply (dict): The reply dictionary containing user information.
        text (str): The text message to be prefixed.

    Returns:
        str: The formatted text message with user mention.
    """
    user_identifier = reply.get("user", reply.get("username"))
    return f"<@{user_identifier}>: {text}"


def maybe_set_cache_points(
    messages: list[dict],
    prompt_caching_enabled: bool,
    prompt_caching_ttl: str | None = None,
) -> None:
    """
    Set cache points in user messages if certain conditions are met.

    Args:
        messages (list[dict]): The list of messages.
        prompt_caching_enabled (bool): Flag indicating if prompt caching is enabled.
        prompt_caching_ttl (Optional[str]): TTL for prompt caching (e.g., "5m", "1h").

    Returns:
        None
    """
    if not (
        prompt_caching_enabled
        and len([m for m in messages if m.get("role") == "user"]) >= 2
    ):
        return
    cache_control: dict[str, str] = {"type": "ephemeral"}
    if prompt_caching_ttl:
        cache_control["ttl"] = prompt_caching_ttl
    user_messages_found = 0
    for message in reversed(messages):  # pragma: no branch
        if message.get("role") != "user":
            continue
        message["content"][-1]["cache_control"] = cache_control
        user_messages_found += 1
        if user_messages_found >= 2:
            break


def format_assistant_reply_for_slack(content: str) -> str:
    """
    Format the assistant reply for Slack display.

    Args:
        content (str): The input string containing the assistant reply.

    Returns:
        str: The formatted string for Slack display.
    """
    for o, n in [
        # Remove leading newlines
        ("^\n+", ""),
        # Remove prepended Slack user ID
        ("^<@U.*?>\\s?:\\s?", ""),
        # Remove code block tags since Slack doesn't render them in a message
        ("```\\s*[Rr]ust\n", "```\n"),
        ("```\\s*[Rr]uby\n", "```\n"),
        ("```\\s*[Ss]cala\n", "```\n"),
        ("```\\s*[Kk]otlin\n", "```\n"),
        ("```\\s*[Jj]ava\n", "```\n"),
        ("```\\s*[Gg]o\n", "```\n"),
        ("```\\s*[Ss]wift\n", "```\n"),
        ("```\\s*[Oo]objective[Cc]\n", "```\n"),
        ("```\\s*[Cc]\n", "```\n"),
        ("```\\s*[Cc][+][+]\n", "```\n"),
        ("```\\s*[Cc][Pp][Pp]\n", "```\n"),
        ("```\\s*[Cc]sharp\n", "```\n"),
        ("```\\s*[Mm][Aa][Tt][Ll][Aa][Bb]\n", "```\n"),
        ("```\\s*[Jj][Ss][Oo][Nn]\n", "```\n"),
        ("```\\s*[Ll]a[Tt]e[Xx]\n", "```\n"),
        ("```\\s*[Ll][Uu][Aa]\n", "```\n"),
        ("```\\s*[Cc][Mm][Aa][Kk][Ee]\n", "```\n"),
        ("```\\s*bash\n", "```\n"),
        ("```\\s*zsh\n", "```\n"),
        ("```\\s*sh\n", "```\n"),
        ("```\\s*[Ss][Qq][Ll]\n", "```\n"),
        ("```\\s*[Pp][Hh][Pp]\n", "```\n"),
        ("```\\s*[Pp][Ee][Rr][Ll]\n", "```\n"),
        ("```\\s*[Jj]ava[Ss]cript\n", "```\n"),
        ("```\\s*[Ty]ype[Ss]cript\n", "```\n"),
        ("```\\s*[Pp]ython\n", "```\n"),
    ]:
        content = re.sub(o, n, content)
    return content


def convert_markdown_to_mrkdwn(content: str) -> str:
    """
    Convert Markdown to Slack mrkdwn format.

    See also: https://api.slack.com/reference/surfaces/formatting#basics

    Args:
        content (str): The input string in Markdown format.

    Returns:
        str: The converted string in Slack mrkdwn format.
    """
    # Split the input string into parts based on code blocks and inline code
    parts = re.split(r"(?s)(```.+?```|`[^`\n]+?`)", content)

    # Apply the bold, italic, and strikethrough formatting to text not within code
    result = ""
    for idx, part in enumerate(parts):
        if part.startswith("```") or part.startswith("`"):
            # Insert ASCII spaces around code spans/blocks when adjacent to
            # East Asian wide/fullwidth characters to improve readability.
            left_space = False
            right_space = False
            if result:
                prev = result[-1]
                if (not prev.isspace()) and unicodedata.east_asian_width(prev) in (
                    "W",
                    "F",
                ):
                    left_space = True
            if idx + 1 < len(parts):
                nxt_part = parts[idx + 1]
                if nxt_part:
                    nxt = nxt_part[0]
                    if (not nxt.isspace()) and unicodedata.east_asian_width(nxt) in (
                        "W",
                        "F",
                    ):
                        right_space = True
            if left_space:
                result += " "
            result += part
            if right_space:
                result += " "
        else:
            for o, n in [
                (
                    r"\*\*\*(?!\s)([^\*\n]+?)(?<!\s)\*\*\*",
                    r"_*\1*_",
                ),  # ***bold italic*** to *_bold italic_*
                (
                    r"(?<![\*_])\*(?!\s)([^\*\n]+?)(?<!\s)\*(?![\*_])",
                    r"_\1_",
                ),  # *italic* to _italic_
                (r"\*\*(?!\s)([^\*\n]+?)(?<!\s)\*\*", r"*\1*"),  # **bold** to *bold*
                (r"__(?!\s)([^_\n]+?)(?<!\s)__", r"*\1*"),  # __bold__ to *bold*
                (r"~~(?!\s)([^~\n]+?)(?<!\s)~~", r"~\1~"),  # ~~strike~~ to ~strike~
            ]:
                part = re.sub(o, n, part)
            # Insert ASCII spaces around Slack formatting when adjacent to
            # East Asian wide/fullwidth characters (e.g., CJK, Hiragana,
            # Katakana, Hangul, Bopomofo, and fullwidth punctuation).
            # This improves mrkdwn rendering when tokens touch wide chars.

            def _is_eaw_wide(ch: str) -> bool:
                # East Asian Width: W (wide) and F (fullwidth)
                return unicodedata.east_asian_width(ch) in ("W", "F")

            def _add_space_around_matches(text: str, pattern: re.Pattern) -> str:
                out = []
                last = 0
                for m in pattern.finditer(text):
                    start, end = m.start(), m.end()
                    out.append(text[last:start])
                    if start > 0:
                        prev = text[start - 1]
                        if not prev.isspace() and _is_eaw_wide(prev):
                            out.append(" ")
                    out.append(m.group(0))
                    if end < len(text):
                        nxt = text[end]
                        if not nxt.isspace() and _is_eaw_wide(nxt):
                            out.append(" ")
                    last = end
                out.append(text[last:])
                return "".join(out)

            patterns = [
                re.compile(r"_\*(?!\s)(.+?)(?<!\s)\*_"),  # *_bold italic_*
                re.compile(r"\*(?!\s)([^\*\n]+?)(?<!\s)\*"),  # *bold*
                re.compile(r"_(?!\s)([^_\n]+?)(?<!\s)_"),  # _italic_
                re.compile(r"~(?!\s)([^~\n]+?)(?<!\s)~"),  # ~strike~
            ]

            for ptn in patterns:
                part = _add_space_around_matches(part, ptn)
            result += part
    return result
