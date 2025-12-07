"""
This module contains logic related to LiteLLM.
"""

from litellm.types.utils import ModelResponse


def extract_delta_content(chunk: ModelResponse) -> str | None:
    """
    Extract the delta content from a chunk of model response.

    Args:
        chunk (ModelResponse): The chunk of model response.

    Returns:
        Optional[str]: The delta content, or None if not found.
    """
    if not chunk.choices:
        return None
    delta = chunk.choices[0].get("delta")
    return None if delta is None else delta.get("content")


def is_final_chunk(chunk: ModelResponse) -> bool:
    """
    Check if the chunk is the final chunk of the model response.

    Args:
        chunk (ModelResponse): The chunk of model response.

    Returns:
        bool: True if the chunk is the final chunk, False otherwise.
    """
    return chunk.choices[0].get("finish_reason") is not None
