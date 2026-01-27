# Collmbo

[![CI](https://github.com/enechange/collmbo/actions/workflows/ci.yml/badge.svg)](https://github.com/enechange/collmbo/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/enechange/collmbo/branch/main/graph/badge.svg)](https://app.codecov.io/gh/enechange/collmbo)

![Collmbo icon](https://github.com/user-attachments/assets/b13da1c7-5d2f-4ad3-8c5b-9ef4e500deb8)

**A Slack bot that lets you chat with 100+ LLMs via [LiteLLM](https://github.com/BerriAI/litellm).** Pronounced the same as "Colombo".

> ![](https://github.com/user-attachments/assets/a377b868-3673-4798-b415-44e674cf7ae6)

## Quick Start

Collmbo supports multiple LLMs, but let's begin with OpenAI's gpt-5.2 model for a quick setup.

### 1. Create a Slack App

[Create a Slack app](docs/setup/creating-a-slack-app.md) and obtain the required tokens:

- App-level token (`xapp-1-...`)
- Bot token (`xoxb-...`)

### 2. Create a `.env` File

Save your credentials in a `.env` file:

```sh
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
LITELLM_MODEL=gpt-5.2
OPENAI_API_KEY=sk-...
```

### 3. Run Collmbo Container

Start the bot using Docker:

```sh
docker run -it --env-file .env ghcr.io/enechange/collmbo:latest
```

> [!NOTE]
>
> For versioned releases, you can specify a tag like `x.x.x`. For more details, please check the [list of available tags](https://github.com/enechange/collmbo/pkgs/container/collmbo/versions?filters%5Bversion_type%5D=tagged).

### 4. Say Hello!

Mention the bot in Slack and start chatting:

```
@Collmbo hello!
```

Collmbo should respond in channels, threads, and DMs.

## Want to Use a Different LLM?

First, pick your favorite LLM from [LiteLLM supported providers](https://docs.litellm.ai/docs/providers).

To use it, update the relevant environment variables in your `.env` file and restart the container.

Here are some examples:

### Gemini - Google AI Studio (Gemini 3 Pro)

```sh
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
LITELLM_MODEL=gemini/gemini-3-pro-preview
GEMINI_API_KEY=...
```

### Azure OpenAI (gpt-5.2)

```sh
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
LITELLM_MODEL=azure/<your_deployment_name>

AZURE_API_KEY=...
AZURE_API_BASE=...
AZURE_API_VERSION=...
```

### Amazon Bedrock (Claude Opus 4.5)

```sh
SLACK_APP_TOKEN=...
SLACK_BOT_TOKEN=...
LITELLM_MODEL=bedrock/global.anthropic.claude-opus-4-5-20251101-v1:0

# You can specify a Bedrock region if it's different from your default AWS region
AWS_REGION_NAME=us-west-2

# You can use your access key for authentication, but IAM roles are recommended
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

## Deployment

Collmbo does not serve endpoints and can run in any environment with internet access.

## Features

- **[MCP Tools](docs/features/mcp-tools.md)** - Extends functionality with MCP server.
- **[Tools (Function Calling)](docs/features/tools-function-calling.md)** - Extends functionality with function calling.
- **[Custom Callbacks](docs/features/custom-callbacks.md)** - Hooks into requests and responses for custom processing.
- **[Redaction](docs/features/redaction.md)** - Masks sensitive information before sending requests.
- **[Slack-friendly Formatting](docs/features/slack-friendly-formatting.md)** - Formats messages for better readability in Slack.
- **[Image Input](docs/features/image-input.md)** - Enables AI models to analyze uploaded images.
- **[PDF Input](docs/features/pdf-input.md)** - Enables AI models to analyze uploaded PDFs.
- **[Prompt Caching](docs/features/prompt-caching.md)** - May help reduce costs by reusing context (Anthropic Claude, Amazon Bedrock).

## Configuration

Collmbo runs with default settings, but you can customize its behavior by [setting optional environment variables](docs/configuration/optional-settings.md).

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

All commits must be signed with DCO (`git commit -s`).

## Related Projects

- [seratch/ChatGPT-in-Slack](https://github.com/seratch/ChatGPT-in-Slack) - The original project by @seratch.

## License

**The code** in this repository is licensed under the **MIT License**.

**The Collmbo icon** (`assets/icon.png`) is licensed under **[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)**. For example, you may use it as a Slack profile icon.
