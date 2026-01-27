# Optional Settings

Collmbo works fine with defaults, but you can customize its behavior by setting the following environment variables:

- `LITELLM_DROP_PARAMS` (Comma-separated list of parameters to drop when calling LiteLLM. Example: `"top_p"`)
- `LLM_MAX_TOKENS`
- `LLM_TEMPERATURE`
- `LLM_TIMEOUT_SECONDS`
- `SYSTEM_PROMPT_TEMPLATE` (Use `{bot_user_id}` placeholder for the bot's Slack user ID.)
- `SLACK_APP_LOG_LEVEL`
- `SLACK_UPDATE_TEXT_BUFFER_SIZE` (Slack message update buffer size. Increase if hitting rate limits.)
- `USE_SLACK_LOCALE` (If `"false"`, ignores Slack locale and lets the model handle translations.)

See [`app/env.py`](../../app/env.py) for details.
