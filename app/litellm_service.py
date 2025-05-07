"""
This module provides functions to interact with the LiteLLM API.
"""

import json
import logging
import os
import threading
import time
from functools import lru_cache
from importlib import import_module
from types import ModuleType
from typing import Optional, Union

import litellm
from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper
from litellm.types.utils import (
    ChatCompletionMessageToolCall,
    Choices,
    Message,
    ModelResponse,
)
from slack_sdk.web import SlackResponse, WebClient

from app.env import (
    LITELLM_CALLBACK_MODULE_NAME,
    LITELLM_MAX_TOKENS,
    LITELLM_MODEL,
    LITELLM_MODEL_TYPE,
    LITELLM_TEMPERATURE,
    LITELLM_TOOLS_MODULE_NAME,
    SLACK_LOADING_CHARACTER,
    SLACK_UPDATE_TEXT_BUFFER_SIZE,
    TRANSLATE_MARKDOWN,
)
from app.exceptions import ContextOverflowError
from app.litellm_logic import (
    calculate_max_context_tokens,
    extract_delta_content,
    get_max_input_tokens,
    is_final_chunk,
    load_tools_from_module,
    trim_messages_to_max_context_tokens,
)
from app.message_logic import (
    build_assistant_message,
    build_tool_message,
    convert_markdown_to_mrkdwn,
    format_assistant_reply_for_slack,
)

litellm.drop_params = True

if LITELLM_CALLBACK_MODULE_NAME is not None:
    callback_module = import_module(LITELLM_CALLBACK_MODULE_NAME)
    litellm.callbacks = [callback_module.CallbackHandler()]


def trim_messages_for_model_limit(messages: list[dict]) -> tuple[int, int]:
    """
    Trims messages to fit within the maximum context tokens.

    Args:
        messages (list[dict]): The list of messages to trim.

    Returns:
        tuple[int, int]: The number of tokens in the messages and tool definitions.
    """
    max_input_tokens = get_max_input_tokens(LITELLM_MODEL_TYPE)
    if max_input_tokens is None:
        raise ValueError("LiteLLM does not support the model type")
    tools_tokens = estimate_tools_tokens()
    max_context_tokens = calculate_max_context_tokens(
        max_input_tokens=max_input_tokens,
        tools_tokens=tools_tokens,
        max_output_tokens=LITELLM_MAX_TOKENS,
    )
    messages_tokens = trim_messages_to_max_context_tokens(
        messages=messages,
        model_type=LITELLM_MODEL_TYPE,
        max_context_tokens=max_context_tokens,
    )
    if messages_tokens > max_context_tokens:
        raise ContextOverflowError(messages_tokens, max_context_tokens)
    return messages_tokens, tools_tokens


def reply_to_slack_with_litellm(
    *,
    client: WebClient,
    channel: str,
    user_id: str,
    thread_ts: Optional[str],
    messages: list[dict],
    loading_text: str,
    wip_reply: Union[dict, SlackResponse],
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
    tools: Optional[list] = None,
) -> Union[ModelResponse, CustomStreamWrapper]:
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
    return litellm.completion(
        model=LITELLM_MODEL,
        messages=messages,
        top_p=1,
        n=1,
        max_tokens=max_tokens,
        temperature=temperature,
        presence_penalty=0,
        frequency_penalty=0,
        user=user,
        stream=stream,
        tools=tools,
        aws_region_name=os.environ.get("AWS_REGION_NAME"),
    )


@lru_cache(maxsize=1)
def estimate_tools_tokens() -> int:
    """
    Estimates the number of tokens used by tools in LiteLLM.

    Returns:
        int: The estimated number of tokens used by tools.
    """
    if LITELLM_TOOLS_MODULE_NAME is None:
        return 0

    def calculate_prompt_tokens(tools) -> int:
        response = call_litellm_completion(
            messages=[{"role": "user", "content": "hello"}],
            user="system",
            tools=tools,
        )
        if not isinstance(response, ModelResponse):
            raise TypeError("Expected ModelResponse when streaming is disabled")
        return response["usage"]["prompt_tokens"]

    # TODO: If there is a better way to calculate this, replace the logic with it
    module = import_module(LITELLM_TOOLS_MODULE_NAME)
    return calculate_prompt_tokens(module.tools) - calculate_prompt_tokens(None)


