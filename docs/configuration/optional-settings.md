# Optional Settings

Collmbo works fine with defaults, but you can customize its behavior by setting the following environment variables:

- `LITELLM_DROP_PARAMS` (Comma-separated list of parameters to drop when calling LiteLLM. Example: `"top_p"`)
- `LITELLM_MAX_TOKENS`
- `LITELLM_SYSTEM_TEXT`
- `LITELLM_TEMPERATURE`
- `LITELLM_TIMEOUT_SECONDS`
- `SLACK_APP_LOG_LEVEL`
- `SLACK_UPDATE_TEXT_BUFFER_SIZE` (Slack message update buffer size. Increase if hitting rate limits.)
- `USE_SLACK_LANGUAGE` (If `"false"`, ignores Slack locale and lets the model handle translations.)

See [`app/env.py`](../../app/env.py) for details.
