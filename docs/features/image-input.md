# Image Input

## Usage

1. Set a model that supports image input in the environment variable `LITELLM_MODEL`.
2. Set `true` in the environment variable `IMAGE_FILE_ACCESS_ENABLED`.
3. Run Collmbo.
4. Upload your image(s) and send a message in Slack.

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
LITELLM_MODEL=gpt-5.2
IMAGE_FILE_ACCESS_ENABLED=true

$ docker run -it --env-file ./env ghcr.io/enechange/collmbo:latest
```

> ![Image input example](https://github.com/user-attachments/assets/41e11441-230e-41db-8cae-efe5fd9dd426)
