import pytest
from litellm.types.utils import Delta, ModelResponse, StreamingChoices

from app.litellm_logic import extract_delta_content, is_final_chunk


@pytest.mark.parametrize(
    "chunk, expected",
    [
        (
            ModelResponse(
                choices=[StreamingChoices(delta=Delta(content="Hello"))],
                stream=True,
            ),
            "Hello",
        ),
        (
            ModelResponse(
                choices=[StreamingChoices(delta=Delta(tool_calls=[]))],
                stream=True,
            ),
            None,
        ),
        (
            ModelResponse(
                choices=[StreamingChoices(delta=None)],
                stream=True,
            ),
            None,
        ),
        (
            ModelResponse(
                choices=[],
                stream=True,
            ),
            None,
        ),
    ],
)
def test_extract_delta_content(chunk, expected):
    result = extract_delta_content(chunk)

    assert result == expected


@pytest.mark.parametrize(
    "chunk, expected",
    [
        (
            ModelResponse(
                choices=[StreamingChoices(delta=Delta(content="Hello"))],
                stream=True,
            ),
            False,
        ),
        (
            ModelResponse(
                choices=[StreamingChoices(delta=Delta(), finish_reason="stop")],
                stream=True,
            ),
            True,
        ),
        (
            ModelResponse(
                choices=[StreamingChoices(delta=None, finish_reason="length")],
                stream=True,
            ),
            True,
        ),
    ],
)
def test_is_final_chunk(chunk, expected):
    result = is_final_chunk(chunk)

    assert result == expected
