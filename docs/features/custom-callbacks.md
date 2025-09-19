# Custom Callbacks

## Usage

1. Create a [custom callback](https://docs.litellm.ai/docs/observability/custom_callback) module.
2. Set your module name in the environment variable `LITELLM_CALLBACK_MODULE_NAME`.
3. Run Collmbo.
4. Send a message in Slack.

## Try this Feature

You can try it with [`examples/callback_handler.py`](../../examples/callback_handler.py). This sample logs requests to the model.

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
LITELLM_MODEL=gpt-4o
LITELLM_CALLBACK_MODULE_NAME=examples.callback_handler

$ docker run -it --env-file ./env -v ./examples:/app/examples ghcr.io/enechange/collmbo:latest
```

> ![Custom callbacks example](https://github.com/user-attachments/assets/38a83ac9-1429-46ad-bd6c-95e1d6aac247)
