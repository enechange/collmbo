# PDF Input

## Usage

1. Set a model that supports PDF input in the environment variable `LLM_MODEL`.
2. Set `true` in the environment variable `PDF_INPUT_ENABLED`.
3. Run Collmbo.
4. Upload your PDF(s) and send a message in Slack.

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
LLM_MODEL=bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
PDF_INPUT_ENABLED=true

$ docker run -it --env-file ./env ghcr.io/enechange/collmbo:latest
```

> ![PDF input example](https://github.com/user-attachments/assets/181a5400-3d6c-4daf-aa64-7d7cdd4cfaee)
