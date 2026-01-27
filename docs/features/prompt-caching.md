# Prompt Caching

## Usage

To enable prompt caching, set the environment variable `PROMPT_CACHING_ENABLED` to `true`.

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
ANTHROPIC_API_KEY=sk-ant-...
LITELLM_MODEL=claude-3-7-sonnet-20250219
PROMPT_CACHING_ENABLED=true

$ docker run -it --env-file ./env ghcr.io/enechange/collmbo:latest
```

When enabled, cache breakpoints will automatically be added to **the two most recent user messages** when the total context size is 1,024 tokens or more. This may help reduce API costs.

Currently, this feature is only supported by [models supported by LiteLLM for prompt caching](https://docs.litellm.ai/docs/completion/prompt_caching), such as **Anthropic Claude and Amazon Bedrock models** (e.g., Claude, Amazon Nova).

## Cache TTL

For models that support custom cache TTL, you can specify it via `PROMPT_CACHING_TTL`:

```sh
PROMPT_CACHING_ENABLED=true
PROMPT_CACHING_TTL=1h
```

When set, the TTL value is added to `cache_control`:

```json
"cache_control": {
    "type": "ephemeral",
    "ttl": "1h"
}
```

## Checking cache usage

If you want to check whether prompt caching was used, look at the `cache_read_input_tokens` field in the model response.

You can use [`examples/callback_handler.py`](../../examples/callback_handler.py) as a reference to log the model response via the `log_success_event()` callback. For example:

```python
def log_success_event(self, kwargs, response_obj, start_time, end_time):
    if "complete_streaming_response" in kwargs:
        print(
            f"complete streaming response: {kwargs['complete_streaming_response']}"
        )
```

A sample output might look like this:

```text
complete streaming response: ModelResponse(usage=Usage(..., cache_read_input_tokens=8516))
```
