"""
This module provides functions to interact with the LiteLLM API.
"""

import os
import threading
import time
from importlib import import_module
from typing import cast

import litellm
from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper
from litellm.types.utils import Choices, Message, ModelResponse
from slack_sdk.web import SlackResponse, WebClient

from app.env import (
    LITELLM_CALLBACK_MODULE_NAME,
    LITELLM_DROP_PARAMS,
    LITELLM_MAX_TOKENS,
    LITELLM_MODEL,
    LITELLM_TEMPERATURE,
    SLACK_LOADING_CHARACTER,
    SLACK_UPDATE_TEXT_BUFFER_SIZE,
    TRANSLATE_MARKDOWN,
)
from app.litellm_logic import extract_delta_content, is_final_chunk
from app.message_logic import (
    build_assistant_message,
    convert_markdown_to_mrkdwn,
    format_assistant_reply_for_slack,
)
from app.tools_service import get_all_tools, process_tool_calls

litellm.drop_params = True

if LITELLM_CALLBACK_MODULE_NAME is not None:
    callback_module = import_module(LITELLM_CALLBACK_MODULE_NAME)
    litellm.callbacks = [callback_module.CallbackHandler()]


def reply_to_slack_with_litellm(
    *,
    client: WebClient,
    channel: str,
    user_id: str,
    thread_ts: str | None,
    messages: list[dict],
    loading_text: str,
    wip_reply: dict | SlackResponse,
    timeout_seconds: int,
) -> None:
    """
    Sends a reply to Slack using LiteLLM.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel (str): The Slack channel ID.
        user_id (str): The user ID of the person who initiated the conversation.
        thread_ts (Optional[str]): The timestamp of the thread to reply to.
        messages (list[dict]): The list of messages to include in the reply.
        loading_text (str): The text to display while waiting for a response.
        wip_reply (Union[dict, SlackResponse]): The message object for the in-progress reply.
        timeout_seconds (int): The timeout duration in seconds.

    Returns:
        None
    """
    stream = start_litellm_stream(
        temperature=LITELLM_TEMPERATURE,
        messages=messages,
        user=user_id,
        channel=channel,
    )
    stream_litellm_reply_to_slack(
        client=client,
        wip_reply=wip_reply,
        channel=channel,
        user_id=user_id,
        messages=messages,
        stream=stream,
        thread_ts=thread_ts,
        loading_text=loading_text,
        timeout_seconds=timeout_seconds,
    )


def call_litellm_completion(
    *,
    messages: list[dict],
    user: str,
    max_tokens: int = 1024,
    temperature: float = 0,
    stream: bool = False,
    tools: list | None = None,
) -> ModelResponse | CustomStreamWrapper:
    """
    Calls the LiteLLM completion API.

    Args:
        messages (list[dict]): The list of messages to send to the API.
        user (str): The user ID of the person making the request.
        max_tokens (int): The maximum number of tokens to generate.
        temperature (float): The temperature for sampling.
        stream (bool): Whether to stream the response.
        tools (Optional[list]): The list of tools to use.

    Returns:
        Union[ModelResponse, CustomStreamWrapper]: The response from the API.
    """
    kwargs = {
        "model": LITELLM_MODEL,
        "messages": messages,
        "top_p": 1,
        "n": 1,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "user": user,
        "stream": stream,
        "aws_region_name": os.environ.get("AWS_REGION_NAME"),
    }

    if tools is not None:
        kwargs["tools"] = tools
        kwargs["parallel_tool_calls"] = False

    if LITELLM_DROP_PARAMS is not None:
        kwargs["additional_drop_params"] = [
            param.strip() for param in LITELLM_DROP_PARAMS.split(",")
        ]

    return litellm.completion(**kwargs)


