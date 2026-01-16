# Slack-friendly Formatting

## Usage

To enable Slack-friendly formatting, set the environment variable `TRANSLATE_MARKDOWN` to `true`.

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
LITELLM_MODEL=gpt-5.2
TRANSLATE_MARKDOWN=true

$ docker run -it --env-file ./env ghcr.io/enechange/collmbo:latest
```

> ![Slack formatting example](https://github.com/user-attachments/assets/6d73ed53-2849-4370-acb3-62694c05f86f)
