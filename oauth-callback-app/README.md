# OAuth Callback App for MCP Servers

A Lambda function for handling OAuth callbacks from AWS Bedrock AgentCore Identity for MCP server authentication.

## Purpose

This app receives OAuth callbacks from AgentCore Identity and verifies user identity with a verification code displayed in Slack. This is required for secure OAuth session binding.

## Features

- Receives OAuth callbacks from AgentCore Identity
- Verifies user identity with a verification code
- Calls `CompleteResourceTokenAuth` API to complete OAuth flow

## Deployment

1. Deploy `lambda_handler.py` as a Lambda function with Function URL enabled
2. Set environment variable `AGENTCORE_REGION` to your AgentCore region
3. Attach IAM role with `bedrock-agentcore:CompleteResourceTokenAuth` and `secretsmanager:GetSecretValue` permissions
4. Create a boto3 layer with the latest version if needed
5. Update `config/mcp.yml` with the Function URL:

   ```yaml
   oauth_callback_url: https://abc123.lambda-url.us-west-2.on.aws/callback
   ```

## Endpoints

- `GET /callback` - OAuth callback endpoint (displays verification form)
- `POST /verify` - Verifies user input and completes OAuth flow

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AGENTCORE_REGION` | No | `us-west-2` | AgentCore Identity region |
