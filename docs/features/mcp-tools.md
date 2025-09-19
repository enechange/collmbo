# MCP Tools

Collmbo can integrate with MCP servers using streamable HTTP transport.

## Prerequisites for Using OAuth MCP Servers

If you will use MCP Servers with OAuth authentication, you need:

### AWS Credentials

AWS credentials are required for AgentCore Identity integration. You can authenticate using:

```sh
# Option 1: Access keys (for testing)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Option 2: IAM roles (recommended for production)
# Use IAM roles (e.g., attached to EC2 instance, ECS task, etc.)
```

### AgentCore Identity Configuration

[Configure credential provider(s) in Amazon Bedrock AgentCore Identity](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/resource-providers.html).

> [!CAUTION]
> **Security Note:** Access tokens are temporarily stored in memory during use. Do not share your Collmbo instance with untrusted parties, as they may be able to access authenticated resources on behalf of users.

## Usage

1. Edit [`config/mcp.yml`](../../config/mcp.yml).
2. Run Collmbo.
3. Check the Home tab in Slack to view available MCP servers.
4. Send a message in Slack that triggers tool execution.

## Try this Feature

```sh
$ cat config/mcp.yml
workload_name: Collmbo
auth_session_duration_minutes: 30
agentcore_region: us-west-2
servers:
  - name: AWS Knowledge
    url: https://knowledge-mcp.global.api.aws
    auth_type: none
  - name: GitHub
    url: https://api.githubcopilot.com/mcp/
    auth_type: user_federation
    scopes:
      - repo
      - read:packages
      - read:org
    agentcore_provider: github

$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
LITELLM_MODEL=gpt-4o

# AWS credentials for OAuth MCP servers (GitHub example above)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

$ docker run -it --env-file ./env -v ./config:/app/config ghcr.io/enechange/collmbo:latest
```

`workload_name` will be used as a name for [AgentCore Identity workload](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/creating-agent-identities.html).
