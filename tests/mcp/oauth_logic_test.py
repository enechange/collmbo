"""
Tests for the MCP OAuth logic module.
"""

import pytest

from app.mcp.config_logic import get_oauth_servers_from_config
from app.mcp.oauth_tools_logic import (
    create_bearer_auth_headers,
    is_session_not_expired,
    parse_mcp_tool_name,
)


# Configuration and validation function tests
@pytest.mark.parametrize(
    "config, expected",
    [
        (
            {
                "servers": [
                    {
                        "name": "Server 1",
                        "url": "https://server1.example.com",
                        "auth_type": "none",
                    },
                    {
                        "name": "Server 2",
                        "url": "https://server2.example.com",
                        "auth_type": "user_federation",
                        "agentcore_provider": "aws",
                    },
                ]
            },
            [
                {
                    "name": "Server 2",
                    "url": "https://server2.example.com",
                    "auth_type": "user_federation",
                    "agentcore_provider": "aws",
                }
            ],
        ),
        ({"servers": []}, []),
        ({}, []),
    ],
)
def test_get_oauth_servers(config, expected):
    result = get_oauth_servers_from_config(config)
    assert result == expected


# Session and authentication function tests
@pytest.mark.parametrize(
    "session, current_time, expected",
    [
        (
            {"token": "test_token", "expires_at": 9999999999},
            1000000000,
            True,
        ),
        ({"token": "test_token", "expires_at": 1}, 1000000000, False),
        (None, 1000000000, False),
        ({"token": "test_token"}, 1000000000, False),
        ({}, 1000000000, False),
    ],
)
def test_is_session_not_expired(session, current_time, expected):
    result = is_session_not_expired(session, current_time)
    assert result == expected


@pytest.mark.parametrize(
    "token, additional_headers, expected",
    [
        (
            "test_token_123",
            None,
            {
                "Authorization": "Bearer test_token_123",
                "Content-Type": "application/json",
            },
        ),
        (
            "",
            None,
            {
                "Authorization": "Bearer ",
                "Content-Type": "application/json",
            },
        ),
        (
            "test_token_123",
            {"Notion-Version": "2022-06-28"},
            {
                "Authorization": "Bearer test_token_123",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            },
        ),
        (
            "test_token_123",
            {"Custom-Header": "value1", "Another-Header": "value2"},
            {
                "Authorization": "Bearer test_token_123",
                "Content-Type": "application/json",
                "Custom-Header": "value1",
                "Another-Header": "value2",
            },
        ),
        (
            "test_token_123",
            {},
            {
                "Authorization": "Bearer test_token_123",
                "Content-Type": "application/json",
            },
        ),
    ],
)
def test_create_bearer_auth_headers(token, additional_headers, expected):
    result = create_bearer_auth_headers(token, additional_headers)
    assert result == expected


@pytest.mark.parametrize(
    "tool_name, expected",
    [
        # Gemini format (dot-separated)
        (
            "u.0.get_user_info",
            ("get_user_info", "user_federation", 0),
        ),
        (
            "u.1.search_repositories",
            ("search_repositories", "user_federation", 1),
        ),
        (
            "n.2.create_issue",
            ("create_issue", "none", 2),
        ),
        (
            "u.5.complex-tool-name",
            ("complex-tool-name", "user_federation", 5),
        ),
        (
            "n.10.tool-with-multiple-hyphens-in-name",
            ("tool-with-multiple-hyphens-in-name", "none", 10),
        ),
        # GPT format (hyphen-separated)
        (
            "u-0-get_user_info",
            ("get_user_info", "user_federation", 0),
        ),
        (
            "u-1-search_repositories",
            ("search_repositories", "user_federation", 1),
        ),
        (
            "n-2-create_issue",
            ("create_issue", "none", 2),
        ),
        (
            "u-5-complex-tool-name",
            ("complex-tool-name", "user_federation", 5),
        ),
        (
            "n-10-tool-with-multiple-hyphens-in-name",
            ("tool-with-multiple-hyphens-in-name", "none", 10),
        ),
        # Invalid cases
        (
            "invalid",
            ("", "", -1),
        ),
        (
            "invalid.tool",
            ("", "", -1),
        ),
        (
            "invalid_auth.0.tool",
            ("", "", -1),
        ),
        (
            "u.invalid_index.tool",
            ("", "", -1),
        ),
        (
            "",
            ("", "", -1),
        ),
    ],
)
def test_parse_mcp_tool_name(tool_name, expected):
    result = parse_mcp_tool_name(tool_name)
    assert result == expected
