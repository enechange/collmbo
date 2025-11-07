"""
OAuth Callback Lambda Handler for MCP Servers

AWS Lambda handler for OAuth callbacks from AWS Bedrock AgentCore Identity
for MCP server authentication with user verification.

Deploy this as a Lambda function with Function URL enabled.
"""

import json
import os

import boto3

AGENTCORE_REGION = os.environ.get("AGENTCORE_REGION", "us-west-2")


def lambda_handler(event, context):
    """
    AWS Lambda handler for OAuth callback.

    Handles both GET (display form) and POST (verify code) requests.
    """
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("rawPath", "/")

    # OAuth callback - display form
    if path == "/callback" and method == "GET":
        query_params = event.get("queryStringParameters") or {}
        agentcore_user_id_prefix = query_params.get("state", "")
        session_id = query_params.get("session_id", "")

        if not agentcore_user_id_prefix or not session_id:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "text/html; charset=utf-8"},
                "body": """
                <html>
                    <head>
                        <title>Invalid Request</title>
                        <style>
                            body {
                                font-family: Arial, sans-serif;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                min-height: 100vh;
                                margin: 0;
                                background: #f5f5f5;
                            }
                            .container {
                                background: white;
                                padding: 40px;
                                border-radius: 8px;
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                                max-width: 500px;
                                width: 100%;
                                text-align: center;
                            }
                            .error { color: #dc3545; }
                            h1 { margin-top: 0; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1 class="error">❌ Invalid Request</h1>
                            <p>Missing required parameters. Please start the authorization process again from your Slack app.</p>
                        </div>
                    </body>
                </html>
                """,
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html; charset=utf-8"},
            "body": f"""
            <html>
                <head>
                    <title>Complete Authentication</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            min-height: 100vh;
                            margin: 0;
                            background: #f5f5f5;
                        }}
                        .container {{
                            background: white;
                            padding: 40px;
                            border-radius: 8px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                            max-width: 500px;
                            width: 100%;
                        }}
                        h1 {{ color: #333; margin-top: 0; }}
                        label {{ font-weight: bold; display: block; margin-top: 15px; }}
                        input[type="text"] {{
                            width: 100%;
                            padding: 10px;
                            margin: 10px 0;
                            border: 2px solid #ddd;
                            border-radius: 4px;
                            font-size: 16px;
                            box-sizing: border-box;
                        }}
                        button {{
                            background: #007bff;
                            color: white;
                            padding: 12px 30px;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                            font-size: 16px;
                            margin-top: 15px;
                            width: 100%;
                        }}
                        button:hover {{ background: #0056b3; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🔐 Complete Authentication</h1>
                        <p>Please enter the verification code shown in your Slack app to complete the authentication process.</p>
                        <form method="post" action="/verify">
                            <input type="hidden" name="agentcore_user_id_prefix" value="{agentcore_user_id_prefix}">
                            <input type="hidden" name="session_id" value="{session_id}">
                            <label for="last_8_chars">Verification Code (8 characters):</label>
                            <input type="text" id="last_8_chars" name="last_8_chars" maxlength="8" pattern="[a-f0-9]{{8}}"
                                   placeholder="e.g., e9f0a1b2" required autofocus>
                            <button type="submit">Verify</button>
                        </form>
                    </div>
                </body>
            </html>
            """,
        }

    # Verify endpoint - process form submission
    if path == "/verify" and method == "POST":
        # Parse form data
        body = event.get("body", "")
        if event.get("isBase64Encoded", False):
            import base64

            body = base64.b64decode(body).decode("utf-8")

        # Simple form parsing
        form_data = {}
        for pair in body.split("&"):
            if "=" in pair:
                key, value = pair.split("=", 1)
                # URL decode
                import urllib.parse

                form_data[key] = urllib.parse.unquote_plus(value)

        agentcore_user_id_prefix = form_data.get("agentcore_user_id_prefix", "")
        session_id = form_data.get("session_id", "")
        last_8_chars = form_data.get("last_8_chars", "")

        if not session_id:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "text/html; charset=utf-8"},
                "body": """
                <html>
                    <head>
                        <title>Verification Failed</title>
                        <style>
                            body {
                                font-family: Arial, sans-serif;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                min-height: 100vh;
                                margin: 0;
                                background: #f5f5f5;
                            }
                            .container {
                                background: white;
                                padding: 40px;
                                border-radius: 8px;
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                                max-width: 500px;
                                width: 100%;
                                text-align: center;
                            }
                            .error { color: #dc3545; }
                            h1 { margin-top: 0; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1 class="error">❌ Verification Failed</h1>
                            <p>Missing session information.</p>
                            <p>Please go back to your Slack app and start the authorization process again.</p>
                        </div>
                    </body>
                </html>
                """,
            }

        # Reconstruct full agentcore_user_id
        full_agentcore_user_id = agentcore_user_id_prefix + last_8_chars

        try:
            # Call CompleteResourceTokenAuth API
            client = boto3.client("bedrock-agentcore", region_name=AGENTCORE_REGION)
            client.complete_resource_token_auth(
                sessionUri=session_id,
                userIdentifier={"userId": full_agentcore_user_id},
            )

            return {
                "statusCode": 200,
                "headers": {"Content-Type": "text/html; charset=utf-8"},
                "body": """
                <html>
                    <head>
                        <title>Verification Successful</title>
                        <style>
                            body {
                                font-family: Arial, sans-serif;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                min-height: 100vh;
                                margin: 0;
                                background: #f5f5f5;
                            }
                            .container {
                                background: white;
                                padding: 40px;
                                border-radius: 8px;
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                                max-width: 500px;
                                width: 100%;
                                text-align: center;
                            }
                            .success { color: #28a745; }
                            h1 { margin-top: 0; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1 class="success">✅ Verification Successful!</h1>
                            <p>Your OAuth authentication has been completed successfully.</p>
                            <p>You can now close this window and return to your Slack app.</p>
                        </div>
                    </body>
                </html>
                """,
            }
        except Exception as e:
            print(f"CompleteResourceTokenAuth failed: {e}")
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "text/html; charset=utf-8"},
                "body": """
                <html>
                    <head>
                        <title>Verification Failed</title>
                        <style>
                            body {
                                font-family: Arial, sans-serif;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                min-height: 100vh;
                                margin: 0;
                                background: #f5f5f5;
                            }
                            .container {
                                background: white;
                                padding: 40px;
                                border-radius: 8px;
                                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                                max-width: 500px;
                                width: 100%;
                                text-align: center;
                            }
                            .error { color: #dc3545; }
                            button {
                                background: #007bff;
                                color: white;
                                padding: 12px 30px;
                                border: none;
                                border-radius: 4px;
                                cursor: pointer;
                                font-size: 16px;
                                margin-top: 20px;
                            }
                            button:hover { background: #0056b3; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1 class="error">❌ Verification Failed</h1>
                            <p>The verification code you entered is incorrect or the session has expired.</p>
                            <button onclick="history.back()">Try Again</button>
                        </div>
                    </body>
                </html>
                """,
            }

    # Unknown path/method
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "Not Found"}),
    }
