# Redaction

## Usage

To enable redaction, set `true` in the environment variable `REDACTION_ENABLED`.

Redaction patterns can be customized using [environment variables](#environment-variables).

```sh
$ cat env
SLACK_APP_TOKEN=xapp-1-...
SLACK_BOT_TOKEN=xoxb-...
OPENAI_API_KEY=sk-...
LITELLM_MODEL=gpt-5.2
REDACTION_ENABLED=true

# Overwrite the redaction pattern for custom sensitive data
REDACT_USER_DEFINED_PATTERN=\bsensitive string\b

# Here, logging is enabled to check the effect of redaction
LITELLM_CALLBACK_MODULE_NAME=examples.callback_handler

$ docker run -it --env-file ./env -v ./examples:/app/examples ghcr.io/enechange/collmbo:latest
```

Sensitive strings in the message will be masked before being sent to the model.

> ![Redaction example](https://github.com/user-attachments/assets/4fb7d85f-00d8-4a27-9024-d737d5e77d64)

## Environment Variables

| Environment Variable | Description | Default |
| --- | --- | --- |
| `REDACTION_ENABLED` | Enable (`"true"`) or disable (`"false"`) redaction. | `"false"` |
| `REDACT_EMAIL_PATTERN` | Regex pattern for detecting email addresses. | `r"\b[A-Za-z0-9.*%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"` |
| `REDACT_PHONE_PATTERN` | Regex pattern for detecting phone numbers. | `r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"` |
| `REDACT_CREDIT_CARD_PATTERN` | Regex pattern for detecting credit card numbers. | `r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"` |
| `REDACT_SSN_PATTERN` | Regex pattern for detecting social security numbers (SSN). | `r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b"` |
| `REDACT_USER_DEFINED_PATTERN` | Custom regex pattern for additional sensitive data. The default will never match anything. | `r"(?!)"` |
