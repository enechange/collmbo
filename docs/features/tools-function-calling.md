# Tools (Function Calling)

## Usage

1. Create a Python module with your tools.
2. Set your module name in the environment variable `LITELLM_TOOLS_MODULE_NAME`.
3. Run Collmbo.
4. Send a message in Slack that triggers tool execution.

## Try this Feature

You can try it with [`examples/tools.py`](../../examples/tools.py). This sample returns weather information for a given city.

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
LITELLM_MODEL=gpt-4o
LITELLM_TOOLS_MODULE_NAME=examples.tools

$ docker run -it --env-file ./env -v ./examples:/app/examples ghcr.io/enechange/collmbo:latest
```

> ![Tools example](https://github.com/user-attachments/assets/d48a44fd-56fa-43c7-a0de-567ba03088b5)