def start_litellm_stream(
    *,
    temperature: float,
    messages: list[dict],
    user: str,
    channel: str | None = None,
) -> CustomStreamWrapper:
    """
    Starts a LiteLLM stream for generating completions.

    Args:
        temperature (float): The temperature for sampling.
        messages (list[dict]): The list of messages to send to the API.
        user (str): The user ID of the person making the request.
        channel (Optional[str]): Slack channel ID for context-aware tool selection.

    Returns:
        CustomStreamWrapper: The stream wrapper for the response.
    """
    response = call_litellm_completion(
        messages=messages,
        max_tokens=LITELLM_MAX_TOKENS,
        temperature=temperature,
        user=user,
        stream=True,
        tools=get_all_tools(channel=channel, user_id=user),
    )
    if not isinstance(response, CustomStreamWrapper):
        raise TypeError("Expected CustomStreamWrapper when streaming is enabled")
    return response


def stream_litellm_reply_to_slack(
    *,
    client: WebClient,
    wip_reply: dict | SlackResponse,
    channel: str,
    user_id: str,
    messages: list[dict],
    stream: CustomStreamWrapper,
    thread_ts: str | None,
    loading_text: str,
    timeout_seconds: int,
):
    """
    Streams the LiteLLM response and updates the Slack message.

    Args:
        client (WebClient): The Slack WebClient instance.
        wip_reply (Union[dict, SlackResponse]): The message object for the in-progress reply.
        channel (str): The Slack channel ID.
        user_id (str): The user ID of the person who initiated the conversation.
        messages (list[dict]): The list of messages to include in the reply.
        stream (CustomStreamWrapper): The stream wrapper for the response.
        thread_ts (Optional[str]): The timestamp of the thread to reply to.
        loading_text (str): The text to display while waiting for a response.
        timeout_seconds (int): The timeout duration in seconds.

    Returns:
        None
    """
    start_time = time.time()
    while True:
        assistant_message = build_assistant_message()
        response_message, is_response_too_long = handle_litellm_stream(
            stream=stream,
            assistant_message=assistant_message,
            wip_reply=wip_reply,
            client=client,
            channel=channel,
            timeout_seconds=int(timeout_seconds - (time.time() - start_time)),
            start_time=start_time,
        )
        messages.append(assistant_message)
        if not is_response_too_long:
            break
        wip_reply = client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=SLACK_LOADING_CHARACTER,
        )

    if response_message is None or response_message.tool_calls is None:
        return

    # If the message has already been updated, post a new one
    if (wip_message := wip_reply["message"]) and wip_message["text"] != loading_text:
        wip_reply = client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=loading_text,
        )

    process_tool_calls(
        response_message=response_message,
        assistant_message=assistant_message,
        messages=messages,
        user_id=user_id,
    )
    reply_to_slack_with_litellm(
        client=client,
        wip_reply=wip_reply,
        channel=channel,
        user_id=user_id,
        messages=messages,
        thread_ts=thread_ts,
        loading_text=loading_text,
        timeout_seconds=int(timeout_seconds - (time.time() - start_time)),
    )