def start_litellm_stream(
    *,
    temperature: float,
    messages: list[dict],
    user: str,
) -> CustomStreamWrapper:
    """
    Starts a LiteLLM stream for generating completions.

    Args:
        temperature (float): The temperature for sampling.
        messages (list[dict]): The list of messages to send to the API.
        user (str): The user ID of the person making the request.

    Returns:
        CustomStreamWrapper: The stream wrapper for the response.
    """
    tools = load_tools_from_module(LITELLM_TOOLS_MODULE_NAME)
    response = call_litellm_completion(
        messages=messages,
        max_tokens=LITELLM_MAX_TOKENS,
        temperature=temperature,
        user=user,
        stream=True,
        tools=tools,
    )
    if not isinstance(response, CustomStreamWrapper):
        raise TypeError("Expected CustomStreamWrapper when streaming is enabled")
    return response


def stream_litellm_reply_to_slack(
    *,
    client: WebClient,
    wip_reply: Union[dict, SlackResponse],
    channel: str,
    user_id: str,
    messages: list[dict],
    stream: CustomStreamWrapper,
    thread_ts: Optional[str],
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

    if (
        response_message is None
        or response_message.tool_calls is None
        or LITELLM_TOOLS_MODULE_NAME is None
    ):
        return

    # If the message has already been updated, post a new one
    if wip_reply["message"]["text"] != loading_text:
        wip_reply = client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=loading_text,
        )

    process_tool_calls(
        response_message=response_message,
        tools_module_name=LITELLM_TOOLS_MODULE_NAME,
        assistant_message=assistant_message,
        messages=messages,
        logger=client.logger,
    )
    trim_messages_for_model_limit(messages)
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
    wip_reply: Union[dict, SlackResponse],
    client: WebClient,
    channel: str,
    timeout_seconds: int,
    start_time: float,
) -> tuple[Optional[Message], bool]:
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
            delta_content = extract_delta_content(chunk)
            if delta_content is None:
                continue
            buffered_text += delta_content
            assistant_message["content"] += delta_content
            final_chunk = is_final_chunk(chunk)
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
                    and len(wip_reply["message"]["text"].encode("utf-8")) > 3500
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
    wip_reply: Union[dict, SlackResponse],
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
    wip_reply: Union[dict, SlackResponse],
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
    assistant_reply_text = format_assistant_reply_for_slack(assistant_content)
    if TRANSLATE_MARKDOWN:
        assistant_reply_text = convert_markdown_to_mrkdwn(assistant_reply_text)
    wip_reply["message"]["text"] = assistant_reply_text
    text = assistant_reply_text
    if with_loading_character:
        text += SLACK_LOADING_CHARACTER
    client.chat_update(
        channel=channel,
        ts=wip_reply["message"]["ts"],
        text=text,
    )


def extract_message_from_chunks(chunks: list) -> Optional[Message]:
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


def process_tool_calls(
    *,
    response_message: Message,
    tools_module_name: str,
    assistant_message: dict,
    messages: list[dict],
    logger: logging.Logger,
) -> None:
    """
    Processes the tool calls in the response message.

    Args:
        response_message (Message): The response message containing tool calls.
        tools_module_name (str): The name of the module containing the tools.
        assistant_message (dict): The assistant message to update.
        messages (list[dict]): The list of messages to include in the reply.
        logger (logging.Logger): The logger instance.

    Returns:
        None
    """
    if response_message.tool_calls is None:
        return
    assistant_message["tool_calls"] = response_message.model_dump()["tool_calls"]
    tools_module = import_module(tools_module_name)
    for tool_call in response_message.tool_calls:
        process_tool_call(
            tool_call=tool_call,
            tools_module=tools_module,
            messages=messages,
            logger=logger,
        )


def process_tool_call(
    *,
    tool_call: ChatCompletionMessageToolCall,
    tools_module: ModuleType,
    messages: list[dict],
    logger: logging.Logger,
) -> None:
    """
    Processes a single tool call and updates the messages list.

    Args:
        tool_call (ChatCompletionMessageToolCall): The tool call to process.
        tools_module (ModuleType): The module containing the tools.
        messages (list[dict]): The list of messages to include in the reply.
        logger (logging.Logger): The logger instance.

    Returns:
        None
    """
    function_name = tool_call.function.name
    if function_name is None:
        logger.warning(
            "Skipped a tool call due to missing function name. Tool call details: %s",
            tool_call,
        )
        return
    function_to_call = getattr(tools_module, function_name)
    function_args = json.loads(tool_call.function.arguments)
    function_response = function_to_call(**function_args)
    tool_message = build_tool_message(
        tool_call_id=tool_call.id,
        name=function_name,
        content=function_response,
    )
    messages.append(tool_message)