def handle_litellm_stream(
    *,
    stream: CustomStreamWrapper,
    assistant_message: dict,
    wip_reply: dict | SlackResponse,
    client: WebClient,
    channel: str,
    timeout_seconds: int,
    start_time: float,
) -> tuple[Message | None, bool]:
    """
    Handles the streaming response from LiteLLM and updates the Slack message.

    Args:
        stream (CustomStreamWrapper): The stream wrapper for the response.
        assistant_message (dict): The assistant message to update.
        wip_reply (Union[dict, SlackResponse]): The message object for the in-progress reply.
        client (WebClient): The Slack WebClient instance.
        channel (str): The Slack channel ID.
        timeout_seconds (int): The timeout duration in seconds.
        start_time (float): The start time of the request.

    Returns:
        tuple[Optional[Message], bool]: The response and whether it exceeded the length limit.
    """
    response_chunks: list = []
    is_response_too_long = False
    threads: list[threading.Thread] = []
    buffered_text = ""
    try:
        for chunk in stream:
            if (time.time() - start_time) > timeout_seconds:
                raise TimeoutError()
            response_chunks.append(chunk)
            delta_content = extract_delta_content(cast("ModelResponse", chunk))
            if delta_content is None:
                continue
            buffered_text += delta_content
            assistant_message["content"] += delta_content
            final_chunk = is_final_chunk(cast("ModelResponse", chunk))
            if len(buffered_text) >= SLACK_UPDATE_TEXT_BUFFER_SIZE:
                spawn_update_reply_text(
                    client=client,
                    channel=channel,
                    wip_reply=wip_reply,
                    assistant_content=assistant_message["content"],
                    threads=threads,
                )
                buffered_text = ""
                if (
                    not final_chunk
                    and (wip_message := wip_reply["message"])
                    and len(wip_message["text"].encode("utf-8")) > 3500
                ):
                    is_response_too_long = True
                    break
            if final_chunk:
                break
    finally:
        for t in threads:
            try:
                t.join()
            except Exception:
                pass

    # Final update to remove the loading character after stream ends
    if len(assistant_message["content"]) > 0:
        update_reply_text(
            client=client,
            channel=channel,
            wip_reply=wip_reply,
            assistant_content=assistant_message["content"],
            with_loading_character=False,
        )

    return extract_message_from_chunks(response_chunks), is_response_too_long


def spawn_update_reply_text(
    *,
    client: WebClient,
    channel: str,
    wip_reply: dict | SlackResponse,
    assistant_content: str,
    threads: list[threading.Thread],
) -> None:
    """
    Spawns a thread to update the Slack message with the assistant's reply.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel (str): The Slack channel ID.
        wip_reply (Union[dict, SlackResponse]): The message object for the in-progress reply.
        assistant_content (str): The content of the assistant's reply.
        threads (list[threading.Thread]): The list of threads to manage.

    Returns:
        None
    """
    thread = threading.Thread(
        target=update_reply_text,
        kwargs={
            "client": client,
            "channel": channel,
            "wip_reply": wip_reply,
            "assistant_content": assistant_content,
        },
    )
    thread.daemon = True
    thread.start()
    threads.append(thread)


def update_reply_text(
    *,
    client: WebClient,
    channel: str,
    wip_reply: dict | SlackResponse,
    assistant_content: str,
    with_loading_character: bool = True,
) -> None:
    """
    Updates the Slack message with the assistant's reply.

    Args:
        client (WebClient): The Slack WebClient instance.
        channel (str): The Slack channel ID.
        wip_reply (Union[dict, SlackResponse]): The message object for the in-progress reply.
        assistant_content (str): The content of the assistant's reply.
        with_loading_character (bool): Whether to append a loading character.

    Returns:
        None
    """
    wip_message = wip_reply["message"]
    if not wip_message:
        return
    assistant_reply_text = format_assistant_reply_for_slack(assistant_content)
    if TRANSLATE_MARKDOWN:
        assistant_reply_text = convert_markdown_to_mrkdwn(assistant_reply_text)
    wip_message["text"] = assistant_reply_text
    text = assistant_reply_text
    if with_loading_character:
        text += SLACK_LOADING_CHARACTER
    client.chat_update(channel=channel, ts=wip_message["ts"], text=text)


def extract_message_from_chunks(chunks: list) -> Message | None:
    """
    Extracts the message from the chunks of the model response.

    Args:
        chunks (list): The list of chunks from the model response.

    Returns:
        Optional[Message]: The extracted message, or None if not found.
    """
    response = litellm.stream_chunk_builder(chunks)
    if response is None:
        raise RuntimeError(
            "litellm.stream_chunk_builder returned None. "
            "Check the stream data or API behavior."
        )
    if isinstance(response.choices[0], Choices):
        return response.choices[0].message
    return None
